# CLAUDE.md - AI Assistant Guide for Multi-Heart-Model Repository

**Last Updated:** 2025-11-13
**Repository:** Multi-Heart-Model (Heart-Brain Coupling Model)
**License:** MIT

This document provides comprehensive guidance for AI assistants working with the Multi-Heart-Model codebase. It covers architecture, conventions, workflows, and best practices to help AI assistants effectively understand and contribute to this project.

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Codebase Structure](#codebase-structure)
3. [Development Philosophy](#development-philosophy)
4. [Key Conventions](#key-conventions)
5. [Common Tasks](#common-tasks)
6. [Testing Guidelines](#testing-guidelines)
7. [Git Workflow](#git-workflow)
8. [Documentation](#documentation)
9. [Important Gotchas](#important-gotchas)
10. [Extension Patterns](#extension-patterns)

---

## Repository Overview

### Purpose

The Multi-Heart-Model repository implements the **Heart-Brain Coupling Model (HBCM)**, a multi-domain physiological modeling platform that integrates:

1. **Core Heart-Brain Coupling**: Bidirectional neural-cardiac interactions using delay-differential equations
2. **Hardware Control Integration**: Primal Logic Processor for automotive control applications
3. **Organ-On-Chip Platform**: Drug toxicity screening with mechanistic multi-organ models
4. **Multi-Language Support**: Python (primary), D (high-performance), APL (reference)

### Key Statistics

- **Total Python LOC:** 7,271 (57 files)
- **Test LOC:** 1,024 (30+ test methods)
- **Documentation:** 3,649 lines across 15 files
- **Test Coverage:** ~100% of production code
- **Dependencies:** Minimal (NumPy + stdlib)
- **License:** MIT

### Core Models

1. **VanDerPolOscillator**: Cardiac relaxation oscillator (30 LOC)
2. **FitzHughNagumo**: Two-dimensional neural oscillator (50 LOC)
3. **HeartBrainCouplingModel**: Bidirectional coupling orchestrator (125 LOC)
4. **PrimalLogicProcessor**: Hardware integral controller (283 LOC)
5. **OrganChipSuite**: Multi-organ drug toxicity platform (2,942 LOC)

---

## Codebase Structure

### Directory Layout

```
Multi-Heart-Model/
├── .github/workflows/       # CI/CD (D language builds)
├── config/                  # YAML simulation parameters
│   └── default.yaml         # Default simulation config
├── data/                    # Experimental data (empty, ready for use)
├── disabled/                # Archived/deprecated assets
├── docs/                    # Comprehensive documentation (15 files)
│   ├── INDEX.md             # Documentation navigation guide
│   ├── QUICK_REFERENCE.md   # Quick lookup reference
│   ├── ARCHITECTURE_OVERVIEW.md  # Complete technical guide
│   └── [other docs]
├── examples/                # Demonstration scripts
│   ├── microprocessor_motorhand_demo.py
│   ├── organ_chip/          # Advanced organ chip demos
│   └── organchip/           # Complete system demos
├── source/                  # D language implementation
│   ├── app.d                # Main application (3,308 LOC)
│   ├── models/              # Physiology models in D
│   └── [other D files]
├── src/                     # PRIMARY PYTHON SOURCE (7,271 LOC)
│   ├── cardiac/             # Van der Pol cardiac oscillator
│   │   ├── __init__.py
│   │   └── van_der_pol.py
│   ├── neural/              # FitzHugh-Nagumo neural model
│   │   ├── __init__.py
│   │   └── fitzhugh_nagumo.py
│   ├── coupling/            # Heart-Brain coupling orchestrator
│   │   ├── __init__.py
│   │   └── hbcm.py
│   ├── microprocessor/      # Primal Logic Processor
│   │   ├── __init__.py
│   │   └── primal_logic.py
│   ├── integration/         # MotorHandPro bridge
│   │   ├── __init__.py
│   │   └── motorhand_bridge.py
│   ├── organ_chip/          # Advanced organ-on-chip suite
│   │   └── [7 model files]
│   └── organchip/           # Complete toxicity screening
│       └── [6 model files]
├── tests/                   # Test suite (1,024 LOC)
│   ├── conftest.py          # Pytest configuration
│   ├── test_models.py       # Unit tests
│   ├── integration/         # Integration tests
│   ├── organ_chip/          # Organ chip tests
│   └── organchip/           # Organ chip suite tests
├── *.apl                    # APL reference models (5 files)
├── Makefile                 # D build targets
├── dub.json                 # D build configuration
├── primal_overlay           # Compiled D executable
├── validate_integration.py  # Integration validation
├── validate_organchip.py    # Organ chip validation
└── README.md                # Project overview

```

### Key Source Files by Priority

**Essential (read first):**
- `src/coupling/hbcm.py` - Main coupling orchestrator (125 LOC)
- `src/cardiac/van_der_pol.py` - Cardiac model (30 LOC)
- `src/neural/fitzhugh_nagumo.py` - Neural model (50 LOC)

**Hardware Integration:**
- `src/microprocessor/primal_logic.py` - Control processor (283 LOC)
- `src/integration/motorhand_bridge.py` - Motor interface (399 LOC)

**Organ-On-Chip (choose one implementation):**
- `src/organchip/` - Complete system (2,942 LOC) - **RECOMMENDED**
- `src/organ_chip/` - Advanced suite (3,171 LOC)

**D Language:**
- `source/app.d` - D implementation (3,308 LOC)

---

## Development Philosophy

### Design Principles

1. **Minimal Dependencies**: Only NumPy + stdlib (no heavy frameworks)
2. **Transparency**: Explicit Euler integration, readable code
3. **Modularity**: Each subsystem is self-contained with standard interfaces
4. **Type Safety**: Comprehensive type hints throughout
5. **Production-Ready**: Hardware deployment paths, comprehensive testing
6. **Documentation First**: Extensive docs at multiple levels

### Architectural Patterns

**Modular Composition:**
- Each model encapsulates its own dynamics
- Standard interface: `derivatives(t, state, input)` and `step(t, state, dt, input)`
- Models are stateless (history managed by orchestrators)

**Orchestrator Pattern:**
- `HeartBrainCouplingModel` and `OrganChipSuite` act as conductors
- Manage state history for delay-differential equations
- Coordinate time stepping across subsystems
- Extract and format outputs

**Layered Control:**
```
User Code / Application
    ↓
Orchestrator (HBCM / OrganChipSuite)
    ↓
Subsystems (Neural / Cardiac / Organs)
    ↓
Control Layer (Primal Logic Processor)
    ↓
Hardware Interface (MotorHandPro QUANT)
```

---

## Key Conventions

### Python Code Style

**Type Hints:**
```python
def derivatives(self, t: float, state: Tuple[float, float],
                input_drive: float = 0.0) -> Tuple[float, float]:
    """Compute derivatives with full type annotations."""
    pass
```

**Dataclasses for Configuration:**
```python
from dataclasses import dataclass

@dataclass
class CouplingParameters:
    """Type-safe parameter container."""
    neural_to_cardiac_gain: float = 0.5
    cardiac_to_neural_gain: float = 0.3
    neural_to_cardiac_delay: float = 0.12
    cardiac_to_neural_delay: float = 0.15
```

**Docstrings:**
```python
def simulate(self, initial_state, t_span, dt):
    """
    Simulate the coupled system.

    Args:
        initial_state: Tuple (v, w, x, y) - initial conditions
        t_span: Tuple (t_start, t_end) - time interval
        dt: float - time step size

    Returns:
        List of (time, state) tuples
    """
```

### Naming Conventions

- **Classes:** PascalCase (`VanDerPolOscillator`, `HeartBrainCouplingModel`)
- **Functions/Methods:** snake_case (`compute_control`, `simulate_emergency_braking`)
- **Constants:** UPPER_CASE (`PLANCK_SCALE`, `IC50_hERG`)
- **Private methods:** `_delayed_state`, `_compute_delayed_input`
- **Module imports:** Always use `__all__` in `__init__.py`

### File Organization

- **One main class per file** (name file after class in snake_case)
- **Supporting classes in same file** as main class
- **`__init__.py` exports** define public API
- **Tests mirror source structure** (`src/cardiac/` → `tests/test_cardiac/`)

### Mathematical Conventions

**State Representation:**
- Neural: `(v, w)` where v=voltage, w=recovery
- Cardiac: `(x, y)` where x=position, y=velocity
- Combined: `(v, w, x, y)` - neural then cardiac

**Time Variables:**
- `t` - current time
- `dt` - time step
- `t_span` - (start, end) tuple
- `delay` - communication delay in seconds

**Integration:**
- Default: Explicit Euler (`x_new = x + dt * dx_dt`)
- Alternative: RK4 (mentioned in config, not widely implemented)

---

## Common Tasks

### 1. Running Simulations

**Basic Heart-Brain Coupling:**
```python
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import CouplingParameters, HeartBrainCouplingModel

# Create model
hbcm = HeartBrainCouplingModel(
    neural_model=FitzHughNagumo(stimulus_amplitude=0.2),
    cardiac_model=VanDerPolOscillator(mu=1.2, omega=1.0),
    coupling=CouplingParameters(
        neural_to_cardiac_gain=0.5,
        cardiac_to_neural_gain=0.3
    ),
)

# Run simulation
trajectory = hbcm.simulate(
    initial_state=(0.0, 0.0, 1.0, 0.0),
    t_span=(0.0, 10.0),
    dt=0.01
)

# Extract time series
times, neural, cardiac = hbcm.extract_series(trajectory)
```

**Organ-On-Chip Drug Screening:**
```python
from src.organchip.orchestrator import OrganChipSuite

# Create platform
suite = OrganChipSuite()

# Run drug test
results = suite.run_drug_test(
    drug_name="Doxorubicin",
    dose_mg_kg=5.0,
    duration_hours=48.0,
    dt_minutes=1.0
)

# Check toxicity
print(f"Cardiotoxicity: {results['toxicity_scores']['cardiac']}")
print(f"Hepatotoxicity: {results['toxicity_scores']['hepatic']}")
```

### 2. Building and Testing

**Python Tests:**
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html
```

**Validation Scripts:**
```bash
# Validate microprocessor integration
python validate_integration.py

# Validate organ chip suite
python validate_organchip.py
```

**D Language Build:**
```bash
# Build D executable
make build
# or: dub build --compiler=ldc2 --build=release

# Run D executable
./primal_overlay

# Clean build artifacts
make clean
```

### 3. Viewing Results

**Python Visualization:**
```python
import matplotlib.pyplot as plt

times, neural, cardiac = hbcm.extract_series(trajectory)

plt.figure(figsize=(12, 6))
plt.subplot(2, 1, 1)
plt.plot(times, [v for v, w in neural], label='Neural v')
plt.subplot(2, 1, 2)
plt.plot(times, [x for x, y in cardiac], label='Cardiac x')
plt.show()
```

**CSV Export:**
```python
import csv

with open('results.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['time', 'neural_v', 'cardiac_x'])
    for i, t in enumerate(times):
        writer.writerow([t, neural[i][0], cardiac[i][0]])
```

### 4. Modifying Parameters

**Via Code:**
```python
from src.neural import FitzHughNagumo

# Create with custom parameters
model = FitzHughNagumo(
    a=0.7,
    b=0.8,
    c=3.0,
    stimulus_amplitude=0.5
)
```

**Via Configuration (config/default.yaml):**
```yaml
neural:
  natural_frequency: 0.15
  damping: 0.05
  feedback_strength: 0.8
  delay_to_heart: 0.120

cardiac:
  natural_frequency: 1.1
  damping: 0.12
  feedback_strength: 0.6
  delay_to_brain: 0.150
```

### 5. Adding a New Organ Model

**Follow the Pattern:**
```python
from dataclasses import dataclass
from typing import Tuple

@dataclass
class KidneyParameters:
    """Kidney model parameters."""
    gfr: float = 120.0  # ml/min
    clearance_rate: float = 0.5

class KidneyCell:
    """Kidney cell model for nephrotoxicity."""

    def __init__(self, params: KidneyParameters = None):
        self.params = params or KidneyParameters()

    def step(self, t: float, state: Tuple[float, ...],
             dt: float, drug_conc: float = 0.0) -> Tuple[float, ...]:
        """
        Advance kidney state by one timestep.

        Args:
            t: Current time
            state: Current kidney state
            dt: Time step
            drug_conc: Drug concentration

        Returns:
            New kidney state
        """
        # Implementation here
        pass

    def get_biomarkers(self, state: Tuple[float, ...]) -> dict:
        """Extract kidney biomarkers."""
        return {
            'creatinine': state[0],
            'bun': state[1],
        }
```

**Add to OrganChipSuite:**
1. Add kidney as attribute in `__init__`
2. Update `step` method to include kidney
3. Add kidney biomarkers to outputs
4. Create integration tests

---

## Testing Guidelines

### Test Structure

**Unit Tests (tests/test_models.py):**
- Test individual model derivatives
- Test parameter initialization
- Test edge cases
- Use `pytest.approx` for float comparisons

**Integration Tests (tests/integration/):**
- Test coupled system behavior
- Test delay lookups
- Test end-to-end workflows
- Test hardware interfaces

**Validation Scripts:**
- `validate_integration.py` - Microprocessor integration
- `validate_organchip.py` - Organ chip platform

### Testing Patterns

**Parameterized Tests:**
```python
@pytest.mark.parametrize(
    "state,input_drive,expected",
    [
        ((0.0, 0.0), 0.0, (0.0, pytest.approx(0.7 / 3.0))),
        ((1.0, -0.5), 0.1, (pytest.approx(1.533), pytest.approx(0.9))),
    ],
)
def test_fitzhugh_nagumo_derivatives(state, input_drive, expected):
    model = FitzHughNagumo()
    dv, dw = model.derivatives(0.0, state, input_drive=input_drive)
    assert (dv, dw) == expected
```

**Floating Point Comparisons:**
```python
# Use pytest.approx for floats
assert value == pytest.approx(expected_value)
assert value == pytest.approx(expected_value, rel=1e-6)
```

**Fixture Usage:**
```python
# conftest.py
import pytest

@pytest.fixture
def coupling_model():
    """Provide a standard coupling model for tests."""
    from src.coupling import HeartBrainCouplingModel
    return HeartBrainCouplingModel()
```

### Test Coverage Expectations

- **Unit tests:** 100% coverage of core models
- **Integration tests:** All coupling mechanisms
- **Validation tests:** End-to-end workflows
- **Edge cases:** Boundary conditions, zero inputs, extreme parameters

---

## Git Workflow

### Branch Strategy

**Development Branches:**
- Pattern: `claude/claude-md-{session-id}`
- Always develop on the specified feature branch
- Never push to main/master without explicit permission

**Creating Feature Branch:**
```bash
# Branch is usually created automatically
# If needed:
git checkout -b claude/claude-md-mhxv0p03m5wx83bf-01CJRjzkoXvFsZaF2vbbcoPJ
```

### Commit Guidelines

**Commit Message Format:**
```
Add comprehensive organ chip simulation system

- Implement CardiacCell with ion channel dynamics
- Add Hepatocyte with CYP450 metabolism
- Create OrganChipSuite orchestrator
- Add integration tests for multi-organ coupling
```

**Commit Best Practices:**
- Focus on "why" rather than "what"
- Keep commits atomic (one logical change)
- Include context for complex changes
- Reference issues when applicable

**Committing Changes:**
```bash
# Check status
git status

# Review changes
git diff

# Stage changes
git add src/organchip/cardiac.py tests/organchip/test_cardiac.py

# Commit with message
git commit -m "$(cat <<'EOF'
Add cardiac cell model with hERG channel dynamics

Implements complete action potential generation with drug-induced
QT prolongation for cardiotoxicity screening.
EOF
)"
```

### Push Protocol

**Standard Push:**
```bash
# Push with upstream tracking
git push -u origin claude/claude-md-mhxv0p03m5wx83bf-01CJRjzkoXvFsZaF2vbbcoPJ
```

**Retry Logic (if network fails):**
```bash
# Retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s)
for i in 1 2 3 4; do
    git push -u origin <branch> && break || sleep $((2**i))
done
```

**Important Git Rules:**
- NEVER update git config
- NEVER run destructive commands (hard reset, force push to main)
- NEVER skip hooks (--no-verify)
- NEVER amend other developers' commits
- Always check authorship before amending

### Creating Pull Requests

**Using gh CLI:**
```bash
# Create PR with detailed description
gh pr create --title "Add comprehensive organ chip simulation system" --body "$(cat <<'EOF'
## Summary
- Implement complete multi-organ toxicity screening platform
- Add cardiac, hepatic, and immune system models
- Create orchestration layer for multi-organ coupling
- Add comprehensive integration tests

## Test Plan
- [x] Unit tests for each organ model
- [x] Integration tests for organ coupling
- [x] Validation tests for drug screening workflow
- [x] Example demonstrations in examples/organchip/
EOF
)"
```

---

## Documentation

### Documentation Structure

**Levels of Documentation:**
1. **Quick Reference** (`docs/QUICK_REFERENCE.md`) - Fast lookups
2. **Executive Overview** (`docs/CODEBASE_ANALYSIS_SUMMARY.md`) - High-level
3. **Technical Guide** (`docs/ARCHITECTURE_OVERVIEW.md`) - Complete details
4. **Visual Diagrams** (`docs/ARCHITECTURE_DIAGRAM.txt`) - System flow
5. **Specialized Guides** (`docs/ORGAN_CHIP_GUIDE.md`, etc.)

### Navigation Guide

**New Developer Path:**
1. `docs/QUICK_REFERENCE.md` (5 min)
2. `docs/ARCHITECTURE_DIAGRAM.txt` (10 min)
3. `docs/ARCHITECTURE_OVERVIEW.md` (30 min)
4. Examine code in `src/`
5. Run tests: `pytest tests/ -v`

**Adding Features:**
1. `docs/ARCHITECTURE_OVERVIEW.md` - Understand patterns
2. `docs/QUICK_REFERENCE.md` - Check conventions
3. Study similar models in `src/`
4. Follow modular composition pattern
5. Add comprehensive tests

### Key Documentation Files

**Must Read:**
- `README.md` - Project overview and quick start
- `docs/INDEX.md` - Documentation navigation
- `docs/QUICK_REFERENCE.md` - Parameter tables and examples

**Technical Reference:**
- `docs/ARCHITECTURE_OVERVIEW.md` - Complete architecture
- `docs/architecture.md` - Mathematical formulation
- `docs/hbcm_overview.md` - HBCM model details

**Specialized:**
- `docs/ORGAN_CHIP_GUIDE.md` - Organ chip platform
- `docs/microprocessor_motorhand_integration.md` - Hardware integration
- `src/README.md` - Source code overview

---

## Important Gotchas

### 1. Delay-Differential Equations

**Issue:** Delay lookups require history buffer
```python
# WRONG - No history management
def step(self, t, state, dt):
    delayed = state  # Uses current state!

# RIGHT - Proper history lookup
def step(self, t, state, dt):
    delayed = self._delayed_state(t, delay=0.12, system="neural", default=state)
```

### 2. State Ordering

**Convention:** Neural state comes before cardiac state
```python
# State tuple: (v, w, x, y)
#              |--neural--| |--cardiac--|
initial_state = (0.0, 0.0, 1.0, 0.0)
```

### 3. Time Units

**All times in seconds:**
- `dt = 0.001` - 1 millisecond timestep
- `delay = 0.120` - 120 millisecond delay
- `t_span = (0.0, 10.0)` - 10 second simulation

**Except organ chip:**
- Some organ chip models use minutes/hours
- Check docstrings for units

### 4. Parameter Ranges

**Physiologically Valid Ranges:**
```python
# Neural (FitzHugh-Nagumo)
a: 0.5 - 1.0
b: 0.5 - 1.0
c: 1.0 - 5.0

# Cardiac (Van der Pol)
mu: 0.5 - 3.0
omega: 0.5 - 2.0

# Coupling
gain: 0.0 - 1.0
delay: 0.05 - 0.5 seconds
```

### 5. Integration Stability

**Euler Integration Limitations:**
- Small timesteps required (`dt <= 0.001`)
- Can become unstable with stiff systems
- Trade-off: simplicity vs stability

**Signs of Instability:**
- Exponentially growing values
- NaN or Inf in results
- Oscillations growing unbounded

**Solutions:**
- Reduce timestep
- Add damping
- Consider RK4 integration
- Check parameter ranges

### 6. Hardware Deployment

**QUANT System Requirements:**
```python
# Control values must be in range [0.0, 1.0]
control = np.clip(control, 0.0, 1.0)

# Throttle values in range [0, 255]
throttle = int(control * 255)
```

### 7. Drug Concentrations

**IC50 Values:**
- Units: typically μM (micromolar)
- Check literature for specific drugs
- Default hERG IC50: 0.1 - 10 μM

### 8. File Imports

**Always use package imports:**
```python
# WRONG
from van_der_pol import VanDerPolOscillator

# RIGHT
from src.cardiac import VanDerPolOscillator
```

---

## Extension Patterns

### Adding a New Neural Model

**Create new file: `src/neural/hodgkin_huxley.py`**
```python
from dataclasses import dataclass
from typing import Tuple

@dataclass
class HodgkinHuxleyParameters:
    """Parameters for Hodgkin-Huxley model."""
    C_m: float = 1.0  # membrane capacitance
    g_Na: float = 120.0  # sodium conductance
    g_K: float = 36.0  # potassium conductance
    g_L: float = 0.3  # leak conductance
    # ... other parameters

class HodgkinHuxleyNeuron:
    """Hodgkin-Huxley neuron model."""

    def __init__(self, params: HodgkinHuxleyParameters = None):
        self.params = params or HodgkinHuxleyParameters()

    def derivatives(self, t: float, state: Tuple[float, float, float, float],
                   input_current: float = 0.0) -> Tuple[float, float, float, float]:
        """
        Compute derivatives of HH state variables.

        Args:
            t: Current time (seconds)
            state: (V, m, h, n) - voltage and gating variables
            input_current: External current (μA/cm²)

        Returns:
            (dV/dt, dm/dt, dh/dt, dn/dt)
        """
        V, m, h, n = state

        # Alpha and beta functions
        alpha_m = 0.1 * (V + 40) / (1 - np.exp(-(V + 40) / 10))
        # ... implement full HH equations

        return (dV_dt, dm_dt, dh_dt, dn_dt)

    def step(self, t: float, state: Tuple[float, ...], dt: float,
             input_current: float = 0.0) -> Tuple[float, ...]:
        """Forward Euler integration step."""
        derivs = self.derivatives(t, state, input_current)
        return tuple(s + dt * ds for s, ds in zip(state, derivs))
```

**Update `src/neural/__init__.py`:**
```python
from .fitzhugh_nagumo import FitzHughNagumo
from .hodgkin_huxley import HodgkinHuxleyNeuron, HodgkinHuxleyParameters

__all__ = [
    "FitzHughNagumo",
    "HodgkinHuxleyNeuron",
    "HodgkinHuxleyParameters",
]
```

**Add tests: `tests/test_neural/test_hodgkin_huxley.py`**
```python
import pytest
from src.neural import HodgkinHuxleyNeuron

def test_resting_potential():
    """Test that neuron settles to resting potential."""
    model = HodgkinHuxleyNeuron()
    state = (-65.0, 0.05, 0.6, 0.32)  # resting state

    # Should remain near resting with no input
    for _ in range(100):
        state = model.step(0.0, state, dt=0.01, input_current=0.0)

    assert abs(state[0] - (-65.0)) < 1.0  # voltage near -65 mV
```

### Adding Coupling to New Models

**Extend HeartBrainCouplingModel:**
```python
class MultiSystemCouplingModel:
    """Couple neural, cardiac, and respiratory systems."""

    def __init__(self, neural_model, cardiac_model, respiratory_model,
                 coupling_params):
        self.neural = neural_model
        self.cardiac = cardiac_model
        self.respiratory = respiratory_model
        self.coupling = coupling_params
        self.history = deque(maxlen=10000)

    def step(self, t, state, dt):
        """Coupled integration step."""
        # Extract individual states
        neural_state = state[:2]
        cardiac_state = state[2:4]
        respiratory_state = state[4:6]

        # Get delayed states for coupling
        neural_delayed = self._delayed_state(t, self.coupling.delay_nc,
                                             "neural", neural_state)
        cardiac_delayed = self._delayed_state(t, self.coupling.delay_cn,
                                              "cardiac", cardiac_state)

        # Compute coupling inputs
        cardiac_input = self.coupling.n_to_c_gain * neural_delayed[0]
        neural_input = self.coupling.c_to_n_gain * cardiac_delayed[0]
        respiratory_input = # ... combination of both

        # Step each subsystem
        new_neural = self.neural.step(t, neural_state, dt, neural_input)
        new_cardiac = self.cardiac.step(t, cardiac_state, dt, cardiac_input)
        new_respiratory = self.respiratory.step(t, respiratory_state, dt,
                                                respiratory_input)

        # Combine and store in history
        new_state = new_neural + new_cardiac + new_respiratory
        self.history.append((t + dt, new_neural, new_cardiac, new_respiratory))

        return new_state
```

### Adding Hardware Control Logic

**Custom Control Algorithm:**
```python
class AdaptiveControlProcessor:
    """Adaptive control with online parameter tuning."""

    def __init__(self):
        self.gain_history = []
        self.error_history = []

    def compute_adaptive_control(self, error: float,
                                 error_rate: float) -> float:
        """
        Compute control with adaptive gain.

        Args:
            error: Current tracking error
            error_rate: Rate of change of error

        Returns:
            Control signal
        """
        # Adapt gain based on error magnitude
        if abs(error) > 1.0:
            gain = 2.0  # Strong correction
        elif abs(error) < 0.1:
            gain = 0.5  # Gentle correction
        else:
            gain = 1.0  # Normal

        # Proportional-derivative control
        control = -gain * (error + 0.5 * error_rate)

        # Log for analysis
        self.gain_history.append(gain)
        self.error_history.append(error)

        return control
```

### Creating Demo Scripts

**Pattern for examples:**
```python
#!/usr/bin/env python3
"""
Demonstration of [feature name].

This script shows how to [describe functionality].
"""

from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters

def main():
    """Run demonstration."""
    print("=" * 60)
    print("DEMONSTRATION: [Feature Name]")
    print("=" * 60)

    # Setup
    print("\n1. Setting up model...")
    model = HeartBrainCouplingModel(
        neural_model=FitzHughNagumo(),
        cardiac_model=VanDerPolOscillator(),
        coupling=CouplingParameters()
    )

    # Run simulation
    print("2. Running simulation...")
    trajectory = model.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, 10.0),
        dt=0.01
    )

    # Extract results
    print("3. Extracting results...")
    times, neural, cardiac = model.extract_series(trajectory)

    # Analysis
    print("4. Analyzing results...")
    print(f"   Simulation time: {times[-1]:.2f} seconds")
    print(f"   Total timesteps: {len(times)}")
    print(f"   Neural amplitude: {max(v for v, w in neural):.3f}")
    print(f"   Cardiac amplitude: {max(x for x, y in cardiac):.3f}")

    # Optional visualization
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12, 6))
        plt.subplot(2, 1, 1)
        plt.plot(times, [v for v, w in neural])
        plt.title("Neural Activity")
        plt.subplot(2, 1, 2)
        plt.plot(times, [x for x, y in cardiac])
        plt.title("Cardiac Activity")
        plt.tight_layout()
        plt.savefig('demo_results.png')
        print("\n5. Saved plot to demo_results.png")
    except ImportError:
        print("\n5. Matplotlib not available, skipping visualization")

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

---

## AI Assistant Best Practices

### When Starting Work

1. **Read relevant documentation first:**
   - `docs/INDEX.md` for navigation
   - `docs/QUICK_REFERENCE.md` for quick context
   - Specific component docs as needed

2. **Understand the task scope:**
   - Is it a bug fix, feature, or refactor?
   - Which subsystems are affected?
   - Are there existing tests to guide you?

3. **Check existing patterns:**
   - Look for similar implementations
   - Follow established conventions
   - Maintain consistency with codebase style

### When Writing Code

1. **Follow the module interface:**
   - `derivatives(t, state, input)` for mathematical models
   - `step(t, state, dt, input)` for time stepping
   - Return types match input types

2. **Add type hints:**
   - All function signatures
   - All class attributes
   - Use `Tuple`, `List`, `Dict` from typing

3. **Write comprehensive docstrings:**
   - One-line summary
   - Args section with types
   - Returns section
   - Example usage if complex

4. **Consider test coverage:**
   - Write tests alongside code
   - Test edge cases and boundary conditions
   - Use parameterized tests for multiple scenarios

### When Testing

1. **Run tests before committing:**
   ```bash
   pytest tests/ -v
   python validate_integration.py
   python validate_organchip.py
   ```

2. **Check for integration impacts:**
   - Did you change a core model?
   - Run integration tests
   - Verify examples still work

3. **Test with realistic parameters:**
   - Use physiologically valid ranges
   - Test extremes (min/max)
   - Test zero and negative inputs

### When Documenting

1. **Update existing docs:**
   - Don't create new markdown files unless necessary
   - Update `docs/QUICK_REFERENCE.md` with new parameters
   - Add to `docs/ARCHITECTURE_OVERVIEW.md` if significant

2. **Document design decisions:**
   - Why this approach?
   - What alternatives were considered?
   - What are the limitations?

3. **Provide examples:**
   - Show basic usage
   - Show advanced usage
   - Show common pitfalls

### When Committing

1. **Review your changes:**
   ```bash
   git diff
   git status
   ```

2. **Write descriptive commits:**
   - What changed (summary)
   - Why it changed (context)
   - How it affects the system

3. **Keep commits focused:**
   - One logical change per commit
   - Don't mix features and refactoring
   - Don't commit debugging code

---

## Quick Reference Card

### Essential Commands

```bash
# Testing
pytest tests/ -v                           # All tests
pytest tests/test_models.py -v            # Unit tests
python validate_integration.py            # Integration validation

# Building
make build                                # Build D executable
./primal_overlay                          # Run D executable

# Git
git status                                # Check status
git diff                                  # Review changes
git add <files>                           # Stage changes
git commit -m "message"                   # Commit
git push -u origin <branch>               # Push

# Examples
python examples/microprocessor_motorhand_demo.py
python examples/organchip/demo_complete_system.py
```

### Key File Paths

```
src/coupling/hbcm.py              - Main orchestrator
src/cardiac/van_der_pol.py        - Cardiac model
src/neural/fitzhugh_nagumo.py     - Neural model
src/organchip/suite.py            - Organ chip platform
config/default.yaml               - Simulation parameters
docs/QUICK_REFERENCE.md           - Quick lookup guide
tests/test_models.py              - Core tests
```

### Parameter Defaults

```python
# Neural (FitzHugh-Nagumo)
a=0.7, b=0.8, c=3.0, stimulus=0.5

# Cardiac (Van der Pol)
mu=1.5, omega=1.0, damping=0.1

# Coupling
neural_to_cardiac_gain=0.5
cardiac_to_neural_gain=0.3
neural_to_cardiac_delay=0.12  # seconds
cardiac_to_neural_delay=0.15  # seconds

# Simulation
duration=120.0  # seconds
timestep=0.001  # seconds
```

---

## Conclusion

This guide provides comprehensive information for AI assistants working with the Multi-Heart-Model repository. Key takeaways:

1. **Minimal, Clean Design**: Few dependencies, transparent code, comprehensive tests
2. **Modular Architecture**: Standard interfaces, orchestrator pattern, layered control
3. **Production Ready**: Hardware deployment, extensive documentation, CI/CD
4. **Multiple Domains**: Neural, cardiac, hardware control, drug screening
5. **Extensible**: Clear patterns for adding models, organs, control algorithms

When in doubt:
- Check `docs/QUICK_REFERENCE.md` for quick answers
- Read `docs/ARCHITECTURE_OVERVIEW.md` for deep understanding
- Follow existing patterns in `src/`
- Ask for clarification when requirements are unclear

**Remember:** This codebase values clarity over cleverness, transparency over magic, and comprehensive testing over rapid iteration. Follow these principles when contributing.

---

**Document Maintained By:** AI Assistant (Claude)
**For Updates:** Modify this file when adding significant features or changing conventions
**Questions:** Refer to `docs/INDEX.md` for documentation navigation
