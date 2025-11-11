"""
Primal Logic Processor Core Implementation

Implements hardware-accelerated integral control with exponential memory weighting
based on the mathematical framework: u(t) = -K ∫₀ᵗ Θ(τ) · e(τ) · e^(-λ(t-τ)) dτ

Author: Donte Lightfoot - Lightfoot Technology
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
import time


@dataclass
class ProcessorConfig:
    """Configuration for Primal Logic Processor"""
    num_integral_units: int = 8
    memory_banks: int = 16
    multiply_accumulate_units: int = 32
    floating_point_units: int = 4
    io_channels: int = 64
    safety_cores: int = 2
    processing_latency_us: float = 50.0

    # Control parameters
    K_gain: float = 0.5
    lambda_decay: float = 2.0
    dt: float = 0.01  # 10ms timestep

    # Bounds
    max_control_output: float = 10.0
    min_control_output: float = -10.0


@dataclass
class ControlState:
    """State of the control system"""
    time: float
    velocity: float
    error: float
    integral: float
    control_output: float
    bounded_control: float
    comfort_index: float


class IntegralProcessingUnit:
    """
    Hardware-accelerated Integral Processing Unit (IPU)

    Implements exponential memory weighting for integral control:
    integral(t) = ∫₀ᵗ e(τ) · e^(-λ(t-τ)) dτ
    """

    def __init__(self, lambda_decay: float = 2.0, dt: float = 0.01):
        self.lambda_decay = lambda_decay
        self.dt = dt
        self.integral = 0.0
        self.history = []

    def update(self, error: float) -> float:
        """
        Update integral with exponential memory weighting

        Args:
            error: Current error signal

        Returns:
            Updated integral value
        """
        # Exponential decay of previous integral
        decay_factor = np.exp(-self.lambda_decay * self.dt)
        self.integral = self.integral * decay_factor + error * self.dt

        # Store in history buffer (limited to memory banks)
        self.history.append((time.time(), error, self.integral))
        if len(self.history) > 16:  # memory_banks
            self.history.pop(0)

        return self.integral

    def reset(self):
        """Reset integral state"""
        self.integral = 0.0
        self.history.clear()


class PrimalLogicProcessor:
    """
    Main Primal Logic Processor implementing bounded integral control
    with exponential memory weighting for autonomous vehicle applications.
    """

    def __init__(self, config: Optional[ProcessorConfig] = None):
        self.config = config or ProcessorConfig()

        # Initialize IPUs (parallel processing)
        self.ipus = [
            IntegralProcessingUnit(
                lambda_decay=self.config.lambda_decay,
                dt=self.config.dt
            )
            for _ in range(self.config.num_integral_units)
        ]

        self.current_ipu = 0  # Round-robin scheduling
        self.state_history: List[ControlState] = []

    def compute_control(
        self,
        current_value: float,
        target_value: float,
        timestamp: Optional[float] = None
    ) -> Tuple[float, ControlState]:
        """
        Compute bounded control output using Primal Logic integral control

        Args:
            current_value: Current system state (e.g., velocity)
            target_value: Desired system state
            timestamp: Optional timestamp (uses current time if None)

        Returns:
            Tuple of (bounded_control_output, control_state)
        """
        if timestamp is None:
            timestamp = time.time()

        # Calculate error
        error = current_value - target_value

        # Use round-robin IPU selection for parallel processing
        ipu = self.ipus[self.current_ipu]
        self.current_ipu = (self.current_ipu + 1) % len(self.ipus)

        # Update integral with exponential weighting
        integral = ipu.update(error)

        # Compute control output
        control_output = -self.config.K_gain * integral

        # Apply bounds (hardware enforcement)
        bounded_control = np.clip(
            control_output,
            self.config.min_control_output,
            self.config.max_control_output
        )

        # Compute comfort index (reduced jerk = higher comfort)
        comfort_index = self._compute_comfort_index(bounded_control)

        # Create state record
        state = ControlState(
            time=timestamp,
            velocity=current_value,
            error=error,
            integral=integral,
            control_output=control_output,
            bounded_control=bounded_control,
            comfort_index=comfort_index
        )

        self.state_history.append(state)

        return bounded_control, state

    def _compute_comfort_index(self, control: float) -> float:
        """
        Compute comfort index based on control magnitude
        Lower control magnitude = smoother = higher comfort
        """
        if abs(control) < 5.0:
            return 100.0
        else:
            return max(0.0, 100.0 - abs(control) * 10.0)

    def simulate_emergency_braking(
        self,
        initial_velocity: float = 30.0,
        target_velocity: float = 0.0,
        duration: float = 10.0
    ) -> List[ControlState]:
        """
        Simulate emergency braking scenario

        Args:
            initial_velocity: Starting velocity (m/s)
            target_velocity: Target velocity (m/s)
            duration: Simulation duration (seconds)

        Returns:
            List of control states over time
        """
        self.reset()

        velocity = initial_velocity
        num_steps = int(duration / self.config.dt)
        states = []

        for step in range(num_steps):
            t = step * self.config.dt

            # Compute control
            bounded_control, state = self.compute_control(
                current_value=velocity,
                target_value=target_velocity,
                timestamp=t
            )

            # Update velocity (simple integration)
            velocity += bounded_control * self.config.dt
            velocity = max(0.0, velocity)  # Can't go negative

            states.append(state)

        return states

    def get_hardware_metrics(self) -> dict:
        """Return hardware resource metrics"""
        return {
            'integral_units': self.config.num_integral_units,
            'memory_banks': self.config.memory_banks,
            'multiply_accumulate': self.config.multiply_accumulate_units,
            'floating_point': self.config.floating_point_units,
            'io_channels': self.config.io_channels,
            'safety_cores': self.config.safety_cores,
            'total_area_mm2': 180,
            'power_consumption_w': 25,
            'processing_latency_us': self.config.processing_latency_us
        }

    def reset(self):
        """Reset all processor state"""
        for ipu in self.ipus:
            ipu.reset()
        self.state_history.clear()
        self.current_ipu = 0

    def export_state_csv(self, filename: str):
        """Export state history to CSV format compatible with MotorHandPro"""
        import csv

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['# Primal Logic Processor Output'])
            writer.writerow(['# K=' + str(self.config.K_gain)])
            writer.writerow(['# lambda=' + str(self.config.lambda_decay)])
            writer.writerow(['t', 'velocity', 'error', 'integral', 'control', 'comfort'])

            for state in self.state_history:
                writer.writerow([
                    f'{state.time:.3f}',
                    f'{state.velocity:.6f}',
                    f'{state.error:.6f}',
                    f'{state.integral:.6f}',
                    f'{state.bounded_control:.6f}',
                    f'{state.comfort_index:.2f}'
                ])


if __name__ == '__main__':
    # Example usage
    processor = PrimalLogicProcessor()

    print("Primal Logic Processor - Emergency Braking Simulation")
    print("=" * 60)

    states = processor.simulate_emergency_braking(
        initial_velocity=30.0,
        target_velocity=0.0,
        duration=10.0
    )

    print(f"\nSimulation complete: {len(states)} timesteps")
    print(f"Final velocity: {states[-1].velocity:.2f} m/s")
    print(f"Average comfort index: {np.mean([s.comfort_index for s in states]):.2f}")
    print(f"Max control output: {max([abs(s.bounded_control) for s in states]):.2f}")

    # Export results
    processor.export_state_csv('primal_logic_output.csv')
    print("\nResults exported to primal_logic_output.csv")
