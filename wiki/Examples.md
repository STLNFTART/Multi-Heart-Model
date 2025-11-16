# Examples

Practical code examples for using the Multi-Heart-Model framework.

## 📚 Table of Contents

- [Basic Heart-Brain Coupling](#basic-heart-brain-coupling)
- [Custom Parameters](#custom-parameters)
- [Visualization](#visualization)
- [Export Results](#export-results)
- [Organ-On-Chip Drug Screening](#organ-on-chip-drug-screening)
- [Hardware Integration](#hardware-integration)
- [Advanced Coupling](#advanced-coupling)
- [Batch Simulations](#batch-simulations)

## 🫀 Basic Heart-Brain Coupling

### Simple Simulation

```python
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import CouplingParameters, HeartBrainCouplingModel

# Create models
neural = FitzHughNagumo(stimulus_amplitude=0.2)
cardiac = VanDerPolOscillator(mu=1.2, omega=1.0)
coupling = CouplingParameters(
    neural_to_cardiac_gain=0.5,
    cardiac_to_neural_gain=0.3
)

# Create coupled model
hbcm = HeartBrainCouplingModel(neural, cardiac, coupling)

# Run simulation
trajectory = hbcm.simulate(
    initial_state=(0.0, 0.0, 1.0, 0.0),
    t_span=(0.0, 10.0),
    dt=0.001
)

# Extract results
times, neural_states, cardiac_states = hbcm.extract_series(trajectory)

print(f"Simulation completed: {len(times)} timesteps")
print(f"Duration: {times[-1]:.2f} seconds")
```

### Manual Time Stepping

```python
from src.coupling import HeartBrainCouplingModel

# Initialize
hbcm = HeartBrainCouplingModel(neural, cardiac, coupling)
state = (0.0, 0.0, 1.0, 0.0)
dt = 0.001
t = 0.0

# Manual loop
results = []
for i in range(10000):  # 10 seconds at 1ms steps
    results.append((t, state))
    state = hbcm.step(t, state, dt)
    t += dt

print(f"Final state: {state}")
```

## ⚙️ Custom Parameters

### Parameter Exploration

```python
import numpy as np

# Test different coupling strengths
gains = np.linspace(0.0, 1.0, 11)

results = {}
for gain in gains:
    coupling = CouplingParameters(
        neural_to_cardiac_gain=gain,
        cardiac_to_neural_gain=gain * 0.6
    )

    hbcm = HeartBrainCouplingModel(neural, cardiac, coupling)
    trajectory = hbcm.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, 60.0),
        dt=0.001
    )

    times, neural_states, _ = hbcm.extract_series(trajectory)
    max_voltage = max(v for v, w in neural_states)

    results[gain] = max_voltage
    print(f"Gain {gain:.2f}: Max voltage = {max_voltage:.3f}")
```

### Loading from Configuration

```python
import yaml

# Load config
with open('config/default.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Extract parameters
neural_config = config['neural']
cardiac_config = config['cardiac']

# Create models
neural = FitzHughNagumo(
    a=neural_config.get('a', 0.7),
    b=neural_config.get('b', 0.8),
    c=neural_config.get('c', 3.0),
    stimulus_amplitude=neural_config.get('stimulus_amplitude', 0.5)
)

cardiac = VanDerPolOscillator(
    mu=cardiac_config.get('mu', 1.5),
    omega=cardiac_config['natural_frequency'],
    damping=cardiac_config['damping']
)

print("Models created from configuration")
```

## 📊 Visualization

### Basic Time Series Plot

```python
import matplotlib.pyplot as plt

times, neural, cardiac = hbcm.extract_series(trajectory)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Neural activity
ax1.plot(times, [v for v, w in neural], label='Voltage (v)', linewidth=1.5)
ax1.plot(times, [w for v, w in neural], label='Recovery (w)', linewidth=1.5, alpha=0.7)
ax1.set_ylabel('Neural State')
ax1.set_title('Neural Activity (FitzHugh-Nagumo)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Cardiac activity
ax2.plot(times, [x for x, y in cardiac], label='Position (x)', linewidth=1.5)
ax2.plot(times, [y for x, y in cardiac], label='Velocity (y)', linewidth=1.5, alpha=0.7)
ax2.set_xlabel('Time (seconds)')
ax2.set_ylabel('Cardiac State')
ax2.set_title('Cardiac Activity (Van der Pol)')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('coupling_results.png', dpi=300, bbox_inches='tight')
plt.show()
```

### Phase Space Plot

```python
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Neural phase space
v_vals = [v for v, w in neural]
w_vals = [w for v, w in neural]
ax1.plot(v_vals, w_vals, linewidth=0.8, alpha=0.7)
ax1.scatter(v_vals[0], w_vals[0], c='green', s=100, label='Start', zorder=5)
ax1.scatter(v_vals[-1], w_vals[-1], c='red', s=100, label='End', zorder=5)
ax1.set_xlabel('Voltage (v)')
ax1.set_ylabel('Recovery (w)')
ax1.set_title('Neural Phase Space')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Cardiac phase space
x_vals = [x for x, y in cardiac]
y_vals = [y for x, y in cardiac]
ax2.plot(x_vals, y_vals, linewidth=0.8, alpha=0.7)
ax2.scatter(x_vals[0], y_vals[0], c='green', s=100, label='Start', zorder=5)
ax2.scatter(x_vals[-1], y_vals[-1], c='red', s=100, label='End', zorder=5)
ax2.set_xlabel('Position (x)')
ax2.set_ylabel('Velocity (y)')
ax2.set_title('Cardiac Phase Space')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('phase_space.png', dpi=300)
plt.show()
```

### Frequency Analysis

```python
import numpy as np
from scipy import signal

# Extract voltage signal
v_signal = np.array([v for v, w in neural])
fs = 1 / (times[1] - times[0])  # Sampling frequency

# Compute power spectral density
frequencies, psd = signal.welch(v_signal, fs=fs, nperseg=1024)

# Plot
plt.figure(figsize=(10, 6))
plt.semilogy(frequencies, psd)
plt.xlabel('Frequency (Hz)')
plt.ylabel('Power Spectral Density')
plt.title('Neural Voltage Frequency Spectrum')
plt.grid(True, alpha=0.3)
plt.xlim([0, 5])  # Focus on low frequencies
plt.savefig('frequency_spectrum.png', dpi=300)
plt.show()

# Find dominant frequency
dominant_freq = frequencies[np.argmax(psd)]
print(f"Dominant frequency: {dominant_freq:.3f} Hz")
```

## 💾 Export Results

### CSV Export

```python
import csv

times, neural, cardiac = hbcm.extract_series(trajectory)

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

results_dict = {
    'metadata': {
        'duration': times[-1],
        'timestep': times[1] - times[0],
        'num_points': len(times),
        'coupling_gain_n2c': coupling.neural_to_cardiac_gain,
        'coupling_gain_c2n': coupling.cardiac_to_neural_gain
    },
    'data': {
        'times': times,
        'neural_v': [v for v, w in neural],
        'neural_w': [w for v, w in neural],
        'cardiac_x': [x for x, y in cardiac],
        'cardiac_y': [y for x, y in cardiac]
    }
}

with open('simulation_results.json', 'w') as f:
    json.dump(results_dict, f, indent=2)

print("Results exported to simulation_results.json")
```

### NumPy Archive

```python
import numpy as np

# Save as compressed NumPy archive
np.savez_compressed(
    'simulation_results.npz',
    times=np.array(times),
    neural_v=np.array([v for v, w in neural]),
    neural_w=np.array([w for v, w in neural]),
    cardiac_x=np.array([x for x, y in cardiac]),
    cardiac_y=np.array([y for x, y in cardiac])
)

# Load later
data = np.load('simulation_results.npz')
times_loaded = data['times']
v_loaded = data['neural_v']
print(f"Loaded {len(times_loaded)} time points")
```

## 🧬 Organ-On-Chip Drug Screening

### Basic Drug Test

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

# Print toxicity scores
print("\nToxicity Scores:")
for organ, score in results['toxicity_scores'].items():
    print(f"  {organ.capitalize()}: {score:.2f}")

# Print key biomarkers
cardiac_bio = results['biomarkers']['cardiac']
hepatic_bio = results['biomarkers']['hepatic']

print("\nCardiac Biomarkers:")
print(f"  Troponin I: {cardiac_bio['troponin_i'][-1]:.4f} ng/mL")
print(f"  QT interval: {cardiac_bio['qt_interval'][-1]:.2f} ms")

print("\nHepatic Biomarkers:")
print(f"  ALT: {hepatic_bio['alt'][-1]:.1f} U/L")
print(f"  AST: {hepatic_bio['ast'][-1]:.1f} U/L")
```

### Multi-Drug Comparison

```python
drugs = [
    ("Doxorubicin", 5.0),
    ("Cisplatin", 2.0),
    ("Acetaminophen", 150.0),
]

comparison_results = {}

for drug_name, dose in drugs:
    print(f"\nTesting {drug_name} at {dose} mg/kg...")

    results = suite.run_drug_test(
        drug_name=drug_name,
        dose_mg_kg=dose,
        duration_hours=24.0,
        dt_minutes=5.0
    )

    comparison_results[drug_name] = results['toxicity_scores']

# Compare cardiotoxicity
print("\nCardiotoxicity Comparison:")
for drug, scores in comparison_results.items():
    print(f"  {drug}: {scores['cardiac']:.2f}")
```

### Dose-Response Curve

```python
import numpy as np
import matplotlib.pyplot as plt

doses = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]  # mg/kg
cardiotoxicity = []

for dose in doses:
    results = suite.run_drug_test(
        drug_name="Doxorubicin",
        dose_mg_kg=dose,
        duration_hours=48.0,
        dt_minutes=5.0
    )
    cardiotoxicity.append(results['toxicity_scores']['cardiac'])

# Plot
plt.figure(figsize=(10, 6))
plt.plot(doses, cardiotoxicity, 'o-', linewidth=2, markersize=8)
plt.xlabel('Dose (mg/kg)')
plt.ylabel('Cardiotoxicity Score')
plt.title('Doxorubicin Dose-Response Curve')
plt.grid(True, alpha=0.3)
plt.xscale('log')
plt.savefig('dose_response.png', dpi=300)
plt.show()
```

## 🖥️ Hardware Integration

### Basic Control Loop

```python
from src.microprocessor import PrimalLogicProcessor
from src.integration import MotorHandProBridge

# Initialize hardware
controller = PrimalLogicProcessor(Kp=1.5, Ki=0.2)
bridge = MotorHandProBridge(device_id="/dev/ttyUSB0")

# Control loop
setpoint = 50.0  # Target velocity
dt = 0.01  # 10ms control loop

for i in range(1000):  # 10 seconds
    # Read sensors
    sensors = bridge.read_sensors()
    current_velocity = sensors['velocity']

    # Compute error
    error = setpoint - current_velocity

    # Compute control
    control = controller.compute_control(error, dt)

    # Convert to throttle [0, 255]
    throttle = int(np.clip(control * 255, 0, 255))

    # Send to hardware
    bridge.send_control(throttle=throttle, brake=0, steering=128)

    # Wait for next cycle
    time.sleep(dt)

print("Control loop completed")
```

### Emergency Braking Demo

```python
# Run the example
from examples import microprocessor_motorhand_demo

microprocessor_motorhand_demo.main()
```

## 🔬 Advanced Coupling

### Asymmetric Coupling

```python
# Strong neural → cardiac, weak cardiac → neural
coupling = CouplingParameters(
    neural_to_cardiac_gain=0.8,  # Strong
    cardiac_to_neural_gain=0.1,  # Weak
    neural_to_cardiac_delay=0.10,
    cardiac_to_neural_delay=0.20
)

hbcm = HeartBrainCouplingModel(neural, cardiac, coupling)
trajectory = hbcm.simulate(
    initial_state=(0.0, 0.0, 1.0, 0.0),
    t_span=(0.0, 30.0),
    dt=0.001
)
```

### Time-Varying Coupling

```python
# Simulate varying coupling strength over time
initial_state = (0.0, 0.0, 1.0, 0.0)
dt = 0.001
t = 0.0
duration = 60.0

results = []
state = initial_state

while t < duration:
    # Modulate coupling with time
    gain = 0.5 * (1 + 0.5 * np.sin(2 * np.pi * t / 10.0))

    coupling = CouplingParameters(
        neural_to_cardiac_gain=gain,
        cardiac_to_neural_gain=gain * 0.6
    )

    hbcm = HeartBrainCouplingModel(neural, cardiac, coupling)
    state = hbcm.step(t, state, dt)

    results.append((t, state, gain))
    t += dt

# Extract and plot
times = [r[0] for r in results]
gains = [r[2] for r in results]
voltages = [r[1][0] for r in results]  # Neural voltage

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
ax1.plot(times, gains)
ax1.set_ylabel('Coupling Gain')
ax1.set_title('Time-Varying Coupling Strength')
ax2.plot(times, voltages)
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Neural Voltage')
plt.tight_layout()
plt.show()
```

## 📦 Batch Simulations

### Parameter Sweep

```python
import itertools
import pandas as pd

# Define parameter ranges
mu_values = [0.8, 1.2, 1.6, 2.0]
gain_values = [0.2, 0.4, 0.6, 0.8]

# Run sweep
sweep_results = []

for mu, gain in itertools.product(mu_values, gain_values):
    print(f"Running: mu={mu}, gain={gain}")

    cardiac = VanDerPolOscillator(mu=mu)
    coupling = CouplingParameters(
        neural_to_cardiac_gain=gain,
        cardiac_to_neural_gain=gain * 0.6
    )

    hbcm = HeartBrainCouplingModel(neural, cardiac, coupling)
    trajectory = hbcm.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, 30.0),
        dt=0.001
    )

    times, neural_states, cardiac_states = hbcm.extract_series(trajectory)

    # Compute metrics
    max_v = max(v for v, w in neural_states)
    max_x = max(x for x, y in cardiac_states)

    sweep_results.append({
        'mu': mu,
        'gain': gain,
        'max_neural_v': max_v,
        'max_cardiac_x': max_x
    })

# Convert to DataFrame
df = pd.DataFrame(sweep_results)
print(df)

# Save results
df.to_csv('parameter_sweep.csv', index=False)
```

## 📚 See Also

- **[API Reference](API-Reference)** - Detailed API docs
- **[Getting Started](Getting-Started)** - Installation guide
- **[Development Guide](Development-Guide)** - Contributing examples

---

**Tip**: All example scripts in the `examples/` directory can be run directly:
```bash
python examples/organchip/demo_complete_system.py
```
