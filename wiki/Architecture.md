# Architecture Overview

This page provides a comprehensive overview of the Multi-Heart-Model architecture, design patterns, and system organization.

## 📐 System Architecture

### Layered Design

```
┌─────────────────────────────────────────────────┐
│         User Applications / Scripts              │
├─────────────────────────────────────────────────┤
│     Orchestrators (HBCM, OrganChipSuite)        │
├─────────────────────────────────────────────────┤
│  Subsystems (Neural, Cardiac, Organ Models)     │
├─────────────────────────────────────────────────┤
│    Control Layer (Primal Logic Processor)       │
├─────────────────────────────────────────────────┤
│   Hardware Interface (MotorHandPro QUANT)       │
└─────────────────────────────────────────────────┘
```

### Core Design Principles

1. **Minimal Dependencies**: Only NumPy + stdlib (no heavy frameworks)
2. **Transparency**: Explicit Euler integration, readable code
3. **Modularity**: Each subsystem is self-contained with standard interfaces
4. **Type Safety**: Comprehensive type hints throughout
5. **Production-Ready**: Hardware deployment paths, comprehensive testing
6. **Documentation First**: Extensive docs at multiple levels

## 🏗️ Directory Structure

```
Multi-Heart-Model/
├── config/                 # YAML simulation parameters
│   └── default.yaml        # Default configuration
├── data/                   # Experimental data (ready for use)
├── docs/                   # Comprehensive documentation (15 files)
│   ├── INDEX.md            # Documentation navigation
│   ├── QUICK_REFERENCE.md  # Quick lookup reference
│   └── ARCHITECTURE_OVERVIEW.md  # Complete technical guide
├── examples/               # Demonstration scripts
│   ├── microprocessor_motorhand_demo.py
│   ├── organ_chip/         # Advanced organ chip demos
│   └── organchip/          # Complete system demos
├── source/                 # D language implementation
│   ├── app.d               # Main application (3,308 LOC)
│   └── models/             # Physiology models in D
├── src/                    # PRIMARY PYTHON SOURCE (7,271 LOC)
│   ├── cardiac/            # Van der Pol cardiac oscillator
│   ├── neural/             # FitzHugh-Nagumo neural model
│   ├── coupling/           # Heart-Brain coupling orchestrator
│   ├── microprocessor/     # Primal Logic Processor
│   ├── integration/        # MotorHandPro bridge
│   ├── organ_chip/         # Advanced organ-on-chip suite
│   └── organchip/          # Complete toxicity screening
├── tests/                  # Test suite (1,024 LOC)
│   ├── test_models.py      # Unit tests
│   ├── integration/        # Integration tests
│   └── organchip/          # Organ chip tests
└── *.apl                   # APL reference models
```

## 🔄 Architectural Patterns

### 1. Modular Composition Pattern

Each model encapsulates its own dynamics with a standard interface:

```python
class PhysiologicalModel:
    """Standard interface for all physiological models."""

    def derivatives(self, t: float, state: Tuple, input: float) -> Tuple:
        """
        Compute state derivatives.

        Args:
            t: Current time
            state: Current state vector
            input: External input signal

        Returns:
            State derivatives
        """
        pass

    def step(self, t: float, state: Tuple, dt: float, input: float) -> Tuple:
        """
        Advance state by one timestep using Euler integration.

        Args:
            t: Current time
            state: Current state
            dt: Time step size
            input: External input

        Returns:
            New state
        """
        derivs = self.derivatives(t, state, input)
        return tuple(s + dt * ds for s, ds in zip(state, derivs))
```

**Benefits**:
- Uniform interface across all models
- Easy to swap implementations
- Testable in isolation
- Composable into larger systems

### 2. Orchestrator Pattern

Orchestrators like `HeartBrainCouplingModel` and `OrganChipSuite` coordinate multiple subsystems:

```python
class HeartBrainCouplingModel:
    """Orchestrates bidirectional neural-cardiac coupling."""

    def __init__(self, neural_model, cardiac_model, coupling):
        self.neural = neural_model
        self.cardiac = cardiac_model
        self.coupling = coupling
        self.history = deque(maxlen=10000)  # For delay lookups

    def step(self, t, state, dt):
        """Coupled integration step."""
        # Extract subsystem states
        neural_state = state[:2]
        cardiac_state = state[2:4]

        # Get delayed states for coupling
        neural_delayed = self._delayed_state(t, "neural")
        cardiac_delayed = self._delayed_state(t, "cardiac")

        # Compute coupling inputs
        cardiac_input = self.coupling.n_to_c_gain * neural_delayed[0]
        neural_input = self.coupling.c_to_n_gain * cardiac_delayed[0]

        # Step each subsystem
        new_neural = self.neural.step(t, neural_state, dt, neural_input)
        new_cardiac = self.cardiac.step(t, cardiac_state, dt, cardiac_input)

        # Combine and store in history
        new_state = new_neural + new_cardiac
        self.history.append((t + dt, new_neural, new_cardiac))

        return new_state
```

**Responsibilities**:
- Manage state history for delay-differential equations
- Coordinate time stepping across subsystems
- Extract and format outputs
- Handle coupling logic

### 3. Parameter Object Pattern

Type-safe parameter containers using dataclasses:

```python
from dataclasses import dataclass

@dataclass
class CouplingParameters:
    """Heart-brain coupling configuration."""
    neural_to_cardiac_gain: float = 0.5
    cardiac_to_neural_gain: float = 0.3
    neural_to_cardiac_delay: float = 0.12  # seconds
    cardiac_to_neural_delay: float = 0.15  # seconds

@dataclass
class FitzHughNagumoParameters:
    """FitzHugh-Nagumo model parameters."""
    a: float = 0.7
    b: float = 0.8
    c: float = 3.0
    stimulus_amplitude: float = 0.5
```

**Benefits**:
- Type checking
- Default values
- Self-documenting
- Easy to serialize/deserialize

## 🧩 Core Components

### Neural System (FitzHugh-Nagumo)

**File**: `src/neural/fitzhugh_nagumo.py`

**Purpose**: Two-dimensional neural oscillator model

**State Variables**:
- `v`: Voltage (activation)
- `w`: Recovery variable

**Equations**:
```
dv/dt = v - v³/3 - w + I_ext
dw/dt = (v + a - b*w) / c
```

**Parameters**:
- `a`: 0.7 (default) - affects nullcline position
- `b`: 0.8 (default) - recovery rate
- `c`: 3.0 (default) - timescale separation
- `stimulus_amplitude`: External input strength

### Cardiac System (Van der Pol)

**File**: `src/cardiac/van_der_pol.py`

**Purpose**: Cardiac relaxation oscillator

**State Variables**:
- `x`: Position (displacement)
- `y`: Velocity

**Equations**:
```
dx/dt = y
dy/dt = μ(1 - x²)y - ω²x + I_ext
```

**Parameters**:
- `mu`: 1.5 (default) - nonlinearity strength
- `omega`: 1.0 (default) - natural frequency
- `damping`: 0.1 (default) - damping coefficient

### Coupling System

**File**: `src/coupling/hbcm.py`

**Purpose**: Bidirectional neural-cardiac coupling with delays

**Key Features**:
- Delay-differential equation support
- History buffer management
- Configurable coupling gains
- Physiological delay times (120-150ms)

**State Representation**:
```python
state = (v, w, x, y)
         |---neural---| |---cardiac---|
```

### Primal Logic Processor

**File**: `src/microprocessor/primal_logic.py`

**Purpose**: Hardware integral controller

**Functions**:
- Proportional-integral control
- Error accumulation
- Saturation handling
- Reset capabilities

### Organ-On-Chip Platform

**File**: `src/organchip/suite.py`

**Purpose**: Multi-organ drug toxicity screening

**Organ Models**:
1. **CardiacCell**: Ion channel dynamics, hERG inhibition
2. **Hepatocyte**: CYP450 metabolism, drug clearance
3. **EndothelialCell**: Barrier function, inflammation
4. **ImmuneCell**: Cytokine release, activation
5. **NeuronCell**: Synaptic transmission, neurotoxicity
6. **KidneyCell**: Filtration, clearance (extensible)

## 🔀 Data Flow

### Heart-Brain Coupling Simulation

```
1. Initialize Models
   ↓
2. Set Initial State (v, w, x, y)
   ↓
3. For each timestep:
   a. Look up delayed states
   b. Compute coupling inputs
   c. Step neural model → new (v, w)
   d. Step cardiac model → new (x, y)
   e. Store in history
   f. Combine states
   ↓
4. Extract time series
   ↓
5. Return results
```

### Organ-On-Chip Drug Test

```
1. Initialize OrganChipSuite
   ↓
2. Configure drug parameters (IC50, dose)
   ↓
3. For each timestep:
   a. Compute drug concentration in blood
   b. Update each organ with drug exposure
   c. Compute organ interactions
   d. Extract biomarkers
   e. Compute toxicity scores
   ↓
4. Aggregate results
   ↓
5. Return toxicity profile
```

## 🧮 Numerical Methods

### Euler Integration

Default method for all models:

```python
def euler_step(state, derivatives, dt):
    """Forward Euler integration."""
    return tuple(s + dt * ds for s, ds in zip(state, derivatives))
```

**Advantages**:
- Simple and transparent
- Easy to debug
- Low computational cost

**Limitations**:
- Requires small timesteps (dt ≤ 0.001)
- Can be unstable for stiff systems
- First-order accuracy

**Recommended timestep**: `dt = 0.001` (1 millisecond)

### Delay-Differential Equations

History buffer for past states:

```python
from collections import deque

class CouplingModel:
    def __init__(self):
        self.history = deque(maxlen=10000)

    def _delayed_state(self, t, delay, system, default):
        """Look up state from delay seconds ago."""
        target_time = t - delay

        for hist_t, neural, cardiac in reversed(self.history):
            if hist_t <= target_time:
                return neural if system == "neural" else cardiac

        return default  # Use default if history insufficient
```

## 🔧 Extension Points

### Adding a New Neural Model

1. Create `src/neural/your_model.py`
2. Implement `derivatives()` and `step()` methods
3. Add to `src/neural/__init__.py`
4. Write tests in `tests/test_neural/`
5. Update documentation

### Adding a New Organ Model

1. Create organ cell class with `step()` method
2. Add `get_biomarkers()` method
3. Integrate into `OrganChipSuite`
4. Add toxicity scoring logic
5. Write integration tests

### Adding Custom Coupling

1. Extend `CouplingParameters` dataclass
2. Modify coupling logic in orchestrator
3. Update delay lookup if needed
4. Add configuration options
5. Document new parameters

## 🎯 Design Decisions

### Why Euler Integration?

**Decision**: Use explicit Euler instead of RK4 or adaptive methods

**Rationale**:
- Transparency over sophistication
- Easy to understand and debug
- Sufficient for non-stiff physiological models
- Minimal code complexity

**Trade-off**: Requires smaller timesteps but provides clarity

### Why Separate Orchestrators?

**Decision**: Use orchestrator pattern instead of monolithic simulator

**Rationale**:
- Separation of concerns
- Easy to test subsystems independently
- Flexible coupling configurations
- Can swap implementations

**Trade-off**: Slightly more code but much more maintainable

### Why Type Hints Everywhere?

**Decision**: Comprehensive type annotations

**Rationale**:
- Catch errors early
- Better IDE support
- Self-documenting code
- Enables static analysis

**Trade-off**: More verbose but much safer

### Why Multiple Language Implementations?

**Decision**: Python (primary), D (performance), APL (reference)

**Rationale**:
- Python: Accessibility and ecosystem
- D: High-performance production deployments
- APL: Mathematical clarity and validation

**Trade-off**: Maintenance overhead justified by use cases

## 📊 Performance Considerations

### Memory Usage

- **History buffer**: O(n) where n = delay / dt
- **State storage**: O(t_total / dt) for full trajectory
- **Typical simulation**: ~10-50 MB for 60 second run

### Computational Complexity

- **Per timestep**: O(1) for basic coupling
- **Organ chip**: O(n_organs) per timestep
- **Delay lookup**: O(log n) with binary search (currently O(n))

### Optimization Opportunities

1. **Use D implementation** for production (10-100x speedup)
2. **Reduce history storage** for shorter delays
3. **Implement binary search** for delay lookups
4. **Use NumPy vectorization** for batch processing
5. **Profile bottlenecks** with cProfile

## 🔒 Safety and Validation

### Type Safety

- All public APIs have type hints
- Dataclasses for parameters
- Runtime validation in constructors

### Numerical Stability

- Timestep validation (warn if dt > 0.01)
- Parameter range checking
- NaN/Inf detection in integration

### Hardware Safety

- Control signal clamping [0, 1]
- Saturation limits in controllers
- Emergency shutdown protocols

## 📚 Related Documentation

- **[API Reference](API-Reference)** - Detailed API documentation
- **[Development Guide](Development-Guide)** - Contributing guidelines
- **[Testing Guide](Testing)** - Testing strategies
- **[Examples](Examples)** - Code examples demonstrating architecture

---

**See Also**:
- `docs/ARCHITECTURE_OVERVIEW.md` - Detailed technical documentation
- `docs/architecture.md` - Mathematical formulation
- `CLAUDE.md` - AI assistant guide with architectural patterns
