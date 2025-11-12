# Multi-Heart-Model: Quick Reference Guide

## Key Files by Purpose

### Core Models
| File | Purpose | Key Classes | LOC |
|------|---------|-------------|-----|
| `src/cardiac/van_der_pol.py` | Cardiac oscillator | `VanDerPolOscillator` | 30 |
| `src/neural/fhn.py` | Neural oscillator | `FitzHughNagumo` | 50 |
| `src/coupling/hbcm.py` | Orchestration | `HeartBrainCouplingModel`, `CouplingParameters` | 125 |

### Control & Integration
| File | Purpose | Key Classes | LOC |
|------|---------|-------------|-----|
| `src/microprocessor/primal_processor.py` | Integral control | `PrimalLogicProcessor`, `ProcessorConfig`, `IntegralProcessingUnit` | 283 |
| `src/microprocessor/control_system.py` | Control utilities | `ExponentialMemoryWeighting`, `IntegralControlSystem` | 214 |
| `src/integration/motorhand_bridge.py` | Motor interface | `MotorHandBridge`, `QuantInterface`, `QuantParameters` | 399 |

### Testing
| File | Purpose | Test Count | LOC |
|------|---------|-----------|-----|
| `tests/test_models.py` | Unit tests | 4 | 49 |
| `tests/integration/test_microprocessor_motorhand.py` | Integration tests | 26+ | 390+ |

### Configuration & Documentation
| File | Purpose |
|------|---------|
| `config/default.yaml` | Simulation parameters |
| `examples/microprocessor_motorhand_demo.py` | Complete demo script |
| `docs/architecture.md` | Architecture decisions |
| `docs/hbcm_overview.md` | Model overview |

---

## Quick Start Code Examples

### Basic Heart-Brain Coupling
```python
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters

# Create coupling model
hbcm = HeartBrainCouplingModel(
    neural_model=FitzHughNagumo(stimulus_amplitude=0.2),
    cardiac_model=VanDerPolOscillator(mu=1.2, omega=1.0),
    coupling=CouplingParameters(
        neural_to_cardiac_gain=0.5,
        cardiac_to_neural_gain=0.3
    )
)

# Simulate for 10 seconds
trajectory = hbcm.simulate(
    initial_state=(0.0, 0.0, 1.0, 0.0),  # (v, w, x, y)
    t_span=(0.0, 10.0),
    dt=0.01
)

# Extract results
times, neural, cardiac = hbcm.extract_series(trajectory)
```

### Primal Logic Control
```python
from src.microprocessor import PrimalLogicProcessor, ProcessorConfig

# Create processor
processor = PrimalLogicProcessor(ProcessorConfig(
    K_gain=0.5,
    lambda_decay=2.0,
    num_integral_units=8
))

# Emergency braking simulation
states = processor.simulate_emergency_braking(
    initial_velocity=30.0,  # m/s
    target_velocity=0.0,
    duration=10.0
)

# Export results
processor.export_state_csv('output.csv')
```

### Motor Integration
```python
from src.microprocessor import PrimalLogicProcessor
from src.integration import MotorHandBridge

# Create systems
processor = PrimalLogicProcessor()
bridge = MotorHandBridge()

# Closed-loop simulation
states = bridge.simulate_closed_loop(
    primal_processor=processor,
    initial_state=30.0,
    target_state=0.0,
    duration=10.0
)

# Export
bridge.export_integration_csv(states, 'integration_output.csv')
```

---

## Module Relationships & Data Flow

```
User Application Code
         │
         ▼
HeartBrainCouplingModel (orchestrator)
    │        │
    ▼        ▼
 FitzHugh  VanDerPol
  Nagumo    Oscillator
    │        │
    └───┬────┘
        ▼
   [Coupling terms]
        ▼
PrimalLogicProcessor (optional control)
        ▼
MotorHandBridge (optional motor control)
        ▼
    CSV Export
```

---

## State Representations

### Neural Model State
- `v`: Activator (voltage-like variable)
- `w`: Recovery variable (slower dynamics)
- **Total**: 2D state

### Cardiac Model State
- `x`: Position variable
- `y`: Velocity variable
- **Total**: 2D state

### Combined HBCM State
- **Vector**: `(v, w, x, y)` - 4D
- **Type**: `Tuple[float, float, float, float]`

### Primal Logic State
- `error`: Current - Target
- `integral`: Accumulated weighted error
- `control_output`: Unbounded control
- `bounded_control`: Control clipped to [-10, +10]
- `comfort_index`: Jerk-based comfort metric (0-100)

---

## Parameter Ranges & Defaults

### Neural Model (FitzHugh-Nagumo)
| Parameter | Default | Range | Meaning |
|-----------|---------|-------|---------|
| `a` | 0.7 | [0, 2] | Excitability |
| `b` | 0.8 | [0, 2] | Recovery rate |
| `c` | 3.0 | [1, 10] | Time scaling |
| `stimulus_amplitude` | 0.0 | [0, 1] | Baseline input |

### Cardiac Model (Van der Pol)
| Parameter | Default | Range | Meaning |
|-----------|---------|-------|---------|
| `mu` | 1.5 | [0.5, 3] | Relaxation strength |
| `omega` | 1.0 | [0.5, 3] | Natural frequency (rad/s) |
| `damping` | 0.0 | [0, 0.5] | Damping coefficient |

### Coupling Parameters
| Parameter | Default | Range | Meaning |
|-----------|---------|-------|---------|
| `neural_to_cardiac_gain` | 0.4 | [0, 1] | Neural → Cardiac strength |
| `cardiac_to_neural_gain` | 0.2 | [0, 1] | Cardiac → Neural strength |
| `neural_delay` | 0.0 | [0, 1] | Delay neural feedback (s) |
| `cardiac_delay` | 0.0 | [0, 1] | Delay cardiac feedback (s) |
| `neural_bias` | 0.0 | [-1, 1] | Constant neural input |
| `cardiac_bias` | 0.0 | [-1, 1] | Constant cardiac input |

### Primal Logic Parameters
| Parameter | Default | Range | Meaning |
|-----------|---------|-------|---------|
| `K_gain` | 0.5 | [0.1, 2] | Control gain |
| `lambda_decay` | 2.0 | [0.5, 5] | Memory decay rate |
| `dt` | 0.01 | [0.001, 0.1] | Integration timestep (s) |
| `max_control_output` | 10.0 | [1, 100] | Upper control bound |
| `min_control_output` | -10.0 | [-100, -1] | Lower control bound |

---

## Common Patterns

### Pattern 1: Extract Time Series
```python
times, neural, cardiac = hbcm.extract_series(trajectory)
# Returns lists: times (float), neural (float), cardiac (float)
```

### Pattern 2: Access State Components
```python
for time, state in trajectory:
    v, w, x, y = state  # Unpack 4D state
    # v, w = neural state
    # x, y = cardiac state
```

### Pattern 3: Configure via Parameters
```python
params = CouplingParameters(
    neural_to_cardiac_gain=0.5,
    cardiac_to_neural_gain=0.3,
    neural_delay=0.05,
    cardiac_delay=0.1
)
hbcm = HeartBrainCouplingModel(coupling=params)
```

### Pattern 4: Reset for New Simulation
```python
hbcm.reset_history()
trajectory = hbcm.simulate(...)
```

---

## Integration Testing Checklist

When adding new modules:

- [ ] Create subsystem model with `derivatives()` and `step()`
- [ ] Add unit tests in `tests/test_models.py`
- [ ] Extend `CouplingParameters` for new couplings
- [ ] Update `HeartBrainCouplingModel` if needed
- [ ] Add integration tests in `tests/integration/`
- [ ] Update `config/default.yaml` with new parameters
- [ ] Add documentation in `docs/`
- [ ] Test CSV export functionality
- [ ] Verify backward compatibility with existing tests

---

## Performance Tips

1. **Vectorize operations** when possible using NumPy
2. **Use smaller timesteps** for higher accuracy (trade-off with speed)
3. **Limit history size** to reduce memory usage (currently 16 memory banks)
4. **Round timestamps** to avoid floating-point errors: `round(t, 12)`
5. **Use dataclasses** for configuration (immutable, type-safe)
6. **Enable bounds checking** in Primal Logic to prevent control spikes

---

## Troubleshooting

### Issue: Simulation diverges
- Solution: Reduce timestep `dt`, reduce coupling gains

### Issue: Delays don't work
- Solution: Ensure delay <= simulation time, check history buffer size

### Issue: Control output exceeds bounds
- Solution: Check K_gain and lambda_decay parameters

### Issue: Tests fail with floating-point errors
- Solution: Use `pytest.approx()` for comparisons, increase tolerance

---

## Hardware Deployment Path

1. **Simulation** (Python + pytest) ← You are here
2. **Arduino Interface** (generated .ino code)
3. **Hardware Compilation** (Arduino IDE or PlatformIO)
4. **Microcontroller Deployment** (Arduino/STM32)
5. **Motor Integration** (MotorHandPro QUANT)
6. **Real-Time Feedback Loop** (Sensor → Control → Actuator)

---

## Key Equations Reference

### FitzHugh-Nagumo Neural Model
```
dv/dt = v - v³/3 - w + I_ext
dw/dt = (v + a - b·w) / c
```

### Van der Pol Oscillator (Cardiac)
```
dx/dt = y
dy/dt = μ(1 - x²)y - ω²x + F_ext
```

### Primal Logic Control
```
u(t) = -K ∫₀ᵗ e(τ) · e^(-λ(t-τ)) dτ
```

### Coupling Terms
```
Neural Input: I_n = G_cn · x_cardiac(t - Δ_bn) + B_n
Cardiac Input: I_c = G_nc · v_neural(t - Δ_cn) + B_c
```

---

## Version Information

- **Repository**: Multi-Heart-Model
- **Language**: Python 3.7+
- **License**: MIT
- **Patent**: U.S. Provisional Patent Application No. 63/842,846
- **Last Updated**: November 2025

---

## Additional Resources

- **Full Architecture**: See `/tmp/codebase_overview.md`
- **Visual Diagram**: See `/tmp/architecture_diagram.txt`
- **Documentation**: `docs/` directory
- **Examples**: `examples/microprocessor_motorhand_demo.py`
- **Tests**: `tests/` directory (30+ test methods)

