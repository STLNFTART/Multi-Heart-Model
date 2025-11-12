"""
Hepatocyte Population Model

Cell population dynamics with viability, damage, and death states.
Implements birth, death, and damage/repair processes.

Mathematical formulation:
    dN_viable/dt = α·N_viable·(1 - N_total/N_max) - μ(tox)·N_viable - δ·N_viable
    dN_damaged/dt = δ·N_viable + ρ·N_damaged - (μ_d(tox) + γ)·N_damaged
    dN_dead/dt = μ(tox)·N_viable + μ_d(tox)·N_damaged

where:
    N_viable: Healthy hepatocytes
    N_damaged: Damaged but recoverable cells
    N_dead: Necrotic cells
    α: Growth/proliferation rate
    μ(tox): Toxicity-dependent death rate
    δ: Damage rate
    ρ: Repair rate
    γ: Death rate for damaged cells
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, Callable


@dataclass
class HepatocyteParameters:
    """Parameters for hepatocyte population"""
    N_max: float = 1000.0              # Maximum hepatocyte capacity
    alpha_growth: float = 0.01         # Proliferation rate
    delta_damage: float = 0.02         # Damage rate (baseline)
    rho_repair: float = 0.05           # Repair rate for damaged cells
    gamma_death_damaged: float = 0.01  # Death rate for damaged cells
    mu_death_baseline: float = 0.005   # Baseline death rate

    # Toxicity sensitivity
    toxicity_sensitivity: float = 0.1

    # Metabolic capacity
    metabolic_capacity_per_cell: float = 0.1  # Arbitrary units


class HepatocytePopulation:
    """
    Hepatocyte population with viability states.

    State variables:
    - N_viable: Healthy functional hepatocytes
    - N_damaged: Damaged cells (reduced function)
    - N_dead: Necrotic cells
    - ATP_level: Cellular energy state
    - GSH_level: Glutathione (antioxidant capacity)

    Usage:
        >>> hep = HepatocytePopulation()
        >>> hep.set_toxicity_function(lambda t: drug_concentration * 0.01)
        >>> times, states = hep.simulate(t_span=(0, 100), dt=0.1)
    """

    def __init__(self, params: Optional[HepatocyteParameters] = None):
        self.params = params or HepatocyteParameters()

        # State: [N_viable, N_damaged, N_dead, ATP, GSH]
        self.state = np.array([
            self.params.N_max * 0.9,  # Start with 90% viable
            self.params.N_max * 0.1,  # 10% damaged
            0.0,                       # No dead cells initially
            1.0,                       # Normalized ATP level
            1.0                        # Normalized GSH level
        ])

        # Toxicity function (default: none)
        self._toxicity_func = lambda t: 0.0

        # Oxidative stress function
        self._oxidative_stress_func = lambda t: 0.0

    def set_toxicity_function(self, func: Callable[[float], float]):
        """Set time-varying toxicity signal (e.g., from drug)"""
        self._toxicity_func = func

    def set_oxidative_stress_function(self, func: Callable[[float], float]):
        """Set oxidative stress signal (ROS, etc.)"""
        self._oxidative_stress_func = func

    def derivatives(self, state: np.ndarray, t: float) -> np.ndarray:
        """
        Compute time derivatives.

        Args:
            state: [N_viable, N_damaged, N_dead, ATP, GSH]
            t: Current time

        Returns:
            derivatives
        """
        N_viable, N_damaged, N_dead, ATP, GSH = state

        N_total = N_viable + N_damaged
        toxicity = self._toxicity_func(t)
        oxidative_stress = self._oxidative_stress_func(t)

        # Toxicity-dependent death rates
        mu_viable = self.params.mu_death_baseline + \
                    self.params.toxicity_sensitivity * toxicity * (1.0 / (GSH + 0.1))
        mu_damaged = 2.0 * mu_viable  # Damaged cells more susceptible

        # Proliferation (density-dependent)
        proliferation = self.params.alpha_growth * N_viable * (
            1 - N_total / self.params.N_max
        )

        # State transitions
        dN_viable = (
            proliferation
            - self.params.delta_damage * N_viable
            - mu_viable * N_viable
        )

        dN_damaged = (
            self.params.delta_damage * N_viable
            + self.params.rho_repair * N_damaged * (ATP / (ATP + 0.5))  # Repair needs ATP
            - mu_damaged * N_damaged
            - self.params.gamma_death_damaged * N_damaged
        )

        dN_dead = (
            mu_viable * N_viable
            + mu_damaged * N_damaged
            + self.params.gamma_death_damaged * N_damaged
        )

        # ATP dynamics (production - consumption - toxicity)
        ATP_production = 1.0 * (N_viable / self.params.N_max)  # Normalized
        ATP_consumption = 0.5 + 0.3 * (self.params.rho_repair * N_damaged / self.params.N_max)
        ATP_toxicity = 0.2 * toxicity

        dATP = ATP_production - ATP_consumption - ATP_toxicity - 0.3 * ATP

        # GSH dynamics (synthesis - consumption by ROS)
        GSH_synthesis = 0.5 * (N_viable / self.params.N_max)
        GSH_consumption = oxidative_stress + 0.5 * toxicity

        dGSH = GSH_synthesis - GSH_consumption - 0.2 * GSH

        return np.array([dN_viable, dN_damaged, dN_dead, dATP, dGSH])

    def integrate_step(self, dt: float, t: float) -> np.ndarray:
        """Update state by one timestep using RK4"""
        k1 = self.derivatives(self.state, t)
        k2 = self.derivatives(self.state + 0.5*dt*k1, t + 0.5*dt)
        k3 = self.derivatives(self.state + 0.5*dt*k2, t + 0.5*dt)
        k4 = self.derivatives(self.state + dt*k3, t + dt)

        self.state += (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

        # Ensure non-negative
        self.state = np.maximum(self.state, 0.0)

        # Cap ATP and GSH at physiological maximum
        self.state[3] = min(self.state[3], 2.0)
        self.state[4] = min(self.state[4], 2.0)

        return self.state

    def simulate(
        self,
        t_span: Tuple[float, float],
        dt: float = 0.1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate hepatocyte population dynamics.

        Args:
            t_span: (start_time, end_time)
            dt: Timestep

        Returns:
            (times, states) where states has shape (N, 5)
        """
        t_start, t_end = t_span
        n_steps = int((t_end - t_start) / dt)

        times = np.linspace(t_start, t_end, n_steps)
        states = np.zeros((n_steps, 5))
        states[0] = self.state

        for i in range(1, n_steps):
            t = times[i]
            states[i] = self.integrate_step(dt, t)

        return times, states

    def get_viability_fraction(self) -> float:
        """Return fraction of viable cells"""
        N_total = self.state[0] + self.state[1] + self.state[2]
        if N_total > 0:
            return self.state[0] / N_total
        return 0.0

    def get_metabolic_capacity(self) -> float:
        """Return total metabolic capacity (viable + partial damaged)"""
        N_viable, N_damaged = self.state[0], self.state[1]
        ATP = self.state[3]

        capacity = (
            N_viable * self.params.metabolic_capacity_per_cell +
            N_damaged * self.params.metabolic_capacity_per_cell * 0.5 * (ATP / (ATP + 0.5))
        )

        return capacity

    def get_biomarkers(self) -> dict:
        """
        Return hepatotoxicity biomarkers.

        ALT, AST: Leakage from damaged/dying cells
        LDH: Cell death marker
        Albumin: Synthetic function
        """
        N_viable, N_damaged, N_dead, ATP, GSH = self.state

        # ALT/AST: proportional to damaged + dying cells
        ALT = N_damaged * 0.5 + N_dead * 1.0
        AST = N_damaged * 0.3 + N_dead * 0.8

        # LDH: cell death
        LDH = N_dead * 1.5

        # Albumin: synthetic function (requires viable cells + ATP)
        Albumin = N_viable * (ATP / (ATP + 0.5))

        return {
            'ALT': ALT,
            'AST': AST,
            'LDH': LDH,
            'Albumin': Albumin,
            'GSH': GSH,
            'ATP': ATP,
            'Viability': self.get_viability_fraction()
        }

    def reset(self):
        """Reset to initial healthy state"""
        self.state = np.array([
            self.params.N_max * 0.9,
            self.params.N_max * 0.1,
            0.0,
            1.0,
            1.0
        ])


if __name__ == "__main__":
    print("=" * 70)
    print("HEPATOCYTE POPULATION MODEL")
    print("=" * 70)

    # Example 1: Baseline homeostasis
    print("\n1. Testing baseline homeostasis...")
    hep = HepatocytePopulation()
    times, states = hep.simulate(t_span=(0, 100), dt=0.1)

    print(f"   Initial viability: {states[0,0]:.1f} cells")
    print(f"   Final viability: {states[-1,0]:.1f} cells")
    print(f"   Viability fraction: {hep.get_viability_fraction():.2%}")
    print(f"   Metabolic capacity: {hep.get_metabolic_capacity():.2f}")

    # Example 2: Acute toxicity
    print("\n2. Testing acute hepatotoxicity...")
    hep.reset()

    # Toxic insult at t=20
    def acute_toxicity(t):
        if 20 < t < 40:
            return 0.5
        return 0.0

    hep.set_toxicity_function(acute_toxicity)
    hep.set_oxidative_stress_function(lambda t: 0.3 if 20 < t < 40 else 0.0)

    times, states = hep.simulate(t_span=(0, 100), dt=0.1)

    print(f"   Pre-toxicity viable cells: {states[200,0]:.1f}")
    print(f"   During toxicity viable cells: {states[300,0]:.1f}")
    print(f"   Post-toxicity viable cells: {states[-1,0]:.1f}")
    print(f"   Dead cells accumulated: {states[-1,2]:.1f}")

    biomarkers = hep.get_biomarkers()
    print(f"\n   Biomarkers at t=100:")
    print(f"     ALT: {biomarkers['ALT']:.2f}")
    print(f"     AST: {biomarkers['AST']:.2f}")
    print(f"     LDH: {biomarkers['LDH']:.2f}")
    print(f"     Albumin: {biomarkers['Albumin']:.2f}")
    print(f"     ATP: {biomarkers['ATP']:.3f}")
    print(f"     GSH: {biomarkers['GSH']:.3f}")

    print("\n" + "=" * 70)
    print("KEY FEATURES:")
    print("=" * 70)
    print("✓ POPULATION: Viable, damaged, dead cell states")
    print("✓ METABOLISM: ATP and GSH tracking")
    print("✓ BIOMARKERS: ALT, AST, LDH, Albumin")
    print("✓ TOXICITY: Dose-dependent cell death")
    print("=" * 70)
