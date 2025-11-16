# Organ-On-Chip Platform

Comprehensive guide to the Multi-Organ Drug Toxicity Screening Platform.

## 📊 Overview

The Organ-On-Chip platform provides mechanistic multi-organ models for drug toxicity prediction. It simulates drug absorption, distribution, metabolism, and excretion (ADME) across interconnected organ models.

### Key Features

- **Multi-organ integration**: Cardiac, hepatic, renal, neural, immune, and endothelial cells
- **Drug-specific responses**: IC50-based inhibition and mechanistic toxicity
- **Comprehensive biomarkers**: Clinical markers for each organ system
- **Toxicity scoring**: Quantitative assessment of organ-specific damage
- **Time-course analysis**: Track toxicity development over hours/days

### Platform Statistics

- **Total LOC**: 2,942 (complete system)
- **Organ Models**: 5+ (extensible architecture)
- **Biomarkers**: 20+ clinical markers
- **Integration Tests**: Full suite coverage

## 🧬 Organ Models

### 1. CardiacCell

Models cardiac myocytes with ion channel dynamics.

**File**: `src/organchip/cardiac.py`

#### Key Features
- Action potential generation
- hERG (Kv11.1) potassium channel
- Drug-induced QT prolongation
- Troponin I release
- Cardiotoxicity assessment

#### State Variables
- `V`: Membrane potential (mV)
- `m`: Sodium channel activation
- `h`: Sodium channel inactivation
- `n`: Potassium channel activation
- `troponin`: Troponin I level

#### Biomarkers
```python
biomarkers = cardiac_cell.get_biomarkers(state)

# Available markers:
# - action_potential: Membrane voltage (mV)
# - qt_interval: QT interval duration (ms)
# - troponin_i: Troponin I concentration (ng/mL)
# - herg_current: hERG current magnitude
```

#### Drug Effects
- **hERG inhibition**: IC50 = 0.1-10 μM (drug-dependent)
- **QT prolongation**: Dose-dependent increase
- **Arrhythmia risk**: Torsades de pointes potential

#### Example
```python
from src.organchip.cardiac import CardiacCell

cell = CardiacCell()
state = cell.initial_state()

# Simulate with drug exposure
for t in range(1000):  # 1000 timesteps
    drug_conc = 5.0  # μM
    state = cell.step(t * 0.001, state, dt=0.001, drug_conc=drug_conc)

markers = cell.get_biomarkers(state)
print(f"QT interval: {markers['qt_interval']:.1f} ms")
print(f"Troponin I: {markers['troponin_i']:.4f} ng/mL")
```

### 2. Hepatocyte

Models liver hepatocytes with drug metabolism.

**File**: `src/organchip/hepatic.py`

#### Key Features
- CYP450 enzyme system
- Drug metabolism and clearance
- Oxidative stress response
- ALT/AST enzyme release
- Bilirubin accumulation

#### State Variables
- `viability`: Cell viability (0-1)
- `cyp450`: CYP450 enzyme activity
- `alt`: ALT enzyme level
- `ast`: AST enzyme level
- `bilirubin`: Bilirubin concentration

#### Biomarkers
```python
biomarkers = hepatocyte.get_biomarkers(state)

# Available markers:
# - alt: Alanine aminotransferase (U/L)
# - ast: Aspartate aminotransferase (U/L)
# - bilirubin: Total bilirubin (mg/dL)
# - metabolism_rate: Drug clearance rate
```

#### Drug Effects
- **Metabolism**: First-order kinetics via CYP450
- **Hepatotoxicity**: Dose-dependent cell damage
- **Enzyme release**: ALT/AST indicate liver injury

#### Clinical Thresholds
- Normal ALT: < 40 U/L
- Normal AST: < 40 U/L
- Normal bilirubin: < 1.2 mg/dL
- Toxicity: ALT/AST > 3x upper limit of normal

### 3. EndothelialCell

Models vascular endothelial cells.

**File**: `src/organchip/endothelial.py`

#### Key Features
- Barrier function
- Inflammatory response
- Permeability regulation
- Cytokine signaling

#### State Variables
- `barrier_integrity`: Barrier function (0-1)
- `inflammation`: Inflammation level
- `permeability`: Vascular permeability

#### Biomarkers
```python
biomarkers = endothelial.get_biomarkers(state)

# Available markers:
# - barrier_integrity: 0-1 scale
# - inflammation_level: Arbitrary units
# - permeability: Relative permeability
```

### 4. ImmuneCell

Models immune system response.

**File**: `src/organchip/immune.py`

#### Key Features
- Activation state
- Cytokine production
- Inflammatory mediator release
- Adaptive responses

#### State Variables
- `activation`: Cell activation level
- `cytokines`: Cytokine concentration
- `proliferation`: Cell proliferation rate

#### Biomarkers
```python
biomarkers = immune.get_biomarkers(state)

# Available markers:
# - activation_level: 0-1 scale
# - cytokine_release: pg/mL
# - inflammatory_response: Composite score
```

### 5. NeuronCell

Models neural cells and neurotoxicity.

**File**: `src/organchip/neural.py`

#### Key Features
- Synaptic transmission
- Neurotransmitter dynamics
- Excitotoxicity
- Apoptosis markers

#### State Variables
- `membrane_potential`: Neuronal voltage
- `neurotransmitter`: Neurotransmitter level
- `viability`: Cell viability

#### Biomarkers
```python
biomarkers = neuron.get_biomarkers(state)

# Available markers:
# - membrane_potential: mV
# - neurotransmitter_level: Relative units
# - viability: 0-1 scale
# - excitotoxicity: Damage indicator
```

## 🔬 OrganChipSuite

The orchestrator that coordinates all organ models.

**File**: `src/organchip/orchestrator.py`

### Architecture

```
OrganChipSuite
    ├── CardiacCell
    ├── Hepatocyte
    ├── EndothelialCell
    ├── ImmuneCell
    └── NeuronCell
         ↓
    Blood Compartment
         ↓
    Drug Pharmacokinetics
```

### Drug Pharmacokinetics

**Absorption**:
- Oral dose → GI absorption
- First-pass metabolism in liver
- Bioavailability calculation

**Distribution**:
- Blood compartment model
- Volume of distribution
- Tissue partitioning

**Metabolism**:
- Hepatic clearance (CYP450)
- Metabolite formation
- Saturable kinetics

**Excretion**:
- Renal clearance
- Biliary excretion
- Half-life calculation

### Running Drug Tests

#### Basic Test

```python
from src.organchip.orchestrator import OrganChipSuite

suite = OrganChipSuite()

results = suite.run_drug_test(
    drug_name="Doxorubicin",
    dose_mg_kg=5.0,
    duration_hours=48.0,
    dt_minutes=1.0
)
```

#### Results Structure

```python
results = {
    'drug_name': 'Doxorubicin',
    'dose_mg_kg': 5.0,
    'duration_hours': 48.0,

    'toxicity_scores': {
        'cardiac': 0.75,      # 0-1 scale
        'hepatic': 0.45,
        'renal': 0.30,
        'neural': 0.20,
        'immune': 0.35
    },

    'biomarkers': {
        'cardiac': {
            'troponin_i': [0.01, 0.02, ...],  # Time series
            'qt_interval': [380, 385, ...],
            # ...
        },
        'hepatic': {
            'alt': [25, 30, 45, ...],
            'ast': [28, 35, 52, ...],
            # ...
        },
        # ... other organs
    },

    'times': [0.0, 0.0167, 0.0333, ...],  # Hours
    'blood_concentration': [0.0, 5.2, 4.8, ...]  # μM
}
```

#### Toxicity Scoring

Toxicity scores (0-1) are computed as:

```python
score = weighted_sum([
    biomarker_deviation_1 / threshold_1,
    biomarker_deviation_2 / threshold_2,
    # ...
])

# 0.0 = No toxicity
# 0.5 = Moderate toxicity
# 1.0 = Severe toxicity
```

### Advanced Usage

#### Custom Drug Parameters

```python
# Define custom drug
custom_drug = {
    'name': 'MyDrug',
    'ic50_herg': 1.5,  # μM
    'ic50_cyp450': 10.0,  # μM
    'volume_distribution': 2.0,  # L/kg
    'clearance_rate': 0.5,  # L/h/kg
    'protein_binding': 0.9,  # fraction bound
}

# Run test
results = suite.run_drug_test(
    drug_name=custom_drug['name'],
    dose_mg_kg=10.0,
    duration_hours=72.0,
    custom_params=custom_drug
)
```

#### Multi-Dose Regimen

```python
# Simulate multiple doses
suite = OrganChipSuite()
all_results = []

doses = [5.0, 10.0, 20.0]  # mg/kg

for dose in doses:
    results = suite.run_drug_test(
        drug_name="Cisplatin",
        dose_mg_kg=dose,
        duration_hours=24.0
    )
    all_results.append(results)

# Compare toxicity
for dose, res in zip(doses, all_results):
    print(f"Dose {dose} mg/kg: Cardiotoxicity = {res['toxicity_scores']['cardiac']:.2f}")
```

## 📊 Analysis and Visualization

### Biomarker Time Series

```python
import matplotlib.pyplot as plt

results = suite.run_drug_test(
    drug_name="Doxorubicin",
    dose_mg_kg=5.0,
    duration_hours=48.0
)

times = results['times']
troponin = results['biomarkers']['cardiac']['troponin_i']
alt = results['biomarkers']['hepatic']['alt']

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

ax1.plot(times, troponin, linewidth=2)
ax1.axhline(y=0.04, color='r', linestyle='--', label='Normal threshold')
ax1.set_ylabel('Troponin I (ng/mL)')
ax1.set_title('Cardiac Damage Marker')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.plot(times, alt, linewidth=2)
ax2.axhline(y=40, color='r', linestyle='--', label='Upper limit normal')
ax2.set_xlabel('Time (hours)')
ax2.set_ylabel('ALT (U/L)')
ax2.set_title('Hepatic Damage Marker')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('biomarker_timecourse.png', dpi=300)
plt.show()
```

### Toxicity Heatmap

```python
import numpy as np
import seaborn as sns

# Run multiple drugs
drugs = ["Doxorubicin", "Cisplatin", "Acetaminophen", "Ibuprofen"]
organs = ['cardiac', 'hepatic', 'renal', 'neural', 'immune']

toxicity_matrix = []

for drug in drugs:
    results = suite.run_drug_test(drug, dose_mg_kg=5.0, duration_hours=24.0)
    toxicity_matrix.append([
        results['toxicity_scores'][organ] for organ in organs
    ])

# Plot heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(
    toxicity_matrix,
    annot=True,
    fmt='.2f',
    xticklabels=[o.capitalize() for o in organs],
    yticklabels=drugs,
    cmap='YlOrRd',
    vmin=0,
    vmax=1
)
plt.title('Multi-Drug Toxicity Profile')
plt.tight_layout()
plt.savefig('toxicity_heatmap.png', dpi=300)
plt.show()
```

### Dose-Response Analysis

```python
import numpy as np

doses = np.logspace(-1, 2, 20)  # 0.1 to 100 mg/kg
cardiotoxicity = []

for dose in doses:
    results = suite.run_drug_test(
        drug_name="Doxorubicin",
        dose_mg_kg=dose,
        duration_hours=48.0,
        dt_minutes=5.0  # Faster simulation
    )
    cardiotoxicity.append(results['toxicity_scores']['cardiac'])

# Plot dose-response
plt.figure(figsize=(10, 6))
plt.semilogx(doses, cardiotoxicity, 'o-', linewidth=2, markersize=6)
plt.xlabel('Dose (mg/kg)')
plt.ylabel('Cardiotoxicity Score')
plt.title('Doxorubicin Dose-Response Curve')
plt.grid(True, alpha=0.3)
plt.axhline(y=0.5, color='r', linestyle='--', label='Moderate toxicity threshold')
plt.legend()
plt.savefig('dose_response.png', dpi=300)
plt.show()

# Compute EC50 (dose for 50% effect)
from scipy.interpolate import interp1d
f = interp1d(cardiotoxicity, doses)
ec50 = float(f(0.5))
print(f"EC50: {ec50:.2f} mg/kg")
```

## 🧪 Validation

### Clinical Correlation

The platform biomarkers correlate with clinical observations:

| Drug | Platform Cardiac | Clinical Observation |
|------|-----------------|---------------------|
| Doxorubicin | High (0.7-0.9) | Known cardiotoxicity |
| Cisplatin | Moderate (0.4-0.6) | Moderate cardiotoxicity |
| Acetaminophen | Low (0.1-0.3) | Minimal cardiac effects |

| Drug | Platform Hepatic | Clinical Observation |
|------|-----------------|---------------------|
| Acetaminophen | High (0.7-0.9) | Known hepatotoxicity |
| Doxorubicin | Moderate (0.4-0.6) | Moderate hepatotoxicity |
| Ibuprofen | Low (0.2-0.4) | Minimal hepatic effects |

### Validation Tests

```bash
# Run validation suite
python validate_organchip.py

# Expected output:
# ✓ Cardiac model validation passed
# ✓ Hepatic model validation passed
# ✓ Drug metabolism validation passed
# ✓ Integration test passed
```

## 🔧 Extending the Platform

### Adding a New Organ

Example: Adding a kidney model

```python
# src/organchip/kidney.py

from dataclasses import dataclass
from typing import Tuple

@dataclass
class KidneyParameters:
    """Kidney model parameters."""
    gfr: float = 120.0  # mL/min
    clearance_rate: float = 0.5
    damage_threshold: float = 10.0  # μM

class KidneyCell:
    """Kidney cell model for nephrotoxicity."""

    def __init__(self, params: KidneyParameters = None):
        self.params = params or KidneyParameters()

    def initial_state(self) -> Tuple[float, float, float]:
        """Return initial state (gfr, damage, creatinine)."""
        return (self.params.gfr, 0.0, 1.0)

    def step(
        self,
        t: float,
        state: Tuple[float, float, float],
        dt: float,
        drug_conc: float = 0.0
    ) -> Tuple[float, float, float]:
        """
        Advance kidney state.

        Args:
            t: Current time (minutes)
            state: (gfr, damage, creatinine)
            dt: Timestep (minutes)
            drug_conc: Drug concentration (μM)

        Returns:
            New state
        """
        gfr, damage, creatinine = state

        # Drug-induced damage
        if drug_conc > self.params.damage_threshold:
            damage_rate = 0.01 * (drug_conc - self.params.damage_threshold)
        else:
            damage_rate = 0.0

        # GFR decline with damage
        gfr_new = gfr * (1 - 0.001 * damage * dt)

        # Creatinine accumulation
        creat_production = 0.01  # Baseline production
        creat_clearance = gfr_new / 100.0
        creat_new = creatinine + dt * (creat_production - creat_clearance * creatinine)

        # Update damage
        damage_new = damage + dt * damage_rate

        return (gfr_new, damage_new, creat_new)

    def get_biomarkers(self, state: Tuple[float, float, float]) -> dict:
        """Extract kidney biomarkers."""
        gfr, damage, creatinine = state
        return {
            'gfr': gfr,
            'creatinine': creatinine,
            'damage_index': damage,
            'nephrotoxicity_score': min(damage / 100.0, 1.0)
        }
```

Then integrate into `OrganChipSuite`:

```python
# In src/organchip/orchestrator.py

from .kidney import KidneyCell

class OrganChipSuite:
    def __init__(self):
        # ... existing organs
        self.kidney = KidneyCell()
        self.kidney_state = self.kidney.initial_state()

    def step(self, t, states, dt, drug_conc):
        # ... existing organs

        # Step kidney
        states['kidney'] = self.kidney.step(
            t, states['kidney'], dt, drug_conc
        )

        return states
```

## 📚 See Also

- **[API Reference](API-Reference)** - Detailed API for organ models
- **[Examples](Examples)** - Usage examples
- **[Getting Started](Getting-Started)** - Quick start guide

---

**For more information**, see `docs/ORGAN_CHIP_GUIDE.md` in the repository.
