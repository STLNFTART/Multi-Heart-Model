"""
Liver Chip Module - Drug Metabolism and Hepatotoxicity
Part of Multi-Heart-Model Organ-on-Chip Suite

Built on Primal Logic Framework: dx/dt = α*θ - λ*x
"""

import numpy as np
from typing import Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class LiverParameters:
    """Physiological parameters for liver chip model"""

    # Hepatocyte population
    N_initial: float = 1e6              # Initial viable cell count
    N_max: float = 2e6                  # Carrying capacity
    growth_rate: float = 0.01           # Per hour division rate
    baseline_death_rate: float = 0.001  # Per hour apoptosis
    repair_rate: float = 0.05           # Damage recovery rate

    # Metabolism
    CYP450_Vmax: float = 100.0          # Max metabolism rate (μM/hr)
    CYP450_Km: float = 10.0             # Michaelis constant (μM)
    metabolite_toxicity: float = 0.5    # Relative toxicity vs parent

    # Bioenergetics
    ATP_baseline: float = 5.0           # mM
    ATP_production_rate: float = 2.0    # mM/hr
    ATP_consumption_rate: float = 1.5   # mM/hr
    ATP_critical: float = 1.0           # Below this = cell death

    # Antioxidant capacity
    GSH_baseline: float = 10.0          # mM glutathione
    GSH_synthesis_rate: float = 2.0     # mM/hr
    GSH_consumption_rate: float = 0.5   # mM/hr per μM drug
    GSH_critical: float = 2.0           # Below this = oxidative stress

    # Circulation
    hepatic_blood_flow: float = 1.5     # L/hr (fraction of cardiac output)
    volume_liver: float = 0.001         # L (1 mL for chip)


class HepatocytePopulation:
    """
    Hepatocyte population dynamics with drug-induced damage
    """

    def __init__(self, params: Optional[LiverParameters] = None):
        self.params = params or LiverParameters()

    def viability_dynamics(
        self,
        N_viable: float,
        N_damaged: float,
        drug_concentration: float,
        metabolite_concentration: float,
        ATP_level: float,
        GSH_level: float
    ) -> Tuple[float, float, float]:
        """
        Cell population dynamics with damage and death

        Returns: (dN_viable/dt, dN_damaged/dt, dN_dead/dt)
        """
        params = self.params
        N_total = N_viable + N_damaged

        # Toxicity function (Primal Logic decay term λ)
        toxicity_score = self._compute_toxicity(
            drug_concentration,
            metabolite_concentration,
            ATP_level,
            GSH_level
        )

        # Viable cell dynamics
        growth = params.growth_rate * N_viable * (1 - N_total / params.N_max)
        damage = toxicity_score * N_viable
        repair_gain = params.repair_rate * N_damaged

        dN_viable = growth - damage + repair_gain

        # Damaged cell dynamics
        irreversible_damage = (toxicity_score * 2.0) * N_damaged  # Damaged cells die faster

        dN_damaged = damage - repair_gain - irreversible_damage

        # Dead cells (accumulate, no clearance in simplified model)
        dN_dead = irreversible_damage

        return dN_viable, dN_damaged, dN_dead

    def _compute_toxicity(
        self,
        drug: float,
        metabolite: float,
        ATP: float,
        GSH: float
    ) -> float:
        """
        Compute integrated toxicity score from multiple stressors
        """
        params = self.params

        # Direct chemical toxicity (concentration-dependent)
        chem_tox = 0.01 * (drug + params.metabolite_toxicity * metabolite)

        # Energy depletion toxicity
        if ATP < params.ATP_critical:
            energy_tox = 0.5 * (1 - ATP / params.ATP_critical)
        else:
            energy_tox = 0.0

        # Oxidative stress toxicity
        if GSH < params.GSH_critical:
            oxidative_tox = 0.3 * (1 - GSH / params.GSH_critical)
        else:
            oxidative_tox = 0.0

        # Combined toxicity (multiplicative for synergy)
        total_toxicity = (chem_tox + energy_tox + oxidative_tox) * (1 + 0.5 * energy_tox)

        return np.clip(total_toxicity, 0.0, 1.0)


class LiverMetabolism:
    """
    Drug metabolism via CYP450 system
    """

    def __init__(self, params: Optional[LiverParameters] = None):
        self.params = params or LiverParameters()

    def metabolism_rate(
        self,
        drug_concentration: float,
        CYP450_activity: float,
        N_viable: float
    ) -> Tuple[float, float]:
        """
        Michaelis-Menten drug metabolism

        Returns: (drug_clearance_rate, metabolite_production_rate)
        """
        params = self.params

        # Michaelis-Menten kinetics
        # V = Vmax * [S] / (Km + [S])
        Vmax_effective = params.CYP450_Vmax * CYP450_activity * (N_viable / params.N_initial)

        clearance = (Vmax_effective * drug_concentration) / (params.CYP450_Km + drug_concentration)

        # Assume 1:1 stoichiometry (simplified)
        production = clearance

        return clearance, production

    def enzyme_activity_dynamics(
        self,
        CYP450_activity: float,
        drug_concentration: float,
        ATP_level: float
    ) -> float:
        """
        CYP450 activity affected by substrate and energy

        Returns: dActivity/dt
        """
        params = self.params

        # Baseline activity
        baseline = 1.0

        # Induction by substrate (increase with prolonged exposure)
        induction = 0.01 * drug_concentration

        # Inhibition by energy depletion
        if ATP_level < params.ATP_baseline:
            inhibition = 0.1 * (1 - ATP_level / params.ATP_baseline)
        else:
            inhibition = 0.0

        # Primal Logic: cautious accumulation
        dActivity = 0.1 * (induction) - 0.05 * (CYP450_activity - baseline) - inhibition

        return dActivity


class LiverBioenergetics:
    """
    ATP and GSH dynamics
    """

    def __init__(self, params: Optional[LiverParameters] = None):
        self.params = params or LiverParameters()

    def ATP_dynamics(
        self,
        ATP_level: float,
        drug_concentration: float,
        metabolic_load: float
    ) -> float:
        """
        Cellular energy balance

        Primal Logic: α (production) - λ (consumption + toxicity)
        """
        params = self.params

        # Production (oxygen-dependent, simplified as constant here)
        production = params.ATP_production_rate

        # Basal consumption
        consumption = params.ATP_consumption_rate

        # Increased consumption from metabolic load
        metabolic_cost = 0.5 * metabolic_load

        # Drug-induced mitochondrial damage (decreases production)
        mito_damage = 0.1 * drug_concentration

        dATP = (production * (1 - mito_damage)) - (consumption + metabolic_cost)

        return dATP

    def GSH_dynamics(
        self,
        GSH_level: float,
        drug_concentration: float,
        metabolite_concentration: float
    ) -> float:
        """
        Glutathione (antioxidant) balance
        """
        params = self.params

        # Synthesis
        synthesis = params.GSH_synthesis_rate

        # Consumption by reactive species (drug-induced)
        consumption = params.GSH_consumption_rate * (drug_concentration + 2 * metabolite_concentration)

        dGSH = synthesis - consumption

        return dGSH


class LiverChipModel:
    """
    Integrated liver-on-chip model
    """

    def __init__(self, params: Optional[LiverParameters] = None):
        self.params = params or LiverParameters()
        self.population = HepatocytePopulation(params)
        self.metabolism = LiverMetabolism(params)
        self.bioenergetics = LiverBioenergetics(params)

    def state_derivatives(
        self,
        state: np.ndarray,
        t: float,
        drug_input: float,
        blood_flow: float
    ) -> np.ndarray:
        """
        Complete liver chip dynamics

        State vector:
        [0] N_viable: Viable hepatocytes
        [1] N_damaged: Damaged hepatocytes
        [2] N_dead: Dead hepatocytes
        [3] drug_conc: Drug concentration in liver (μM)
        [4] metabolite_conc: Metabolite concentration (μM)
        [5] CYP450_activity: Enzyme activity (normalized)
        [6] ATP_level: Cellular ATP (mM)
        [7] GSH_level: Glutathione (mM)
        """
        N_viable, N_damaged, N_dead, drug, metabolite, CYP_act, ATP, GSH = state

        # Cell population dynamics
        dN_viable, dN_damaged, dN_dead = self.population.viability_dynamics(
            N_viable, N_damaged, drug, metabolite, ATP, GSH
        )

        # Drug metabolism
        drug_clearance, metabolite_production = self.metabolism.metabolism_rate(
            drug, CYP_act, N_viable
        )

        # Drug pharmacokinetics (simplified)
        # Primal Logic: α (input + circulation) - λ (metabolism + outflow)
        drug_influx = blood_flow * drug_input / self.params.volume_liver
        drug_outflow = blood_flow * drug / self.params.volume_liver

        dDrug = drug_influx - drug_clearance - drug_outflow

        # Metabolite kinetics
        metabolite_outflow = blood_flow * metabolite / self.params.volume_liver
        metabolite_clearance = 0.1 * metabolite  # Simplified excretion

        dMetabolite = metabolite_production - metabolite_outflow - metabolite_clearance

        # Enzyme activity
        dCYP_act = self.metabolism.enzyme_activity_dynamics(CYP_act, drug, ATP)

        # Bioenergetics
        metabolic_load = drug_clearance / self.params.CYP450_Vmax
        dATP = self.bioenergetics.ATP_dynamics(ATP, drug, metabolic_load)
        dGSH = self.bioenergetics.GSH_dynamics(GSH, drug, metabolite)

        return np.array([
            dN_viable, dN_damaged, dN_dead,
            dDrug, dMetabolite,
            dCYP_act,
            dATP, dGSH
        ])

    def get_biomarkers(self, state: np.ndarray) -> Dict[str, float]:
        """
        Extract clinically relevant biomarkers
        """
        N_viable, N_damaged, N_dead, drug, metabolite, CYP_act, ATP, GSH = state

        # ALT/AST based on cell damage (U/L)
        cell_damage_fraction = N_damaged / self.params.N_initial
        ALT = 40 + 400 * cell_damage_fraction  # Normal ~40 U/L

        # LDH from cell death (U/L)
        cell_death_fraction = N_dead / self.params.N_initial
        LDH = 100 + 900 * cell_death_fraction  # Normal ~100 U/L

        # Synthetic function (albumin surrogate)
        viability_fraction = N_viable / self.params.N_initial
        albumin = 4.0 * viability_fraction  # Normal ~4 g/dL

        return {
            'ALT': ALT,
            'AST': ALT * 0.8,  # AST slightly lower than ALT
            'LDH': LDH,
            'Albumin': albumin,
            'ATP': ATP,
            'GSH': GSH,
            'Viability': viability_fraction * 100,
            'Drug_clearance': CYP_act,
            'Drug_conc': drug,
            'Metabolite_conc': metabolite
        }

    def simulate(
        self,
        t_span: Tuple[float, float],
        drug_dose_schedule: callable,
        blood_flow: float,
        dt: float = 0.01
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Run liver chip simulation

        Args:
            t_span: (t_start, t_end) in hours
            drug_dose_schedule: Function of time returning drug input concentration
            blood_flow: Hepatic blood flow (L/hr)
            dt: Timestep (hours)
        """
        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt)

        times = np.linspace(t_start, t_end, n_steps)
        states = np.zeros((n_steps, 8))

        # Initial conditions
        states[0] = np.array([
            self.params.N_initial,  # N_viable
            0.0,                     # N_damaged
            0.0,                     # N_dead
            0.0,                     # drug
            0.0,                     # metabolite
            1.0,                     # CYP450_activity
            self.params.ATP_baseline,
            self.params.GSH_baseline
        ])

        # RK4 integration
        for i in range(1, n_steps):
            t = times[i-1]
            y = states[i-1]

            drug_input = drug_dose_schedule(t)

            k1 = self.state_derivatives(y, t, drug_input, blood_flow)
            k2 = self.state_derivatives(y + 0.5*dt*k1, t + 0.5*dt, drug_input, blood_flow)
            k3 = self.state_derivatives(y + 0.5*dt*k2, t + 0.5*dt, drug_input, blood_flow)
            k4 = self.state_derivatives(y + dt*k3, t + dt, drug_input, blood_flow)

            states[i] = y + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

            # Ensure non-negative populations and bounded values
            states[i, 0:3] = np.maximum(states[i, 0:3], 0.0)
            states[i, 3:5] = np.clip(states[i, 3:5], 0.0, 1000.0)  # drug/metabolite
            states[i, 5] = np.clip(states[i, 5], 0.0, 2.0)  # CYP activity
            states[i, 6] = np.clip(states[i, 6], 0.0, 20.0)  # ATP
            states[i, 7] = np.clip(states[i, 7], 0.0, 20.0)  # GSH

        return times, states


# Example usage and validation
if __name__ == "__main__":
    print("Liver Chip Model - Acetaminophen Toxicity Simulation")
    print("=" * 70)

    # Initialize model
    liver = LiverChipModel()

    # Acetaminophen dosing schedule (therapeutic then toxic dose)
    def acetaminophen_dose(t):
        """Pulsed dosing: therapeutic for 24hr, then toxic dose"""
        if t < 24:
            return 50.0  # Therapeutic dose (μM)
        elif 24 <= t < 48:
            return 200.0  # Toxic dose (μM)
        else:
            return 0.0

    print("\nSimulating 72-hour exposure...")
    print("  0-24hr: Therapeutic dose (50 μM)")
    print("  24-48hr: Toxic dose (200 μM)")
    print("  48-72hr: Washout\n")

    # Run simulation
    times, states = liver.simulate(
        t_span=(0.0, 72.0),
        drug_dose_schedule=acetaminophen_dose,
        blood_flow=1.5,  # L/hr
        dt=0.1  # 6 minute timesteps
    )

    # Analyze key timepoints
    timepoints = [0, 12, 24, 36, 48, 60, 72]

    print("Timepoint Analysis:")
    print("-" * 70)
    print(f"{'Time (hr)':<10} {'Viability (%)':<15} {'ALT (U/L)':<12} {'ATP (mM)':<10} {'GSH (mM)':<10}")
    print("-" * 70)

    for tp in timepoints:
        idx = int(tp / 0.1)
        if idx < len(times):
            biomarkers = liver.get_biomarkers(states[idx])
            print(f"{tp:<10} {biomarkers['Viability']:<15.1f} "
                  f"{biomarkers['ALT']:<12.1f} {biomarkers['ATP']:<10.2f} "
                  f"{biomarkers['GSH']:<10.2f}")

    print("\n" + "=" * 70)
    print("Key Observations:")
    final_biomarkers = liver.get_biomarkers(states[-1])

    if final_biomarkers['Viability'] < 50:
        print("  ⚠ SEVERE HEPATOTOXICITY: <50% viable cells")
    elif final_biomarkers['Viability'] < 80:
        print("  ⚠ MODERATE HEPATOTOXICITY: 50-80% viable cells")
    else:
        print("  ✓ MINIMAL TOXICITY: >80% viable cells")

    if final_biomarkers['ALT'] > 200:
        print(f"  ⚠ ELEVATED ALT: {final_biomarkers['ALT']:.0f} U/L (normal <40)")

    if final_biomarkers['GSH'] < 5.0:
        print(f"  ⚠ GSH DEPLETION: {final_biomarkers['GSH']:.1f} mM (normal ~10)")

    print("\n✓ Simulation complete!")
    print("\nNext: Integrate with cardiac model for heart-liver coupling")
