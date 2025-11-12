"""
Ligand-Receptor Binding Module

This module implements molecular-scale ligand-receptor binding dynamics
using mass action kinetics with receptor internalization and recycling.

Mathematical Model:
-------------------
The system is described by the following ODEs:

dL/dt = -kon*L*R + koff*LR + k_recycle*R_int - k_deg_L*L
dR/dt = -kon*L*R + koff*LR + k_synth - k_deg_R*R + k_recycle*R_int
dLR/dt = kon*L*R - koff*LR - k_int*LR
dR_int/dt = k_int*LR - k_recycle*R_int - k_deg_int*R_int

Where:
- L: Free ligand concentration (nM)
- R: Free receptor concentration (receptors/cell)
- LR: Ligand-receptor complex concentration (complexes/cell)
- R_int: Internalized receptor concentration (receptors/cell)
- kon: Association rate constant (1/(nM·s))
- koff: Dissociation rate constant (1/s)
- k_int: Internalization rate constant (1/s)
- k_recycle: Recycling rate constant (1/s)
- k_synth: Receptor synthesis rate (receptors/(cell·s))
- k_deg_L: Ligand degradation rate constant (1/s)
- k_deg_R: Receptor degradation rate constant (1/s)
- k_deg_int: Internalized receptor degradation rate constant (1/s)

References:
-----------
- Lauffenburger & Linderman (1993) "Receptors: Models for Binding,
  Trafficking, and Signaling"
- Wiley & Cunningham (1981) "The endocytic rate constant"
"""

import numpy as np
from typing import Dict, Optional, Tuple


class LigandReceptorModel:
    """
    Ligand-receptor binding model with internalization and recycling.

    This model captures:
    - Reversible ligand-receptor binding (mass action kinetics)
    - Receptor-mediated endocytosis (internalization)
    - Receptor recycling to cell surface
    - Ligand and receptor degradation
    - Receptor synthesis

    State Variables:
    ----------------
    [L, R, LR, R_int] where:
    - L: Free ligand (nM)
    - R: Surface receptors (receptors/cell)
    - LR: Bound complexes (complexes/cell)
    - R_int: Internalized receptors (receptors/cell)
    """

    def __init__(
        self,
        kon: float = 0.01,           # Association rate (1/(nM·s))
        koff: float = 0.1,            # Dissociation rate (1/s)
        k_int: float = 0.001,         # Internalization rate (1/s)
        k_recycle: float = 0.002,     # Recycling rate (1/s)
        k_synth: float = 100.0,       # Receptor synthesis (receptors/(cell·s))
        k_deg_L: float = 0.0001,      # Ligand degradation (1/s)
        k_deg_R: float = 0.0005,      # Receptor degradation (1/s)
        k_deg_int: float = 0.001,     # Internalized receptor degradation (1/s)
        L0: float = 100.0,            # Initial ligand (nM)
        R0: float = 10000.0,          # Initial receptors (receptors/cell)
        LR0: float = 0.0,             # Initial complexes (complexes/cell)
        R_int0: float = 0.0,          # Initial internalized (receptors/cell)
    ):
        """
        Initialize ligand-receptor binding model.

        Parameters
        ----------
        kon : float
            Association rate constant (1/(nM·s))
        koff : float
            Dissociation rate constant (1/s)
        k_int : float
            Internalization rate constant (1/s)
        k_recycle : float
            Recycling rate constant (1/s)
        k_synth : float
            Receptor synthesis rate (receptors/(cell·s))
        k_deg_L : float
            Ligand degradation rate (1/s)
        k_deg_R : float
            Receptor degradation rate (1/s)
        k_deg_int : float
            Internalized receptor degradation rate (1/s)
        L0 : float
            Initial ligand concentration (nM)
        R0 : float
            Initial receptor number (receptors/cell)
        LR0 : float
            Initial complex number (complexes/cell)
        R_int0 : float
            Initial internalized receptor number (receptors/cell)
        """
        self.kon = kon
        self.koff = koff
        self.k_int = k_int
        self.k_recycle = k_recycle
        self.k_synth = k_synth
        self.k_deg_L = k_deg_L
        self.k_deg_R = k_deg_R
        self.k_deg_int = k_deg_int

        # State: [L, R, LR, R_int]
        self.state = np.array([L0, R0, LR0, R_int0], dtype=np.float64)

        # History for time series
        self.history = {
            't': [0.0],
            'L': [L0],
            'R': [R0],
            'LR': [LR0],
            'R_int': [R_int0],
        }

    def derivatives(self, state: np.ndarray, t: float = 0.0) -> np.ndarray:
        """
        Compute derivatives of state variables.

        Parameters
        ----------
        state : np.ndarray
            Current state [L, R, LR, R_int]
        t : float
            Current time (not used, included for consistency)

        Returns
        -------
        np.ndarray
            Derivatives [dL/dt, dR/dt, dLR/dt, dR_int/dt]
        """
        L, R, LR, R_int = state

        # Ensure non-negative concentrations (numerical stability)
        L = max(0.0, L)
        R = max(0.0, R)
        LR = max(0.0, LR)
        R_int = max(0.0, R_int)

        # Binding and unbinding flux
        binding_flux = self.kon * L * R
        unbinding_flux = self.koff * LR

        # Internalization and recycling flux
        internalization_flux = self.k_int * LR
        recycling_flux = self.k_recycle * R_int

        # Degradation fluxes
        ligand_deg = self.k_deg_L * L
        receptor_deg = self.k_deg_R * R
        int_deg = self.k_deg_int * R_int

        # ODEs
        dL_dt = -binding_flux + unbinding_flux + recycling_flux - ligand_deg
        dR_dt = -binding_flux + unbinding_flux + self.k_synth - receptor_deg + recycling_flux
        dLR_dt = binding_flux - unbinding_flux - internalization_flux
        dR_int_dt = internalization_flux - recycling_flux - int_deg

        return np.array([dL_dt, dR_dt, dLR_dt, dR_int_dt])

    def step(self, dt: float, external_ligand: Optional[float] = None) -> np.ndarray:
        """
        Advance simulation by one time step using explicit Euler integration.

        Parameters
        ----------
        dt : float
            Time step (seconds)
        external_ligand : float, optional
            External ligand input to add (nM)

        Returns
        -------
        np.ndarray
            Updated state [L, R, LR, R_int]
        """
        # Add external ligand if provided
        if external_ligand is not None:
            self.state[0] += external_ligand

        # Euler integration
        derivs = self.derivatives(self.state)
        self.state = self.state + dt * derivs

        # Ensure non-negative (physical constraint)
        self.state = np.maximum(0.0, self.state)

        # Update history
        current_time = self.history['t'][-1] + dt
        self.history['t'].append(current_time)
        self.history['L'].append(self.state[0])
        self.history['R'].append(self.state[1])
        self.history['LR'].append(self.state[2])
        self.history['R_int'].append(self.state[3])

        return self.state.copy()

    def get_occupancy(self) -> float:
        """
        Calculate receptor occupancy (fraction of receptors bound).

        Returns
        -------
        float
            Occupancy fraction (0 to 1)
        """
        _, R, LR, _ = self.state
        total_surface = R + LR
        if total_surface > 0:
            return LR / total_surface
        return 0.0

    def get_total_receptors(self) -> float:
        """
        Calculate total receptor number (surface + internalized).

        Returns
        -------
        float
            Total receptor number (receptors/cell)
        """
        _, R, LR, R_int = self.state
        return R + LR + R_int

    def get_equilibrium_dissociation_constant(self) -> float:
        """
        Calculate equilibrium dissociation constant (Kd).

        Returns
        -------
        float
            Kd value (nM)
        """
        return self.koff / self.kon

    def reset(self, L0: Optional[float] = None, R0: Optional[float] = None):
        """
        Reset the model to initial conditions.

        Parameters
        ----------
        L0 : float, optional
            New initial ligand concentration
        R0 : float, optional
            New initial receptor number
        """
        if L0 is not None:
            self.state[0] = L0
        if R0 is not None:
            self.state[1] = R0
        self.state[2] = 0.0  # LR
        self.state[3] = 0.0  # R_int

        self.history = {
            't': [0.0],
            'L': [self.state[0]],
            'R': [self.state[1]],
            'LR': [self.state[2]],
            'R_int': [self.state[3]],
        }

    def get_state(self) -> Dict[str, float]:
        """
        Get current state as a dictionary.

        Returns
        -------
        dict
            Dictionary with keys: L, R, LR, R_int, occupancy, total_receptors, Kd
        """
        return {
            'L': self.state[0],
            'R': self.state[1],
            'LR': self.state[2],
            'R_int': self.state[3],
            'occupancy': self.get_occupancy(),
            'total_receptors': self.get_total_receptors(),
            'Kd': self.get_equilibrium_dissociation_constant(),
        }


def create_growth_factor_receptor() -> LigandReceptorModel:
    """
    Create a ligand-receptor model parameterized for growth factor receptors
    (e.g., EGF-EGFR).

    Returns
    -------
    LigandReceptorModel
        Configured model instance
    """
    return LigandReceptorModel(
        kon=0.05,              # Higher affinity
        koff=0.01,             # Lower off-rate
        k_int=0.005,           # Faster internalization
        k_recycle=0.001,       # Slower recycling
        k_synth=50.0,          # Moderate synthesis
        k_deg_L=0.0005,        # Ligand degradation
        k_deg_R=0.0002,        # Receptor degradation
        k_deg_int=0.002,       # Internalized degradation
        L0=10.0,               # Low initial ligand (ng/mL)
        R0=50000.0,            # High receptor density
    )


def create_cytokine_receptor() -> LigandReceptorModel:
    """
    Create a ligand-receptor model parameterized for cytokine receptors
    (e.g., IL-6, TNF-α).

    Returns
    -------
    LigandReceptorModel
        Configured model instance
    """
    return LigandReceptorModel(
        kon=0.1,               # Fast association
        koff=0.1,              # Moderate dissociation
        k_int=0.002,           # Moderate internalization
        k_recycle=0.005,       # Faster recycling
        k_synth=200.0,         # Higher synthesis
        k_deg_L=0.001,         # Faster ligand degradation
        k_deg_R=0.001,         # Moderate receptor degradation
        k_deg_int=0.001,       # Moderate internalized degradation
        L0=50.0,               # Moderate initial ligand
        R0=10000.0,            # Moderate receptor density
    )
