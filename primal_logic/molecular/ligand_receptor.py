"""
Ligand-Receptor Binding Dynamics

Molecular-scale drug-receptor interactions with macro-scale feedback.
Implements cellular-level biochemical dynamics.

Mathematical formulation:
    Ṙ(t) = k_on·L(t)·(R_T - R(t)) - k_off·R(t) + γ·F(t)

where:
    R(t): Receptor occupancy (bound receptors)
    L(t): Ligand concentration (drug, hormone, neurotransmitter)
    R_T: Total receptor pool
    k_on: Association rate constant (M⁻¹s⁻¹)
    k_off: Dissociation rate constant (s⁻¹)
    F(t): Macro-scale feedback (stress hormones, cytokines)
    γ: Feedback coupling strength
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Callable, Tuple, Optional


@dataclass
class LigandReceptorParameters:
    """Parameters for ligand-receptor binding"""
    k_on: float = 1.0              # Association rate (M⁻¹s⁻¹)
    k_off: float = 0.1             # Dissociation rate (s⁻¹)
    R_total: float = 100.0         # Total receptor pool
    gamma_feedback: float = 0.05   # Feedback coupling strength

    @property
    def K_d(self) -> float:
        """Dissociation constant (equilibrium)"""
        return self.k_off / self.k_on

    @property
    def occupancy_at_Kd(self) -> float:
        """Receptor occupancy when L = K_d"""
        return 0.5  # 50% occupancy at equilibrium


class LigandReceptor:
    """
    Ligand-receptor binding with macro-scale feedback.

    Usage:
        >>> lr = LigandReceptor()
        >>> lr.set_ligand_function(lambda t: 10.0 * np.exp(-0.5*t))
        >>> times, occupancy = lr.simulate(t_span=(0, 20), dt=0.01)
    """

    def __init__(self, params: Optional[LigandReceptorParameters] = None):
        self.params = params or LigandReceptorParameters()
        self.state = 0.0  # Initial receptor occupancy

        # Default ligand function (constant)
        self._ligand_func = lambda t: 0.0

        # Default feedback function (none)
        self._feedback_func = lambda t: 0.0

    def set_ligand_function(self, func: Callable[[float], float]):
        """Set time-varying ligand concentration"""
        self._ligand_func = func

    def set_feedback_function(self, func: Callable[[float], float]):
        """Set macro-scale feedback (e.g., from stress response)"""
        self._feedback_func = func

    def derivatives(self, R: float, t: float) -> float:
        """
        Compute dR/dt.

        Args:
            R: Current receptor occupancy
            t: Current time

        Returns:
            dR/dt
        """
        L = self._ligand_func(t)
        F = self._feedback_func(t)

        # Binding dynamics
        binding_on = self.params.k_on * L * (self.params.R_total - R)
        binding_off = self.params.k_off * R
        feedback_term = self.params.gamma_feedback * F

        dR = binding_on - binding_off + feedback_term

        return dR

    def integrate_step(self, dt: float, t: float) -> float:
        """Update state by one timestep using RK4"""
        R = self.state

        k1 = self.derivatives(R, t)
        k2 = self.derivatives(R + 0.5*dt*k1, t + 0.5*dt)
        k3 = self.derivatives(R + 0.5*dt*k2, t + 0.5*dt)
        k4 = self.derivatives(R + dt*k3, t + dt)

        self.state += (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

        # Ensure physical bounds
        self.state = np.clip(self.state, 0.0, self.params.R_total)

        return self.state

    def simulate(
        self,
        t_span: Tuple[float, float],
        dt: float = 0.01,
        initial_occupancy: float = 0.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate ligand-receptor dynamics.

        Args:
            t_span: (start_time, end_time)
            dt: Timestep
            initial_occupancy: Initial receptor occupancy

        Returns:
            (times, occupancy)
        """
        self.state = initial_occupancy

        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt)

        times = np.linspace(t_start, t_end, n_steps)
        occupancy = np.zeros(n_steps)
        occupancy[0] = self.state

        for i in range(1, n_steps):
            t = times[i]
            occupancy[i] = self.integrate_step(dt, t)

        return times, occupancy

    def get_fractional_occupancy(self) -> float:
        """Return fractional occupancy (R/R_total)"""
        return self.state / self.params.R_total

    def reset(self, initial_occupancy: float = 0.0):
        """Reset to initial state"""
        self.state = initial_occupancy


# ==============================================================================
# DRUG-SPECIFIC RECEPTOR MODELS
# ==============================================================================

class DrugReceptorBinding:
    """
    Common drug-receptor binding scenarios.
    """

    @staticmethod
    def hERG_channel_block(drug_concentration: float) -> LigandReceptor:
        """
        hERG potassium channel blocking (cardiotoxicity).

        Typical drugs: dofetilide, sotalol, cisapride
        """
        params = LigandReceptorParameters(
            k_on=0.5,      # Fast association
            k_off=0.05,    # Slow dissociation (tight binding)
            R_total=100.0,
            gamma_feedback=0.0  # No feedback for ion channels
        )
        return LigandReceptor(params)

    @staticmethod
    def opioid_receptor(drug_concentration: float) -> LigandReceptor:
        """
        Opioid μ-receptor binding.

        Typical drugs: morphine, fentanyl
        """
        params = LigandReceptorParameters(
            k_on=2.0,       # Moderate association
            k_off=0.2,      # Moderate dissociation
            R_total=50.0,   # Lower receptor density
            gamma_feedback=0.1  # Feedback from stress response
        )
        return LigandReceptor(params)

    @staticmethod
    def beta_adrenergic(drug_concentration: float) -> LigandReceptor:
        """
        β-adrenergic receptor (cardiac).

        Typical drugs: propranolol, metoprolol
        """
        params = LigandReceptorParameters(
            k_on=1.5,
            k_off=0.3,
            R_total=80.0,
            gamma_feedback=0.2  # Strong autonomic feedback
        )
        return LigandReceptor(params)


if __name__ == "__main__":
    print("=" * 70)
    print("LIGAND-RECEPTOR BINDING DYNAMICS")
    print("=" * 70)

    # Example 1: Exponential decay drug concentration
    print("\n1. Testing exponential decay drug input...")
    lr = LigandReceptor()
    lr.set_ligand_function(lambda t: 10.0 * np.exp(-0.5 * t))

    times, occupancy = lr.simulate(t_span=(0, 20), dt=0.01)

    print(f"   Initial occupancy: {occupancy[0]:.2f}")
    print(f"   Peak occupancy: {np.max(occupancy):.2f}")
    print(f"   Final occupancy: {occupancy[-1]:.2f}")
    print(f"   Fractional occupancy (peak): {np.max(occupancy)/lr.params.R_total:.2%}")

    # Example 2: Pulsatile ligand (periodic dosing)
    print("\n2. Testing pulsatile drug dosing...")
    lr.reset()

    def pulsatile_ligand(t):
        """Pulse every 5 time units"""
        if t % 5.0 < 0.5:
            return 20.0
        return 0.0

    lr.set_ligand_function(pulsatile_ligand)
    times, occupancy = lr.simulate(t_span=(0, 30), dt=0.01)

    print(f"   Peak occupancy: {np.max(occupancy):.2f}")
    print(f"   Trough occupancy: {np.min(occupancy[100:]):.2f}")  # After first pulse
    print(f"   K_d = {lr.params.K_d:.2f} (dissociation constant)")

    # Example 3: hERG channel block (cardiotoxicity)
    print("\n3. Testing hERG channel blocking...")
    herg = DrugReceptorBinding.hERG_channel_block(drug_concentration=5.0)
    herg.set_ligand_function(lambda t: 5.0)  # Constant drug exposure

    times, occupancy = herg.simulate(t_span=(0, 50), dt=0.01)

    print(f"   Equilibrium occupancy: {occupancy[-1]:.2f}")
    print(f"   Fractional block: {occupancy[-1]/herg.params.R_total:.2%}")
    print(f"   Time to 90% equilibrium: {times[np.argmax(occupancy > 0.9*occupancy[-1])]:.2f}")

    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("=" * 70)
    print("✓ MECHANISTIC: Law of mass action binding")
    print("✓ FEEDBACK: Macro-scale modulation of binding")
    print("✓ DRUG-SPECIFIC: Pre-configured receptor types")
    print("✓ BOUNDED: Physical constraints enforced")
    print("=" * 70)
