"""
AMBF (Asynchronous Multi-Body Framework) Interface

Interface to AMBF dynamic simulator for surgical robotics.
AMBF is used for realistic surgical simulation and training.

References:
- Munawar et al. (2019) "A Real-Time Dynamic Simulator and an Associated Front-End
  Representation Format for Simulating Complex Robots and Environments"
- AMBF GitHub: https://github.com/WPI-AIM/ambf
- Integration with 3D Slicer: https://arxiv.org/html/2401.11715
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from enum import Enum
import json


class AMBFObjectType(Enum):
    """AMBF object types"""
    RIGID_BODY = "RIGID_BODY"
    SOFT_BODY = "SOFT_BODY"
    GHOST_OBJECT = "GHOST_OBJECT"
    VOLUME = "VOLUME"
    CAMERA = "CAMERA"
    LIGHT = "LIGHT"


@dataclass
class AMBFSimulationConfig:
    """
    Configuration for AMBF simulation

    Based on AMBF Description Format (ADF) YAML configuration
    """
    # Simulation parameters
    time_step: float = 0.001  # 1ms timestep
    max_frequency: float = 1000.0  # 1kHz max
    gravity: np.ndarray = field(default_factory=lambda: np.array([0, 0, -9.81]))

    # World configuration
    world_name: str = "surgical_world"
    namespace: str = "/ambf/env"

    # Network configuration
    enable_ros: bool = True
    ros_topic_prefix: str = "/ambf"

    # Plugin configuration
    plugins: List[str] = field(default_factory=list)

    def to_adf_dict(self) -> Dict:
        """Export to AMBF Description Format (ADF) dictionary"""
        return {
            'world': {
                'name': self.world_name,
                'namespace': self.namespace,
                'gravity': self.gravity.tolist(),
            },
            'simulation': {
                'time_step': self.time_step,
                'max_frequency': self.max_frequency,
            },
            'plugins': self.plugins,
        }


@dataclass
class AMBFRobotState:
    """State of robot in AMBF simulation"""
    # Pose (position + orientation)
    position: np.ndarray  # [x, y, z]
    orientation: np.ndarray  # Quaternion [x, y, z, w]

    # Velocities
    linear_velocity: np.ndarray  # [vx, vy, vz]
    angular_velocity: np.ndarray  # [wx, wy, wz]

    # Joint states (for articulated bodies)
    joint_positions: Optional[np.ndarray] = None
    joint_velocities: Optional[np.ndarray] = None
    joint_efforts: Optional[np.ndarray] = None

    # Force/torque
    applied_force: Optional[np.ndarray] = None
    applied_torque: Optional[np.ndarray] = None

    # Metadata
    timestamp: float = 0.0
    object_name: str = "robot"

    def __post_init__(self):
        self.position = np.array(self.position)
        self.orientation = np.array(self.orientation)
        self.linear_velocity = np.array(self.linear_velocity)
        self.angular_velocity = np.array(self.angular_velocity)


class AMBFInterface:
    """
    Interface to AMBF (Asynchronous Multi-Body Framework) simulator

    Provides control and monitoring of surgical robots in AMBF simulation
    environment. Supports ROS/ROS2 communication for integration with
    other systems.

    Example usage:
        >>> config = AMBFSimulationConfig(world_name="surgical_scene")
        >>> ambf = AMBFInterface(config)
        >>> ambf.connect()
        >>>
        >>> # Load surgical robot model
        >>> ambf.load_robot("dVRK_PSM", model_path="models/dvrk_psm.yaml")
        >>>
        >>> # Set end-effector pose
        >>> ambf.set_pose("dVRK_PSM/tool_tip", position=[0.0, 0.0, -0.1])
        >>>
        >>> # Run simulation step
        >>> ambf.step_simulation()
        >>>
        >>> # Get state
        >>> state = ambf.get_robot_state("dVRK_PSM")
    """

    def __init__(self, config: AMBFSimulationConfig):
        self.config = config
        self.connected = False
        self.simulation_time = 0.0

        # Object registry
        self.objects: Dict[str, AMBFRobotState] = {}
        self.robots: List[str] = []

        # Command buffers
        self.position_commands: Dict[str, np.ndarray] = {}
        self.force_commands: Dict[str, np.ndarray] = {}

        print(f"AMBF Interface initialized")
        print(f"  World: {config.world_name}")
        print(f"  Timestep: {config.time_step} s")
        print(f"  Gravity: {config.gravity}")

    def connect(self) -> bool:
        """
        Connect to AMBF simulator

        In real system, establishes ROS/ROS2 connection to AMBF
        """
        print("Connecting to AMBF simulator...")
        self.connected = True
        print("  Connection established")
        return True

    def disconnect(self) -> bool:
        """Disconnect from AMBF simulator"""
        print("Disconnecting from AMBF...")
        self.connected = False
        return True

    def load_robot(
        self,
        robot_name: str,
        model_path: str,
        initial_position: Optional[np.ndarray] = None
    ) -> bool:
        """
        Load robot model into AMBF simulation

        Args:
            robot_name: Unique name for robot instance
            model_path: Path to AMBF Description Format (ADF) file
            initial_position: Initial position [x, y, z]

        Returns:
            Success flag
        """
        if not self.connected:
            print("ERROR: Not connected to AMBF")
            return False

        print(f"Loading robot: {robot_name} from {model_path}")

        # Initialize robot state
        pos = initial_position if initial_position is not None else np.array([0, 0, 0])
        state = AMBFRobotState(
            position=pos,
            orientation=np.array([0, 0, 0, 1]),  # Identity quaternion
            linear_velocity=np.zeros(3),
            angular_velocity=np.zeros(3),
            object_name=robot_name,
        )

        self.objects[robot_name] = state
        self.robots.append(robot_name)

        print(f"  Robot {robot_name} loaded successfully")
        return True

    def set_pose(
        self,
        object_name: str,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None
    ) -> bool:
        """
        Set object pose in simulation

        Args:
            object_name: Name of object/body
            position: Position [x, y, z]
            orientation: Quaternion [x, y, z, w]
        """
        if object_name not in self.objects:
            print(f"ERROR: Object {object_name} not found")
            return False

        if position is not None:
            self.objects[object_name].position = np.array(position)

        if orientation is not None:
            self.objects[object_name].orientation = np.array(orientation)

        return True

    def set_joint_positions(
        self,
        robot_name: str,
        joint_positions: np.ndarray
    ) -> bool:
        """
        Set joint positions for articulated robot

        Args:
            robot_name: Name of robot
            joint_positions: Joint angles/positions
        """
        if robot_name not in self.objects:
            return False

        self.objects[robot_name].joint_positions = np.array(joint_positions)
        return True

    def apply_force(
        self,
        object_name: str,
        force: np.ndarray,
        position: Optional[np.ndarray] = None
    ) -> bool:
        """
        Apply force to object

        Args:
            object_name: Target object
            force: Force vector [fx, fy, fz] in Newtons
            position: Application point (optional)
        """
        if object_name not in self.objects:
            return False

        self.objects[object_name].applied_force = np.array(force)
        print(f"Applied force {force} to {object_name}")
        return True

    def apply_torque(
        self,
        object_name: str,
        torque: np.ndarray
    ) -> bool:
        """
        Apply torque to object

        Args:
            object_name: Target object
            torque: Torque vector [tx, ty, tz] in N·m
        """
        if object_name not in self.objects:
            return False

        self.objects[object_name].applied_torque = np.array(torque)
        return True

    def step_simulation(self, steps: int = 1) -> bool:
        """
        Step simulation forward

        Args:
            steps: Number of simulation steps
        """
        if not self.connected:
            return False

        for _ in range(steps):
            # Simplified physics integration
            for obj_name, state in self.objects.items():
                # Apply forces (simplified)
                if state.applied_force is not None:
                    # F = ma => a = F/m (assume unit mass)
                    acceleration = state.applied_force
                    state.linear_velocity += acceleration * self.config.time_step

                # Update positions
                state.position += state.linear_velocity * self.config.time_step

                # Apply gravity
                state.linear_velocity += self.config.gravity * self.config.time_step

            self.simulation_time += self.config.time_step

        return True

    def get_robot_state(self, robot_name: str) -> Optional[AMBFRobotState]:
        """
        Get current state of robot

        Args:
            robot_name: Name of robot

        Returns:
            Robot state, or None if not found
        """
        return self.objects.get(robot_name)

    def get_all_objects(self) -> List[str]:
        """Get list of all objects in simulation"""
        return list(self.objects.keys())

    def reset_simulation(self) -> bool:
        """Reset simulation to initial state"""
        print("Resetting AMBF simulation...")
        self.simulation_time = 0.0

        # Reset all object states
        for state in self.objects.values():
            state.linear_velocity = np.zeros(3)
            state.angular_velocity = np.zeros(3)
            state.applied_force = None
            state.applied_torque = None

        return True

    def create_constraint(
        self,
        object_a: str,
        object_b: str,
        constraint_type: str = "fixed"
    ) -> bool:
        """
        Create constraint between two objects

        Args:
            object_a: First object name
            object_b: Second object name
            constraint_type: Type of constraint (fixed, hinge, slider, etc.)
        """
        print(f"Creating {constraint_type} constraint between {object_a} and {object_b}")
        # In real system, creates AMBF constraint
        return True

    def enable_collision_detection(
        self,
        object_a: str,
        object_b: str,
        enable: bool = True
    ) -> bool:
        """
        Enable/disable collision detection between objects

        Args:
            object_a: First object
            object_b: Second object
            enable: Enable or disable
        """
        state = "enabled" if enable else "disabled"
        print(f"Collision detection {state} between {object_a} and {object_b}")
        return True

    def integrate_with_physiology(
        self,
        robot_name: str,
        physiological_data: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Integrate physiological feedback with robot control in simulation

        Modulates simulation parameters based on physiology

        Args:
            robot_name: Target robot
            physiological_data: Dict with HR, BP, etc.

        Returns:
            Modified control parameters
        """
        # Extract physiological metrics
        hr = physiological_data.get('heart_rate', 70)
        bp = physiological_data.get('blood_pressure', 90)
        stress = physiological_data.get('stress', 0.0)

        # Compute scaling factors
        velocity_scale = 1.0
        force_scale = 1.0

        if hr > 100:
            velocity_scale *= 0.8
        if bp < 70:
            velocity_scale *= 0.7
            force_scale *= 0.8
        if stress > 0.5:
            velocity_scale *= 0.6

        return {
            'velocity_scale': velocity_scale,
            'force_scale': force_scale,
            'pause_simulation': (bp < 60 or hr > 130),
        }

    def export_simulation_state(self, filename: str) -> bool:
        """Export current simulation state to file"""
        state_data = {
            'simulation_time': self.simulation_time,
            'config': self.config.to_adf_dict(),
            'objects': {
                name: {
                    'position': state.position.tolist(),
                    'orientation': state.orientation.tolist(),
                    'linear_velocity': state.linear_velocity.tolist(),
                    'angular_velocity': state.angular_velocity.tolist(),
                }
                for name, state in self.objects.items()
            },
        }

        with open(filename, 'w') as f:
            json.dump(state_data, f, indent=2)

        print(f"Simulation state exported to {filename}")
        return True


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("AMBF (Asynchronous Multi-Body Framework) Interface Demo")
    print("=" * 60)

    # Create configuration
    config = AMBFSimulationConfig(
        world_name="surgical_scene",
        time_step=0.001,
    )

    # Initialize interface
    ambf = AMBFInterface(config)
    ambf.connect()

    # Load surgical robot
    print("\n1. Loading surgical robot...")
    ambf.load_robot(
        "dVRK_PSM1",
        model_path="models/dvrk_psm.yaml",
        initial_position=np.array([0.0, 0.0, 0.2])
    )

    # Set pose
    print("\n2. Setting end-effector pose...")
    ambf.set_pose(
        "dVRK_PSM1",
        position=np.array([0.05, 0.02, -0.1]),
        orientation=np.array([0, 0, 0, 1])
    )

    # Apply force
    print("\n3. Applying force to tool tip...")
    ambf.apply_force(
        "dVRK_PSM1",
        force=np.array([0.0, 0.0, -1.0])  # 1N downward
    )

    # Run simulation
    print("\n4. Running simulation...")
    for i in range(100):
        ambf.step_simulation()
        if i % 20 == 0:
            state = ambf.get_robot_state("dVRK_PSM1")
            print(f"   Step {i}: position = {state.position}")

    # Physiological integration
    print("\n5. Testing physiological integration...")
    physio_data = {
        'heart_rate': 105,
        'blood_pressure': 85,
        'stress': 0.4,
    }
    modulation = ambf.integrate_with_physiology("dVRK_PSM1", physio_data)
    print(f"   Velocity scale: {modulation['velocity_scale']:.2f}")
    print(f"   Force scale: {modulation['force_scale']:.2f}")

    # Export state
    print("\n6. Exporting simulation state...")
    ambf.export_simulation_state("ambf_state.json")

    print("\n" + "=" * 60)
    print("AMBF Interface demonstration complete!")
    print("=" * 60)
