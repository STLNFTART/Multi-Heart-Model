# Organ Chip Suite - Quick Start Guide

## Installation

The organ chip suite is part of the Multi-Heart-Model repository.

```bash
# Clone repository
git clone https://github.com/STLNFTART/Multi-Heart-Model.git
cd Multi-Heart-Model

# Install dependencies (if needed)
pip install numpy scipy matplotlib pytest
```

## Running Your First Simulation

### 1. Basic Drug Toxicity Study

```python
from src.organchip.orchestrator import create_default_organ_chip_suite

# Create the organ chip suite
suite = create_default_organ_chip_suite()

# Run a complete drug toxicity study
trajectory, toxicity = suite.run_complete_study(
    dose_mg=100.0,         # Drug dose in milligrams
    duration_hours=48.0,   # Simulation duration
    export_file="my_study_results.json"
)

# View results
print(f"Overall Toxicity: {toxicity['overall_severity']}")
print(f"Liver Toxicity: {toxicity['liver']['severity']}")
print(f"Cardiac Toxicity: {toxicity['cardiac']['severity']}")
```

### 2. Testing a Cardiotoxic Drug

```python
from src.organchip.orchestrator import create_default_organ_chip_suite

# Create suite
suite = create_default_organ_chip_suite()

# Configure for hERG channel blocker
suite.cardiac.ion_channels.IC50_hERG = 0.5  # Potent hERG blocker (μM)

# Run study
trajectory, tox = suite.run_complete_study(
    dose_mg=200.0,
    duration_hours=48.0
)

# Check QT prolongation
qtc_change = tox['cardiac']['QTc_prolongation_ms']
risk = tox['cardiac']['arrhythmia_risk']

print(f"QTc Prolongation: {qtc_change:.1f} ms")
print(f"Arrhythmia Risk: {risk}")
```

### 3. Testing a Hepatotoxic Drug

```python
from src.organchip.orchestrator import create_default_organ_chip_suite

# Create suite
suite = create_default_organ_chip_suite()

# Configure for reactive metabolite formation
suite.liver.metabolism.frac_phase1_to_reactive = 0.4  # 40% forms reactive metabolite

# Run study
trajectory, tox = suite.run_complete_study(
    dose_mg=500.0,
    duration_hours=72.0
)

# Check liver injury
alt_fold = tox['liver']['ALT_elevation_fold']
gsh_depletion = tox['liver']['GSH_depletion']
viability = tox['liver']['cell_viability']

print(f"ALT Elevation: {alt_fold:.1f}x normal")
print(f"GSH Depletion: {gsh_depletion:.1%}")
print(f"Cell Viability: {viability:.1%}")
```

## Running Example Demonstrations

### Complete System Demo

```bash
cd examples/organchip
python demo_complete_system.py
```

This runs 4 scenarios:
1. Therapeutic dose
2. High dose
3. Cardiotoxic drug (hERG blocker)
4. Hepatotoxic drug (reactive metabolite)

### Ligand-Receptor Binding Demo

```bash
python demo_ligand_receptor.py
```

Demonstrates:
- Basic receptor binding kinetics
- Competitive inhibition
- Receptor desensitization
- Dose-response curves

### Immune Response Demo

```bash
python demo_immune_response.py
```

Shows:
- Inflammatory cascade
- Acute phase response
- Drug-induced inflammation
- Resolution phase

## Running Tests

### Run All Organ Chip Tests

```bash
cd tests/organchip
pytest test_drug_toxicity.py -v
```

### Run Specific Test Classes

```bash
# Test doxorubicin cardiotoxicity
pytest test_drug_toxicity.py::TestDoxorubicinCardiotoxicity -v

# Test acetaminophen hepatotoxicity
pytest test_drug_toxicity.py::TestAcetaminophenHepatotoxicity -v

# Test multi-organ interactions
pytest test_drug_toxicity.py::TestMultiOrganInteractions -v
```

## Understanding Results

### Toxicity Assessment Output

```python
{
    'overall_toxicity_score': 0.523,
    'overall_severity': 'Moderate - Caution',

    'liver': {
        'toxicity_score': 0.612,
        'severity': 'Moderate',
        'ALT_elevation_fold': 4.2,
        'AST_elevation_fold': 3.8,
        'GSH_depletion': 0.45,
        'cell_viability': 0.78
    },

    'cardiac': {
        'toxicity_score': 0.434,
        'severity': 'Mild',
        'QTc_prolongation_ms': 25.3,
        'arrhythmia_risk': 'Moderate',
        'force_reduction_pct': 18.5,
        'troponin_fold_elevation': 2.1
    },

    'immune': {
        'inflammatory_index': 3.2,
        'TNFa_fold': 4.5,
        'IL6_fold': 6.2
    }
}
```

### Interpreting Scores

**Overall Toxicity Score** (0-1):
- **< 0.2**: Safe - No concerns
- **0.2-0.4**: Mild - Monitor closely
- **0.4-0.6**: Moderate - Use with caution
- **0.6-0.8**: Severe - High risk
- **> 0.8**: Critical - Avoid use

**Biomarker Thresholds**:

| Biomarker | Normal | Elevated | Severe |
|-----------|--------|----------|--------|
| ALT | < 40 U/L | 40-200 U/L | > 200 U/L |
| AST | < 40 U/L | 40-200 U/L | > 200 U/L |
| Troponin | < 0.04 ng/mL | 0.04-0.4 ng/mL | > 0.4 ng/mL |
| QTc prolongation | < 10 ms | 10-30 ms | > 30 ms |

## Customizing Simulations

### Adjusting Drug Parameters

```python
suite = create_default_organ_chip_suite()

# Cardiac parameters
suite.cardiac.ion_channels.IC50_hERG = 2.0    # hERG inhibition (μM)
suite.cardiac.ion_channels.IC50_Nav = 50.0    # Nav inhibition (μM)
suite.cardiac.ion_channels.IC50_Cav = 100.0   # Cav inhibition (μM)

# Liver parameters
suite.liver.metabolism.params.Vmax_phase1 = 150.0  # Phase I Vmax (μM/h)
suite.liver.metabolism.params.Km_phase1 = 40.0     # Phase I Km (μM)
suite.liver.metabolism.frac_phase1_to_reactive = 0.25

# Run customized study
trajectory, tox = suite.run_complete_study(dose_mg=300.0, duration_hours=48.0)
```

### Extracting Time Series Data

```python
# Run simulation
trajectory, _ = suite.simulate_drug_exposure(
    dose_mg=200.0,
    duration_hours=72.0,
    dt=0.1
)

# Extract specific metrics
times = []
plasma_conc = []
liver_viability = []
cardiac_troponin = []

for t, state in trajectory:
    times.append(t)

    # Plasma drug concentration
    plasma_drug = state['circulation']['plasma'] / 3.0  # Vplasma = 3L
    plasma_conc.append(plasma_drug)

    # Liver viability
    liver_viability.append(state['liver']['Cell_viability'])

    # Cardiac troponin
    cardiac_troponin.append(state['cardiac']['Troponin'])

# Plot with matplotlib
import matplotlib.pyplot as plt

fig, axes = plt.subplots(3, 1, figsize=(10, 8))

axes[0].plot(times, plasma_conc)
axes[0].set_ylabel('Plasma [μM]')
axes[0].set_title('Drug Concentration')

axes[1].plot(times, liver_viability)
axes[1].set_ylabel('Viability')
axes[1].set_title('Liver Cell Viability')

axes[2].plot(times, cardiac_troponin)
axes[2].set_ylabel('Troponin [ng/mL]')
axes[2].set_xlabel('Time [hours]')
axes[2].set_title('Cardiac Troponin Release')

plt.tight_layout()
plt.savefig('toxicity_timecourse.png')
```

## Common Use Cases

### 1. Dose-Response Study

```python
suite = create_default_organ_chip_suite()

doses = [10, 50, 100, 200, 500, 1000]  # mg
results = []

for dose in doses:
    _, tox = suite.run_complete_study(
        dose_mg=dose,
        duration_hours=48.0,
        export_file=None
    )
    results.append({
        'dose': dose,
        'toxicity_score': tox['overall_toxicity_score'],
        'liver_severity': tox['liver']['severity'],
        'cardiac_severity': tox['cardiac']['severity']
    })

# Print dose-response table
for r in results:
    print(f"Dose: {r['dose']:>4} mg | "
          f"Score: {r['toxicity_score']:.3f} | "
          f"Liver: {r['liver_severity']:<10} | "
          f"Cardiac: {r['cardiac_severity']}")
```

### 2. Drug Comparison

```python
def test_drug(name, ic50_herg, reactive_frac):
    suite = create_default_organ_chip_suite()
    suite.cardiac.ion_channels.IC50_hERG = ic50_herg
    suite.liver.metabolism.frac_phase1_to_reactive = reactive_frac

    _, tox = suite.run_complete_study(dose_mg=200.0, duration_hours=48.0)

    return {
        'name': name,
        'overall': tox['overall_toxicity_score'],
        'liver': tox['liver']['toxicity_score'],
        'cardiac': tox['cardiac']['toxicity_score']
    }

# Compare drugs
drugs = [
    test_drug('Drug A', ic50_herg=10.0, reactive_frac=0.1),
    test_drug('Drug B', ic50_herg=1.0, reactive_frac=0.3),
    test_drug('Drug C', ic50_herg=5.0, reactive_frac=0.05),
]

# Print comparison
print(f"{'Drug':<10} {'Overall':<10} {'Liver':<10} {'Cardiac':<10}")
print("-" * 45)
for d in drugs:
    print(f"{d['name']:<10} {d['overall']:<10.3f} "
          f"{d['liver']:<10.3f} {d['cardiac']:<10.3f}")
```

## Troubleshooting

### Common Issues

**1. Import errors**
```python
# Make sure to add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
```

**2. Simulation too slow**
```python
# Use larger time step (less accurate but faster)
trajectory, tox = suite.run_complete_study(
    dose_mg=100.0,
    duration_hours=48.0,
    dt=0.5  # Larger time step
)
```

**3. Unrealistic results**
```python
# Check parameter ranges
# IC50 should be in μM (not nM or mM)
# Doses should be in mg (not μg or g)
# Time should be in hours
```

## Next Steps

1. Read the full [Architecture Documentation](organchip_architecture.md)
2. Explore [Example Demonstrations](../examples/organchip/)
3. Review [Test Suite](../tests/organchip/) for validation cases
4. Customize parameters for your specific drug
5. Export and analyze results

## Support

For questions or issues:
- Check documentation in `docs/`
- Review examples in `examples/organchip/`
- Run tests to verify installation
- Open an issue on GitHub

## Citation

If you use this organ chip suite in your research, please cite:

```
Multi-Heart-Model Organ Chip Suite
https://github.com/STLNFTART/Multi-Heart-Model
```
