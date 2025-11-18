# Surgical Robotics Integration Guide

**Multi-Heart-Model Surgical Robotics Interface**

This guide covers the integration of Multi-Heart-Model physiological simulations with surgical robotics platforms.

---

## Table of Contents

1. [Overview](#overview)
2. [Supported Platforms](#supported-platforms)
3. [Architecture](#architecture)
4. [Quick Start](#quick-start)
5. [Interface Documentation](#interface-documentation)
6. [Examples](#examples)
7. [Safety Considerations](#safety-considerations)
8. [References](#references)

---

## Overview

The Surgical Robotics Integration module bridges Multi-Heart-Model's physiological simulation capabilities with major surgical robotics platforms. This enables:

- **Physiologically-aware robot control**: Robot behavior adapts to patient state
- **Real-time safety monitoring**: Multi-level alerts based on vital signs
- **Standardized interfaces**: Support for dVRK, CRTK, AMBF, and ROS2
- **Simulation and hardware**: Works with both simulators and real robots

### Key Features

✅ **dVRK (da Vinci Research Kit)** integration with cisst-SAW
✅ **CRTK (Collaborative Robotics Toolkit)** standardized API
✅ **AMBF (Asynchronous Multi-Body Framework)** simulator interface
✅ **ROS2 middleware** communication bridge
✅ **Physiological feedback controller** for adaptive robot control
✅ **Heart-Brain Coupling Model (HBCM)** integration

---

## Supported Platforms

### 1. dVRK (da Vinci Research Kit)

**Description**: Open-source research platform based on first-generation da Vinci surgical system.

**Features**:
- Patient Side Manipulators (PSM1, PSM2, PSM3)
- Master Tool Manipulators (MTM, MTML, MTMR)
- Endoscopic Camera Manipulator (ECM)
- Real-time control at 100Hz
- Cartesian and joint space control
- Force/wrench feedback

**References**:
- Kazanzides et al. (2014) "An open-source research kit for the da Vinci Surgical System"
- GitHub: https://github.com/jhu-dvrk
- Wiki: https://github.com/jhu-dvrk/sawIntuitiveResearchKit/wiki

### 2. CRTK (Collaborative Robotics Toolkit)

**Description**: Standardized API vocabulary for surgical robotics.

**Features**:
- Operating state management (DISABLED, ENABLED, PAUSED, FAULT)
- Measured values (position, velocity, force)
- Setpoint commands (servo)
- Move commands (goal-based)
- Standard ROS/ROS2 message types

**References**:
- Kazanzides et al. (2021) "The Collaborative Robotics Toolkit"
- IEEE RA-L Paper: https://ieeexplore.ieee.org/document/9367656
- Documentation: https://collaborative-robotics.github.io/

### 3. AMBF (Asynchronous Multi-Body Framework)

**Description**: Real-time dynamic simulator for surgical robotics.

**Features**:
- Realistic physics simulation
- dVRK manipulator models
- Multi-body dynamics
- Collision detection
- ROS/ROS2 integration
- 3D Slicer compatibility

**References**:
- Munawar et al. (2019) "A Real-Time Dynamic Simulator..."
- GitHub: https://github.com/WPI-AIM/ambf
- Integration paper: https://arxiv.org/html/2401.11715

### 4. ROS2 Communication Bridge

**Description**: Middleware for inter-system communication.

**Features**:
- Standard message types (geometry_msgs, sensor_msgs)
- Custom physiological messages
- Quality of Service (QoS) profiles
- Topic publishers and subscribers
- Real-time communication

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Heart-Model HBCM                       │
│          (Heart-Brain Coupling Physiological Model)              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Physiological Controller                            │
│  • Real-time vital signs monitoring                              │
│  • Alert level determination (Normal/Caution/Warning/Critical)   │
│  • Control constraint computation                                │
│  • Safety enforcement                                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ROS2 Communication Bridge                      │
│  • Publish physiological state                                   │
│  • Subscribe to robot feedback                                   │
│  • Standard message formats                                      │
└───────────┬─────────────────┬──────────────────┬────────────────┘
            │                 │                  │
            ▼                 ▼                  ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  dVRK Interface  │ │CRTK Interface│ │ AMBF Interface   │
│  • PSM control   │ │• Servo/Move  │ │ • Simulation     │
│  • Kinematics    │ │• Standard API│ │ • Physics        │
│  • Safety limits │ │• Multi-robot │ │ • Collision      │
└──────────────────┘ └──────────────┘ └──────────────────┘
            │                 │                  │
            ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              Hardware / Simulation Environment                   │
│  • Actual dVRK robot hardware                                    │
│  • AMBF physics simulator                                        │
│  • Other CRTK-compatible robots                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Physiological Monitoring**: HBCM model simulates patient cardiovascular state
2. **State Assessment**: Physiological controller evaluates vital signs
3. **Constraint Computation**: Safety constraints computed based on patient state
4. **Control Modulation**: Robot control parameters scaled by constraints
5. **Robot Command**: Commands sent to robot via appropriate interface
6. **Feedback Loop**: Robot state fed back to update physiological model

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/STLNFTART/Multi-Heart-Model.git
cd Multi-Heart-Model

# Install dependencies (if needed)
# pip install numpy  # Core only requires NumPy
```

### Basic Example: dVRK Control

```python
from src.surgical_robotics import (
    DVRKInterface,
    DVRKConfiguration,
    DVRKArmType,
    DVRKCartesianCommand,
    PhysiologicalController,
)
import numpy as np

# Initialize dVRK
config = DVRKConfiguration(arm_type=DVRKArmType.PSM1)
dvrk = DVRKInterface(config)
dvrk.enable()
dvrk.home()

# Initialize physiological controller
physio = PhysiologicalController()

# Get current patient state
patient_state = physio.get_physiological_feedback()

# Compute safe control constraints
constraints = physio.compute_control_constraints(patient_state)

# Move robot (scaled by physiological state)
if not constraints.emergency_stop:
    target_pos = np.array([0.05, 0.02, -0.12])
    target_ori = np.array([0, 0, 0, 1])
    cmd = DVRKCartesianCommand(target_pos, target_ori)
    dvrk.move_cartesian(cmd)

# Get current robot state
robot_state = dvrk.get_measured_state()
print(f"Position: {robot_state.cartesian_position}")
```

### Basic Example: CRTK Interface

```python
from src.surgical_robotics import CRTKInterface, CRTKConfiguration
import numpy as np

# Initialize CRTK interface
config = CRTKConfiguration(robot_name="PSM1")
crtk = CRTKInterface(config)
crtk.enable()

# Servo control (continuous setpoint)
pose = np.array([0.0, 0.0, -0.1, 0, 0, 0, 1])  # pos + quaternion
crtk.servo_cp(pose)

# Move command (goal-based)
goal = np.array([0.05, 0.02, -0.15, 0, 0, 0, 1])
crtk.move_cp(goal, blocking=True)

# Get measured state
state = crtk.get_measured_state()
print(f"Current pose: {state.measured_cp}")
```

### Basic Example: Complete Integration

```python
from src.surgical_robotics import *
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel

# 1. Create physiological model
hbcm = HeartBrainCouplingModel(
    neural_model=FitzHughNagumo(),
    cardiac_model=VanDerPolOscillator()
)

# 2. Create physiological controller
controller = PhysiologicalController(hbcm_model=hbcm)

# 3. Initialize robot
dvrk = DVRKInterface(DVRKConfiguration())
dvrk.enable()

# 4. Control loop
for step in range(100):
    # Get physiological state
    physio_state = controller.get_physiological_feedback()

    # Compute constraints
    constraints = controller.compute_control_constraints(physio_state)

    # Apply to robot
    velocity_scale = dvrk.integrate_physiological_feedback(
        physio_state.heart_rate,
        physio_state.mean_arterial_pressure,
        physio_state.stress_index
    )

    # Command robot (with scaled velocity)
    # ... robot motion commands ...
```

---

## Interface Documentation

### 1. dVRK Interface (`dvrk_interface.py`)

#### Key Classes

**`DVRKConfiguration`**: Configuration for dVRK arm
- `arm_type`: PSM1, PSM2, PSM3, MTM, MTML, MTMR, ECM
- `control_rate_hz`: Control loop frequency (default: 100 Hz)
- `workspace_limits`: Safety boundaries
- `enable_physio_feedback`: Enable physiological integration

**`DVRKInterface`**: Main interface class
- `enable()`: Enable arm
- `disable()`: Disable arm
- `home()`: Home arm
- `move_cartesian(cmd)`: Cartesian motion
- `move_joint(cmd)`: Joint motion
- `set_wrench(force, torque)`: Force control
- `open_gripper(angle)`: Gripper control
- `get_measured_state()`: Get current state
- `integrate_physiological_feedback(hr, bp, stress)`: Physiological adaptation

#### Example Commands

```python
# Cartesian motion
cmd = DVRKCartesianCommand(
    position=np.array([0.05, 0.02, -0.12]),
    orientation=np.array([0, 0, 0, 1]),  # quaternion
    reference_frame="base"
)
dvrk.move_cartesian(cmd)

# Joint motion
cmd = DVRKJointCommand(
    joint_positions=np.array([0.1, 0.2, 0.15, 0, 0, 0, 0])
)
dvrk.move_joint(cmd)

# Force control
dvrk.set_wrench(
    force=np.array([0, 0, -1.0]),  # 1N downward
    torque=np.array([0, 0, 0])
)
```

### 2. CRTK Interface (`crtk_interface.py`)

#### CRTK API Structure

**Operating States**:
- `DISABLED`: Robot disabled
- `ENABLED`: Robot enabled and operational
- `PAUSED`: Motion paused
- `FAULT`: Error state

**Command Types**:
- **Servo commands** (`servo_*`): Continuous setpoints
- **Move commands** (`move_*`): Goal-based motion
- **Measured values** (`measured_*`): Feedback

#### Key Methods

```python
# State management
crtk.enable()
crtk.disable()
crtk.pause()
crtk.resume()

# Servo commands
crtk.servo_cp(pose)         # Cartesian position
crtk.servo_cv(velocity)     # Cartesian velocity
crtk.servo_cf(wrench)       # Cartesian force
crtk.servo_jp(joints)       # Joint positions
crtk.servo_jv(velocities)   # Joint velocities
crtk.servo_jf(efforts)      # Joint forces

# Move commands
crtk.move_cp(pose, blocking=True)    # Cartesian move
crtk.move_jr(joints, blocking=True)  # Joint move

# Measured values
state = crtk.get_measured_state()
pose = crtk.get_measured_cp()
velocity = crtk.get_measured_cv()
```

### 3. AMBF Interface (`ambf_interface.py`)

#### Key Methods

```python
# Initialize
ambf = AMBFInterface(AMBFSimulationConfig())
ambf.connect()

# Load robot
ambf.load_robot("dVRK_PSM", model_path="models/dvrk.yaml")

# Control
ambf.set_pose("dVRK_PSM", position=[0, 0, -0.1])
ambf.set_joint_positions("dVRK_PSM", joint_positions)
ambf.apply_force("dVRK_PSM", force=[0, 0, -1])

# Simulation
ambf.step_simulation(steps=100)

# State
state = ambf.get_robot_state("dVRK_PSM")
print(state.position, state.orientation)
```

### 4. ROS2 Bridge (`ros2_bridge.py`)

#### Creating Publishers/Subscribers

```python
# Initialize bridge
bridge = ROS2Bridge(ROS2NodeConfig())
bridge.initialize()

# Create publisher
bridge.create_publisher(
    "/physio/heart_rate",
    ROS2MessageType.FLOAT64
)

# Publish data
bridge.publish("/physio/heart_rate", {'data': 75.0})

# Create subscriber
def callback(msg):
    print(f"Received: {msg}")

bridge.create_subscriber(
    "/robot/state",
    ROS2MessageType.POSE_STAMPED,
    callback
)
```

#### Physiological State Publishing

```python
bridge.publish_physiological_state(
    topic_prefix="/physio",
    heart_rate=72.0,
    bp_systolic=120.0,
    bp_diastolic=80.0,
    spo2=98.0,
    resp_rate=16.0
)
```

### 5. Physiological Controller (`physio_controller.py`)

#### Alert Levels

| Level | HR (bpm) | BP Systolic (mmHg) | SpO2 (%) | Action |
|-------|----------|-------------------|----------|--------|
| **NORMAL** | 60-100 | 90-140 | 94-100 | Normal operation |
| **CAUTION** | 50-60 or 100-120 | <100 or >140 | <94 | Reduced velocity (60%) |
| **WARNING** | <50 or >120 | <90 or >160 | <90 | Major slowdown (30%) |
| **CRITICAL** | <40 or >150 | <80 or >180 | <85 | Emergency stop |

#### Usage

```python
controller = PhysiologicalController(
    baseline_heart_rate=70.0,
    baseline_blood_pressure=90.0
)

# Set surgical phase
controller.set_surgical_phase(SurgicalPhase.MANIPULATION)

# Get physiological state
physio_state = controller.get_physiological_feedback()

# Compute control constraints
constraints = controller.compute_control_constraints(physio_state)

# Apply constraints to robot
robot_velocity *= constraints.max_velocity_scale
robot_force *= constraints.max_force_scale

if constraints.emergency_stop:
    robot.disable()
```

---

## Examples

### Example 1: Basic dVRK Control

See `examples/surgical_robotics_demo.py` for complete demonstration.

### Example 2: Physiologically-Adaptive Surgery

```python
from src.surgical_robotics import *
from src.coupling import HeartBrainCouplingModel

# Initialize system
hbcm = HeartBrainCouplingModel(...)
controller = PhysiologicalController(hbcm_model=hbcm)
dvrk = DVRKInterface(DVRKConfiguration())

# Surgical procedure
controller.set_surgical_phase(SurgicalPhase.MANIPULATION)

for waypoint in surgical_trajectory:
    # Monitor patient
    physio = controller.get_physiological_feedback()

    # Check safety
    if physio.alert_level == PhysiologicalAlertLevel.CRITICAL:
        dvrk.disable()
        print("EMERGENCY STOP: Critical physiological state")
        break

    # Compute adaptive constraints
    constraints = controller.compute_control_constraints(physio)

    # Scale robot motion
    scaled_velocity = nominal_velocity * constraints.max_velocity_scale
    scaled_force = nominal_force * constraints.max_force_scale

    # Execute motion
    dvrk.move_cartesian(waypoint)
```

### Example 3: Multi-Robot Coordination

```python
# Initialize multiple robots via CRTK
psm1 = CRTKInterface(CRTKConfiguration(robot_name="PSM1"))
psm2 = CRTKInterface(CRTKConfiguration(robot_name="PSM2"))

psm1.enable()
psm2.enable()

# Coordinated motion
pose1 = np.array([0.05, 0.02, -0.12, 0, 0, 0, 1])
pose2 = np.array([-0.05, 0.02, -0.12, 0, 0, 0, 1])

psm1.servo_cp(pose1)
psm2.servo_cp(pose2)

# Synchronized state
state1 = psm1.get_measured_state()
state2 = psm2.get_measured_state()
```

---

## Safety Considerations

### Critical Safety Rules

1. **Never disable safety limits** without explicit authorization
2. **Always monitor physiological state** during operation
3. **Implement emergency stop** mechanisms
4. **Respect workspace boundaries** to prevent collisions
5. **Test in simulation** before hardware deployment
6. **Follow hospital protocols** for clinical use

### Safety Features

✅ **Workspace limits**: Configurable boundaries prevent dangerous motions
✅ **Velocity scaling**: Automatic slowdown based on patient state
✅ **Emergency stop**: Critical alerts trigger immediate stop
✅ **Multi-level alerts**: Progressive response to physiological changes
✅ **Force limits**: Maximum force constraints prevent tissue damage

### Recommended Testing Protocol

1. **Unit tests**: Verify each interface independently
2. **Integration tests**: Test combined system behavior
3. **Simulation**: Validate in AMBF before hardware
4. **Dry runs**: Execute motions without patient
5. **Supervised operation**: Monitor first clinical uses
6. **Continuous monitoring**: Track physiological state throughout procedure

---

## References

### Surgical Robotics Platforms

1. Kazanzides, P., et al. (2014). "An open-source research kit for the da Vinci Surgical System." *ICRA 2014*.

2. Kazanzides, P., et al. (2021). "The Collaborative Robotics Toolkit (CRTK)." *IEEE Robotics and Automation Letters*.

3. Munawar, A., et al. (2019). "A Real-Time Dynamic Simulator and an Associated Front-End Representation Format for Simulating Complex Robots and Environments." *Frontiers in Robotics and AI*.

### Physiological Modeling

4. Van der Pol, B., & Van der Mark, J. (1928). "The heartbeat considered as a relaxation oscillation." *Philosophical Magazine*.

5. FitzHugh, R. (1961). "Impulses and physiological states in theoretical models of nerve membrane." *Biophysical Journal*.

6. Task Force (1996). "Heart rate variability: Standards of measurement, physiological interpretation, and clinical use." *Circulation*.

### Online Resources

- dVRK Wiki: https://github.com/jhu-dvrk/sawIntuitiveResearchKit/wiki
- CRTK Documentation: https://collaborative-robotics.github.io/
- AMBF GitHub: https://github.com/WPI-AIM/ambf
- ROS 2 Documentation: https://docs.ros.org/

---

## Support

For issues or questions:
- **GitHub Issues**: https://github.com/STLNFTART/Multi-Heart-Model/issues
- **Documentation**: See `docs/` directory
- **Examples**: See `examples/surgical_robotics_demo.py`

---

**Last Updated**: 2025-11-18
**Version**: 1.0.0
**Maintainer**: Multi-Heart-Model Development Team
