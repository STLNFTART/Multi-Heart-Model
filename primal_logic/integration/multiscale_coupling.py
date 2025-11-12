"""
Multiscale Coupling Integration Layer

Connects multiple biological scales:
- Molecular: Ligand-receptor binding
- Cellular: Immune signaling, hepatocyte/cardiomyocyte dynamics
- Organ: Liver and heart function
- Systemic: Circulation and whole-body distribution

Implements bidirectional feedback across scales.

Architecture:
    Molecular ↔ Cellular ↔ Organ ↔ Systemic

Example feedback loops:
- Drug → Receptor → Immune → Liver/Heart dysfunction → Altered circulation
- Stress → Autonomic → Heart rate → Circulation → Organ perfusion
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Optional, Dict, Callable
from dataclasses import dataclass

from ..molecular.ligand_receptor import LigandReceptor
from ..cellular.immune_signaling import ImmuneSignaling
from ..organ.liver.hepatocyte import HepatocytePopulation
from ..organ.liver.metabolism import LiverMetabolism
from ..organ.liver.toxicity import LiverToxicity
from ..organ.cardiac.cardiomyocyte import CardiomyocyteModel
from ..organ.cardiac.toxicity import CardiacToxicity
from ..systemic.circulation import SystemicCirculation


@dataclass
class MultiscaleCouplingParameters:
    """Parameters for multiscale coupling"""
    # Molecular → Cellular coupling
    receptor_to_immune_gain: float = 0.5

    # Cellular → Organ coupling
    immune_to_liver_gain: float = 0.3
    immune_to_heart_gain: float = 0.2

    # Organ → Systemic coupling
    liver_to_circulation_gain: float = 1.0
    heart_to_circulation_gain: float = 1.0

    # Systemic → Organ feedback
    circulation_to_liver_gain: float = 0.8
    circulation_to_heart_gain: float = 0.8

    # Timescales
    dt: float = 0.01  # Integration timestep (hours)


class MultiscaleCoupling:
    """
    Orchestrates bidirectional coupling across biological scales.

    State organization:
    - Molecular: Receptor occupancy [R]
    - Cellular: Immune states [I_pro, I_anti]
    - Organ (liver): Hepatocyte states [N_viable, N_damaged, N_dead, ATP, GSH]
    - Organ (cardiac): Cardiomyocyte states [V, V', Ca, ATP]
    - Systemic: Circulation states [C_art, C_ven, C_liver, C_heart, C_brain, C_other]
    - Toxicity tracking: Cumulative damage scores

    Usage:
        >>> coupling = MultiscaleCoupling()
        >>> coupling.set_drug_dosing(lambda t: 100.0 if t < 0.1 else 0.0)
        >>> times, results = coupling.simulate(t_span=(0, 48), dt=0.01)
    """

    def __init__(self, params: Optional[MultiscaleCouplingParameters] = None):
        self.params = params or MultiscaleCouplingParameters()

        # Initialize subsystems
        self.ligand_receptor = LigandReceptor()
        self.immune_signaling = ImmuneSignaling()
        self.hepatocytes = HepatocytePopulation()
        self.liver_metabolism = LiverMetabolism()
        self.liver_toxicity = LiverToxicity()
        self.cardiomyocyte = CardiomyocyteModel()
        self.cardiac_toxicity = CardiacToxicity()
        self.circulation = SystemicCirculation()

        # Drug dosing function
        self._drug_dosing_func = lambda t: 0.0

        # Store baseline metrics for comparison
        self.baseline_cardiac_metrics = None

    def set_drug_dosing(self, func: Callable[[float], float]):
        """
        Set drug dosing schedule.

        Args:
            func: Time (hours) -> dose rate (μM*L/hr)
        """
        self._drug_dosing_func = func

    def configure_drug_pathway(
        self,
        drug_name: str,
        cyp_isoform: str,
        hERG_IC50: float = 10.0,
        hepatotoxic: bool = False
    ):
        """
        Configure drug-specific pathways.

        Args:
            drug_name: Drug identifier
            cyp_isoform: CYP450 isoform for metabolism
            hERG_IC50: IC50 for hERG blockade (μM)
            hepatotoxic: Whether drug is hepatotoxic
        """
        # Add metabolism pathway
        from ..organ.liver.metabolism import CYP450Isoform
        iso_enum = CYP450Isoform[cyp_isoform.replace('.', '')]
        self.liver_metabolism.add_drug_pathway(drug_name, iso_enum, 1.0)

        # Set cardiac toxicity parameters
        self.cardiac_toxicity.params.hERG_IC50 = hERG_IC50

    def molecular_to_cellular_coupling(
        self,
        receptor_occupancy: float
    ) -> float:
        """
        Map receptor occupancy to immune activation signal.

        Receptor binding → Damage-associated molecular patterns (DAMPs) → Immune activation
        """
        immune_signal = self.params.receptor_to_immune_gain * receptor_occupancy

        return immune_signal

    def cellular_to_organ_coupling(
        self,
        immune_intensity: float
    ) -> Tuple[float, float]:
        """
        Map immune intensity to organ damage signals.

        Returns:
            (liver_damage_signal, cardiac_damage_signal)
        """
        liver_damage = self.params.immune_to_liver_gain * immune_intensity
        cardiac_damage = self.params.immune_to_heart_gain * immune_intensity

        return liver_damage, cardiac_damage

    def organ_to_systemic_coupling(
        self,
        liver_metabolism_rate: float,
        cardiac_contractility: float
    ) -> Tuple[float, float]:
        """
        Map organ function to systemic parameters.

        Returns:
            (drug_clearance, cardiac_output)
        """
        drug_clearance = self.params.liver_to_circulation_gain * liver_metabolism_rate
        cardiac_output = self.params.heart_to_circulation_gain * cardiac_contractility / 20.0

        # Ensure cardiac output is within physiological range
        cardiac_output = np.clip(cardiac_output, 2.0, 8.0)

        return drug_clearance, cardiac_output

    def systemic_to_organ_feedback(
        self,
        C_liver: float,
        C_heart: float
    ) -> Tuple[float, float]:
        """
        Map systemic drug concentrations to organ exposure.

        Returns:
            (liver_drug_exposure, heart_drug_exposure)
        """
        liver_exposure = self.params.circulation_to_liver_gain * C_liver
        heart_exposure = self.params.circulation_to_heart_gain * C_heart

        return liver_exposure, heart_exposure

    def integrate_step(self, t: float, dt: float) -> Dict[str, any]:
        """
        Perform one multiscale integration step.

        Returns:
            Dictionary with all subsystem states and metrics
        """
        # === SYSTEMIC LEVEL ===
        # Get current circulation state
        C_art, C_ven, C_liver, C_heart, C_brain, C_other = self.circulation.state

        # Drug dosing
        drug_dose = self._drug_dosing_func(t)

        # === ORGAN LEVEL ===
        # Liver function
        hepatocyte_viability = self.hepatocytes.get_viability_fraction()
        liver_clearance, _ = self.liver_metabolism.metabolize_drug(
            "drug", C_liver, hepatocyte_viability
        )

        # Cardiac function
        cardio_state = self.cardiomyocyte.state
        cardiac_contractility = self.cardiomyocyte.compute_contractility(cardio_state[2])

        # Map organ function → systemic parameters
        drug_clearance, cardiac_output = self.organ_to_systemic_coupling(
            liver_clearance, cardiac_contractility
        )

        # Update circulation
        self.circulation.set_drug_input(lambda t_inner: drug_dose)
        self.circulation.set_metabolism_function(lambda C_liv, t_inner: liver_clearance)
        self.circulation.set_cardiac_output(lambda t_inner: cardiac_output)
        self.circulation.integrate_step(dt, t)

        # === SYSTEMIC → ORGAN FEEDBACK ===
        C_liver_new, C_heart_new = self.circulation.state[2], self.circulation.state[3]
        liver_exposure, heart_exposure = self.systemic_to_organ_feedback(C_liver_new, C_heart_new)

        # === MOLECULAR LEVEL ===
        # Ligand-receptor binding (drug concentration drives it)
        self.ligand_receptor.set_ligand_function(lambda t_inner: C_art)
        self.ligand_receptor.integrate_step(dt, t)
        receptor_occupancy = self.ligand_receptor.state

        # === CELLULAR LEVEL ===
        # Immune signaling
        immune_damage_signal = self.molecular_to_cellular_coupling(receptor_occupancy)

        # Add damage from toxicity
        liver_tox_damage = self.liver_toxicity.state[0]
        cardiac_tox_damage = self.cardiac_toxicity.state[0]
        total_damage = immune_damage_signal + 0.5 * (liver_tox_damage + cardiac_tox_damage)

        self.immune_signaling.set_damage_signal(lambda t_inner: total_damage)
        self.immune_signaling.integrate_step(dt, t)
        immune_intensity = self.immune_signaling.state

        # === CELLULAR → ORGAN ===
        liver_damage, cardiac_damage = self.cellular_to_organ_coupling(immune_intensity)

        # Update hepatocytes
        self.hepatocytes.set_toxicity_function(lambda t_inner: liver_exposure * 0.01)
        self.hepatocytes.set_oxidative_stress_function(lambda t_inner: liver_damage)
        self.hepatocytes.integrate_step(dt, t)

        # Update liver toxicity
        self.liver_toxicity.set_drug_concentration(lambda t_inner: C_liver_new)
        self.liver_toxicity.set_metabolite_concentration(lambda t_inner: 0.0)  # Simplified
        self.liver_toxicity.set_immune_signal(lambda t_inner: immune_intensity)
        self.liver_toxicity.integrate_step(dt, t)

        # Update cardiomyocyte
        hERG_block = min(0.9, C_heart_new / (self.cardiac_toxicity.params.hERG_IC50 + C_heart_new))
        drug_effects = {
            'hERG_block': hERG_block,
            'mitochondrial': cardiac_damage * 0.5
        }
        self.cardiomyocyte.set_drug_effect(lambda t_inner: drug_effects)
        self.cardiomyocyte.integrate_step(dt, t)

        # Update cardiac toxicity
        if self.baseline_cardiac_metrics is None:
            self.baseline_cardiac_metrics = {
                'APD': 0.3,
                'contractility': 50.0
            }

        current_cardiac_metrics = {
            'APD': 0.3 * (1 + 0.5 * hERG_block),
            'Ca': cardio_state[2],
            'contractility': cardiac_contractility,
            'ATP': cardio_state[3]
        }

        self.cardiac_toxicity.set_drug_concentration(lambda t_inner: C_heart_new)
        self.cardiac_toxicity.integrate_step(dt, t, current_cardiac_metrics)

        # Update enzyme levels (chronic adaptation)
        self.liver_metabolism.update_enzyme_levels(dt, {"drug": C_liver_new})

        # Collect results
        results = {
            # Molecular
            'receptor_occupancy': receptor_occupancy,

            # Cellular
            'immune_intensity': immune_intensity,
            'immune_anti': self.immune_signaling.anti_inflammatory,

            # Organ - Liver
            'hepatocyte_viability': hepatocyte_viability,
            'liver_ATP': self.hepatocytes.state[3],
            'liver_GSH': self.hepatocytes.state[4],
            'liver_toxicity': self.liver_toxicity.state[0],

            # Organ - Cardiac
            'cardiac_V': cardio_state[0],
            'cardiac_Ca': cardio_state[2],
            'cardiac_ATP': cardio_state[3],
            'cardiac_contractility': cardiac_contractility,
            'cardiac_toxicity': self.cardiac_toxicity.state[0],

            # Systemic
            'C_arterial': C_art,
            'C_liver': C_liver_new,
            'C_heart': C_heart_new,
            'cardiac_output': cardiac_output,
            'liver_clearance': liver_clearance,

            # Integrated metrics
            'total_damage_signal': total_damage,
            'hERG_block': hERG_block
        }

        return results

    def simulate(
        self,
        t_span: Tuple[float, float],
        dt: Optional[float] = None
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Run complete multiscale simulation.

        Args:
            t_span: (start_time, end_time) in hours
            dt: Integration timestep (hours)

        Returns:
            (times, results_dict) where results_dict contains timeseries for all variables
        """
        if dt is None:
            dt = self.params.dt

        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt)

        times = np.linspace(t_start, t_end, n_steps)

        # Initialize result storage
        result_keys = None
        results_arrays = None

        for i, t in enumerate(times):
            step_results = self.integrate_step(t, dt)

            # Initialize on first step
            if result_keys is None:
                result_keys = list(step_results.keys())
                results_arrays = {key: np.zeros(n_steps) for key in result_keys}

            # Store results
            for key in result_keys:
                results_arrays[key][i] = step_results[key]

        return times, results_arrays

    def reset(self):
        """Reset all subsystems to initial state"""
        self.ligand_receptor.reset()
        self.immune_signaling.reset()
        self.hepatocytes.reset()
        self.liver_metabolism.reset()
        self.liver_toxicity.reset()
        self.cardiomyocyte.reset()
        self.cardiac_toxicity.reset()
        self.circulation.reset()
        self.baseline_cardiac_metrics = None


if __name__ == "__main__":
    print("=" * 70)
    print("MULTISCALE COUPLING INTEGRATION")
    print("=" * 70)

    # Example: Drug administration with multiscale effects
    print("\n1. Simulating IV bolus with multiscale effects...")

    coupling = MultiscaleCoupling()

    # Configure drug (e.g., dofetilide - potent hERG blocker)
    coupling.configure_drug_pathway(
        drug_name="drug",
        cyp_isoform="CYP3A4",
        hERG_IC50=5.0,  # Low IC50 = potent blocker
        hepatotoxic=False
    )

    # IV bolus at t=0
    def bolus_dose(t):
        if t < 0.05:
            return 500.0  # μM*L/hr
        return 0.0

    coupling.set_drug_dosing(bolus_dose)

    # Run simulation
    times, results = coupling.simulate(t_span=(0, 24), dt=0.1)

    # Report key findings
    print(f"\n   Time Course Analysis:")
    print(f"   {'Time (hr)':<12} {'C_art':<10} {'hERG':<10} {'Cardiac':<12} {'Liver':<10}")
    print("   " + "-" * 60)

    for tp in [0, 1, 6, 12, 24]:
        idx = int(tp / 0.1)
        if idx < len(times):
            print(f"   {tp:<12.1f} "
                  f"{results['C_arterial'][idx]:<10.2f} "
                  f"{results['hERG_block'][idx]:<10.2%} "
                  f"{results['cardiac_toxicity'][idx]:<12.3f} "
                  f"{results['liver_toxicity'][idx]:<10.3f}")

    print(f"\n   Peak hERG blockade: {np.max(results['hERG_block']):.1%}")
    print(f"   Peak cardiac toxicity: {np.max(results['cardiac_toxicity']):.3f}")
    print(f"   Final hepatocyte viability: {results['hepatocyte_viability'][-1]:.1%}")

    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("=" * 70)
    print("✓ BIDIRECTIONAL: Feedback across all scales")
    print("✓ MOLECULAR → SYSTEMIC: Complete hierarchy")
    print("✓ REALISTIC: Physiologically-based parameters")
    print("✓ EMERGENT: System-level toxicity from molecular events")
    print("=" * 70)
