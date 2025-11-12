# Organ-On-Chip Multiscale Modeling Suite

## Overview

The Organ-On-Chip suite is a comprehensive multiscale modeling framework for simulating drug-induced toxicity in a body-on-a-chip system. It integrates models across five distinct spatial and temporal scales:

1. **Molecular** (μs-ms): Ligand-receptor binding dynamics
2. **Cellular** (ms-s): Ion channels, immune signaling, enzyme kinetics
3. **Tissue** (s-min): Hepatocyte populations, local metabolism
4. **Organ** (min-h): Liver function, cardiac electrophysiology
5. **Systemic** (h-days): Pharmacokinetics, drug distribution

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/STLNFTART/Multi-Heart-Model.git
cd Multi-Heart-Model

# Install dependencies
pip install numpy pytest

# Verify installation
python -c "from organ_chip.orchestrator import OrganChipSuite; print('✓ Installation successful')"
```

### Basic Usage

```python
from organ_chip.orchestrator import OrganChipSuite

# Create acetaminophen toxicity simulation
suite = OrganChipSuite.create_acetaminophen_toxicity()

# Run simulation (24 hours, toxic dose)
results = suite.run(duration=24.0, dt=0.1, dose=2000.0)

# Get summary
summary = suite.get_summary()
print(f"Max liver damage: {summary['liver']['max_damage']:.1%}")

# Export results
suite.export_results('results.csv', format='csv')
```

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   Organ-On-Chip Suite                           │
│                                                                 │
│  ┌───────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │   Molecular   │  │    Cellular    │  │      Organ       │  │
│  │    Models     │→ │     Models     │→ │     Models       │  │
│  │               │  │                │  │                  │  │
│  │ • Ligand-     │  │ • Immune       │  │ • Liver          │  │
│  │   Receptor    │  │   Signaling    │  │ • Heart          │  │
│  │               │  │ • Ion Channels │  │                  │  │
│  └───────────────┘  └────────────────┘  └──────────────────┘  │
│         ↓                  ↓                      ↓            │
│  ┌────────────────────────────────────────────────────────┐   │
│  │          Multiscale Coupling Layer                     │   │
│  │  • Signal routing                                      │   │
│  │  • Time scale synchronization                          │   │
│  │  • Adaptive sub-stepping                               │   │
│  └────────────────────────────────────────────────────────┘   │
│         ↓                                                      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │      Systemic Circulation (PBPK)                       │   │
│  │  • Blood, liver, heart, peripheral compartments        │   │
│  │  • Hepatic and renal clearance                         │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Module Structure

```
src/organ_chip/
├── molecular/          # Ligand-receptor binding
│   └── ligand_receptor.py
├── immune/            # Immune signaling
│   └── cytokine_signaling.py
├── liver/             # Hepatocyte model
│   └── hepatocyte.py
├── cardiac_enhanced/  # Cardiac electrophysiology with drug effects
│   └── drug_cardiac_model.py
├── circulation/       # Pharmacokinetics
│   └── pharmacokinetics.py
├── multiscale/        # Coupling infrastructure
│   └── coupling.py
└── orchestrator/      # High-level orchestration
    └── organ_chip_suite.py
```

## Core Models

### 1. Ligand-Receptor Binding (`molecular/ligand_receptor.py`)

Models ligand-receptor interactions using mass action kinetics with receptor internalization and recycling.

**Key Features:**
- Reversible binding (kon, koff)
- Receptor-mediated endocytosis
- Receptor recycling to surface
- Ligand and receptor degradation

**Equations:**
```
dL/dt = -kon*L*R + koff*LR + k_recycle*R_int - k_deg_L*L
dR/dt = -kon*L*R + koff*LR + k_synth - k_deg_R*R + k_recycle*R_int
dLR/dt = kon*L*R - koff*LR - k_int*LR
dR_int/dt = k_int*LR - k_recycle*R_int - k_deg_int*R_int
```

**Usage:**
```python
from organ_chip.molecular import create_cytokine_receptor

model = create_cytokine_receptor()
model.step(dt=1.0, external_ligand=10.0)  # Add 10 nM ligand
occupancy = model.get_occupancy()  # Get receptor occupancy
```

### 2. Immune Signaling (`immune/cytokine_signaling.py`)

Models cytokine network dynamics with macrophage polarization.

**Key Features:**
- Pro-inflammatory cytokines (IL-6, TNF-α)
- Anti-inflammatory cytokines (IL-10)
- Macrophage polarization (M0 → M1/M2)
- Positive and negative feedback

**Equations:**
```
dIL6/dt = k_IL6_prod * M1 - k_IL6_deg * IL6
dTNFa/dt = k_TNFa_prod * M1 - k_TNFa_deg * TNFa
dIL10/dt = k_IL10_prod * M2 - k_IL10_deg * IL10
dM1/dt = k_M1_act * (TNFa + IL6) * M0 - k_M1_deact * IL10 * M1 - k_M1_death * M1
```

**Usage:**
```python
from organ_chip.immune import CytokineSignalingModel

model = CytokineSignalingModel()
model.step(dt=1.0, external_stimulus={'damage': 10.0})
inflammatory_index = model.get_inflammatory_index()
```

### 3. Hepatocyte Model (`liver/hepatocyte.py`)

Comprehensive model of drug metabolism and hepatotoxicity.

**Key Features:**
- Phase I metabolism (CYP450)
- Phase II metabolism (conjugation)
- Glutathione (GSH) redox cycle
- ROS production and scavenging
- ATP dynamics
- Cell damage and viability

**Equations:**
```
Phase I:  dD/dt = -V_CYP * D / (K_CYP + D)
Phase II: dM/dt = V_CYP * D / (K_CYP + D) - V_conj * M / (K_conj + M)
GSH:      dGSH/dt = k_GSH_synth - k_GSH_ox * ROS * GSH - GSH_conj
ROS:      dROS/dt = k_ROS_prod * M - k_ROS_scav * GSH * ROS
ATP:      dATP/dt = k_ATP_prod * (1 - Damage) - k_ATP_cons
Damage:   dDamage/dt = k_damage * (ROS + M) - k_repair * Damage * ATP
```

**Usage:**
```python
from organ_chip.liver import create_acetaminophen_model

model = create_acetaminophen_model()
model.step(dt=0.1, drug_input=100.0)  # Add 100 μM drug
viability = model.get_viability()
gsh_ratio = model.get_GSH_GSSG_ratio()
```

### 4. Cardiac Model (`cardiac_enhanced/drug_cardiac_model.py`)

Enhanced cardiac electrophysiology with drug-induced ion channel block.

**Key Features:**
- Action potential dynamics (modified Hodgkin-Huxley)
- hERG (IKr) block → QT prolongation
- Nav1.5 (INa) block → conduction slowing
- Cav1.2 (ICa) block → reduced contractility
- Calcium handling and force generation

**Equations:**
```
Membrane: C_m * dV/dt = -(I_Na + I_Ca + I_K + I_leak) + I_stim
Currents: I_X = g_X * gates * (V - E_X) * (1 - block_X)
Block:    block_X = [Drug] / (IC50_X + [Drug])
Gating:   dx/dt = (x_inf(V) - x) / tau_x(V)
Calcium:  dCa_i/dt = -I_Ca / (2*F*V) + J_SR - k_uptake * Ca_i
Force:    F = k * Ca_i^n / (K^n + Ca_i^n)
```

**Usage:**
```python
from organ_chip.cardiac_enhanced import create_doxorubicin_cardiac_model

model = create_doxorubicin_cardiac_model()
model.step(dt=0.001, drug_conc=5.0, pacing=True)  # 5 μM drug, paced
force = model.get_force()
herg_block = model.get_state()['hERG_block']
```

### 5. Pharmacokinetics (`circulation/pharmacokinetics.py`)

Physiologically-based pharmacokinetic (PBPK) model.

**Key Features:**
- Multi-compartment distribution (blood, liver, heart, peripheral)
- Organ-specific blood flows and partition coefficients
- Hepatic metabolism
- Renal clearance

**Equations:**
```
Blood:    dC_blood/dt = (Q_organs * C_organs - Q_total * C_blood) / V_blood
                        - CL_renal * C_blood / V_blood + Dose(t) / V_blood
Liver:    dC_liver/dt = Q_liver * (C_blood - C_liver/K_liver) / V_liver
                        - CL_hepatic * C_liver / V_liver
Heart:    dC_heart/dt = Q_heart * (C_blood - C_heart/K_heart) / V_heart
Periph:   dC_periph/dt = Q_periph * (C_blood - C_periph/K_periph) / V_periph
```

**Usage:**
```python
from organ_chip.circulation import create_standard_drug_pk

model = create_standard_drug_pk()
model.step(dt=0.1, dose=1000.0)  # Bolus dose
c_max = model.state[0]  # Blood concentration
auc = model.history['AUC'][-1]
```

## Multiscale Coupling

### Coupling Mechanisms

The `MultiscaleCoupler` manages signal routing between models:

```python
from organ_chip.multiscale import MultiscaleCoupler

coupler = MultiscaleCoupler()

# Register models
coupler.register_model('pk', pk_model, time_scale=3600.0)  # Hour scale
coupler.register_model('liver', liver_model, time_scale=3600.0)
coupler.register_model('heart', heart_model, time_scale=0.001)  # ms scale

# Add coupling: PK → Liver
def pk_to_liver(pk_model, liver_model, dt):
    state = pk_model.get_state()
    return {'drug_input': state['C_liver']}

coupler.add_coupling('pk', 'liver', pk_to_liver)

# Step with adaptive sub-stepping
states = coupler.step(dt=0.1, adaptive=True)
```

### Predefined Couplings

The suite provides predefined coupling functions:

- `drug_circulation_to_organ`: PK → Organ drug concentration
- `organ_damage_to_immune`: Organ damage → Immune activation
- `immune_to_organ_feedback`: Inflammation → Organ damage
- `hepatic_clearance_to_pk`: Liver viability → PK clearance

## Drug Toxicity Scenarios

### Acetaminophen (APAP) Hepatotoxicity

```python
suite = OrganChipSuite.create_acetaminophen_toxicity()
results = suite.run(duration=48.0, dt=0.1, dose=2000.0)  # Toxic dose
summary = suite.get_summary()

print(f"Max damage: {summary['liver']['max_damage']:.1%}")
print(f"GSH/GSSG ratio: {summary['liver']['final_GSH_GSSG_ratio']:.2f}")
```

**Mechanism:**
1. APAP metabolized by CYP2E1 to NAPQI (toxic metabolite)
2. NAPQI depletes glutathione (GSH)
3. ROS accumulation causes oxidative stress
4. Hepatocellular damage and necrosis

### Doxorubicin Cardiotoxicity

```python
suite = OrganChipSuite.create_doxorubicin_cardiotoxicity()
results = suite.run(duration=72.0, dt=0.1, dose=500.0)  # Therapeutic dose
summary = suite.get_summary()

print(f"hERG block: {summary['heart']['max_hERG_block']:.1%}")
print(f"Force reduction: {1 - summary['heart']['final_force']:.1%}")
```

**Mechanism:**
1. Mitochondrial dysfunction
2. ROS generation
3. Calcium handling dysregulation
4. hERG channel block (QT prolongation)
5. Reduced contractility

## Running Demos

### Acetaminophen Toxicity Demo

```bash
python examples/organ_chip/demo_acetaminophen_toxicity.py
```

Output includes:
- Time course of drug concentration and liver damage
- GSH depletion dynamics
- Immune activation
- Summary statistics
- Clinical recommendations

### Doxorubicin Cardiotoxicity Demo

```bash
python examples/organ_chip/demo_doxorubicin_cardiotoxicity.py
```

Output includes:
- Cardiac drug exposure
- hERG block progression
- Contractility changes
- Multi-organ effects

### Multiscale Integration Demo

```bash
python examples/organ_chip/demo_multiscale_integration.py
```

Demonstrates:
- Signal propagation across scales
- Time scale analysis
- Coupling strength quantification
- Adaptive sub-stepping

## Testing

### Run Test Suite

```bash
# Run all organ chip tests
pytest tests/organ_chip/test_drug_toxicity.py -v

# Run specific test class
pytest tests/organ_chip/test_drug_toxicity.py::TestAcetaminophenToxicity -v

# Run with coverage
pytest tests/organ_chip/ --cov=src/organ_chip --cov-report=html
```

### Validation Tests

The test suite includes:

1. **Therapeutic vs. Toxic Doses**: Validates dose-response
2. **Mechanism Verification**: Confirms GSH depletion, hERG block
3. **Time Course Realism**: Checks physiological time scales
4. **Mass Balance**: Validates PK conservation
5. **Multi-Organ Crosstalk**: Tests organ-organ interactions

## Advanced Usage

### Custom Drug Configuration

```python
from organ_chip.orchestrator import OrganChipSuite, OrganChipConfig
from organ_chip.liver import HepatocyteModel
from organ_chip.cardiac_enhanced import DrugCardiacModel

# Create custom configuration
config = OrganChipConfig(
    include_molecular=True,
    include_immune=True,
    include_liver=True,
    include_heart=True,
    include_pk=True,
    drug_name='CustomDrug'
)

suite = OrganChipSuite(config)

# Customize liver model for specific drug
suite.liver_model = HepatocyteModel(
    V_CYP=200.0,        # High CYP activity
    K_CYP=75.0,         # Custom Km
    k_ROS_prod=0.15,    # High ROS production
)

# Customize cardiac model
suite.heart_model = DrugCardiacModel(
    IC50_hERG=2.0,      # Moderate hERG block
    IC50_Na=50.0,       # Weak Na+ block
)

# Run simulation
results = suite.run(duration=24.0, dt=0.1, dose=1000.0)
```

### Export and Visualization

```python
# Export to CSV
suite.export_results('results.csv', format='csv')

# Export to JSON
suite.export_results('results.json', format='json')

# Access raw data for custom plotting
import matplotlib.pyplot as plt

times = results['time']
damages = [s['Damage'] for s in results['liver']]
gshs = [s['GSH'] for s in results['liver']]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

ax1.plot(times, damages, 'r-', label='Damage')
ax1.set_ylabel('Liver Damage')
ax1.legend()

ax2.plot(times, gshs, 'g-', label='GSH')
ax2.set_xlabel('Time (h)')
ax2.set_ylabel('GSH (mM)')
ax2.legend()

plt.tight_layout()
plt.savefig('toxicity_time_course.png', dpi=300)
```

## References

### Ligand-Receptor Binding
- Lauffenburger & Linderman (1993) "Receptors: Models for Binding, Trafficking, and Signaling"

### Immune Signaling
- Vodovotz et al. (2008) "Evidence-based modeling of critical illness"
- Reynolds et al. (2006) "A reduced mathematical model of the acute inflammatory response"

### Hepatotoxicity
- Godoy et al. (2013) "Recent advances in 2D and 3D in vitro systems using primary hepatocytes"
- Schug et al. (2013) "Acetaminophen hepatotoxicity: molecular mechanisms"

### Cardiotoxicity
- Ten Tusscher et al. (2004) "A model for human ventricular tissue"
- Mirams et al. (2011) "Simulation of multiple ion channel block"
- Colatsky et al. (2016) "The Comprehensive in Vitro Proarrhythmia Assay (CiPA)"

### Pharmacokinetics
- Jones & Rowland-Yeo (2013) "Basic concepts in physiologically based pharmacokinetic modeling"
- Nestorov (2003) "Whole body pharmacokinetic models"

## License

[Your License Here]

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

## Contact

For questions or issues, please open an issue on GitHub.
