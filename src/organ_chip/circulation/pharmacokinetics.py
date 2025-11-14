"""
Systemic Circulation Module - Pharmacokinetics and Drug Distribution

This module implements physiologically-based pharmacokinetic (PBPK) modeling
for multi-organ drug distribution and clearance.

Mathematical Model:
-------------------
The system models drug distribution across multiple compartments:

Central Compartment (Blood):
dC_blood/dt = (Q_liver * C_liver + Q_heart * C_heart - Q_total * C_blood
               + Dose(t)) / V_blood - CL_renal * C_blood / V_blood

Liver Compartment:
dC_liver/dt = Q_liver * (C_blood - C_liver / K_liver) / V_liver
              - CL_hepatic * C_liver / V_liver

Heart Compartment:
dC_heart/dt = Q_heart * (C_blood - C_heart / K_heart) / V_heart

Peripheral Compartment:
dC_periph/dt = Q_periph * (C_blood - C_periph / K_periph) / V_periph

Where:
- C_X: Drug concentration in compartment X (μM)
- V_X: Volume of compartment X (L)
- Q_X: Blood flow to compartment X (L/h)
- K_X: Partition coefficient (tissue:blood ratio)
- CL_X: Clearance from compartment X (L/h)
- Dose(t): Dosing function

This is a simplified PBPK model focusing on key organs for organ-on-chip
integration.

References:
-----------
- Jones & Rowland-Yeo (2013) "Basic concepts in physiologically based
  pharmacokinetic modeling in drug discovery"
- Nestorov (2003) "Whole body pharmacokinetic models"
- Rowland et al. (2011) "Physiologically-based pharmacokinetics in drug
  development"
"""

import numpy as np
from typing import Dict, Optional, Callable


class PharmacokineticsModel:
    """
    Physiologically-based pharmacokinetics (PBPK) model.

    This model captures:
    - Drug distribution across blood, liver, heart, and peripheral compartments
    - Organ-specific blood flows and partition coefficients
    - Hepatic metabolism (clearance)
    - Renal clearance
    - Flexible dosing regimens

    State Variables:
    ----------------
    [C_blood, C_liver, C_heart, C_periph]
    """

    def __init__(
        self,
        # Compartment volumes (L)
        V_blood: float = 5.0,           # Blood volume
        V_liver: float = 1.8,           # Liver volume
        V_heart: float = 0.3,           # Heart volume
        V_periph: float = 40.0,         # Peripheral volume
        # Blood flows (L/h)
        Q_liver: float = 90.0,          # Hepatic blood flow
        Q_heart: float = 15.0,          # Cardiac blood flow
        Q_periph: float = 150.0,        # Peripheral blood flow
        # Partition coefficients (tissue:blood)
        K_liver: float = 2.0,           # Liver partition coefficient
        K_heart: float = 1.5,           # Heart partition coefficient
        K_periph: float = 1.0,          # Peripheral partition coefficient
        # Clearance (L/h)
        CL_hepatic: float = 10.0,       # Hepatic clearance
        CL_renal: float = 1.0,          # Renal clearance
        # Initial conditions (μM)
        C_blood0: float = 0.0,
        C_liver0: float = 0.0,
        C_heart0: float = 0.0,
        C_periph0: float = 0.0,
    ):
        """
        Initialize pharmacokinetics model.

        Parameters
        ----------
        V_blood, V_liver, V_heart, V_periph : float
            Compartment volumes (L)
        Q_liver, Q_heart, Q_periph : float
            Blood flows to compartments (L/h)
        K_liver, K_heart, K_periph : float
            Partition coefficients (tissue:blood ratio)
        CL_hepatic : float
            Hepatic metabolic clearance (L/h)
        CL_renal : float
            Renal clearance (L/h)
        C_X0 : float
            Initial concentrations (μM)
        """
        self.V_blood = V_blood
        self.V_liver = V_liver
        self.V_heart = V_heart
        self.V_periph = V_periph
        self.Q_liver = Q_liver
        self.Q_heart = Q_heart
        self.Q_periph = Q_periph
        self.K_liver = K_liver
        self.K_heart = K_heart
        self.K_periph = K_periph
        self.CL_hepatic = CL_hepatic
        self.CL_renal = CL_renal

        # Total blood flow
        self.Q_total = Q_liver + Q_heart + Q_periph

        # State: [C_blood, C_liver, C_heart, C_periph]
        self.state = np.array([C_blood0, C_liver0, C_heart0, C_periph0], dtype=np.float64)

        # Dosing
        self.dose_rate = 0.0  # μM·L/h (concentration × volume / time)

        # History
        self.history = {
            't': [0.0],
            'C_blood': [C_blood0],
            'C_liver': [C_liver0],
            'C_heart': [C_heart0],
            'C_periph': [C_periph0],
            'AUC': [0.0],  # Area under curve
        }

    def derivatives(self, state: np.ndarray, t: float = 0.0) -> np.ndarray:
        """
        Compute derivatives of state variables.

        Parameters
        ----------
        state : np.ndarray
            Current state [C_blood, C_liver, C_heart, C_periph]
        t : float
            Current time (h)

        Returns
        -------
        np.ndarray
            Derivatives
        """
        C_blood, C_liver, C_heart, C_periph = state

        # Ensure non-negative
        C_blood = max(0.0, C_blood)
        C_liver = max(0.0, C_liver)
        C_heart = max(0.0, C_heart)
        C_periph = max(0.0, C_periph)

        # Venous return from organs (accounting for partition coefficients)
        venous_liver = self.Q_liver * C_liver / self.K_liver
        venous_heart = self.Q_heart * C_heart / self.K_heart
        venous_periph = self.Q_periph * C_periph / self.K_periph

        # Arterial delivery (same concentration to all organs)
        arterial_total = self.Q_total * C_blood

        # Blood compartment
        dC_blood_dt = (
            (venous_liver + venous_heart + venous_periph - arterial_total) / self.V_blood
            - self.CL_renal * C_blood / self.V_blood
            + self.dose_rate / self.V_blood
        )

        # Liver compartment
        dC_liver_dt = (
            self.Q_liver * (C_blood - C_liver / self.K_liver) / self.V_liver
            - self.CL_hepatic * C_liver / self.V_liver
        )

        # Heart compartment
        dC_heart_dt = self.Q_heart * (C_blood - C_heart / self.K_heart) / self.V_heart

        # Peripheral compartment
        dC_periph_dt = self.Q_periph * (C_blood - C_periph / self.K_periph) / self.V_periph

        return np.array([dC_blood_dt, dC_liver_dt, dC_heart_dt, dC_periph_dt])

    def step(
        self,
        dt: float,
        dose: Optional[float] = None,
        dose_rate: Optional[float] = None
    ) -> np.ndarray:
        """
        Advance simulation by one time step.

        Parameters
        ----------
        dt : float
            Time step (hours)
        dose : float, optional
            Bolus dose (μM·L) - added directly to blood
        dose_rate : float, optional
            Infusion rate (μM·L/h)

        Returns
        -------
        np.ndarray
            Updated state
        """
        # Add bolus dose if provided
        if dose is not None:
            self.state[0] += dose / self.V_blood

        # Set infusion rate
        if dose_rate is not None:
            self.dose_rate = dose_rate
        elif dose is None:
            self.dose_rate = 0.0

        # Euler integration
        derivs = self.derivatives(self.state)
        self.state = self.state + dt * derivs

        # Ensure non-negative
        self.state = np.maximum(0.0, self.state)

        # Update AUC (trapezoidal rule)
        current_time = self.history['t'][-1]
        prev_C_blood = self.history['C_blood'][-1]
        AUC_increment = (prev_C_blood + self.state[0]) * dt / 2.0
        new_AUC = self.history['AUC'][-1] + AUC_increment

        # Update history
        self.history['t'].append(current_time + dt)
        self.history['C_blood'].append(self.state[0])
        self.history['C_liver'].append(self.state[1])
        self.history['C_heart'].append(self.state[2])
        self.history['C_periph'].append(self.state[3])
        self.history['AUC'].append(new_AUC)

        return self.state.copy()

    def get_total_amount(self) -> float:
        """
        Calculate total drug amount in body.

        Returns
        -------
        float
            Total amount (μM·L)
        """
        C_blood, C_liver, C_heart, C_periph = self.state
        return (
            C_blood * self.V_blood +
            C_liver * self.V_liver +
            C_heart * self.V_heart +
            C_periph * self.V_periph
        )

    def get_clearance(self) -> float:
        """
        Calculate total clearance.

        Returns
        -------
        float
            Total clearance (L/h)
        """
        return self.CL_hepatic + self.CL_renal

    def get_volume_of_distribution(self) -> float:
        """
        Calculate steady-state volume of distribution.

        Returns
        -------
        float
            Vss (L)
        """
        return (
            self.V_blood +
            self.V_liver * self.K_liver +
            self.V_heart * self.K_heart +
            self.V_periph * self.K_periph
        )

    def get_half_life(self) -> float:
        """
        Calculate elimination half-life.

        Returns
        -------
        float
            Half-life (h)
        """
        CL_total = self.get_clearance()
        Vd = self.get_volume_of_distribution()
        if CL_total > 0:
            return 0.693 * Vd / CL_total
        return float('inf')

    def get_state(self) -> Dict[str, float]:
        """
        Get current state as dictionary.

        Returns
        -------
        dict
            State dictionary
        """
        return {
            'C_blood': self.state[0],
            'C_liver': self.state[1],
            'C_heart': self.state[2],
            'C_periph': self.state[3],
            'total_amount': self.get_total_amount(),
            'AUC': self.history['AUC'][-1],
            'clearance': self.get_clearance(),
            'Vd': self.get_volume_of_distribution(),
            'half_life': self.get_half_life(),
        }

    def reset(self):
        """Reset to initial conditions."""
        self.state = np.zeros(4)
        self.dose_rate = 0.0
        self.history = {
            't': [0.0],
            'C_blood': [0.0],
            'C_liver': [0.0],
            'C_heart': [0.0],
            'C_periph': [0.0],
            'AUC': [0.0],
        }


def create_standard_drug_pk() -> PharmacokineticsModel:
    """
    Create a PK model with standard physiological parameters.

    Returns
    -------
    PharmacokineticsModel
        Configured model
    """
    return PharmacokineticsModel(
        V_blood=5.0,
        V_liver=1.8,
        V_heart=0.3,
        V_periph=40.0,
        Q_liver=90.0,
        Q_heart=15.0,
        Q_periph=150.0,
        K_liver=2.0,
        K_heart=1.5,
        K_periph=1.0,
        CL_hepatic=10.0,
        CL_renal=1.0,
    )


def create_high_clearance_drug_pk() -> PharmacokineticsModel:
    """
    Create a PK model for a high hepatic extraction drug.

    Returns
    -------
    PharmacokineticsModel
        Configured model
    """
    return PharmacokineticsModel(
        CL_hepatic=50.0,        # High hepatic clearance
        K_liver=5.0,            # High liver partition
        CL_renal=0.5,           # Low renal clearance
    )


def create_lipophilic_drug_pk() -> PharmacokineticsModel:
    """
    Create a PK model for a lipophilic drug (high Vd).

    Returns
    -------
    PharmacokineticsModel
        Configured model
    """
    return PharmacokineticsModel(
        K_liver=10.0,           # Very high tissue partition
        K_heart=8.0,
        K_periph=5.0,
        CL_hepatic=5.0,         # Moderate clearance
        CL_renal=0.1,           # Low renal clearance
    )
