"""
MotorHandPro Integration Bridge

Connects Primal Logic Processor integral control with MotorHandPro's
QUANT system for robotic hand motor control.

Author: Donte Lightfoot - Lightfoot Technology
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
import subprocess
import csv
import os


@dataclass
class QuantParameters:
    """
    MotorHandPro QUANT system parameters
    Based on quant_full.h constants
    """
    PLANCK_SCALE: float = 23.098341716530
    PLANCK_D: float = 149.9992314000
    PLANCK_I3: float = 6.4939394023
    KERNEL_MU: float = 0.169050000000
    DONTE_CONSTANT: float = 149.9992314000

    # Computed values
    D: float = 149.9992314000
    I3: float = 6.4939394023
    S: float = 23.098341716530  # D/I3
    xFixed: float = 149.9992314000

    def throttle_from_fixed(self, x_fixed: float) -> int:
        """
        Convert fixed-point value to throttle (0-255)
        Implements QUANT::throttleFromFixed()
        """
        t = np.clip((x_fixed / 150.0) * 255.0, 0.0, 255.0)
        return int(t + 0.5)


@dataclass
class MotorFeedback:
    """Feedback from motor system"""
    psi: float  # State variable from MotorHandPro
    gamma: float  # Control variable
    Ec: float  # Control energy
    timestamp: float


class QuantInterface:
    """
    Interface to MotorHandPro QUANT system

    Provides methods to:
    - Convert control signals to QUANT throttle values
    - Parse MotorHandPro CSV feedback
    - Compute QUANT parameters
    """

    def __init__(self):
        self.params = QuantParameters()
        self.feedback_history = []

    def control_to_throttle(self, control_value: float, scale: float = 1.0) -> int:
        """
        Convert Primal Logic control output to MotorHandPro throttle

        Args:
            control_value: Control output from Primal Logic (-10 to +10)
            scale: Scaling factor to map control range

        Returns:
            Throttle value (0-255)
        """
        # Map control_value to xFixed range (0 to 150)
        # control_value range: -10 to +10
        # Map to 0-150 range
        x_fixed = (control_value + 10.0) * (150.0 / 20.0) * scale

        # Clamp to valid range
        x_fixed = np.clip(x_fixed, 0.0, 150.0)

        # Convert to throttle
        return self.params.throttle_from_fixed(x_fixed)

    def parse_motorhand_feedback(self, csv_line: str) -> Optional[MotorFeedback]:
        """
        Parse feedback from MotorHandPro CSV output

        Expected format: t, psi, gamma, Ec
        """
        try:
            if csv_line.startswith('#') or csv_line.strip() == '':
                return None

            parts = csv_line.strip().split(',')
            if len(parts) < 4:
                return None

            return MotorFeedback(
                timestamp=float(parts[0]),
                psi=float(parts[1]),
                gamma=float(parts[2]),
                Ec=float(parts[3])
            )
        except (ValueError, IndexError):
            return None

    def compute_error_from_feedback(
        self,
        feedback: MotorFeedback,
        target_psi: float = 0.0
    ) -> float:
        """
        Compute error signal from motor feedback for Primal Logic control

        Args:
            feedback: Motor feedback data
            target_psi: Target psi value

        Returns:
            Error signal
        """
        return feedback.psi - target_psi


class MotorHandBridge:
    """
    Complete integration bridge between Primal Logic Processor and MotorHandPro

    Workflow:
    1. Primal Logic computes control signal
    2. Bridge converts to QUANT throttle
    3. MotorHandPro actuates motors
    4. Feedback (psi, gamma, Ec) returned
    5. Error computed and fed back to Primal Logic
    """

    def __init__(self, motorhand_repo_path: str = "/tmp/MotorHandPro"):
        self.motorhand_path = motorhand_repo_path
        self.quant = QuantInterface()
        self.control_history = []

    def integrate_control_signal(
        self,
        primal_control: float,
        feedback: Optional[MotorFeedback] = None
    ) -> Tuple[int, Dict]:
        """
        Integrate Primal Logic control with MotorHandPro

        Args:
            primal_control: Control output from Primal Logic Processor
            feedback: Optional motor feedback for closed-loop control

        Returns:
            Tuple of (throttle_value, integration_data)
        """
        # Convert control to throttle
        throttle = self.quant.control_to_throttle(primal_control)

        # Prepare integration data
        integration_data = {
            'primal_control': primal_control,
            'throttle': throttle,
            'quant_xfixed': (throttle / 255.0) * 150.0,
            'feedback': feedback
        }

        # If we have feedback, compute error for next iteration
        if feedback:
            error = self.quant.compute_error_from_feedback(feedback)
            integration_data['computed_error'] = error

        self.control_history.append(integration_data)

        return throttle, integration_data

    def simulate_closed_loop(
        self,
        primal_processor,
        initial_state: float = 30.0,
        target_state: float = 0.0,
        duration: float = 10.0,
        dt: float = 0.01
    ) -> list:
        """
        Simulate closed-loop control with both systems

        Args:
            primal_processor: PrimalLogicProcessor instance
            initial_state: Initial system state
            target_state: Target system state
            duration: Simulation duration
            dt: Timestep

        Returns:
            List of integration states
        """
        states = []
        current_state = initial_state
        num_steps = int(duration / dt)

        for step in range(num_steps):
            t = step * dt

            # Primal Logic computes control
            primal_control, primal_state = primal_processor.compute_control(
                current_value=current_state,
                target_value=target_state,
                timestamp=t
            )

            # Create mock feedback (in real system, this comes from hardware)
            feedback = MotorFeedback(
                psi=current_state,
                gamma=primal_control,
                Ec=primal_state.integral,
                timestamp=t
            )

            # Bridge integrates control
            throttle, integration_data = self.integrate_control_signal(
                primal_control,
                feedback
            )

            # Update state (simple dynamics model)
            current_state += primal_control * dt
            current_state = max(0.0, current_state)

            # Record state
            state_record = {
                'time': t,
                'state': current_state,
                'primal_control': primal_control,
                'throttle': throttle,
                'psi': feedback.psi,
                'gamma': feedback.gamma,
                'Ec': feedback.Ec,
                'comfort': primal_state.comfort_index
            }
            states.append(state_record)

        return states

    def export_integration_csv(self, states: list, filename: str):
        """Export integration results to CSV"""
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['# Primal Logic + MotorHandPro Integration'])
            writer.writerow(['# Combined control system output'])
            writer.writerow([
                't', 'state', 'primal_control', 'throttle',
                'psi', 'gamma', 'Ec', 'comfort'
            ])

            for state in states:
                writer.writerow([
                    f"{state['time']:.3f}",
                    f"{state['state']:.6f}",
                    f"{state['primal_control']:.6f}",
                    f"{state['throttle']:d}",
                    f"{state['psi']:.6f}",
                    f"{state['gamma']:.6f}",
                    f"{state['Ec']:.6f}",
                    f"{state['comfort']:.2f}"
                ])

    def generate_arduino_interface(self, output_file: str = "primal_motorhand_interface.ino"):
        """
        Generate Arduino sketch for hardware integration

        Creates interface code that can run on actual Arduino hardware
        """
        arduino_code = '''
// Primal Logic + MotorHandPro Integration
// Hardware interface for autonomous vehicle control
// Author: Donte Lightfoot - Lightfoot Technology

#include "quant_full.h"

// Primal Logic parameters
const float K_GAIN = 0.5;
const float LAMBDA_DECAY = 2.0;
const float DT = 0.01; // 10ms

// State variables
float integral = 0.0;
float velocity = 0.0;
float target_velocity = 0.0;

void setup() {
  Serial.begin(115200);
  delay(1500);

  // Initialize QUANT system
  auto quant_results = QUANT::computeAll();
  QUANT::print(quant_results);

  Serial.println("Primal Logic Integration Active");
}

void loop() {
  // Read sensor inputs (velocity, position, etc.)
  velocity = readVelocitySensor();

  // Compute error
  float error = velocity - target_velocity;

  // Update integral with exponential weighting
  float decay_factor = exp(-LAMBDA_DECAY * DT);
  integral = integral * decay_factor + error * DT;

  // Compute control
  float control = -K_GAIN * integral;

  // Bound control
  control = constrain(control, -10.0, 10.0);

  // Convert to throttle via QUANT
  float x_fixed = (control + 10.0) * (150.0 / 20.0);
  x_fixed = constrain(x_fixed, 0.0, 150.0);
  uint8_t throttle = QUANT::throttleFromFixed(x_fixed);

  // Send to motor controller
  sendMotorCommand(throttle);

  // Log data
  Serial.print(millis()/1000.0);
  Serial.print(",");
  Serial.print(velocity);
  Serial.print(",");
  Serial.print(control);
  Serial.print(",");
  Serial.println(throttle);

  delay(10); // 10ms = 100Hz control loop
}

float readVelocitySensor() {
  // TODO: Implement actual sensor reading
  return analogRead(A0) * (50.0 / 1023.0);
}

void sendMotorCommand(uint8_t throttle) {
  // TODO: Implement motor control interface
  analogWrite(9, throttle);
}
'''

        output_path = os.path.join(
            os.path.dirname(__file__),
            '../../',
            output_file
        )

        with open(output_path, 'w') as f:
            f.write(arduino_code)

        return output_path


if __name__ == '__main__':
    # Example usage
    from src.microprocessor import PrimalLogicProcessor

    print("MotorHandPro Integration Bridge")
    print("=" * 60)

    # Initialize components
    processor = PrimalLogicProcessor()
    bridge = MotorHandBridge()

    print("\n1. Simulating closed-loop control...")
    states = bridge.simulate_closed_loop(
        primal_processor=processor,
        initial_state=30.0,
        target_state=0.0,
        duration=10.0
    )

    print(f"   Simulation complete: {len(states)} timesteps")
    print(f"   Final state: {states[-1]['state']:.2f}")
    print(f"   Final throttle: {states[-1]['throttle']}")

    # Export results
    bridge.export_integration_csv(states, 'integration_output.csv')
    print("\n2. Results exported to integration_output.csv")

    # Generate Arduino interface
    arduino_file = bridge.generate_arduino_interface()
    print(f"\n3. Arduino interface generated: {arduino_file}")

    print("\nIntegration bridge ready for deployment!")
