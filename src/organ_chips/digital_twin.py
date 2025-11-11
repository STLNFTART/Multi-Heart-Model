"""
Multi-Organ Digital Twin Orchestrator

Integrates heart, liver, and other organ chips with systemic circulation
and immune response to create a comprehensive digital twin for drug testing.

Key Features:
- Multi-organ system orchestration
- Drug administration and PK/PD modeling
- Real-time monitoring and data collection
- Clinical-grade toxicity assessment
- Integration with existing heart-brain coupling
- Export capabilities for analysis

Author: Multi-Organ Chip Architecture Team
"""

from __future__ import annotations

import numpy as np
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from .rpo_organ_chip import Ligand, DrugReceptorInteraction
from .heart_chip import HeartChip, CardiacToxicity
from .liver_chip import LiverChip, LiverToxicity
from .circulation import SystemicCirculation, PharmacokineticsModel
from .immune_system import SystemicImmuneResponse, ImmuneSignalingBridge
from ..coupling.hbcm import HeartBrainCouplingModel


@dataclass
class SimulationConfig:
    """Configuration for digital twin simulation"""
    duration: float = 24.0  # hours
    dt: float = 0.01  # seconds
    output_interval: float = 60.0  # seconds (save data every minute)

    # Drug administration
    drug_name: str = "test_drug"
    dose_mg: float = 100.0
    route: str = "IV"  # IV, PO, IM
    infusion_duration: float = 0.0  # hours (0 = bolus)

    # Organ flags
    enable_heart: bool = True
    enable_liver: bool = True
    enable_brain: bool = True
    enable_immune: bool = True

    # Monitoring
    monitor_biomarkers: bool = True
    monitor_hemodynamics: bool = True
    monitor_toxicity: bool = True


@dataclass
class TimePoint:
    """Single time point snapshot of digital twin state"""
    time: float

    # Drug concentrations
    drug_concentration_arterial: float = 0.0
    drug_concentration_venous: float = 0.0

    # Hemodynamics
    cardiac_output: float = 5.0
    heart_rate: float = 70.0
    mean_arterial_pressure: float = 93.0

    # Organ function
    heart_viability: float = 1.0
    liver_viability: float = 1.0
    heart_contractility: float = 1.0
    ejection_fraction: float = 0.60

    # Biomarkers
    troponin_i: float = 0.01
    ck_mb: float = 2.0
    bnp: float = 50.0
    alt: float = 20.0
    ast: float = 25.0
    bilirubin: float = 0.5

    # Immune
    tnf_alpha: float = 0.0
    il6: float = 0.0
    crp: float = 0.5
    wbc: float = 7000.0

    # Toxicity
    qt_interval: float = 400.0
    qtc: float = 400.0
    oxidative_stress_heart: float = 0.0
    oxidative_stress_liver: float = 0.0


class MultiOrganDigitalTwin:
    """
    Complete multi-organ digital twin system
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()

        # Initialize organs
        self.heart: Optional[HeartChip] = None
        self.liver: Optional[LiverChip] = None
        self.circulation: Optional[SystemicCirculation] = None
        self.immune_system: Optional[SystemicImmuneResponse] = None
        self.hbcm: Optional[HeartBrainCouplingModel] = None

        # Data storage
        self.time_points: List[TimePoint] = []
        self.time: float = 0.0
        self.step_count: int = 0

        # Initialize systems
        self._initialize_systems()

    def _initialize_systems(self) -> None:
        """Initialize all organ systems"""
        # Heart
        if self.config.enable_heart:
            self.heart = HeartChip()

        # Liver
        if self.config.enable_liver:
            self.liver = LiverChip()

        # Circulation
        self.circulation = SystemicCirculation()

        # Immune system
        if self.config.enable_immune:
            self.immune_system = SystemicImmuneResponse()
            if self.heart:
                self.immune_system.add_organ("heart", self.heart.cardiomyocytes.stress)
            if self.liver:
                self.immune_system.add_organ("liver", self.liver.hepatocytes.stress)

        # Heart-Brain coupling (integrate with existing model)
        if self.config.enable_brain and self.config.enable_heart:
            from ..neural.fhn import FitzHughNagumo
            from ..cardiac.van_der_pol import VanDerPolOscillator
            from ..coupling.hbcm import CouplingParameters

            self.hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(stimulus_amplitude=0.2),
                cardiac_model=VanDerPolOscillator(mu=1.5, omega=1.0),
                coupling=CouplingParameters(
                    neural_to_cardiac_gain=0.5,
                    cardiac_to_neural_gain=0.3
                ),
            )

    def administer_drug(self, drug: Ligand, dose_mg: float, route: str = "IV") -> None:
        """
        Administer drug to the digital twin

        Args:
            drug: Drug to administer
            dose_mg: Dose in milligrams
            route: Administration route (IV, PO, IM)
        """
        if self.circulation:
            self.circulation.distribute_drug(drug, dose_mg, route)
            print(f"Administered {dose_mg} mg of {drug.name} via {route} route")

    def update(self, dt: float) -> None:
        """Update all systems for one time step"""
        self.time += dt
        self.step_count += 1

        # Build organ dictionary for circulation
        organs = {}
        if self.heart:
            organs["heart"] = self.heart
        if self.liver:
            organs["liver"] = self.liver

        # Update circulation (drug distribution, hemodynamics)
        if self.circulation:
            self.circulation.update(organs, dt)

            # Update organ-specific drug effects
            for drug_name, concentration in self.circulation.arterial.drugs.items():
                drug = Ligand(name=drug_name, concentration=concentration)

                # Liver metabolism
                if self.liver:
                    self.liver.apply_drug(drug, dt)

                # Heart exposure (update drug concentration for cardiac effects)
                if self.heart:
                    # Drugs can affect ion channels, receptors, etc.
                    pass  # Already handled via circulation

        # Update organs
        if self.heart:
            self.heart.update(dt)

        if self.liver:
            self.liver.update(dt)

        # Update immune system
        if self.immune_system:
            self.immune_system.update(organs, dt)

        # Update heart-brain coupling
        if self.hbcm and self.heart:
            # Get immune modulation of neural activity
            neural_input = 0.0
            if self.immune_system:
                neural_input = ImmuneSignalingBridge.immune_to_neural_signal(self.immune_system)

            # Step the HBCM
            hbcm_state = (0.0, 0.0,
                         self.heart.cardiomyocytes.oscillator_state[0],
                         self.heart.cardiomyocytes.oscillator_state[1])
            # Update oscillator state from HBCM
            self.heart.cardiomyocytes.oscillator_state = (hbcm_state[2], hbcm_state[3])

    def capture_snapshot(self) -> TimePoint:
        """Capture current state snapshot"""
        snapshot = TimePoint(time=self.time)

        # Drug concentrations
        if self.circulation:
            drug_name = self.config.drug_name
            snapshot.drug_concentration_arterial = self.circulation.arterial.get_drug_concentration(drug_name)
            snapshot.drug_concentration_venous = self.circulation.venous.get_drug_concentration(drug_name)
            snapshot.cardiac_output = self.circulation.cardiac_output / 1000.0  # mL/min to L/min
            snapshot.mean_arterial_pressure = self.circulation.mean_arterial_pressure

        # Heart
        if self.heart:
            snapshot.heart_viability = self.heart.get_viability()
            cardiac_func = self.heart.get_cardiac_function()
            snapshot.heart_rate = cardiac_func['heart_rate']
            snapshot.heart_contractility = cardiac_func['contractility']
            snapshot.ejection_fraction = cardiac_func['ejection_fraction']

            biomarkers = self.heart.get_biomarkers()
            snapshot.troponin_i = biomarkers['troponin_I']
            snapshot.ck_mb = biomarkers['CK_MB']
            snapshot.bnp = biomarkers['BNP']

            ecg = self.heart.get_ecg_parameters()
            snapshot.qt_interval = ecg['QT_interval']
            snapshot.qtc = ecg['QTc']

            snapshot.oxidative_stress_heart = self.heart.cardiomyocytes.stress.oxidative_stress

        # Liver
        if self.liver:
            snapshot.liver_viability = self.liver.get_viability()
            lfts = self.liver.get_liver_function_tests()
            snapshot.alt = lfts['ALT']
            snapshot.ast = lfts['AST']
            snapshot.bilirubin = lfts['bilirubin']

            snapshot.oxidative_stress_liver = self.liver.hepatocytes.stress.oxidative_stress

        # Immune system
        if self.immune_system:
            immune_state = self.immune_system.get_state()
            snapshot.tnf_alpha = immune_state['cytokines']['TNF_alpha']
            snapshot.il6 = immune_state['cytokines']['IL6']
            snapshot.crp = immune_state['cytokines']['CRP']
            snapshot.wbc = immune_state['immune_cells']['neutrophils']

        return snapshot

    def simulate(self, drug: Optional[Ligand] = None) -> List[TimePoint]:
        """
        Run complete simulation

        Args:
            drug: Optional drug to administer at t=0

        Returns:
            List of time point snapshots
        """
        print(f"\n{'='*70}")
        print(f"Multi-Organ Digital Twin Simulation")
        print(f"{'='*70}")
        print(f"Duration: {self.config.duration} hours")
        print(f"Time step: {self.config.dt} seconds")
        print(f"Organs: Heart={self.config.enable_heart}, Liver={self.config.enable_liver}, "
              f"Brain={self.config.enable_brain}")

        # Administer drug if provided
        if drug:
            self.administer_drug(drug, self.config.dose_mg, self.config.route)

        # Initial snapshot
        self.time_points.append(self.capture_snapshot())

        # Simulation loop
        total_steps = int(self.config.duration * 3600 / self.config.dt)
        output_steps = int(self.config.output_interval / self.config.dt)

        print(f"\nRunning simulation...")
        for step in range(total_steps):
            self.update(self.config.dt)

            # Save snapshot at output intervals
            if step % output_steps == 0:
                self.time_points.append(self.capture_snapshot())

                # Progress update
                progress = (step / total_steps) * 100
                if progress % 10 < (self.config.dt / (self.config.duration * 36)):
                    print(f"  Progress: {progress:.0f}% (t={self.time/3600:.1f}h)")

        # Final snapshot
        self.time_points.append(self.capture_snapshot())

        print(f"\nSimulation complete!")
        print(f"Total time points: {len(self.time_points)}")

        return self.time_points

    def assess_toxicity(self) -> Dict[str, Any]:
        """
        Comprehensive toxicity assessment
        """
        assessment = {
            'simulation_time': self.time / 3600.0,  # hours
            'overall_safety': 'Safe',
        }

        # Heart toxicity
        if self.heart:
            cardiac_tox = self.heart.assess_cardiotoxicity()
            assessment['cardiac_toxicity'] = cardiac_tox

            # Determine if cardiotoxic
            if cardiac_tox['viability'] < 0.7 or cardiac_tox['QTc_prolongation'] == 'High':
                assessment['overall_safety'] = 'Cardiotoxic'

        # Liver toxicity
        if self.liver:
            hepato_tox = self.liver.assess_hepatotoxicity()
            assessment['hepatotoxicity'] = hepato_tox

            # Determine if hepatotoxic
            if hepato_tox['severity'] in ['Moderate', 'Severe']:
                assessment['overall_safety'] = 'Hepatotoxic'

        # Immune/inflammatory toxicity
        if self.immune_system:
            sepsis_risk = self.immune_system.assess_sepsis_risk()
            assessment['immune_toxicity'] = sepsis_risk

            if sepsis_risk['risk'] == 'High':
                assessment['overall_safety'] = 'Immunotoxic'

        # Overall viability
        viabilities = []
        if self.heart:
            viabilities.append(self.heart.get_viability())
        if self.liver:
            viabilities.append(self.liver.get_viability())

        if viabilities:
            avg_viability = np.mean(viabilities)
            assessment['average_viability'] = avg_viability

            if avg_viability < 0.5:
                assessment['overall_safety'] = 'Severe Toxicity'

        return assessment

    def export_results(self, filepath: str) -> None:
        """
        Export simulation results to JSON

        Args:
            filepath: Path to output file
        """
        results = {
            'config': asdict(self.config),
            'time_points': [asdict(tp) for tp in self.time_points],
            'toxicity_assessment': self.assess_toxicity(),
        }

        # Pharmacokinetic analysis
        if len(self.time_points) > 1:
            times = np.array([tp.time / 3600.0 for tp in self.time_points])
            concentrations = np.array([tp.drug_concentration_arterial for tp in self.time_points])

            pk = PharmacokineticsModel()
            results['pharmacokinetics'] = {
                'AUC': float(pk.calculate_auc(concentrations, times)),
                'Cmax': float(pk.calculate_cmax_tmax(concentrations, times)[0]),
                'Tmax': float(pk.calculate_cmax_tmax(concentrations, times)[1]),
                'half_life': float(pk.calculate_half_life(concentrations, times)),
            }

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nResults exported to: {filepath}")

    def export_csv(self, filepath: str) -> None:
        """
        Export simulation results to CSV format

        Args:
            filepath: Path to output CSV file
        """
        import csv

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='') as f:
            if not self.time_points:
                return

            # Write header
            fieldnames = list(asdict(self.time_points[0]).keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Write data
            for tp in self.time_points:
                writer.writerow(asdict(tp))

        print(f"Results exported to CSV: {filepath}")

    def plot_results(self, filepath: Optional[str] = None) -> None:
        """
        Plot simulation results

        Args:
            filepath: Optional path to save figure
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Matplotlib not available for plotting")
            return

        if not self.time_points:
            print("No data to plot")
            return

        times = np.array([tp.time / 3600.0 for tp in self.time_points])

        fig, axes = plt.subplots(3, 2, figsize=(15, 12))

        # Drug concentration
        drug_conc = np.array([tp.drug_concentration_arterial for tp in self.time_points])
        axes[0, 0].plot(times, drug_conc, 'b-', linewidth=2)
        axes[0, 0].set_xlabel('Time (hours)')
        axes[0, 0].set_ylabel('Drug Concentration (μM)')
        axes[0, 0].set_title('Pharmacokinetics')
        axes[0, 0].grid(True, alpha=0.3)

        # Cardiac function
        if self.heart:
            ef = np.array([tp.ejection_fraction for tp in self.time_points])
            axes[0, 1].plot(times, ef * 100, 'r-', linewidth=2)
            axes[0, 1].set_xlabel('Time (hours)')
            axes[0, 1].set_ylabel('Ejection Fraction (%)')
            axes[0, 1].set_title('Cardiac Function')
            axes[0, 1].axhline(y=50, color='k', linestyle='--', alpha=0.3)
            axes[0, 1].grid(True, alpha=0.3)

        # Liver function (ALT)
        if self.liver:
            alt = np.array([tp.alt for tp in self.time_points])
            axes[1, 0].plot(times, alt, 'g-', linewidth=2)
            axes[1, 0].set_xlabel('Time (hours)')
            axes[1, 0].set_ylabel('ALT (U/L)')
            axes[1, 0].set_title('Liver Function')
            axes[1, 0].axhline(y=40, color='k', linestyle='--', alpha=0.3, label='Normal')
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].legend()

        # Biomarkers (Troponin)
        if self.heart:
            trop = np.array([tp.troponin_i for tp in self.time_points])
            axes[1, 1].plot(times, trop, 'm-', linewidth=2)
            axes[1, 1].set_xlabel('Time (hours)')
            axes[1, 1].set_ylabel('Troponin I (ng/mL)')
            axes[1, 1].set_title('Cardiac Injury Biomarker')
            axes[1, 1].axhline(y=0.04, color='k', linestyle='--', alpha=0.3, label='Threshold')
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].legend()

        # Viability
        heart_viab = np.array([tp.heart_viability for tp in self.time_points])
        liver_viab = np.array([tp.liver_viability for tp in self.time_points])
        axes[2, 0].plot(times, heart_viab * 100, 'r-', linewidth=2, label='Heart')
        axes[2, 0].plot(times, liver_viab * 100, 'g-', linewidth=2, label='Liver')
        axes[2, 0].set_xlabel('Time (hours)')
        axes[2, 0].set_ylabel('Viability (%)')
        axes[2, 0].set_title('Organ Viability')
        axes[2, 0].legend()
        axes[2, 0].grid(True, alpha=0.3)

        # Inflammation
        if self.immune_system:
            il6 = np.array([tp.il6 for tp in self.time_points])
            axes[2, 1].plot(times, il6, 'orange', linewidth=2)
            axes[2, 1].set_xlabel('Time (hours)')
            axes[2, 1].set_ylabel('IL-6 (pg/mL)')
            axes[2, 1].set_title('Inflammatory Response')
            axes[2, 1].grid(True, alpha=0.3)

        plt.tight_layout()

        if filepath:
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Figure saved to: {filepath}")
        else:
            plt.show()


if __name__ == "__main__":
    # Example: Run a simple simulation
    print("Multi-Organ Digital Twin - Example Simulation")

    # Configure simulation
    config = SimulationConfig(
        duration=2.0,  # 2 hours
        dt=0.01,
        output_interval=60.0,
        drug_name="test_compound",
        dose_mg=100.0,
        route="IV"
    )

    # Create digital twin
    twin = MultiOrganDigitalTwin(config)

    # Create test drug
    drug = Ligand(
        name="test_compound",
        concentration=0.0,
        molecular_weight=400.0,
        clearance_rate=0.2
    )

    # Run simulation
    results = twin.simulate(drug)

    # Assess toxicity
    toxicity = twin.assess_toxicity()
    print(f"\nToxicity Assessment:")
    print(f"  Overall Safety: {toxicity['overall_safety']}")
    print(f"  Average Viability: {toxicity.get('average_viability', 'N/A'):.3f}")

    # Export results
    twin.export_results("results/digital_twin_output.json")
    twin.export_csv("results/digital_twin_output.csv")

    print("\nDigital twin orchestrator ready!")
