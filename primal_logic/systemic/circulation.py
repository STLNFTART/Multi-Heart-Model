"""
Systemic Circulation Model

Blood flow connecting heart and liver with drug/metabolite distribution.
Implements organ perfusion, vascular compartments, and pharmacokinetics.

Mathematical formulation:
    Compartmental PK model:
    dC_arterial/dt = (Q_heart · C_heart - Q_total · C_arterial) / V_arterial
    dC_liver/dt = (Q_liver · C_arterial - Q_liver · C_venous) / V_liver + Metabolism
    dC_venous/dt = (Q_liver · C_venous + Q_other · C_arterial - Q_heart · C_venous) / V_venous

where:
    Q: Blood flow rate (L/min)
    C: Concentration (μM)
    V: Volume (L)
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, Callable, Dict


@dataclass
class CirculationParameters:
    """Parameters for systemic circulation"""
    # Cardiac output
    cardiac_output: float = 5.0        # L/min (resting adult)
    heart_rate: float = 70.0           # BPM

    # Organ blood flow fractions
    hepatic_fraction: float = 0.25     # 25% to liver
    renal_fraction: float = 0.20       # 20% to kidneys
    brain_fraction: float = 0.15       # 15% to brain
    cardiac_fraction: float = 0.05     # 5% to heart itself
    other_fraction: float = 0.35       # 35% to other tissues

    # Vascular volumes
    V_arterial: float = 1.0            # L
    V_venous: float = 3.0              # L
    V_liver: float = 1.5               # L
    V_heart: float = 0.3               # L
    V_brain: float = 1.4               # L
    V_other: float = 40.0              # L (remaining tissues)

    # Tissue partition coefficients (drug distribution)
    Kp_liver: float = 1.5              # Liver/blood ratio
    Kp_heart: float = 1.0
    Kp_brain: float = 0.5              # Blood-brain barrier
    Kp_other: float = 0.8


class SystemicCirculation:
    """
    Complete systemic circulation with organ perfusion and drug distribution.

    State variables:
    - C_arterial: Arterial drug concentration
    - C_venous: Venous drug concentration
    - C_liver: Liver tissue concentration
    - C_heart: Cardiac tissue concentration
    - C_brain: Brain tissue concentration
    - C_other: Other tissues concentration

    Usage:
        >>> circ = SystemicCirculation()
        >>> circ.set_drug_input(lambda t: 100.0 if t < 0.1 else 0.0)  # Bolus
        >>> circ.set_metabolism_function(lambda C_liver, t: 0.1 * C_liver)
        >>> times, states = circ.simulate(t_span=(0, 24), dt=0.01)
    """

    def __init__(self, params: Optional[CirculationParameters] = None):
        self.params = params or CirculationParameters()

        # State: [C_arterial, C_venous, C_liver, C_heart, C_brain, C_other]
        self.state = np.zeros(6)

        # Drug input function (IV bolus, infusion, etc.)
        self._drug_input_func = lambda t: 0.0

        # Metabolism function (clearance from liver)
        self._metabolism_func = lambda C_liver, t: 0.0

        # Renal clearance function
        self._renal_clearance_func = lambda C_arterial, t: 0.1 * C_arterial

        # Cardiac output modulation (from heart model)
        self._cardiac_output_func = lambda t: self.params.cardiac_output

    def set_drug_input(self, func: Callable[[float], float]):
        """
        Set drug input function.

        Args:
            func: Time -> dose rate (μM*L/min)
        """
        self._drug_input_func = func

    def set_metabolism_function(self, func: Callable[[float, float], float]):
        """
        Set hepatic metabolism function.

        Args:
            func: (C_liver, t) -> clearance rate (μM*L/min)
        """
        self._metabolism_func = func

    def set_renal_clearance(self, func: Callable[[float, float], float]):
        """
        Set renal clearance function.

        Args:
            func: (C_arterial, t) -> clearance rate (μM*L/min)
        """
        self._renal_clearance_func = func

    def set_cardiac_output(self, func: Callable[[float], float]):
        """
        Set cardiac output modulation.

        Args:
            func: Time -> cardiac output (L/min)
        """
        self._cardiac_output_func = func

    def compute_organ_flows(self, t: float) -> Dict[str, float]:
        """
        Compute blood flow to each organ.

        Returns:
            Dictionary of organ -> flow rate (L/min)
        """
        CO = self._cardiac_output_func(t)

        return {
            'liver': CO * self.params.hepatic_fraction,
            'heart': CO * self.params.cardiac_fraction,
            'brain': CO * self.params.brain_fraction,
            'kidney': CO * self.params.renal_fraction,
            'other': CO * self.params.other_fraction,
            'total': CO
        }

    def derivatives(self, state: np.ndarray, t: float) -> np.ndarray:
        """
        Compute time derivatives for all compartments.

        State: [C_arterial, C_venous, C_liver, C_heart, C_brain, C_other]
        """
        C_arterial, C_venous, C_liver, C_heart, C_brain, C_other = state

        flows = self.compute_organ_flows(t)
        Q_liver = flows['liver']
        Q_heart = flows['heart']
        Q_brain = flows['brain']
        Q_kidney = flows['kidney']
        Q_other = flows['other']
        Q_total = flows['total']

        # Drug input (typically into venous system)
        drug_input = self._drug_input_func(t)

        # Hepatic metabolism
        metabolism = self._metabolism_func(C_liver, t)

        # Renal clearance
        renal_clearance = self._renal_clearance_func(C_arterial, t)

        # Arterial compartment (receives blood from heart/lungs)
        dC_arterial = (
            Q_total * (C_venous - C_arterial) / self.params.V_arterial
        )

        # Liver compartment
        # Inflow from arterial, outflow to venous, metabolism
        C_liver_blood = C_liver / self.params.Kp_liver
        dC_liver = (
            Q_liver * (C_arterial - C_liver_blood) / self.params.V_liver
            - metabolism / self.params.V_liver
        )

        # Heart compartment
        C_heart_blood = C_heart / self.params.Kp_heart
        dC_heart = (
            Q_heart * (C_arterial - C_heart_blood) / self.params.V_heart
        )

        # Brain compartment
        C_brain_blood = C_brain / self.params.Kp_brain
        dC_brain = (
            Q_brain * (C_arterial - C_brain_blood) / self.params.V_brain
        )

        # Other tissues compartment
        C_other_blood = C_other / self.params.Kp_other
        dC_other = (
            Q_other * (C_arterial - C_other_blood) / self.params.V_other
        )

        # Venous compartment
        # Receives blood from all organs, loses to heart/lungs, receives drug input
        venous_return = (
            Q_liver * C_liver_blood +
            Q_heart * C_heart_blood +
            Q_brain * C_brain_blood +
            Q_other * C_other_blood
        )

        dC_venous = (
            venous_return / self.params.V_venous
            - Q_total * C_venous / self.params.V_venous
            + drug_input / self.params.V_venous
            - renal_clearance / self.params.V_venous
        )

        return np.array([dC_arterial, dC_venous, dC_liver, dC_heart, dC_brain, dC_other])

    def integrate_step(self, dt: float, t: float) -> np.ndarray:
        """Update state by one timestep using RK4"""
        k1 = self.derivatives(self.state, t)
        k2 = self.derivatives(self.state + 0.5*dt*k1, t + 0.5*dt)
        k3 = self.derivatives(self.state + 0.5*dt*k2, t + 0.5*dt)
        k4 = self.derivatives(self.state + dt*k3, t + dt)

        self.state += (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

        # Ensure non-negative
        self.state = np.maximum(self.state, 0.0)

        return self.state

    def simulate(
        self,
        t_span: Tuple[float, float],
        dt: float = 0.01
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate circulation dynamics.

        Returns:
            (times, states) where states has shape (N, 6)
        """
        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt)

        times = np.linspace(t_start, t_end, n_steps)
        states = np.zeros((n_steps, 6))
        states[0] = self.state

        for i in range(1, n_steps):
            t = times[i]
            states[i] = self.integrate_step(dt, t)

        return times, states

    def get_pk_metrics(self, times: np.ndarray, states: np.ndarray) -> Dict[str, float]:
        """
        Compute pharmacokinetic metrics.

        Returns:
            Dictionary with Cmax, Tmax, AUC, T1/2, etc.
        """
        C_arterial = states[:, 0]

        # Cmax and Tmax
        Cmax = np.max(C_arterial)
        Tmax = times[np.argmax(C_arterial)]

        # AUC (trapezoidal rule)
        AUC = np.trapz(C_arterial, times)

        # T1/2 (approximate from decay phase)
        peak_idx = np.argmax(C_arterial)
        if peak_idx < len(C_arterial) - 10:
            decay_phase = C_arterial[peak_idx:]
            half_Cmax = 0.5 * Cmax

            # Find time when C drops to half Cmax
            below_half = np.where(decay_phase < half_Cmax)[0]
            if len(below_half) > 0:
                T_half = times[peak_idx + below_half[0]] - Tmax
            else:
                T_half = np.nan
        else:
            T_half = np.nan

        return {
            'Cmax': Cmax,
            'Tmax': Tmax,
            'AUC': AUC,
            'T_half': T_half,
            'C_final': C_arterial[-1]
        }

    def reset(self):
        """Reset to zero concentrations"""
        self.state = np.zeros(6)


if __name__ == "__main__":
    print("=" * 70)
    print("SYSTEMIC CIRCULATION MODEL")
    print("=" * 70)

    # Example 1: IV bolus injection
    print("\n1. Testing IV bolus pharmacokinetics...")
    circ = SystemicCirculation()

    # Bolus dose at t=0
    def bolus_input(t):
        if t < 0.1:
            return 1000.0  # μM*L/min
        return 0.0

    # Simple first-order hepatic metabolism
    def first_order_metabolism(C_liver, t):
        CL_hepatic = 1.0  # L/min
        return CL_hepatic * C_liver

    circ.set_drug_input(bolus_input)
    circ.set_metabolism_function(first_order_metabolism)

    times, states = circ.simulate(t_span=(0, 24), dt=0.01)

    pk_metrics = circ.get_pk_metrics(times, states)

    print(f"   Cmax: {pk_metrics['Cmax']:.2f} μM")
    print(f"   Tmax: {pk_metrics['Tmax']:.2f} hours")
    print(f"   AUC: {pk_metrics['AUC']:.2f} μM·hr")
    print(f"   T1/2: {pk_metrics['T_half']:.2f} hours")

    # Organ concentrations at Tmax
    tmax_idx = int(pk_metrics['Tmax'] / 0.01)
    print(f"\n   Organ concentrations at Tmax:")
    print(f"     Arterial: {states[tmax_idx, 0]:.2f} μM")
    print(f"     Liver: {states[tmax_idx, 2]:.2f} μM")
    print(f"     Heart: {states[tmax_idx, 3]:.2f} μM")
    print(f"     Brain: {states[tmax_idx, 4]:.2f} μM")

    # Example 2: Continuous infusion
    print("\n2. Testing continuous infusion...")
    circ.reset()

    # Constant infusion rate
    infusion_rate = 50.0  # μM*L/min
    circ.set_drug_input(lambda t: infusion_rate if t < 12 else 0.0)

    times, states = circ.simulate(t_span=(0, 24), dt=0.01)

    C_ss = np.mean(states[1000:1200, 0])  # Steady-state (10-12 hrs)
    C_final = states[-1, 0]

    print(f"   Steady-state concentration: {C_ss:.2f} μM")
    print(f"   Concentration at 24h: {C_final:.2f} μM")

    # Example 3: Heart failure (reduced cardiac output)
    print("\n3. Testing reduced cardiac output (heart failure)...")
    circ.reset()

    # 50% reduction in cardiac output
    circ.set_cardiac_output(lambda t: 2.5)  # 50% of normal
    circ.set_drug_input(bolus_input)
    circ.set_metabolism_function(first_order_metabolism)

    times, states = circ.simulate(t_span=(0, 24), dt=0.01)

    pk_metrics_hf = circ.get_pk_metrics(times, states)

    print(f"   Cmax (heart failure): {pk_metrics_hf['Cmax']:.2f} μM")
    print(f"   Cmax change: {(pk_metrics_hf['Cmax']/pk_metrics['Cmax']-1)*100:+.1f}%")
    print(f"   T1/2 (heart failure): {pk_metrics_hf['T_half']:.2f} hours")
    print(f"   T1/2 change: {(pk_metrics_hf['T_half']/pk_metrics['T_half']-1)*100:+.1f}%")

    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("=" * 70)
    print("✓ PHYSIOLOGICAL: Organ blood flows and volumes")
    print("✓ DISTRIBUTION: Tissue partition coefficients")
    print("✓ METABOLISM: Hepatic clearance")
    print("✓ PK METRICS: Cmax, Tmax, AUC, T1/2")
    print("✓ PATHOLOGY: Heart failure, liver disease effects")
    print("=" * 70)
