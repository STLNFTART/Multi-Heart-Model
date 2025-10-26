"""Heart–Brain Coupling Model orchestration utilities."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Iterable, List, Tuple

from ..cardiac.van_der_pol import VanDerPolOscillator
from ..neural.fhn import FitzHughNagumo

State = Tuple[float, float, float, float]
HistoryEntry = Tuple[float, Tuple[float, float], Tuple[float, float]]


@dataclass
class CouplingParameters:
    """Bidirectional coupling configuration for the HBCM."""

    neural_to_cardiac_gain: float = 0.4
    cardiac_to_neural_gain: float = 0.2
    neural_delay: float = 0.0
    cardiac_delay: float = 0.0
    neural_bias: float = 0.0
    cardiac_bias: float = 0.0


@dataclass
class HeartBrainCouplingModel:
    """Integrates neural and cardiac oscillators with bidirectional feedback."""

    neural_model: FitzHughNagumo = field(default_factory=FitzHughNagumo)
    cardiac_model: VanDerPolOscillator = field(default_factory=VanDerPolOscillator)
    coupling: CouplingParameters = field(default_factory=CouplingParameters)
    history: Deque[HistoryEntry] = field(default_factory=deque, init=False)

    def reset_history(self) -> None:
        """Clear previously stored states used for delay lookups."""

        self.history.clear()

    def _delayed_state(self, current_time: float, delay: float, component: str, fallback: Tuple[float, float]) -> Tuple[float, float]:
        """Return the state recorded ``delay`` seconds before ``current_time``."""

        if delay <= 0.0 or not self.history:
            return fallback

        target = current_time - delay
        candidate: HistoryEntry | None = None
        for entry in reversed(self.history):
            time, neural_state, cardiac_state = entry
            if time <= target:
                candidate = entry
                break

        if candidate is None:
            candidate = self.history[0]

        _, neural_state, cardiac_state = candidate
        return neural_state if component == "neural" else cardiac_state

    def derivatives(self, t: float, state: State) -> State:
        """Compute state derivatives with feedback coupling applied."""

        neural_state = (state[0], state[1])
        cardiac_state = (state[2], state[3])

        delayed_neural = self._delayed_state(t, self.coupling.cardiac_delay, "neural", neural_state)
        delayed_cardiac = self._delayed_state(t, self.coupling.neural_delay, "cardiac", cardiac_state)

        neural_input = self.coupling.cardiac_to_neural_gain * delayed_cardiac[0] + self.coupling.neural_bias
        cardiac_input = self.coupling.neural_to_cardiac_gain * delayed_neural[0] + self.coupling.cardiac_bias

        dv, dw = self.neural_model.derivatives(t, neural_state, input_drive=neural_input)
        dx, dy = self.cardiac_model.derivatives(t, cardiac_state, input_force=cardiac_input)
        return dv, dw, dx, dy

    def step(self, t: float, state: State, dt: float) -> State:
        """Advance the coupled system by one explicit Euler step."""

        dv, dw, dx, dy = self.derivatives(t, state)
        v, w, x, y = state
        next_state = (v + dt * dv, w + dt * dw, x + dt * dx, y + dt * dy)
        return next_state

    def simulate(
        self,
        initial_state: State,
        t_span: Tuple[float, float],
        dt: float,
    ) -> List[Tuple[float, State]]:
        """Simulate the coupled model using explicit Euler integration."""

        start, stop = t_span
        if stop <= start:
            raise ValueError("t_span must have stop > start")
        if dt <= 0:
            raise ValueError("dt must be positive")

        self.reset_history()

        results: List[Tuple[float, State]] = []
        t = start
        state = initial_state
        self.history.append((t, (state[0], state[1]), (state[2], state[3])))

        while t <= stop:
            results.append((t, state))
            state = self.step(t, state, dt)
            t = round(t + dt, 12)
            self.history.append((t, (state[0], state[1]), (state[2], state[3])))

        return results

    def extract_series(self, trajectory: Iterable[Tuple[float, State]]) -> Tuple[List[float], List[float], List[float]]:
        """Split a trajectory into separate neural and cardiac activation series."""

        times: List[float] = []
        neural_values: List[float] = []
        cardiac_values: List[float] = []
        for time, state in trajectory:
            times.append(time)
            neural_values.append(state[0])
            cardiac_values.append(state[2])
        return times, neural_values, cardiac_values
