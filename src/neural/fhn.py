"""FitzHugh–Nagumo neural oscillator implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class FitzHughNagumo:
    """Canonical two-dimensional neural oscillator.

    Parameters
    ----------
    a, b, c:
        Dimensionless constants controlling excitability, recovery, and time
        scaling respectively. Defaults reproduce a tonic spiking regime.
    stimulus_amplitude:
        Baseline tonic input current applied to the voltage-like variable.
    """

    a: float = 0.7
    b: float = 0.8
    c: float = 3.0
    stimulus_amplitude: float = 0.0

    def derivatives(self, t: float, state: Tuple[float, float], input_drive: float = 0.0) -> Tuple[float, float]:
        """Return time derivatives for the FitzHugh–Nagumo state.

        Parameters
        ----------
        t:
            Simulation time (unused but present for API uniformity).
        state:
            Tuple ``(v, w)`` representing the activator and recovery variables.
        input_drive:
            External modulation applied to the activator ``v``.
        """

        v, w = state
        dv = v - (v ** 3) / 3.0 - w + self.stimulus_amplitude + input_drive
        dw = (v + self.a - self.b * w) / self.c
        return dv, dw

    def step(self, t: float, state: Tuple[float, float], dt: float, input_drive: float = 0.0) -> Tuple[float, float]:
        """Advance the state by a single explicit Euler step."""

        dv, dw = self.derivatives(t, state, input_drive=input_drive)
        v, w = state
        return v + dt * dv, w + dt * dw
