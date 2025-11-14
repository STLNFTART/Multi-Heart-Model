# Organ Chip Suite Architecture

## Overview

The Organ Chip Suite is a comprehensive physiologically-based pharmacokinetic (PBPK) and pharmacodynamic (PD) modeling platform for multi-organ drug toxicity screening. It integrates mechanistic models of:

- **Cardiac organ chip**: Electrophysiology and cardiotoxicity
- **Liver organ chip**: Drug metabolism and hepatotoxicity
- **Immune system**: Cytokine signaling and inflammation
- **Systemic circulation**: PBPK and organ-organ coupling
- **Multiscale integration**: Temporal and spatial coupling

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORGAN CHIP SUITE ORCHESTRATOR                │
│                     (orchestrator.py)                           │
└──────────────┬──────────────────────────────────┬───────────────┘
               │                                  │
               v                                  v
    ┌──────────────────────┐          ┌──────────────────────┐
    │  MULTISCALE COUPLING │          │  SYSTEMIC CIRCULATION│
    │   (multiscale/)      │◄────────►│     (circulation/)   │
    └──────────┬───────────┘          └──────────┬───────────┘
               │                                  │
               v                                  │
    ┌──────────────────────────────────────────┐  │
    │      ORGAN MODELS (coupled)              │  │
    ├──────────────────────────────────────────┤  │
    │  ┌────────────┐  ┌────────────┐         │  │
    │  │  CARDIAC   │  │   LIVER    │         │◄─┘
    │  │  (cardiac/)│  │  (liver/)  │         │
    │  └────────────┘  └────────────┘         │
    │  ┌────────────┐  ┌────────────┐         │
    │  │   IMMUNE   │  │  LIGAND-   │         │
    │  │  (immune/) │  │  RECEPTOR  │         │
    │  └────────────┘  └────────────┘         │
    └──────────────────────────────────────────┘
```

## Module Descriptions

### 1. Ligand-Receptor Binding (`ligand_receptor/`)

**Purpose**: Models receptor-mediated drug effects and target engagement.

**Key Features**:
- Receptor occupancy dynamics
- Competitive and non-competitive inhibition
- Receptor desensitization and trafficking
- Target-mediated drug disposition (TMDD)

**Main Classes**:
- `LigandReceptorBinding`: Basic binding kinetics
- `CompetitiveInhibition`: Competition between ligands
- `ReceptorDynamics`: Extended model with desensitization

**State Variables**:
- `L`: Free ligand concentration (nM)
- `R`: Free receptor concentration (nM)
- `LR`: Ligand-receptor complex (nM)
- `Rint`: Internalized complex (nM)

**Equations**:
```
dL/dt = -kon·L·R + koff·LR
dR/dt = ksyn - kdeg·R - kon·L·R + koff·LR
dLR/dt = kon·L·R - koff·LR - kint·LR
dRint/dt = kint·LR - kdeg·Rint
```

---

### 2. Immune System (`immune/`)

**Purpose**: Models inflammatory responses and cytokine signaling.

**Key Features**:
- Pro-inflammatory cascade (TNF-α, IL-1β, IL-6)
- Anti-inflammatory response (IL-10, TGF-β)
- Acute phase response
- Drug-induced immunotoxicity

**Main Classes**:
- `CytokineNetwork`: Mechanistic cytokine interactions
- `InflammatoryResponse`: Acute inflammation dynamics

**State Variables** (all in pg/mL):
- `TNFa`: Tumor necrosis factor alpha
- `IL1b`: Interleukin-1 beta
- `IL6`: Interleukin-6
- `IL10`: Interleukin-10 (anti-inflammatory)
- `TGFb`: Transforming growth factor beta

**Key Interactions**:
- TNF-α → amplifies IL-1β and IL-6
- IL-1β → amplifies IL-6
- IL-10 → inhibits TNF-α and IL-1β
- TGF-β → inhibits TNF-α

---

### 3. Liver Organ Chip (`liver/`)

**Purpose**: Models hepatic drug metabolism and toxicity.

**Key Features**:
- Phase I metabolism (CYP450)
- Phase II conjugation
- Reactive metabolite formation
- Glutathione depletion
- Hepatocellular injury (ALT/AST release)
- Mitochondrial dysfunction

**Main Classes**:
- `LiverMetabolism`: Drug metabolism pathways
- `LiverToxicity`: Hepatotoxicity mechanisms
- `Hepatocyte`: Integrated hepatocyte model

**State Variables**:

*Metabolism*:
- `Drug`: Parent drug (μM)
- `Metabolite`: Phase I metabolite (μM)
- `Reactive`: Reactive metabolite (μM)
- `Conjugate`: Phase II product (μM)

*Toxicity*:
- `GSH`: Glutathione (mM)
- `ATP`: Cellular ATP (mM)
- `ROS`: Reactive oxygen species (mM)
- `Cell_viability`: Fraction [0,1]
- `ALT`, `AST`: Liver enzymes (U/L)

**Metabolic Pathways**:
```
Drug → [Phase I] → Metabolite + Reactive Metabolite
               ↓                    ↓
         [Phase II]           [GSH conjugation]
               ↓                    ↓
          Conjugate → Excretion
```

---

### 4. Cardiac Organ Chip (`cardiac/`)

**Purpose**: Models cardiac electrophysiology and cardiotoxicity.

**Key Features**:
- Ion channel dynamics (Na+, Ca2+, K+, hERG)
- Action potential generation
- Drug-induced QT prolongation
- Contractility and calcium handling
- Biomarker release (troponin, BNP)

**Main Classes**:
- `IonChannelDynamics`: Voltage-gated channels
- `ContractilityModel`: Calcium-force coupling
- `CardiotoxicityModel`: Toxicity assessment
- `CardiacCell`: Integrated cardiac model

**State Variables**:
- `V`: Membrane potential (mV)
- `m, h`: Na+ channel gates
- `d, f`: Ca2+ channel gates
- `xr`: Kr (hERG) channel gate
- `Ca_i`: Intracellular Ca2+ (μM)
- `Force`: Contractile force (mN/mm²)
- `Troponin`: Troponin I (ng/mL)
- `BNP`: B-type natriuretic peptide (pg/mL)

**Ion Currents**:
```
INa   = gNa · m³ · h · (V - ENa)           [Fast Na+]
ICaL  = gCaL · d · f · (V - ECa)           [L-type Ca2+]
IKr   = gKr · xr · (V - EK)                [hERG/IKr]
IK1   = gK1 · f(V) · (V - EK)              [Inward rectifier]
```

**Drug Effects**:
- hERG inhibition → QT prolongation → Torsades de Pointes risk
- Ca2+ channel block → negative inotropy
- Mitochondrial toxicity → troponin release

---

### 5. Systemic Circulation (`circulation/`)

**Purpose**: Models drug distribution via blood flow and PBPK.

**Key Features**:
- Multi-organ PBPK model
- Organ blood flow distribution
- Tissue partitioning (Kp values)
- Hepatic and renal clearance
- AUC calculations

**Main Classes**:
- `SystemicCirculation`: Blood flow dynamics
- `MultiOrganPBPK`: Full PBPK integration
- `CompartmentModel`: Classical PK models

**Organs Modeled**:
- Plasma (central compartment)
- Liver (high clearance)
- Heart (target organ)
- Kidney (renal elimination)
- Muscle (distribution)
- Adipose (lipophilic storage)
- Brain (CNS effects)
- Gut (oral absorption)

**Mass Balance**:
```
dA_organ/dt = Q_organ · (C_plasma - C_organ/Kp)

where:
  A_organ = Amount in organ (mg)
  Q_organ = Blood flow (L/h)
  C_plasma = Plasma concentration (mg/L)
  Kp = Tissue:plasma partition coefficient
```

---

### 6. Multiscale Coupling (`multiscale/`)

**Purpose**: Integrates all organ systems with feedback loops.

**Key Features**:
- Circulation-mediated substance transport
- Liver metabolite → cardiac toxicity
- Cardiac output → hepatic perfusion
- Cytokine effects on organ function
- Temporal scale integration

**Main Classes**:
- `MultiscaleCoupling`: Top-level integration
- `OrganInteractions`: Inter-organ signaling

**Coupling Mechanisms**:

1. **Liver → Cardiac**:
   - Reactive metabolites → hERG inhibition
   - Metabolites → contractility reduction
   - Metabolites → troponin release

2. **Cardiac → Liver**:
   - Reduced cardiac output → hepatic hypoperfusion
   - Hypoperfusion → reduced metabolism

3. **Immune → Organs**:
   - TNF-α → cardiac dysfunction
   - IL-6 → altered metabolism
   - Cytokines → organ stress

4. **Circulation-Mediated**:
   - Substance transport between organs
   - Proportional to blood flow

---

## Orchestrator (`orchestrator.py`)

**Purpose**: Top-level system integration and user interface.

**Main Class**: `OrganChipSuite`

**Key Methods**:

1. `initialize_state()`: Set up initial conditions
2. `simulate_drug_exposure()`: Run drug study
3. `assess_toxicity()`: Multi-organ toxicity assessment
4. `export_results()`: Data export to JSON
5. `run_complete_study()`: End-to-end workflow

**Workflow**:
```
1. Initialize all organ models
2. Link models via MultiscaleCoupling
3. Set drug parameters (IC50, metabolism, etc.)
4. Run simulation with specified dose/duration
5. Extract time series data
6. Assess toxicity for each organ
7. Generate overall toxicity score
8. Export results
```

---

## Data Flow

```
Drug Dose (mg)
      │
      v
┌─────────────────┐
│ PBPK Circulation│
│  Distribution   │
└────────┬────────┘
         │
    ┌────┴─────┬─────────┬────────┐
    v          v         v        v
┌───────┐  ┌──────┐  ┌──────┐  ┌──────┐
│ Liver │  │Heart │  │Brain │  │Other │
│ Cmet  │  │ Chrt │  │ Cbrn │  │ ...  │
└───┬───┘  └──┬───┘  └──────┘  └──────┘
    │         │
    v         │
Reactive      │
Metabolite────┘
    │
    v
Cardiac Toxicity
```

---

## Temporal Scales

The system handles multiple time scales:

| Process | Time Scale | Integration |
|---------|-----------|-------------|
| Cardiac AP | 100-500 ms | Sub-stepping |
| Calcium transient | 10-100 ms | Sub-stepping |
| Drug metabolism | Minutes-hours | Main loop |
| Cytokine signaling | Hours | Main loop |
| PBPK distribution | Minutes-hours | Main loop |
| Tissue injury | Hours-days | Main loop |

---

## Output Metrics

### Toxicity Scores

**Overall Toxicity Score** (0-1):
```
Score = 0.4·Liver + 0.4·Cardiac + 0.2·Immune
```

**Severity Classification**:
- < 0.2: None - Safe
- 0.2-0.4: Mild - Monitor
- 0.4-0.6: Moderate - Caution
- 0.6-0.8: Severe - High Risk
- > 0.8: Critical - Contraindicated

### Biomarkers

**Hepatotoxicity**:
- ALT, AST elevation (> 3x ULN)
- GSH depletion (< 20% baseline)
- Cell viability (< 80%)

**Cardiotoxicity**:
- QTc prolongation (> 30 ms)
- Troponin elevation (> 2x baseline)
- Force reduction (> 30%)

**Inflammation**:
- Inflammatory Index (Pro/Anti ratio)
- TNF-α fold change
- IL-6 fold change

---

## Usage Example

```python
from organchip.orchestrator import create_default_organ_chip_suite

# Create suite
suite = create_default_organ_chip_suite()

# Configure for specific drug
suite.cardiac.ion_channels.IC50_hERG = 1.0  # μM
suite.liver.metabolism.frac_phase1_to_reactive = 0.3

# Run toxicity study
trajectory, toxicity = suite.run_complete_study(
    dose_mg=200.0,
    duration_hours=48.0,
    export_file="results.json"
)

# Assess results
print(f"Overall Severity: {toxicity['overall_severity']}")
print(f"Liver: {toxicity['liver']['severity']}")
print(f"Cardiac: {toxicity['cardiac']['severity']}")
```

---

## References

1. **PBPK Modeling**: Jamei et al. (2009) - Simcyp population-based ADME simulator
2. **Cardiac Electrophysiology**: ten Tusscher et al. (2006) - Ventricular cell model
3. **Hepatotoxicity**: Howell et al. (2012) - DILI prediction
4. **Cytokine Networks**: Vodovotz et al. (2008) - Inflammatory dynamics
5. **Multi-organ toxicity**: Ewart et al. (2018) - CiPA cardiotoxicity initiative

---

## Future Enhancements

1. **Additional Organs**:
   - Kidney (nephrotoxicity)
   - Lung (pulmonary toxicity)
   - GI tract (absorption, gut microbiome)

2. **Advanced Features**:
   - Drug-drug interactions
   - Population variability
   - Time-dependent inhibition
   - Active metabolites

3. **Validation**:
   - Clinical trial data comparison
   - FDA-approved drug database
   - Adverse event correlation

4. **Machine Learning**:
   - Toxicity prediction models
   - Parameter optimization
   - Uncertainty quantification
