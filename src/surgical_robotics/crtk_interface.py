"""
CRTK (Collaborative Robotics Toolkit) Interface

Implements the CRTK standardized API for surgical robotics systems.
CRTK provides a common vocabulary and API for robot control.

References:
- Kazanzides et al. (2021) "The Collaborative Robotics Toolkit"
- CRTK Documentation: https://collaborative-robotics.github.io/
- IEEE RA-L Paper: https://ieeexplore.ieee.org/document/9367656

CRTK API Structure:
- Operating states: /operating_state, /state_command
- Measured values: /measured_cp, /measured_cv, /measured_cf, /measured_js, /measured_jv, /measured_jf
- Setpoint commands: /servo_cp, /servo_cv, /servo_cf, /servo_jp, /servo_jv, /servo_jf
- Move commands: /move_cp, /move_jr
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
import time


class CRTKOperatingState(Enum):
    """
    CRTK standardized operating states

    State machine transitions defined by CRTK specification
    """
    DISABLED = "DISABLED"
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    FAULT = "FAULT"


class CRTKCoordinateFrame(Enum):
    """CRTK coordinate frame specifications"""
    BASE = "base"
    WORLD = "world"
    LOCAL = "local"
    TOOL = "tool"


@dataclass
class CRTKMeasuredState:
    """
    CRTK measured state variables

    Follows CRTK naming conventions:
    - _cp: Cartesian Position
    - _cv: Cartesian Velocity
    - _cf: Cartesian Force/Wrench
    - _js: Joint State (positions)
    - _jv: Joint Velocities
    - _jf: Joint Forces/Torques
    """
    # Cartesian measurements
    measured_cp: Optional[np.ndarray] = None  # Position + orientation
    measured_cv: Optional[np.ndarray] = None  # Linear + angular velocity
    measured_cf: Optional[np.ndarray] = None  # Force + torque wrench

    # Joint measurements
    measured_js: Optional[np.ndarray] = None  # Joint states
    measured_jv: Optional[np.ndarray] = None  # Joint velocities
    measured_jf: Optional[np.ndarray] = None  # Joint forces/torques

    # Metadata
    timestamp: float = 0.0
    frame_id: str = "base"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/transmission"""
        return {
            'measured_cp': self.measured_cp.tolist() if self.measured_cp is not None else None,
            'measured_cv': self.measured_cv.tolist() if self.measured_cv is not None else None,
            'measured_cf': self.measured_cf.tolist() if self.measured_cf is not None else None,
            'measured_js': self.measured_js.tolist() if self.measured_js is not None else None,
            'measured_jv': self.measured_jv.tolist() if self.measured_jv is not None else None,
            'measured_jf': self.measured_jf.tolist() if self.measured_jf is not None else None,
            'timestamp': self.timestamp,
            'frame_id': self.frame_id,
        }


@dataclass
class CRTKConfiguration:
    """Configuration for CRTK interface"""
    robot_name: str = "surgical_robot"
    namespace: str = "/crtk"
    control_rate_hz: float = 100.0

    # Safety parameters
    max_cartesian_velocity: float = 0.1  # m/s
    max_cartesian_force: float = 10.0  # N
    max_joint_velocity: float = 0.5  # rad/s
    max_joint_torque: float = 5.0  # N·m

    # Physiological integration
    enable_adaptive_control: bool = True
    physio_scaling: bool = True


class CRTKInterface:
    """
    CRTK (Collaborative Robotics Toolkit) standardized interface

    Implements CRTK API specification for surgical robotics control.
    Compatible with any CRTK-compliant robot system.

    The CRTK API defines:
    1. Operating state management
    2. Measured values (feedback)
    3. Setpoint commands (servo)
    4. Move commands

    Example usage:
        >>> config = CRTKConfiguration(robot_name="PSM1")
        >>> crtk = CRTKInterface(config)
        >>> crtk.enable()
        >>>
        >>> # Servo control (continuous setpoint)
        >>> target_pose = np.array([0.0, 0.0, -0.1, 0, 0, 0, 1])  # pos + quat
        >>> crtk.servo_cp(target_pose)
        >>>
        >>> # Move command (goal-based)
        >>> crtk.move_cp(target_pose, blocking=True)
        >>>
        >>> # Get measurements
        >>> state = crtk.get_measured_state()
        >>> print(f"Position: {state.measured_cp}")
    """

    def __init__(self, config: CRTKConfiguration):
        self.config = config
        self.operating_state = CRTKOperatingState.DISABLED

        # Internal state (simulated)
        self._measured_cp = np.array([0.0, 0.0, -0.1, 0, 0, 0, 1])  # pos + quat
        self._measured_cv = np.zeros(6)  # linear + angular velocity
        self._measured_cf = np.zeros(6)  # force + torque
        self._measured_js = np.zeros(7)  # joint positions
        self._measured_jv = np.zeros(7)  # joint velocities
        self._measured_jf = np.zeros(7)  # joint forces

        # Command history
        self.command_log = []

        # Callbacks for state changes
        self.state_callbacks: Dict[str, List[Callable]] = {
            'operating_state': [],
            'measured_cp': [],
            'measured_js': [],
        }

        print(f"CRTK Interface initialized: {config.robot_name}")
        print(f"  Namespace: {config.namespace}")
        print(f"  Control rate: {config.control_rate_hz} Hz")

    # ========== Operating State Management ==========

    def enable(self) -> bool:
        """
        Enable the robot (CRTK state command)

        Publishes to: /{namespace}/{robot_name}/state_command
        Message: "ENABLED"
        """
        if self.operating_state == CRTKOperatingState.FAULT:
            print("ERROR: Cannot enable - robot in FAULT state. Clear fault first.")
            return False

        print(f"Enabling {self.config.robot_name}...")
        self.operating_state = CRTKOperatingState.ENABLED
        self._notify_callbacks('operating_state', self.operating_state)
        return True

    def disable(self) -> bool:
        """Disable the robot"""
        print(f"Disabling {self.config.robot_name}...")
        self.operating_state = CRTKOperatingState.DISABLED
        self._notify_callbacks('operating_state', self.operating_state)
        return True

    def pause(self) -> bool:
        """Pause robot motion"""
        if self.operating_state != CRTKOperatingState.ENABLED:
            print("ERROR: Robot must be enabled to pause")
            return False

        print(f"Pausing {self.config.robot_name}...")
        self.operating_state = CRTKOperatingState.PAUSED
        self._notify_callbacks('operating_state', self.operating_state)
        return True

    def resume(self) -> bool:
        """Resume robot motion from paused state"""
        if self.operating_state != CRTKOperatingState.PAUSED:
            print("ERROR: Robot must be paused to resume")
            return False

        print(f"Resuming {self.config.robot_name}...")
        self.operating_state = CRTKOperatingState.ENABLED
        self._notify_callbacks('operating_state', self.operating_state)
        return True

    def get_operating_state(self) -> CRTKOperatingState:
        """
        Get current operating state

        Subscribes to: /{namespace}/{robot_name}/operating_state
        """
        return self.operating_state

    # ========== Measured Values (Feedback) ==========

    def get_measured_state(self) -> CRTKMeasuredState:
        """
        Get all measured values

        In real system, subscribes to:
        - /{namespace}/{robot_name}/measured_cp
        - /{namespace}/{robot_name}/measured_cv
        - /{namespace}/{robot_name}/measured_cf
        - /{namespace}/{robot_name}/measured_js
        - /{namespace}/{robot_name}/measured_jv
        - /{namespace}/{robot_name}/measured_jf
        """
        return CRTKMeasuredState(
            measured_cp=self._measured_cp.copy(),
            measured_cv=self._measured_cv.copy(),
            measured_cf=self._measured_cf.copy(),
            measured_js=self._measured_js.copy(),
            measured_jv=self._measured_jv.copy(),
            measured_jf=self._measured_jf.copy(),
            timestamp=time.time(),
            frame_id="base",
        )

    def get_measured_cp(self) -> np.ndarray:
        """Get measured Cartesian position (pose)"""
        return self._measured_cp.copy()

    def get_measured_cv(self) -> np.ndarray:
        """Get measured Cartesian velocity (twist)"""
        return self._measured_cv.copy()

    def get_measured_cf(self) -> np.ndarray:
        """Get measured Cartesian force (wrench)"""
        return self._measured_cf.copy()

    def get_measured_js(self) -> np.ndarray:
        """Get measured joint state (positions)"""
        return self._measured_js.copy()

    def get_measured_jv(self) -> np.ndarray:
        """Get measured joint velocities"""
        return self._measured_jv.copy()

    def get_measured_jf(self) -> np.ndarray:
        """Get measured joint forces/torques"""
        return self._measured_jf.copy()

    # ========== Setpoint Commands (Servo) ==========

    def servo_cp(self, pose: np.ndarray, frame: CRTKCoordinateFrame = CRTKCoordinateFrame.BASE) -> bool:
        """
        Servo Cartesian position (continuous setpoint)

        Publishes to: /{namespace}/{robot_name}/servo_cp
        Message type: geometry_msgs/PoseStamped

        Args:
            pose: 7-element array [x, y, z, qx, qy, qz, qw]
            frame: Reference frame

        Returns:
            Success flag
        """
        if self.operating_state != CRTKOperatingState.ENABLED:
            print("ERROR: Robot not enabled")
            return False

        # Apply safety checks
        if not self._check_cartesian_limits(pose):
            print("ERROR: Pose outside safety limits")
            return False

        # Update simulated state
        self._measured_cp = pose.copy()

        # Log command
        self._log_command('servo_cp', pose, frame)

        return True

    def servo_cv(self, velocity: np.ndarray) -> bool:
        """
        Servo Cartesian velocity (twist)

        Publishes to: /{namespace}/{robot_name}/servo_cv
        Message type: geometry_msgs/TwistStamped

        Args:
            velocity: 6-element array [vx, vy, vz, wx, wy, wz]
        """
        if self.operating_state != CRTKOperatingState.ENABLED:
            return False

        # Safety check
        linear_vel = np.linalg.norm(velocity[:3])
        if linear_vel > self.config.max_cartesian_velocity:
            print(f"ERROR: Velocity {linear_vel:.3f} exceeds limit {self.config.max_cartesian_velocity}")
            return False

        self._measured_cv = velocity.copy()
        self._log_command('servo_cv', velocity)
        return True

    def servo_cf(self, wrench: np.ndarray) -> bool:
        """
        Servo Cartesian force/wrench

        Publishes to: /{namespace}/{robot_name}/servo_cf
        Message type: geometry_msgs/WrenchStamped

        Args:
            wrench: 6-element array [fx, fy, fz, tx, ty, tz]
        """
        if self.operating_state != CRTKOperatingState.ENABLED:
            return False

        # Safety check
        force_mag = np.linalg.norm(wrench[:3])
        if force_mag > self.config.max_cartesian_force:
            print(f"ERROR: Force {force_mag:.3f} exceeds limit {self.config.max_cartesian_force}")
            return False

        self._measured_cf = wrench.copy()
        self._log_command('servo_cf', wrench)
        return True

    def servo_jp(self, joint_positions: np.ndarray) -> bool:
        """
        Servo joint positions

        Publishes to: /{namespace}/{robot_name}/servo_jp
        Message type: sensor_msgs/JointState
        """
        if self.operating_state != CRTKOperatingState.ENABLED:
            return False

        self._measured_js = joint_positions.copy()
        self._log_command('servo_jp', joint_positions)
        return True

    def servo_jv(self, joint_velocities: np.ndarray) -> bool:
        """Servo joint velocities"""
        if self.operating_state != CRTKOperatingState.ENABLED:
            return False

        # Safety check
        max_vel = np.max(np.abs(joint_velocities))
        if max_vel > self.config.max_joint_velocity:
            print(f"ERROR: Joint velocity {max_vel:.3f} exceeds limit")
            return False

        self._measured_jv = joint_velocities.copy()
        self._log_command('servo_jv', joint_velocities)
        return True

    def servo_jf(self, joint_efforts: np.ndarray) -> bool:
        """Servo joint forces/torques"""
        if self.operating_state != CRTKOperatingState.ENABLED:
            return False

        # Safety check
        max_torque = np.max(np.abs(joint_efforts))
        if max_torque > self.config.max_joint_torque:
            print(f"ERROR: Joint torque {max_torque:.3f} exceeds limit")
            return False

        self._measured_jf = joint_efforts.copy()
        self._log_command('servo_jf', joint_efforts)
        return True

    # ========== Move Commands (Goal-based) ==========

    def move_cp(self, pose: np.ndarray, blocking: bool = False) -> bool:
        """
        Move to Cartesian position (goal-based motion)

        Publishes to: /{namespace}/{robot_name}/move_cp
        Message type: geometry_msgs/PoseStamped

        Unlike servo_cp, this is a goal command that plans a trajectory
        and executes until reaching the goal.

        Args:
            pose: Target pose [x, y, z, qx, qy, qz, qw]
            blocking: If True, wait until motion complete
        """
        if self.operating_state != CRTKOperatingState.ENABLED:
            return False

        if not self._check_cartesian_limits(pose):
            return False

        print(f"Moving to Cartesian pose: {pose[:3]}")  # Print position only

        # Simulate motion (in real system, trajectory planning occurs)
        self._measured_cp = pose.copy()
        self._log_command('move_cp', pose)

        if blocking:
            # In real system, wait for motion to complete
            time.sleep(0.1)  # Simulate motion time

        return True

    def move_jr(self, joint_positions: np.ndarray, blocking: bool = False) -> bool:
        """
        Move to joint position (goal-based motion)

        Publishes to: /{namespace}/{robot_name}/move_jr
        Message type: sensor_msgs/JointState
        """
        if self.operating_state != CRTKOperatingState.ENABLED:
            return False

        print(f"Moving to joint positions: {joint_positions}")

        self._measured_js = joint_positions.copy()
        self._log_command('move_jr', joint_positions)

        if blocking:
            time.sleep(0.1)

        return True

    # ========== Physiological Integration ==========

    def integrate_physiological_state(
        self,
        heart_rate: float,
        blood_pressure: float,
        oxygen_saturation: float,
        stress_index: float
    ) -> Dict[str, float]:
        """
        Integrate physiological monitoring into robot control

        Modulates control parameters based on patient physiology

        Args:
            heart_rate: HR in bpm
            blood_pressure: MAP in mmHg
            oxygen_saturation: SpO2 (0-100%)
            stress_index: Normalized stress (0-1)

        Returns:
            Dictionary of scaling factors for control
        """
        # Initialize scaling factors
        velocity_scale = 1.0
        force_scale = 1.0
        safety_margin = 0.0

        # Modulate based on heart rate
        if heart_rate > 120:  # Tachycardia
            velocity_scale *= 0.7
            safety_margin += 0.2
        elif heart_rate < 50:  # Bradycardia
            velocity_scale *= 0.8
            safety_margin += 0.15

        # Modulate based on blood pressure
        if blood_pressure > 110:  # Hypertension
            force_scale *= 0.8
            safety_margin += 0.1
        elif blood_pressure < 70:  # Hypotension
            velocity_scale *= 0.6
            force_scale *= 0.7
            safety_margin += 0.3

        # Modulate based on oxygen saturation
        if oxygen_saturation < 90:  # Hypoxemia
            velocity_scale *= 0.5
            force_scale *= 0.6
            safety_margin += 0.4

        # Modulate based on stress
        velocity_scale *= (1.0 - 0.3 * stress_index)
        force_scale *= (1.0 - 0.2 * stress_index)

        return {
            'velocity_scale': velocity_scale,
            'force_scale': force_scale,
            'safety_margin': safety_margin,
            'recommended_pause': safety_margin > 0.5,
        }

    # ========== Helper Methods ==========

    def _check_cartesian_limits(self, pose: np.ndarray) -> bool:
        """Check if Cartesian pose is within safe limits"""
        # Simplified workspace check
        position = pose[:3]
        if np.linalg.norm(position) > 0.3:  # 30cm from origin
            return False
        return True

    def _log_command(self, command_type: str, data: Any, frame: CRTKCoordinateFrame = None):
        """Log command for debugging/analysis"""
        self.command_log.append({
            'timestamp': time.time(),
            'type': command_type,
            'data': data,
            'frame': frame.value if frame else None,
        })

    def _notify_callbacks(self, event_type: str, data: Any):
        """Notify registered callbacks of state changes"""
        if event_type in self.state_callbacks:
            for callback in self.state_callbacks[event_type]:
                callback(data)

    def register_callback(self, event_type: str, callback: Callable):
        """Register callback for state changes"""
        if event_type in self.state_callbacks:
            self.state_callbacks[event_type].append(callback)

    def get_command_history(self, command_type: Optional[str] = None) -> List[Dict]:
        """Get command history, optionally filtered by type"""
        if command_type:
            return [cmd for cmd in self.command_log if cmd['type'] == command_type]
        return self.command_log


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("CRTK (Collaborative Robotics Toolkit) Interface Demo")
    print("=" * 60)

    # Create configuration
    config = CRTKConfiguration(
        robot_name="PSM1",
        enable_adaptive_control=True,
    )

    # Initialize interface
    crtk = CRTKInterface(config)

    # State management
    print("\n1. Testing state management...")
    crtk.enable()
    print(f"   Operating state: {crtk.get_operating_state()}")

    # Servo commands
    print("\n2. Testing servo commands...")
    target_pose = np.array([0.05, 0.02, -0.15, 0, 0, 0, 1])
    crtk.servo_cp(target_pose)
    state = crtk.get_measured_state()
    print(f"   Current pose: {state.measured_cp[:3]}")

    # Move commands
    print("\n3. Testing move commands...")
    goal_pose = np.array([0.0, 0.0, -0.1, 0, 0, 0, 1])
    crtk.move_cp(goal_pose, blocking=True)

    # Physiological integration
    print("\n4. Testing physiological integration...")
    physio_modulation = crtk.integrate_physiological_state(
        heart_rate=105,
        blood_pressure=95,
        oxygen_saturation=97,
        stress_index=0.3,
    )
    print(f"   Velocity scale: {physio_modulation['velocity_scale']:.2f}")
    print(f"   Force scale: {physio_modulation['force_scale']:.2f}")
    print(f"   Safety margin: {physio_modulation['safety_margin']:.2f}")

    # Velocity control
    print("\n5. Testing velocity servo...")
    velocity = np.array([0.01, 0.0, -0.02, 0, 0, 0])
    crtk.servo_cv(velocity)

    # Get command history
    print("\n6. Command history:")
    history = crtk.get_command_history()
    print(f"   Total commands: {len(history)}")
    for cmd in history[-3:]:  # Show last 3
        print(f"   - {cmd['type']} at {cmd['timestamp']:.2f}")

    print("\n" + "=" * 60)
    print("CRTK Interface demonstration complete!")
    print("=" * 60)
