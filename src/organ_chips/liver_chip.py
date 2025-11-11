"""
Liver-on-Chip Module

Implements hepatocyte populations, liver metabolism, and hepatotoxicity
within the RPO framework for drug testing and digital twin applications.

Key Features:
- Hepatocyte cell population dynamics
- Drug metabolism (Phase I and Phase II)
- Cytochrome P450 enzyme systems
- Bile acid synthesis and transport
- Hepatotoxicity mechanisms (acetaminophen, alcohol, etc.)
- Liver function markers (ALT, AST, bilirubin)

Author: Multi-Organ Chip Architecture Team
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .rpo_organ_chip import (
    OrganChip,
    CellPopulation,
    Receptor,
    ReceptorType,
    Ligand,
    ToxicityMechanism,
    CellularStress,
    SignalTransduction,
    ProteinExpression,
)


@dataclass
class CytochromeP450:
    """
    Cytochrome P450 enzyme system for drug metabolism

    Models Phase I metabolism: Drug → Metabolite + ROS
    """
    isoform: str  # e.g., CYP3A4, CYP2D6, CYP2C9
    activity: float = 1.0  # relative activity
    km: float = 10.0  # μM, Michaelis constant
    vmax: float = 100.0  # μM/h, maximum velocity
    expression: float = 1.0  # relative expression level

    # Drug-specific parameters
    substrate_affinity: Dict[str, float] = field(default_factory=dict)

    def metabolize(self, drug_concentration: float, drug_name: str, dt: float) -> tuple[float, float]:
        """
        Metabolize drug via Michaelis-Menten kinetics

        Returns: (metabolized_amount, ROS_produced)
        """
        affinity = self.substrate_affinity.get(drug_name, 1.0)
        effective_vmax = self.vmax * self.activity * self.expression * affinity

        # Michaelis-Menten kinetics
        rate = effective_vmax * drug_concentration / (self.km + drug_concentration)
        metabolized = rate * dt

        # ROS production (uncoupling)
        ros_production = metabolized * 0.1  # 10% uncoupling rate

        return metabolized, ros_production


@dataclass
class PhaseIIEnzyme:
    """
    Phase II conjugation enzymes

    Models conjugation reactions: Metabolite + Cofactor → Conjugate
    """
    enzyme_type: str  # e.g., UGT, SULT, GST
    activity: float = 1.0
    cofactor_level: float = 1.0  # e.g., glucuronic acid, sulfate, glutathione

    def conjugate(self, metabolite_concentration: float, dt: float) -> float:
        """Conjugate metabolite for excretion"""
        rate = self.activity * self.cofactor_level * metabolite_concentration
        conjugated = rate * dt * 10.0
        return conjugated


@dataclass
class LiverMetabolism:
    """
    Comprehensive liver metabolism model
    """
    # Phase I enzymes
    cyp3a4: CytochromeP450 = field(default_factory=lambda: CytochromeP450(
        isoform="CYP3A4", vmax=150.0, km=15.0
    ))
    cyp2d6: CytochromeP450 = field(default_factory=lambda: CytochromeP450(
        isoform="CYP2D6", vmax=80.0, km=5.0
    ))
    cyp2c9: CytochromeP450 = field(default_factory=lambda: CytochromeP450(
        isoform="CYP2C9", vmax=100.0, km=10.0
    ))
    cyp1a2: CytochromeP450 = field(default_factory=lambda: CytochromeP450(
        isoform="CYP1A2", vmax=70.0, km=12.0
    ))

    # Phase II enzymes
    ugt: PhaseIIEnzyme = field(default_factory=lambda: PhaseIIEnzyme(
        enzyme_type="UGT", activity=1.0
    ))
    gst: PhaseIIEnzyme = field(default_factory=lambda: PhaseIIEnzyme(
        enzyme_type="GST", activity=1.0
    ))
    sult: PhaseIIEnzyme = field(default_factory=lambda: PhaseIIEnzyme(
        enzyme_type="SULT", activity=1.0
    ))

    # Metabolite tracking
    phase1_metabolites: Dict[str, float] = field(default_factory=dict)
    phase2_conjugates: Dict[str, float] = field(default_factory=dict)
    reactive_metabolites: float = 0.0  # toxic intermediates

    # Energy metabolism
    glucose_consumption: float = 0.0
    lactate_production: float = 0.0
    oxygen_consumption: float = 0.0

    # Bile acids
    bile_acid_synthesis: float = 1.0
    bile_acid_level: float = 5.0  # μM

    def metabolize_drug(self, drug: Ligand, dt: float) -> tuple[float, float]:
        """
        Complete drug metabolism (Phase I + Phase II)

        Returns: (total_clearance, ROS_production)
        """
        total_metabolized = 0.0
        total_ros = 0.0

        # Phase I metabolism by multiple CYPs
        for cyp in [self.cyp3a4, self.cyp2d6, self.cyp2c9, self.cyp1a2]:
            metabolized, ros = cyp.metabolize(
                drug.concentration,
                drug.name,
                dt
            )
            total_metabolized += metabolized
            total_ros += ros

            # Track metabolites
            metabolite_name = f"{drug.name}_M{cyp.isoform}"
            if metabolite_name not in self.phase1_metabolites:
                self.phase1_metabolites[metabolite_name] = 0.0
            self.phase1_metabolites[metabolite_name] += metabolized

        # Some metabolites are reactive (toxic)
        if "acetaminophen" in drug.name.lower():
            # NAPQI formation
            self.reactive_metabolites += total_metabolized * 0.05

        # Phase II conjugation
        for metabolite_name, metabolite_conc in self.phase1_metabolites.items():
            conjugated = self.ugt.conjugate(metabolite_conc, dt)
            conjugated += self.gst.conjugate(metabolite_conc, dt)
            conjugated += self.sult.conjugate(metabolite_conc, dt)

            self.phase1_metabolites[metabolite_name] = max(0, metabolite_conc - conjugated)

            if metabolite_name not in self.phase2_conjugates:
                self.phase2_conjugates[metabolite_name] = 0.0
            self.phase2_conjugates[metabolite_name] += conjugated

        return total_metabolized, total_ros

    def update_energy_metabolism(self, stress_level: float, dt: float) -> None:
        """Update hepatocyte energy metabolism"""
        # Glucose consumption increases with stress
        self.glucose_consumption = 1.0 + stress_level * 0.5

        # Oxygen consumption
        self.oxygen_consumption = 0.8 + stress_level * 0.3

        # Lactate production (anaerobic metabolism under stress)
        self.lactate_production = stress_level * 0.4

    def update_bile_synthesis(self, dt: float) -> None:
        """Update bile acid synthesis"""
        # Bile acid synthesis from cholesterol
        synthesis_rate = 0.1 * self.cyp3a4.activity
        self.bile_acid_level += synthesis_rate * dt

        # Bile secretion
        secretion_rate = 0.08
        self.bile_acid_level -= secretion_rate * self.bile_acid_level * dt


@dataclass
class HepatocytePopulation(CellPopulation):
    """
    Hepatocyte cell population with liver-specific functions
    """
    metabolism: LiverMetabolism = field(default_factory=LiverMetabolism)

    # Hepatocyte-specific receptors
    bile_acid_receptor: Optional[Receptor] = None  # FXR
    ppar_alpha: Optional[Receptor] = None  # lipid metabolism
    ahr: Optional[Receptor] = None  # aryl hydrocarbon receptor

    # Liver function markers
    alt: float = 20.0  # ALT (U/L) - normal range
    ast: float = 25.0  # AST (U/L)
    alp: float = 50.0  # Alkaline phosphatase
    bilirubin: float = 0.5  # mg/dL

    # Synthetic function
    albumin: float = 4.0  # g/dL
    clotting_factors: float = 1.0  # relative level

    def __post_init__(self):
        """Initialize hepatocyte-specific receptors"""
        super().__post_init__() if hasattr(super(), '__post_init__') else None

        # Bile acid receptor (FXR)
        self.bile_acid_receptor = Receptor(
            name="FXR",
            receptor_type=ReceptorType.NUCLEAR,
            total_density=5000.0,
            k_on=1e5,
            k_off=0.01
        )
        self.add_receptor(self.bile_acid_receptor)

        # PPAR-alpha (fatty acid metabolism)
        self.ppar_alpha = Receptor(
            name="PPAR_alpha",
            receptor_type=ReceptorType.NUCLEAR,
            total_density=3000.0,
            k_on=5e4,
            k_off=0.05
        )
        self.add_receptor(self.ppar_alpha)

    def update_liver_markers(self, dt: float) -> None:
        """Update liver function test markers"""
        viability = self.stress.viability()
        damage = 1.0 - viability

        # ALT and AST increase with hepatocyte damage
        self.alt += (damage * 100.0 - 0.1 * self.alt) * dt
        self.ast += (damage * 80.0 - 0.1 * self.ast) * dt

        # ALP increases with cholestasis
        bile_stress = max(0, self.metabolism.bile_acid_level - 5.0)
        self.alp += (bile_stress * 20.0 - 0.05 * self.alp) * dt

        # Bilirubin increases with liver damage
        self.bilirubin += (damage * 2.0 - 0.1 * self.bilirubin) * dt

        # Synthetic function decreases with damage
        self.albumin = 4.0 * viability
        self.clotting_factors = 1.0 * viability

    def metabolize_drug(self, drug: Ligand, dt: float) -> None:
        """Process drug through hepatocyte metabolism"""
        clearance, ros_production = self.metabolism.metabolize_drug(drug, dt)

        # Drug concentration decreases
        drug.concentration = max(0, drug.concentration - clearance)

        # ROS causes oxidative stress
        toxicity_signals = {
            ToxicityMechanism.OXIDATIVE_STRESS: ros_production
        }

        # Reactive metabolites cause additional toxicity
        if self.metabolism.reactive_metabolites > 0:
            # NAPQI depletes glutathione
            gsh_depletion = min(self.gsh_level, self.metabolism.reactive_metabolites * 0.1)
            self.gsh_level -= gsh_depletion * dt

            # If glutathione depleted, direct cellular damage
            if self.gsh_level < 0.3:
                toxicity_signals[ToxicityMechanism.MITOCHONDRIAL_DYSFUNCTION] = \
                    self.metabolism.reactive_metabolites * 2.0
                toxicity_signals[ToxicityMechanism.PROTEIN_MISFOLDING] = \
                    self.metabolism.reactive_metabolites * 1.5

        self.stress.update(toxicity_signals, dt)

    def update(self, dt: float) -> None:
        """Update hepatocyte population with metabolism"""
        super().update(dt)

        # Update metabolism
        self.metabolism.update_energy_metabolism(self.stress.total_stress(), dt)
        self.metabolism.update_bile_synthesis(dt)

        # Update liver markers
        self.update_liver_markers(dt)

        # Reactive metabolite clearance
        self.metabolism.reactive_metabolites *= np.exp(-0.5 * dt)


class LiverChip(OrganChip):
    """
    Liver-on-chip with multiple cell types and metabolic functions
    """

    def __init__(self):
        super().__init__(organ_name="liver")

        # Liver tissue properties
        self.tissue_properties = {
            'mass': 1500.0,  # grams (typical adult liver)
            'blood_flow': 1500.0,  # mL/min
            'oxygen_extraction': 0.35,
            'albumin_synthesis': 12.0,  # g/day
        }

        # Create hepatocyte population (80% of liver cells)
        self.hepatocytes = HepatocytePopulation(
            cell_type="hepatocyte",
            cell_count=2.4e11  # ~240 billion hepatocytes
        )
        self.add_cell_population(self.hepatocytes)

        # Kupffer cells (liver macrophages) - could be added
        # Stellate cells - could be added for fibrosis modeling
        # Endothelial cells - could be added for vascular function

    def apply_drug(self, drug: Ligand, dt: float = 0.01) -> None:
        """
        Apply drug to liver chip and metabolize

        Args:
            drug: Drug to apply
            dt: Time step for metabolism
        """
        # Hepatocyte metabolism
        self.hepatocytes.metabolize_drug(drug, dt)

        # First-pass extraction
        extraction_ratio = 0.3  # typical hepatic extraction
        drug.concentration *= (1.0 - extraction_ratio * dt)

    def get_liver_function_tests(self) -> Dict[str, float]:
        """
        Get liver function test results

        Returns standard clinical markers
        """
        return {
            'ALT': self.hepatocytes.alt,
            'AST': self.hepatocytes.ast,
            'ALP': self.hepatocytes.alp,
            'bilirubin': self.hepatocytes.bilirubin,
            'albumin': self.hepatocytes.albumin,
            'PT_INR': 2.0 - self.hepatocytes.clotting_factors,  # INR increases with dysfunction
        }

    def get_metabolic_state(self) -> Dict[str, float]:
        """Get current metabolic state"""
        return {
            'glucose_consumption': self.hepatocytes.metabolism.glucose_consumption,
            'oxygen_consumption': self.hepatocytes.metabolism.oxygen_consumption,
            'lactate_production': self.hepatocytes.metabolism.lactate_production,
            'bile_acid_level': self.hepatocytes.metabolism.bile_acid_level,
            'gsh_level': self.hepatocytes.gsh_level,
            'reactive_metabolites': self.hepatocytes.metabolism.reactive_metabolites,
        }

    def assess_hepatotoxicity(self) -> Dict[str, any]:
        """
        Assess drug-induced liver injury

        Returns clinical-grade hepatotoxicity assessment
        """
        lfts = self.get_liver_function_tests()
        viability = self.get_viability()

        # DILI classification (Drug-Induced Liver Injury)
        alt_elevation = lfts['ALT'] / 40.0  # fold change from normal (40 U/L)
        alp_elevation = lfts['ALP'] / 120.0  # fold change from normal (120 U/L)

        # R-value for DILI classification
        r_value = alt_elevation / alp_elevation if alp_elevation > 0 else 0

        # Classify injury pattern
        if r_value >= 5:
            injury_pattern = "Hepatocellular"
        elif r_value <= 2:
            injury_pattern = "Cholestatic"
        else:
            injury_pattern = "Mixed"

        # Severity assessment
        if alt_elevation < 3:
            severity = "Normal"
        elif alt_elevation < 5:
            severity = "Mild"
        elif alt_elevation < 10:
            severity = "Moderate"
        else:
            severity = "Severe"

        return {
            'injury_pattern': injury_pattern,
            'severity': severity,
            'R_value': r_value,
            'ALT_fold_elevation': alt_elevation,
            'ALP_fold_elevation': alp_elevation,
            'viability': viability,
            'oxidative_stress': self.hepatocytes.stress.oxidative_stress,
            'mitochondrial_damage': self.hepatocytes.stress.mitochondrial_damage,
        }


# Specific hepatotoxicity models
class LiverToxicity:
    """
    Models for specific hepatotoxic drugs
    """

    @staticmethod
    def acetaminophen_toxicity(liver_chip: LiverChip, dose_mg_kg: float, duration_hours: float, dt: float = 0.1):
        """
        Model acetaminophen (paracetamol) hepatotoxicity

        Mechanism: CYP2E1 → NAPQI → GSH depletion → hepatocyte necrosis
        Therapeutic dose: 10-15 mg/kg
        Toxic dose: >150 mg/kg (7.5g in 70kg adult)
        """
        # Convert dose to concentration (simplified)
        concentration_uM = dose_mg_kg * 70 / 151.16 * 1000  # MW of acetaminophen = 151.16

        drug = Ligand(
            name="acetaminophen",
            concentration=concentration_uM,
            molecular_weight=151.16,
            clearance_rate=0.25,  # per hour
        )

        # Enhanced CYP2E1 activity for NAPQI formation
        liver_chip.hepatocytes.metabolism.cyp2d6.substrate_affinity["acetaminophen"] = 2.0

        # Simulate over time
        steps = int(duration_hours * 3600 / dt)
        results = []

        for step in range(steps):
            liver_chip.apply_drug(drug, dt=dt)
            liver_chip.update(dt)

            if step % 100 == 0:
                state = liver_chip.get_state()
                state['drug_concentration'] = drug.concentration
                state['liver_function'] = liver_chip.get_liver_function_tests()
                state['toxicity_assessment'] = liver_chip.assess_hepatotoxicity()
                results.append(state)

        return results

    @staticmethod
    def alcohol_toxicity(liver_chip: LiverChip, alcohol_concentration: float, duration_hours: float, dt: float = 0.1):
        """
        Model alcohol-induced liver injury

        Mechanism: Alcohol → Acetaldehyde → ROS + lipid peroxidation
        """
        ethanol = Ligand(
            name="ethanol",
            concentration=alcohol_concentration,  # mM
            molecular_weight=46.07,
            clearance_rate=0.15,
        )

        # Simulate chronic exposure
        steps = int(duration_hours * 3600 / dt)
        results = []

        for step in range(steps):
            # Ethanol metabolism produces ROS
            metabolism_rate = 0.1 * ethanol.concentration
            ros_production = metabolism_rate * 0.5

            # Apply toxicity
            toxicity = {
                ToxicityMechanism.OXIDATIVE_STRESS: ros_production,
                ToxicityMechanism.MITOCHONDRIAL_DYSFUNCTION: metabolism_rate * 0.3
            }
            liver_chip.hepatocytes.stress.update(toxicity, dt)

            # Ethanol clearance
            ethanol.concentration *= np.exp(-0.15 * dt / 3600)

            liver_chip.update(dt)

            if step % 100 == 0:
                results.append(liver_chip.get_state())

        return results


if __name__ == "__main__":
    # Example: Acetaminophen toxicity simulation
    print("Liver-on-Chip: Acetaminophen Hepatotoxicity Simulation")
    print("=" * 70)

    liver = LiverChip()

    # Simulate therapeutic dose
    print("\n1. Therapeutic dose (15 mg/kg):")
    results_therapeutic = LiverToxicity.acetaminophen_toxicity(
        liver, dose_mg_kg=15, duration_hours=2.0, dt=0.1
    )
    final_state = results_therapeutic[-1]
    print(f"   Viability: {final_state['viability']:.3f}")
    print(f"   Severity: {final_state['toxicity_assessment']['severity']}")
    print(f"   ALT: {final_state['liver_function']['ALT']:.1f} U/L")

    # Reset liver
    liver = LiverChip()

    # Simulate toxic dose
    print("\n2. Toxic dose (200 mg/kg):")
    results_toxic = LiverToxicity.acetaminophen_toxicity(
        liver, dose_mg_kg=200, duration_hours=2.0, dt=0.1
    )
    final_state = results_toxic[-1]
    print(f"   Viability: {final_state['viability']:.3f}")
    print(f"   Severity: {final_state['toxicity_assessment']['severity']}")
    print(f"   ALT: {final_state['liver_function']['ALT']:.1f} U/L")
    print(f"   Injury pattern: {final_state['toxicity_assessment']['injury_pattern']}")

    print("\nLiver chip module ready for integration!")
