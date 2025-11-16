# Getting Started

This guide will help you set up and run your first Heart-Brain Coupling Model simulation.

## 📋 Prerequisites

- **Python**: 3.8 or higher
- **NumPy**: For numerical computations
- **Git**: For cloning the repository
- **Optional**: Matplotlib for visualization

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/STLNFTART/Multi-Heart-Model.git
cd Multi-Heart-Model
```

### 2. Install Dependencies

```bash
# Using pip
pip install numpy

# Optional: For visualization
pip install matplotlib

# Optional: For testing
pip install pytest pytest-cov
```

### 3. Verify Installation

```bash
# Run the test suite
pytest tests/ -v

# Run validation scripts
python validate_integration.py
python validate_organchip.py
```

## 🚀 Your First Simulation

### Basic Heart-Brain Coupling

Create a new Python file (e.g., `my_first_simulation.py`):

```python
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import CouplingParameters, HeartBrainCouplingModel

# Create the coupled model
hbcm = HeartBrainCouplingModel(
    neural_model=FitzHughNagumo(stimulus_amplitude=0.2),
    cardiac_model=VanDerPolOscillator(mu=1.2, omega=1.0),
    coupling=CouplingParameters(
        neural_to_cardiac_gain=0.5,
        cardiac_to_neural_gain=0.3
    ),
)

# Run simulation for 10 seconds
trajectory = hbcm.simulate(
    initial_state=(0.0, 0.0, 1.0, 0.0),  # (v, w, x, y)
    t_span=(0.0, 10.0),  # 10 seconds
    dt=0.01  # 10ms timestep
)

# Extract results
times, neural, cardiac = hbcm.extract_series(trajectory)

# Print summary
print(f"Simulation completed: {len(times)} timesteps")
print(f"Neural amplitude: {max(v for v, w in neural):.3f}")
print(f"Cardiac amplitude: {max(x for x, y in cardiac):.3f}")
```

Run it:

```bash
python my_first_simulation.py
```

### Visualize Results

Add visualization to your script:

```python
import matplotlib.pyplot as plt

# Create figure with subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6))

# Plot neural activity
ax1.plot(times, [v for v, w in neural], label='Voltage (v)', color='blue')
ax1.plot(times, [w for v, w in neural], label='Recovery (w)', color='red', alpha=0.7)
ax1.set_ylabel('Neural State')
ax1.set_title('Neural Activity (FitzHugh-Nagumo)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot cardiac activity
ax2.plot(times, [x for x, y in cardiac], label='Position (x)', color='green')
ax2.plot(times, [y for x, y in cardiac], label='Velocity (y)', color='orange', alpha=0.7)
ax2.set_xlabel('Time (seconds)')
ax2.set_ylabel('Cardiac State')
ax2.set_title('Cardiac Activity (Van der Pol)')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('heart_brain_coupling.png', dpi=300)
plt.show()

print("Plot saved to heart_brain_coupling.png")
```

## 🧪 Running Examples

The repository includes several demonstration scripts:

### Microprocessor Integration

```bash
python examples/microprocessor_motorhand_demo.py
```

This demonstrates:
- Hardware control integration
- Primal Logic Processor usage
- Motor hand bridge interface

### Organ-On-Chip Platform

```bash
# Complete system demo
python examples/organchip/demo_complete_system.py

# Drug screening demo
python examples/organchip/demo_drug_screening.py

# Cardiotoxicity demo
python examples/organchip/demo_cardiotoxicity.py
```

## 📊 Working with Configuration Files

Simulations can be configured using YAML files in the `config/` directory.

### Using Custom Configuration

```python
import yaml
from src.coupling import HeartBrainCouplingModel, CouplingParameters
from src.neural import FitzHughNagumo
from src.cardiac import VanDerPolOscillator

# Load configuration
with open('config/default.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create models from config
neural_config = config['neural']
cardiac_config = config['cardiac']

neural_model = FitzHughNagumo(
    a=neural_config.get('a', 0.7),
    b=neural_config.get('b', 0.8),
    c=neural_config.get('c', 3.0)
)

cardiac_model = VanDerPolOscillator(
    mu=cardiac_config.get('mu', 1.5),
    omega=cardiac_config.get('omega', 1.0)
)

# Create coupling
coupling = CouplingParameters(
    neural_to_cardiac_gain=neural_config['feedback_strength'],
    cardiac_to_neural_gain=cardiac_config['feedback_strength'],
    neural_to_cardiac_delay=neural_config['delay_to_heart'],
    cardiac_to_neural_delay=cardiac_config['delay_to_brain']
)

# Create and run model
hbcm = HeartBrainCouplingModel(neural_model, cardiac_model, coupling)
```

## 🏗️ Building the D Implementation

For high-performance simulations, you can build the D language implementation:

```bash
# Install D compiler (if not already installed)
# Visit: https://dlang.org/download.html

# Build with dub
dub build --compiler=ldc2 --build=release

# Or use make
make build

# Run the executable
./primal_overlay
```

The D executable writes results to `results.csv`.

## 🧬 Organ-On-Chip Quick Start

For drug toxicity screening:

```python
from src.organchip.orchestrator import OrganChipSuite

# Create the platform
suite = OrganChipSuite()

# Run a drug test
results = suite.run_drug_test(
    drug_name="Doxorubicin",
    dose_mg_kg=5.0,
    duration_hours=48.0,
    dt_minutes=1.0
)

# Check toxicity scores
print(f"Cardiotoxicity: {results['toxicity_scores']['cardiac']:.2f}")
print(f"Hepatotoxicity: {results['toxicity_scores']['hepatic']:.2f}")
print(f"Nephrotoxicity: {results['toxicity_scores']['renal']:.2f}")

# Access detailed biomarkers
cardiac_biomarkers = results['biomarkers']['cardiac']
print(f"Troponin I: {cardiac_biomarkers['troponin_i']:.4f} ng/mL")
```

## 📝 Export Results

### CSV Export

```python
import csv

# Export time series to CSV
with open('simulation_results.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['time', 'neural_v', 'neural_w', 'cardiac_x', 'cardiac_y'])

    for i, t in enumerate(times):
        v, w = neural[i]
        x, y = cardiac[i]
        writer.writerow([t, v, w, x, y])

print("Results exported to simulation_results.csv")
```

### JSON Export

```python
import json

# Export results as JSON
results_dict = {
    'metadata': {
        'duration': times[-1],
        'timestep': times[1] - times[0],
        'num_points': len(times)
    },
    'neural': {
        'voltage': [v for v, w in neural],
        'recovery': [w for v, w in neural]
    },
    'cardiac': {
        'position': [x for x, y in cardiac],
        'velocity': [y for x, y in cardiac]
    }
}

with open('simulation_results.json', 'w') as f:
    json.dump(results_dict, f, indent=2)

print("Results exported to simulation_results.json")
```

## 🐛 Troubleshooting

### Import Errors

If you get import errors, make sure you're running from the repository root:

```bash
cd /path/to/Multi-Heart-Model
python -c "from src.coupling import HeartBrainCouplingModel"
```

### Numerical Instability

If simulations produce NaN or Inf values:

1. **Reduce timestep**: Try `dt=0.001` instead of `dt=0.01`
2. **Check parameters**: Ensure parameters are in valid ranges
3. **Add damping**: Increase damping coefficients

### D Build Errors

If the D build fails:

```bash
# Clean and rebuild
make clean
make build

# Or with dub
dub clean
dub build --compiler=ldc2 --build=release
```

## 📚 Next Steps

- **[Architecture](Architecture)** - Understand the system design
- **[Examples](Examples)** - Explore more code examples
- **[API Reference](API-Reference)** - Detailed API documentation
- **[Development Guide](Development-Guide)** - Start contributing

## 💡 Tips

1. **Start small**: Begin with short simulations (10-60 seconds)
2. **Use small timesteps**: `dt=0.001` is recommended for stability
3. **Validate results**: Check that outputs are physiologically reasonable
4. **Save your work**: Export results to CSV/JSON for later analysis
5. **Visualize often**: Plotting helps identify issues early

---

**Next**: [Examples →](Examples)
