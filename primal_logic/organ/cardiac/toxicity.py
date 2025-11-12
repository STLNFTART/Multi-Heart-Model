"""
Cardiac Toxicity Mechanisms

Models multiple pathways of drug-induced cardiac injury:
- hERG K+ channel blockade (QT prolongation, arrhythmia)
- L-type Ca channel effects
- Mitochondrial dysfunction
- Oxidative stress
- Direct myocyte damage

Mathematical formulation:
    Cardiotoxicity Score = Σ w_i · f_i([Drug], Metrics)
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, Callable
from enum import Enum


class CardiacToxicityMechanism(Enum):
    """Mechanisms of cardiotoxicity"""
    HERG_BLOCK = "hERG_block"            # QT prolongation
    CALCIUM_DYSREGULATION = "calcium"    # Contractility/arrhythmia
    MITOCHONDRIAL = "mitochondrial"      # Energy depletion
    OXIDATIVE = "oxidative"              # ROS damage
    DIRECT_MYOCYTE = "direct"            # Cell death


@dataclass
class CardiacToxicityParameters:
    """Parameters for cardiac toxicity assessment"""
    # Mechanism weights
    w_hERG: float = 0.35              # High weight (life-threatening)
    w_calcium: float = 0.25
    w_mitochondrial: float = 0.2
    w_oxidative: float = 0.15
    w_direct: float = 0.05

    # Thresholds
    QTc_prolongation_threshold: float = 1.2    # 20% prolongation → high risk
    ATP_depletion_threshold: float = 0.5
    contractility_loss_threshold: float = 0.3   # 30% loss
    troponin_threshold: float = 0.5            # Myocyte damage

    # Drug-specific IC50 values (can be overridden)
    hERG_IC50: float = 10.0           # μM
    Ca_channel_IC50: float = 50.0
    mito_tox_IC50: float = 100.0


class CardiacToxicity:
    """
    Multi-mechanism cardiotoxicity model.

    Integrates:
    - Electrophysiology (APD, QT)
    - Contractile function
    - Energetics (ATP, mitochondria)
    - Cell viability (troponin release)

    Usage:
        >>> tox = CardiacToxicity()
        >>> tox.set_drug_concentration(lambda t: 50.0)
        >>> times, scores = tox.simulate(t_span=(0, 100), dt=0.1, cardio_model=cardio)
    """

    def __init__(self, params: Optional[CardiacToxicityParameters] = None):
        self.params = params or CardiacToxicityParameters()

        # State: [cumulative_damage, troponin_released, oxidative_damage]
        self.state = np.array([0.0, 0.0, 0.0])

        # Drug concentration function
        self._drug_func = lambda t: 0.0

        # Metabolite concentration (often more toxic)
        self._metabolite_func = lambda t: 0.0

    def set_drug_concentration(self, func: Callable[[float], float]):
        """Set time-varying drug concentration"""
        self._drug_func = func

    def set_metabolite_concentration(self, func: Callable[[float], float]):
        """Set time-varying metabolite concentration"""
        self._metabolite_func = func

    def hERG_block_fraction(self, drug_conc: float) -> float:
        """
        Compute fractional hERG K+ channel blockade.

        Uses Hill equation: Block = [Drug]^n / (IC50^n + [Drug]^n)
        """
        n = 1.0  # Hill coefficient (typically 1 for hERG)
        block = (drug_conc ** n) / (self.params.hERG_IC50 ** n + drug_conc ** n)

        return block

    def hERG_toxicity_score(
        self,
        drug_conc: float,
        APD: float,
        APD_baseline: float
    ) -> float:
        """
        Compute hERG-mediated toxicity score.

        Based on:
        - Drug concentration vs IC50
        - APD/QTc prolongation
        """
        # Drug concentration score
        block_fraction = self.hERG_block_fraction(drug_conc)

        # APD prolongation score
        if APD_baseline > 0:
            QTc_ratio = APD / APD_baseline
            prolongation_score = max(
                0.0,
                (QTc_ratio - self.params.QTc_prolongation_threshold) /
                self.params.QTc_prolongation_threshold
            )
        else:
            prolongation_score = 0.0

        return block_fraction + prolongation_score

    def calcium_toxicity_score(
        self,
        drug_conc: float,
        Ca_level: float,
        contractility: float,
        contractility_baseline: float
    ) -> float:
        """
        Compute calcium dysregulation toxicity score.

        Based on:
        - L-type Ca channel effects
        - Contractility changes
        - Calcium overload
        """
        # Ca channel inhibition
        Ca_block = (drug_conc ** 1.5) / (self.params.Ca_channel_IC50 ** 1.5 + drug_conc ** 1.5)

        # Contractility loss
        if contractility_baseline > 0:
            contractility_ratio = contractility / contractility_baseline
            contractility_loss = max(
                0.0,
                (self.params.contractility_loss_threshold - contractility_ratio) /
                self.params.contractility_loss_threshold
            )
        else:
            contractility_loss = 0.0

        # Calcium overload (can also be toxic)
        Ca_overload = max(0.0, Ca_level - 2.0) / 2.0

        return Ca_block + contractility_loss + Ca_overload

    def mitochondrial_toxicity_score(
        self,
        drug_conc: float,
        metabolite_conc: float,
        ATP: float
    ) -> float:
        """
        Compute mitochondrial dysfunction score.

        Based on:
        - Direct mitochondrial toxicity
        - ATP depletion
        """
        # Direct mitochondrial toxins (e.g., doxorubicin metabolites)
        mito_damage = (
            (drug_conc ** 2) / (self.params.mito_tox_IC50 ** 2 + drug_conc ** 2) +
            2.0 * (metabolite_conc ** 2) / (self.params.mito_tox_IC50 ** 2 + metabolite_conc ** 2)
        )

        # ATP depletion severity
        ATP_depletion = max(
            0.0,
            (self.params.ATP_depletion_threshold - ATP) / self.params.ATP_depletion_threshold
        )

        return mito_damage + ATP_depletion

    def oxidative_toxicity_score(
        self,
        drug_conc: float,
        metabolite_conc: float,
        oxidative_damage: float
    ) -> float:
        """
        Compute oxidative stress score.

        ROS production, lipid peroxidation, protein oxidation.
        """
        # ROS production from drug/metabolite
        ROS_production = 0.01 * drug_conc + 0.03 * metabolite_conc

        # Cumulative oxidative damage
        return ROS_production + oxidative_damage

    def direct_myocyte_toxicity_score(
        self,
        drug_conc: float,
        troponin: float
    ) -> float:
        """
        Compute direct myocyte damage score.

        Based on troponin release (cell death marker).
        """
        # Direct cytotoxicity
        direct_damage = 0.005 * drug_conc

        # Troponin release
        troponin_score = troponin / (self.params.troponin_threshold + troponin)

        return direct_damage + troponin_score

    def compute_total_toxicity_score(
        self,
        drug_conc: float,
        metabolite_conc: float,
        cardiac_metrics: dict,
        baseline_metrics: dict
    ) -> Tuple[float, dict]:
        """
        Compute weighted total cardiotoxicity score.

        Args:
            drug_conc: Drug concentration (μM)
            metabolite_conc: Metabolite concentration (μM)
            cardiac_metrics: Current cardiac metrics
            baseline_metrics: Baseline cardiac metrics

        Returns:
            (total_score, mechanism_contributions)
        """
        # Extract metrics
        APD = cardiac_metrics.get('APD', 0.0)
        Ca = cardiac_metrics.get('Ca', 0.5)
        contractility = cardiac_metrics.get('contractility', 50.0)
        ATP = cardiac_metrics.get('ATP', 1.0)

        APD_baseline = baseline_metrics.get('APD', 1.0)
        contractility_baseline = baseline_metrics.get('contractility', 50.0)

        # Compute mechanism scores
        hERG = self.hERG_toxicity_score(drug_conc, APD, APD_baseline)
        calcium = self.calcium_toxicity_score(drug_conc, Ca, contractility, contractility_baseline)
        mito = self.mitochondrial_toxicity_score(drug_conc, metabolite_conc, ATP)
        oxid = self.oxidative_toxicity_score(drug_conc, metabolite_conc, self.state[2])
        direct = self.direct_myocyte_toxicity_score(drug_conc, self.state[1])

        # Weighted total
        total = (
            self.params.w_hERG * hERG +
            self.params.w_calcium * calcium +
            self.params.w_mitochondrial * mito +
            self.params.w_oxidative * oxid +
            self.params.w_direct * direct
        )

        contributions = {
            'hERG': hERG,
            'calcium': calcium,
            'mitochondrial': mito,
            'oxidative': oxid,
            'direct': direct,
            'total': total
        }

        return total, contributions

    def derivatives(
        self,
        state: np.ndarray,
        t: float,
        cardiac_metrics: dict
    ) -> np.ndarray:
        """
        Compute time derivatives.

        State: [cumulative_damage, troponin_released, oxidative_damage]
        """
        cumulative_damage, troponin, oxidative_damage = state

        drug_conc = self._drug_func(t)
        metabolite_conc = self._metabolite_func(t)

        # Cumulative damage accumulation
        ATP = cardiac_metrics.get('ATP', 1.0)
        damage_rate = 0.01 * (drug_conc + 2.0 * metabolite_conc) * (1.0 / (ATP + 0.5))
        repair_rate = 0.005 * cumulative_damage * ATP

        dDamage = damage_rate - repair_rate

        # Troponin release (myocyte death)
        troponin_release_rate = 0.05 * cumulative_damage + 0.001 * drug_conc
        troponin_clearance = 0.01 * troponin

        dTroponin = troponin_release_rate - troponin_clearance

        # Oxidative damage
        ROS_production = 0.01 * drug_conc + 0.03 * metabolite_conc
        antioxidant_capacity = 0.02 * oxidative_damage

        dOxidative = ROS_production - antioxidant_capacity

        return np.array([dDamage, dTroponin, dOxidative])

    def integrate_step(
        self,
        dt: float,
        t: float,
        cardiac_metrics: dict
    ) -> np.ndarray:
        """Update state by one timestep using RK4"""
        k1 = self.derivatives(self.state, t, cardiac_metrics)
        k2 = self.derivatives(self.state + 0.5*dt*k1, t + 0.5*dt, cardiac_metrics)
        k3 = self.derivatives(self.state + 0.5*dt*k2, t + 0.5*dt, cardiac_metrics)
        k4 = self.derivatives(self.state + dt*k3, t + dt, cardiac_metrics)

        self.state += (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

        # Ensure non-negative
        self.state = np.maximum(self.state, 0.0)

        return self.state

    def reset(self):
        """Reset to healthy state"""
        self.state = np.array([0.0, 0.0, 0.0])

    def get_biomarkers(self) -> dict:
        """
        Return cardiotoxicity biomarkers.

        Troponin: Myocyte damage
        BNP: Heart failure marker (proportional to cumulative damage)
        """
        cumulative_damage, troponin, oxidative_damage = self.state

        return {
            'Troponin': troponin,
            'BNP': cumulative_damage * 10.0,  # Arbitrary scaling
            'Oxidative_damage': oxidative_damage,
            'Cumulative_damage': cumulative_damage
        }


if __name__ == "__main__":
    print("=" * 70)
    print("CARDIAC TOXICITY MECHANISMS")
    print("=" * 70)

    # Example 1: hERG block assessment
    print("\n1. Testing hERG K+ channel blockade...")
    tox = CardiacToxicity()

    drug_concentrations = [1.0, 5.0, 10.0, 20.0, 50.0]
    print(f"   {'[Drug] (μM)':<15} {'hERG Block':<15} {'Risk':<10}")
    print("   " + "-" * 40)

    for conc in drug_concentrations:
        block = tox.hERG_block_fraction(conc)
        risk = "HIGH" if block > 0.5 else ("MODERATE" if block > 0.2 else "LOW")
        print(f"   {conc:<15.1f} {block:<15.2%} {risk:<10}")

    # Example 2: Integrated toxicity score
    print("\n2. Testing integrated cardiotoxicity score...")

    baseline_metrics = {
        'APD': 0.3,
        'Ca': 0.5,
        'contractility': 50.0,
        'ATP': 1.0
    }

    # After drug exposure
    drug_metrics = {
        'APD': 0.4,      # 33% prolongation
        'Ca': 0.6,
        'contractility': 35.0,  # 30% loss
        'ATP': 0.6       # 40% depletion
    }

    total_score, contributions = tox.compute_total_toxicity_score(
        drug_conc=25.0,
        metabolite_conc=10.0,
        cardiac_metrics=drug_metrics,
        baseline_metrics=baseline_metrics
    )

    print(f"\n   Toxicity Score Breakdown:")
    print(f"   {'Mechanism':<20} {'Score':<10}")
    print("   " + "-" * 30)
    for mechanism, score in contributions.items():
        print(f"   {mechanism.capitalize():<20} {score:<10.3f}")

    print(f"\n   Overall Risk: {'HIGH' if total_score > 1.0 else ('MODERATE' if total_score > 0.5 else 'LOW')}")

    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("=" * 70)
    print("✓ MULTI-MECHANISM: hERG, Ca, mitochondrial, oxidative, direct")
    print("✓ QT PROLONGATION: APD-based arrhythmia risk")
    print("✓ BIOMARKERS: Troponin, BNP")
    print("✓ DOSE-DEPENDENT: IC50-based scoring")
    print("=" * 70)
