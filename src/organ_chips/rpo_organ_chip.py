"""
Enhanced Receptor-Protein-Organ (RPO) Framework for Organ-on-Chip Systems

This module implements a comprehensive RPO framework that models:
- Receptor-ligand binding dynamics
- Signal transduction pathways
- Protein expression and regulation
- Organ-level responses
- Drug-induced toxicity mechanisms

Author: Multi-Organ Chip Architecture Team
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum


class ReceptorType(Enum):
    """Types of cellular receptors"""
    GPCR = "G-protein coupled receptor"
    TYROSINE_KINASE = "Tyrosine kinase receptor"
    NUCLEAR = "Nuclear receptor"
    ION_CHANNEL = "Ion channel receptor"
    CYTOKINE = "Cytokine receptor"


class ToxicityMechanism(Enum):
    """Drug toxicity mechanisms"""
    OXIDATIVE_STRESS = "Oxidative stress"
    MITOCHONDRIAL_DYSFUNCTION = "Mitochondrial dysfunction"
    DNA_DAMAGE = "DNA damage"
    PROTEIN_MISFOLDING = "Protein misfolding"
    MEMBRANE_DISRUPTION = "Membrane disruption"
    APOPTOSIS = "Apoptosis"


@dataclass
class Receptor:
    """
    Molecular receptor model with binding kinetics

    Implements receptor-ligand binding: R + L ⇌ RL
    """
    name: str
    receptor_type: ReceptorType
    total_density: float = 1000.0  # receptors per cell
    free_receptors: float = 1000.0  # unbound receptors
    bound_receptors: float = 0.0    # ligand-bound receptors

    # Binding kinetics
    k_on: float = 1e6   # M⁻¹ s⁻¹, association rate
    k_off: float = 0.1  # s⁻¹, dissociation rate

    # Signal transduction
    signal_amplification: float = 10.0
    desensitization_rate: float = 0.01

    def kd(self) -> float:
        """Dissociation constant (Kd = k_off / k_on)"""
        return self.k_off / self.k_on

    def occupancy(self) -> float:
        """Receptor occupancy fraction"""
        if self.total_density == 0:
            return 0.0
        return self.bound_receptors / self.total_density

    def signal_output(self) -> float:
        """Downstream signal based on receptor occupancy"""
        return self.bound_receptors * self.signal_amplification


@dataclass
class Ligand:
    """
    Drug or signaling molecule
    """
    name: str
    concentration: float = 0.0  # μM
    molecular_weight: float = 500.0  # Da
    logP: float = 2.0  # lipophilicity
    charge: int = 0

    # Pharmacokinetics
    clearance_rate: float = 0.1  # per hour
    volume_distribution: float = 1.0  # L/kg
    protein_binding: float = 0.9  # fraction bound to plasma proteins

    def free_concentration(self) -> float:
        """Unbound drug concentration"""
        return self.concentration * (1.0 - self.protein_binding)


@dataclass
class SignalTransduction:
    """
    Intracellular signaling cascade

    Models: Receptor → G-protein/Kinase → Second messengers → Gene expression
    """
    pathway_name: str
    receptors: List[Receptor] = field(default_factory=list)

    # Signal cascade levels
    second_messenger: float = 0.0  # cAMP, Ca2+, IP3, etc.
    kinase_activity: float = 0.0   # Activated kinases
    transcription_factors: float = 0.0

    # Kinetics
    signal_decay: float = 0.5  # per second
    amplification: float = 100.0

    def integrate_signals(self) -> float:
        """Combine signals from multiple receptors"""
        total_signal = sum(r.signal_output() for r in self.receptors)
        return total_signal

    def update(self, dt: float) -> None:
        """Update signaling cascade state"""
        # Receptor signals activate second messengers
        receptor_signal = self.integrate_signals()
        self.second_messenger += (receptor_signal - self.signal_decay * self.second_messenger) * dt

        # Second messengers activate kinases
        self.kinase_activity += (self.second_messenger * 0.1 - self.signal_decay * self.kinase_activity) * dt

        # Kinases activate transcription factors
        self.transcription_factors += (self.kinase_activity * 0.05 - self.signal_decay * 0.5 * self.transcription_factors) * dt


@dataclass
class ProteinExpression:
    """
    Protein synthesis and degradation dynamics

    Models: mRNA → Protein with regulation
    """
    protein_name: str
    mrna_level: float = 1.0
    protein_level: float = 1.0

    # Transcription
    basal_transcription: float = 0.1
    induced_transcription: float = 0.0
    mrna_degradation: float = 0.5

    # Translation
    translation_rate: float = 1.0
    protein_degradation: float = 0.1

    def update(self, transcription_factor_activity: float, dt: float) -> None:
        """Update protein expression dynamics"""
        # mRNA synthesis and degradation
        transcription = self.basal_transcription + transcription_factor_activity * self.induced_transcription
        dmrna = transcription - self.mrna_degradation * self.mrna_level
        self.mrna_level += dmrna * dt

        # Protein synthesis and degradation
        translation = self.translation_rate * self.mrna_level
        dprotein = translation - self.protein_degradation * self.protein_level
        self.protein_level += dprotein * dt


@dataclass
class CellularStress:
    """
    Cellular stress response and toxicity
    """
    oxidative_stress: float = 0.0  # ROS level
    mitochondrial_damage: float = 0.0
    dna_damage: float = 0.0
    protein_damage: float = 0.0

    # Protective mechanisms
    antioxidant_capacity: float = 1.0
    repair_capacity: float = 1.0

    # Thresholds
    apoptosis_threshold: float = 5.0
    necrosis_threshold: float = 10.0

    def total_stress(self) -> float:
        """Overall cellular stress level"""
        return (self.oxidative_stress +
                self.mitochondrial_damage +
                self.dna_damage +
                self.protein_damage)

    def viability(self) -> float:
        """Cell viability (0 = dead, 1 = healthy)"""
        stress = self.total_stress()
        if stress >= self.necrosis_threshold:
            return 0.0
        elif stress >= self.apoptosis_threshold:
            return np.exp(-(stress - self.apoptosis_threshold))
        else:
            return 1.0 - 0.1 * stress / self.apoptosis_threshold

    def update(self, toxicity_signals: Dict[ToxicityMechanism, float], dt: float) -> None:
        """Update stress levels based on toxicity signals"""
        # Oxidative stress
        ros_production = toxicity_signals.get(ToxicityMechanism.OXIDATIVE_STRESS, 0.0)
        self.oxidative_stress += (ros_production - self.antioxidant_capacity * 0.5 * self.oxidative_stress) * dt

        # Mitochondrial damage
        mito_toxicity = toxicity_signals.get(ToxicityMechanism.MITOCHONDRIAL_DYSFUNCTION, 0.0)
        self.mitochondrial_damage += (mito_toxicity - self.repair_capacity * 0.2 * self.mitochondrial_damage) * dt

        # DNA damage
        dna_toxicity = toxicity_signals.get(ToxicityMechanism.DNA_DAMAGE, 0.0)
        self.dna_damage += (dna_toxicity + self.oxidative_stress * 0.1 - self.repair_capacity * 0.3 * self.dna_damage) * dt

        # Protein damage
        protein_toxicity = toxicity_signals.get(ToxicityMechanism.PROTEIN_MISFOLDING, 0.0)
        self.protein_damage += (protein_toxicity + self.oxidative_stress * 0.05 - self.repair_capacity * 0.4 * self.protein_damage) * dt


@dataclass
class CellPopulation:
    """
    Population of cells with RPO dynamics
    """
    cell_type: str
    cell_count: float = 1e6

    # RPO components
    receptors: Dict[str, Receptor] = field(default_factory=dict)
    signaling: Dict[str, SignalTransduction] = field(default_factory=dict)
    proteins: Dict[str, ProteinExpression] = field(default_factory=dict)
    stress: CellularStress = field(default_factory=CellularStress)

    # Metabolic state
    atp_level: float = 1.0
    nadh_level: float = 1.0
    gsh_level: float = 1.0  # glutathione (antioxidant)

    def add_receptor(self, receptor: Receptor) -> None:
        """Add a receptor type to cells"""
        self.receptors[receptor.name] = receptor

    def add_signaling_pathway(self, pathway: SignalTransduction) -> None:
        """Add a signaling pathway"""
        self.signaling[pathway.pathway_name] = pathway

    def add_protein(self, protein: ProteinExpression) -> None:
        """Add a protein to track"""
        self.proteins[protein.protein_name] = protein

    def bind_ligand(self, receptor_name: str, ligand: Ligand, dt: float) -> None:
        """
        Simulate ligand binding to receptor

        dRL/dt = k_on * [R] * [L] - k_off * [RL]
        """
        if receptor_name not in self.receptors:
            return

        receptor = self.receptors[receptor_name]
        free_ligand = ligand.free_concentration()

        # Binding dynamics
        d_bound = (receptor.k_on * receptor.free_receptors * free_ligand * 1e-6 -
                   receptor.k_off * receptor.bound_receptors) * dt

        receptor.bound_receptors = max(0, min(receptor.total_density, receptor.bound_receptors + d_bound))
        receptor.free_receptors = receptor.total_density - receptor.bound_receptors

    def update_metabolism(self, dt: float) -> None:
        """Update cellular metabolism"""
        # ATP depletion from stress
        atp_consumption = 0.1 + self.stress.mitochondrial_damage * 0.5
        atp_production = 1.0 - self.stress.mitochondrial_damage * 0.8
        self.atp_level += (atp_production - atp_consumption) * dt
        self.atp_level = max(0.0, min(2.0, self.atp_level))

        # NADH dynamics
        self.nadh_level += (0.5 - self.stress.oxidative_stress * 0.3) * dt
        self.nadh_level = max(0.0, min(2.0, self.nadh_level))

        # Glutathione (antioxidant)
        gsh_consumption = self.stress.oxidative_stress * 0.5
        gsh_synthesis = 0.3 * self.atp_level
        self.gsh_level += (gsh_synthesis - gsh_consumption) * dt
        self.gsh_level = max(0.0, min(2.0, self.gsh_level))

        # Update stress antioxidant capacity
        self.stress.antioxidant_capacity = self.gsh_level

    def update(self, dt: float) -> None:
        """Update all cellular dynamics"""
        # Update signaling pathways
        for pathway in self.signaling.values():
            pathway.update(dt)

        # Update protein expression
        for protein_name, protein in self.proteins.items():
            # Get transcription factor activity from relevant pathway
            tf_activity = 0.0
            for pathway in self.signaling.values():
                tf_activity += pathway.transcription_factors
            protein.update(tf_activity, dt)

        # Update metabolism
        self.update_metabolism(dt)

        # Update stress (with empty toxicity signals by default)
        self.stress.update({}, dt)

        # Cell death
        viability = self.stress.viability()
        self.cell_count *= (1.0 - (1.0 - viability) * dt)


class OrganChip:
    """
    Base class for organ-on-chip models with RPO framework
    """

    def __init__(self, organ_name: str):
        self.organ_name = organ_name
        self.cell_populations: Dict[str, CellPopulation] = {}
        self.tissue_properties: Dict[str, float] = {}
        self.time: float = 0.0

        # Perfusion and transport
        self.flow_rate: float = 1.0  # mL/min
        self.oxygen_level: float = 21.0  # % O2
        self.glucose_level: float = 5.0  # mM

    def add_cell_population(self, population: CellPopulation) -> None:
        """Add a cell population to the organ chip"""
        self.cell_populations[population.cell_type] = population

    def apply_drug(self, drug: Ligand, receptor_targets: Dict[str, List[str]]) -> None:
        """
        Apply drug to organ chip

        Args:
            drug: Ligand/drug to apply
            receptor_targets: Dict mapping cell_type -> list of receptor names
        """
        for cell_type, receptor_names in receptor_targets.items():
            if cell_type in self.cell_populations:
                population = self.cell_populations[cell_type]
                for receptor_name in receptor_names:
                    if receptor_name in population.receptors:
                        population.bind_ligand(receptor_name, drug, 0.01)

    def update(self, dt: float) -> None:
        """Update organ chip state"""
        self.time += dt

        # Update each cell population
        for population in self.cell_populations.values():
            population.update(dt)

    def get_viability(self) -> float:
        """Overall organ viability"""
        if not self.cell_populations:
            return 1.0

        total_cells = sum(p.cell_count for p in self.cell_populations.values())
        if total_cells == 0:
            return 0.0

        viable_cells = sum(p.cell_count * p.stress.viability()
                          for p in self.cell_populations.values())
        return viable_cells / total_cells

    def get_state(self) -> Dict:
        """Get current organ state"""
        return {
            'time': self.time,
            'viability': self.get_viability(),
            'cell_populations': {
                name: {
                    'count': pop.cell_count,
                    'viability': pop.stress.viability(),
                    'atp': pop.atp_level,
                    'stress': pop.stress.total_stress()
                }
                for name, pop in self.cell_populations.items()
            }
        }


# Drug-Receptor Interaction Models
class DrugReceptorInteraction:
    """
    Models drug-receptor interactions and downstream effects
    """

    @staticmethod
    def hill_equation(concentration: float, ec50: float, hill_coefficient: float = 1.0) -> float:
        """
        Hill equation for dose-response

        E = [D]^n / (EC50^n + [D]^n)
        """
        if ec50 <= 0:
            return 0.0
        return (concentration ** hill_coefficient) / (ec50 ** hill_coefficient + concentration ** hill_coefficient)

    @staticmethod
    def competitive_inhibition(ligand_conc: float, inhibitor_conc: float,
                              kd_ligand: float, ki_inhibitor: float) -> float:
        """
        Competitive inhibition binding

        Returns fractional occupancy by ligand in presence of inhibitor
        """
        return ligand_conc / (kd_ligand * (1 + inhibitor_conc / ki_inhibitor) + ligand_conc)

    @staticmethod
    def allosteric_modulation(ligand_response: float, modulator_conc: float,
                            kd_modulator: float, cooperativity: float = 2.0) -> float:
        """
        Allosteric modulation of receptor response
        """
        modulation_factor = 1.0 + cooperativity * modulator_conc / (kd_modulator + modulator_conc)
        return ligand_response * modulation_factor


# Immune Response Integration
@dataclass
class RPO_ImmuneResponse:
    """
    Immune system response within RPO framework
    """
    # Immune cell populations
    macrophages: float = 1e5
    t_cells: float = 1e4
    b_cells: float = 1e3

    # Cytokines
    tnf_alpha: float = 0.0  # pg/mL
    il6: float = 0.0
    il10: float = 0.0  # anti-inflammatory

    # Inflammation markers
    crp: float = 0.0  # C-reactive protein
    inflammation_level: float = 0.0

    def detect_damage(self, cell_stress: CellularStress) -> float:
        """Detect cellular damage and activate immune response"""
        damage_signal = cell_stress.total_stress()
        return damage_signal

    def activate(self, damage_signal: float, dt: float) -> None:
        """Activate immune response"""
        # Pro-inflammatory cytokines
        self.tnf_alpha += (damage_signal * 10.0 - 0.5 * self.tnf_alpha) * dt
        self.il6 += (damage_signal * 8.0 - 0.4 * self.il6) * dt

        # Anti-inflammatory response (negative feedback)
        self.il10 += (self.tnf_alpha * 0.1 - 0.3 * self.il10) * dt

        # Overall inflammation
        self.inflammation_level = (self.tnf_alpha + self.il6 - self.il10 * 0.5) / 10.0

        # CRP production
        self.crp += (self.il6 * 0.5 - 0.2 * self.crp) * dt

    def update(self, organ_stress: Dict[str, float], dt: float) -> None:
        """Update immune response based on organ stress levels"""
        total_damage = sum(organ_stress.values())
        damage_signal = self.detect_damage(CellularStress(
            oxidative_stress=total_damage * 0.3,
            mitochondrial_damage=total_damage * 0.3,
            dna_damage=total_damage * 0.2,
            protein_damage=total_damage * 0.2
        ))
        self.activate(damage_signal, dt)


if __name__ == "__main__":
    # Example: Create a simple organ chip with RPO dynamics
    print("RPO Organ Chip Framework - Example")
    print("=" * 60)

    # Create receptor
    receptor = Receptor(
        name="beta_adrenergic",
        receptor_type=ReceptorType.GPCR,
        k_on=1e6,
        k_off=0.1
    )

    # Create ligand (drug)
    drug = Ligand(
        name="isoproterenol",
        concentration=1.0,  # μM
        molecular_weight=247.7
    )

    # Create cell population
    cells = CellPopulation(cell_type="cardiomyocyte", cell_count=1e6)
    cells.add_receptor(receptor)

    # Simulate binding
    for step in range(100):
        cells.bind_ligand("beta_adrenergic", drug, dt=0.1)
        cells.update(dt=0.1)

        if step % 20 == 0:
            occupancy = receptor.occupancy()
            viability = cells.stress.viability()
            print(f"t={step*0.1:.1f}s: Receptor occupancy={occupancy:.3f}, Viability={viability:.3f}")

    print("\nRPO framework initialized successfully!")
