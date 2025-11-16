# Frequently Asked Questions (FAQ)

Common questions and answers about the Multi-Heart-Model project.

## 🎯 General Questions

### What is the Multi-Heart-Model?

The Multi-Heart-Model (HBCM - Heart-Brain Coupling Model) is a multi-domain physiological modeling platform that integrates:
- Neural-cardiac coupling via delay-differential equations
- Hardware control integration for automotive systems
- Organ-on-chip drug toxicity screening
- Multiple language implementations (Python, D, APL)

### Who should use this project?

- **Researchers**: Studying heart-brain interactions and autonomic regulation
- **Drug developers**: Screening compounds for organ toxicity
- **Control engineers**: Implementing physiological feedback in hardware systems
- **Educators**: Teaching computational physiology and dynamical systems

### What license is it under?

MIT License - free for academic and commercial use with attribution.

### How do I get started?

See the [Getting Started](Getting-Started) guide for installation and your first simulation.

## 🔧 Installation & Setup

### What are the minimum requirements?

- Python 3.8 or higher
- NumPy (only required dependency)
- 50 MB disk space
- No GPU required

### Do I need a GPU?

No, all computations run on CPU. The models are designed to be lightweight and efficient.

### Can I use this on Windows/Mac/Linux?

Yes! The Python implementation works on all platforms. The D implementation requires a D compiler (available for all platforms).

### Installation fails with "module not found"

Ensure you're running from the repository root:
```bash
cd Multi-Heart-Model
python -c "from src.coupling import HeartBrainCouplingModel"
```

If still failing, check your Python path:
```bash
python -c "import sys; print(sys.path)"
```

## 🧪 Usage Questions

### How long should my timestep be?

**Recommended**: `dt = 0.001` (1 millisecond)

- Smaller is more accurate but slower
- Larger than 0.01 may cause instability
- Use 0.0001 for very stiff systems

### What initial conditions should I use?

**Default safe values**:
```python
initial_state = (0.0, 0.0, 1.0, 0.0)  # (v, w, x, y)
```

- Neural starts at rest: `(v=0, w=0)`
- Cardiac starts displaced: `(x=1, y=0)`
- Experiment to find interesting dynamics!

### My simulation produces NaN/Inf values. Why?

Common causes:
1. **Timestep too large**: Reduce `dt` to 0.001 or smaller
2. **Parameters out of range**: Check parameter bounds in [API Reference](API-Reference)
3. **Numerical instability**: Add damping or reduce coupling gains

**Debug**:
```python
for t, state in trajectory:
    if not all(np.isfinite(state)):
        print(f"Instability at t={t}: {state}")
        break
```

### How do I visualize results?

Use matplotlib:
```python
import matplotlib.pyplot as plt

times, neural, cardiac = hbcm.extract_series(trajectory)

plt.plot(times, [v for v, w in neural])
plt.xlabel('Time (s)')
plt.ylabel('Neural Voltage')
plt.show()
```

See [Examples](Examples) for more visualization code.

### Can I save simulation results?

Yes! Export to CSV, JSON, or NumPy:

**CSV**:
```python
import csv
with open('results.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['time', 'neural_v', 'cardiac_x'])
    for i, t in enumerate(times):
        writer.writerow([t, neural[i][0], cardiac[i][0]])
```

**NumPy**:
```python
np.savez('results.npz', times=times, neural=neural, cardiac=cardiac)
```

## 🧬 Organ-On-Chip Questions

### What organs are supported?

Currently:
- **CardiacCell**: Heart muscle cells
- **Hepatocyte**: Liver cells
- **EndothelialCell**: Vascular cells
- **ImmuneCell**: Immune system
- **NeuronCell**: Neural cells

Easily extensible - see [Organ-Chip-Platform](Organ-Chip-Platform) for adding organs.

### How accurate are toxicity predictions?

The models are mechanistic and correlate with clinical observations, but are:
- **Not FDA-approved** for regulatory decisions
- **Research tools** for hypothesis testing
- **Screening platforms** to prioritize compounds

Always validate with in vitro/in vivo experiments.

### Can I test my own drug?

Yes! Provide custom drug parameters:
```python
results = suite.run_drug_test(
    drug_name="MyDrug",
    dose_mg_kg=5.0,
    duration_hours=48.0,
    custom_params={
        'ic50_herg': 1.5,  # μM
        'ic50_cyp450': 10.0,
    }
)
```

### What units are used?

**Time**: hours (organ chip) or seconds (heart-brain)
**Concentration**: μM (micromolar)
**Dose**: mg/kg body weight
**Biomarkers**: Standard clinical units (ng/mL, U/L, etc.)

Always check docstrings for specific units!

## 🖥️ Hardware Integration Questions

### What hardware is supported?

- **MotorHandPro QUANT**: Automotive control platform
- **Serial communication**: RS-232, USB-Serial

### Do I need special hardware to run examples?

No! Examples work with simulated hardware by default. Real hardware is optional.

To use simulation mode:
```python
from src.integration import MockMotorHandBridge
bridge = MockMotorHandBridge()  # Simulated
```

### How do I connect to real hardware?

1. Connect via USB-Serial adapter
2. Identify port: `ls /dev/ttyUSB*` (Linux) or Device Manager (Windows)
3. Create bridge:
```python
bridge = MotorHandProBridge(device_id="/dev/ttyUSB0")
bridge.connect()
```

### What if I get "Permission denied" on serial port?

**Linux**:
```bash
sudo chmod 666 /dev/ttyUSB0
# Or add user to dialout group:
sudo usermod -a -G dialout $USER
# Then log out and back in
```

**Windows**: Run as Administrator or adjust COM port permissions

## 🔬 Scientific Questions

### What's the mathematical basis?

Delay-differential equations for coupled oscillators:

```
dn_b/dt = -λ_b n_b(t) + f_b[n_h(t - Δ_bh), S_b(t)]
dn_h/dt = -λ_h n_h(t) + f_h[n_b(t - Δ_hb), S_h(t)]
```

See [Architecture](Architecture) for details.

### What integration method is used?

**Forward Euler** by default:
- Simple and transparent
- First-order accuracy
- Requires small timesteps

**Why not RK4 or adaptive methods?**
- Prioritizing simplicity and transparency
- Euler is sufficient for non-stiff physiological models
- D implementation available for speed-critical applications

### Can I use different coupling functions?

Yes! Extend the coupling models:

```python
class CustomCouplingModel(HeartBrainCouplingModel):
    def _compute_coupling(self, neural_state, cardiac_state):
        # Custom coupling logic
        return custom_neural_input, custom_cardiac_input
```

### Are there published papers using this model?

The framework implements established models:
- **FitzHugh-Nagumo**: Neural excitability (FitzHugh 1961, Nagumo 1962)
- **Van der Pol**: Cardiac oscillations (Van der Pol 1926)
- **Delay coupling**: Physiological delays (Pfeiffer et al. 2020)

See `docs/` for references.

## 💻 Performance Questions

### How fast is it?

**Python implementation**:
- 60 seconds of simulation in ~0.5 seconds (real-time × 120)
- 10,000 timesteps/second on modern CPU

**D implementation**:
- 10-100× faster than Python
- Suitable for real-time hardware control

### Can I speed it up?

1. **Use D implementation**: `make build && ./primal_overlay`
2. **Increase timestep**: Balance speed vs accuracy
3. **Reduce history buffer**: Shorter delays = less memory
4. **Profile code**: `python -m cProfile your_script.py`

### How much memory does it use?

**Typical simulation** (60 seconds, dt=0.001):
- Trajectory: ~5 MB
- History buffer: ~2 MB
- Total: ~10 MB

**Large simulations** (1 hour, dt=0.0001):
- Trajectory: ~300 MB
- May need to downsample or stream to disk

### Can I run parallel simulations?

Yes! Simulations are independent:

```python
from multiprocessing import Pool

def run_sim(gain):
    coupling = CouplingParameters(neural_to_cardiac_gain=gain)
    hbcm = HeartBrainCouplingModel(neural, cardiac, coupling)
    return hbcm.simulate(...)

gains = [0.1, 0.2, 0.3, 0.4, 0.5]
with Pool(4) as p:
    results = p.map(run_sim, gains)
```

## 🛠️ Development Questions

### How do I contribute?

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request

See [Development Guide](Development-Guide) for details.

### What coding style should I follow?

- **PEP 8** for Python
- **Type hints** on all public APIs
- **Google-style docstrings**
- **100% test coverage** for new code

### How do I add a new model?

Follow existing patterns:

1. Create `src/module/model.py`
2. Implement `derivatives()` and `step()` methods
3. Add to `__init__.py`
4. Write tests in `tests/test_module/`
5. Update documentation

See [Development Guide](Development-Guide) for detailed instructions.

### Where should tests go?

Mirror source structure:
- `src/cardiac/van_der_pol.py` → `tests/test_cardiac/test_van_der_pol.py`
- `src/neural/fitzhugh_nagumo.py` → `tests/test_neural/test_fitzhugh_nagumo.py`

### How do I run tests?

```bash
pytest tests/ -v                    # All tests
pytest tests/test_models.py -v     # Specific file
pytest tests/ --cov=src            # With coverage
```

See [Testing](Testing) for complete guide.

## 🐛 Troubleshooting

### Import errors when running examples

Ensure you're in the repository root:
```bash
cd Multi-Heart-Model
python examples/microprocessor_motorhand_demo.py
```

### ModuleNotFoundError: No module named 'src'

Python can't find the source. Either:
1. Run from repository root
2. Add to PYTHONPATH: `export PYTHONPATH=$PYTHONPATH:$(pwd)`
3. Install as package: `pip install -e .`

### Tests fail with "fixture not found"

Make sure `conftest.py` is in the tests directory:
```
tests/
├── conftest.py  # Required!
├── test_models.py
└── ...
```

### D build fails

Install D compiler:
```bash
# Ubuntu/Debian
sudo apt-get install ldc

# macOS
brew install ldc

# Or download from https://dlang.org/download.html
```

### Simulation hangs/freezes

Check for infinite loop or very long simulation:
```python
# Add timeout or progress indicator
import time
start = time.time()
for i, (t, state) in enumerate(trajectory):
    if i % 1000 == 0:
        print(f"Progress: {t:.1f}s / {t_end}s")
    if time.time() - start > 60:
        print("Timeout!")
        break
```

## 📚 Documentation Questions

### Where is the complete documentation?

- **Wiki**: [Home](Home) - Start here!
- **Repository docs**: `docs/` directory
- **Code docs**: Docstrings in source code
- **AI assistant guide**: `CLAUDE.md`

### Is there a quick reference?

Yes! See [docs/QUICK_REFERENCE.md](https://github.com/STLNFTART/Multi-Heart-Model/blob/main/docs/QUICK_REFERENCE.md) for parameter tables and quick examples.

### Are there API docs?

Yes! [API Reference](API-Reference) has complete API documentation.

### Where can I find examples?

- **Wiki**: [Examples](Examples) page
- **Repository**: `examples/` directory
- **Tests**: `tests/` directory (shows API usage)

## 🤝 Support

### Where do I report bugs?

[GitHub Issues](https://github.com/STLNFTART/Multi-Heart-Model/issues)

Please include:
- Python version
- Operating system
- Minimal code to reproduce
- Error message (full traceback)

### How do I ask questions?

- **General questions**: [GitHub Discussions](https://github.com/STLNFTART/Multi-Heart-Model/discussions)
- **Bugs**: [GitHub Issues](https://github.com/STLNFTART/Multi-Heart-Model/issues)
- **Features**: [GitHub Issues](https://github.com/STLNFTART/Multi-Heart-Model/issues) with "enhancement" label

### Is there a mailing list or forum?

Use [GitHub Discussions](https://github.com/STLNFTART/Multi-Heart-Model/discussions) for community discussions.

### Can I hire support/consulting?

Contact the maintainers via GitHub for commercial support inquiries.

## 🔗 See Also

- **[Getting Started](Getting-Started)** - Installation and first steps
- **[Examples](Examples)** - Code examples
- **[Development Guide](Development-Guide)** - Contributing
- **[API Reference](API-Reference)** - Complete API docs

---

**Still have questions?** Ask on [GitHub Discussions](https://github.com/STLNFTART/Multi-Heart-Model/discussions)!
