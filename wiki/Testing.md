# Testing Guide

Comprehensive guide to testing in the Multi-Heart-Model project.

## 🎯 Testing Philosophy

- **High Coverage**: Aim for >95% code coverage
- **Fast Execution**: Unit tests should run in seconds
- **Comprehensive**: Test edge cases and boundary conditions
- **Maintainable**: Tests should be clear and well-documented
- **Automated**: All tests run in CI/CD pipeline

## 📊 Test Statistics

- **Total Test LOC**: 1,024
- **Test Files**: 15+
- **Test Methods**: 30+
- **Coverage Target**: 100% of production code
- **Execution Time**: < 30 seconds (full suite)

## 🧪 Test Types

### 1. Unit Tests

Test individual components in isolation.

**Location**: `tests/test_models.py`, `tests/test_*/`

**Example**:
```python
import pytest
from src.neural import FitzHughNagumo

def test_fitzhugh_nagumo_initialization():
    """Test FH-N model initializes correctly."""
    model = FitzHughNagumo(a=0.7, b=0.8, c=3.0)

    assert model.a == 0.7
    assert model.b == 0.8
    assert model.c == 3.0
    assert model.stimulus_amplitude == 0.5  # default

def test_derivatives_at_origin():
    """Test derivatives at (0, 0) state."""
    model = FitzHughNagumo()
    state = (0.0, 0.0)
    dv, dw = model.derivatives(t=0.0, state=state)

    assert dv == pytest.approx(0.0)
    assert dw == pytest.approx(0.7 / 3.0, rel=1e-6)
```

### 2. Integration Tests

Test multiple components working together.

**Location**: `tests/integration/`

**Example**:
```python
from src.coupling import HeartBrainCouplingModel
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo

def test_coupled_simulation():
    """Test full coupled heart-brain simulation."""
    hbcm = HeartBrainCouplingModel(
        neural_model=FitzHughNagumo(),
        cardiac_model=VanDerPolOscillator(),
        coupling=CouplingParameters()
    )

    trajectory = hbcm.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, 1.0),
        dt=0.001
    )

    # Check trajectory length
    assert len(trajectory) == 1001

    # Check states are finite
    for t, state in trajectory:
        assert all(np.isfinite(state))

    # Check oscillations occurred
    times, neural, cardiac = hbcm.extract_series(trajectory)
    v_vals = [v for v, w in neural]
    assert max(v_vals) > 0.5  # Neural activity occurred
```

### 3. Validation Tests

Test against known results and real-world expectations.

**Location**: `validate_integration.py`, `validate_organchip.py`

**Example**:
```python
def test_cardiac_frequency():
    """Test cardiac oscillation frequency matches omega."""
    model = VanDerPolOscillator(mu=1.0, omega=1.0)  # 1 Hz
    state = (1.0, 0.0)
    dt = 0.001
    t = 0.0

    # Run for 10 periods
    trajectory = []
    for _ in range(int(10 / dt)):
        trajectory.append((t, state))
        state = model.step(t, state, dt)
        t += dt

    # Measure period via zero crossings
    x_vals = [s[0] for _, s in trajectory]
    times = [t for t, _ in trajectory]

    zero_crossings = []
    for i in range(1, len(x_vals)):
        if x_vals[i-1] < 0 and x_vals[i] >= 0:
            zero_crossings.append(times[i])

    periods = [zero_crossings[i+1] - zero_crossings[i]
               for i in range(len(zero_crossings)-1)]
    avg_period = np.mean(periods)

    # Period should be ~2π for ω=1
    assert avg_period == pytest.approx(2 * np.pi, rel=0.1)
```

### 4. Performance Tests

Test execution speed and resource usage.

**Example**:
```python
import time
import pytest

@pytest.mark.slow
def test_simulation_performance():
    """Test simulation completes in reasonable time."""
    hbcm = HeartBrainCouplingModel()

    start = time.time()
    trajectory = hbcm.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, 60.0),  # 60 seconds
        dt=0.001
    )
    elapsed = time.time() - start

    # Should complete in < 5 seconds on modern hardware
    assert elapsed < 5.0
    print(f"Simulation time: {elapsed:.2f}s for 60s of data")
```

## 🔧 Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v

# Run specific test function
pytest tests/test_models.py::test_van_der_pol_derivatives -v

# Run tests matching pattern
pytest tests/ -v -k "neural"
```

### Coverage Analysis

```bash
# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Test Markers

```bash
# Run only fast tests (skip slow integration tests)
pytest tests/ -v -m "not slow"

# Run only integration tests
pytest tests/ -v -m "integration"

# Run only unit tests
pytest tests/ -v -m "unit"
```

**Defining markers in `pytest.ini`**:
```ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    hardware: marks tests requiring hardware
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/ -v -n 4
```

## 📝 Writing Good Tests

### Test Structure

Follow the **Arrange-Act-Assert** pattern:

```python
def test_example():
    # Arrange: Set up test conditions
    model = FitzHughNagumo(a=0.7)
    state = (0.0, 0.0)

    # Act: Execute the code being tested
    dv, dw = model.derivatives(t=0.0, state=state)

    # Assert: Verify expected outcomes
    assert dv == pytest.approx(0.0)
    assert dw == pytest.approx(0.7 / 3.0)
```

### Parameterized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize(
    "mu,omega,expected_stable",
    [
        (0.5, 1.0, True),   # Low mu: stable oscillations
        (3.0, 1.0, True),   # High mu: relaxation oscillations
        (1.5, 0.0, False),  # Zero omega: no oscillation
    ],
)
def test_van_der_pol_stability(mu, omega, expected_stable):
    """Test stability for various parameters."""
    model = VanDerPolOscillator(mu=mu, omega=omega)

    # Run simulation
    state = (1.0, 0.0)
    for _ in range(10000):
        state = model.step(0.0, state, dt=0.001)

    # Check if state remains bounded
    is_stable = all(abs(s) < 10.0 for s in state)
    assert is_stable == expected_stable
```

### Fixtures

Reuse common test setups:

```python
# conftest.py
import pytest

@pytest.fixture
def default_hbcm():
    """Provide default coupled model."""
    from src.coupling import HeartBrainCouplingModel
    return HeartBrainCouplingModel()

@pytest.fixture
def sample_trajectory(default_hbcm):
    """Provide sample simulation trajectory."""
    return default_hbcm.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, 10.0),
        dt=0.001
    )

# test_coupling.py
def test_extract_series(sample_trajectory):
    """Test time series extraction."""
    from src.coupling import HeartBrainCouplingModel

    hbcm = HeartBrainCouplingModel()
    times, neural, cardiac = hbcm.extract_series(sample_trajectory)

    assert len(times) == len(neural) == len(cardiac)
    assert all(len(n) == 2 for n in neural)  # (v, w)
    assert all(len(c) == 2 for c in cardiac)  # (x, y)
```

### Testing Floating Point

Use `pytest.approx` for float comparisons:

```python
# Bad: Exact equality rarely works
assert result == 0.3333333

# Good: Approximate equality
assert result == pytest.approx(1/3, rel=1e-6)

# Absolute tolerance
assert result == pytest.approx(0.0, abs=1e-9)

# Relative tolerance (default 1e-6)
assert result == pytest.approx(expected, rel=1e-5)
```

### Testing Exceptions

```python
def test_invalid_timestep():
    """Test that negative dt raises ValueError."""
    hbcm = HeartBrainCouplingModel()

    with pytest.raises(ValueError, match="timestep must be positive"):
        hbcm.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 10.0),
            dt=-0.001  # Invalid!
        )
```

## 🧩 Test Organization

### Directory Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_models.py           # Core model tests
├── test_cardiac/
│   └── test_van_der_pol.py
├── test_neural/
│   └── test_fitzhugh_nagumo.py
├── test_coupling/
│   └── test_hbcm.py
├── integration/
│   ├── test_full_simulation.py
│   └── test_delay_coupling.py
├── organchip/
│   ├── test_cardiac_cell.py
│   ├── test_hepatocyte.py
│   └── test_orchestrator.py
└── hardware/
    ├── test_primal_logic.py
    └── test_motorhand_bridge.py
```

### Naming Conventions

**Test Files**: `test_<module>.py`
**Test Functions**: `test_<functionality>()`
**Test Classes**: `Test<ClassName>`

```python
# test_van_der_pol.py

class TestVanDerPolOscillator:
    """Tests for Van der Pol oscillator."""

    def test_initialization(self):
        """Test default initialization."""
        pass

    def test_initialization_custom_params(self):
        """Test initialization with custom parameters."""
        pass

    def test_derivatives_at_origin(self):
        """Test derivatives at origin."""
        pass
```

## 🔍 Debugging Failed Tests

### Verbose Output

```bash
# Show print statements and full tracebacks
pytest tests/ -v -s

# Show local variables in traceback
pytest tests/ -v -l

# Drop into debugger on failure
pytest tests/ -v --pdb
```

### Selective Execution

```bash
# Run only failed tests from last run
pytest tests/ --lf

# Run failed tests first, then others
pytest tests/ --ff
```

### Logging

```python
import logging

def test_with_logging():
    """Test with debug logging."""
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    logger.debug("Starting test")
    # ... test code ...
    logger.debug(f"Result: {result}")
```

## 📊 Test Coverage

### Coverage Goals

- **Overall**: >95%
- **Core Models**: 100%
- **Utilities**: >90%
- **Examples**: Not required (but encouraged)

### Checking Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML report
pytest tests/ --cov=src --cov-report=html

# Show uncovered lines
pytest tests/ --cov=src --cov-report=term-missing
```

### Coverage Output

```
Name                               Stmts   Miss  Cover   Missing
----------------------------------------------------------------
src/__init__.py                        0      0   100%
src/cardiac/__init__.py                2      0   100%
src/cardiac/van_der_pol.py            30      0   100%
src/neural/__init__.py                 2      0   100%
src/neural/fitzhugh_nagumo.py         50      2    96%   87, 92
src/coupling/__init__.py               3      0   100%
src/coupling/hbcm.py                 125      5    96%   45, 67, 89, 102, 115
----------------------------------------------------------------
TOTAL                                212      7    97%
```

## 🚀 Continuous Integration

### GitHub Actions

Tests run automatically on every push and pull request.

**Workflow**: `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

Run tests before committing:

**`.git/hooks/pre-commit`**:
```bash
#!/bin/bash

# Run tests
pytest tests/ -q

if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi
```

## 🧪 Validation Scripts

### Integration Validation

```bash
python validate_integration.py
```

**Output**:
```
========================================
VALIDATION: Hardware Integration
========================================

1. Testing Primal Logic Processor...
   ✓ Proportional control
   ✓ Integral control
   ✓ Output saturation
   ✓ Reset functionality

2. Testing MotorHandPro Bridge...
   ✓ Connection
   ✓ Control commands
   ✓ Sensor reading

3. Testing Emergency Braking...
   ✓ Braking sequence
   ✓ Safety shutdown

========================================
ALL VALIDATIONS PASSED
========================================
```

### Organ Chip Validation

```bash
python validate_organchip.py
```

**Output**:
```
========================================
VALIDATION: Organ-On-Chip Platform
========================================

1. Testing Cardiac Cell...
   ✓ Action potential generation
   ✓ hERG channel dynamics
   ✓ Troponin release

2. Testing Hepatocyte...
   ✓ CYP450 metabolism
   ✓ ALT/AST release
   ✓ Drug clearance

3. Testing Drug Test...
   ✓ Doxorubicin cardiotoxicity
   ✓ Acetaminophen hepatotoxicity
   ✓ Biomarker correlation

========================================
ALL VALIDATIONS PASSED
========================================
```

## 📚 Best Practices

### DO

✅ Write tests before or alongside code (TDD)
✅ Test edge cases and boundary conditions
✅ Use descriptive test names
✅ Keep tests independent (no shared state)
✅ Use fixtures for common setups
✅ Mock external dependencies (hardware, network)
✅ Test both success and failure cases

### DON'T

❌ Write tests that depend on execution order
❌ Use hard-coded paths or file locations
❌ Test implementation details (test behavior)
❌ Skip error handling tests
❌ Commit code without tests
❌ Ignore failing tests

## 🔗 See Also

- **[Development Guide](Development-Guide)** - Contributing guidelines
- **[API Reference](API-Reference)** - API documentation
- **[Examples](Examples)** - Usage examples

---

**Test early, test often!** 🧪
