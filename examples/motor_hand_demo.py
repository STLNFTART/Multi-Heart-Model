#!/usr/bin/env python3
"""
Motor Hand Pro Integration Demo

Demonstrates real-time control of Motor Hand Pro prosthetic using
physiological signals from the Heart-Brain Coupling Model (HBCM).

This example shows three control modes:
1. Neural-driven: Hand grip controlled by brain activity
2. Cardiac-driven: Hand grip controlled by heart activity
3. Coupled: Blended control from both systems

Usage:
    python examples/motor_hand_demo.py --mode simulation
    python examples/motor_hand_demo.py --mode hardware --port /dev/ttyUSB0
"""

import argparse
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cardiac import VanDerPolOscillator
from src.coupling import CouplingParameters, HeartBrainCouplingModel
from src.hardware import HBCMMotorHandController, MotorHandConfig, MotorHandPro, Gesture
from src.neural import FitzHughNagumo


def run_neural_control_demo(controller: HBCMMotorHandController, duration: float = 10.0):
    """Demonstrate neural-driven hand control.

    Args:
        controller: HBCM motor hand controller.
        duration: Simulation duration in seconds.
    """
    print("\n=== Neural Control Demo ===")
    print("Hand grip strength driven by neural oscillations")

    # Create HBCM with emphasis on neural activity
    hbcm = HeartBrainCouplingModel(
        neural_model=FitzHughNagumo(stimulus_amplitude=0.3),  # Strong neural stimulus
        cardiac_model=VanDerPolOscillator(mu=1.0, omega=1.0),
        coupling=CouplingParameters(
            neural_to_cardiac_gain=0.3,
            cardiac_to_neural_gain=0.1,
        ),
    )

    # Run simulation
    trajectory = hbcm.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, duration),
        dt=0.01,
    )

    # Update hand at 10 Hz
    update_interval = 10  # Every 10 steps (0.1s)
    for idx, (t, state) in enumerate(trajectory):
        if idx % update_interval == 0:
            neural_v = state[0]
            controller.update_from_neural_state(neural_v)
            print(f"t={t:.2f}s, neural={neural_v:.3f}, grip={controller.motor_hand.get_positions()}")

    print("Neural control demo complete")


def run_cardiac_control_demo(controller: HBCMMotorHandController, duration: float = 10.0):
    """Demonstrate cardiac-driven hand control.

    Args:
        controller: HBCM motor hand controller.
        duration: Simulation duration in seconds.
    """
    print("\n=== Cardiac Control Demo ===")
    print("Hand grip strength driven by cardiac oscillations")

    # Create HBCM with emphasis on cardiac activity
    hbcm = HeartBrainCouplingModel(
        neural_model=FitzHughNagumo(stimulus_amplitude=0.1),
        cardiac_model=VanDerPolOscillator(mu=1.5, omega=1.2),  # Strong cardiac activity
        coupling=CouplingParameters(
            neural_to_cardiac_gain=0.1,
            cardiac_to_neural_gain=0.3,
        ),
    )

    # Run simulation
    trajectory = hbcm.simulate(
        initial_state=(0.0, 0.0, 1.5, 0.0),
        t_span=(0.0, duration),
        dt=0.01,
    )

    # Update hand at 10 Hz
    update_interval = 10
    for idx, (t, state) in enumerate(trajectory):
        if idx % update_interval == 0:
            cardiac_x = state[2]
            controller.update_from_cardiac_state(cardiac_x)
            print(f"t={t:.2f}s, cardiac={cardiac_x:.3f}")

    print("Cardiac control demo complete")


def run_coupled_control_demo(controller: HBCMMotorHandController, duration: float = 10.0):
    """Demonstrate coupled neural-cardiac hand control.

    Args:
        controller: HBCM motor hand controller.
        duration: Simulation duration in seconds.
    """
    print("\n=== Coupled Control Demo ===")
    print("Hand grip driven by blended neural and cardiac signals")

    # Create fully coupled HBCM
    hbcm = HeartBrainCouplingModel(
        neural_model=FitzHughNagumo(stimulus_amplitude=0.2),
        cardiac_model=VanDerPolOscillator(mu=1.2, omega=1.0),
        coupling=CouplingParameters(
            neural_to_cardiac_gain=0.5,
            cardiac_to_neural_gain=0.3,
            neural_delay=0.05,
            cardiac_delay=0.08,
        ),
    )

    # Run simulation
    trajectory = hbcm.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, duration),
        dt=0.01,
    )

    # Update hand at 10 Hz
    update_interval = 10
    for idx, (t, state) in enumerate(trajectory):
        if idx % update_interval == 0:
            neural_v = state[0]
            cardiac_x = state[2]

            # Blend neural and cardiac signals (50/50)
            controller.update_from_coupled_state(neural_v, cardiac_x, blend=0.5)
            print(f"t={t:.2f}s, neural={neural_v:.3f}, cardiac={cardiac_x:.3f}")

    print("Coupled control demo complete")


def run_gesture_demo(motor_hand: MotorHandPro):
    """Demonstrate predefined gesture execution.

    Args:
        motor_hand: Motor hand interface.
    """
    print("\n=== Gesture Demo ===")
    print("Executing predefined hand gestures")

    gestures = [Gesture.OPEN, Gesture.FIST, Gesture.POINT, Gesture.PEACE, Gesture.OK]

    for gesture in gestures:
        print(f"\nExecuting: {gesture.value}")
        motor_hand.execute_gesture(gesture)
        time.sleep(2)  # Hold gesture for 2 seconds

    print("\nReturning to neutral")
    motor_hand.reset_to_neutral()

    print("Gesture demo complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Motor Hand Pro + HBCM Integration Demo")
    parser.add_argument(
        "--mode",
        choices=["simulation", "hardware"],
        default="simulation",
        help="Run in simulation mode or with real hardware",
    )
    parser.add_argument(
        "--port",
        default="/dev/ttyUSB0",
        help="Serial port for Arduino (if using hardware mode)",
    )
    parser.add_argument(
        "--demo",
        choices=["all", "neural", "cardiac", "coupled", "gestures"],
        default="all",
        help="Which demo to run",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Duration for control demos (seconds)",
    )

    args = parser.parse_args()

    # Configure motor hand
    config = MotorHandConfig(
        port=args.port,
        simulation_mode=(args.mode == "simulation"),
        auto_reconnect=True,
    )

    print("=" * 60)
    print("Motor Hand Pro + HBCM Integration Demo")
    print("=" * 60)
    print(f"Mode: {args.mode.upper()}")
    if args.mode == "hardware":
        print(f"Port: {args.port}")
    print(f"Demo: {args.demo}")
    print("=" * 60)

    # Initialize motor hand
    with MotorHandPro(config) as motor_hand:
        print(f"\nMotor Hand Pro connected: {motor_hand.connected}")

        # Enable the hand
        motor_hand.enable()
        print("Motor Hand Pro enabled")

        # Get initial status
        status = motor_hand.get_status()
        if status:
            print(f"Initial status: {status}")

        # Create controller
        controller = HBCMMotorHandController(motor_hand)

        # Run selected demos
        if args.demo in ["all", "gestures"]:
            run_gesture_demo(motor_hand)

        if args.demo in ["all", "neural"]:
            run_neural_control_demo(controller, args.duration)

        if args.demo in ["all", "cardiac"]:
            run_cardiac_control_demo(controller, args.duration)

        if args.demo in ["all", "coupled"]:
            run_coupled_control_demo(controller, args.duration)

        # Return to neutral before exit
        print("\nReturning to neutral position...")
        motor_hand.reset_to_neutral()
        time.sleep(1)

        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60)


if __name__ == "__main__":
    main()
