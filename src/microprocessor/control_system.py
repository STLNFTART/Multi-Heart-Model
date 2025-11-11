"""
Control System Components

Additional control system utilities for Primal Logic Processor integration.

Author: Donte Lightfoot - Lightfoot Technology
"""

import numpy as np
from typing import Callable, List


class ExponentialMemoryWeighting:
    """
    Exponential memory weighting function: Θ(τ) · e^(-λ(t-τ))

    Implements time-decaying weight for historical error values,
    giving more importance to recent errors while maintaining
    bounded memory of past states.
    """

    def __init__(self, lambda_decay: float = 2.0):
        """
        Args:
            lambda_decay: Decay rate (higher = faster decay)
        """
        self.lambda_decay = lambda_decay

    def weight(self, time_delta: float) -> float:
        """
        Compute weight for error at time_delta in the past

        Args:
            time_delta: Time difference (t - τ)

        Returns:
            Weight value
        """
        return np.exp(-self.lambda_decay * time_delta)

    def weighted_integral(
        self,
        errors: List[float],
        times: List[float],
        current_time: float
    ) -> float:
        """
        Compute weighted integral: ∫ e(τ) · e^(-λ(t-τ)) dτ

        Args:
            errors: List of error values
            times: List of timestamps
            current_time: Current time

        Returns:
            Weighted integral value
        """
        if len(errors) != len(times):
            raise ValueError("errors and times must have same length")

        integral = 0.0
        for i in range(len(errors) - 1):
            dt = times[i + 1] - times[i]
            time_delta = current_time - times[i]
            weight = self.weight(time_delta)

            # Trapezoidal integration with weighting
            avg_error = (errors[i] + errors[i + 1]) / 2.0
            integral += weight * avg_error * dt

        return integral


class IntegralControlSystem:
    """
    Complete integral control system with exponential memory weighting

    Implements: u(t) = -K ∫₀ᵗ Θ(τ) · e(τ) · e^(-λ(t-τ)) dτ
    """

    def __init__(
        self,
        K_gain: float = 0.5,
        lambda_decay: float = 2.0,
        control_bounds: tuple = (-10.0, 10.0)
    ):
        """
        Args:
            K_gain: Control gain
            lambda_decay: Memory decay rate
            control_bounds: (min, max) control output bounds
        """
        self.K_gain = K_gain
        self.memory = ExponentialMemoryWeighting(lambda_decay)
        self.control_bounds = control_bounds

        self.error_history = []
        self.time_history = []

    def compute_control(
        self,
        error: float,
        time: float
    ) -> float:
        """
        Compute control output for current error

        Args:
            error: Current error signal
            time: Current timestamp

        Returns:
            Bounded control output
        """
        # Store error
        self.error_history.append(error)
        self.time_history.append(time)

        # Compute weighted integral
        if len(self.error_history) > 1:
            integral = self.memory.weighted_integral(
                self.error_history,
                self.time_history,
                time
            )
        else:
            integral = 0.0

        # Apply control law
        control = -self.K_gain * integral

        # Apply bounds
        control = np.clip(control, *self.control_bounds)

        return control

    def reset(self):
        """Reset controller state"""
        self.error_history.clear()
        self.time_history.clear()


def compute_jerk_reduction(
    traditional_control: List[float],
    primal_control: List[float],
    dt: float
) -> float:
    """
    Compute jerk reduction percentage

    Jerk = d³x/dt³ ≈ Δ(acceleration) / dt

    Args:
        traditional_control: Traditional control signal
        primal_control: Primal Logic control signal
        dt: Timestep

    Returns:
        Percentage reduction in jerk
    """
    def compute_jerk(control_signal):
        # Compute acceleration (control is proportional to acceleration)
        accel = np.array(control_signal)

        # Compute jerk (derivative of acceleration)
        jerk = np.diff(accel) / dt

        # Return RMS jerk
        return np.sqrt(np.mean(jerk ** 2))

    trad_jerk = compute_jerk(traditional_control)
    primal_jerk = compute_jerk(primal_control)

    if trad_jerk == 0:
        return 0.0

    reduction = (trad_jerk - primal_jerk) / trad_jerk * 100.0
    return reduction


def compute_comfort_metrics(control_signals: List[float], dt: float) -> dict:
    """
    Compute comprehensive comfort metrics

    Args:
        control_signals: List of control values
        dt: Timestep

    Returns:
        Dictionary of comfort metrics
    """
    control_array = np.array(control_signals)

    # Jerk (rate of change of acceleration)
    accel_diff = np.diff(control_array)
    jerk = accel_diff / dt
    rms_jerk = np.sqrt(np.mean(jerk ** 2))

    # Smoothness (inverse of variance)
    variance = np.var(control_array)
    smoothness = 1.0 / (1.0 + variance)

    # Peak control magnitude
    peak_control = np.max(np.abs(control_array))

    # Comfort index (0-100)
    comfort_index = 100.0 * smoothness * (1.0 - min(peak_control / 10.0, 1.0))

    return {
        'rms_jerk': rms_jerk,
        'smoothness': smoothness,
        'peak_control': peak_control,
        'comfort_index': comfort_index
    }
