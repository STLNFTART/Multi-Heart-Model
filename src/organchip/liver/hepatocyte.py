"""Hepatocyte dynamics, drug metabolism, and hepatotoxicity models.

This module implements:
- Phase I and Phase II drug metabolism
- Michaelis-Menten enzyme kinetics
- Reactive metabolite formation
- Hepatocellular injury and biomarkers
- Mitochondrial dysfunction
- Oxidative stress and glutathione depletion
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Dict, List
import math


@dataclass
class HepatocyteParameters:
    """Parameters for hepatocyte metabolism and toxicity.

    Attributes
    ----------
    Vmax_phase1 : float
        Maximum velocity for Phase I metabolism (μM/h)
    Km_phase1 : float
        Michaelis constant for Phase I (μM)
    Vmax_phase2 : float
        Maximum velocity for Phase II conjugation (μM/h)
    Km_phase2 : float
        Michaelis constant for Phase II (μM)
    GSH_total : float
        Total glutathione pool (mM)
    ATP_baseline : float
        Baseline ATP concentration (mM)
    """

    # Phase I metabolism (CYP450)
    Vmax_phase1: float = 100.0  # μM/h
    Km_phase1: float = 50.0      # μM

    # Phase II conjugation
    Vmax_phase2: float = 150.0   # μM/h
    Km_phase2: float = 30.0      # μM

    # Cellular energy and redox
    GSH_total: float = 10.0      # mM - total glutathione
    ATP_baseline: float = 5.0    # mM

    # Toxicity thresholds
    GSH_critical: float = 2.0    # mM - critical GSH level
    ROS_threshold: float = 1.0   # mM - reactive oxygen species threshold


@dataclass
class LiverMetabolism:
    """Mechanistic model of hepatic drug metabolism.

    Models:
    - Phase I oxidative metabolism (CYP450-mediated)
    - Phase II conjugation (glucuronidation, sulfation, GSH conjugation)
    - Reactive metabolite formation
    - Enzyme induction and inhibition
    """

    params: HepatocyteParameters = field(default_factory=HepatocyteParameters)

    # Metabolic pathway fractions
    frac_phase1_to_metabolite: float = 0.8   # Fraction going to stable metabolite
    frac_phase1_to_reactive: float = 0.2     # Fraction forming reactive metabolite

    def michaelis_menten(self, substrate: float, Vmax: float, Km: float) -> float:
        """Michaelis-Menten enzyme kinetics.

        Parameters
        ----------
        substrate : float
            Substrate concentration (μM)
        Vmax : float
            Maximum reaction velocity (μM/h)
        Km : float
            Michaelis constant (μM)

        Returns
        -------
        float
            Reaction rate (μM/h)
        """
        return Vmax * substrate / (Km + substrate)

    def phase1_metabolism(self, drug_conc: float, inhibition: float = 0.0) -> Tuple[float, float]:
        """Phase I oxidative metabolism.

        Parameters
        ----------
        drug_conc : float
            Parent drug concentration (μM)
        inhibition : float
            Fractional inhibition [0, 1]

        Returns
        -------
        tuple
            (metabolite_formation_rate, reactive_formation_rate) in μM/h
        """
        # Effective Vmax accounting for inhibition
        Vmax_eff = self.params.Vmax_phase1 * (1.0 - inhibition)

        total_rate = self.michaelis_menten(drug_conc, Vmax_eff, self.params.Km_phase1)

        metabolite_rate = total_rate * self.frac_phase1_to_metabolite
        reactive_rate = total_rate * self.frac_phase1_to_reactive

        return metabolite_rate, reactive_rate

    def phase2_conjugation(self, metabolite_conc: float, GSH_available: float) -> float:
        """Phase II conjugation metabolism.

        Parameters
        ----------
        metabolite_conc : float
            Metabolite concentration (μM)
        GSH_available : float
            Available glutathione (mM)

        Returns
        -------
        float
            Conjugation rate (μM/h)
        """
        # GSH availability modulates conjugation capacity
        GSH_factor = GSH_available / self.params.GSH_total

        Vmax_eff = self.params.Vmax_phase2 * GSH_factor

        return self.michaelis_menten(metabolite_conc, Vmax_eff, self.params.Km_phase2)

    def derivatives(
        self,
        t: float,
        state: Tuple[float, float, float, float],
        drug_input: float = 0.0
    ) -> Tuple[float, float, float, float]:
        """Compute derivatives for drug metabolism system.

        State variables:
        - Drug: Parent drug concentration (μM)
        - Metabolite: Phase I metabolite (μM)
        - Reactive: Reactive metabolite (μM)
        - Conjugate: Phase II conjugated product (μM)

        Parameters
        ----------
        t : float
            Time (hours)
        state : tuple
            (Drug, Metabolite, Reactive, Conjugate)
        drug_input : float
            Drug input rate (μM/h)

        Returns
        -------
        tuple
            Time derivatives
        """
        Drug, Metabolite, Reactive, Conjugate = state

        # Phase I metabolism
        metabolite_formation, reactive_formation = self.phase1_metabolism(Drug)

        # Phase II conjugation
        conjugation_rate = self.phase2_conjugation(
            Metabolite,
            GSH_available=self.params.GSH_total * 0.8  # Simplified
        )

        # Reactive metabolite detoxification (GSH conjugation)
        reactive_detox = self.michaelis_menten(Reactive, 50.0, 10.0)

        # Drug dynamics
        dDrug = drug_input - metabolite_formation - reactive_formation

        # Metabolite dynamics
        dMetabolite = metabolite_formation - conjugation_rate

        # Reactive metabolite dynamics
        dReactive = reactive_formation - reactive_detox

        # Conjugate dynamics (excretion)
        excretion_rate = 0.5  # 1/h
        dConjugate = conjugation_rate + reactive_detox - excretion_rate * Conjugate

        return dDrug, dMetabolite, dReactive, dConjugate


@dataclass
class LiverToxicity:
    """Hepatotoxicity model with cellular injury mechanisms.

    Models:
    - Reactive metabolite-induced toxicity
    - Mitochondrial dysfunction
    - Oxidative stress and GSH depletion
    - Hepatocellular injury biomarkers (ALT, AST)
    - Cell death pathways
    """

    params: HepatocyteParameters = field(default_factory=HepatocyteParameters)
    metabolism: LiverMetabolism = field(default_factory=LiverMetabolism)

    # Toxicity rate constants
    k_reactive_damage: float = 0.1    # 1/(μM·h)
    k_GSH_consumption: float = 0.05   # 1/(μM·h)
    k_GSH_synthesis: float = 1.0      # mM/h
    k_ATP_depletion: float = 0.02     # 1/h
    k_ROS_generation: float = 0.01    # mM/(μM·h)

    def derivatives(
        self,
        t: float,
        state: Tuple[float, float, float, float, float, float],
        reactive_metabolite: float = 0.0
    ) -> Tuple[float, float, float, float, float, float]:
        """Compute derivatives for hepatotoxicity model.

        State variables:
        - GSH: Reduced glutathione (mM)
        - ATP: Cellular ATP (mM)
        - ROS: Reactive oxygen species (mM)
        - Cell_viability: Cell viability fraction [0, 1]
        - ALT: Alanine transaminase (U/L)
        - AST: Aspartate transaminase (U/L)

        Parameters
        ----------
        t : float
            Time (hours)
        state : tuple
            (GSH, ATP, ROS, Cell_viability, ALT, AST)
        reactive_metabolite : float
            Reactive metabolite concentration (μM)

        Returns
        -------
        tuple
            Time derivatives
        """
        GSH, ATP, ROS, Cell_viability, ALT, AST = state
        p = self.params

        # Glutathione dynamics
        GSH_consumption = self.k_GSH_consumption * reactive_metabolite * GSH
        GSH_synthesis = self.k_GSH_synthesis * (1.0 - GSH / p.GSH_total)
        dGSH = GSH_synthesis - GSH_consumption

        # ROS generation from reactive metabolites and mitochondrial dysfunction
        ROS_generation = self.k_ROS_generation * reactive_metabolite
        ROS_scavenging = 0.5 * ROS * (GSH / p.GSH_total)  # GSH-dependent
        dROS = ROS_generation - ROS_scavenging

        # ATP depletion from mitochondrial damage
        ATP_damage_factor = 1.0 + self.k_ATP_depletion * ROS
        ATP_synthesis = 2.0 * (1.0 - ROS / 5.0) if ROS < 5.0 else 0.0
        dATP = ATP_synthesis - ATP_damage_factor * ATP

        # Cell viability (decreases with GSH depletion and ATP loss)
        GSH_stress = max(0.0, (p.GSH_critical - GSH) / p.GSH_critical)
        ATP_stress = max(0.0, (p.ATP_baseline - ATP) / p.ATP_baseline)
        ROS_stress = max(0.0, (ROS - p.ROS_threshold) / p.ROS_threshold)

        cell_death_rate = 0.01 * (GSH_stress + ATP_stress + ROS_stress) * Cell_viability
        dCell_viability = -cell_death_rate

        # Liver enzyme release (ALT, AST) - markers of hepatocellular injury
        enzyme_release_rate = 100.0 * cell_death_rate
        enzyme_clearance = 0.2  # 1/h

        dALT = enzyme_release_rate - enzyme_clearance * ALT
        dAST = enzyme_release_rate * 1.5 - enzyme_clearance * AST  # AST higher in severe injury

        return dGSH, dATP, dROS, dCell_viability, dALT, dAST

    def assess_hepatotoxicity(
        self,
        GSH: float,
        ATP: float,
        ALT: float,
        AST: float,
        cell_viability: float
    ) -> Dict[str, any]:
        """Assess hepatotoxicity severity.

        Parameters
        ----------
        GSH : float
            Glutathione level (mM)
        ATP : float
            ATP level (mM)
        ALT : float
            ALT level (U/L)
        AST : float
            AST level (U/L)
        cell_viability : float
            Cell viability fraction

        Returns
        -------
        dict
            Toxicity assessment with severity scores
        """
        # Normal ranges
        ALT_normal = 40.0  # U/L
        AST_normal = 40.0  # U/L

        # Calculate severity scores
        GSH_depletion_score = max(0.0, 1.0 - GSH / self.params.GSH_total)
        ATP_depletion_score = max(0.0, 1.0 - ATP / self.params.ATP_baseline)
        ALT_elevation_score = max(0.0, min(1.0, (ALT - ALT_normal) / (10 * ALT_normal)))
        AST_elevation_score = max(0.0, min(1.0, (AST - AST_normal) / (10 * AST_normal)))
        cell_death_score = 1.0 - cell_viability

        # Overall toxicity score (weighted average)
        toxicity_score = (
            0.2 * GSH_depletion_score +
            0.2 * ATP_depletion_score +
            0.2 * ALT_elevation_score +
            0.2 * AST_elevation_score +
            0.2 * cell_death_score
        )

        # Severity classification
        if toxicity_score < 0.2:
            severity = "None"
        elif toxicity_score < 0.4:
            severity = "Mild"
        elif toxicity_score < 0.6:
            severity = "Moderate"
        elif toxicity_score < 0.8:
            severity = "Severe"
        else:
            severity = "Critical"

        return {
            "toxicity_score": toxicity_score,
            "severity": severity,
            "GSH_depletion": GSH_depletion_score,
            "ATP_depletion": ATP_depletion_score,
            "ALT_elevation_fold": ALT / ALT_normal,
            "AST_elevation_fold": AST / AST_normal,
            "cell_viability": cell_viability,
        }


@dataclass
class Hepatocyte:
    """Integrated hepatocyte model combining metabolism and toxicity.

    Complete cell model including:
    - Drug uptake and efflux
    - Metabolic pathways
    - Toxicity mechanisms
    - Biomarker release
    """

    metabolism: LiverMetabolism = field(default_factory=LiverMetabolism)
    toxicity: LiverToxicity = field(default_factory=LiverToxicity)

    # Transport parameters
    uptake_clearance: float = 10.0   # μL/min
    efflux_clearance: float = 5.0    # μL/min

    def integrated_derivatives(
        self,
        t: float,
        state: Tuple[float, ...],
        extracellular_drug: float = 0.0
    ) -> Tuple[float, ...]:
        """Compute derivatives for integrated hepatocyte model.

        State (10 variables):
        - Drug_intra: Intracellular drug (μM)
        - Metabolite, Reactive, Conjugate: Metabolic products (μM)
        - GSH, ATP, ROS: Cellular health markers
        - Cell_viability, ALT, AST: Toxicity markers

        Parameters
        ----------
        t : float
            Time (hours)
        state : tuple
            Full state vector
        extracellular_drug : float
            Extracellular drug concentration (μM)

        Returns
        -------
        tuple
            Time derivatives
        """
        if len(state) != 10:
            raise ValueError(f"Expected 10 state variables, got {len(state)}")

        Drug_intra = state[0]
        metab_state = state[0:4]  # Drug, Metabolite, Reactive, Conjugate
        tox_state = state[4:10]   # GSH, ATP, ROS, Cell_viability, ALT, AST

        # Drug transport
        uptake = self.uptake_clearance * extracellular_drug / 60.0  # Convert min to hours
        efflux = self.efflux_clearance * Drug_intra / 60.0

        # Metabolism
        metab_derivs = self.metabolism.derivatives(t, metab_state, drug_input=0.0)

        # Toxicity (driven by reactive metabolite)
        Reactive = state[2]
        tox_derivs = self.toxicity.derivatives(t, tox_state, reactive_metabolite=Reactive)

        # Update drug derivative with transport
        dDrug_intra = metab_derivs[0] + uptake - efflux

        # Combine all derivatives
        return (dDrug_intra,) + metab_derivs[1:] + tox_derivs
