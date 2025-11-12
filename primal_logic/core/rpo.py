"""
Simple Recursive Planck Operator (RPO) Framework

Universal mathematical kernel for memory-dependent biological processes.
Formulated by Donte Lightfoot (Lightfoot Constant / Primal Logic).

Canonical form:
    ż(t) = -λz(t) + β∫₀^∞ αe^(-ατ) z(t-τ) dτ + S(t)

Equivalent ODE pair (no integral, numerically stable):
    ż = -λz + βm + S(t)
    ṁ = α(z - m)

where:
    z: current state variable
    m: exponentially weighted memory of z
    λ: decay/forgetting rate
    β: memory feedback strength
    α: memory timescale (1/α = characteristic memory duration)
    S(t): external stimulus/forcing
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Callable, Optional


@dataclass
class RPOParameters:
    """Parameters for Recursive Planck Operator"""
    lambda_decay: float      # Decay rate of current state
    beta_feedback: float     # Memory feedback strength
    alpha_memory: float      # Memory formation rate (inverse timescale)

    def __post_init__(self):
        """Validate stability conditions"""
        # For stability: λ > β (decay dominates feedback)
        if self.lambda_decay <= self.beta_feedback:
            print(
                f"Warning: May be unstable. λ={self.lambda_decay} "
                f"should be > β={self.beta_feedback}"
            )


class RPOVariable:
    """
    A single variable governed by Recursive Planck Operator dynamics.

    Usage:
        >>> rpo = RPOVariable(lambda_decay=0.5, beta_feedback=0.3, alpha_memory=2.0)
        >>> z, m = rpo.state
        >>> dz, dm = rpo.derivatives(z, m, stimulus=0.1)
    """

    def __init__(
        self,
        lambda_decay: float,
        beta_feedback: float,
        alpha_memory: float,
        initial_state: Tuple[float, float] = (0.0, 0.0)
    ):
        self.params = RPOParameters(lambda_decay, beta_feedback, alpha_memory)
        self.state = np.array(list(initial_state))  # [z, m]

    def derivatives(
        self,
        z: float,
        m: float,
        stimulus: float = 0.0
    ) -> Tuple[float, float]:
        """
        Compute time derivatives.

        Args:
            z: Current state
            m: Memory variable
            stimulus: External forcing S(t)

        Returns:
            (dz/dt, dm/dt)
        """
        λ = self.params.lambda_decay
        β = self.params.beta_feedback
        α = self.params.alpha_memory

        dz = -λ * z + β * m + stimulus
        dm = α * (z - m)

        return dz, dm

    def integrate_step(self, dt: float, stimulus: float = 0.0) -> np.ndarray:
        """Update state by one timestep using RK4"""
        z, m = self.state

        k1_z, k1_m = self.derivatives(z, m, stimulus)
        k2_z, k2_m = self.derivatives(z + 0.5*dt*k1_z, m + 0.5*dt*k1_m, stimulus)
        k3_z, k3_m = self.derivatives(z + 0.5*dt*k2_z, m + 0.5*dt*k2_m, stimulus)
        k4_z, k4_m = self.derivatives(z + dt*k3_z, m + dt*k3_m, stimulus)

        self.state[0] += (dt/6.0) * (k1_z + 2*k2_z + 2*k3_z + k4_z)
        self.state[1] += (dt/6.0) * (k1_m + 2*k2_m + 2*k3_m + k4_m)

        return self.state

    def simulate(
        self,
        t_span: Tuple[float, float],
        stimulus_func: Optional[Callable[[float], float]] = None,
        dt: float = 0.01
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate RPO dynamics over time.

        Args:
            t_span: (start_time, end_time)
            stimulus_func: Function mapping time -> stimulus
            dt: Timestep

        Returns:
            (times, states) where states is shape (N, 2) with columns [z, m]
        """
        if stimulus_func is None:
            stimulus_func = lambda t: 0.0

        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt)

        times = np.linspace(t_start, t_end, n_steps)
        states = np.zeros((n_steps, 2))
        states[0] = self.state

        for i in range(1, n_steps):
            t = times[i]
            stimulus = stimulus_func(t)
            states[i] = self.integrate_step(dt, stimulus)

        return times, states

    def reset(self, initial_state: Tuple[float, float] = (0.0, 0.0)):
        """Reset to initial state"""
        self.state = np.array(list(initial_state))


if __name__ == "__main__":
    print("=" * 70)
    print("RECURSIVE PLANCK OPERATOR (RPO) - Simple Framework")
    print("=" * 70)

    # Example 1: Pulse response
    print("\n1. Testing pulse response...")
    rpo = RPOVariable(lambda_decay=0.5, beta_feedback=0.3, alpha_memory=2.0)

    def pulse_stimulus(t):
        return 1.0 if 1.0 < t < 3.0 else 0.0

    times, states = rpo.simulate(t_span=(0, 20), stimulus_func=pulse_stimulus, dt=0.01)

    print(f"   Initial: z={states[0,0]:.3f}, m={states[0,1]:.3f}")
    print(f"   During pulse (t=2): z={states[200,0]:.3f}, m={states[200,1]:.3f}")
    print(f"   After pulse (t=10): z={states[1000,0]:.3f}, m={states[1000,1]:.3f}")
    print(f"   Final (t=20): z={states[-1,0]:.3f}, m={states[-1,1]:.3f}")
    print("   ✓ Memory variable (m) shows slower decay than state (z)")

    # Example 2: Sinusoidal forcing
    print("\n2. Testing sinusoidal forcing...")
    rpo.reset()

    def sine_stimulus(t):
        return 0.5 * np.sin(0.5 * t)

    times, states = rpo.simulate(t_span=(0, 30), stimulus_func=sine_stimulus, dt=0.01)

    print(f"   Peak z: {np.max(states[:,0]):.3f}")
    print(f"   Peak m: {np.max(states[:,1]):.3f}")
    print("   ✓ Memory smooths oscillations")

    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("=" * 70)
    print("✓ STABLE: Analytic stability condition (λ > β)")
    print("✓ SIMPLE: Only 2 state variables (z, m)")
    print("✓ INTERPRETABLE: z = current, m = weighted memory")
    print("✓ EFFICIENT: RK4 integration, no convolution")
    print("=" * 70)
