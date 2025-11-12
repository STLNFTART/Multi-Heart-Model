"""
Immune Signaling and Inflammatory Response

Cellular-scale immune dynamics with memory and feedback.
Cytokine production, accumulation, and resolution with bidirectional coupling
to tissue damage and systemic stress.

Mathematical formulation:
    İ(t) = ρ·R(t) - δ·I(t)

    Modulated decay rates:
    λ_b(t) = λ_b0·(1 + α_b·I(t))
    λ_h(t) = λ_h0·(1 + α_h·I(t))

where:
    I(t): Immune intensity (cytokine concentration)
    R(t): Receptor occupancy (damage signal)
    ρ: Immune accumulation rate
    δ: Resolution/decay rate
    λ_b, λ_h: Brain and heart decay rates (modulated by inflammation)
    α_b, α_h: Sensitivity coefficients
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, Callable


@dataclass
class ImmuneParameters:
    """Parameters for immune response"""
    rho_accumulation: float = 0.1      # Immune accumulation rate
    delta_resolution: float = 0.08     # Resolution/decay rate

    # Feedback to other systems
    alpha_brain: float = 0.05          # Brain sensitivity to inflammation
    alpha_heart: float = 0.03          # Cardiac sensitivity to inflammation
    alpha_liver: float = 0.1           # Liver sensitivity to inflammation

    # Baseline decay rates
    lambda_brain_0: float = 0.3
    lambda_heart_0: float = 0.8

    # Pro/anti-inflammatory balance
    pro_inflammatory_weight: float = 1.0
    anti_inflammatory_weight: float = 0.5


class ImmuneSignaling:
    """
    Immune response with accumulation and decay.

    Bidirectional coupling:
    - Bottom-up: Tissue damage → immune activation
    - Top-down: Inflammation → modulated organ function

    Usage:
        >>> immune = ImmuneSignaling()
        >>> immune.set_damage_signal(lambda t: receptor_occupancy)
        >>> times, intensity = immune.simulate(t_span=(0, 100), dt=0.01)
    """

    def __init__(self, params: Optional[ImmuneParameters] = None):
        self.params = params or ImmuneParameters()
        self.state = 0.0  # Initial immune intensity

        # Default damage signal (none)
        self._damage_signal = lambda t: 0.0

        # Anti-inflammatory component (separate state)
        self.anti_inflammatory = 0.0

    def set_damage_signal(self, func: Callable[[float], float]):
        """Set tissue damage/receptor occupancy signal"""
        self._damage_signal = func

    def derivatives(self, I: float, I_anti: float, t: float) -> Tuple[float, float]:
        """
        Compute dI/dt for pro- and anti-inflammatory components.

        Args:
            I: Pro-inflammatory intensity
            I_anti: Anti-inflammatory intensity
            t: Current time

        Returns:
            (dI_pro/dt, dI_anti/dt)
        """
        damage = self._damage_signal(t)

        # Pro-inflammatory: driven by damage, suppressed by anti-inflammatory
        dI_pro = (
            self.params.rho_accumulation * damage * self.params.pro_inflammatory_weight
            - self.params.delta_resolution * I
            - 0.3 * I_anti  # Suppression by regulatory response
        )

        # Anti-inflammatory: counter-regulatory response to inflammation
        dI_anti = (
            0.3 * I * self.params.anti_inflammatory_weight  # Activated by inflammation
            - 0.5 * self.params.delta_resolution * I_anti  # Slower resolution
        )

        return dI_pro, dI_anti

    def integrate_step(self, dt: float, t: float) -> Tuple[float, float]:
        """Update state by one timestep using RK4"""
        I = self.state
        I_anti = self.anti_inflammatory

        k1_pro, k1_anti = self.derivatives(I, I_anti, t)
        k2_pro, k2_anti = self.derivatives(
            I + 0.5*dt*k1_pro,
            I_anti + 0.5*dt*k1_anti,
            t + 0.5*dt
        )
        k3_pro, k3_anti = self.derivatives(
            I + 0.5*dt*k2_pro,
            I_anti + 0.5*dt*k2_anti,
            t + 0.5*dt
        )
        k4_pro, k4_anti = self.derivatives(
            I + dt*k3_pro,
            I_anti + dt*k3_anti,
            t + dt
        )

        self.state += (dt/6.0) * (k1_pro + 2*k2_pro + 2*k3_pro + k4_pro)
        self.anti_inflammatory += (dt/6.0) * (k1_anti + 2*k2_anti + 2*k3_anti + k4_anti)

        # Ensure non-negative
        self.state = max(0.0, self.state)
        self.anti_inflammatory = max(0.0, self.anti_inflammatory)

        return self.state, self.anti_inflammatory

    def simulate(
        self,
        t_span: Tuple[float, float],
        dt: float = 0.01,
        initial_intensity: float = 0.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Simulate immune dynamics.

        Args:
            t_span: (start_time, end_time)
            dt: Timestep
            initial_intensity: Initial immune intensity

        Returns:
            (times, pro_inflammatory, anti_inflammatory)
        """
        self.state = initial_intensity
        self.anti_inflammatory = 0.0

        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt)

        times = np.linspace(t_start, t_end, n_steps)
        pro_inflammatory = np.zeros(n_steps)
        anti_inflammatory = np.zeros(n_steps)

        pro_inflammatory[0] = self.state
        anti_inflammatory[0] = self.anti_inflammatory

        for i in range(1, n_steps):
            t = times[i]
            pro, anti = self.integrate_step(dt, t)
            pro_inflammatory[i] = pro
            anti_inflammatory[i] = anti

        return times, pro_inflammatory, anti_inflammatory

    def get_modulated_decay_rates(self, I: float) -> Tuple[float, float]:
        """
        Compute modulated decay rates for brain and heart.

        Args:
            I: Current immune intensity

        Returns:
            (lambda_brain, lambda_heart)
        """
        lambda_brain = self.params.lambda_brain_0 * (1 + self.params.alpha_brain * I)
        lambda_heart = self.params.lambda_heart_0 * (1 + self.params.alpha_heart * I)

        return lambda_brain, lambda_heart

    def get_net_inflammatory_state(self) -> float:
        """Return net inflammation (pro - anti)"""
        return max(0.0, self.state - 0.5 * self.anti_inflammatory)

    def reset(self, initial_intensity: float = 0.0):
        """Reset to initial state"""
        self.state = initial_intensity
        self.anti_inflammatory = 0.0


# ==============================================================================
# CYTOKINE-SPECIFIC MODELS
# ==============================================================================

class CytokineProfiles:
    """
    Pre-configured cytokine response profiles.
    """

    @staticmethod
    def acute_inflammatory() -> ImmuneSignaling:
        """
        Acute inflammatory response (e.g., bacterial infection).
        Fast accumulation, moderate resolution.
        """
        params = ImmuneParameters(
            rho_accumulation=0.15,
            delta_resolution=0.1,
            alpha_brain=0.08,
            alpha_heart=0.05,
            pro_inflammatory_weight=1.2,
            anti_inflammatory_weight=0.4
        )
        return ImmuneSignaling(params)

    @staticmethod
    def chronic_inflammatory() -> ImmuneSignaling:
        """
        Chronic low-grade inflammation (e.g., metabolic syndrome).
        Slow accumulation, poor resolution.
        """
        params = ImmuneParameters(
            rho_accumulation=0.05,
            delta_resolution=0.02,
            alpha_brain=0.1,
            alpha_heart=0.06,
            alpha_liver=0.15,
            pro_inflammatory_weight=0.8,
            anti_inflammatory_weight=0.3  # Impaired regulation
        )
        return ImmuneSignaling(params)

    @staticmethod
    def cytokine_storm() -> ImmuneSignaling:
        """
        Cytokine storm (e.g., severe COVID-19, sepsis).
        Very fast accumulation, delayed resolution.
        """
        params = ImmuneParameters(
            rho_accumulation=0.3,
            delta_resolution=0.05,
            alpha_brain=0.15,
            alpha_heart=0.1,
            alpha_liver=0.2,
            pro_inflammatory_weight=2.0,
            anti_inflammatory_weight=0.2  # Overwhelmed regulation
        )
        return ImmuneSignaling(params)


if __name__ == "__main__":
    print("=" * 70)
    print("IMMUNE SIGNALING AND INFLAMMATORY RESPONSE")
    print("=" * 70)

    # Example 1: Acute infection
    print("\n1. Testing acute inflammatory response...")
    immune = CytokineProfiles.acute_inflammatory()

    # Damage signal: rapid rise, slow decay (pathogen clearance)
    def acute_damage(t):
        if t < 10:
            return 0.5 * (1 - np.exp(-0.5 * t))
        else:
            return 0.5 * np.exp(-0.1 * (t - 10))

    immune.set_damage_signal(acute_damage)
    times, pro, anti = immune.simulate(t_span=(0, 100), dt=0.01)

    print(f"   Peak pro-inflammatory: {np.max(pro):.3f}")
    print(f"   Peak anti-inflammatory: {np.max(anti):.3f}")
    print(f"   Time to peak: {times[np.argmax(pro)]:.1f}")
    print(f"   Final intensity: {pro[-1]:.3f}")

    # Example 2: Chronic inflammation
    print("\n2. Testing chronic low-grade inflammation...")
    chronic = CytokineProfiles.chronic_inflammatory()

    # Sustained low-level damage
    chronic.set_damage_signal(lambda t: 0.2)
    times, pro, anti = chronic.simulate(t_span=(0, 200), dt=0.01)

    print(f"   Steady-state pro-inflammatory: {pro[-1]:.3f}")
    print(f"   Steady-state anti-inflammatory: {anti[-1]:.3f}")
    print(f"   Net inflammatory state: {chronic.get_net_inflammatory_state():.3f}")

    # Modulated organ decay rates
    lambda_b, lambda_h = chronic.get_modulated_decay_rates(pro[-1])
    print(f"   Modulated brain decay rate: {lambda_b:.3f}")
    print(f"   Modulated heart decay rate: {lambda_h:.3f}")

    # Example 3: Cytokine storm
    print("\n3. Testing cytokine storm...")
    storm = CytokineProfiles.cytokine_storm()

    # Severe acute damage
    storm.set_damage_signal(lambda t: 2.0 if t < 5 else 0.5)
    times, pro, anti = storm.simulate(t_span=(0, 50), dt=0.01)

    print(f"   Peak pro-inflammatory: {np.max(pro):.3f}")
    print(f"   Peak anti-inflammatory: {np.max(anti):.3f}")
    print(f"   Pro/Anti ratio at peak: {np.max(pro)/np.max(anti):.2f}")
    print(f"   Time to 50% resolution: {times[np.argmax(pro > 0.5*np.max(pro))]:.1f}")

    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("=" * 70)
    print("✓ BIDIRECTIONAL: Tissue damage ↔ systemic inflammation")
    print("✓ BALANCE: Pro- and anti-inflammatory dynamics")
    print("✓ MODULATION: Inflammation alters organ function")
    print("✓ PROFILES: Acute, chronic, cytokine storm presets")
    print("=" * 70)
