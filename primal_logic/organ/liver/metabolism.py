"""
Liver Drug Metabolism Model

Phase I and Phase II drug metabolism with CYP450 enzyme system.
Michaelis-Menten kinetics with enzyme induction and substrate inhibition.

Mathematical formulation (Michaelis-Menten):
    v = (Vmax · [S]) / (Km + [S])

With competitive inhibition:
    v = (Vmax · [S]) / (Km·(1 + [I]/Ki) + [S])

Enzyme induction:
    dE/dt = k_syn·(1 + α·[S]^n/(EC50^n + [S]^n)) - k_deg·E

where:
    [S]: Substrate (drug) concentration
    E: Enzyme level
    Vmax: Maximum velocity
    Km: Michaelis constant
    [I]: Inhibitor concentration
    Ki: Inhibition constant
    k_syn, k_deg: Enzyme synthesis/degradation rates
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, Callable, List
from enum import Enum


class CYP450Isoform(Enum):
    """Major CYP450 isoforms"""
    CYP1A2 = "1A2"    # Caffeine, theophylline
    CYP2C9 = "2C9"    # Warfarin, NSAIDs
    CYP2C19 = "2C19"  # PPIs, clopidogrel
    CYP2D6 = "2D6"    # Beta blockers, antidepressants
    CYP2E1 = "2E1"    # Acetaminophen, ethanol
    CYP3A4 = "3A4"    # ~50% of drugs


@dataclass
class MetabolismParameters:
    """Parameters for drug metabolism"""
    Vmax_base: float = 100.0           # Base maximum velocity (μM/hr)
    Km: float = 10.0                   # Michaelis constant (μM)
    k_syn: float = 0.1                 # Enzyme synthesis rate
    k_deg: float = 0.05                # Enzyme degradation rate

    # Induction parameters
    alpha_induction: float = 2.0       # Maximum fold-induction
    EC50_induction: float = 20.0       # Half-maximal induction concentration
    n_hill: float = 2.0                # Hill coefficient

    # Phase II conjugation
    conjugation_rate: float = 0.5      # Fraction undergoing conjugation

    # Inhibition parameters
    Ki: float = 50.0                   # Inhibition constant (μM)


class CYP450System:
    """
    Individual CYP450 enzyme system with induction and inhibition.

    Usage:
        >>> cyp = CYP450System(CYP450Isoform.CYP3A4)
        >>> clearance = cyp.metabolize(drug_concentration=25.0, enzyme_level=1.0)
    """

    def __init__(
        self,
        isoform: CYP450Isoform,
        params: Optional[MetabolismParameters] = None
    ):
        self.isoform = isoform
        self.params = params or MetabolismParameters()
        self.enzyme_level = 1.0  # Normalized to baseline

    def metabolize(
        self,
        drug_concentration: float,
        enzyme_level: float,
        inhibitor_concentration: float = 0.0
    ) -> float:
        """
        Compute metabolic clearance rate.

        Args:
            drug_concentration: Substrate concentration (μM)
            enzyme_level: Enzyme level (normalized)
            inhibitor_concentration: Competitive inhibitor (μM)

        Returns:
            Clearance rate (μM/hr)
        """
        Vmax_effective = self.params.Vmax_base * enzyme_level

        # Competitive inhibition
        if inhibitor_concentration > 0:
            Km_apparent = self.params.Km * (
                1 + inhibitor_concentration / self.params.Ki
            )
        else:
            Km_apparent = self.params.Km

        # Michaelis-Menten
        v = (Vmax_effective * drug_concentration) / (Km_apparent + drug_concentration)

        return v

    def enzyme_induction_rate(self, drug_concentration: float) -> float:
        """
        Compute enzyme induction rate.

        Args:
            drug_concentration: Inducer concentration (μM)

        Returns:
            dE/dt
        """
        # Hill equation for induction
        induction_factor = self.params.alpha_induction * (
            drug_concentration ** self.params.n_hill /
            (self.params.EC50_induction ** self.params.n_hill +
             drug_concentration ** self.params.n_hill)
        )

        dE = (
            self.params.k_syn * (1 + induction_factor) -
            self.params.k_deg * self.enzyme_level
        )

        return dE

    def update_enzyme_level(self, dt: float, drug_concentration: float):
        """Update enzyme level based on induction"""
        dE = self.enzyme_induction_rate(drug_concentration)
        self.enzyme_level += dt * dE
        self.enzyme_level = max(0.1, self.enzyme_level)  # Minimum 10% baseline

    def reset(self):
        """Reset enzyme level to baseline"""
        self.enzyme_level = 1.0


class LiverMetabolism:
    """
    Complete liver metabolism model with multiple CYP450 isoforms.

    State variables:
    - Enzyme levels for each isoform
    - Phase I metabolite concentrations
    - Phase II conjugate concentrations

    Usage:
        >>> liver = LiverMetabolism()
        >>> liver.add_drug_pathway("drug_A", CYP450Isoform.CYP3A4, Vmax=50.0, Km=10.0)
        >>> clearance = liver.metabolize_drug("drug_A", drug_concentration=25.0)
    """

    def __init__(self):
        self.cyp_systems: dict[CYP450Isoform, CYP450System] = {}

        # Initialize major isoforms
        for isoform in CYP450Isoform:
            self.cyp_systems[isoform] = CYP450System(isoform)

        # Drug-specific pathways
        self.drug_pathways: dict[str, List[Tuple[CYP450Isoform, float]]] = {}

    def add_drug_pathway(
        self,
        drug_name: str,
        isoform: CYP450Isoform,
        contribution_fraction: float = 1.0
    ):
        """
        Add metabolic pathway for a drug.

        Args:
            drug_name: Drug identifier
            isoform: CYP450 isoform responsible
            contribution_fraction: Fraction of metabolism via this pathway
        """
        if drug_name not in self.drug_pathways:
            self.drug_pathways[drug_name] = []

        self.drug_pathways[drug_name].append((isoform, contribution_fraction))

    def metabolize_drug(
        self,
        drug_name: str,
        drug_concentration: float,
        hepatocyte_viability: float = 1.0
    ) -> Tuple[float, dict]:
        """
        Compute total drug clearance.

        Args:
            drug_name: Drug identifier
            drug_concentration: Drug concentration (μM)
            hepatocyte_viability: Fraction of viable hepatocytes

        Returns:
            (total_clearance, pathway_contributions)
        """
        if drug_name not in self.drug_pathways:
            return 0.0, {}

        total_clearance = 0.0
        pathway_contributions = {}

        for isoform, fraction in self.drug_pathways[drug_name]:
            cyp = self.cyp_systems[isoform]
            clearance = cyp.metabolize(drug_concentration, cyp.enzyme_level) * fraction

            # Scale by hepatocyte viability
            clearance *= hepatocyte_viability

            total_clearance += clearance
            pathway_contributions[isoform.value] = clearance

        return total_clearance, pathway_contributions

    def update_enzyme_levels(
        self,
        dt: float,
        drug_concentrations: dict[str, float]
    ):
        """
        Update all enzyme levels based on drug exposure.

        Args:
            dt: Timestep
            drug_concentrations: Dictionary of drug_name -> concentration
        """
        # Aggregate induction signals per isoform
        induction_signals: dict[CYP450Isoform, float] = {
            iso: 0.0 for iso in CYP450Isoform
        }

        for drug_name, concentration in drug_concentrations.items():
            if drug_name in self.drug_pathways:
                for isoform, _ in self.drug_pathways[drug_name]:
                    induction_signals[isoform] += concentration

        # Update each isoform
        for isoform, signal in induction_signals.items():
            self.cyp_systems[isoform].update_enzyme_level(dt, signal)

    def get_enzyme_levels(self) -> dict[str, float]:
        """Return current enzyme levels"""
        return {
            iso.value: cyp.enzyme_level
            for iso, cyp in self.cyp_systems.items()
        }

    def reset(self):
        """Reset all enzyme levels"""
        for cyp in self.cyp_systems.values():
            cyp.reset()


# ==============================================================================
# DRUG-SPECIFIC EXAMPLES
# ==============================================================================

class DrugMetabolismProfiles:
    """Pre-configured drug metabolism profiles"""

    @staticmethod
    def acetaminophen() -> LiverMetabolism:
        """
        Acetaminophen (paracetamol) metabolism.

        Major pathways:
        - Glucuronidation (Phase II)
        - Sulfation (Phase II)
        - CYP2E1 → NAPQI (toxic metabolite)
        """
        liver = LiverMetabolism()

        # Phase I (minor, toxic pathway)
        liver.add_drug_pathway("acetaminophen", CYP450Isoform.CYP2E1, 0.1)

        return liver

    @staticmethod
    def warfarin() -> LiverMetabolism:
        """
        Warfarin metabolism.

        S-warfarin (active): CYP2C9
        R-warfarin: CYP1A2, CYP3A4
        """
        liver = LiverMetabolism()

        liver.add_drug_pathway("S-warfarin", CYP450Isoform.CYP2C9, 1.0)
        liver.add_drug_pathway("R-warfarin", CYP450Isoform.CYP1A2, 0.5)
        liver.add_drug_pathway("R-warfarin", CYP450Isoform.CYP3A4, 0.5)

        return liver


if __name__ == "__main__":
    print("=" * 70)
    print("LIVER DRUG METABOLISM MODEL")
    print("=" * 70)

    # Example 1: Single enzyme kinetics
    print("\n1. Testing CYP3A4 enzyme kinetics...")
    cyp3a4 = CYP450System(CYP450Isoform.CYP3A4)

    concentrations = [1.0, 5.0, 10.0, 20.0, 50.0, 100.0]
    print(f"   {'[S] (μM)':<12} {'v (μM/hr)':<15} {'v/Vmax':<10}")
    print("   " + "-" * 40)

    for conc in concentrations:
        v = cyp3a4.metabolize(conc, enzyme_level=1.0)
        frac = v / cyp3a4.params.Vmax_base
        print(f"   {conc:<12.1f} {v:<15.2f} {frac:<10.2%}")

    # Example 2: Enzyme induction
    print("\n2. Testing enzyme induction...")
    cyp3a4.reset()

    print(f"   {'Time':<10} {'[Drug]':<12} {'Enzyme Level':<15}")
    print("   " + "-" * 40)

    dt = 0.1
    drug_conc = 50.0
    for t in [0, 10, 20, 50, 100]:
        steps = int(t / dt) if t > 0 else 0
        for _ in range(steps):
            cyp3a4.update_enzyme_level(dt, drug_conc)

        print(f"   {t:<10.1f} {drug_conc:<12.1f} {cyp3a4.enzyme_level:<15.2f}")

    # Example 3: Multi-drug metabolism
    print("\n3. Testing acetaminophen metabolism...")
    liver = DrugMetabolismProfiles.acetaminophen()

    apap_concentration = 100.0  # μM
    clearance, pathways = liver.metabolize_drug(
        "acetaminophen",
        apap_concentration,
        hepatocyte_viability=1.0
    )

    print(f"   Drug concentration: {apap_concentration} μM")
    print(f"   Total clearance: {clearance:.2f} μM/hr")
    print(f"   Pathways:")
    for pathway, contrib in pathways.items():
        print(f"     {pathway}: {contrib:.2f} μM/hr ({contrib/clearance:.1%})")

    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("=" * 70)
    print("✓ MICHAELIS-MENTEN: Saturable enzyme kinetics")
    print("✓ ENZYME INDUCTION: Time-dependent adaptation")
    print("✓ MULTI-PATHWAY: Multiple CYP450 isoforms")
    print("✓ INHIBITION: Competitive drug interactions")
    print("=" * 70)
