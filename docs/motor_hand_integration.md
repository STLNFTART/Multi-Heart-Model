# Motor Hand Pro Integration Guide

This guide explains how to integrate the Motor Hand Pro prosthetic hand with the Heart-Brain Coupling Model (HBCM) for physiologically-driven control experiments.

## Overview

The Motor Hand Pro integration enables real-time control of a 5-finger prosthetic hand based on simulated physiological signals from the HBCM. This creates a closed-loop system where:

1. **HBCM** simulates coupled neural and cardiac dynamics
2. **Python interface** translates physiological signals to control commands
3. **Arduino controller** drives servo motors in the prosthetic hand
4. **Motor Hand Pro** responds with physical movements

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Heart-Brain Coupling Model (HBCM)                      │
│  ┌──────────────┐         ┌──────────────┐             │
│  │ Neural Model │ ◄─────► │Cardiac Model │             │
│  │ (FitzHugh-   │         │ (Van der Pol)│             │
│  │  Nagumo)     │         │              │             │
│  └──────────────┘         └──────────────┘             │
│         │                        │                       │
│         └───────────┬────────────┘                       │
│                     ▼                                    │
│         ┌──────────────────────┐                        │
│         │ Coupling Layer       │                        │
│         └──────────────────────┘                        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  HBCMMotorHandController (Python)                       │
│  - Maps neural/cardiac states to grip strength          │
│  - Supports multiple control modes                      │
└─────────────────────┬───────────────────────────────────┘
                      │ USB Serial
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Arduino Motor Hand Controller                          │
│  - Receives commands via serial                         │
│  - Controls 5 servo motors                              │
│  - Provides safety features                             │
└─────────────────────┬───────────────────────────────────┘
                      │ PWM Signals
                      ▼
            ┌────────────────────┐
            │  Motor Hand Pro    │
            │  (5 Servo Motors)  │
            └────────────────────┘
```

## Hardware Setup

### Required Components

1. **Arduino Board**: Mega 2560 or Uno
2. **Servos**: 5x SG90 or MG996R servo motors
3. **Power Supply**: 5-6V DC, 2-3A capacity
4. **USB Cable**: For Arduino-computer connection
5. **Jumper Wires**: For servo connections

### Wiring

Connect servos to Arduino pins:
- Thumb → Pin 3
- Index → Pin 5
- Middle → Pin 6
- Ring → Pin 9
- Pinky → Pin 10

**Important**: Use external power supply for servos, NOT the Arduino 5V pin.

See [`arduino/motor_hand_pro/README.md`](../arduino/motor_hand_pro/README.md) for detailed wiring diagram.

### Arduino Firmware Upload

1. Install Arduino IDE
2. Open `arduino/motor_hand_pro/motor_hand_pro.ino`
3. Select your board: Tools → Board → Arduino Mega 2560
4. Select port: Tools → Port → (your Arduino port)
5. Upload: Sketch → Upload

## Software Setup

### Install Dependencies

```bash
# Install Python serial library
pip install pyserial

# Install testing dependencies (optional)
pip install pytest pytest-cov
```

### Verify Installation

```bash
# Run tests
python -m pytest tests/test_motor_hand.py -v

# Should show all tests passing
```

## Usage

### Quick Start (Simulation Mode)

No hardware required - perfect for development and testing:

```python
from src.hardware import MotorHandPro, MotorHandConfig, Gesture

# Run in simulation mode
config = MotorHandConfig(simulation_mode=True)
hand = MotorHandPro(config)

# Control the hand
hand.enable()
hand.execute_gesture(Gesture.FIST)
hand.set_grip_strength(0.75)  # 75% closed
hand.reset_to_neutral()
```

### Hardware Mode

With actual Arduino and servos connected:

```python
from src.hardware import MotorHandPro, MotorHandConfig

# Configure for real hardware
config = MotorHandConfig(
    port="/dev/ttyUSB0",  # or "COM3" on Windows
    simulation_mode=False
)

with MotorHandPro(config) as hand:
    hand.enable()
    hand.set_grip_strength(0.5)
    # Hand will physically move!
```

### HBCM Integration

Control the hand based on physiological simulations:

```python
from src.coupling import HeartBrainCouplingModel
from src.hardware import MotorHandPro, HBCMMotorHandController

# Initialize HBCM
hbcm = HeartBrainCouplingModel()

# Initialize motor hand
motor_hand = MotorHandPro()
controller = HBCMMotorHandController(motor_hand)

# Run simulation
trajectory = hbcm.simulate(
    initial_state=(0.0, 0.0, 1.0, 0.0),
    t_span=(0.0, 10.0),
    dt=0.01
)

# Update hand in real-time
for time, state in trajectory:
    neural_v = state[0]
    cardiac_x = state[2]

    # Coupled control mode
    controller.update_from_coupled_state(neural_v, cardiac_x, blend=0.5)
```

## Control Modes

### 1. Neural-Driven Control

Hand grip strength controlled by neural oscillations:

```python
controller.update_from_neural_state(neural_activation)
```

**Use cases**: Modeling brain-controlled prosthetics, BCI applications

### 2. Cardiac-Driven Control

Hand grip strength controlled by heart activity:

```python
controller.update_from_cardiac_state(cardiac_activation)
```

**Use cases**: Stress response modeling, autonomic feedback

### 3. Coupled Control

Blended control from both systems:

```python
controller.update_from_coupled_state(
    neural_activation,
    cardiac_activation,
    blend=0.5  # 0=all neural, 1=all cardiac
)
```

**Use cases**: Full physiological integration, complex feedback loops

## Example Demonstrations

### Run Complete Demo

```bash
# Simulation mode (no hardware)
python examples/motor_hand_demo.py --mode simulation --demo all

# Hardware mode
python examples/motor_hand_demo.py --mode hardware --port /dev/ttyUSB0

# Specific demos
python examples/motor_hand_demo.py --demo gestures
python examples/motor_hand_demo.py --demo neural --duration 15
python examples/motor_hand_demo.py --demo coupled --duration 20
```

### Demo Options

- `--mode`: `simulation` or `hardware`
- `--port`: Serial port (e.g., `/dev/ttyUSB0`, `COM3`)
- `--demo`: `all`, `neural`, `cardiac`, `coupled`, `gestures`
- `--duration`: Simulation duration in seconds

## Configuration

### YAML Configuration

Edit `config/motor_hand_example.yaml`:

```yaml
hardware:
  motor_hand_pro:
    enabled: true
    port: /dev/ttyUSB0
    simulation_mode: false
    control_mode: coupled     # neural, cardiac, or coupled
    control_blend: 0.5        # Blending factor
    update_rate: 10.0         # Hz
```

### Python Configuration

```python
config = MotorHandConfig(
    port="/dev/ttyUSB0",
    baud_rate=115200,
    timeout=1.0,
    auto_reconnect=True,
    reconnect_delay=2.0,
    simulation_mode=False
)
```

## Communication Protocol

The Arduino firmware uses a simple text-based protocol:

### Commands (PC → Arduino)

```
<SET,thumb,index,middle,ring,pinky>   # Set individual angles
<GRIP,percentage>                     # Set grip strength (0-100)
<GESTURE,name>                        # Execute gesture
<NEUTRAL>                             # Reset to neutral
<STATUS>                              # Query status
<ENABLE>                              # Enable control
<DISABLE>                             # Disable control
```

### Responses (Arduino → PC)

```
<ACK,COMMAND>                         # Command acknowledged
<ERROR,message>                       # Error occurred
<STATUS,state,t,i,m,r,p>             # Status response
```

## Safety Features

### Arduino-Side Safety

1. **Timeout Protection**: Returns to neutral if no commands for 5 seconds
2. **Position Limits**: Constrains servo angles to 0-180°
3. **Smooth Movement**: Gradual transitions prevent jerky motion
4. **Emergency Disable**: Immediately stops and neutralizes

### Python-Side Safety

1. **Input Validation**: Checks all parameters before sending
2. **Auto-Reconnect**: Recovers from connection losses
3. **Simulation Mode**: Test without hardware risk
4. **Thread-Safe**: Safe for multi-threaded applications

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Arduino
- Check port name is correct (`/dev/ttyUSB0` on Linux, `COM3` on Windows)
- Verify Arduino is powered and USB connected
- Try listing ports: `MotorHandPro.list_available_ports()`
- Check user permissions: `sudo usermod -a -G dialout $USER` (Linux)

**Problem**: Commands timeout
- Verify baud rate matches (115200)
- Close Arduino Serial Monitor if open
- Check USB cable quality

### Movement Issues

**Problem**: Servos don't move
- Verify external power supply connected
- Check servo wiring
- Test with Arduino Serial Monitor: `<GRIP,50>`

**Problem**: Erratic movements
- Ensure power supply has adequate current (2-3A)
- Check for loose connections
- Reduce movement speed in firmware (`STEP_SIZE`)

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'serial'`
```bash
pip install pyserial
```

**Problem**: Cannot import from src
- Run from project root directory
- Or add to PYTHONPATH: `export PYTHONPATH=/path/to/Multi-Heart-Model`

## Testing

### Run Tests

```bash
# All motor hand tests
python -m pytest tests/test_motor_hand.py -v

# Specific test class
python -m pytest tests/test_motor_hand.py::TestMotorHandProSimulation -v

# With coverage
python -m pytest tests/test_motor_hand.py --cov=src.hardware
```

### Test Coverage

- Configuration validation
- Simulation mode operations
- Command formatting and validation
- HBCM integration
- Error handling
- Thread safety

## Research Applications

### Suggested Experiments

1. **Stress Response Modeling**
   - Vary HBCM parameters to simulate stress
   - Observe hand grip modulation
   - Correlate with physiological stress markers

2. **Brain-Computer Interface Simulation**
   - Use neural model as "brain signal" source
   - Map to prosthetic control
   - Test control strategies

3. **Autonomic Feedback Loops**
   - Hand position sensors feed back to HBCM
   - Create closed-loop control
   - Study entrainment and stability

4. **Multi-Modal Control**
   - Combine neural and cardiac signals
   - Optimize blending parameters
   - Evaluate control smoothness

## Performance Considerations

### Update Rates

- **HBCM Simulation**: 100-1000 Hz (dt=0.01-0.001)
- **Serial Communication**: Up to 115200 baud
- **Recommended Hand Update**: 10-20 Hz
- **Servo Response**: ~20ms per step

### Optimization Tips

1. **Batch Commands**: Update only when values change significantly
2. **Downsample**: Don't send every simulation step
3. **Async I/O**: Use threading for concurrent simulation and control
4. **Buffer Management**: Clear serial buffers regularly

## Future Enhancements

Potential extensions:

- [ ] Add force/pressure sensors for feedback
- [ ] Implement PID control for smoother movements
- [ ] Support multiple hands (bilateral control)
- [ ] Add EMG sensor integration
- [ ] Develop gesture recognition from HBCM patterns
- [ ] Create GUI for real-time visualization

## References

- Main README: [`README.md`](../README.md)
- HBCM Architecture: [`docs/architecture.md`](architecture.md)
- Arduino Firmware: [`arduino/motor_hand_pro/README.md`](../arduino/motor_hand_pro/README.md)
- Python Interface: [`src/hardware/README.md`](../src/hardware/README.md)
- Example Code: [`examples/motor_hand_demo.py`](../examples/motor_hand_demo.py)

## Support

For issues or questions:
1. Check this documentation
2. Review example code in `examples/`
3. Run tests to verify setup
4. Check Arduino serial output for debugging
5. Open GitHub issue with details

## License

MIT License - Part of the Multi-Heart-Model project
