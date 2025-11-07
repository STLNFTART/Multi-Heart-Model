"""Cardiac limit-cycle oscillator based on the Van der Pol model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class VanDerPolOscillator:
    """Simple relaxation oscillator capturing cardiac-like cycles."""

    mu: float = 1.5
    omega: float = 1.0
    damping: float = 0.0

    def derivatives(self, t: float, state: Tuple[float, float], input_force: float = 0.0) -> Tuple[float, float]:
        """Compute derivatives for the Van der Pol oscillator."""

        x, y = state
        dx = y
        dy = self.mu * (1 - x ** 2) * y - (self.omega ** 2) * x - self.damping * y + input_force
        return dx, dy

    def step(self, t: float, state: Tuple[float, float], dt: float, input_force: float = 0.0) -> Tuple[float, float]:
        """Advance the oscillator by one explicit Euler step."""

        dx, dy = self.derivatives(t, state, input_force=input_force)
        x, y = state
        return x + dt * dx, y + dt * dy
