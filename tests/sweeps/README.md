# Parameter Sweep Test Suite

Comprehensive parameter and variable vector sweeps for the Multi-Heart-Model codebase.

## Overview

This test suite executes exhaustive parameter sweeps across all model subsystems to verify:

- **Numerical stability** across parameter ranges
- **Physical correctness** of model responses
- **Robustness** to extreme parameter values
- **Parameter sensitivity** for optimization
- **Regression testing** for code changes

## Test Structure

```
tests/sweeps/
├── __init__.py                        # Package init
├── README.md                          # This file
├── SWEEP_RESULTS_REPORT.md           # Detailed results and analysis
│
├── test_parameter_sweeps.py          # Core models (Neural, Cardiac, Coupling)
├── test_control_system_sweeps.py     # Microprocessor control systems
├── test_organchip_sweeps.py          # Organ-on-chip models
│
├── sweep_results.json                # Core model results (auto-generated)
├── control_sweep_results.json        # Control system results (auto-generated)
└── organchip_sweep_results.json      # Organ chip results (auto-generated)
```

## Quick Start

### Run All Core Model Sweeps

```bash
# From repository root
pytest tests/sweeps/test_parameter_sweeps.py -v -s

# Expected output: 30 passed in ~0.2s
```

### Run Control System Sweeps (requires NumPy)

```bash
pytest tests/sweeps/test_control_system_sweeps.py -v -s

# Skipped if NumPy not available
# With dependencies: 20 passed
```

### Run Organ Chip Sweeps (requires organ chip modules)

```bash
pytest tests/sweeps/test_organchip_sweeps.py -v -s

# Skipped if modules not available
# With dependencies: 21 passed
```

### Run All Sweeps

```bash
pytest tests/sweeps/ -v -s

# Total: 71 tests
```

## Test Categories

### 1. Core Model Sweeps (`test_parameter_sweeps.py`)

#### FitzHugh-Nagumo Neural Oscillator (9 tests)
- Parameter sweeps: `a`, `b`, `c`, `stimulus_amplitude`, `input_drive`
- State variable sweeps: `v`, `w`, combined (v,w) grid
- Multi-parameter: 3D grid of (a, b, c)

#### Van der Pol Cardiac Oscillator (8 tests)
- Parameter sweeps: `mu`, `omega`, `damping`, `input_force`
- State variable sweeps: `x`, `y`, combined (x,y) grid
- Multi-parameter: 3D grid of (mu, omega, damping)

#### Heart-Brain Coupling Model (9 tests)
- Coupling gains: `neural_to_cardiac_gain`, `cardiac_to_neural_gain`
- Communication delays: `neural_delay`, `cardiac_delay`
- Bias parameters: `neural_bias`, `cardiac_bias`
- Initial conditions: 81 combinations of (v, w, x, y)
- Simulation parameters: `dt` (timestep), `duration`
- Coupling symmetry: 7 configurations (symmetric, asymmetric, unidirectional)

#### Numerical Stability (3 tests)
- FitzHugh-Nagumo stability limits (8 timesteps tested)
- Van der Pol stability limits (6 timesteps tested)
- Extreme parameter combinations (4 configurations)

#### Results Collection (1 test)
- Automated export to `sweep_results.json`

**Total: 30 tests, 320+ parameter combinations**

---

### 2. Control System Sweeps (`test_control_system_sweeps.py`)

#### Primal Logic Processor (9 tests)
- `K_gain`: Proportional gain (8 values)
- `lambda_decay`: Memory decay rate (7 values)
- `dt`: Timestep (6 values)
- Error magnitudes: 0.1 to 500.0 (8 values)
- Target values: Setpoint tracking (8 values)
- Emergency braking: Initial velocities (6 scenarios)
- IPU parallel processing: Round-robin scheduling (6 tests)
- Control bounds: Saturation verification (4 configs)
- Comfort index: Monotonicity check (7 values)

#### Exponential Memory Weighting (3 tests)
- Lambda decay effects on weight
- Time delta sweep
- Weighted integral error scaling

#### QUANT Interface (2 tests)
- Control-to-throttle conversion (7 values)
- Extreme value handling (5 edge cases)

#### MotorHand Bridge (3 tests)
- Control signal integration (7 signals)
- Closed-loop initial states (5 values)
- Simulation durations (5 values)

#### Control Performance (2 tests)
- Multi-parameter K-lambda grid (16 combinations)
- Repeated braking scenarios (10 scenarios)

#### Results Export (1 test)
- Automated export to `control_sweep_results.json`

**Total: 20 tests, 190+ parameter combinations**

---

### 3. Organ Chip Sweeps (`test_organchip_sweeps.py`)

#### PBPK Circulation (4 tests)
- Cardiac output: 150 - 500 L/h (5 values)
- Hepatic clearance: 1 - 100 L/h (6 values)
- Partition coefficients (Kp): 0.1 - 10.0 (6 values)
- Drug doses: 1 - 5000 mg (7 values)

#### Cardiac Cell Electrophysiology (3 tests)
- hERG IC50: 0.01 - 50 μM (7 values)
- Drug concentrations: 0 - 100 μM (9 values)
- Pacing frequencies: 0.5 - 3.0 Hz (6 values)

#### Hepatocyte Metabolism (4 tests)
- Phase I metabolism rate: 0.01 - 2.0 1/h (7 values)
- GSH baseline: 2 - 20 mM (6 values)
- Reactive metabolite fraction: 0.0 - 0.7 (7 values)
- Plasma drug concentration: 0 - 500 μM (7 values)

#### Ligand-Receptor Binding (3 tests)
- Association rate (kon): 0.001 - 5.0 1/(nM·s) (6 values)
- Affinity (Kd): 0.01 - 100 nM (5 values)
- Ligand concentration: 0.01 - 1000 nM (6 values)

#### Organ Chip Suite Integration (4 tests)
- Drug doses: 10 - 5000 mg (6 values)
- Study durations: 6 - 96 hours (6 values)
- Simulation timesteps: 0.1 - 5.0 hours (5 values)
- Multi-dose comparison (3 doses)

#### Drug-Specific Screens (2 tests)
- Acetaminophen hepatotoxicity (6 doses)
- Doxorubicin cardiotoxicity (5 doses)

#### Results Export (1 test)
- Automated export to `organchip_sweep_results.json`

**Total: 21 tests, 240+ parameter combinations**

---

## Results Format

All sweep results are exported as structured JSON files for downstream analysis.

### Example: Core Model Results

```json
{
  "fitzhugh_nagumo": {
    "parameter_a_sweep": [
      {"a": 0.3, "dv": 0.458, "dw": 0.267},
      {"a": 0.5, "dv": 0.458, "dw": 0.333},
      {"a": 0.7, "dv": 0.458, "dw": 0.400}
    ]
  },
  "van_der_pol": {
    "parameter_mu_sweep": [...]
  },
  "coupling": {
    "symmetric_gain_sweep": [...]
  }
}
```

### Loading Results in Python

```python
import json
import matplotlib.pyplot as plt

# Load results
with open('tests/sweeps/sweep_results.json') as f:
    results = json.load(f)

# Plot parameter sweep
sweep = results['fitzhugh_nagumo']['parameter_a_sweep']
a_values = [entry['a'] for entry in sweep]
dw_values = [entry['dw'] for entry in sweep]

plt.plot(a_values, dw_values, 'o-')
plt.xlabel('Parameter a')
plt.ylabel('Recovery rate dw')
plt.title('FitzHugh-Nagumo: Parameter a Sweep')
plt.show()
```

## Interpreting Results

### Numerical Stability

Tests verify that models remain numerically stable (no NaN, Inf, or exponential blow-up) across parameter ranges.

**Stability limits identified:**
- FitzHugh-Nagumo Euler: dt ≤ 0.5 s
- Van der Pol Euler: dt ≤ 0.2 s
- Coupled system (conservative): dt ≤ 0.1 s

**Recommendation:** Use dt = 0.01 s for production simulations.

### Parameter Sensitivity

Tests reveal which parameters have strong vs. weak effects on model dynamics.

**High sensitivity:**
- Coupling gains (linear effect on cross-talk)
- Control gain K (determines saturation)
- Timescale parameter c (affects oscillation frequency)

**Low sensitivity:**
- Small delays (< 0.05 s)
- Bias terms (shift equilibrium only)

### Physical Correctness

Tests verify expected physical behavior:

✅ Higher coupling gain → stronger synchronization
✅ Larger delays → phase lag
✅ Increased drug concentration → increased toxicity
✅ Higher clearance → faster elimination

## Adding New Sweeps

### Template for New Parameter Sweep

```python
def test_new_parameter_sweep(self):
    """Sweep description."""
    param_values = [v1, v2, v3, ...]  # Define range
    results = []

    for param in param_values:
        # Create model with parameter
        model = Model(parameter=param)

        # Run simulation or compute derivatives
        output = model.compute(...)

        # Stability check
        assert output is valid, f"Unstable at {param}"

        # Store result
        results.append(output)

    # Verify expected behavior
    assert len(set(results)) > 1, "Parameter has no effect"

    print(f"✓ Parameter sweep: {len(param_values)} values tested")
```

### Template for Multi-Parameter Grid

```python
import itertools

def test_multi_parameter_grid(self):
    """2D or 3D parameter grid."""
    param1_values = [...]
    param2_values = [...]

    count = 0
    for p1, p2 in itertools.product(param1_values, param2_values):
        model = Model(param1=p1, param2=p2)
        output = model.compute(...)

        assert output is valid
        count += 1

    print(f"✓ Grid sweep: {count} combinations tested")
```

## Performance

### Execution Times (on standard hardware)

| Test Suite | Tests | Time | Per Test |
|------------|-------|------|----------|
| Core models | 30 | ~0.15s | ~5ms |
| Control systems | 20 | ~2.0s | ~100ms |
| Organ chips | 21 | ~15s | ~700ms |

### Scalability

The sweep framework is designed for:
- **Monte Carlo simulations** (10,000+ runs)
- **Optimization workflows** (gradient-free methods)
- **Uncertainty quantification** (parameter distributions)
- **CI/CD regression testing** (fast feedback)

## Dependencies

### Core Model Sweeps
- ✅ No external dependencies
- Uses: `src.neural`, `src.cardiac`, `src.coupling`

### Control System Sweeps
- Requires: `numpy`
- Uses: `src.microprocessor`, `src.integration`

### Organ Chip Sweeps
- Requires: `numpy` (implicitly)
- Uses: `organchip.*` modules

### Install All Dependencies

```bash
# From repository root
pip install -r requirements.txt
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Parameter Sweep Tests

on: [push, pull_request]

jobs:
  sweep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/sweeps/ -v --tb=short
      - uses: actions/upload-artifact@v3
        with:
          name: sweep-results
          path: tests/sweeps/*_results.json
```

## Troubleshooting

### Tests Skipped (NumPy Not Available)

```
SKIPPED [20] ... NumPy or microprocessor modules not available
```

**Solution:**
```bash
pip install numpy
```

### Tests Skipped (Organ Chip Modules Not Available)

```
SKIPPED [21] ... Organ chip modules not available
```

**Solution:** Ensure `src/organchip/` is properly installed:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/sweeps/test_organchip_sweeps.py -v
```

### Assertion Failures

If a parameter sweep fails:

1. **Check parameter range:** Is it physiologically valid?
2. **Check timestep:** May be too large (try dt=0.001)
3. **Check initial conditions:** May be in unstable region
4. **Review test logic:** May be expecting wrong behavior

### Performance Issues

If tests are slow:

1. **Reduce sweep resolution:** Fewer parameter values
2. **Reduce simulation duration:** Shorter time windows
3. **Use coarser timesteps:** Larger dt (within stability limits)
4. **Parallelize:** Use `pytest-xdist`

```bash
pip install pytest-xdist
pytest tests/sweeps/ -n auto  # Parallel execution
```

## Citation

If you use this parameter sweep suite in research, please cite:

```
Multi-Heart-Model Parameter Sweep Suite
Repository: STLNFTART/Multi-Heart-Model
Tests: tests/sweeps/
```

## Contributing

To add new parameter sweeps:

1. **Choose subsystem:** Core models, control, or organ chips
2. **Identify parameters:** Physiologically relevant ranges
3. **Write test:** Follow templates above
4. **Document:** Add to this README and SWEEP_RESULTS_REPORT.md
5. **Verify:** Run locally before committing
6. **Submit:** Pull request with test + documentation

## License

MIT License (same as parent repository)

## Contact

For questions or issues with parameter sweeps, open an issue on GitHub:
https://github.com/STLNFTART/Multi-Heart-Model/issues

---

**Last Updated:** 2025-11-14
**Test Suite Version:** 1.0.0
**Total Tests:** 71
**Total Parameter Combinations:** 750+
