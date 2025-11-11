# Hardware Interface Module

Python interface for integrating external hardware devices with the Heart-Brain Coupling Model (HBCM).

## Motor Hand Pro Interface

The `motor_hand_interface.py` module provides a complete serial communication interface for controlling a 5-finger prosthetic hand via Arduino.

### Installation

Install required dependency:

```bash
pip install pyserial
```

### Quick Start

```python
from src.hardware import MotorHandPro, MotorHandConfig, Gesture

# List available ports
ports = MotorHandPro.list_available_ports()
print(f"Available ports: {ports}")

# Configure connection
config = MotorHandConfig(
    port="/dev/ttyUSB0",  # or "COM3" on Windows
    baud_rate=115200,
    auto_reconnect=True
)

# Connect and control
with MotorHandPro(config) as hand:
    # Enable the hand
    hand.enable()

    # Execute a gesture
    hand.execute_gesture(Gesture.OPEN)
    time.sleep(2)

    # Set grip strength
    hand.set_grip_strength(0.75)  # 75% closed

    # Set individual fingers
    hand.set_finger_positions(
        thumb=90,
        index=45,
        middle=90,
        ring=120,
        pinky=180
    )

    # Get current status
    status = hand.get_status()
    print(f"Status: {status}")
```

### Integration with HBCM

The `HBCMMotorHandController` class provides automatic mapping from physiological signals to hand movements:

```python
from src.hardware import MotorHandPro, HBCMMotorHandController
from src.coupling import HeartBrainCouplingModel

# Initialize HBCM
hbcm = HeartBrainCouplingModel()

# Initialize motor hand
motor_hand = MotorHandPro()
controller = HBCMMotorHandController(motor_hand)

# Simulate and control in real-time
trajectory = hbcm.simulate(
    initial_state=(0.0, 0.0, 1.0, 0.0),
    t_span=(0.0, 10.0),
    dt=0.01
)

# Update hand based on neural activity
for time, state in trajectory:
    neural_v = state[0]
    cardiac_x = state[2]

    # Option 1: Neural-driven
    controller.update_from_neural_state(neural_v)

    # Option 2: Cardiac-driven
    # controller.update_from_cardiac_state(cardiac_x)

    # Option 3: Blended control
    # controller.update_from_coupled_state(neural_v, cardiac_x, blend=0.5)

    time.sleep(0.01)
```

### Simulation Mode

For development and testing without hardware:

```python
config = MotorHandConfig(simulation_mode=True)
hand = MotorHandPro(config)

# All commands work but don't send to hardware
hand.set_grip_strength(0.5)
print(f"Simulated positions: {hand.get_positions()}")
```

### API Reference

#### MotorHandPro

**Methods:**
- `connect()`: Establish serial connection
- `disconnect()`: Close connection
- `set_finger_positions(thumb, index, middle, ring, pinky)`: Set each finger angle (0-180°)
- `set_grip_strength(strength)`: Set grip strength (0.0-1.0)
- `execute_gesture(gesture)`: Execute predefined gesture
- `reset_to_neutral()`: Return to neutral position
- `enable()`: Enable motor control
- `disable()`: Disable motor control
- `get_status()`: Get current state
- `get_positions()`: Get cached positions

**Static Methods:**
- `list_available_ports()`: List available serial ports

#### HBCMMotorHandController

**Methods:**
- `update_from_neural_state(neural_activation)`: Map neural state to grip
- `update_from_cardiac_state(cardiac_activation)`: Map cardiac state to grip
- `update_from_coupled_state(neural, cardiac, blend)`: Blend both signals

### Configuration Options

```python
@dataclass
class MotorHandConfig:
    port: str = "/dev/ttyUSB0"        # Serial port
    baud_rate: int = 115200           # Communication speed
    timeout: float = 1.0              # Read timeout (seconds)
    auto_reconnect: bool = True       # Auto-reconnect on failure
    reconnect_delay: float = 2.0      # Delay between reconnect attempts
    simulation_mode: bool = False     # Run without hardware
```

### Communication Protocol

Commands use angle brackets as delimiters:

**Request:** `<COMMAND,param1,param2,...>`
**Response:** `<ACK,COMMAND>` or `<ERROR,message>`

See `arduino/motor_hand_pro/README.md` for complete protocol specification.

### Error Handling

```python
hand = MotorHandPro(config)

if not hand.connected:
    print("Failed to connect")
    # Handle connection failure

# All methods return bool or None on failure
if not hand.set_grip_strength(0.5):
    print("Command failed")
    # Handle command failure

# Get detailed status
status = hand.get_status()
if status is None:
    print("Status query failed")
else:
    print(f"Enabled: {status['enabled']}")
    print(f"Positions: {status['positions']}")
```

### Thread Safety

The `MotorHandPro` class uses internal locking for thread-safe operation:

```python
import threading

hand = MotorHandPro()

def control_loop():
    while running:
        hand.set_grip_strength(0.8)
        time.sleep(0.1)

thread = threading.Thread(target=control_loop)
thread.start()
```

### Troubleshooting

**Import error: No module named 'serial'**
```bash
pip install pyserial
```

**Connection failed**
- Check port name (`/dev/ttyUSB0` on Linux, `COM3` on Windows)
- Verify Arduino is connected and powered
- Check user has permission to access serial port: `sudo usermod -a -G dialout $USER`

**Commands timeout**
- Verify baud rate matches Arduino sketch (115200)
- Check Arduino Serial Monitor isn't open (conflicts with other connections)
- Ensure adequate power supply for servos

**Erratic behavior**
- Enable simulation mode first to test logic
- Check Arduino logs via Serial Monitor
- Verify servo power supply is adequate

## Future Hardware Integrations

Additional hardware interfaces can be added to this module:
- ECG sensors
- EEG headsets
- Pressure sensors
- Biomedical signal acquisition devices

Each should follow similar patterns with:
- Dedicated configuration dataclass
- Thread-safe communication
- Simulation mode for testing
- Integration controller for HBCM
