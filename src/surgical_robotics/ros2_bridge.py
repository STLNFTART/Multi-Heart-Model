"""
ROS2 Communication Bridge

Provides ROS2 middleware communication for surgical robotics integration.
Bridges Multi-Heart-Model physiological simulations with ROS2-based
surgical robotics systems.

References:
- ROS 2 Documentation: https://docs.ros.org/
- geometry_msgs: https://docs.ros.org/en/api/geometry_msgs/html/index-msg.html
- sensor_msgs: https://docs.ros.org/en/api/sensor_msgs/html/index-msg.html
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Callable
from enum import Enum
import json
import time


class ROS2MessageType(Enum):
    """Standard ROS2 message types for surgical robotics"""
    # geometry_msgs
    POSE = "geometry_msgs/Pose"
    POSE_STAMPED = "geometry_msgs/PoseStamped"
    TWIST = "geometry_msgs/Twist"
    TWIST_STAMPED = "geometry_msgs/TwistStamped"
    WRENCH = "geometry_msgs/Wrench"
    WRENCH_STAMPED = "geometry_msgs/WrenchStamped"
    TRANSFORM = "geometry_msgs/Transform"
    TRANSFORM_STAMPED = "geometry_msgs/TransformStamped"

    # sensor_msgs
    JOINT_STATE = "sensor_msgs/JointState"
    IMAGE = "sensor_msgs/Image"
    POINT_CLOUD = "sensor_msgs/PointCloud2"

    # std_msgs
    STRING = "std_msgs/String"
    FLOAT64 = "std_msgs/Float64"
    BOOL = "std_msgs/Bool"

    # Custom physiological messages
    HEART_RATE = "physio_msgs/HeartRate"
    BLOOD_PRESSURE = "physio_msgs/BloodPressure"
    PHYSIOLOGICAL_STATE = "physio_msgs/PhysiologicalState"


class ROS2QoS(Enum):
    """ROS2 Quality of Service profiles"""
    DEFAULT = "default"
    SENSOR_DATA = "sensor_data"
    SERVICES = "services"
    PARAMETERS = "parameters"
    SYSTEM_DEFAULT = "system_default"
    BEST_EFFORT = "best_effort"
    RELIABLE = "reliable"


@dataclass
class ROS2TopicConfig:
    """Configuration for a ROS2 topic"""
    name: str
    msg_type: ROS2MessageType
    qos: ROS2QoS = ROS2QoS.DEFAULT
    queue_size: int = 10
    is_publisher: bool = True  # True for publish, False for subscribe


@dataclass
class ROS2NodeConfig:
    """Configuration for ROS2 node"""
    node_name: str = "multi_heart_surgical_bridge"
    namespace: str = ""
    use_sim_time: bool = False
    parameter_overrides: Dict[str, Any] = field(default_factory=dict)


class ROS2Bridge:
    """
    ROS2 communication bridge for surgical robotics

    Provides pub/sub interface for ROS2 topics, enabling integration
    of Multi-Heart-Model physiological simulations with ROS2-based
    surgical robotics systems (dVRK, AMBF, etc.)

    Example usage:
        >>> config = ROS2NodeConfig(node_name="physio_bridge")
        >>> bridge = ROS2Bridge(config)
        >>> bridge.initialize()
        >>>
        >>> # Create publisher for physiological state
        >>> topic_config = ROS2TopicConfig(
        ...     name="/physio/heart_rate",
        ...     msg_type=ROS2MessageType.FLOAT64,
        ...     is_publisher=True
        ... )
        >>> bridge.create_topic(topic_config)
        >>>
        >>> # Publish heart rate
        >>> bridge.publish("/physio/heart_rate", {'data': 75.0})
        >>>
        >>> # Subscribe to robot state
        >>> bridge.subscribe("/dvrk/PSM1/measured_cp", callback_fn)
    """

    def __init__(self, config: ROS2NodeConfig):
        self.config = config
        self.initialized = False

        # Topic registries
        self.publishers: Dict[str, ROS2TopicConfig] = {}
        self.subscribers: Dict[str, ROS2TopicConfig] = {}
        self.callbacks: Dict[str, List[Callable]] = {}

        # Message queues (for simulation without actual ROS2)
        self.message_queue: Dict[str, List[Dict]] = {}

        # Statistics
        self.stats = {
            'messages_published': 0,
            'messages_received': 0,
            'start_time': time.time(),
        }

        print(f"ROS2 Bridge initialized")
        print(f"  Node: {config.node_name}")
        print(f"  Namespace: {config.namespace or '/'}")

    def initialize(self) -> bool:
        """
        Initialize ROS2 node

        In real system, calls:
        - rclpy.init()
        - rclpy.create_node()
        """
        print("Initializing ROS2 node...")
        self.initialized = True
        print("  ROS2 node active")
        return True

    def shutdown(self) -> bool:
        """Shutdown ROS2 node"""
        print("Shutting down ROS2 node...")
        self.initialized = False
        return True

    def create_publisher(
        self,
        topic_name: str,
        msg_type: ROS2MessageType,
        qos: ROS2QoS = ROS2QoS.DEFAULT
    ) -> bool:
        """
        Create ROS2 publisher

        Args:
            topic_name: Topic name (e.g., "/physio/heart_rate")
            msg_type: Message type
            qos: Quality of Service profile

        Returns:
            Success flag
        """
        if not self.initialized:
            print("ERROR: ROS2 node not initialized")
            return False

        config = ROS2TopicConfig(
            name=topic_name,
            msg_type=msg_type,
            qos=qos,
            is_publisher=True
        )

        self.publishers[topic_name] = config
        self.message_queue[topic_name] = []

        print(f"Created publisher: {topic_name} ({msg_type.value})")
        return True

    def create_subscriber(
        self,
        topic_name: str,
        msg_type: ROS2MessageType,
        callback: Callable,
        qos: ROS2QoS = ROS2QoS.DEFAULT
    ) -> bool:
        """
        Create ROS2 subscriber

        Args:
            topic_name: Topic name
            msg_type: Message type
            callback: Callback function for messages
            qos: Quality of Service profile
        """
        if not self.initialized:
            return False

        config = ROS2TopicConfig(
            name=topic_name,
            msg_type=msg_type,
            qos=qos,
            is_publisher=False
        )

        self.subscribers[topic_name] = config

        # Register callback
        if topic_name not in self.callbacks:
            self.callbacks[topic_name] = []
        self.callbacks[topic_name].append(callback)

        print(f"Created subscriber: {topic_name} ({msg_type.value})")
        return True

    def publish(self, topic_name: str, message: Dict[str, Any]) -> bool:
        """
        Publish message to topic

        Args:
            topic_name: Topic to publish to
            message: Message data as dictionary

        Returns:
            Success flag
        """
        if topic_name not in self.publishers:
            print(f"ERROR: No publisher for topic {topic_name}")
            return False

        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = time.time()

        # Store in queue (simulated)
        self.message_queue[topic_name].append(message)
        self.stats['messages_published'] += 1

        return True

    def spin_once(self, timeout_sec: float = 0.1) -> bool:
        """
        Process callbacks for one iteration

        In real ROS2, this calls rclpy.spin_once()

        Args:
            timeout_sec: Timeout for waiting
        """
        if not self.initialized:
            return False

        # Process any pending messages
        # In real system, ROS2 middleware handles this
        return True

    # ========== Message Creation Helpers ==========

    def create_pose_stamped_msg(
        self,
        position: np.ndarray,
        orientation: np.ndarray,
        frame_id: str = "base"
    ) -> Dict[str, Any]:
        """
        Create geometry_msgs/PoseStamped message

        Args:
            position: [x, y, z] in meters
            orientation: [qx, qy, qz, qw] quaternion
            frame_id: Reference frame

        Returns:
            Message dictionary
        """
        return {
            'header': {
                'stamp': {'sec': int(time.time()), 'nanosec': 0},
                'frame_id': frame_id,
            },
            'pose': {
                'position': {
                    'x': float(position[0]),
                    'y': float(position[1]),
                    'z': float(position[2]),
                },
                'orientation': {
                    'x': float(orientation[0]),
                    'y': float(orientation[1]),
                    'z': float(orientation[2]),
                    'w': float(orientation[3]),
                },
            },
        }

    def create_twist_msg(
        self,
        linear: np.ndarray,
        angular: np.ndarray
    ) -> Dict[str, Any]:
        """
        Create geometry_msgs/Twist message

        Args:
            linear: Linear velocity [vx, vy, vz]
            angular: Angular velocity [wx, wy, wz]
        """
        return {
            'linear': {
                'x': float(linear[0]),
                'y': float(linear[1]),
                'z': float(linear[2]),
            },
            'angular': {
                'x': float(angular[0]),
                'y': float(angular[1]),
                'z': float(angular[2]),
            },
        }

    def create_wrench_msg(
        self,
        force: np.ndarray,
        torque: np.ndarray
    ) -> Dict[str, Any]:
        """Create geometry_msgs/Wrench message"""
        return {
            'force': {
                'x': float(force[0]),
                'y': float(force[1]),
                'z': float(force[2]),
            },
            'torque': {
                'x': float(torque[0]),
                'y': float(torque[1]),
                'z': float(torque[2]),
            },
        }

    def create_joint_state_msg(
        self,
        joint_names: List[str],
        positions: np.ndarray,
        velocities: Optional[np.ndarray] = None,
        efforts: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Create sensor_msgs/JointState message

        Args:
            joint_names: List of joint names
            positions: Joint positions
            velocities: Joint velocities (optional)
            efforts: Joint efforts/torques (optional)
        """
        msg = {
            'header': {
                'stamp': {'sec': int(time.time()), 'nanosec': 0},
                'frame_id': '',
            },
            'name': joint_names,
            'position': positions.tolist(),
        }

        if velocities is not None:
            msg['velocity'] = velocities.tolist()
        if efforts is not None:
            msg['effort'] = efforts.tolist()

        return msg

    def create_physiological_state_msg(
        self,
        heart_rate: float,
        blood_pressure_systolic: float,
        blood_pressure_diastolic: float,
        oxygen_saturation: float,
        respiratory_rate: float
    ) -> Dict[str, Any]:
        """
        Create custom physiological state message

        Combines multiple physiological parameters
        """
        return {
            'header': {
                'stamp': {'sec': int(time.time()), 'nanosec': 0},
                'frame_id': 'patient',
            },
            'heart_rate': float(heart_rate),
            'blood_pressure': {
                'systolic': float(blood_pressure_systolic),
                'diastolic': float(blood_pressure_diastolic),
                'mean': float((blood_pressure_systolic + 2 * blood_pressure_diastolic) / 3),
            },
            'oxygen_saturation': float(oxygen_saturation),
            'respiratory_rate': float(respiratory_rate),
            'timestamp': time.time(),
        }

    # ========== Physiological Integration ==========

    def publish_physiological_state(
        self,
        topic_prefix: str = "/physio",
        heart_rate: float = 70.0,
        bp_systolic: float = 120.0,
        bp_diastolic: float = 80.0,
        spo2: float = 98.0,
        resp_rate: float = 16.0
    ) -> bool:
        """
        Publish physiological state to multiple topics

        Creates and publishes to:
        - {prefix}/heart_rate
        - {prefix}/blood_pressure
        - {prefix}/oxygen_saturation
        - {prefix}/state (combined)
        """
        # Individual topics
        topics = {
            f"{topic_prefix}/heart_rate": {'data': heart_rate},
            f"{topic_prefix}/oxygen_saturation": {'data': spo2},
        }

        for topic, data in topics.items():
            if topic not in self.publishers:
                self.create_publisher(topic, ROS2MessageType.FLOAT64)
            self.publish(topic, data)

        # Combined state
        combined_topic = f"{topic_prefix}/state"
        if combined_topic not in self.publishers:
            self.create_publisher(combined_topic, ROS2MessageType.PHYSIOLOGICAL_STATE)

        combined_msg = self.create_physiological_state_msg(
            heart_rate, bp_systolic, bp_diastolic, spo2, resp_rate
        )
        self.publish(combined_topic, combined_msg)

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get bridge statistics"""
        runtime = time.time() - self.stats['start_time']
        return {
            'runtime_seconds': runtime,
            'messages_published': self.stats['messages_published'],
            'messages_received': self.stats['messages_received'],
            'publish_rate': self.stats['messages_published'] / runtime if runtime > 0 else 0,
            'active_publishers': len(self.publishers),
            'active_subscribers': len(self.subscribers),
        }

    def export_topic_list(self, filename: str) -> bool:
        """Export list of topics to file"""
        topic_data = {
            'publishers': [
                {
                    'topic': name,
                    'type': config.msg_type.value,
                    'qos': config.qos.value,
                }
                for name, config in self.publishers.items()
            ],
            'subscribers': [
                {
                    'topic': name,
                    'type': config.msg_type.value,
                    'qos': config.qos.value,
                }
                for name, config in self.subscribers.items()
            ],
        }

        with open(filename, 'w') as f:
            json.dump(topic_data, f, indent=2)

        print(f"Topic list exported to {filename}")
        return True


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("ROS2 Communication Bridge Demo")
    print("=" * 60)

    # Create and initialize bridge
    config = ROS2NodeConfig(
        node_name="multi_heart_surgical_bridge",
        namespace="/multi_heart"
    )
    bridge = ROS2Bridge(config)
    bridge.initialize()

    # Create publishers
    print("\n1. Creating publishers...")
    bridge.create_publisher("/physio/heart_rate", ROS2MessageType.FLOAT64)
    bridge.create_publisher("/physio/blood_pressure", ROS2MessageType.FLOAT64)
    bridge.create_publisher("/robot/target_pose", ROS2MessageType.POSE_STAMPED)

    # Publish physiological data
    print("\n2. Publishing physiological state...")
    bridge.publish_physiological_state(
        heart_rate=75.0,
        bp_systolic=120.0,
        bp_diastolic=80.0,
        spo2=98.0,
        resp_rate=16.0
    )

    # Publish robot command
    print("\n3. Publishing robot command...")
    pose_msg = bridge.create_pose_stamped_msg(
        position=np.array([0.05, 0.02, -0.12]),
        orientation=np.array([0, 0, 0, 1]),
        frame_id="base"
    )
    bridge.publish("/robot/target_pose", pose_msg)

    # Create subscriber (with callback)
    print("\n4. Creating subscriber...")
    def robot_state_callback(msg):
        print(f"  Received robot state: {msg}")

    bridge.create_subscriber(
        "/robot/measured_cp",
        ROS2MessageType.POSE_STAMPED,
        robot_state_callback
    )

    # Get statistics
    print("\n5. Bridge statistics:")
    stats = bridge.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Export topic list
    print("\n6. Exporting topic list...")
    bridge.export_topic_list("ros2_topics.json")

    print("\n" + "=" * 60)
    print("ROS2 Bridge demonstration complete!")
    print("=" * 60)
