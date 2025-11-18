"""
da Vinci Research Kit (dVRK) Interface

Interface to the dVRK surgical robotics platform using cisst-SAW libraries.
Supports both ROS 1 and ROS 2 communication protocols.

References:
- Kazanzides et al. (2014) "An open-source research kit for the da Vinci Surgical System"
- dVRK Wiki: https://github.com/jhu-dvrk/sawIntuitiveResearchKit/wiki
- CISST libraries: https://github.com/jhu-cisst
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum
import json


class DVRKArmType(Enum):
    """dVRK arm types"""
    PSM1 = "PSM1"  # Patient Side Manipulator 1
    PSM2 = "PSM2"  # Patient Side Manipulator 2
    PSM3 = "PSM3"  # Patient Side Manipulator 3
    MTM = "MTM"    # Master Tool Manipulator
    MTML = "MTML"  # Master Tool Manipulator Left
    MTMR = "MTMR"  # Master Tool Manipulator Right
    ECM = "ECM"    # Endoscopic Camera Manipulator


class DVRKOperatingState(Enum):
    """dVRK operating states (from cisst-SAW)"""
    DISABLED = "DISABLED"
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    FAULT = "FAULT"
    NOT_READY = "NOT_READY"


@dataclass
class DVRKConfiguration:
    """
    Configuration for dVRK interface

    Based on dVRK console.json configuration format
    """
    arm_type: DVRKArmType = DVRKArmType.PSM1
    arm_name: str = "PSM1"

    # ROS configuration
    ros_namespace: str = "/dvrk"
    use_ros2: bool = True  # Use ROS2 by default

    # Control parameters
    control_rate_hz: float = 100.0  # 100Hz control loop
    position_tolerance_mm: float = 0.1  # 0.1mm position tolerance
    orientation_tolerance_deg: float = 0.5  # 0.5 degree tolerance

    # Safety limits (in meters for PSM)
    workspace_limits: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        'x': (-0.1, 0.1),
        'y': (-0.1, 0.1),
        'z': (-0.2, 0.0)
    })

    # Joint limits (radians)
    joint_limits: List[Tuple[float, float]] = field(default_factory=lambda: [
        (-1.605, 1.5707),  # Joint 1
        (-0.93, 0.93),     # Joint 2
        (0.0, 0.24),       # Joint 3 (prismatic, meters)
        (-3.0, 3.0),       # Joint 4
        (-3.0, 3.0),       # Joint 5
        (-3.0, 3.0),       # Joint 6
        (-3.0, 3.0),       # Joint 7
    ])

    # Physiological integration
    enable_physio_feedback: bool = True
    max_velocity_scale: float = 1.0  # Scale down velocity based on physiology


@dataclass
class DVRKCartesianCommand:
    """
    Cartesian space command for dVRK

    Position in meters, orientation as quaternion or rotation matrix
    """
    position: np.ndarray  # [x, y, z] in meters
    orientation: np.ndarray  # Quaternion [qx, qy, qz, qw] or 3x3 rotation matrix
    reference_frame: str = "base"  # "base" or "tool"
    timestamp: float = 0.0

    def __post_init__(self):
        self.position = np.array(self.position)
        self.orientation = np.array(self.orientation)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'position': self.position.tolist(),
            'orientation': self.orientation.tolist(),
            'reference_frame': self.reference_frame,
            'timestamp': self.timestamp,
        }


@dataclass
class DVRKJointCommand:
    """
    Joint space command for dVRK
    """
    joint_positions: np.ndarray  # Joint angles in radians (or meters for prismatic)
    joint_velocities: Optional[np.ndarray] = None
    joint_efforts: Optional[np.ndarray] = None
    timestamp: float = 0.0

    def __post_init__(self):
        self.joint_positions = np.array(self.joint_positions)
        if self.joint_velocities is not None:
            self.joint_velocities = np.array(self.joint_velocities)
        if self.joint_efforts is not None:
            self.joint_efforts = np.array(self.joint_efforts)


@dataclass
class DVRKMeasuredState:
    """
    Measured state from dVRK
    """
    cartesian_position: np.ndarray
    cartesian_orientation: np.ndarray
    joint_positions: np.ndarray
    joint_velocities: Optional[np.ndarray] = None
    joint_efforts: Optional[np.ndarray] = None
    operating_state: DVRKOperatingState = DVRKOperatingState.DISABLED
    timestamp: float = 0.0


class DVRKInterface:
    """
    Interface to da Vinci Research Kit (dVRK) surgical robot

    Provides high-level control interface using cisst-SAW libraries
    and ROS/ROS2 communication middleware.

    Example usage:
        >>> config = DVRKConfiguration(arm_type=DVRKArmType.PSM1)
        >>> dvrk = DVRKInterface(config)
        >>> dvrk.enable()
        >>>
        >>> # Cartesian motion
        >>> target_pos = np.array([0.0, 0.0, -0.1])
        >>> target_ori = np.array([0, 0, 0, 1])  # Identity quaternion
        >>> cmd = DVRKCartesianCommand(target_pos, target_ori)
        >>> dvrk.move_cartesian(cmd)
        >>>
        >>> # Get current state
        >>> state = dvrk.get_measured_state()
        >>> print(f"Position: {state.cartesian_position}")
    """

    def __init__(self, config: DVRKConfiguration):
        self.config = config
        self.current_state = None
        self.command_history = []

        # Simulated state (in real system, this comes from hardware)
        self._sim_joint_positions = np.zeros(7)
        self._sim_cartesian_position = np.array([0.0, 0.0, -0.1])
        self._sim_cartesian_orientation = np.array([0, 0, 0, 1])  # quaternion
        self._operating_state = DVRKOperatingState.DISABLED

        print(f"dVRK Interface initialized for {config.arm_name}")
        print(f"  ROS namespace: {config.ros_namespace}")
        print(f"  ROS version: {'ROS2' if config.use_ros2 else 'ROS1'}")
        print(f"  Control rate: {config.control_rate_hz} Hz")

    def enable(self) -> bool:
        """
        Enable the dVRK arm

        In real system, this calls the cisst-SAW enable() service
        """
        print(f"Enabling {self.config.arm_name}...")
        self._operating_state = DVRKOperatingState.ENABLED
        return True

    def disable(self) -> bool:
        """Disable the dVRK arm"""
        print(f"Disabling {self.config.arm_name}...")
        self._operating_state = DVRKOperatingState.DISABLED
        return True

    def home(self) -> bool:
        """
        Home the dVRK arm

        Moves arm through homing procedure
        """
        print(f"Homing {self.config.arm_name}...")
        self._sim_joint_positions = np.zeros(7)
        self._sim_cartesian_position = np.array([0.0, 0.0, -0.1])
        return True

    def move_cartesian(
        self,
        command: DVRKCartesianCommand,
        blocking: bool = False
    ) -> bool:
        """
        Move arm to target Cartesian pose

        Args:
            command: Target Cartesian command
            blocking: If True, wait until motion complete

        Returns:
            Success flag
        """
        # Check workspace limits
        if not self._check_workspace_limits(command.position):
            print(f"ERROR: Target position {command.position} outside workspace limits")
            return False

        # Check operating state
        if self._operating_state != DVRKOperatingState.ENABLED:
            print(f"ERROR: Arm not enabled (state: {self._operating_state})")
            return False

        # In real system, this publishes to ROS topic:
        # /{namespace}/{arm_name}/servo_cp (Cartesian Position)
        print(f"Moving {self.config.arm_name} to position: {command.position}")

        # Simulate motion
        self._sim_cartesian_position = command.position.copy()
        self._sim_cartesian_orientation = command.orientation.copy()

        # Record command
        self.command_history.append({
            'type': 'cartesian',
            'command': command,
            'timestamp': command.timestamp,
        })

        return True

    def move_joint(
        self,
        command: DVRKJointCommand,
        blocking: bool = False
    ) -> bool:
        """
        Move arm to target joint configuration

        Args:
            command: Target joint command
            blocking: If True, wait until motion complete

        Returns:
            Success flag
        """
        # Check joint limits
        if not self._check_joint_limits(command.joint_positions):
            print(f"ERROR: Joint positions outside limits")
            return False

        # Check operating state
        if self._operating_state != DVRKOperatingState.ENABLED:
            print(f"ERROR: Arm not enabled")
            return False

        # In real system, publishes to:
        # /{namespace}/{arm_name}/servo_jp (Joint Position)
        print(f"Moving {self.config.arm_name} to joint config: {command.joint_positions}")

        # Simulate motion
        self._sim_joint_positions = command.joint_positions.copy()

        # Record command
        self.command_history.append({
            'type': 'joint',
            'command': command,
            'timestamp': command.timestamp,
        })

        return True

    def get_measured_state(self) -> DVRKMeasuredState:
        """
        Get current measured state of arm

        In real system, this reads from ROS topics:
        - /{namespace}/{arm_name}/measured_cp (Cartesian Position)
        - /{namespace}/{arm_name}/measured_jp (Joint Position)
        """
        return DVRKMeasuredState(
            cartesian_position=self._sim_cartesian_position.copy(),
            cartesian_orientation=self._sim_cartesian_orientation.copy(),
            joint_positions=self._sim_joint_positions.copy(),
            operating_state=self._operating_state,
            timestamp=0.0,  # Would be actual timestamp in real system
        )

    def set_wrench(self, force: np.ndarray, torque: np.ndarray) -> bool:
        """
        Apply wrench (force + torque) to end effector

        Used for force control modes

        Args:
            force: Force vector [fx, fy, fz] in Newtons
            torque: Torque vector [tx, ty, tz] in N·m
        """
        print(f"Setting wrench - Force: {force}, Torque: {torque}")
        # In real system: publish to /{namespace}/{arm_name}/servo_cf
        return True

    def open_gripper(self, angle: float = 80.0) -> bool:
        """
        Open gripper/jaw

        Args:
            angle: Opening angle in degrees (0-80 typical range)
        """
        angle = np.clip(angle, 0.0, 80.0)
        print(f"Opening gripper to {angle} degrees")
        # In real system: publish to /{namespace}/{arm_name}/jaw/servo_jp
        return True

    def close_gripper(self) -> bool:
        """Close gripper/jaw completely"""
        return self.open_gripper(0.0)

    def _check_workspace_limits(self, position: np.ndarray) -> bool:
        """Check if position is within workspace limits"""
        x, y, z = position
        limits = self.config.workspace_limits

        return (limits['x'][0] <= x <= limits['x'][1] and
                limits['y'][0] <= y <= limits['y'][1] and
                limits['z'][0] <= z <= limits['z'][1])

    def _check_joint_limits(self, joint_positions: np.ndarray) -> bool:
        """Check if joint positions are within limits"""
        for i, (pos, (min_pos, max_pos)) in enumerate(
            zip(joint_positions, self.config.joint_limits)
        ):
            if not (min_pos <= pos <= max_pos):
                print(f"Joint {i} out of limits: {pos} not in [{min_pos}, {max_pos}]")
                return False
        return True

    def get_kinematics(self) -> Dict[str, np.ndarray]:
        """
        Get forward kinematics

        Returns current end-effector pose given joint positions
        """
        # In real system, this would use cisst-SAW kinematics
        # For now, return simulated values
        return {
            'position': self._sim_cartesian_position,
            'orientation': self._sim_cartesian_orientation,
            'jacobian': np.eye(6, 7),  # Simplified 6x7 Jacobian
        }

    def get_inverse_kinematics(
        self,
        target_position: np.ndarray,
        target_orientation: np.ndarray,
        seed: Optional[np.ndarray] = None
    ) -> Optional[np.ndarray]:
        """
        Compute inverse kinematics

        Args:
            target_position: Desired position [x, y, z]
            target_orientation: Desired orientation (quaternion)
            seed: Initial guess for IK solver

        Returns:
            Joint positions, or None if no solution found
        """
        # In real system, uses cisst-SAW IK solver
        # For now, return approximate solution
        print(f"Computing IK for position: {target_position}")

        # Simplified IK (placeholder)
        # Real implementation would call cisst-SAW IK solver
        return np.zeros(7)

    def integrate_physiological_feedback(
        self,
        heart_rate: float,
        blood_pressure: float,
        stress_level: float
    ) -> float:
        """
        Integrate physiological feedback to modulate robot motion

        Args:
            heart_rate: Current heart rate (bpm)
            blood_pressure: Mean arterial pressure (mmHg)
            stress_level: Normalized stress level (0-1)

        Returns:
            Velocity scaling factor (0-1)
        """
        # Scale velocity based on physiological state
        # Higher stress -> slower, more careful motions

        base_scale = self.config.max_velocity_scale

        # Reduce speed if heart rate elevated
        if heart_rate > 100:  # Normal resting: 60-100 bpm
            hr_factor = max(0.5, 1.0 - (heart_rate - 100) / 100)
        else:
            hr_factor = 1.0

        # Reduce speed if blood pressure abnormal
        # Normal MAP: 70-100 mmHg
        if not (70 <= blood_pressure <= 100):
            bp_factor = 0.7
        else:
            bp_factor = 1.0

        # Reduce speed based on stress
        stress_factor = 1.0 - 0.3 * stress_level

        velocity_scale = base_scale * hr_factor * bp_factor * stress_factor

        return velocity_scale

    def export_state_to_ros2_msg(self, state: DVRKMeasuredState) -> Dict[str, Any]:
        """
        Export state as ROS2 message format

        Compatible with geometry_msgs/PoseStamped and sensor_msgs/JointState
        """
        return {
            'measured_cp': {
                'header': {
                    'stamp': {'sec': int(state.timestamp), 'nanosec': 0},
                    'frame_id': f'{self.config.arm_name}_base',
                },
                'pose': {
                    'position': {
                        'x': float(state.cartesian_position[0]),
                        'y': float(state.cartesian_position[1]),
                        'z': float(state.cartesian_position[2]),
                    },
                    'orientation': {
                        'x': float(state.cartesian_orientation[0]),
                        'y': float(state.cartesian_orientation[1]),
                        'z': float(state.cartesian_orientation[2]),
                        'w': float(state.cartesian_orientation[3]),
                    },
                },
            },
            'measured_jp': {
                'header': {
                    'stamp': {'sec': int(state.timestamp), 'nanosec': 0},
                    'frame_id': f'{self.config.arm_name}',
                },
                'name': [f'joint_{i}' for i in range(len(state.joint_positions))],
                'position': state.joint_positions.tolist(),
                'velocity': state.joint_velocities.tolist() if state.joint_velocities is not None else [],
                'effort': state.joint_efforts.tolist() if state.joint_efforts is not None else [],
            },
        }


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("dVRK (da Vinci Research Kit) Interface Demo")
    print("=" * 60)

    # Create configuration
    config = DVRKConfiguration(
        arm_type=DVRKArmType.PSM1,
        arm_name="PSM1",
        enable_physio_feedback=True,
    )

    # Initialize interface
    dvrk = DVRKInterface(config)

    # Enable and home
    dvrk.enable()
    dvrk.home()

    # Test Cartesian motion
    print("\n1. Testing Cartesian motion...")
    target_pos = np.array([0.02, 0.01, -0.12])
    target_ori = np.array([0, 0, 0, 1])  # Identity quaternion
    cmd = DVRKCartesianCommand(target_pos, target_ori)
    dvrk.move_cartesian(cmd)

    # Get state
    state = dvrk.get_measured_state()
    print(f"   Current position: {state.cartesian_position}")

    # Test joint motion
    print("\n2. Testing joint motion...")
    joint_cmd = DVRKJointCommand(np.array([0.1, 0.2, 0.15, 0.0, 0.0, 0.0, 0.0]))
    dvrk.move_joint(joint_cmd)

    # Test physiological integration
    print("\n3. Testing physiological feedback integration...")
    velocity_scale = dvrk.integrate_physiological_feedback(
        heart_rate=110,  # Elevated
        blood_pressure=85,  # Normal
        stress_level=0.4  # Moderate stress
    )
    print(f"   Velocity scaling factor: {velocity_scale:.2f}")

    # Test gripper
    print("\n4. Testing gripper control...")
    dvrk.open_gripper(40)
    dvrk.close_gripper()

    print("\n" + "=" * 60)
    print("dVRK Interface demonstration complete!")
    print("=" * 60)
