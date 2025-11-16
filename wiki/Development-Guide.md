# Development Guide

Guide for contributing to the Multi-Heart-Model project.

## 🎯 Development Philosophy

### Core Principles

1. **Minimal Dependencies**: Keep external dependencies to a minimum
2. **Transparency**: Code should be readable and understandable
3. **Modularity**: Components should be self-contained and composable
4. **Type Safety**: Use type hints throughout
5. **Test Coverage**: Aim for 100% coverage of production code
6. **Documentation First**: Write docs alongside code

## 🛠️ Setting Up Development Environment

### Prerequisites

- Python 3.8+
- Git
- Optional: D compiler (LDC2) for D implementation
- Optional: pytest for testing

### Installation

```bash
# Clone repository
git clone https://github.com/STLNFTART/Multi-Heart-Model.git
cd Multi-Heart-Model

# Install dependencies
pip install numpy pytest pytest-cov

# Optional: matplotlib for visualization
pip install matplotlib

# Optional: YAML support
pip install pyyaml

# Verify installation
pytest tests/ -v
```

### Development Tools

```bash
# Type checking (optional)
pip install mypy
mypy src/

# Code formatting (optional)
pip install black
black src/ tests/

# Linting (optional)
pip install flake8
flake8 src/ tests/
```

## 📝 Code Style Conventions

### Python Style Guide

Follow PEP 8 with these specifics:

#### Naming Conventions

```python
# Classes: PascalCase
class HeartBrainCouplingModel:
    pass

class VanDerPolOscillator:
    pass

# Functions/Methods: snake_case
def compute_derivatives(t, state):
    pass

def simulate_drug_test(dose, duration):
    pass

# Constants: UPPER_CASE
MAX_TIMESTEP = 0.01
PLANCK_SCALE = 1e-35

# Private methods: _leading_underscore
def _delayed_state(self, t, delay):
    pass

# Module variables: snake_case
default_gain = 0.5
```

#### Type Hints

Always use type hints for public APIs:

```python
from typing import Tuple, List, Optional, Dict

def derivatives(
    self,
    t: float,
    state: Tuple[float, float],
    input_drive: float = 0.0
) -> Tuple[float, float]:
    """
    Compute state derivatives.

    Args:
        t: Current time in seconds
        state: Current state (v, w)
        input_drive: External input signal

    Returns:
        Derivatives (dv/dt, dw/dt)
    """
    v, w = state
    # ... implementation
    return (dv_dt, dw_dt)
```

#### Docstrings

Use Google-style docstrings:

```python
def simulate(
    self,
    initial_state: Tuple[float, ...],
    t_span: Tuple[float, float],
    dt: float
) -> List[Tuple[float, Tuple[float, ...]]]:
    """
    Run complete simulation from t_start to t_end.

    Integrates the coupled system over the specified time interval
    using Euler integration with the given timestep.

    Args:
        initial_state: Initial state vector (v, w, x, y)
        t_span: Time interval (t_start, t_end) in seconds
        dt: Timestep size in seconds. Recommended: 0.001

    Returns:
        List of (time, state) tuples representing the trajectory

    Raises:
        ValueError: If dt is too large (> 0.01) or negative

    Example:
        >>> trajectory = model.simulate(
        ...     initial_state=(0.0, 0.0, 1.0, 0.0),
        ...     t_span=(0.0, 10.0),
        ...     dt=0.001
        ... )
    """
    pass
```

#### File Organization

```python
# 1. Module docstring
"""
FitzHugh-Nagumo neural oscillator model.

This module implements the two-dimensional FitzHugh-Nagumo model
for neural excitability and oscillations.
"""

# 2. Imports (grouped: stdlib, third-party, local)
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from src.utils import validate_parameters

# 3. Constants
DEFAULT_A = 0.7
DEFAULT_B = 0.8

# 4. Classes and functions
@dataclass
class FitzHughNagumoParameters:
    """Parameters for FitzHugh-Nagumo model."""
    a: float = DEFAULT_A
    # ...

class FitzHughNagumo:
    """FitzHugh-Nagumo neural oscillator."""
    # ...

# 5. Module exports
__all__ = [
    "FitzHughNagumo",
    "FitzHughNagumoParameters",
]
```

## 🧪 Testing Guidelines

### Test Structure

Tests mirror source structure:

```
src/
├── cardiac/
│   └── van_der_pol.py
└── neural/
    └── fitzhugh_nagumo.py

tests/
├── test_cardiac/
│   └── test_van_der_pol.py
└── test_neural/
    └── test_fitzhugh_nagumo.py
```

### Writing Unit Tests

```python
import pytest
from src.neural import FitzHughNagumo

class TestFitzHughNagumo:
    """Tests for FitzHugh-Nagumo model."""

    def test_initialization(self):
        """Test model initialization with default parameters."""
        model = FitzHughNagumo()
        assert model.a == 0.7
        assert model.b == 0.8
        assert model.c == 3.0

    def test_initialization_custom(self):
        """Test model initialization with custom parameters."""
        model = FitzHughNagumo(a=0.5, b=0.6, c=2.0)
        assert model.a == 0.5
        assert model.b == 0.6
        assert model.c == 2.0

    def test_derivatives_at_rest(self):
        """Test derivatives at resting state."""
        model = FitzHughNagumo()
        state = (0.0, 0.0)
        dv, dw = model.derivatives(t=0.0, state=state, input_drive=0.0)

        # At (0, 0), dv/dt ≈ 0 and dw/dt ≈ a/c
        assert dv == pytest.approx(0.0)
        assert dw == pytest.approx(0.7 / 3.0, rel=1e-6)

    @pytest.mark.parametrize(
        "state,input_drive,expected_dv",
        [
            ((0.0, 0.0), 0.0, 0.0),
            ((1.0, 0.0), 0.0, 1.0 - 1.0/3),
            ((0.5, 0.2), 0.1, pytest.approx(0.558333, rel=1e-5)),
        ],
    )
    def test_derivatives_values(self, state, input_drive, expected_dv):
        """Test derivative values for specific states."""
        model = FitzHughNagumo()
        dv, dw = model.derivatives(t=0.0, state=state, input_drive=input_drive)
        assert dv == expected_dv

    def test_step_integration(self):
        """Test single integration step."""
        model = FitzHughNagumo()
        state = (0.0, 0.0)
        dt = 0.001

        new_state = model.step(t=0.0, state=state, dt=dt, input_drive=0.0)

        # Check state has changed
        assert new_state != state
        # Check values are reasonable
        assert -5.0 < new_state[0] < 5.0
        assert -5.0 < new_state[1] < 5.0
```

### Parameterized Tests

Use `@pytest.mark.parametrize` for testing multiple scenarios:

```python
@pytest.mark.parametrize(
    "mu,omega,expected_period",
    [
        (1.0, 1.0, pytest.approx(2 * np.pi, rel=0.1)),
        (1.5, 2.0, pytest.approx(np.pi, rel=0.1)),
    ],
)
def test_oscillation_period(mu, omega, expected_period):
    """Test oscillation period matches omega."""
    model = VanDerPolOscillator(mu=mu, omega=omega)
    # ... run simulation and measure period
    assert measured_period == expected_period
```

### Fixtures

Use fixtures for common test setups:

```python
# conftest.py
import pytest
from src.coupling import HeartBrainCouplingModel

@pytest.fixture
def default_hbcm():
    """Provide default HBCM instance."""
    return HeartBrainCouplingModel()

@pytest.fixture
def custom_hbcm():
    """Provide custom HBCM instance."""
    neural = FitzHughNagumo(a=0.5)
    cardiac = VanDerPolOscillator(mu=2.0)
    coupling = CouplingParameters(neural_to_cardiac_gain=0.8)
    return HeartBrainCouplingModel(neural, cardiac, coupling)

# test_coupling.py
def test_simulation(default_hbcm):
    """Test simulation with default model."""
    trajectory = default_hbcm.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, 1.0),
        dt=0.001
    )
    assert len(trajectory) == 1001  # 1 second at 1ms steps
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_neural/test_fitzhugh_nagumo.py -v

# Run specific test
pytest tests/test_neural/test_fitzhugh_nagumo.py::test_initialization -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run only fast tests (skip slow integration tests)
pytest tests/ -v -m "not slow"
```

## 🔀 Git Workflow

### Branch Strategy

Development happens on feature branches:

```bash
# Create feature branch
git checkout -b claude/add-kidney-model

# Make changes and commit
git add src/organchip/kidney.py tests/organchip/test_kidney.py
git commit -m "Add kidney cell model for nephrotoxicity screening"

# Push to remote
git push -u origin claude/add-kidney-model
```

### Commit Message Format

```
<type>: <short summary>

<detailed description>

<optional footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples**:

```
feat: Add kidney cell model for nephrotoxicity

Implement KidneyCell class with:
- Glomerular filtration rate modeling
- Creatinine clearance tracking
- Drug-induced tubular damage
- Integration with OrganChipSuite

Closes #42
```

```
fix: Correct delay lookup in coupling model

The delay lookup was using linear search which could miss
the exact time point. Changed to use binary search with
interpolation for more accurate delayed state retrieval.

Performance improved from O(n) to O(log n) per lookup.
```

### Pull Request Process

1. **Create feature branch**
2. **Make changes with tests**
3. **Ensure tests pass**: `pytest tests/ -v`
4. **Update documentation** if needed
5. **Commit changes** with clear messages
6. **Push to remote**: `git push -u origin <branch-name>`
7. **Create pull request** on GitHub
8. **Address review feedback**
9. **Merge when approved**

## 📦 Adding New Components

### Adding a New Neural Model

1. **Create model file**: `src/neural/hodgkin_huxley.py`

```python
"""Hodgkin-Huxley neuron model."""

from dataclasses import dataclass
from typing import Tuple

@dataclass
class HodgkinHuxleyParameters:
    """HH model parameters."""
    C_m: float = 1.0
    g_Na: float = 120.0
    g_K: float = 36.0
    g_L: float = 0.3

class HodgkinHuxleyNeuron:
    """Hodgkin-Huxley neuron model."""

    def __init__(self, params: HodgkinHuxleyParameters = None):
        self.params = params or HodgkinHuxleyParameters()

    def derivatives(
        self,
        t: float,
        state: Tuple[float, float, float, float],
        input_current: float = 0.0
    ) -> Tuple[float, float, float, float]:
        """
        Compute HH derivatives.

        Args:
            t: Time in seconds
            state: (V, m, h, n) - voltage and gating variables
            input_current: External current (μA/cm²)

        Returns:
            (dV/dt, dm/dt, dh/dt, dn/dt)
        """
        # Implementation here
        pass

    def step(
        self,
        t: float,
        state: Tuple[float, float, float, float],
        dt: float,
        input_current: float = 0.0
    ) -> Tuple[float, float, float, float]:
        """Euler integration step."""
        derivs = self.derivatives(t, state, input_current)
        return tuple(s + dt * ds for s, ds in zip(state, derivs))

__all__ = ["HodgkinHuxleyNeuron", "HodgkinHuxleyParameters"]
```

2. **Update package init**: `src/neural/__init__.py`

```python
from .fitzhugh_nagumo import FitzHughNagumo
from .hodgkin_huxley import HodgkinHuxleyNeuron, HodgkinHuxleyParameters

__all__ = [
    "FitzHughNagumo",
    "HodgkinHuxleyNeuron",
    "HodgkinHuxleyParameters",
]
```

3. **Write tests**: `tests/test_neural/test_hodgkin_huxley.py`

4. **Add documentation** to relevant wiki pages

5. **Create example**: `examples/hodgkin_huxley_demo.py`

### Adding a New Organ Model

Follow the same pattern as existing organ models in `src/organchip/`.

1. **Create organ file**: `src/organchip/kidney.py`
2. **Implement standard interface**:
   - `__init__(params)`
   - `step(t, state, dt, drug_conc)`
   - `get_biomarkers(state)`
3. **Add to OrganChipSuite** in `src/organchip/orchestrator.py`
4. **Write integration tests**
5. **Update documentation**

## 📚 Documentation Standards

### Code Documentation

- All public classes and functions must have docstrings
- Use Google-style docstrings
- Include type hints
- Provide usage examples for complex APIs

### Wiki Documentation

When adding significant features:

1. Update relevant wiki pages
2. Add to [Examples](Examples) if applicable
3. Update [API Reference](API-Reference)
4. Consider adding to [Getting Started](Getting-Started)

### Inline Comments

```python
# Good: Explain why, not what
# Use adaptive timestep when system becomes stiff
if max(abs(dv), abs(dw)) > threshold:
    dt = dt / 2

# Bad: Explain what (obvious from code)
# Set dt to dt divided by 2
dt = dt / 2
```

## 🐛 Debugging Tips

### Common Issues

**Numerical Instability**:
```python
# Check for NaN/Inf
if not all(np.isfinite(state)):
    print(f"Unstable at t={t}: {state}")
    # Reduce timestep or check parameters
```

**Delay Lookups**:
```python
# Debug delay lookup
def _delayed_state(self, t, delay, system, default):
    target_time = t - delay
    print(f"Looking for t={target_time:.4f} in history of {len(self.history)} points")
    # ...
```

**Integration Issues**:
```python
# Log intermediate values
def step(self, t, state, dt):
    derivs = self.derivatives(t, state)
    new_state = tuple(s + dt * ds for s, ds in zip(state, derivs))

    # Sanity check
    if any(abs(s) > 100 for s in new_state):
        print(f"WARNING: Large state values at t={t}: {new_state}")

    return new_state
```

## 🔍 Code Review Checklist

Before submitting a pull request, ensure:

- [ ] Code follows style conventions
- [ ] All functions have type hints
- [ ] All public APIs have docstrings
- [ ] Tests are added and passing
- [ ] Test coverage is maintained (>95%)
- [ ] No hardcoded values (use constants or parameters)
- [ ] No print statements (use logging if needed)
- [ ] Documentation updated if needed
- [ ] Commit messages are clear and descriptive

## 📊 Performance Optimization

### Profiling

```python
import cProfile
import pstats

# Profile code
profiler = cProfile.Profile()
profiler.enable()

# Run simulation
trajectory = hbcm.simulate(
    initial_state=(0.0, 0.0, 1.0, 0.0),
    t_span=(0.0, 60.0),
    dt=0.001
)

profiler.disable()

# Print stats
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Optimization Tips

1. **Use NumPy for vectorization** when processing arrays
2. **Reduce history buffer size** if memory is an issue
3. **Use D implementation** for production (10-100x faster)
4. **Cache expensive computations**
5. **Profile before optimizing**

## 🚀 Release Process

1. Update version in `setup.py` (if applicable)
2. Update CHANGELOG.md
3. Create release branch: `git checkout -b release/v1.2.0`
4. Run full test suite
5. Build and test D implementation
6. Create git tag: `git tag -a v1.2.0 -m "Release v1.2.0"`
7. Push tag: `git push origin v1.2.0`
8. Create GitHub release

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/STLNFTART/Multi-Heart-Model/issues)
- **Discussions**: [GitHub Discussions](https://github.com/STLNFTART/Multi-Heart-Model/discussions)
- **Documentation**: See [Home](Home) for full documentation index

---

**Happy Coding!** 🎉
