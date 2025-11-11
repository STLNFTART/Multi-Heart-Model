"""
Systemic Circulation Module

Implements blood circulation connecting multiple organ-on-chip systems
with pharmacokinetic/pharmacodynamic modeling.

Key Features:
- Physiologically-based pharmacokinetic (PBPK) modeling
- Multi-compartment circulation (arterial, venous, organ-specific)
- Drug distribution and clearance
- Organ perfusion and flow dynamics
- Metabolite transport between organs
- Systemic biomarkers (complete blood count, chemistry panel)

Author: Multi-Organ Chip Architecture Team
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .rpo_organ_chip import Ligand, OrganChip


@dataclass
class BloodCompartment:
    """
    Blood compartment for multi-organ circulation
    """
    name: str
    volume: float = 5000.0  # mL (total blood volume ~5L)

    # Drug concentrations
    drugs: Dict[str, float] = field(default_factory=dict)  # drug_name -> concentration (μM)
    metabolites: Dict[str, float] = field(default_factory=dict)

    # Blood composition
    hemoglobin: float = 14.0  # g/dL
    hematocrit: float = 0.42  # fraction
    plasma_proteins: float = 7.0  # g/dL
    albumin: float = 4.0  # g/dL

    # Oxygen and nutrients
    po2: float = 100.0  # mmHg (arterial)
    pco2: float = 40.0  # mmHg
    glucose: float = 90.0  # mg/dL
    lactate: float = 1.0  # mM

    # Inflammatory markers
    wbc: float = 7000.0  # cells/μL
    crp: float = 0.5  # mg/L

    def add_drug(self, drug_name: str, amount: float) -> None:
        """Add drug to compartment (bolus or infusion)"""
        if drug_name not in self.drugs:
            self.drugs[drug_name] = 0.0
        # Convert amount to concentration
        concentration_increase = amount / self.volume
        self.drugs[drug_name] += concentration_increase

    def get_drug_concentration(self, drug_name: str) -> float:
        """Get current drug concentration"""
        return self.drugs.get(drug_name, 0.0)

    def clear_drug(self, drug_name: str, clearance_amount: float, dt: float) -> None:
        """Remove drug due to metabolism/excretion"""
        if drug_name in self.drugs:
            self.drugs[drug_name] = max(0, self.drugs[drug_name] - clearance_amount * dt)


@dataclass
class OrganPerfusion:
    """
    Organ-specific perfusion parameters
    """
    organ_name: str
    blood_flow: float = 1000.0  # mL/min
    fraction_cardiac_output: float = 0.2  # fraction of total CO
    extraction_ratio: float = 0.3  # fraction of drug extracted per pass

    # Tissue properties
    tissue_volume: float = 1000.0  # mL
    tissue_blood_partition: float = 1.0  # Kp (tissue:blood ratio)

    # Vascular resistance
    resistance: float = 1.0  # mmHg·min/mL
    arterial_pressure: float = 100.0  # mmHg
    venous_pressure: float = 5.0  # mmHg

    def flow_rate(self, cardiac_output: float) -> float:
        """Calculate blood flow based on cardiac output"""
        return cardiac_output * self.fraction_cardiac_output


@dataclass
class SystemicCirculation:
    """
    Complete systemic circulation model connecting multiple organs
    """
    # Blood compartments
    arterial: BloodCompartment = field(default_factory=lambda: BloodCompartment(
        name="arterial", volume=1000.0, po2=100.0
    ))
    venous: BloodCompartment = field(default_factory=lambda: BloodCompartment(
        name="venous", volume=3500.0, po2=40.0
    ))

    # Organ perfusion
    perfusions: Dict[str, OrganPerfusion] = field(default_factory=dict)

    # Hemodynamics
    cardiac_output: float = 5000.0  # mL/min
    mean_arterial_pressure: float = 93.0  # mmHg
    systemic_vascular_resistance: float = 1200.0  # dyn·s/cm⁵

    # Time
    time: float = 0.0

    def __post_init__(self):
        """Initialize organ perfusions"""
        # Liver perfusion (25% of CO, dual blood supply)
        self.perfusions["liver"] = OrganPerfusion(
            organ_name="liver",
            blood_flow=1500.0,
            fraction_cardiac_output=0.25,
            extraction_ratio=0.3,
            tissue_volume=1500.0,
            tissue_blood_partition=1.5
        )

        # Heart perfusion (coronary circulation, 5% of CO)
        self.perfusions["heart"] = OrganPerfusion(
            organ_name="heart",
            blood_flow=250.0,
            fraction_cardiac_output=0.05,
            extraction_ratio=0.1,
            tissue_volume=300.0,
            tissue_blood_partition=1.2
        )

        # Kidney perfusion (20% of CO) - for future expansion
        self.perfusions["kidney"] = OrganPerfusion(
            organ_name="kidney",
            blood_flow=1200.0,
            fraction_cardiac_output=0.24,
            extraction_ratio=0.5,
            tissue_volume=300.0,
            tissue_blood_partition=0.8
        )

        # Brain perfusion (15% of CO) - for existing neural model
        self.perfusions["brain"] = OrganPerfusion(
            organ_name="brain",
            blood_flow=750.0,
            fraction_cardiac_output=0.15,
            extraction_ratio=0.05,
            tissue_volume=1400.0,
            tissue_blood_partition=1.0
        )

        # Muscle perfusion (15% of CO)
        self.perfusions["muscle"] = OrganPerfusion(
            organ_name="muscle",
            blood_flow=750.0,
            fraction_cardiac_output=0.15,
            extraction_ratio=0.1,
            tissue_volume=30000.0,
            tissue_blood_partition=0.7
        )

    def distribute_drug(self, drug: Ligand, dose_mg: float, route: str = "IV") -> None:
        """
        Administer drug to circulation

        Args:
            drug: Drug to administer
            dose_mg: Dose in milligrams
            route: Administration route (IV, PO, etc.)
        """
        if route == "IV":
            # Intravenous: direct to arterial compartment
            self.arterial.add_drug(drug.name, dose_mg)
        elif route == "PO":
            # Oral: add to venous (after GI absorption) with bioavailability
            bioavailability = 0.7  # typical
            self.venous.add_drug(drug.name, dose_mg * bioavailability)
        elif route == "IM":
            # Intramuscular: slower absorption
            self.venous.add_drug(drug.name, dose_mg * 0.8)

    def update_drug_distribution(self, organs: Dict[str, OrganChip], dt: float) -> None:
        """
        Update drug distribution across organs and compartments

        Implements PBPK equations:
        dC/dt = Q/V * (C_arterial - C_venous)
        """
        # For each drug in circulation
        all_drugs = set(self.arterial.drugs.keys()) | set(self.venous.drugs.keys())

        for drug_name in all_drugs:
            c_arterial = self.arterial.get_drug_concentration(drug_name)

            # Drug distribution to each organ
            for organ_name, perfusion in self.perfusions.items():
                if organ_name not in organs:
                    continue

                organ = organs[organ_name]

                # Blood flow to organ
                q_organ = perfusion.flow_rate(self.cardiac_output)

                # Drug uptake by organ (simplified)
                uptake_rate = q_organ / perfusion.tissue_volume * perfusion.extraction_ratio
                drug_uptake = c_arterial * uptake_rate * dt

                # Remove from arterial blood
                if drug_name in self.arterial.drugs:
                    self.arterial.drugs[drug_name] = max(0, c_arterial - drug_uptake)

                # Add to venous blood (after organ extraction)
                c_venous_organ = c_arterial * (1.0 - perfusion.extraction_ratio)
                self.venous.add_drug(drug_name, c_venous_organ * q_organ * dt / 1000.0)

            # Venous return to arterial (through heart/lungs)
            c_venous = self.venous.get_drug_concentration(drug_name)
            venous_return_rate = self.cardiac_output / self.venous.volume
            arterial_input = c_venous * venous_return_rate * dt

            self.arterial.add_drug(drug_name, arterial_input * self.arterial.volume / 1000.0)
            self.venous.drugs[drug_name] = max(0, c_venous - arterial_input)

    def update_metabolite_transport(self, organs: Dict[str, OrganChip], dt: float) -> None:
        """Transport metabolites from liver to circulation"""
        if "liver" in organs:
            liver = organs["liver"]

            # Get liver metabolites (from liver_chip module)
            if hasattr(liver, 'hepatocytes'):
                metabolism = liver.hepatocytes.metabolism

                # Transport Phase II conjugates to blood for excretion
                for metabolite_name, conc in metabolism.phase2_conjugates.items():
                    if conc > 0:
                        # Add to venous blood
                        self.venous.add_drug(metabolite_name, conc * 0.01)  # 1% per timestep
                        metabolism.phase2_conjugates[metabolite_name] *= 0.99

    def update_hemodynamics(self, organs: Dict[str, OrganChip], dt: float) -> None:
        """Update cardiovascular hemodynamics"""
        # Get cardiac output from heart chip
        if "heart" in organs:
            heart = organs["heart"]
            if hasattr(heart, 'cardiomyocytes'):
                cardiac_function = heart.get_cardiac_function()
                self.cardiac_output = cardiac_function['cardiac_output'] * 1000.0  # L/min to mL/min

        # Mean arterial pressure (MAP = CO × SVR)
        self.mean_arterial_pressure = self.cardiac_output * self.systemic_vascular_resistance / 1000.0

        # Update organ perfusion based on MAP
        for perfusion in self.perfusions.values():
            perfusion.blood_flow = (
                (perfusion.arterial_pressure - perfusion.venous_pressure) /
                perfusion.resistance
            )

    def update_blood_gases(self, organs: Dict[str, OrganChip], dt: float) -> None:
        """Update oxygen and CO2 levels"""
        # Oxygen consumption by organs
        total_o2_consumption = 0.0
        for organ_name, perfusion in self.perfusions.items():
            if organ_name in organs:
                # Simplified O2 consumption
                o2_consumption = perfusion.blood_flow * 0.05  # mL O2/min
                total_o2_consumption += o2_consumption

        # Arterial PO2 (from lungs - assumed constant for now)
        self.arterial.po2 = 100.0

        # Venous PO2 (reduced after tissue extraction)
        o2_extraction = total_o2_consumption / (self.cardiac_output * 0.2)
        self.venous.po2 = self.arterial.po2 * (1.0 - o2_extraction)

        # CO2 production
        self.arterial.pco2 = 40.0
        self.venous.pco2 = 46.0  # Higher in venous blood

    def update_biomarkers(self, organs: Dict[str, OrganChip], dt: float) -> None:
        """Update systemic biomarkers from organ damage"""
        # Liver enzymes in blood
        if "liver" in organs:
            liver = organs["liver"]
            if hasattr(liver, 'hepatocytes'):
                lfts = liver.get_liver_function_tests()
                # Enzymes leak into blood with hepatocyte damage
                # These are already tracked in liver_chip

        # Cardiac biomarkers
        if "heart" in organs:
            heart = organs["heart"]
            if hasattr(heart, 'cardiomyocytes'):
                # Troponin leaks into blood with cardiomyocyte damage
                # Already tracked in heart_chip
                pass

        # Inflammatory markers
        total_inflammation = 0.0
        for organ in organs.values():
            for pop in organ.cell_populations.values():
                total_inflammation += pop.stress.total_stress()

        # WBC increases with inflammation
        self.arterial.wbc += (total_inflammation * 100.0 - 0.1 * (self.arterial.wbc - 7000.0)) * dt
        self.venous.wbc = self.arterial.wbc

        # CRP increases with inflammation
        self.arterial.crp += (total_inflammation * 2.0 - 0.05 * self.arterial.crp) * dt
        self.venous.crp = self.arterial.crp

    def update(self, organs: Dict[str, OrganChip], dt: float) -> None:
        """Update complete circulation"""
        self.time += dt

        # Update all circulatory functions
        self.update_hemodynamics(organs, dt)
        self.update_drug_distribution(organs, dt)
        self.update_metabolite_transport(organs, dt)
        self.update_blood_gases(organs, dt)
        self.update_biomarkers(organs, dt)

    def get_state(self) -> Dict:
        """Get current circulation state"""
        return {
            'time': self.time,
            'cardiac_output': self.cardiac_output,
            'mean_arterial_pressure': self.mean_arterial_pressure,
            'arterial': {
                'drugs': dict(self.arterial.drugs),
                'po2': self.arterial.po2,
                'glucose': self.arterial.glucose,
                'lactate': self.arterial.lactate,
            },
            'venous': {
                'drugs': dict(self.venous.drugs),
                'po2': self.venous.po2,
            },
            'inflammatory_markers': {
                'wbc': self.arterial.wbc,
                'crp': self.arterial.crp,
            }
        }


class PharmacokineticsModel:
    """
    Pharmacokinetic analysis tools
    """

    @staticmethod
    def one_compartment_pk(dose: float, volume: float, clearance: float,
                          time_points: np.ndarray) -> np.ndarray:
        """
        One-compartment PK model

        C(t) = (Dose/V) * exp(-CL/V * t)
        """
        ke = clearance / volume  # elimination rate constant
        c0 = dose / volume  # initial concentration
        return c0 * np.exp(-ke * time_points)

    @staticmethod
    def two_compartment_pk(dose: float, v1: float, v2: float,
                          cl: float, q: float, time_points: np.ndarray) -> np.ndarray:
        """
        Two-compartment PK model (central + peripheral)

        C(t) = A * exp(-alpha * t) + B * exp(-beta * t)
        """
        # Micro-constants
        k10 = cl / v1
        k12 = q / v1
        k21 = q / v2

        # Macro-constants
        alpha = 0.5 * ((k10 + k12 + k21) + np.sqrt((k10 + k12 + k21)**2 - 4*k10*k21))
        beta = 0.5 * ((k10 + k12 + k21) - np.sqrt((k10 + k12 + k21)**2 - 4*k10*k21))

        # Coefficients
        A = (dose / v1) * (alpha - k21) / (alpha - beta)
        B = (dose / v1) * (k21 - beta) / (alpha - beta)

        return A * np.exp(-alpha * time_points) + B * np.exp(-beta * time_points)

    @staticmethod
    def calculate_auc(concentrations: np.ndarray, times: np.ndarray) -> float:
        """
        Calculate area under the curve (AUC) using trapezoidal rule

        AUC is a key PK parameter for drug exposure
        """
        return np.trapz(concentrations, times)

    @staticmethod
    def calculate_cmax_tmax(concentrations: np.ndarray, times: np.ndarray) -> Tuple[float, float]:
        """
        Calculate peak concentration (Cmax) and time to peak (Tmax)
        """
        idx_max = np.argmax(concentrations)
        return concentrations[idx_max], times[idx_max]

    @staticmethod
    def calculate_half_life(concentrations: np.ndarray, times: np.ndarray) -> float:
        """
        Calculate elimination half-life

        t1/2 = ln(2) / ke
        """
        # Use terminal phase (last 50% of data)
        n = len(concentrations)
        terminal_conc = concentrations[n//2:]
        terminal_time = times[n//2:]

        # Fit exponential decay
        if len(terminal_conc) < 2:
            return 0.0

        log_conc = np.log(terminal_conc + 1e-10)
        slope, _ = np.polyfit(terminal_time, log_conc, 1)
        ke = -slope

        return np.log(2) / ke if ke > 0 else np.inf


if __name__ == "__main__":
    # Example: Multi-organ circulation with drug distribution
    print("Systemic Circulation Model - Drug Distribution Example")
    print("=" * 70)

    # Create circulation
    circulation = SystemicCirculation()

    # Administer drug
    test_drug = Ligand(name="test_drug", concentration=0.0, molecular_weight=300.0)
    circulation.distribute_drug(test_drug, dose_mg=100.0, route="IV")

    print(f"\nInitial arterial concentration: {circulation.arterial.get_drug_concentration('test_drug'):.2f} μM")

    # Simulate circulation (without organs for this example)
    time_points = []
    concentrations = []

    for step in range(100):
        t = step * 0.1
        time_points.append(t)
        concentrations.append(circulation.arterial.get_drug_concentration('test_drug'))

        # Simple clearance
        circulation.arterial.clear_drug('test_drug', 0.1, 0.1)
        circulation.update({}, dt=0.1)

    # Calculate PK parameters
    pk = PharmacokineticsModel()
    auc = pk.calculate_auc(np.array(concentrations), np.array(time_points))
    cmax, tmax = pk.calculate_cmax_tmax(np.array(concentrations), np.array(time_points))
    t_half = pk.calculate_half_life(np.array(concentrations), np.array(time_points))

    print(f"\nPharmacokinetic Parameters:")
    print(f"  AUC: {auc:.2f} μM·h")
    print(f"  Cmax: {cmax:.2f} μM at Tmax: {tmax:.2f} h")
    print(f"  Half-life: {t_half:.2f} h")

    print("\nCirculation module ready for multi-organ integration!")
