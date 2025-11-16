# Hardware Integration

Guide to integrating the Multi-Heart-Model with hardware control systems.

## 🎯 Overview

The hardware integration layer connects physiological models to real-world control systems, specifically the **MotorHandPro QUANT** automotive control platform via the **Primal Logic Processor**.

### Key Components

1. **Primal Logic Processor**: Integral controller for real-time control
2. **MotorHandPro Bridge**: Serial communication interface to QUANT hardware
3. **Control Loops**: Closed-loop control algorithms
4. **Safety Systems**: Emergency shutdown and saturation limits

## 🖥️ Primal Logic Processor

The Primal Logic Processor is a proportional-integral (PI) controller designed for hardware integration.

**File**: `src/microprocessor/primal_logic.py`

### Architecture

```
Setpoint ──┬──> Error ──┬──> Proportional ─┬──> Sum ──> Control Output
           │             │                   │
Feedback ──┘             └──> Integral ──────┘
                              (with anti-windup)
```

### Features

- **PI Control**: Proportional + Integral action
- **Anti-windup**: Prevents integral saturation
- **Output Limiting**: Configurable saturation bounds
- **Reset Capability**: Clear integral accumulator
- **Real-time Ready**: Minimal computational overhead

### API

#### Constructor

```python
from src.microprocessor import PrimalLogicProcessor

controller = PrimalLogicProcessor(
    Kp=1.0,          # Proportional gain
    Ki=0.1,          # Integral gain
    integral_limit=10.0,  # Anti-windup limit
    output_limit=1.0      # Output saturation
)
```

#### Methods

##### `compute_control(error, dt)`

Compute control signal from tracking error.

```python
control = controller.compute_control(error=0.5, dt=0.01)
# Returns: float in range [-output_limit, +output_limit]
```

**Math**:
```
P_term = Kp * error
I_term = I_term_prev + Ki * error * dt  (clamped)
control = P_term + I_term  (clamped to output_limit)
```

##### `reset()`

Reset integral accumulator to zero.

```python
controller.reset()
```

### Example: Velocity Control

```python
from src.microprocessor import PrimalLogicProcessor
import time

# Initialize controller
controller = PrimalLogicProcessor(Kp=1.5, Ki=0.3, output_limit=1.0)

# Control parameters
setpoint = 50.0  # Target velocity (m/s)
dt = 0.01  # 10ms control loop

# Simulation variables
current_velocity = 0.0
acceleration = 0.0

# Control loop
for i in range(1000):  # 10 seconds
    # Compute error
    error = setpoint - current_velocity

    # Compute control
    control = controller.compute_control(error, dt)

    # Apply control (simple dynamics)
    acceleration = control * 5.0  # m/s²
    current_velocity += acceleration * dt

    # Log
    if i % 100 == 0:
        print(f"t={i*dt:.2f}s: velocity={current_velocity:.2f} m/s, "
              f"control={control:.3f}")

    time.sleep(dt)
```

### Tuning Guidelines

**Proportional Gain (Kp)**:
- Increases response speed
- Too high → oscillations
- Typical range: 0.5 - 5.0

**Integral Gain (Ki)**:
- Eliminates steady-state error
- Too high → overshoot and instability
- Typical range: 0.05 - 1.0

**Ziegler-Nichols Method**:
1. Set Ki = 0
2. Increase Kp until oscillation occurs → Ku (ultimate gain)
3. Measure oscillation period → Tu
4. Set Kp = 0.45 * Ku
5. Set Ki = 0.54 * Ku / Tu

## 🔌 MotorHandPro Bridge

Interface to MotorHandPro QUANT hardware via serial communication.

**File**: `src/integration/motorhand_bridge.py`

### Features

- **Serial Communication**: RS-232/USB interface
- **Command Protocol**: Proprietary QUANT protocol
- **Sensor Reading**: Velocity, position, pressure sensors
- **Control Output**: Throttle, brake, steering
- **Error Handling**: Timeout and checksum verification

### API

#### Constructor

```python
from src.integration import MotorHandProBridge

bridge = MotorHandProBridge(
    device_id="/dev/ttyUSB0",  # Serial port
    baud_rate=115200           # Communication speed
)
```

#### Connection Management

```python
# Connect to hardware
bridge.connect()

# Check connection
if bridge.is_connected():
    print("Connected to QUANT")

# Disconnect
bridge.disconnect()
```

#### Sending Control Commands

```python
# Send control values
success = bridge.send_control(
    throttle=128,   # 0-255 (0=off, 255=full)
    brake=0,        # 0-255
    steering=128    # 0-255 (128=center)
)

if success:
    print("Command sent successfully")
```

#### Reading Sensors

```python
# Read all sensors
sensors = bridge.read_sensors()

# Access sensor values
print(f"Velocity: {sensors['velocity']:.2f} m/s")
print(f"Position: {sensors['position']:.2f} m")
print(f"Brake pressure: {sensors['brake_pressure']:.1f} bar")
print(f"Steering angle: {sensors['steering_angle']:.1f} degrees")
```

**Sensor Dictionary**:
```python
sensors = {
    'velocity': float,        # m/s
    'position': float,        # meters
    'brake_pressure': float,  # bar
    'steering_angle': float,  # degrees
    'throttle_position': int, # 0-255
    'timestamp': float        # seconds
}
```

### Communication Protocol

**Command Format**:
```
[START] [CMD] [DATA_LEN] [DATA...] [CHECKSUM] [END]
```

- START: 0x02 (STX)
- CMD: Command byte
  - 0x10: Set throttle
  - 0x11: Set brake
  - 0x12: Set steering
  - 0x20: Read sensors
- DATA_LEN: Length of data payload
- DATA: Command-specific data
- CHECKSUM: XOR of all bytes
- END: 0x03 (ETX)

## 🚗 Complete Integration Example

### Emergency Braking System

Demonstrates full integration of heart-brain model → controller → hardware.

**File**: `examples/microprocessor_motorhand_demo.py`

```python
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters
from src.microprocessor import PrimalLogicProcessor
from src.integration import MotorHandProBridge

def emergency_braking_demo():
    """
    Demonstrate emergency braking controlled by heart-brain model.

    Scenario:
    1. Vehicle cruising at 30 m/s
    2. Heart-brain model detects stress (high neural activity)
    3. Controller initiates emergency braking
    4. Vehicle decelerates to safe stop
    """

    # Initialize physiological model
    hbcm = HeartBrainCouplingModel(
        neural_model=FitzHughNagumo(stimulus_amplitude=0.5),
        cardiac_model=VanDerPolOscillator(mu=1.2),
        coupling=CouplingParameters()
    )

    # Initialize hardware controller
    controller = PrimalLogicProcessor(Kp=2.0, Ki=0.5, output_limit=1.0)

    # Initialize hardware bridge
    bridge = MotorHandProBridge(device_id="/dev/ttyUSB0")
    bridge.connect()

    # Simulation state
    physio_state = (0.0, 0.0, 1.0, 0.0)  # (v, w, x, y)
    t = 0.0
    dt = 0.01  # 10ms control loop

    # Control variables
    target_velocity = 30.0  # Initial cruise speed
    emergency_active = False

    print("=" * 60)
    print("EMERGENCY BRAKING DEMO")
    print("=" * 60)
    print("\nInitial cruise: 30 m/s")
    print("Monitoring heart-brain coupling for stress detection...\n")

    try:
        for i in range(1000):  # 10 seconds
            # Step physiological model
            physio_state = hbcm.step(t, physio_state, dt)
            v, w, x, y = physio_state

            # Read vehicle sensors
            sensors = bridge.read_sensors()
            current_velocity = sensors['velocity']

            # Detect emergency condition (high neural voltage)
            if v > 1.5 and not emergency_active:
                print(f"t={t:.2f}s: EMERGENCY DETECTED!")
                print(f"  Neural voltage: {v:.3f} (threshold: 1.5)")
                emergency_active = True
                target_velocity = 0.0  # Emergency stop
                controller.reset()  # Reset integral

            # Compute control
            error = target_velocity - current_velocity
            control = controller.compute_control(error, dt)

            # Convert to brake/throttle commands
            if emergency_active:
                # Emergency braking
                brake = int(min(abs(control) * 255, 255))
                throttle = 0
                print(f"t={t:.2f}s: Braking at {brake}/255, "
                      f"velocity={current_velocity:.1f} m/s")
            else:
                # Normal cruise control
                if control > 0:
                    throttle = int(control * 255)
                    brake = 0
                else:
                    throttle = 0
                    brake = int(abs(control) * 255)

            # Send to hardware
            bridge.send_control(throttle=throttle, brake=brake, steering=128)

            # Check if stopped
            if emergency_active and current_velocity < 0.1:
                print(f"\nt={t:.2f}s: Vehicle stopped safely")
                print(f"  Final velocity: {current_velocity:.3f} m/s")
                break

            t += dt

    finally:
        # Safety: ensure vehicle stopped
        bridge.send_control(throttle=0, brake=255, steering=128)
        bridge.disconnect()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    emergency_braking_demo()
```

### Running the Demo

```bash
# Ensure hardware is connected
ls /dev/ttyUSB*

# Run demo
python examples/microprocessor_motorhand_demo.py
```

## 🛡️ Safety Features

### Output Saturation

All control outputs are clamped to safe ranges:

```python
# In PrimalLogicProcessor
control = np.clip(control, -self.output_limit, self.output_limit)

# In MotorHandProBridge
throttle = int(np.clip(throttle, 0, 255))
brake = int(np.clip(brake, 0, 255))
steering = int(np.clip(steering, 0, 255))
```

### Integral Windup Protection

Prevents integral term from growing unbounded:

```python
self.integral = np.clip(
    self.integral,
    -self.integral_limit,
    self.integral_limit
)
```

### Emergency Shutdown

```python
def emergency_stop(bridge):
    """Execute emergency shutdown protocol."""
    # Full brake, no throttle, center steering
    for _ in range(10):  # Send multiple times for redundancy
        bridge.send_control(throttle=0, brake=255, steering=128)
        time.sleep(0.01)

    bridge.disconnect()
    print("EMERGENCY STOP EXECUTED")
```

### Watchdog Timer

```python
class SafetyWatchdog:
    """Monitor control loop and trigger safety if timeout."""

    def __init__(self, timeout=0.1):
        self.timeout = timeout
        self.last_update = time.time()

    def update(self):
        """Call this every control loop iteration."""
        self.last_update = time.time()

    def check(self):
        """Returns True if watchdog expired."""
        return (time.time() - self.last_update) > self.timeout

# Usage
watchdog = SafetyWatchdog(timeout=0.1)  # 100ms timeout

while running:
    # ... control loop ...
    watchdog.update()

    if watchdog.check():
        emergency_stop(bridge)
        break
```

## 🔧 Hardware Setup

### Required Hardware

- **MotorHandPro QUANT**: Automotive control unit
- **USB-Serial Adapter**: For PC connection
- **Power Supply**: 12V DC for QUANT
- **Sensors**: Wheel speed, brake pressure, steering angle

### Wiring Diagram

```
PC (USB) ──> USB-Serial ──> QUANT RX/TX
                            QUANT GND ──> Common Ground
                            QUANT +12V ──> Power Supply
                            QUANT Sensors ──> Vehicle
                            QUANT Actuators ──> Vehicle
```

### Serial Port Configuration

**Linux**:
```bash
# Check available ports
ls /dev/ttyUSB*

# Set permissions
sudo chmod 666 /dev/ttyUSB0

# Test connection
screen /dev/ttyUSB0 115200
```

**Windows**:
```
Device Manager → Ports → Check COM port number
Use COM3, COM4, etc. in code
```

### Baud Rate Settings

- **Standard**: 115200 bps
- **Alternative**: 57600, 9600 for debugging
- **Parity**: None
- **Stop Bits**: 1
- **Flow Control**: None

## 📊 Performance Metrics

### Control Loop Timing

Typical performance on modern PC:

- **Control loop**: 10 ms (100 Hz)
- **Physiological model step**: < 1 ms
- **Controller compute**: < 0.1 ms
- **Serial communication**: 2-5 ms
- **Sensor read**: 3-8 ms

### Latency Analysis

```
Total Latency = Physio Step + Control Compute + Serial TX/RX
              = 1 ms + 0.1 ms + 5 ms
              = ~6 ms (well within 10 ms loop time)
```

### Optimization Tips

1. **Use binary protocol** instead of ASCII for faster communication
2. **Batch sensor reads** to reduce serial overhead
3. **Pre-allocate buffers** to avoid memory allocation in loop
4. **Use compiled language (D)** for production (10-100x faster)

## 🧪 Testing and Validation

### Hardware-in-Loop Testing

```python
# Test with simulated hardware
from src.integration import MockMotorHandBridge

bridge = MockMotorHandBridge()  # Simulated hardware

# Same API as real bridge
bridge.send_control(throttle=100, brake=0, steering=128)
sensors = bridge.read_sensors()
```

### Validation Script

```bash
# Run hardware integration validation
python validate_integration.py

# Expected output:
# ✓ Primal Logic Processor tests passed
# ✓ MotorHand Bridge connection test passed
# ✓ Control loop timing test passed
# ✓ Emergency braking test passed
```

### Unit Tests

```python
import pytest
from src.microprocessor import PrimalLogicProcessor

def test_proportional_control():
    """Test proportional term."""
    controller = PrimalLogicProcessor(Kp=2.0, Ki=0.0)
    control = controller.compute_control(error=0.5, dt=0.01)
    assert control == pytest.approx(1.0)  # 2.0 * 0.5

def test_integral_control():
    """Test integral accumulation."""
    controller = PrimalLogicProcessor(Kp=0.0, Ki=1.0)

    # Accumulate error over time
    for _ in range(10):
        control = controller.compute_control(error=0.1, dt=0.01)

    # Integral should be 10 * 0.1 * 0.01 = 0.01
    assert control == pytest.approx(0.01 * 10)

def test_output_saturation():
    """Test output limiting."""
    controller = PrimalLogicProcessor(Kp=10.0, output_limit=1.0)
    control = controller.compute_control(error=1.0, dt=0.01)
    assert control <= 1.0  # Clamped to limit
```

## 📚 See Also

- **[API Reference](API-Reference)** - Detailed API docs
- **[Examples](Examples)** - More hardware integration examples
- **[Architecture](Architecture)** - System architecture overview

---

**For technical details**, see `docs/microprocessor_motorhand_integration.md` in the repository.
