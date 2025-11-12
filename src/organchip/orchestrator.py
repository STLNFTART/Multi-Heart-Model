"""Organ chip suite orchestrator - complete system integration.

This module provides the top-level orchestration of all organ chip models,
including:
- System initialization
- Simulation execution
- Data collection and export
- Visualization helpers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Dict, List, Optional
import json

from .cardiac.cardiotoxicity import CardiacCell, CardiotoxicityModel
from .liver.hepatocyte import Hepatocyte, LiverToxicity
from .immune.cytokines import CytokineNetwork, InflammatoryResponse
from .circulation.pbpk import MultiOrganPBPK, SystemicCirculation
from .multiscale.integration import MultiscaleCoupling, OrganInteractions


@dataclass
class OrganChipSuite:
    """Complete organ-on-a-chip platform orchestrator.

    Integrates all subsystems:
    - Cardiac organ chip with electrophysiology
    - Liver organ chip with metabolism and toxicity
    - Immune system with cytokine signaling
    - Systemic circulation (PBPK)
    - Multiscale coupling

    Provides unified interface for:
    - Drug screening
    - Toxicity prediction
    - Multi-organ interaction studies
    """

    # Core subsystems
    cardiac: CardiacCell = field(default_factory=CardiacCell)
    liver: Hepatocyte = field(default_factory=Hepatocyte)
    immune: InflammatoryResponse = field(default_factory=InflammatoryResponse)
    circulation: MultiOrganPBPK = field(default_factory=MultiOrganPBPK)
    coupling: MultiscaleCoupling = field(default_factory=MultiscaleCoupling)

    # Configuration
    verbose: bool = True

    def __post_init__(self):
        """Link subsystems to coupling framework."""
        self.coupling.cardiac_model = self.cardiac
        self.coupling.liver_model = self.liver
        self.coupling.immune_model = self.immune.cytokine_network
        self.coupling.circulation_model = self.circulation

    def initialize_state(
        self,
        drug_amount_mg: float = 0.0
    ) -> Dict[str, any]:
        """Initialize complete system state.

        Parameters
        ----------
        drug_amount_mg : float
            Initial drug amount in plasma (mg)

        Returns
        -------
        dict
            Complete initialized state
        """
        # Circulation state (all organs)
        circ_state = {'plasma': drug_amount_mg}
        for organ in self.circulation.organs:
            circ_state[organ] = 0.0

        # Liver state (10 variables)
        # [Drug_intra, Metabolite, Reactive, Conjugate, GSH, ATP, ROS, Viability, ALT, AST]
        liver_state = {
            'Drug_intra': 0.0,
            'Metabolite': 0.0,
            'Reactive': 0.0,
            'Conjugate': 0.0,
            'GSH': 10.0,           # Baseline GSH
            'ATP': 5.0,            # Baseline ATP
            'ROS': 0.1,            # Low baseline ROS
            'Cell_viability': 1.0, # Full viability
            'ALT': 20.0,           # Normal ALT
            'AST': 25.0,           # Normal AST
        }

        # Cardiac state (10 variables)
        # [V, m, h, d, f, xr, Ca_i, Force, Troponin, BNP]
        cardiac_state = {
            'V': -85.0,            # Resting potential
            'm': 0.01,
            'h': 0.99,
            'd': 0.01,
            'f': 0.99,
            'xr': 0.01,
            'Ca_i': 0.1,           # Baseline calcium
            'Force': 0.0,
            'Troponin': 0.01,      # Normal troponin
            'BNP': 20.0,           # Normal BNP
            'APD': 300.0,          # Normal APD
            'cardiac_output': 300.0,  # Normal CO
            'drug_exposure': 0.0,
            'inflammation_effect': 0.0,
        }

        # Immune state (5 cytokines)
        immune_state = {
            'TNFa': 0.5,
            'IL1b': 0.3,
            'IL6': 0.4,
            'IL10': 1.0,
            'TGFb': 0.8,
        }

        return {
            'circulation': circ_state,
            'liver': liver_state,
            'cardiac': cardiac_state,
            'immune': immune_state,
        }

    def simulate_drug_exposure(
        self,
        dose_mg: float,
        duration_hours: float,
        dt: float = 0.1,
        dosing_type: str = 'bolus',
        infusion_duration: float = 1.0
    ) -> List[Tuple[float, Dict[str, any]]]:
        """Simulate drug exposure across multi-organ system.

        Parameters
        ----------
        dose_mg : float
            Drug dose (mg)
        duration_hours : float
            Simulation duration (hours)
        dt : float
            Time step (hours)
        dosing_type : str
            'bolus' or 'infusion'
        infusion_duration : float
            Duration of infusion (hours) if dosing_type='infusion'

        Returns
        -------
        list
            Time series of complete system state
        """
        if self.verbose:
            print(f"Simulating {dosing_type} dose of {dose_mg} mg for {duration_hours} hours")

        # Initialize state
        if dosing_type == 'bolus':
            state = self.initialize_state(drug_amount_mg=dose_mg)
            dosing_schedule = None
        elif dosing_type == 'infusion':
            state = self.initialize_state(drug_amount_mg=0.0)
            dose_rate = dose_mg / infusion_duration
            dosing_schedule = [(0.0, dose_rate)]
        else:
            raise ValueError(f"Unknown dosing_type: {dosing_type}")

        # Run simulation
        trajectory = self.coupling.simulate_integrated_system(
            initial_state=state,
            t_span=(0.0, duration_hours),
            dt=dt,
            dosing_schedule=dosing_schedule
        )

        if self.verbose:
            print(f"Simulation complete: {len(trajectory)} time points")

        return trajectory

    def assess_toxicity(
        self,
        trajectory: List[Tuple[float, Dict[str, any]]]
    ) -> Dict[str, any]:
        """Assess multi-organ toxicity from simulation trajectory.

        Parameters
        ----------
        trajectory : list
            Simulation time series

        Returns
        -------
        dict
            Comprehensive toxicity assessment
        """
        # Get final state
        t_final, state_final = trajectory[-1]

        liver_state = state_final['liver']
        cardiac_state = state_final['cardiac']
        immune_state = state_final['immune']

        # --- Liver Toxicity Assessment ---
        liver_tox = self.liver.toxicity.assess_hepatotoxicity(
            GSH=liver_state['GSH'],
            ATP=liver_state['ATP'],
            ALT=liver_state['ALT'],
            AST=liver_state['AST'],
            cell_viability=liver_state['Cell_viability']
        )

        # --- Cardiac Toxicity Assessment ---
        # Find peak and baseline APD
        APDs = [s['cardiac'].get('APD', 300.0) for t, s in trajectory]
        APD_baseline = APDs[0] if len(APDs) > 0 else 300.0
        APD_final = cardiac_state.get('APD', 300.0)

        cardiac_tox = self.cardiac.toxicity.assess_toxicity(
            APD=APD_final,
            APD_baseline=APD_baseline,
            force=cardiac_state.get('Force', 50.0),
            force_baseline=50.0,
            troponin=cardiac_state.get('Troponin', 0.01),
            BNP=cardiac_state.get('BNP', 20.0)
        )

        # --- Immune Response Assessment ---
        inflammatory_index = self.immune.cytokine_network.inflammatory_index(
            (immune_state['TNFa'], immune_state['IL1b'], immune_state['IL6'],
             immune_state['IL10'], immune_state['TGFb'])
        )

        # --- Overall Assessment ---
        overall_score = (
            0.4 * liver_tox['toxicity_score'] +
            0.4 * cardiac_tox['toxicity_score'] +
            0.2 * min(1.0, inflammatory_index / 5.0)
        )

        if overall_score < 0.2:
            overall_severity = "None - Safe"
        elif overall_score < 0.4:
            overall_severity = "Mild - Monitor"
        elif overall_score < 0.6:
            overall_severity = "Moderate - Caution"
        elif overall_score < 0.8:
            overall_severity = "Severe - High Risk"
        else:
            overall_severity = "Critical - Contraindicated"

        return {
            'overall_toxicity_score': overall_score,
            'overall_severity': overall_severity,
            'liver': liver_tox,
            'cardiac': cardiac_tox,
            'immune': {
                'inflammatory_index': inflammatory_index,
                'TNFa_fold': immune_state['TNFa'] / 0.5,
                'IL6_fold': immune_state['IL6'] / 0.4,
            },
            'time_hours': t_final,
        }

    def export_results(
        self,
        trajectory: List[Tuple[float, Dict[str, any]]],
        toxicity_assessment: Dict[str, any],
        filename: str = "organ_chip_results.json"
    ) -> None:
        """Export simulation results to JSON.

        Parameters
        ----------
        trajectory : list
            Simulation time series
        toxicity_assessment : dict
            Toxicity assessment results
        filename : str
            Output filename
        """
        # Extract key metrics
        metrics = self.coupling.extract_key_metrics(trajectory)

        # Prepare export data
        export_data = {
            'toxicity_assessment': toxicity_assessment,
            'time_series': metrics,
            'metadata': {
                'duration_hours': trajectory[-1][0] if trajectory else 0.0,
                'num_timepoints': len(trajectory),
            }
        }

        # Write to file
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        if self.verbose:
            print(f"Results exported to {filename}")

    def run_complete_study(
        self,
        dose_mg: float,
        duration_hours: float = 48.0,
        dt: float = 0.1,
        export_file: Optional[str] = None
    ) -> Tuple[List[Tuple[float, Dict]], Dict]:
        """Run complete drug toxicity study.

        Parameters
        ----------
        dose_mg : float
            Drug dose (mg)
        duration_hours : float
            Study duration (hours)
        dt : float
            Time step (hours)
        export_file : str, optional
            Export filename (if provided)

        Returns
        -------
        tuple
            (trajectory, toxicity_assessment)
        """
        if self.verbose:
            print("="*60)
            print("ORGAN CHIP SUITE - DRUG TOXICITY STUDY")
            print("="*60)

        # Run simulation
        trajectory = self.simulate_drug_exposure(
            dose_mg=dose_mg,
            duration_hours=duration_hours,
            dt=dt,
            dosing_type='bolus'
        )

        # Assess toxicity
        tox_assessment = self.assess_toxicity(trajectory)

        if self.verbose:
            print("\n" + "="*60)
            print("TOXICITY ASSESSMENT")
            print("="*60)
            print(f"Overall Score: {tox_assessment['overall_toxicity_score']:.3f}")
            print(f"Severity: {tox_assessment['overall_severity']}")
            print(f"\nLiver: {tox_assessment['liver']['severity']}")
            print(f"  - ALT elevation: {tox_assessment['liver']['ALT_elevation_fold']:.1f}x")
            print(f"  - Cell viability: {tox_assessment['liver']['cell_viability']:.1%}")
            print(f"\nCardiac: {tox_assessment['cardiac']['severity']}")
            print(f"  - QTc change: {tox_assessment['cardiac']['QTc_prolongation_ms']:.1f} ms")
            print(f"  - Arrhythmia risk: {tox_assessment['cardiac']['arrhythmia_risk']}")
            print(f"\nInflammatory Index: {tox_assessment['immune']['inflammatory_index']:.2f}")
            print("="*60)

        # Export if requested
        if export_file:
            self.export_results(trajectory, tox_assessment, export_file)

        return trajectory, tox_assessment


def create_default_organ_chip_suite() -> OrganChipSuite:
    """Create organ chip suite with default parameters.

    Returns
    -------
    OrganChipSuite
        Configured organ chip platform
    """
    return OrganChipSuite(verbose=True)
