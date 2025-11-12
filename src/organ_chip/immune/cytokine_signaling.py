"""
Immune Signaling Module - Cytokine Network Dynamics

This module implements immune cell signaling and cytokine network dynamics
for organ-on-chip applications, focusing on inflammatory responses.

Mathematical Model:
-------------------
The system models pro-inflammatory and anti-inflammatory cytokine dynamics:

dIL6/dt = k_IL6_prod * M1 - k_IL6_deg * IL6
dTNFa/dt = k_TNFa_prod * M1 - k_TNFa_deg * TNFa
dIL10/dt = k_IL10_prod * M2 - k_IL10_deg * IL10
dM1/dt = k_M1_act * (TNFa + IL6) * M0 - k_M1_deact * IL10 * M1 - k_M1_death * M1
dM2/dt = k_M2_act * IL10 * M0 - k_M2_deact * TNFa * M2 - k_M2_death * M2
dM0/dt = k_M0_recruit + k_M1_deact * IL10 * M1 + k_M2_deact * TNFa * M2
         - k_M1_act * (TNFa + IL6) * M0 - k_M2_act * IL10 * M0 - k_M0_death * M0

Where:
- IL6: Interleukin-6 concentration (pg/mL) - pro-inflammatory
- TNFa: Tumor Necrosis Factor-α concentration (pg/mL) - pro-inflammatory
- IL10: Interleukin-10 concentration (pg/mL) - anti-inflammatory
- M0: Resting macrophages (cells/mL)
- M1: M1 (pro-inflammatory) macrophages (cells/mL)
- M2: M2 (anti-inflammatory) macrophages (cells/mL)

References:
-----------
- Vodovotz et al. (2008) "Evidence-based modeling of critical illness"
- Reynolds et al. (2006) "A reduced mathematical model of the acute
  inflammatory response"
- Dunster et al. (2014) "The resolution of inflammation"
"""

import numpy as np
from typing import Dict, Optional


class CytokineSignalingModel:
    """
    Cytokine network model with macrophage polarization.

    This model captures:
    - Pro-inflammatory cytokine production (IL-6, TNF-α)
    - Anti-inflammatory cytokine production (IL-10)
    - Macrophage polarization (M0 → M1/M2)
    - Positive feedback (M1 activation)
    - Negative feedback (M2 suppression)

    State Variables:
    ----------------
    [IL6, TNFa, IL10, M0, M1, M2] where:
    - IL6, TNFa, IL10: Cytokine concentrations (pg/mL)
    - M0, M1, M2: Macrophage populations (cells/mL)
    """

    def __init__(
        self,
        k_IL6_prod: float = 10.0,      # IL-6 production rate (pg/(cell·h))
        k_IL6_deg: float = 0.1,         # IL-6 degradation rate (1/h)
        k_TNFa_prod: float = 20.0,      # TNF-α production rate (pg/(cell·h))
        k_TNFa_deg: float = 0.5,        # TNF-α degradation rate (1/h)
        k_IL10_prod: float = 15.0,      # IL-10 production rate (pg/(cell·h))
        k_IL10_deg: float = 0.2,        # IL-10 degradation rate (1/h)
        k_M1_act: float = 0.001,        # M1 activation rate (mL/(pg·h))
        k_M1_deact: float = 0.0005,     # M1 deactivation rate (mL/(pg·h))
        k_M1_death: float = 0.01,       # M1 death rate (1/h)
        k_M2_act: float = 0.0008,       # M2 activation rate (mL/(pg·h))
        k_M2_deact: float = 0.0003,     # M2 deactivation rate (mL/(pg·h))
        k_M2_death: float = 0.01,       # M2 death rate (1/h)
        k_M0_recruit: float = 10.0,     # M0 recruitment rate (cells/(mL·h))
        k_M0_death: float = 0.005,      # M0 death rate (1/h)
        IL6_0: float = 0.0,             # Initial IL-6 (pg/mL)
        TNFa_0: float = 0.0,            # Initial TNF-α (pg/mL)
        IL10_0: float = 0.0,            # Initial IL-10 (pg/mL)
        M0_0: float = 1000.0,           # Initial M0 (cells/mL)
        M1_0: float = 0.0,              # Initial M1 (cells/mL)
        M2_0: float = 0.0,              # Initial M2 (cells/mL)
    ):
        """
        Initialize cytokine signaling model.

        Parameters
        ----------
        k_IL6_prod : float
            IL-6 production rate by M1 macrophages
        k_IL6_deg : float
            IL-6 degradation/clearance rate
        k_TNFa_prod : float
            TNF-α production rate by M1 macrophages
        k_TNFa_deg : float
            TNF-α degradation/clearance rate
        k_IL10_prod : float
            IL-10 production rate by M2 macrophages
        k_IL10_deg : float
            IL-10 degradation/clearance rate
        k_M1_act : float
            M0 → M1 activation rate
        k_M1_deact : float
            M1 → M0 deactivation rate
        k_M1_death : float
            M1 death rate
        k_M2_act : float
            M0 → M2 activation rate
        k_M2_deact : float
            M2 → M0 deactivation rate
        k_M2_death : float
            M2 death rate
        k_M0_recruit : float
            M0 recruitment rate
        k_M0_death : float
            M0 death rate
        IL6_0 : float
            Initial IL-6 concentration
        TNFa_0 : float
            Initial TNF-α concentration
        IL10_0 : float
            Initial IL-10 concentration
        M0_0 : float
            Initial M0 population
        M1_0 : float
            Initial M1 population
        M2_0 : float
            Initial M2 population
        """
        self.k_IL6_prod = k_IL6_prod
        self.k_IL6_deg = k_IL6_deg
        self.k_TNFa_prod = k_TNFa_prod
        self.k_TNFa_deg = k_TNFa_deg
        self.k_IL10_prod = k_IL10_prod
        self.k_IL10_deg = k_IL10_deg
        self.k_M1_act = k_M1_act
        self.k_M1_deact = k_M1_deact
        self.k_M1_death = k_M1_death
        self.k_M2_act = k_M2_act
        self.k_M2_deact = k_M2_deact
        self.k_M2_death = k_M2_death
        self.k_M0_recruit = k_M0_recruit
        self.k_M0_death = k_M0_death

        # State: [IL6, TNFa, IL10, M0, M1, M2]
        self.state = np.array([IL6_0, TNFa_0, IL10_0, M0_0, M1_0, M2_0], dtype=np.float64)

        # History
        self.history = {
            't': [0.0],
            'IL6': [IL6_0],
            'TNFa': [TNFa_0],
            'IL10': [IL10_0],
            'M0': [M0_0],
            'M1': [M1_0],
            'M2': [M2_0],
        }

    def derivatives(self, state: np.ndarray, t: float = 0.0) -> np.ndarray:
        """
        Compute derivatives of state variables.

        Parameters
        ----------
        state : np.ndarray
            Current state [IL6, TNFa, IL10, M0, M1, M2]
        t : float
            Current time (not used)

        Returns
        -------
        np.ndarray
            Derivatives
        """
        IL6, TNFa, IL10, M0, M1, M2 = state

        # Ensure non-negative
        IL6 = max(0.0, IL6)
        TNFa = max(0.0, TNFa)
        IL10 = max(0.0, IL10)
        M0 = max(0.0, M0)
        M1 = max(0.0, M1)
        M2 = max(0.0, M2)

        # Cytokine production and degradation
        dIL6_dt = self.k_IL6_prod * M1 - self.k_IL6_deg * IL6
        dTNFa_dt = self.k_TNFa_prod * M1 - self.k_TNFa_deg * TNFa
        dIL10_dt = self.k_IL10_prod * M2 - self.k_IL10_deg * IL10

        # Macrophage dynamics
        # M0 → M1 activation (driven by pro-inflammatory cytokines)
        M1_activation = self.k_M1_act * (TNFa + IL6) * M0
        M1_deactivation = self.k_M1_deact * IL10 * M1

        # M0 → M2 activation (driven by anti-inflammatory cytokines)
        M2_activation = self.k_M2_act * IL10 * M0
        M2_deactivation = self.k_M2_deact * TNFa * M2

        dM1_dt = M1_activation - M1_deactivation - self.k_M1_death * M1
        dM2_dt = M2_activation - M2_deactivation - self.k_M2_death * M2
        dM0_dt = (self.k_M0_recruit + M1_deactivation + M2_deactivation
                  - M1_activation - M2_activation - self.k_M0_death * M0)

        return np.array([dIL6_dt, dTNFa_dt, dIL10_dt, dM0_dt, dM1_dt, dM2_dt])

    def step(
        self,
        dt: float,
        external_stimulus: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """
        Advance simulation by one time step.

        Parameters
        ----------
        dt : float
            Time step (hours)
        external_stimulus : dict, optional
            External inputs: {'IL6': value, 'TNFa': value, 'IL10': value,
                             'M0': value, 'M1': value, 'damage': value}

        Returns
        -------
        np.ndarray
            Updated state
        """
        # Add external stimuli if provided
        if external_stimulus is not None:
            if 'IL6' in external_stimulus:
                self.state[0] += external_stimulus['IL6']
            if 'TNFa' in external_stimulus:
                self.state[1] += external_stimulus['TNFa']
            if 'IL10' in external_stimulus:
                self.state[2] += external_stimulus['IL10']
            if 'M0' in external_stimulus:
                self.state[3] += external_stimulus['M0']
            if 'M1' in external_stimulus:
                self.state[4] += external_stimulus['M1']
            # Damage signal can trigger M1 activation
            if 'damage' in external_stimulus:
                damage = external_stimulus['damage']
                # Convert damage to TNFa burst
                self.state[1] += damage * 100.0

        # Euler integration
        derivs = self.derivatives(self.state)
        self.state = self.state + dt * derivs

        # Ensure non-negative
        self.state = np.maximum(0.0, self.state)

        # Update history
        current_time = self.history['t'][-1] + dt
        self.history['t'].append(current_time)
        self.history['IL6'].append(self.state[0])
        self.history['TNFa'].append(self.state[1])
        self.history['IL10'].append(self.state[2])
        self.history['M0'].append(self.state[3])
        self.history['M1'].append(self.state[4])
        self.history['M2'].append(self.state[5])

        return self.state.copy()

    def get_inflammatory_index(self) -> float:
        """
        Calculate inflammatory index (ratio of pro/anti-inflammatory signals).

        Returns
        -------
        float
            Inflammatory index (>1: pro-inflammatory, <1: anti-inflammatory)
        """
        IL6, TNFa, IL10, _, _, _ = self.state
        pro_inflammatory = IL6 + TNFa
        anti_inflammatory = IL10 + 1e-6  # Avoid division by zero
        return pro_inflammatory / anti_inflammatory

    def get_M1_M2_ratio(self) -> float:
        """
        Calculate M1/M2 macrophage ratio.

        Returns
        -------
        float
            M1/M2 ratio
        """
        _, _, _, _, M1, M2 = self.state
        if M2 > 0:
            return M1 / M2
        return float('inf') if M1 > 0 else 0.0

    def get_state(self) -> Dict[str, float]:
        """
        Get current state as a dictionary.

        Returns
        -------
        dict
            State dictionary
        """
        return {
            'IL6': self.state[0],
            'TNFa': self.state[1],
            'IL10': self.state[2],
            'M0': self.state[3],
            'M1': self.state[4],
            'M2': self.state[5],
            'inflammatory_index': self.get_inflammatory_index(),
            'M1_M2_ratio': self.get_M1_M2_ratio(),
        }

    def reset(self):
        """Reset to initial conditions."""
        IL6_0, TNFa_0, IL10_0 = 0.0, 0.0, 0.0
        M0_0, M1_0, M2_0 = 1000.0, 0.0, 0.0

        self.state = np.array([IL6_0, TNFa_0, IL10_0, M0_0, M1_0, M2_0], dtype=np.float64)
        self.history = {
            't': [0.0],
            'IL6': [IL6_0],
            'TNFa': [TNFa_0],
            'IL10': [IL10_0],
            'M0': [M0_0],
            'M1': [M1_0],
            'M2': [M2_0],
        }


def create_acute_inflammation_model() -> CytokineSignalingModel:
    """
    Create a model configured for acute inflammatory response.

    Returns
    -------
    CytokineSignalingModel
        Configured model
    """
    return CytokineSignalingModel(
        k_IL6_prod=15.0,
        k_TNFa_prod=30.0,
        k_IL10_prod=5.0,
        k_M1_act=0.002,
        k_M1_deact=0.0002,
        k_M2_act=0.0005,
        M0_0=1000.0,
    )


def create_chronic_inflammation_model() -> CytokineSignalingModel:
    """
    Create a model configured for chronic inflammation.

    Returns
    -------
    CytokineSignalingModel
        Configured model
    """
    return CytokineSignalingModel(
        k_IL6_prod=20.0,       # Higher sustained production
        k_TNFa_prod=25.0,
        k_IL10_prod=10.0,      # Higher anti-inflammatory
        k_M1_act=0.0015,
        k_M1_deact=0.0008,     # More deactivation
        k_M2_act=0.001,
        k_M0_recruit=15.0,     # Higher recruitment
        M0_0=1500.0,
        M1_0=200.0,            # Pre-existing M1
    )
