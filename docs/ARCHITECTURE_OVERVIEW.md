# Multi-Heart-Model Codebase Architecture Overview

## 1. OVERALL DIRECTORY STRUCTURE

```
/home/user/Multi-Heart-Model/
├── .git/                              # Git repository
├── .github/                           # GitHub workflows/CI-CD
├── config/                            # YAML configuration files
│   └── default.yaml                   # Default simulation parameters
├── data/                              # Data storage for experiments
├── docs/                              # Documentation
│   ├── architecture.md
│   ├── hbcm_overview.md
│   ├── microprocessor_motorhand_integration.md
│   └── README.md
├── disabled/                          # Disabled/archived modules
├── examples/                          # Example scripts and demos
│   └── microprocessor_motorhand_demo.py
├── source/                            # D language implementation (Primal Overlay engine)
│   ├── app.d
│   ├── common.d
│   ├── logger.d
│   └── models/
│       ├── mm.d (Michaelis-Menten)
│       └── sir.d (Epidemiological model)
├── src/                               # Python source code (PRIMARY FOCUS)
│   ├── __init__.py
│   ├── cardiac/                       # Cardiac subsystem models
│   │   ├── __init__.py
│   │   └── van_der_pol.py            # Van der Pol oscillator for cardiac dynamics
│   ├── neural/                        # Neural subsystem models
│   │   ├── __init__.py
│   │   └── fhn.py                    # FitzHugh-Nagumo neural oscillator
│   ├── coupling/                      # Heart-brain coupling orchestration
│   │   ├── __init__.py
│   │   └── hbcm.py                   # Heart-Brain Coupling Model implementation
│   ├── microprocessor/                # Primal Logic Processor integration
│   │   ├── __init__.py
│   │   ├── primal_processor.py        # Main processor (8 IPUs)
│   │   └── control_system.py          # Control utilities
│   └── integration/                   # MotorHandPro bridge
│       ├── __init__.py
│       └── motorhand_bridge.py        # QUANT interface bridge
├── tests/                             # Test suite
│   ├── conftest.py                   # Pytest configuration
│   ├── test_models.py                # Basic model tests
│   └── integration/
│       └── test_microprocessor_motorhand.py  # Integration tests
├── Makefile                           # Build targets
├── dub.json                           # D build configuration
├── Makefile, LICENSE, README.md, etc.
```

## 2. EXISTING MODELS AND MODULES

### A. CARDIAC SUBSYSTEM (`src/cardiac/`)

**VanDerPolOscillator** (van_der_pol.py)
- **Type**: Relaxation oscillator for cardiac dynamics
- **Equations**: 
  ```
  dx/dt = y
  dy/dt = μ(1 - x²)y - ω²x - damping·y + input_force
  ```
- **Parameters**:
  - `mu` (default: 1.5) - Controls relaxation strength
  - `omega` (default: 1.0) - Natural frequency
  - `damping` (default: 0.0) - Damping coefficient
- **Methods**:
  - `derivatives()` - Compute state derivatives
  - `step()` - Explicit Euler integration step
- **Size**: 30 lines of code

### B. NEURAL SUBSYSTEM (`src/neural/`)

**FitzHughNagumo** (fhn.py)
- **Type**: 2D neural oscillator (canonical neuronal model)
- **Equations**:
  ```
  dv/dt = v - v³/3 - w + stimulus + input_drive
  dw/dt = (v + a - b·w) / c
  ```
- **Parameters**:
  - `a` (default: 0.7) - Excitability
  - `b` (default: 0.8) - Recovery rate
  - `c` (default: 3.0) - Time scaling
  - `stimulus_amplitude` (default: 0.0) - Baseline tonic input
- **Methods**:
  - `derivatives()` - State derivatives with external input
  - `step()` - Explicit Euler integration step
- **Size**: 50 lines of code

### C. COUPLING SUBSYSTEM (`src/coupling/`)

**HeartBrainCouplingModel** (hbcm.py)
- **Type**: Orchestration layer for bidirectional coupling
- **Architecture**: 
  - Manages history buffer for delay lookups
  - Implements bidirectional coupling with configurable delays
  - Supports external stimulus injection
- **Core Classes**:
  
  **CouplingParameters**:
  ```
  - neural_to_cardiac_gain: float (0.4)
  - cardiac_to_neural_gain: float (0.2)
  - neural_delay: float (0.0)
  - cardiac_delay: float (0.0)
  - neural_bias: float (0.0)
  - cardiac_bias: float (0.0)
  ```
  
  **HeartBrainCouplingModel**:
  - `neural_model` - FitzHughNagumo instance
  - `cardiac_model` - VanDerPolOscillator instance
  - `coupling` - CouplingParameters instance
  - `history` - Deque for time-delayed state lookups
- **Key Methods**:
  - `derivatives()` - Compute coupled derivatives
  - `step()` - Euler integration with coupling
  - `simulate()` - Full simulation loop
  - `extract_series()` - Extract neural/cardiac time series
- **State Management**:
  - 4D state: (v, w, x, y) = neural + cardiac
  - History-based delay implementation (non-integer delays)
- **Size**: 125 lines of code

### D. MICROPROCESSOR MODULE (`src/microprocessor/`)

**PrimalLogicProcessor** (primal_processor.py)
- **Type**: Hardware-accelerated integral control with exponential memory weighting
- **Mathematical Basis**: `u(t) = -K ∫₀ᵗ Θ(τ) · e(τ) · e^(-λ(t-τ)) dτ`
- **Architecture**:
  - 8 Integral Processing Units (IPUs) - parallel processing
  - Round-robin IPU scheduling
  - Hardware bounds enforcement
- **Configuration**:
  ```python
  ProcessorConfig:
    num_integral_units: int = 8
    memory_banks: int = 16
    multiply_accumulate_units: int = 32
    floating_point_units: int = 4
    io_channels: int = 64
    safety_cores: int = 2
    K_gain: float = 0.5
    lambda_decay: float = 2.0
    dt: float = 0.01
    max_control_output: float = 10.0
    min_control_output: float = -10.0
  ```
- **Key Features**:
  - Exponential memory decay (recent errors weighted higher)
  - Bounded control outputs (prevents spikes)
  - Comfort index calculation (jerk reduction)
  - State history tracking
- **Methods**:
  - `compute_control()` - Main control computation
  - `simulate_emergency_braking()` - Demo scenario
  - `export_state_csv()` - CSV output
- **Size**: 283 lines of code

**ExponentialMemoryWeighting & IntegralControlSystem** (control_system.py)
- Supporting control utilities
- Implements: `weight(t) = e^(-λ·t)`
- Methods for weighted integral computation
- Jerk reduction and comfort metrics calculation
- Size**: 214 lines of code

### E. INTEGRATION MODULE (`src/integration/`)

**MotorHandBridge** (motorhand_bridge.py)
- **Type**: Bridge layer between Primal Logic and MotorHandPro QUANT system
- **Components**:
  
  **QuantInterface**:
  - QUANT system parameter constants
  - Control-to-throttle conversion
  - CSV feedback parsing
  - Error computation from motor feedback
  
  **QuantParameters**:
  ```
  PLANCK_SCALE: 23.098341716530
  PLANCK_D: 149.9992314000
  PLANCK_I3: 6.4939394023
  KERNEL_MU: 0.169050000000
  ```
  
  **MotorHandBridge**:
  - Integrates Primal Logic control with motor system
  - Implements closed-loop control simulation
  - CSV export functionality
  - Arduino interface code generation
- **Control Flow**:
  ```
  Error → Primal Logic → Control Signal → QUANT Conversion 
  → Throttle (0-255) → Motor → Feedback (psi, gamma, Ec)
  ```
- **Size**: 399 lines of code

---

## 3. ARCHITECTURE PATTERN

### A. **Modular Composition Pattern**
- **Principle**: Each subsystem (neural, cardiac) encapsulates its own dynamics
- **Implementation**: 
  - Oscillator classes with `derivatives()` and `step()` methods
  - Standard interface for state and input/output
  - Stateless models (no history kept in models themselves)

### B. **Coupling as Orchestrator**
- **Pattern**: HeartBrainCouplingModel acts as a conductor
- **Responsibilities**:
  - Manages state history for delay lookups
  - Computes coupling terms from delayed states
  - Coordinates time stepping across subsystems
  - Extracts and formats output

### C. **Explicit Euler Integration**
- **Method**: Simple forward Euler stepping
  ```
  x(t+dt) = x(t) + dt · dx/dt
  ```
- **Trade-off**: Less stable/accurate but transparent and deterministic
- **Alternative**: Could upgrade to RK4 (mentioned in config)

### D. **Layered Control Architecture**
```
User Code / Application
    ↓
HeartBrainCouplingModel (orchestrator)
    ↓
Neural Model + Cardiac Model (subsystems)
    ↓
Microprocessor Control (Primal Logic)
    ↓
Integration Bridge (MotorHandPro QUANT)
    ↓
Hardware (Motor actuators)
```

### E. **Configuration-Driven Design**
- Parameters stored in `config/default.yaml`
- YAML structure:
  ```yaml
  simulation:
    duration, timestep, integrator
  neural:
    natural_frequency, damping, feedback_strength, delay
  cardiac:
    natural_frequency, damping, feedback_strength, delay
  outputs:
    signals to export, export path
  ```

---

## 4. EXISTING HEART, BRAIN, AND OTHER ORGAN MODELS

### Heart Models
- **Van der Pol Oscillator** - Primary cardiac model
  - Captures relaxation oscillations similar to action potentials
  - Natural frequency ~1.1 Hz (approx. 66 bpm per config)
  - Flexible parameters (μ, ω, damping)

### Brain/Neural Models
- **FitzHugh-Nagumo (FHN)** - Primary neural model
  - Canonical 2D spiking neuron model
  - Captures fast voltage dynamics + slow recovery
  - Natural frequency ~0.15 Hz per config
  - Supports external stimulus injection

### Other Organ/System Models (D Implementation)
In `source/models/`:
- **Michaelis-Menten** (mm.d) - Enzyme kinetics
- **SIR Model** (sir.d) - Epidemiological dynamics
- **Pressure-Volume Loops** - Hemodynamic modeling
- **ECG Traces** - Electrocardiogram generation
- **Neural Oscillations** - Brain electrical activity

### Expansion Potential
- Additional cardiac models: Hodgkin-Huxley, Luo-Rudy, TenTusscher
- Additional neural models: Izhikevich, Morris-Lecar, Hindmarsh-Rose
- Other systems: Respiratory, Endocrine, Immune

---

## 5. DEPENDENCIES AND FRAMEWORKS

### Core Python Dependencies
- **NumPy** - Numerical computing (arrays, exponential decay, clipping)
- **Standard Library Only** - No heavy frameworks for core models
  - `dataclasses` - Configuration and state classes
  - `collections.deque` - History buffer
  - `typing` - Type hints
  - `csv` - Data export
  - `time` - Timestamps
  - `subprocess` - Process management

### Optional Dependencies
- **Matplotlib** - Visualization (in examples, graceful fallback)
- **Pytest** - Testing framework
- **D Language** - Alternative implementation (source/)
- **APL** - Reference models (*.apl files)

### No Heavy Framework Dependencies
- ❌ No TensorFlow, PyTorch, JAX, or other ML frameworks
- ❌ No large scientific computing suites (only NumPy)
- ❌ Clean, minimal dependencies for reliability and performance
- ✅ Pure Python implementations for transparency

### Hardware Integration
- **Arduino Interface** - Generated C++ code for microcontroller deployment
- **QUANT System** - MotorHandPro quantum-inspired motor control
- **SkyWater 90nm Process** - Target manufacturing (Primal Logic)

---

## 6. TESTING FRAMEWORK

### Test Infrastructure
- **Framework**: PyTest
- **Configuration**: `tests/conftest.py`
- **Coverage**: ~1150 lines of Python code tested

### Test Organization

**Unit Tests** (`tests/test_models.py`)
- FitzHugh-Nagumo derivative calculations
- Van der Pol oscillator dynamics
- Delay-based state lookup
- Trajectory timestep verification

**Integration Tests** (`tests/integration/test_microprocessor_motorhand.py`)
Organized into test classes:
1. **TestPrimalLogicProcessor** - Processor initialization, control computation, emergency braking
2. **TestExponentialMemoryWeighting** - Weight decay, weighted integral
3. **TestQuantInterface** - QUANT parameters, throttle conversion, feedback parsing
4. **TestMotorHandBridge** - Bridge initialization, control integration, closed-loop simulation
5. **TestComfortMetrics** - Jerk reduction, comfort calculations
6. **TestIntegration** - End-to-end system tests, performance comparisons

### Test Statistics
- **Total test methods**: 30+
- **Test file lines**: ~390 (microprocessor_motorhand tests)
- **Model test lines**: ~49 (basic model tests)

### Test Utilities
- `pytest.approx()` - Floating-point tolerance
- `pytest.mark.parametrize()` - Parameterized tests
- `tmp_path` - Temporary file fixtures
- CSV validation and data export testing

### Example Test
```python
def test_coupled_simulation_produces_expected_timesteps():
    model = HeartBrainCouplingModel(
        coupling=CouplingParameters(
            neural_to_cardiac_gain=0.0, 
            cardiac_to_neural_gain=0.0
        )
    )
    trajectory = model.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0), 
        t_span=(0.0, 0.5), 
        dt=0.1
    )
    times = [time for time, _ in trajectory]
    assert len(times) == 6  # 0.0, 0.1, 0.2, 0.3, 0.4, 0.5
```

---

## 7. EXISTING COUPLING AND INTEGRATION MECHANISMS

### A. **Delay-Differential Coupling** (HeartBrainCouplingModel)

**Mechanism**:
```python
# Retrieve delayed states from history
delayed_neural = self._delayed_state(t, delay_cardiac, "neural", fallback)
delayed_cardiac = self._delayed_state(t, delay_neural, "cardiac", fallback)

# Apply coupling gains
neural_input = gain_ct2n · delayed_cardiac[0] + bias_n
cardiac_input = gain_nc2c · delayed_neural[0] + bias_c

# Update with coupling
dv, dw = neural_model.derivatives(t, neural_state, input_drive=neural_input)
dx, dy = cardiac_model.derivatives(t, cardiac_state, input_force=cardiac_input)
```

**Features**:
- History-based delay lookup (interpolation-free)
- Configurable coupling gains (0.2-0.8 typical)
- Configurable delays (Δ_bh, Δ_hb)
- Additive biases for asymmetry
- Bidirectional information flow

### B. **Control-Motor Integration** (MotorHandBridge)

**Control Loop**:
```
Primal Logic Processor
    ↓ (bounded control signal: -10 to +10)
QuantInterface (conversion)
    ↓ (throttle: 0-255)
Motor System (MotorHandPro)
    ↓ (physical actuation)
Sensor Feedback (psi, gamma, Ec)
    ↓ (error computation)
Error Signal → back to Primal Logic
```

**Conversion Mathematics**:
```python
x_fixed = (control + 10.0) * (150.0 / 20.0)  # Map [-10, +10] to [0, 150]
throttle = QUANT::throttleFromFixed(x_fixed)  # Convert to [0, 255]
```

### C. **Microprocessor-Bridge Integration**

**Closed-Loop Simulation**:
```python
for step in range(num_steps):
    # 1. Primal Logic computes control
    control, state = processor.compute_control(current_value, target_value)
    
    # 2. Bridge converts to motor command
    throttle, data = bridge.integrate_control_signal(control, feedback)
    
    # 3. Update system state (simple dynamics)
    current_value += control * dt
    
    # 4. Generate feedback
    feedback = MotorFeedback(psi=current_state, gamma=control, Ec=integral)
```

### D. **Data Export Integration**

**CSV Outputs**:
- `results.csv` - Main simulation output
- `emergency_braking_output.csv` - Primal Logic processor results
- `integration_output.csv` - Combined system output

**CSV Structure**:
```
t,velocity,error,integral,control,comfort
0.000,30.000,30.000,0.300,−0.150,50.0
0.010,29.998,29.998,0.598,−0.299,50.0
...
```

### E. **Hardware Code Generation**

**Arduino Interface Generator**:
- Generates `.ino` sketch from bridge configuration
- Implements real-time control loop
- QUANT system integration code
- Motor sensor reading and command transmission

---

## 8. KEY STATISTICS AND METRICS

| Metric | Value |
|--------|-------|
| Total Python LOC | 1,153 |
| Cardiac model LOC | 30 |
| Neural model LOC | 50 |
| Coupling model LOC | 125 |
| Microprocessor LOC | 283 |
| Integration bridge LOC | 399 |
| Test LOC | 390+ |
| Test methods | 30+ |
| Modules | 5 main (neural, cardiac, coupling, microprocessor, integration) |
| Classes | 12+ |
| Configuration files | 1 YAML |
| Example scripts | 1 comprehensive demo |

---

## 9. PERFORMANCE CHARACTERISTICS

### Primal Logic Processor Metrics
- **Jerk Reduction**: 75% vs traditional control (3.8 vs 15.2 m/s³)
- **Comfort Index**: 87.6 vs 48.3 (81% improvement)
- **Control Latency**: 50μs (hardware specification)
- **Hardware Die Area**: 180 mm² (90nm process)
- **Power Consumption**: 25W

### Simulation Performance
- **Default Timestep**: 0.01s (100 Hz)
- **Simulation Speed**: Real-time capable
- **Memory**: Deque-based history (fixed size: 16 banks)

---

## 10. PATTERNS FOR ORGAN CHIP SYSTEM INTEGRATION

### Suggested Architecture for New Modules

Based on existing patterns:

1. **Create Subsystem Modules** (like cardiac/, neural/)
   ```
   src/organ_system/
   ├── __init__.py
   └── model.py  # Similar to van_der_pol.py or fhn.py
   ```

2. **Extend Coupling Model**
   - Add new coupling terms to `hbcm.py`
   - Increase state dimensionality (from 4D to higher)
   - Add new parameters to `CouplingParameters`

3. **Maintain Standard Interface**
   - Implement `derivatives(t, state, input_signal)` 
   - Implement `step(t, state, dt, input_signal)`
   - Keep models stateless (history managed by orchestrator)

4. **Update Tests**
   - Add tests to `test_models.py` for new models
   - Add integration tests to test new couplings
   - Maintain >90% coverage target

5. **Configuration Extension**
   - Add new section to `config/default.yaml`
   - Update simulation parameters

6. **Documentation**
   - Equations in `docs/`
   - Architecture decision in `docs/architecture.md`
   - Usage examples

---

## SUMMARY

The Multi-Heart-Model codebase implements a **modular, configuration-driven framework** for simulating coupled biological systems. It combines:

1. **Core Physics**: FitzHugh-Nagumo (neural) + Van der Pol (cardiac)
2. **Coupling Strategy**: Delay-differential equations with configurable feedback
3. **Control Integration**: Primal Logic Processor with exponential memory weighting
4. **Hardware Interface**: MotorHandPro QUANT system bridge
5. **Testing**: Comprehensive pytest suite with 30+ tests
6. **Extensibility**: Clear patterns for adding new organ systems

The architecture is **lightweight** (no heavy ML frameworks), **transparent** (readable equations), and **production-ready** (hardware deployment capable).
