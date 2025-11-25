#!/usr/bin/env python3
"""
Comprehensive Surgical Robotics Integration Demo

Demonstrates integration of Multi-Heart-Model physiological simulation
with surgical robotics platforms (dVRK, CRTK, AMBF, ROS2).

This example shows:
1. Physiological monitoring integration
2. dVRK surgical robot control
3. CRTK standardized API usage
4. AMBF simulation environment
5. ROS2 communication bridge
6. Adaptive control based on patient physiology

Author: Multi-Heart-Model Development Team
"""

import sys
import numpy as np
import time

# Import surgical robotics interfaces
sys.path.insert(0, '/home/user/Multi-Heart-Model')

from src.surgical_robotics import (
    # dVRK interface
    DVRKInterface,
    DVRKConfiguration,
    DVRKArmType,
    DVRKCartesianCommand,

    # CRTK interface
    CRTKInterface,
    CRTKConfiguration,

    # AMBF simulator
    AMBFInterface,
    AMBFSimulationConfig,

    # ROS2 bridge
    ROS2Bridge,
    ROS2NodeConfig,
    ROS2MessageType,

    # Physiological controller
    PhysiologicalController,
    SurgicalPhase,
    SurgicalFeedbackState,
)

# Import Multi-Heart-Model components
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def demo_dvrk_integration():
    """Demonstrate dVRK surgical robot integration"""
    print_section("1. dVRK (da Vinci Research Kit) Integration")

    # Configure dVRK
    config = DVRKConfiguration(
        arm_type=DVRKArmType.PSM1,
        arm_name="PSM1",
        control_rate_hz=100.0,
        enable_physio_feedback=True,
    )

    # Initialize interface
    dvrk = DVRKInterface(config)
    dvrk.enable()
    dvrk.home()

    # Create physiological controller
    physio_controller = PhysiologicalController(
        baseline_heart_rate=70.0,
        baseline_blood_pressure=90.0
    )

    # Set surgical phase
    physio_controller.set_surgical_phase(SurgicalPhase.APPROACH)

    # Simulate surgical task with physiological feedback
    print("\n  Executing surgical approach with physiological monitoring...")

    target_positions = [
        np.array([0.02, 0.01, -0.10]),
        np.array([0.04, 0.02, -0.12]),
        np.array([0.05, 0.02, -0.15]),
    ]

    for i, target_pos in enumerate(target_positions):
        # Get current physiological state
        physio_state = physio_controller.get_physiological_feedback()

        # Compute control constraints
        constraints = physio_controller.compute_control_constraints(physio_state)

        # Apply physiological feedback to robot control
        velocity_scale = dvrk.integrate_physiological_feedback(
            physio_state.heart_rate,
            physio_state.mean_arterial_pressure,
            physio_state.stress_index
        )

        print(f"\n  Step {i+1}:")
        print(f"    Target position: {target_pos}")
        print(f"    HR: {physio_state.heart_rate:.1f} bpm")
        print(f"    BP: {physio_state.mean_arterial_pressure:.0f} mmHg")
        print(f"    Velocity scale: {velocity_scale:.2f}")
        print(f"    Alert level: {physio_state.alert_level.name}")

        # Check for emergency stop
        if constraints.emergency_stop:
            print("    WARNING: Emergency stop triggered!")
            dvrk.disable()
            break

        # Move robot (scaled by physiological state)
        target_ori = np.array([0, 0, 0, 1])  # Identity quaternion
        cmd = DVRKCartesianCommand(target_pos, target_ori)

        if not constraints.pause_required:
            dvrk.move_cartesian(cmd)
        else:
            print("    PAUSED: Waiting for stable physiological state")

        time.sleep(0.1)

    # Get final state
    final_state = dvrk.get_measured_state()
    print(f"\n  Final position: {final_state.cartesian_position}")
    print(f"  Operating state: {final_state.operating_state.value}")

    return dvrk, physio_controller


def demo_crtk_interface():
    """Demonstrate CRTK standardized API"""
    print_section("2. CRTK (Collaborative Robotics Toolkit) Interface")

    # Configure CRTK
    config = CRTKConfiguration(
        robot_name="PSM2",
        enable_adaptive_control=True,
    )

    # Initialize interface
    crtk = CRTKInterface(config)
    crtk.enable()

    print("\n  Testing CRTK standardized commands...")

    # Servo commands (continuous setpoint)
    print("\n  1. Servo control (continuous):")
    target_pose = np.array([0.03, 0.02, -0.12, 0, 0, 0, 1])
    crtk.servo_cp(target_pose)
    state = crtk.get_measured_state()
    print(f"     Current pose: {state.measured_cp[:3]}")

    # Move command (goal-based)
    print("\n  2. Move command (goal-based):")
    goal_pose = np.array([0.05, 0.03, -0.15, 0, 0, 0, 1])
    crtk.move_cp(goal_pose, blocking=True)

    # Velocity control
    print("\n  3. Velocity servo:")
    velocity = np.array([0.01, 0.0, -0.01, 0, 0, 0])  # Linear + angular
    crtk.servo_cv(velocity)

    # Physiological integration
    print("\n  4. Physiological state integration:")
    physio_modulation = crtk.integrate_physiological_state(
        heart_rate=95,
        blood_pressure=100,
        oxygen_saturation=96,
        stress_index=0.3
    )

    print(f"     Velocity scale: {physio_modulation['velocity_scale']:.2f}")
    print(f"     Force scale: {physio_modulation['force_scale']:.2f}")
    print(f"     Safety margin: {physio_modulation['safety_margin']:.2f}")
    print(f"     Recommended pause: {physio_modulation['recommended_pause']}")

    # Get command history
    history = crtk.get_command_history()
    print(f"\n  Total commands executed: {len(history)}")

    return crtk


def demo_ambf_simulation():
    """Demonstrate AMBF simulator integration"""
    print_section("3. AMBF (Asynchronous Multi-Body Framework) Simulation")

    # Configure simulation
    config = AMBFSimulationConfig(
        world_name="surgical_operating_room",
        time_step=0.001,
        max_frequency=1000.0,
    )

    # Initialize simulator
    ambf = AMBFInterface(config)
    ambf.connect()

    # Load surgical robot
    print("\n  Loading surgical robot into simulation...")
    ambf.load_robot(
        "dVRK_PSM1",
        model_path="models/dvrk_psm.yaml",
        initial_position=np.array([0.0, 0.0, 0.3])
    )

    # Load patient anatomy (simplified)
    ambf.load_robot(
        "patient_anatomy",
        model_path="models/patient_heart.yaml",
        initial_position=np.array([0.0, 0.0, 0.0])
    )

    # Run simulation with physiological feedback
    print("\n  Running simulation with physiological integration...")

    physio_data = {
        'heart_rate': 75.0,
        'blood_pressure': 92.0,
        'stress': 0.25,
    }

    for step in range(100):
        # Update physiology
        if step % 10 == 0:
            physio_data['heart_rate'] += np.random.normal(0, 2)

            # Integrate with robot control
            modulation = ambf.integrate_with_physiology("dVRK_PSM1", physio_data)

            if step % 20 == 0:
                print(f"\n  Step {step}:")
                print(f"    HR: {physio_data['heart_rate']:.1f} bpm")
                print(f"    Velocity scale: {modulation['velocity_scale']:.2f}")
                print(f"    Pause: {modulation['pause_simulation']}")

        # Step simulation
        ambf.step_simulation()

    # Get robot state
    robot_state = ambf.get_robot_state("dVRK_PSM1")
    print(f"\n  Final robot position: {robot_state.position}")

    # Export simulation state
    ambf.export_simulation_state("ambf_surgical_sim.json")
    print("  Simulation state exported to: ambf_surgical_sim.json")

    return ambf


def demo_ros2_bridge():
    """Demonstrate ROS2 communication bridge"""
    print_section("4. ROS2 Communication Bridge")

    # Configure ROS2 node
    config = ROS2NodeConfig(
        node_name="multi_heart_surgical_bridge",
        namespace="/multi_heart"
    )

    # Initialize bridge
    bridge = ROS2Bridge(config)
    bridge.initialize()

    print("\n  Creating ROS2 publishers and subscribers...")

    # Create physiological data publishers
    bridge.create_publisher("/physio/heart_rate", ROS2MessageType.FLOAT64)
    bridge.create_publisher("/physio/blood_pressure", ROS2MessageType.FLOAT64)
    bridge.create_publisher("/physio/state", ROS2MessageType.PHYSIOLOGICAL_STATE)

    # Create robot command publisher
    bridge.create_publisher("/robot/target_pose", ROS2MessageType.POSE_STAMPED)

    # Publish physiological state
    print("\n  Publishing physiological data to ROS2...")
    bridge.publish_physiological_state(
        topic_prefix="/physio",
        heart_rate=72.0,
        bp_systolic=118.0,
        bp_diastolic=78.0,
        spo2=98.0,
        resp_rate=15.0
    )

    # Publish robot command
    print("  Publishing robot command...")
    pose_msg = bridge.create_pose_stamped_msg(
        position=np.array([0.05, 0.02, -0.12]),
        orientation=np.array([0, 0, 0, 1]),
        frame_id="base"
    )
    bridge.publish("/robot/target_pose", pose_msg)

    # Get statistics
    stats = bridge.get_statistics()
    print(f"\n  Bridge statistics:")
    print(f"    Messages published: {stats['messages_published']}")
    print(f"    Active publishers: {stats['active_publishers']}")
    print(f"    Publish rate: {stats['publish_rate']:.2f} Hz")

    # Export topic list
    bridge.export_topic_list("ros2_surgical_topics.json")
    print("  Topic list exported to: ros2_surgical_topics.json")

    return bridge


def demo_hbcm_integration():
    """Demonstrate HBCM physiological model integration"""
    print_section("5. Heart-Brain Coupling Model Integration")

    print("\n  Creating HBCM physiological simulation...")

    # Create heart-brain coupling model
    hbcm = HeartBrainCouplingModel(
        neural_model=FitzHughNagumo(stimulus_amplitude=0.3),
        cardiac_model=VanDerPolOscillator(mu=1.5, omega=1.0),
        coupling=CouplingParameters(
            neural_to_cardiac_gain=0.5,
            cardiac_to_neural_gain=0.3,
            neural_delay=0.10,  # 100ms vagal delay
            cardiac_delay=0.15   # 150ms baroreceptor delay
        )
    )

    # Initialize physiological controller with HBCM
    controller = PhysiologicalController(
        hbcm_model=hbcm,
        baseline_heart_rate=70.0,
        baseline_blood_pressure=90.0
    )

    # Set surgical phase
    controller.set_surgical_phase(SurgicalPhase.MANIPULATION)

    # Simulate surgery with HBCM feedback
    print("\n  Simulating surgical procedure with HBCM feedback...")

    for t in range(10):
        # Get physiological state from HBCM
        physio_state = controller.get_physiological_feedback()

        # Compute control constraints
        constraints = controller.compute_control_constraints(physio_state)

        if t % 2 == 0:
            print(f"\n  t = {t}s:")
            print(f"    HR: {physio_state.heart_rate:.1f} bpm")
            print(f"    MAP: {physio_state.mean_arterial_pressure:.0f} mmHg")
            print(f"    Alert: {physio_state.alert_level.name}")
            print(f"    Velocity scale: {constraints.max_velocity_scale:.2f}")
            print(f"    Force scale: {constraints.max_force_scale:.2f}")

    # Compute HRV metrics
    print("\n  Computing HRV metrics...")
    hrv_metrics = controller.compute_hrv_metrics(duration_seconds=10.0)
    print(f"    SDNN: {hrv_metrics['sdnn']:.2f} ms")
    print(f"    RMSSD: {hrv_metrics['rmssd']:.2f} ms")
    print(f"    Mean HR: {hrv_metrics['mean_hr']:.1f} bpm")

    return controller, hbcm


def demo_complete_integration():
    """Demonstrate complete integrated system"""
    print_section("6. Complete Integrated System Demo")

    print("\n  Initializing complete surgical robotics system...")

    # 1. Initialize HBCM physiological model
    hbcm = HeartBrainCouplingModel(
        neural_model=FitzHughNagumo(),
        cardiac_model=VanDerPolOscillator(),
    )

    # 2. Initialize physiological controller
    physio_controller = PhysiologicalController(hbcm_model=hbcm)
    physio_controller.set_surgical_phase(SurgicalPhase.MANIPULATION)

    # 3. Initialize ROS2 bridge
    ros2_bridge = ROS2Bridge(ROS2NodeConfig(node_name="surgical_system"))
    ros2_bridge.initialize()
    ros2_bridge.create_publisher("/physio/state", ROS2MessageType.PHYSIOLOGICAL_STATE)

    # 4. Initialize dVRK robot
    dvrk = DVRKInterface(DVRKConfiguration(arm_name="PSM1"))
    dvrk.enable()
    dvrk.home()

    # 5. Initialize CRTK interface
    crtk = CRTKInterface(CRTKConfiguration(robot_name="PSM2"))
    crtk.enable()

    # 6. Initialize AMBF simulator
    ambf = AMBFInterface(AMBFSimulationConfig(world_name="surgery"))
    ambf.connect()
    ambf.load_robot("PSM1_sim", "models/psm.yaml")

    print("\n  Running integrated surgical simulation...")

    # Simulate surgical procedure
    for step in range(20):
        # Get physiological feedback
        physio_state = physio_controller.get_physiological_feedback()

        # Publish to ROS2
        ros2_bridge.publish_physiological_state(
            heart_rate=physio_state.heart_rate,
            bp_systolic=physio_state.blood_pressure_systolic,
            bp_diastolic=physio_state.blood_pressure_diastolic,
            spo2=physio_state.oxygen_saturation,
            resp_rate=physio_state.respiratory_rate,
        )

        # Compute control constraints
        constraints = physio_controller.compute_control_constraints(physio_state)

        # Apply to robots
        if not constraints.emergency_stop:
            # dVRK control
            velocity_scale = dvrk.integrate_physiological_feedback(
                physio_state.heart_rate,
                physio_state.mean_arterial_pressure,
                physio_state.stress_index
            )

            # CRTK control
            crtk_mod = crtk.integrate_physiological_state(
                physio_state.heart_rate,
                physio_state.mean_arterial_pressure,
                physio_state.oxygen_saturation,
                physio_state.stress_index
            )

            # AMBF simulation
            ambf.step_simulation()

        if step % 5 == 0:
            print(f"\n  Step {step}:")
            print(f"    HR: {physio_state.heart_rate:.1f} bpm")
            print(f"    Alert: {physio_state.alert_level.name}")
            print(f"    dVRK velocity scale: {velocity_scale:.2f}")
            print(f"    CRTK velocity scale: {crtk_mod['velocity_scale']:.2f}")
            print(f"    Emergency stop: {constraints.emergency_stop}")

    print("\n  Integrated system simulation complete!")

    # Get final statistics
    ros2_stats = ros2_bridge.get_statistics()
    print(f"\n  System statistics:")
    print(f"    ROS2 messages published: {ros2_stats['messages_published']}")
    print(f"    Physiological samples: {len(physio_controller.physio_history)}")
    print(f"    AMBF simulation time: {ambf.simulation_time:.3f}s")

    return {
        'hbcm': hbcm,
        'physio_controller': physio_controller,
        'ros2_bridge': ros2_bridge,
        'dvrk': dvrk,
        'crtk': crtk,
        'ambf': ambf,
    }


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 70)
    print(" SURGICAL ROBOTICS INTEGRATION - COMPREHENSIVE DEMO")
    print(" Multi-Heart-Model + Surgical Robotics Platforms")
    print("=" * 70)

    # Run individual demos
    dvrk, physio = demo_dvrk_integration()
    crtk = demo_crtk_interface()
    ambf = demo_ambf_simulation()
    bridge = demo_ros2_bridge()
    controller, hbcm = demo_hbcm_integration()

    # Run complete integrated demo
    integrated_system = demo_complete_integration()

    # Summary
    print_section("DEMONSTRATION SUMMARY")
    print("\n  Successfully demonstrated:")
    print("    ✓ dVRK (da Vinci Research Kit) interface")
    print("    ✓ CRTK (Collaborative Robotics Toolkit) API")
    print("    ✓ AMBF (Asynchronous Multi-Body Framework) simulation")
    print("    ✓ ROS2 communication bridge")
    print("    ✓ Heart-Brain Coupling Model (HBCM) integration")
    print("    ✓ Physiological feedback control")
    print("    ✓ Complete integrated system")

    print("\n  Key capabilities:")
    print("    • Real-time physiological monitoring")
    print("    • Adaptive robot control based on patient state")
    print("    • Multi-level safety alerts")
    print("    • ROS2 middleware communication")
    print("    • Simulation and hardware interfaces")

    print("\n" + "=" * 70)
    print(" DEMO COMPLETE - All systems operational!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
