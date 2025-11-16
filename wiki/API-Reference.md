# API Reference

Complete API documentation for the Multi-Heart-Model package.

## 📦 Package Structure

```
src/
├── cardiac/          # Cardiac models
├── neural/           # Neural models
├── coupling/         # Coupling orchestrators
├── microprocessor/   # Hardware control
├── integration/      # Hardware bridges
├── organ_chip/       # Advanced organ models
└── organchip/        # Complete toxicity platform
```

## 🫀 Cardiac Models

### VanDerPolOscillator

Van der Pol relaxation oscillator for cardiac dynamics.

**Module**: `src.cardiac.van_der_pol`

#### Constructor

```python
VanDerPolOscillator(mu=1.5, omega=1.0, damping=0.1)
```

**Parameters**:
- `mu` (float): Nonlinearity strength. Default: 1.5. Range: [0.5, 3.0]
- `omega` (float): Natural frequency (Hz). Default: 1.0. Range: [0.5, 2.0]
- `damping` (float): Damping coefficient. Default: 0.1. Range: [0.0, 0.5]

#### Methods

##### `derivatives(t, state, input_drive=0.0)`

Compute state derivatives.

**Parameters**:
- `t` (float): Current time in seconds
- `state` (Tuple[float, float]): Current state (x, y)
- `input_drive` (float): External input signal. Default: 0.0

**Returns**: `Tuple[float, float]` - Derivatives (dx/dt, dy/dt)

**Example**:
```python
from src.cardiac import VanDerPolOscillator

model = VanDerPolOscillator(mu=1.2)
state = (1.0, 0.0)
dx, dy = model.derivatives(t=0.0, state=state, input_drive=0.1)
```

##### `step(t, state, dt, input_drive=0.0)`

Advance state by one timestep using Euler integration.

**Parameters**:
- `t` (float): Current time in seconds
- `state` (Tuple[float, float]): Current state (x, y)
- `dt` (float): Timestep size in seconds
- `input_drive` (float): External input signal. Default: 0.0

**Returns**: `Tuple[float, float]` - New state (x_new, y_new)

**Example**:
```python
new_state = model.step(t=0.0, state=(1.0, 0.0), dt=0.001, input_drive=0.1)
```

## 🧠 Neural Models

### FitzHughNagumo

Two-dimensional neural oscillator model.

**Module**: `src.neural.fitzhugh_nagumo`

#### Constructor

```python
FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.5)
```

**Parameters**:
- `a` (float): Nullcline position parameter. Default: 0.7. Range: [0.5, 1.0]
- `b` (float): Recovery rate. Default: 0.8. Range: [0.5, 1.0]
- `c` (float): Timescale separation. Default: 3.0. Range: [1.0, 5.0]
- `stimulus_amplitude` (float): External stimulus strength. Default: 0.5

#### Methods

##### `derivatives(t, state, input_drive=0.0)`

Compute state derivatives.

**Parameters**:
- `t` (float): Current time in seconds
- `state` (Tuple[float, float]): Current state (v, w)
- `input_drive` (float): External input signal. Default: 0.0

**Returns**: `Tuple[float, float]` - Derivatives (dv/dt, dw/dt)

**Example**:
```python
from src.neural import FitzHughNagumo

model = FitzHughNagumo(a=0.7, b=0.8, c=3.0)
state = (0.0, 0.0)
dv, dw = model.derivatives(t=0.0, state=state, input_drive=0.2)
```

##### `step(t, state, dt, input_drive=0.0)`

Advance state by one timestep.

**Parameters**:
- `t` (float): Current time in seconds
- `state` (Tuple[float, float]): Current state (v, w)
- `dt` (float): Timestep size in seconds
- `input_drive` (float): External input signal. Default: 0.0

**Returns**: `Tuple[float, float]` - New state (v_new, w_new)

## 🔗 Coupling System

### CouplingParameters

Configuration for bidirectional heart-brain coupling.

**Module**: `src.coupling.hbcm`

#### Constructor

```python
CouplingParameters(
    neural_to_cardiac_gain=0.5,
    cardiac_to_neural_gain=0.3,
    neural_to_cardiac_delay=0.12,
    cardiac_to_neural_delay=0.15
)
```

**Parameters**:
- `neural_to_cardiac_gain` (float): Coupling strength neural → cardiac. Default: 0.5. Range: [0.0, 1.0]
- `cardiac_to_neural_gain` (float): Coupling strength cardiac → neural. Default: 0.3. Range: [0.0, 1.0]
- `neural_to_cardiac_delay` (float): Communication delay in seconds. Default: 0.12. Range: [0.05, 0.5]
- `cardiac_to_neural_delay` (float): Communication delay in seconds. Default: 0.15. Range: [0.05, 0.5]

### HeartBrainCouplingModel

Orchestrator for bidirectional neural-cardiac coupling with delays.

**Module**: `src.coupling.hbcm`

#### Constructor

```python
HeartBrainCouplingModel(neural_model, cardiac_model, coupling)
```

**Parameters**:
- `neural_model`: Instance of FitzHughNagumo or compatible neural model
- `cardiac_model`: Instance of VanDerPolOscillator or compatible cardiac model
- `coupling`: Instance of CouplingParameters

**Example**:
```python
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import CouplingParameters, HeartBrainCouplingModel

hbcm = HeartBrainCouplingModel(
    neural_model=FitzHughNagumo(),
    cardiac_model=VanDerPolOscillator(),
    coupling=CouplingParameters()
)
```

#### Methods

##### `simulate(initial_state, t_span, dt)`

Run a complete simulation.

**Parameters**:
- `initial_state` (Tuple[float, float, float, float]): Initial state (v, w, x, y)
- `t_span` (Tuple[float, float]): Time interval (t_start, t_end) in seconds
- `dt` (float): Timestep size in seconds

**Returns**: `List[Tuple]` - Trajectory as list of (time, state) tuples

**Example**:
```python
trajectory = hbcm.simulate(
    initial_state=(0.0, 0.0, 1.0, 0.0),
    t_span=(0.0, 10.0),
    dt=0.001
)
```

##### `extract_series(trajectory)`

Extract time series from trajectory.

**Parameters**:
- `trajectory`: Output from `simulate()`

**Returns**: `Tuple[List, List, List]` - (times, neural_states, cardiac_states)
- `times`: List of time points
- `neural_states`: List of (v, w) tuples
- `cardiac_states`: List of (x, y) tuples

**Example**:
```python
times, neural, cardiac = hbcm.extract_series(trajectory)

# Access individual variables
voltages = [v for v, w in neural]
positions = [x for x, y in cardiac]
```

##### `step(t, state, dt)`

Advance coupled system by one timestep.

**Parameters**:
- `t` (float): Current time in seconds
- `state` (Tuple[float, float, float, float]): Current state (v, w, x, y)
- `dt` (float): Timestep size in seconds

**Returns**: `Tuple[float, float, float, float]` - New state

## 🖥️ Hardware Control

### PrimalLogicProcessor

Integral controller for hardware systems.

**Module**: `src.microprocessor.primal_logic`

#### Constructor

```python
PrimalLogicProcessor(
    Kp=1.0,
    Ki=0.1,
    integral_limit=10.0,
    output_limit=1.0
)
```

**Parameters**:
- `Kp` (float): Proportional gain. Default: 1.0
- `Ki` (float): Integral gain. Default: 0.1
- `integral_limit` (float): Integral windup limit. Default: 10.0
- `output_limit` (float): Output saturation limit. Default: 1.0

#### Methods

##### `compute_control(error, dt)`

Compute control signal from error.

**Parameters**:
- `error` (float): Tracking error (setpoint - measurement)
- `dt` (float): Timestep in seconds

**Returns**: `float` - Control signal (clamped to [-output_limit, output_limit])

**Example**:
```python
from src.microprocessor import PrimalLogicProcessor

controller = PrimalLogicProcessor(Kp=1.5, Ki=0.2)
control = controller.compute_control(error=0.5, dt=0.001)
```

##### `reset()`

Reset integral accumulator.

**Returns**: None

## 🧬 Organ-On-Chip Platform

### OrganChipSuite

Multi-organ drug toxicity screening platform.

**Module**: `src.organchip.orchestrator`

#### Constructor

```python
OrganChipSuite()
```

Creates suite with default organ models:
- CardiacCell
- Hepatocyte
- EndothelialCell
- ImmuneCell
- NeuronCell

#### Methods

##### `run_drug_test(drug_name, dose_mg_kg, duration_hours, dt_minutes=1.0)`

Run complete drug toxicity screening.

**Parameters**:
- `drug_name` (str): Drug identifier
- `dose_mg_kg` (float): Dose in mg/kg body weight
- `duration_hours` (float): Test duration in hours
- `dt_minutes` (float): Timestep in minutes. Default: 1.0

**Returns**: `dict` - Results dictionary with keys:
- `'drug_name'`: str
- `'dose_mg_kg'`: float
- `'duration_hours'`: float
- `'toxicity_scores'`: dict - Toxicity scores by organ
- `'biomarkers'`: dict - Biomarker time series by organ
- `'times'`: list - Time points in hours
- `'blood_concentration'`: list - Drug concentration over time

**Example**:
```python
from src.organchip import OrganChipSuite

suite = OrganChipSuite()
results = suite.run_drug_test(
    drug_name="Doxorubicin",
    dose_mg_kg=5.0,
    duration_hours=48.0,
    dt_minutes=1.0
)

print(f"Cardiotoxicity: {results['toxicity_scores']['cardiac']:.2f}")
print(f"Hepatotoxicity: {results['toxicity_scores']['hepatic']:.2f}")
```

##### `step(t, states, dt, drug_concentration)`

Advance all organs by one timestep.

**Parameters**:
- `t` (float): Current time in minutes
- `states` (dict): Current organ states
- `dt` (float): Timestep in minutes
- `drug_concentration` (float): Current drug concentration

**Returns**: `dict` - New organ states

### CardiacCell

Cardiac cell model with ion channel dynamics.

**Module**: `src.organchip.cardiac`

#### Key Features
- Action potential generation
- hERG channel dynamics
- Drug-induced QT prolongation
- Troponin release

#### Methods

##### `step(t, state, dt, drug_conc=0.0)`

**Returns**: New state tuple

##### `get_biomarkers(state)`

**Returns**: `dict` with keys:
- `'action_potential'`: Membrane voltage
- `'qt_interval'`: QT interval duration
- `'troponin_i'`: Troponin I concentration (ng/mL)
- `'herg_current'`: hERG current magnitude

### Hepatocyte

Liver cell model with drug metabolism.

**Module**: `src.organchip.hepatic`

#### Key Features
- CYP450 metabolism
- Drug clearance
- ALT/AST enzyme release
- Oxidative stress

#### Methods

##### `step(t, state, dt, drug_conc=0.0)`

**Returns**: New state tuple

##### `get_biomarkers(state)`

**Returns**: `dict` with keys:
- `'alt'`: ALT enzyme level (U/L)
- `'ast'`: AST enzyme level (U/L)
- `'bilirubin'`: Bilirubin level (mg/dL)
- `'metabolism_rate'`: Drug metabolism rate

## 🔧 Integration Components

### MotorHandProBridge

Bridge to MotorHandPro QUANT hardware.

**Module**: `src.integration.motorhand_bridge`

#### Constructor

```python
MotorHandProBridge(device_id="/dev/ttyUSB0", baud_rate=115200)
```

**Parameters**:
- `device_id` (str): Serial port identifier
- `baud_rate` (int): Communication baud rate. Default: 115200

#### Methods

##### `send_control(throttle, brake, steering)`

Send control commands to hardware.

**Parameters**:
- `throttle` (int): Throttle value [0, 255]
- `brake` (int): Brake value [0, 255]
- `steering` (int): Steering angle [0, 255]

**Returns**: `bool` - Success status

##### `read_sensors()`

Read sensor data from hardware.

**Returns**: `dict` - Sensor readings

## 📊 Utility Functions

### Common Patterns

#### State Initialization

```python
# Neural model
neural_state = (0.0, 0.0)  # (v, w)

# Cardiac model
cardiac_state = (1.0, 0.0)  # (x, y)

# Coupled model
coupled_state = (0.0, 0.0, 1.0, 0.0)  # (v, w, x, y)
```

#### Parameter Validation

```python
# Check parameter ranges
assert 0.5 <= mu <= 3.0, "mu must be in [0.5, 3.0]"
assert 0.0 < dt <= 0.01, "dt should be small for stability"
```

#### Time Units

All times in seconds unless otherwise specified:
- `dt = 0.001` - 1 millisecond
- `delay = 0.12` - 120 milliseconds
- `t_span = (0.0, 10.0)` - 10 seconds

**Exception**: Organ chip models may use minutes/hours (check docstrings)

## 🔍 Type Definitions

### Common Types

```python
from typing import Tuple, List, Dict

# State vectors
NeuralState = Tuple[float, float]  # (v, w)
CardiacState = Tuple[float, float]  # (x, y)
CoupledState = Tuple[float, float, float, float]  # (v, w, x, y)

# Time spans
TimeSpan = Tuple[float, float]  # (t_start, t_end)

# Trajectories
Trajectory = List[Tuple[float, CoupledState]]  # [(t, state), ...]

# Results
OrganChipResults = Dict[str, any]
```

## ⚠️ Important Notes

### Numerical Stability

- **Recommended timestep**: `dt = 0.001` (1 ms)
- **Maximum timestep**: `dt = 0.01` (10 ms)
- Larger timesteps may cause instability

### Parameter Ranges

Follow physiologically valid ranges:

```python
# FitzHugh-Nagumo
a: [0.5, 1.0]
b: [0.5, 1.0]
c: [1.0, 5.0]

# Van der Pol
mu: [0.5, 3.0]
omega: [0.5, 2.0]

# Coupling
gain: [0.0, 1.0]
delay: [0.05, 0.5]  # seconds
```

### State Ordering Convention

Always: **Neural before Cardiac**

```python
# Correct
state = (v, w, x, y)

# Wrong
state = (x, y, v, w)
```

## 📚 See Also

- **[Examples](Examples)** - Usage examples
- **[Architecture](Architecture)** - Design patterns
- **[Development Guide](Development-Guide)** - Contributing
- **[Testing](Testing)** - Testing API usage

---

**Note**: This API reference covers the Python implementation. For D language API, see `source/` directory documentation.
