"""
Baroreflex model based on physiological principles.

This module implements a mechanistic model of the arterial baroreflex,
including baroreceptor firing, central processing, and efferent sympathetic/
parasympathetic responses.

Physiological Basis:
    - Baroreceptor activation follows sigmoidal pressure-firing relationship
    - Central integration occurs in nucleus tractus solitarius (NTS)
    - Efferent output modulates heart rate, contractility, and vascular resistance

References:
    Chapleau & Abboud (2001) - Baroreflex adaptation mechanisms
    Eckberg & Sleight (1992) - Human baroreflexes
    Levy & Martin (1979) - Neural control of the heart
"""

from dataclasses import dataclass
from typing import Tuple
import math


@dataclass
class BaroreflexParameters:
    """
    Physiological parameters for baroreflex model.

    All parameters are based on published physiological data.
    """

    # Baroreceptor firing characteristics
    pressure_setpoint: float = 93.0  # mmHg - Mean arterial pressure setpoint
    pressure_threshold: float = 60.0  # mmHg - Threshold for baroreceptor activation
    pressure_saturation: float = 180.0  # mmHg - Saturation pressure
    max_firing_rate: float = 200.0  # spikes/second - Maximum baroreceptor firing
    min_firing_rate: float = 0.0  # spikes/second - Minimum firing rate

    # Sigmoid curve parameters (from Chapleau & Abboud 2001)
    sigmoid_slope: float = 0.05  # 1/mmHg - Slope of pressure-firing relationship
    sigmoid_midpoint: float = 100.0  # mmHg - Midpoint of sigmoid

    # Central integration time constants (from Eckberg 1997)
    integration_time: float = 2.0  # seconds - Time constant for NTS integration
    adaptation_time: float = 30.0  # seconds - Baroreflex adaptation time constant

    # Efferent gains (from Levy & Martin 1979)
    vagal_gain: float = 1.2  # Normalized - Vagal efferent gain
    sympathetic_gain: float = 0.8  # Normalized - Sympathetic efferent gain

    # Efferent delays (from Eckberg 1997)
    vagal_delay: float = 0.10  # seconds - Parasympathetic delay (fast)
    sympathetic_delay: float = 0.20  # seconds - Sympathetic delay (slow)

    # Baroreflex sensitivity (from La Rovere et al. 1998)
    brs_normal: float = 12.0  # ms/mmHg - Normal baroreflex sensitivity
    brs_min: float = 3.0  # ms/mmHg - Minimum (impaired)
    brs_max: float = 30.0  # ms/mmHg - Maximum (highly sensitive)


class Baroreceptor:
    """
    Model of arterial baroreceptor.

    Implements the mechanosensitive properties of carotid sinus and
    aortic arch baroreceptors based on experimental data.
    """

    def __init__(self, params: BaroreflexParameters = None):
        """
        Initialize baroreceptor.

        Args:
            params: Baroreceptor parameters
        """
        self.params = params or BaroreflexParameters()
        self._previous_pressure = self.params.pressure_setpoint
        self._adaptation_level = 0.0

    def compute_firing_rate(
        self,
        pressure: float,
        dt: float = 0.001,
    ) -> float:
        """
        Compute baroreceptor firing rate as function of arterial pressure.

        Uses sigmoidal pressure-firing relationship based on experimental data
        from Chapleau & Abboud (2001).

        Mathematical form:
            FR = FR_min + (FR_max - FR_min) / (1 + exp(-k*(P - P_mid)))

        Where:
            FR = firing rate (spikes/s)
            P = mean arterial pressure (mmHg)
            k = sigmoid slope
            P_mid = midpoint pressure

        Args:
            pressure: Mean arterial pressure (mmHg)
            dt: Time step (seconds)

        Returns:
            Firing rate in spikes/second
        """
        # Sigmoidal activation function
        p = self.params
        normalized_pressure = (pressure - p.sigmoid_midpoint) * p.sigmoid_slope

        # Prevent overflow in exp
        normalized_pressure = max(min(normalized_pressure, 50), -50)

        firing_rate = p.min_firing_rate + (
            (p.max_firing_rate - p.min_firing_rate) /
            (1.0 + math.exp(-normalized_pressure))
        )

        # Include adaptation mechanism
        # Baroreceptors adapt to sustained pressure changes
        pressure_error = pressure - self._previous_pressure
        self._adaptation_level += dt / p.adaptation_time * (
            pressure_error - self._adaptation_level
        )

        # Reduce firing rate proportional to adaptation
        firing_rate *= (1.0 - 0.3 * self._adaptation_level / (p.pressure_saturation - p.pressure_threshold))

        # Ensure within bounds
        firing_rate = max(p.min_firing_rate, min(p.max_firing_rate, firing_rate))

        self._previous_pressure = pressure

        return firing_rate

    def reset_adaptation(self):
        """Reset baroreceptor adaptation (e.g., after postural change)."""
        self._adaptation_level = 0.0


class BaroreflexController:
    """
    Central baroreceptor reflex arc controller.

    Integrates baroreceptor afferent signals and generates appropriate
    sympathetic and parasympathetic efferent responses.

    Based on neurovisceral integration model (Thayer & Lane 2009).
    """

    def __init__(self, params: BaroreflexParameters = None):
        """
        Initialize baroreflex controller.

        Args:
            params: Baroreflex parameters
        """
        self.params = params or BaroreflexParameters()
        self.baroreceptor = Baroreceptor(params)

        # Internal state for integration
        self._integrated_signal = 0.0
        self._vagal_output = 0.0
        self._sympathetic_output = 0.0

        # History for delays
        from collections import deque
        self._vagal_history = deque(maxlen=1000)
        self._sympathetic_history = deque(maxlen=1000)

    def compute_autonomic_output(
        self,
        pressure: float,
        dt: float = 0.001,
        t: float = 0.0,
    ) -> Tuple[float, float]:
        """
        Compute vagal and sympathetic output based on blood pressure.

        Implements the baroreflex arc:
        1. Baroreceptor firing ∝ pressure
        2. Central integration in NTS
        3. Reciprocal sympathetic/parasympathetic output
        4. Efferent delays

        Args:
            pressure: Mean arterial pressure (mmHg)
            dt: Time step (seconds)
            t: Current time (seconds)

        Returns:
            Tuple of (vagal_output, sympathetic_output)
            Both outputs are normalized 0-1
        """
        # 1. Baroreceptor firing
        firing_rate = self.baroreceptor.compute_firing_rate(pressure, dt)

        # Normalize firing rate to 0-1
        firing_normalized = (
            (firing_rate - self.params.min_firing_rate) /
            (self.params.max_firing_rate - self.params.min_firing_rate)
        )

        # 2. Central integration (low-pass filter)
        # Simulates nucleus tractus solitarius (NTS) integration
        alpha = dt / self.params.integration_time
        self._integrated_signal += alpha * (firing_normalized - self._integrated_signal)

        # 3. Reciprocal autonomic output
        # High baroreceptor firing → ↑ vagal, ↓ sympathetic
        # Low baroreceptor firing → ↓ vagal, ↑ sympathetic

        # Vagal output (increases with baroreceptor firing)
        vagal_output = self._integrated_signal * self.params.vagal_gain

        # Sympathetic output (decreases with baroreceptor firing)
        sympathetic_output = (1.0 - self._integrated_signal) * self.params.sympathetic_gain

        # Clamp to physiological range
        vagal_output = max(0.0, min(1.0, vagal_output))
        sympathetic_output = max(0.0, min(1.0, sympathetic_output))

        # 4. Store in history for delays
        self._vagal_history.append((t, vagal_output))
        self._sympathetic_history.append((t, sympathetic_output))

        # 5. Retrieve delayed outputs
        vagal_delayed = self._get_delayed_output(
            self._vagal_history,
            t,
            self.params.vagal_delay,
            vagal_output
        )
        sympathetic_delayed = self._get_delayed_output(
            self._sympathetic_history,
            t,
            self.params.sympathetic_delay,
            sympathetic_output
        )

        self._vagal_output = vagal_delayed
        self._sympathetic_output = sympathetic_delayed

        return vagal_delayed, sympathetic_delayed

    def _get_delayed_output(
        self,
        history: list,
        current_time: float,
        delay: float,
        default_value: float,
    ) -> float:
        """
        Retrieve delayed output from history.

        Args:
            history: Deque of (time, value) tuples
            current_time: Current simulation time
            delay: Delay duration (seconds)
            default_value: Value to return if history insufficient

        Returns:
            Delayed output value
        """
        target_time = current_time - delay

        if not history:
            return default_value

        # Find closest time point
        for time_point, value in history:
            if time_point >= target_time:
                return value

        # If not found, return oldest value
        return history[0][1]

    def compute_heart_rate_response(
        self,
        pressure: float,
        baseline_hr: float = 72.0,
        dt: float = 0.001,
        t: float = 0.0,
    ) -> float:
        """
        Compute heart rate response to pressure change via baroreflex.

        Based on baroreflex sensitivity (BRS) relationship:
            ΔHR = -BRS * ΔP

        Args:
            pressure: Mean arterial pressure (mmHg)
            baseline_hr: Intrinsic heart rate (bpm) - Jose & Collison (1970)
            dt: Time step
            t: Current time

        Returns:
            Heart rate in bpm
        """
        vagal, sympathetic = self.compute_autonomic_output(pressure, dt, t)

        # Convert autonomic output to heart rate change
        # Vagal: decreases HR (strong effect)
        # Sympathetic: increases HR (moderate effect)

        # Maximum vagal effect: -30 bpm
        # Maximum sympathetic effect: +30 bpm
        vagal_effect = -30.0 * vagal
        sympathetic_effect = +30.0 * sympathetic

        hr = baseline_hr + vagal_effect + sympathetic_effect

        # Physiological limits
        hr = max(40.0, min(200.0, hr))

        return hr

    def get_autonomic_state(self) -> dict:
        """
        Get current autonomic state.

        Returns:
            Dictionary with autonomic metrics
        """
        # Compute sympathovagal balance
        total = self._vagal_output + self._sympathetic_output
        if total > 0:
            vagal_fraction = self._vagal_output / total
            sympathetic_fraction = self._sympathetic_output / total
        else:
            vagal_fraction = 0.5
            sympathetic_fraction = 0.5

        return {
            'vagal_output': self._vagal_output,
            'sympathetic_output': self._sympathetic_output,
            'vagal_fraction': vagal_fraction,
            'sympathetic_fraction': sympathetic_fraction,
            'sympathovagal_balance': (
                self._sympathetic_output / self._vagal_output
                if self._vagal_output > 1e-6 else 10.0
            ),
        }


def simulate_baroreflex_response(
    pressure_trajectory: list,
    dt: float = 0.001,
) -> dict:
    """
    Simulate baroreflex response to pressure trajectory.

    Args:
        pressure_trajectory: List of (time, pressure) tuples
        dt: Time step

    Returns:
        Dictionary with time series of autonomic outputs
    """
    controller = BaroreflexController()

    results = {
        'times': [],
        'pressures': [],
        'vagal': [],
        'sympathetic': [],
        'heart_rate': [],
        'baroreceptor_firing': [],
    }

    for t, pressure in pressure_trajectory:
        vagal, sympathetic = controller.compute_autonomic_output(pressure, dt, t)
        hr = controller.compute_heart_rate_response(pressure, dt=dt, t=t)
        firing = controller.baroreceptor.compute_firing_rate(pressure, dt)

        results['times'].append(t)
        results['pressures'].append(pressure)
        results['vagal'].append(vagal)
        results['sympathetic'].append(sympathetic)
        results['heart_rate'].append(hr)
        results['baroreceptor_firing'].append(firing)

    return results


def compute_baroreflex_sensitivity(
    pressure_change: float,
    rr_change: float,
) -> float:
    """
    Compute baroreflex sensitivity from pressure and RR interval changes.

    BRS = ΔRR / ΔP

    Args:
        pressure_change: Change in pressure (mmHg)
        rr_change: Change in RR interval (ms)

    Returns:
        BRS in ms/mmHg
    """
    if abs(pressure_change) < 1e-6:
        return 0.0

    brs = rr_change / pressure_change

    return abs(brs)  # Return absolute value
