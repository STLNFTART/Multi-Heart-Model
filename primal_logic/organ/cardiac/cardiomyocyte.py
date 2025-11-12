"""
Cardiomyocyte Model with Drug Effects

Enhanced cardiac cell model extending the Van der Pol oscillator
with electrophysiology, calcium dynamics, and drug interactions.

Mathematical formulation:
    Electrophysiology (Van der Pol-like):
    dV/dt = μ(1 - V²)V' - ω²V + I_ext + I_drug
    dV'/dt = V

    Calcium dynamics:
    dCa/dt = J_in - J_out - J_pump + Ca_drug_effect

    Contractility:
    Force = F_max · [Ca²⁺]^n / (EC50^n + [Ca²⁺]^n)

where:
    V: Membrane potential (normalized)
    Ca: Intracellular calcium
    I_drug: Drug effects on ion channels
    F_max: Maximum force
    EC50: Half-maximal calcium for contraction
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, Callable


@dataclass
class CardiomyocyteParameters:
    """Parameters for cardiomyocyte model"""
    # Van der Pol oscillator (electrical)
    mu: float = 1.5                    # Nonlinearity parameter
    omega: float = 1.0                 # Natural frequency (Hz)

    # Calcium dynamics
    J_in_max: float = 1.0              # Maximum Ca influx
    J_out_rate: float = 0.5            # Ca efflux rate
    J_pump_Vmax: float = 0.8           # SERCA pump max rate
    Ca_pump_Km: float = 0.5            # SERCA pump affinity

    # Contractility
    F_max: float = 100.0               # Maximum force (arbitrary units)
    EC50_contraction: float = 0.5      # Half-maximal [Ca] for contraction
    n_hill_contraction: float = 2.0    # Hill coefficient

    # Ion channel parameters
    g_Na: float = 1.0                  # Sodium conductance
    g_K: float = 1.0                   # Potassium conductance
    g_Ca: float = 0.5                  # Calcium conductance

    # Drug sensitivity
    hERG_sensitivity: float = 1.0      # Sensitivity to K+ channel blockers
    Ca_channel_sensitivity: float = 1.0
    Na_channel_sensitivity: float = 1.0

    # ATP dependence
    ATP_baseline: float = 1.0


class CardiomyocyteModel:
    """
    Enhanced cardiomyocyte model with drug effects.

    State variables:
    - V: Membrane potential
    - V_prime: dV/dt (for Van der Pol)
    - Ca: Intracellular calcium
    - ATP: Energy level

    Usage:
        >>> cardio = CardiomyocyteModel()
        >>> cardio.set_drug_effect(lambda t: {"hERG_block": 0.5})
        >>> times, states = cardio.simulate(t_span=(0, 10), dt=0.01)
    """

    def __init__(self, params: Optional[CardiomyocyteParameters] = None):
        self.params = params or CardiomyocyteParameters()

        # State: [V, V_prime, Ca, ATP]
        self.state = np.array([0.1, 0.0, 0.3, 1.0])

        # Drug effect function (returns dict of effects)
        self._drug_effect_func = lambda t: {}

        # External stimulus
        self._stimulus_func = lambda t: 0.0

    def set_drug_effect(self, func: Callable[[float], dict]):
        """
        Set drug effect function.

        Expected dict keys:
        - 'hERG_block': 0-1 (K+ channel block)
        - 'Ca_block': 0-1 (L-type Ca channel block)
        - 'Na_block': 0-1 (Na channel block)
        - 'mitochondrial': 0-1 (ATP depletion)
        """
        self._drug_effect_func = func

    def set_stimulus(self, func: Callable[[float], float]):
        """Set external stimulus (e.g., pacing)"""
        self._stimulus_func = func

    def compute_contractility(self, Ca: float) -> float:
        """
        Compute contractile force from calcium.

        Hill equation: F = F_max · [Ca]^n / (EC50^n + [Ca]^n)
        """
        Ca_n = Ca ** self.params.n_hill_contraction
        EC50_n = self.params.EC50_contraction ** self.params.n_hill_contraction

        force = self.params.F_max * Ca_n / (EC50_n + Ca_n)

        return force

    def compute_APD(self, V_trace: np.ndarray, times: np.ndarray, threshold: float = 0.9) -> float:
        """
        Compute Action Potential Duration (APD).

        Proxy for QT interval.
        """
        # Find upstroke
        upstroke_idx = np.where(V_trace > threshold)[0]

        if len(upstroke_idx) < 2:
            return 0.0

        # APD = time from upstroke to repolarization
        first_up = upstroke_idx[0]
        repolarization_idx = np.where(V_trace[first_up:] < -threshold)[0]

        if len(repolarization_idx) == 0:
            return 0.0

        APD = times[first_up + repolarization_idx[0]] - times[first_up]

        return APD

    def derivatives(self, state: np.ndarray, t: float) -> np.ndarray:
        """
        Compute time derivatives.

        State: [V, V_prime, Ca, ATP]
        """
        V, V_prime, Ca, ATP = state

        drug_effects = self._drug_effect_func(t)
        stimulus = self._stimulus_func(t)

        # Extract drug effects
        hERG_block = drug_effects.get('hERG_block', 0.0)
        Ca_block = drug_effects.get('Ca_block', 0.0)
        Na_block = drug_effects.get('Na_block', 0.0)
        mito_damage = drug_effects.get('mitochondrial', 0.0)

        # Effective conductances (reduced by drugs)
        g_K_eff = self.params.g_K * (1 - hERG_block * self.params.hERG_sensitivity)
        g_Ca_eff = self.params.g_Ca * (1 - Ca_block * self.params.Ca_channel_sensitivity)
        g_Na_eff = self.params.g_Na * (1 - Na_block * self.params.Na_channel_sensitivity)

        # Van der Pol oscillator with drug-modulated currents
        I_Na = g_Na_eff * (-V)  # Simplified Na current
        I_K = g_K_eff * V_prime  # Delayed rectifier
        I_ext = stimulus

        dV_prime = (
            self.params.mu * (1 - V**2) * V_prime
            - self.params.omega**2 * V
            + I_Na + I_K + I_ext
        )

        dV = V_prime

        # Calcium dynamics
        J_in = self.params.J_in_max * g_Ca_eff * (1.0 if V > 0 else 0.0)  # Voltage-gated
        J_out = self.params.J_out_rate * Ca
        J_pump = (self.params.J_pump_Vmax * Ca) / (self.params.Ca_pump_Km + Ca)

        # SERCA pump requires ATP
        J_pump *= (ATP / (ATP + 0.5))

        dCa = J_in - J_out - J_pump

        # ATP dynamics
        ATP_production = 1.0 * (1 - mito_damage)
        ATP_consumption = 0.5 + 0.3 * J_pump  # Pumping costs energy

        dATP = ATP_production - ATP_consumption - 0.2 * ATP

        return np.array([dV, dV_prime, dCa, dATP])

    def integrate_step(self, dt: float, t: float) -> np.ndarray:
        """Update state by one timestep using RK4"""
        k1 = self.derivatives(self.state, t)
        k2 = self.derivatives(self.state + 0.5*dt*k1, t + 0.5*dt)
        k3 = self.derivatives(self.state + 0.5*dt*k2, t + 0.5*dt)
        k4 = self.derivatives(self.state + dt*k3, t + dt)

        self.state += (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

        # Ensure physical bounds
        self.state[2] = np.clip(self.state[2], 0.0, 5.0)  # Ca
        self.state[3] = np.clip(self.state[3], 0.0, 2.0)  # ATP

        return self.state

    def simulate(
        self,
        t_span: Tuple[float, float],
        dt: float = 0.01
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate cardiomyocyte dynamics.

        Returns:
            (times, states) where states has shape (N, 4)
        """
        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt)

        times = np.linspace(t_start, t_end, n_steps)
        states = np.zeros((n_steps, 4))
        states[0] = self.state

        for i in range(1, n_steps):
            t = times[i]
            states[i] = self.integrate_step(dt, t)

        return times, states

    def get_cardiac_metrics(self, times: np.ndarray, states: np.ndarray) -> dict:
        """
        Extract cardiac performance metrics.

        Returns:
            Dictionary with heart rate, contractility, APD, etc.
        """
        V_trace = states[:, 0]
        Ca_trace = states[:, 2]

        # Heart rate (count peaks)
        peaks = np.where((V_trace[1:-1] > V_trace[:-2]) & (V_trace[1:-1] > V_trace[2:]))[0]

        if len(peaks) > 1:
            dt_peaks = np.diff(times[peaks])
            heart_rate = 60.0 / np.mean(dt_peaks)  # BPM
        else:
            heart_rate = 0.0

        # APD (QT interval proxy)
        APD = self.compute_APD(V_trace, times)

        # Contractility (mean force)
        forces = [self.compute_contractility(Ca) for Ca in Ca_trace]
        mean_contractility = np.mean(forces)

        # ATP level
        mean_ATP = np.mean(states[:, 3])

        return {
            'heart_rate': heart_rate,
            'APD': APD,
            'QTc_proxy': APD * np.sqrt(heart_rate / 60.0) if heart_rate > 0 else 0.0,
            'mean_contractility': mean_contractility,
            'mean_ATP': mean_ATP
        }

    def reset(self):
        """Reset to initial state"""
        self.state = np.array([0.1, 0.0, 0.3, 1.0])


if __name__ == "__main__":
    print("=" * 70)
    print("CARDIOMYOCYTE MODEL WITH DRUG EFFECTS")
    print("=" * 70)

    # Example 1: Baseline dynamics
    print("\n1. Testing baseline cardiac dynamics...")
    cardio = CardiomyocyteModel()

    times, states = cardio.simulate(t_span=(0, 10), dt=0.01)
    metrics = cardio.get_cardiac_metrics(times, states)

    print(f"   Heart rate: {metrics['heart_rate']:.1f} BPM")
    print(f"   APD: {metrics['APD']:.3f} s")
    print(f"   QTc proxy: {metrics['QTc_proxy']:.3f}")
    print(f"   Mean contractility: {metrics['mean_contractility']:.2f}")
    print(f"   Mean ATP: {metrics['mean_ATP']:.3f}")

    # Example 2: hERG channel block (QT prolongation)
    print("\n2. Testing hERG K+ channel block...")
    cardio.reset()

    # 50% hERG block
    cardio.set_drug_effect(lambda t: {'hERG_block': 0.5})

    times, states = cardio.simulate(t_span=(0, 10), dt=0.01)
    metrics_drug = cardio.get_cardiac_metrics(times, states)

    print(f"   Heart rate: {metrics_drug['heart_rate']:.1f} BPM")
    print(f"   APD: {metrics_drug['APD']:.3f} s ({(metrics_drug['APD']/metrics['APD']-1)*100:+.1f}%)")
    print(f"   QTc proxy: {metrics_drug['QTc_proxy']:.3f} ({(metrics_drug['QTc_proxy']/metrics['QTc_proxy']-1)*100:+.1f}%)")
    print(f"   Arrhythmia risk: {'HIGH' if metrics_drug['APD'] > 1.2 * metrics['APD'] else 'LOW'}")

    # Example 3: Mitochondrial toxicity
    print("\n3. Testing mitochondrial cardiotoxicity...")
    cardio.reset()

    # Progressive mitochondrial damage
    cardio.set_drug_effect(lambda t: {'mitochondrial': min(0.8, 0.1 * t)})

    times, states = cardio.simulate(t_span=(0, 20), dt=0.01)

    print(f"   Initial ATP: {states[0, 3]:.3f}")
    print(f"   Final ATP: {states[-1, 3]:.3f}")
    print(f"   ATP depletion: {(1 - states[-1, 3]/states[0, 3])*100:.1f}%")

    metrics_mito = cardio.get_cardiac_metrics(times, states)
    print(f"   Contractility loss: {(1 - metrics_mito['mean_contractility']/metrics['mean_contractility'])*100:.1f}%")

    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("=" * 70)
    print("✓ ELECTROPHYSIOLOGY: Van der Pol oscillator")
    print("✓ CALCIUM: Intracellular Ca²⁺ dynamics")
    print("✓ CONTRACTILITY: Ca-dependent force generation")
    print("✓ DRUG EFFECTS: hERG, Ca/Na channels, mitochondria")
    print("✓ METRICS: HR, APD/QTc, contractility, ATP")
    print("=" * 70)
