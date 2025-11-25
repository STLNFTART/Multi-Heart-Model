"""
Windkessel Arterial Hemodynamics Models

The Windkessel model describes arterial blood pressure and flow dynamics
using electrical circuit analogies. Essential for cardiovascular system modeling.

References:
- Frank, O. (1899). "Die Grundform des arteriellen Pulses."
  Zeitschrift für Biologie, 37, 483-526.

- Westerhof, N., Lankhaar, J. W., & Westerhof, B. E. (2009). "The arterial
  Windkessel." Medical & Biological Engineering & Computing, 47(2), 131-141.

- Stergiopulos, N., Westerhof, B. E., & Westerhof, N. (1999). "Total arterial
  inertance as the fourth element of the Windkessel model." American Journal
  of Physiology-Heart and Circulatory Physiology, 276(1), H81-H88.

Implementations:
- 2-element Windkessel (Frank, 1899)
- 3-element Windkessel (Westerhof et al., 1971)
- 4-element Windkessel with inertance (Stergiopulos et al., 1999)
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class Windkessel2Parameters:
    """
    Parameters for 2-element Windkessel model

    Analogous to RC circuit:
    - R: Total peripheral resistance
    - C: Arterial compliance
    """
    R: float = 1.0  # Total peripheral resistance (mmHg·s/mL)
    C: float = 1.5  # Arterial compliance (mL/mmHg)
    P_0: float = 80.0  # Reference pressure (mmHg)


@dataclass
class Windkessel3Parameters:
    """
    Parameters for 3-element Windkessel model

    Adds characteristic impedance:
    - R_c: Characteristic impedance of proximal aorta
    - R_p: Peripheral resistance
    - C: Arterial compliance
    """
    R_c: float = 0.05  # Characteristic impedance (mmHg·s/mL)
    R_p: float = 1.0  # Peripheral resistance (mmHg·s/mL)
    C: float = 1.5  # Arterial compliance (mL/mmHg)
    P_0: float = 80.0  # Reference pressure (mmHg)


@dataclass
class Windkessel4Parameters:
    """
    Parameters for 4-element Windkessel model

    Adds inertance for high-frequency dynamics:
    - L: Arterial inertance
    - R_c: Characteristic impedance
    - R_p: Peripheral resistance
    - C: Arterial compliance
    """
    L: float = 0.005  # Arterial inertance (mmHg·s²/mL)
    R_c: float = 0.05  # Characteristic impedance (mmHg·s/mL)
    R_p: float = 1.0  # Peripheral resistance (mmHg·s/mL)
    C: float = 1.5  # Arterial compliance (mL/mmHg)
    P_0: float = 80.0  # Reference pressure (mmHg)


class Windkessel2Model:
    """
    2-element Windkessel model (Frank, 1899)

    State: P (arterial pressure)

    Differential equation:
    C·dP/dt = Q_in(t) - (P - P_0)/R

    Example:
        >>> model = Windkessel2Model()
        >>> P = 80.0  # Initial pressure (mmHg)
        >>> Q_in = 100.0  # Cardiac output (mL/s)
        >>> P_new = model.step(0.0, P, 0.01, Q_in)
    """

    def __init__(self, params: Optional[Windkessel2Parameters] = None):
        self.params = params if params is not None else Windkessel2Parameters()

    def derivative(self, t: float, P: float, Q_in: float) -> float:
        """
        Compute pressure derivative

        Args:
            t: Time (s)
            P: Arterial pressure (mmHg)
            Q_in: Input flow from heart (mL/s)

        Returns:
            dP/dt
        """
        p = self.params
        Q_out = (P - p.P_0) / p.R  # Peripheral outflow
        return (Q_in - Q_out) / p.C

    def step(self, t: float, P: float, dt: float, Q_in: float) -> float:
        """Forward Euler step"""
        dP_dt = self.derivative(t, P, Q_in)
        return P + dt * dP_dt

    def get_mean_arterial_pressure(self, P: float) -> float:
        """Calculate mean arterial pressure"""
        return P

    def get_peripheral_flow(self, P: float) -> float:
        """Calculate peripheral outflow"""
        return (P - self.params.P_0) / self.params.R


class Windkessel3Model:
    """
    3-element Windkessel model (Westerhof et al., 1971)

    State: P_a (aortic pressure)

    Differential equation:
    C·dP_a/dt = Q_in(t) - Q_p
    Q_p = (P_a - P_0)/R_p

    Aortic pressure:
    P_ao = P_a + R_c·Q_in(t)

    Example:
        >>> model = Windkessel3Model()
        >>> P_a = 80.0  # Initial pressure
        >>> Q_in = 100.0  # Cardiac output
        >>> P_a_new = model.step(0.0, P_a, 0.01, Q_in)
        >>> P_ao = model.get_aortic_pressure(P_a_new, Q_in)
    """

    def __init__(self, params: Optional[Windkessel3Parameters] = None):
        self.params = params if params is not None else Windkessel3Parameters()

    def derivative(self, t: float, P_a: float, Q_in: float) -> float:
        """
        Compute arterial pressure derivative

        Args:
            t: Time (s)
            P_a: Arterial pressure (mmHg)
            Q_in: Input flow (mL/s)

        Returns:
            dP_a/dt
        """
        p = self.params
        Q_p = (P_a - p.P_0) / p.R_p  # Peripheral flow
        return (Q_in - Q_p) / p.C

    def step(self, t: float, P_a: float, dt: float, Q_in: float) -> float:
        """Forward Euler step"""
        dP_a_dt = self.derivative(t, P_a, Q_in)
        return P_a + dt * dP_a_dt

    def get_aortic_pressure(self, P_a: float, Q_in: float) -> float:
        """
        Calculate proximal aortic pressure

        Args:
            P_a: Arterial pressure
            Q_in: Input flow

        Returns:
            Aortic pressure
        """
        return P_a + self.params.R_c * Q_in

    def get_peripheral_flow(self, P_a: float) -> float:
        """Calculate peripheral flow"""
        return (P_a - self.params.P_0) / self.params.R_p


class Windkessel4Model:
    """
    4-element Windkessel model with inertance (Stergiopulos et al., 1999)

    States: [P_a, Q_p]
    - P_a: Arterial pressure
    - Q_p: Peripheral flow

    Differential equations:
    C·dP_a/dt = Q_in(t) - Q_p
    L·dQ_p/dt = P_a - P_0 - R_p·Q_p

    Aortic pressure:
    P_ao = P_a + R_c·Q_in(t)

    Most accurate model for pulsatile hemodynamics.

    Example:
        >>> model = Windkessel4Model()
        >>> state = np.array([80.0, 80.0])  # [P_a, Q_p]
        >>> Q_in = 100.0
        >>> state_new = model.step(0.0, state, 0.01, Q_in)
    """

    def __init__(self, params: Optional[Windkessel4Parameters] = None):
        self.params = params if params is not None else Windkessel4Parameters()

    def derivatives(self, t: float, state: np.ndarray, Q_in: float) -> np.ndarray:
        """
        Compute state derivatives

        Args:
            t: Time (s)
            state: [P_a, Q_p]
            Q_in: Input flow (mL/s)

        Returns:
            [dP_a/dt, dQ_p/dt]
        """
        P_a, Q_p = state
        p = self.params

        dP_a_dt = (Q_in - Q_p) / p.C
        dQ_p_dt = (P_a - p.P_0 - p.R_p * Q_p) / p.L

        return np.array([dP_a_dt, dQ_p_dt])

    def step(self, t: float, state: np.ndarray, dt: float, Q_in: float) -> np.ndarray:
        """Forward Euler step"""
        derivs = self.derivatives(t, state, Q_in)
        return state + dt * derivs

    def get_aortic_pressure(self, state: np.ndarray, Q_in: float) -> float:
        """Calculate aortic pressure"""
        P_a = state[0]
        return P_a + self.params.R_c * Q_in

    def get_peripheral_flow(self, state: np.ndarray) -> float:
        """Get peripheral flow"""
        return state[1]

    def get_pulse_pressure(self, P_max: float, P_min: float) -> float:
        """Calculate pulse pressure"""
        return P_max - P_min

    def get_mean_arterial_pressure(self, P_systolic: float, P_diastolic: float) -> float:
        """
        Calculate mean arterial pressure

        MAP ≈ DBP + (SBP - DBP)/3
        """
        return P_diastolic + (P_systolic - P_diastolic) / 3.0


def couple_windkessel_to_heart(
    cardiac_output: float,
    heart_rate: float,
    windkessel_model: Windkessel3Model,
    systolic_duration: float = 0.3
) -> Tuple[float, float]:
    """
    Couple Windkessel model to cardiac output

    Args:
        cardiac_output: CO in L/min
        heart_rate: HR in bpm
        windkessel_model: Windkessel model instance
        systolic_duration: Systolic phase duration (s)

    Returns:
        (systolic_pressure, diastolic_pressure)
    """
    # Convert to mL/s
    CO_mL_per_s = cardiac_output * 1000.0 / 60.0

    # Cycle parameters
    cycle_time = 60.0 / heart_rate  # seconds
    systolic_time = min(systolic_duration, cycle_time * 0.4)
    diastolic_time = cycle_time - systolic_time

    # Simulate one cardiac cycle
    P_a = 80.0  # Initial pressure
    dt = 0.001  # 1ms timestep

    P_systolic = P_a
    P_diastolic = P_a

    # Systole
    t = 0.0
    while t < systolic_time:
        Q_in = CO_mL_per_s * (cycle_time / systolic_time)  # Scale flow to systole
        P_a = windkessel_model.step(t, P_a, dt, Q_in)
        P_ao = windkessel_model.get_aortic_pressure(P_a, Q_in)
        P_systolic = max(P_systolic, P_ao)
        t += dt

    # Diastole
    while t < cycle_time:
        Q_in = 0.0  # No flow during diastole
        P_a = windkessel_model.step(t, P_a, dt, Q_in)
        P_diastolic = min(P_diastolic, P_a)
        t += dt

    return P_systolic, P_diastolic


if __name__ == '__main__':
    print("=" * 60)
    print("Windkessel Arterial Hemodynamics Models")
    print("=" * 60)

    # 2-element model
    print("\n1. Two-element Windkessel (Frank, 1899):")
    wk2 = Windkessel2Model()
    P = 80.0
    for i in range(1000):
        Q_in = 100.0 if (i % 100 < 30) else 0.0  # Pulsatile flow
        P = wk2.step(i * 0.001, P, 0.001, Q_in)
    print(f"   Final pressure: {P:.1f} mmHg")

    # 3-element model
    print("\n2. Three-element Windkessel (Westerhof, 1971):")
    wk3 = Windkessel3Model()
    P_a = 80.0
    P_max, P_min = 80.0, 80.0

    for i in range(1000):
        Q_in = 100.0 if (i % 100 < 30) else 0.0
        P_a = wk3.step(i * 0.001, P_a, 0.001, Q_in)
        P_ao = wk3.get_aortic_pressure(P_a, Q_in)
        P_max = max(P_max, P_ao)
        P_min = min(P_min, P_a)

    print(f"   Systolic: {P_max:.1f} mmHg")
    print(f"   Diastolic: {P_min:.1f} mmHg")
    print(f"   MAP: {(P_min + (P_max - P_min) / 3.0):.1f} mmHg")

    # 4-element model
    print("\n3. Four-element Windkessel (Stergiopulos, 1999):")
    wk4 = Windkessel4Model()
    state = np.array([80.0, 80.0])
    P_max, P_min = 80.0, 80.0

    for i in range(1000):
        Q_in = 100.0 if (i % 100 < 30) else 0.0
        state = wk4.step(i * 0.001, state, 0.001, Q_in)
        P_ao = wk4.get_aortic_pressure(state, Q_in)
        P_max = max(P_max, P_ao)
        P_min = min(P_min, state[0])

    print(f"   Systolic: {P_max:.1f} mmHg")
    print(f"   Diastolic: {P_min:.1f} mmHg")
    print(f"   Pulse pressure: {P_max - P_min:.1f} mmHg")

    # Coupled to cardiac output
    print("\n4. Coupled to physiological cardiac output:")
    P_sys, P_dia = couple_windkessel_to_heart(
        cardiac_output=5.0,  # L/min
        heart_rate=70,  # bpm
        windkessel_model=wk3
    )
    MAP = P_dia + (P_sys - P_dia) / 3.0
    print(f"   CO: 5.0 L/min, HR: 70 bpm")
    print(f"   BP: {P_sys:.0f}/{P_dia:.0f} mmHg")
    print(f"   MAP: {MAP:.0f} mmHg")

    print("\n" + "=" * 60)
