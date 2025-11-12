"""
Liver Toxicity Mechanisms

Models multiple pathways of drug-induced liver injury (DILI):
- Mitochondrial dysfunction
- Oxidative stress
- Bile stasis (cholestasis)
- Immune activation

Mathematical formulation:
    Toxicity Score = Σ w_i · f_i([Drug], [Metabolite], Biomarkers)

where f_i are mechanism-specific functions.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, Callable
from enum import Enum


class ToxicityMechanism(Enum):
    """Mechanisms of hepatotoxicity"""
    MITOCHONDRIAL = "mitochondrial"      # ATP depletion
    OXIDATIVE = "oxidative"              # ROS/GSH depletion
    CHOLESTATIC = "cholestatic"          # Bile flow impairment
    IMMUNE = "immune"                    # Inflammatory/idiosyncratic
    DIRECT = "direct"                    # Direct cytotoxicity


@dataclass
class ToxicityParameters:
    """Parameters for toxicity assessment"""
    # Mechanism weights
    w_mitochondrial: float = 0.3
    w_oxidative: float = 0.25
    w_cholestatic: float = 0.2
    w_immune: float = 0.15
    w_direct: float = 0.1

    # Thresholds
    ATP_toxicity_threshold: float = 0.5
    GSH_toxicity_threshold: float = 0.3
    bilirubin_threshold: float = 2.0
    cytokine_threshold: float = 1.0

    # Damage accumulation
    damage_accumulation_rate: float = 0.1
    damage_repair_rate: float = 0.05


class LiverToxicity:
    """
    Multi-mechanism hepatotoxicity model.

    Integrates:
    - Cellular energetics (ATP, mitochondria)
    - Oxidative balance (GSH, ROS)
    - Biliary function
    - Immune activation

    Usage:
        >>> tox = LiverToxicity()
        >>> tox.set_drug_concentration(lambda t: 100.0)
        >>> tox.set_metabolite_concentration(lambda t: 50.0)
        >>> times, scores = tox.simulate(t_span=(0, 100), dt=0.1)
    """

    def __init__(self, params: Optional[ToxicityParameters] = None):
        self.params = params or ToxicityParameters()

        # State: [cumulative_damage, ATP, GSH, bilirubin, inflammatory_signal]
        self.state = np.array([0.0, 1.0, 1.0, 1.0, 0.0])

        # Drug/metabolite functions
        self._drug_func = lambda t: 0.0
        self._metabolite_func = lambda t: 0.0

        # External signals
        self._immune_signal_func = lambda t: 0.0

    def set_drug_concentration(self, func: Callable[[float], float]):
        """Set time-varying drug concentration"""
        self._drug_func = func

    def set_metabolite_concentration(self, func: Callable[[float], float]):
        """Set time-varying metabolite concentration"""
        self._metabolite_func = func

    def set_immune_signal(self, func: Callable[[float], float]):
        """Set immune activation signal"""
        self._immune_signal_func = func

    def mitochondrial_toxicity(
        self,
        drug_conc: float,
        metabolite_conc: float,
        ATP: float
    ) -> float:
        """
        Mitochondrial dysfunction score.

        Based on ATP depletion and direct mitochondrial damage.
        """
        # Direct mitochondrial uncoupling/damage
        direct_damage = 0.01 * (drug_conc + 2.0 * metabolite_conc)

        # ATP depletion severity
        ATP_depletion = max(
            0.0,
            (self.params.ATP_toxicity_threshold - ATP) / self.params.ATP_toxicity_threshold
        )

        return direct_damage + ATP_depletion

    def oxidative_toxicity(
        self,
        drug_conc: float,
        metabolite_conc: float,
        GSH: float
    ) -> float:
        """
        Oxidative stress score.

        Based on GSH depletion and ROS production.
        """
        # ROS production from drug/metabolite
        ROS_production = 0.02 * (drug_conc + 1.5 * metabolite_conc)

        # GSH depletion severity
        GSH_depletion = max(
            0.0,
            (self.params.GSH_toxicity_threshold - GSH) / self.params.GSH_toxicity_threshold
        )

        return ROS_production + 2.0 * GSH_depletion

    def cholestatic_toxicity(
        self,
        drug_conc: float,
        bilirubin: float
    ) -> float:
        """
        Cholestatic (bile flow) toxicity score.

        Based on bile acid transport inhibition.
        """
        # Bile transporter inhibition
        transporter_inhibition = 0.005 * drug_conc

        # Bilirubin accumulation
        bilirubin_excess = max(
            0.0,
            (bilirubin - self.params.bilirubin_threshold) / self.params.bilirubin_threshold
        )

        return transporter_inhibition + bilirubin_excess

    def immune_toxicity(
        self,
        drug_conc: float,
        inflammatory_signal: float
    ) -> float:
        """
        Immune-mediated toxicity score.

        Idiosyncratic, inflammatory component.
        """
        # Drug-protein adducts (hapten formation)
        hapten_formation = 0.003 * drug_conc

        # Inflammatory amplification
        inflammation_score = max(
            0.0,
            (inflammatory_signal - self.params.cytokine_threshold) / self.params.cytokine_threshold
        )

        return hapten_formation + inflammation_score

    def direct_toxicity(
        self,
        drug_conc: float,
        metabolite_conc: float
    ) -> float:
        """
        Direct cytotoxicity score.

        Dose-dependent cell membrane damage.
        """
        return 0.008 * drug_conc + 0.015 * metabolite_conc

    def compute_total_toxicity_score(
        self,
        drug_conc: float,
        metabolite_conc: float,
        ATP: float,
        GSH: float,
        bilirubin: float,
        inflammatory_signal: float
    ) -> Tuple[float, dict]:
        """
        Compute weighted total toxicity score.

        Returns:
            (total_score, mechanism_contributions)
        """
        mito = self.mitochondrial_toxicity(drug_conc, metabolite_conc, ATP)
        oxid = self.oxidative_toxicity(drug_conc, metabolite_conc, GSH)
        chol = self.cholestatic_toxicity(drug_conc, bilirubin)
        immu = self.immune_toxicity(drug_conc, inflammatory_signal)
        dire = self.direct_toxicity(drug_conc, metabolite_conc)

        total = (
            self.params.w_mitochondrial * mito +
            self.params.w_oxidative * oxid +
            self.params.w_cholestatic * chol +
            self.params.w_immune * immu +
            self.params.w_direct * dire
        )

        contributions = {
            'mitochondrial': mito,
            'oxidative': oxid,
            'cholestatic': chol,
            'immune': immu,
            'direct': dire,
            'total': total
        }

        return total, contributions

    def derivatives(self, state: np.ndarray, t: float) -> np.ndarray:
        """
        Compute time derivatives.

        State: [cumulative_damage, ATP, GSH, bilirubin, inflammatory_signal]
        """
        cumulative_damage, ATP, GSH, bilirubin, inflammatory = state

        drug_conc = self._drug_func(t)
        metabolite_conc = self._metabolite_func(t)
        immune_signal = self._immune_signal_func(t)

        # Compute toxicity score
        tox_score, _ = self.compute_total_toxicity_score(
            drug_conc, metabolite_conc, ATP, GSH, bilirubin, immune_signal
        )

        # Cumulative damage accumulation/repair
        dDamage = (
            self.params.damage_accumulation_rate * tox_score -
            self.params.damage_repair_rate * cumulative_damage * (1 - tox_score)
        )

        # ATP dynamics
        ATP_production = 1.0 * (1 - 0.5 * cumulative_damage)
        ATP_consumption = 0.5
        ATP_mitotoxicity = 0.1 * (drug_conc + 2.0 * metabolite_conc)

        dATP = ATP_production - ATP_consumption - ATP_mitotoxicity - 0.2 * ATP

        # GSH dynamics
        GSH_synthesis = 0.5 * (1 - 0.3 * cumulative_damage)
        GSH_consumption = 0.02 * (drug_conc + metabolite_conc) + 0.1 * metabolite_conc

        dGSH = GSH_synthesis - GSH_consumption - 0.1 * GSH

        # Bilirubin dynamics
        bilirubin_production = 0.1  # Baseline heme catabolism
        bilirubin_clearance = 0.08 * (1 - 0.01 * drug_conc)  # Transporter inhibition

        dBilirubin = bilirubin_production - bilirubin_clearance

        # Inflammatory signal
        damage_induced_inflammation = 0.1 * cumulative_damage
        inflammation_resolution = 0.05 * inflammatory

        dInflammatory = damage_induced_inflammation + immune_signal - inflammation_resolution

        return np.array([dDamage, dATP, dGSH, dBilirubin, dInflammatory])

    def integrate_step(self, dt: float, t: float) -> np.ndarray:
        """Update state by one timestep using RK4"""
        k1 = self.derivatives(self.state, t)
        k2 = self.derivatives(self.state + 0.5*dt*k1, t + 0.5*dt)
        k3 = self.derivatives(self.state + 0.5*dt*k2, t + 0.5*dt)
        k4 = self.derivatives(self.state + dt*k3, t + dt)

        self.state += (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

        # Ensure physical bounds
        self.state[0] = max(0.0, self.state[0])  # Damage >= 0
        self.state[1] = np.clip(self.state[1], 0.0, 2.0)  # ATP
        self.state[2] = np.clip(self.state[2], 0.0, 2.0)  # GSH
        self.state[3] = max(0.0, self.state[3])  # Bilirubin
        self.state[4] = max(0.0, self.state[4])  # Inflammation

        return self.state

    def simulate(
        self,
        t_span: Tuple[float, float],
        dt: float = 0.1
    ) -> Tuple[np.ndarray, np.ndarray, list]:
        """
        Simulate hepatotoxicity dynamics.

        Returns:
            (times, states, toxicity_scores)
        """
        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt)

        times = np.linspace(t_start, t_end, n_steps)
        states = np.zeros((n_steps, 5))
        toxicity_scores = []

        states[0] = self.state

        for i in range(1, n_steps):
            t = times[i]
            states[i] = self.integrate_step(dt, t)

            # Compute toxicity score at this timepoint
            drug_conc = self._drug_func(t)
            metabolite_conc = self._metabolite_func(t)
            score, contribs = self.compute_total_toxicity_score(
                drug_conc, metabolite_conc,
                states[i, 1], states[i, 2], states[i, 3], states[i, 4]
            )
            toxicity_scores.append(contribs)

        return times, states, toxicity_scores

    def reset(self):
        """Reset to healthy state"""
        self.state = np.array([0.0, 1.0, 1.0, 1.0, 0.0])


if __name__ == "__main__":
    print("=" * 70)
    print("LIVER TOXICITY MECHANISMS")
    print("=" * 70)

    # Example 1: Acute high-dose toxicity
    print("\n1. Testing acute hepatotoxicity...")
    tox = LiverToxicity()

    # High-dose drug exposure
    tox.set_drug_concentration(lambda t: 200.0 if t < 10 else 50.0)
    tox.set_metabolite_concentration(lambda t: 100.0 if t < 10 else 25.0)

    times, states, scores = tox.simulate(t_span=(0, 50), dt=0.1)

    print(f"   Initial cumulative damage: {states[0,0]:.3f}")
    print(f"   Peak cumulative damage: {np.max(states[:,0]):.3f}")
    print(f"   Final ATP level: {states[-1,1]:.3f}")
    print(f"   Final GSH level: {states[-1,2]:.3f}")
    print(f"   Final bilirubin: {states[-1,3]:.3f}")

    # Peak toxicity score breakdown
    peak_idx = np.argmax(states[:,0])
    peak_score = scores[peak_idx]
    print(f"\n   Peak toxicity breakdown:")
    print(f"     Mitochondrial: {peak_score['mitochondrial']:.3f}")
    print(f"     Oxidative: {peak_score['oxidative']:.3f}")
    print(f"     Cholestatic: {peak_score['cholestatic']:.3f}")
    print(f"     Immune: {peak_score['immune']:.3f}")
    print(f"     Direct: {peak_score['direct']:.3f}")
    print(f"     TOTAL: {peak_score['total']:.3f}")

    # Example 2: Chronic low-dose toxicity
    print("\n2. Testing chronic hepatotoxicity...")
    tox.reset()

    tox.set_drug_concentration(lambda t: 50.0)
    tox.set_metabolite_concentration(lambda t: 25.0)
    tox.set_immune_signal(lambda t: 0.5)  # Low-grade inflammation

    times, states, scores = tox.simulate(t_span=(0, 200), dt=0.1)

    print(f"   Steady-state damage: {states[-1,0]:.3f}")
    print(f"   Steady-state ATP: {states[-1,1]:.3f}")
    print(f"   Steady-state GSH: {states[-1,2]:.3f}")

    final_score = scores[-1]
    print(f"\n   Steady-state toxicity:")
    for mechanism, value in final_score.items():
        print(f"     {mechanism.capitalize()}: {value:.3f}")

    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("=" * 70)
    print("✓ MULTI-MECHANISM: 5 distinct toxicity pathways")
    print("✓ CUMULATIVE: Damage accumulation over time")
    print("✓ METABOLIC: ATP and GSH depletion")
    print("✓ WEIGHTED: Mechanism-specific contributions")
    print("=" * 70)
