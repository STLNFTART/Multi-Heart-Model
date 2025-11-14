"""
Liver Subsystem - Hepatocyte Model with Drug Metabolism and Toxicity

This module implements a comprehensive hepatocyte model including:
- Drug metabolism (Phase I and Phase II)
- Mitochondrial function and ATP production
- Oxidative stress and glutathione dynamics
- Hepatotoxicity mechanisms
- Cell viability and damage

Mathematical Model:
-------------------
The system models drug metabolism and hepatotoxicity:

Phase I Metabolism (CYP450):
dD/dt = -V_CYP * D / (K_CYP + D) - k_uptake * D + k_efflux * D_cell

Phase II Metabolism (Conjugation):
dM/dt = V_CYP * D / (K_CYP + D) - V_conj * M / (K_conj + M)
dM_conj/dt = V_conj * M / (K_conj + M) - k_excrete * M_conj

Glutathione Dynamics:
dGSH/dt = k_GSH_synth - k_GSH_ox * ROS * GSH - V_conj * M / (K_conj + M)
dGSSG/dt = k_GSH_ox * ROS * GSH / 2 - k_GSSG_red * GSSG

Reactive Oxygen Species (ROS):
dROS/dt = k_ROS_prod * M + k_ROS_mito * (1 - ATP/ATP_max) - k_ROS_scav * GSH * ROS

ATP Dynamics:
dATP/dt = k_ATP_prod * (1 - Damage) - k_ATP_cons - k_ATP_damage * M * ATP

Cell Damage:
dDamage/dt = k_damage * (ROS + M) * (1 - Damage) - k_repair * Damage * ATP

Where:
- D: Drug concentration in medium (μM)
- D_cell: Drug concentration in cell (μM)
- M: Metabolite concentration (μM)
- M_conj: Conjugated metabolite (μM)
- GSH: Reduced glutathione (mM)
- GSSG: Oxidized glutathione (mM)
- ROS: Reactive oxygen species (AU)
- ATP: ATP level (mM)
- Damage: Cell damage (0-1)

References:
-----------
- Godoy et al. (2013) "Recent advances in 2D and 3D in vitro systems using
  primary hepatocytes and HepaRG cells"
- Soldatow et al. (2013) "In vitro models for liver toxicity testing"
- Schug et al. (2013) "Acetaminophen hepatotoxicity: molecular mechanisms"
"""

import numpy as np
from typing import Dict, Optional, Tuple


class HepatocyteModel:
    """
    Hepatocyte model with drug metabolism and toxicity.

    This model captures:
    - Phase I metabolism (CYP450-mediated oxidation)
    - Phase II metabolism (glucuronidation, sulfation)
    - Glutathione redox cycle
    - ROS production and scavenging
    - ATP production and consumption
    - Cell damage and repair mechanisms
    - Cell viability

    State Variables:
    ----------------
    [D, M, M_conj, GSH, GSSG, ROS, ATP, Damage]
    """

    def __init__(
        self,
        # Phase I metabolism parameters
        V_CYP: float = 100.0,           # Max CYP450 velocity (μM/h)
        K_CYP: float = 50.0,            # CYP450 Michaelis constant (μM)
        # Phase II metabolism parameters
        V_conj: float = 80.0,           # Max conjugation velocity (μM/h)
        K_conj: float = 30.0,           # Conjugation Michaelis constant (μM)
        k_excrete: float = 2.0,         # Conjugate excretion rate (1/h)
        # Drug transport
        k_uptake: float = 0.5,          # Drug uptake rate (1/h)
        k_efflux: float = 0.1,          # Drug efflux rate (1/h)
        # Glutathione dynamics
        k_GSH_synth: float = 5.0,       # GSH synthesis rate (mM/h)
        k_GSH_ox: float = 0.1,          # GSH oxidation rate (1/(AU·h))
        k_GSSG_red: float = 1.0,        # GSSG reduction rate (1/h)
        GSH_used_conj: float = 0.5,     # GSH used per conjugation (mM/μM)
        # ROS dynamics
        k_ROS_prod: float = 0.05,       # ROS production from metabolite (AU/(μM·h))
        k_ROS_mito: float = 1.0,        # Mitochondrial ROS (AU/h)
        k_ROS_scav: float = 0.5,        # ROS scavenging rate (1/(mM·h))
        # ATP dynamics
        k_ATP_prod: float = 10.0,       # ATP production rate (mM/h)
        k_ATP_cons: float = 3.0,        # ATP consumption rate (mM/h)
        k_ATP_damage: float = 0.01,     # ATP depletion by metabolite (1/(μM·h))
        ATP_max: float = 5.0,           # Maximum ATP (mM)
        # Damage dynamics
        k_damage: float = 0.1,          # Damage rate (1/(μM·h))
        k_repair: float = 0.2,          # Repair rate (1/(mM·h))
        damage_threshold: float = 0.7,  # Cell death threshold
        # Initial conditions
        D0: float = 0.0,                # Initial drug (μM)
        M0: float = 0.0,                # Initial metabolite (μM)
        M_conj0: float = 0.0,           # Initial conjugate (μM)
        GSH0: float = 10.0,             # Initial GSH (mM)
        GSSG0: float = 0.5,             # Initial GSSG (mM)
        ROS0: float = 0.1,              # Initial ROS (AU)
        ATP0: float = 5.0,              # Initial ATP (mM)
        Damage0: float = 0.0,           # Initial damage
    ):
        """
        Initialize hepatocyte model.

        Parameters
        ----------
        See class docstring for parameter descriptions.
        """
        # Store parameters
        self.V_CYP = V_CYP
        self.K_CYP = K_CYP
        self.V_conj = V_conj
        self.K_conj = K_conj
        self.k_excrete = k_excrete
        self.k_uptake = k_uptake
        self.k_efflux = k_efflux
        self.k_GSH_synth = k_GSH_synth
        self.k_GSH_ox = k_GSH_ox
        self.k_GSSG_red = k_GSSG_red
        self.GSH_used_conj = GSH_used_conj
        self.k_ROS_prod = k_ROS_prod
        self.k_ROS_mito = k_ROS_mito
        self.k_ROS_scav = k_ROS_scav
        self.k_ATP_prod = k_ATP_prod
        self.k_ATP_cons = k_ATP_cons
        self.k_ATP_damage = k_ATP_damage
        self.ATP_max = ATP_max
        self.k_damage = k_damage
        self.k_repair = k_repair
        self.damage_threshold = damage_threshold

        # State: [D, M, M_conj, GSH, GSSG, ROS, ATP, Damage]
        self.state = np.array(
            [D0, M0, M_conj0, GSH0, GSSG0, ROS0, ATP0, Damage0],
            dtype=np.float64
        )

        # History
        self.history = {
            't': [0.0],
            'D': [D0],
            'M': [M0],
            'M_conj': [M_conj0],
            'GSH': [GSH0],
            'GSSG': [GSSG0],
            'ROS': [ROS0],
            'ATP': [ATP0],
            'Damage': [Damage0],
        }

    def derivatives(self, state: np.ndarray, t: float = 0.0) -> np.ndarray:
        """
        Compute derivatives of state variables.

        Parameters
        ----------
        state : np.ndarray
            Current state
        t : float
            Current time

        Returns
        -------
        np.ndarray
            Derivatives
        """
        D, M, M_conj, GSH, GSSG, ROS, ATP, Damage = state

        # Ensure non-negative
        D = max(0.0, D)
        M = max(0.0, M)
        M_conj = max(0.0, M_conj)
        GSH = max(0.0, GSH)
        GSSG = max(0.0, GSSG)
        ROS = max(0.0, ROS)
        ATP = max(0.0, ATP)
        Damage = max(0.0, min(1.0, Damage))

        # Check if cell is dead
        if Damage > self.damage_threshold:
            # Cell death - all processes stop
            return np.zeros(8)

        # Phase I metabolism (CYP450)
        v_phase1 = self.V_CYP * D / (self.K_CYP + D)

        # Phase II metabolism (conjugation)
        v_phase2 = self.V_conj * M / (self.K_conj + M)

        # GSH consumption in conjugation
        GSH_consumption_conj = self.GSH_used_conj * v_phase2

        # Drug dynamics
        dD_dt = -v_phase1 - self.k_uptake * D + self.k_efflux * D

        # Metabolite dynamics
        dM_dt = v_phase1 - v_phase2

        # Conjugated metabolite
        dM_conj_dt = v_phase2 - self.k_excrete * M_conj

        # ROS production
        ROS_production = (
            self.k_ROS_prod * M +  # From metabolite
            self.k_ROS_mito * (1 - ATP / self.ATP_max)  # From mitochondrial dysfunction
        )
        ROS_scavenging = self.k_ROS_scav * GSH * ROS

        # Glutathione dynamics
        GSH_oxidation = self.k_GSH_ox * ROS * GSH
        GSSG_reduction = self.k_GSSG_red * GSSG

        dGSH_dt = (
            self.k_GSH_synth +
            GSSG_reduction -
            GSH_oxidation -
            GSH_consumption_conj
        )

        dGSSG_dt = GSH_oxidation / 2.0 - GSSG_reduction

        dROS_dt = ROS_production - ROS_scavenging

        # ATP dynamics
        ATP_production = self.k_ATP_prod * (1.0 - Damage)
        ATP_consumption = self.k_ATP_cons + self.k_ATP_damage * M * ATP

        dATP_dt = ATP_production - ATP_consumption

        # Cell damage
        damage_induction = self.k_damage * (ROS + M) * (1.0 - Damage)
        damage_repair = self.k_repair * Damage * ATP

        dDamage_dt = damage_induction - damage_repair

        return np.array([dD_dt, dM_dt, dM_conj_dt, dGSH_dt, dGSSG_dt, dROS_dt, dATP_dt, dDamage_dt])

    def step(
        self,
        dt: float,
        drug_input: Optional[float] = None
    ) -> np.ndarray:
        """
        Advance simulation by one time step.

        Parameters
        ----------
        dt : float
            Time step (hours)
        drug_input : float, optional
            External drug input (μM)

        Returns
        -------
        np.ndarray
            Updated state
        """
        # Add drug input if provided
        if drug_input is not None:
            self.state[0] += drug_input

        # Euler integration
        derivs = self.derivatives(self.state)
        self.state = self.state + dt * derivs

        # Constraints
        self.state = np.maximum(0.0, self.state)
        self.state[7] = min(1.0, self.state[7])  # Damage ∈ [0, 1]

        # Update history
        current_time = self.history['t'][-1] + dt
        self.history['t'].append(current_time)
        self.history['D'].append(self.state[0])
        self.history['M'].append(self.state[1])
        self.history['M_conj'].append(self.state[2])
        self.history['GSH'].append(self.state[3])
        self.history['GSSG'].append(self.state[4])
        self.history['ROS'].append(self.state[5])
        self.history['ATP'].append(self.state[6])
        self.history['Damage'].append(self.state[7])

        return self.state.copy()

    def get_viability(self) -> float:
        """
        Calculate cell viability (1 - Damage).

        Returns
        -------
        float
            Viability (0-1)
        """
        return 1.0 - self.state[7]

    def get_GSH_GSSG_ratio(self) -> float:
        """
        Calculate GSH/GSSG ratio (oxidative stress indicator).

        Returns
        -------
        float
            GSH/GSSG ratio
        """
        GSH = self.state[3]
        GSSG = self.state[4]
        if GSSG > 0:
            return GSH / GSSG
        return float('inf') if GSH > 0 else 0.0

    def is_alive(self) -> bool:
        """
        Check if cell is alive.

        Returns
        -------
        bool
            True if alive, False if dead
        """
        return self.state[7] < self.damage_threshold

    def get_state(self) -> Dict[str, float]:
        """
        Get current state as dictionary.

        Returns
        -------
        dict
            State dictionary
        """
        return {
            'D': self.state[0],
            'M': self.state[1],
            'M_conj': self.state[2],
            'GSH': self.state[3],
            'GSSG': self.state[4],
            'ROS': self.state[5],
            'ATP': self.state[6],
            'Damage': self.state[7],
            'viability': self.get_viability(),
            'GSH_GSSG_ratio': self.get_GSH_GSSG_ratio(),
            'is_alive': self.is_alive(),
        }


def create_acetaminophen_model() -> HepatocyteModel:
    """
    Create hepatocyte model parameterized for acetaminophen (APAP) toxicity.

    APAP is metabolized to NAPQI (toxic metabolite) which depletes GSH
    and causes oxidative stress.

    Returns
    -------
    HepatocyteModel
        Configured model
    """
    return HepatocyteModel(
        V_CYP=150.0,            # High CYP2E1 activity
        K_CYP=100.0,
        V_conj=200.0,           # High glucuronidation capacity
        K_conj=50.0,
        k_ROS_prod=0.1,         # NAPQI generates ROS
        k_damage=0.15,          # Reactive metabolite damage
        GSH_used_conj=1.0,      # High GSH consumption
        k_GSH_synth=3.0,        # Limited GSH synthesis
    )


def create_doxorubicin_model() -> HepatocyteModel:
    """
    Create hepatocyte model parameterized for doxorubicin cardiotoxicity.

    Doxorubicin causes mitochondrial dysfunction and oxidative stress.

    Returns
    -------
    HepatocyteModel
        Configured model
    """
    return HepatocyteModel(
        V_CYP=50.0,             # Moderate metabolism
        K_CYP=20.0,
        k_ROS_mito=2.0,         # High mitochondrial ROS
        k_ATP_damage=0.05,      # Direct mitochondrial damage
        k_damage=0.2,           # High damage rate
        k_repair=0.1,           # Low repair capacity
    )
