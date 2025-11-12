"""Hepatocyte toxicity model with multi-compartment drug metabolism and cellular dynamics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
import math


@dataclass
class HepatocyteToxicityModel:
    """
    Multi-state hepatocyte toxicity model capturing drug-induced liver injury.

    State Vector (8 dimensions):
    --------------
    [0] N_viable: Number of viable hepatocytes
    [1] N_damaged: Number of damaged hepatocytes
    [2] N_dead: Number of dead hepatocytes
    [3] drug_conc: Drug concentration in liver (μM)
    [4] metabolite_conc: Metabolite concentration (μM)
    [5] CYP450_activity: Enzyme activity (normalized, 0-1)
    [6] ATP_level: Cellular ATP (mM)
    [7] GSH_level: Glutathione (mM)

    Parameters
    ----------
    Drug Metabolism
    ---------------
    Vmax : float
        Maximum CYP450 metabolic rate (μM/hr), default=100.0
    Km : float
        Michaelis-Menten half-saturation constant (μM), default=50.0
    k_drug_clearance : float
        First-order drug elimination rate (1/hr), default=0.1
    k_met_clearance : float
        Metabolite clearance rate (1/hr), default=0.2

    Cellular Dynamics
    -----------------
    k_damage : float
        Damage accumulation rate constant (1/hr), default=0.05
    k_repair : float
        Cellular repair rate constant (1/hr), default=0.02
    k_death : float
        Cell death rate from severe damage (1/hr), default=0.01
    damage_threshold : float
        Damage level triggering transition to damaged state, default=0.5
    death_threshold : float
        Damage level triggering cell death, default=2.0

    Energy Metabolism
    -----------------
    ATP_baseline : float
        Baseline ATP production rate (mM/hr), default=5.0
    ATP_consumption : float
        Basal ATP consumption rate (mM/hr), default=3.0
    ATP_repair_cost : float
        ATP cost for cellular repair, default=1.0

    Antioxidant Defense
    -------------------
    GSH_baseline : float
        Baseline GSH synthesis rate (mM/hr), default=2.0
    GSH_consumption : float
        GSH consumption by oxidative stress (mM/hr/μM metabolite), default=0.1
    GSH_recovery : float
        GSH regeneration rate constant (1/hr), default=0.5

    Toxicity Parameters
    -------------------
    drug_toxicity : float
        Direct toxicity coefficient of parent drug, default=0.01
    metabolite_toxicity : float
        Toxicity coefficient of metabolite, default=0.05
    ROS_generation : float
        Reactive oxygen species generation rate, default=0.02

    CYP450 Dynamics
    ---------------
    CYP450_synthesis : float
        CYP450 enzyme synthesis rate (1/hr), default=0.1
    CYP450_degradation : float
        CYP450 enzyme degradation rate (1/hr), default=0.05
    CYP450_inhibition : float
        Metabolite-mediated CYP450 inhibition constant, default=0.02
    """

    # Drug metabolism parameters
    Vmax: float = 100.0
    Km: float = 50.0
    k_drug_clearance: float = 0.1
    k_met_clearance: float = 0.2

    # Cellular dynamics parameters
    k_damage: float = 0.05
    k_repair: float = 0.02
    k_death: float = 0.01
    damage_threshold: float = 0.5
    death_threshold: float = 2.0

    # Energy metabolism parameters
    ATP_baseline: float = 5.0
    ATP_consumption: float = 3.0
    ATP_repair_cost: float = 1.0

    # Antioxidant defense parameters
    GSH_baseline: float = 2.0
    GSH_consumption: float = 0.1
    GSH_recovery: float = 0.5

    # Toxicity parameters
    drug_toxicity: float = 0.01
    metabolite_toxicity: float = 0.05
    ROS_generation: float = 0.02

    # CYP450 dynamics
    CYP450_synthesis: float = 0.1
    CYP450_degradation: float = 0.05
    CYP450_inhibition: float = 0.02

    def derivatives(
        self,
        t: float,
        state: Tuple[float, float, float, float, float, float, float, float],
        drug_input: float = 0.0
    ) -> Tuple[float, float, float, float, float, float, float, float]:
        """
        Compute time derivatives of all state variables.

        Parameters
        ----------
        t : float
            Current simulation time (hours)
        state : Tuple[float, ...]
            Current state vector:
            (N_viable, N_damaged, N_dead, drug_conc, metabolite_conc,
             CYP450_activity, ATP_level, GSH_level)
        drug_input : float, optional
            External drug input rate (μM/hr), e.g., from dosing regimen

        Returns
        -------
        Tuple[float, ...]
            Time derivatives of state variables in same order
        """

        N_viable, N_damaged, N_dead, drug_conc, metabolite_conc, CYP450_activity, ATP_level, GSH_level = state

        # ================================================================
        # 1. DRUG METABOLISM (Michaelis-Menten kinetics)
        # ================================================================
        # Metabolic rate depends on CYP450 activity and substrate concentration
        V_metabolism = self.Vmax * CYP450_activity * drug_conc / (self.Km + drug_conc)

        # Drug concentration dynamics
        dDrug = drug_input - V_metabolism - self.k_drug_clearance * drug_conc

        # Metabolite concentration dynamics
        dMetabolite = V_metabolism - self.k_met_clearance * metabolite_conc

        # ================================================================
        # 2. CYP450 ENZYME DYNAMICS
        # ================================================================
        # CYP450 activity can be inhibited by metabolites and cellular damage
        damage_factor = N_damaged / max(N_viable + N_damaged, 1.0)  # Avoid division by zero
        metabolite_inhibition = 1.0 / (1.0 + self.CYP450_inhibition * metabolite_conc)

        dCYP450 = (
            self.CYP450_synthesis * (1.0 - damage_factor) * metabolite_inhibition
            - self.CYP450_degradation * CYP450_activity
        )
        # Clamp CYP450 activity between 0 and 1
        dCYP450 = max(dCYP450, -CYP450_activity) if CYP450_activity <= 0 else dCYP450
        dCYP450 = min(dCYP450, 1.0 - CYP450_activity) if CYP450_activity >= 1.0 else dCYP450

        # ================================================================
        # 3. ATP DYNAMICS (Cellular energy)
        # ================================================================
        # ATP production by viable cells
        ATP_production = self.ATP_baseline * (N_viable / max(N_viable + N_damaged + N_dead, 1.0))

        # ATP consumption for basal metabolism and repair
        repair_ATP_cost = self.ATP_repair_cost * self.k_repair * N_damaged
        total_ATP_consumption = self.ATP_consumption + repair_ATP_cost

        dATP = ATP_production - total_ATP_consumption

        # ================================================================
        # 4. GLUTATHIONE DYNAMICS (Antioxidant defense)
        # ================================================================
        # ROS generation by metabolite
        ROS_stress = self.ROS_generation * metabolite_conc

        # GSH depletion by oxidative stress
        GSH_depletion = self.GSH_consumption * ROS_stress * GSH_level

        # GSH regeneration (depends on ATP availability)
        ATP_factor = ATP_level / (ATP_level + 1.0)  # Saturation function
        GSH_regeneration = self.GSH_baseline * ATP_factor + self.GSH_recovery * (10.0 - GSH_level)

        dGSH = GSH_regeneration - GSH_depletion

        # ================================================================
        # 5. CELLULAR DAMAGE INDEX
        # ================================================================
        # Damage is accumulated from multiple sources
        drug_stress = self.drug_toxicity * drug_conc
        metabolite_stress = self.metabolite_toxicity * metabolite_conc
        ATP_stress = max(0.0, 2.0 - ATP_level)  # Stress increases when ATP < 2 mM
        GSH_stress = max(0.0, 3.0 - GSH_level)  # Stress increases when GSH < 3 mM

        damage_index = drug_stress + metabolite_stress + 0.5 * ATP_stress + 0.3 * GSH_stress

        # ================================================================
        # 6. CELL POPULATION DYNAMICS
        # ================================================================
        # Viable → Damaged transition (damage-dependent)
        viable_to_damaged = self.k_damage * damage_index * N_viable

        # Damaged → Viable recovery (ATP and GSH-dependent repair)
        repair_efficiency = min(1.0, ATP_level / 3.0) * min(1.0, GSH_level / 5.0)
        damaged_to_viable = self.k_repair * repair_efficiency * N_damaged

        # Damaged → Dead transition (severe damage)
        severe_damage_factor = max(0.0, damage_index - self.death_threshold)
        damaged_to_dead = self.k_death * severe_damage_factor * N_damaged

        # Cell population derivatives
        dN_viable = -viable_to_damaged + damaged_to_viable
        dN_damaged = viable_to_damaged - damaged_to_viable - damaged_to_dead
        dN_dead = damaged_to_dead

        # ================================================================
        # RETURN DERIVATIVES
        # ================================================================
        return (
            dN_viable,
            dN_damaged,
            dN_dead,
            dDrug,
            dMetabolite,
            dCYP450,
            dATP,
            dGSH
        )

    def step(
        self,
        t: float,
        state: Tuple[float, float, float, float, float, float, float, float],
        dt: float,
        drug_input: float = 0.0
    ) -> Tuple[float, float, float, float, float, float, float, float]:
        """
        Advance the model by one explicit Euler integration step.

        Parameters
        ----------
        t : float
            Current time (hours)
        state : Tuple[float, ...]
            Current state vector
        dt : float
            Time step size (hours)
        drug_input : float, optional
            Drug input rate (μM/hr)

        Returns
        -------
        Tuple[float, ...]
            Updated state vector after time step dt
        """

        # Compute derivatives
        derivs = self.derivatives(t, state, drug_input=drug_input)

        # Euler integration
        new_state = tuple(
            max(0.0, state[i] + dt * derivs[i])  # Enforce non-negativity
            for i in range(8)
        )

        # Special handling for CYP450 activity (clamp to [0, 1])
        new_state_list = list(new_state)
        new_state_list[5] = max(0.0, min(1.0, new_state_list[5]))  # CYP450_activity

        return tuple(new_state_list)

    def get_initial_state(
        self,
        N_total: float = 1000.0,
        drug_conc: float = 0.0,
        CYP450_activity: float = 1.0,
        ATP_level: float = 5.0,
        GSH_level: float = 10.0
    ) -> Tuple[float, float, float, float, float, float, float, float]:
        """
        Generate physiologically reasonable initial conditions.

        Parameters
        ----------
        N_total : float
            Total number of hepatocytes (viable at t=0), default=1000
        drug_conc : float
            Initial drug concentration (μM), default=0.0
        CYP450_activity : float
            Initial CYP450 activity (normalized), default=1.0
        ATP_level : float
            Initial ATP level (mM), default=5.0
        GSH_level : float
            Initial glutathione level (mM), default=10.0

        Returns
        -------
        Tuple[float, ...]
            Initial state vector
        """

        return (
            N_total,     # N_viable
            0.0,         # N_damaged
            0.0,         # N_dead
            drug_conc,   # drug_conc
            0.0,         # metabolite_conc
            CYP450_activity,  # CYP450_activity
            ATP_level,   # ATP_level
            GSH_level    # GSH_level
        )

    def get_state_labels(self) -> Tuple[str, ...]:
        """Return descriptive labels for each state variable."""
        return (
            "N_viable (cells)",
            "N_damaged (cells)",
            "N_dead (cells)",
            "Drug Conc (μM)",
            "Metabolite Conc (μM)",
            "CYP450 Activity",
            "ATP Level (mM)",
            "GSH Level (mM)"
        )

    def compute_viability(self, state: Tuple[float, ...]) -> float:
        """
        Compute cell viability percentage.

        Parameters
        ----------
        state : Tuple[float, ...]
            Current state vector

        Returns
        -------
        float
            Viability percentage (0-100)
        """
        N_viable, N_damaged, N_dead, *_ = state
        total = N_viable + N_damaged + N_dead
        return 100.0 * N_viable / total if total > 0 else 0.0

    def compute_injury_markers(self, state: Tuple[float, ...]) -> dict:
        """
        Compute surrogate biomarkers of hepatocellular injury.

        In practice, damaged/dead cells release ALT, AST, and other enzymes.
        Here we provide relative markers based on cell populations.

        Parameters
        ----------
        state : Tuple[float, ...]
            Current state vector

        Returns
        -------
        dict
            Dictionary with injury biomarkers:
            - 'viability': Cell viability (%)
            - 'damage_fraction': Fraction of damaged cells
            - 'death_fraction': Fraction of dead cells
            - 'metabolic_capacity': Relative metabolic capacity
            - 'oxidative_stress': Oxidative stress index
        """
        N_viable, N_damaged, N_dead, drug_conc, metabolite_conc, CYP450_activity, ATP_level, GSH_level = state

        total_cells = N_viable + N_damaged + N_dead
        if total_cells == 0:
            total_cells = 1.0  # Avoid division by zero

        return {
            'viability': 100.0 * N_viable / total_cells,
            'damage_fraction': N_damaged / total_cells,
            'death_fraction': N_dead / total_cells,
            'metabolic_capacity': CYP450_activity * (N_viable / total_cells),
            'oxidative_stress': max(0.0, 10.0 - GSH_level) * metabolite_conc / 100.0,
            'energy_deficit': max(0.0, 5.0 - ATP_level) / 5.0
        }
