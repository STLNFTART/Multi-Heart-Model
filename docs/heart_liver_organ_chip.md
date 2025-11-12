# Heart-Liver Organ-on-Chip Digital Twin

## Overview

This is a comprehensive computational framework for simulating heart-liver interactions in an organ-on-chip platform. It integrates multiple biological scales—from molecular drug-receptor binding to systemic circulation—into a unified digital twin for drug screening and toxicity prediction.

## Architecture

### Multiscale Hierarchy

```
Molecular Scale
├── Ligand-Receptor Binding
│   ├── Drug-receptor kinetics (k_on, k_off)
│   ├── Receptor occupancy dynamics
│   └── Macro-scale feedback (stress, cytokines)
│
Cellular Scale
├── Immune Signaling
│   ├── Pro-inflammatory cytokines (TNF-α, IL-6)
│   ├── Anti-inflammatory/regulatory response
│   └── Damage signal integration
│
Organ Scale - Liver
├── Hepatocyte Population
│   ├── Viable/damaged/dead cell states
│   ├── ATP and GSH metabolism
│   └── Biomarkers (ALT, AST, LDH, albumin)
├── Drug Metabolism (CYP450)
│   ├── Phase I oxidation (CYP1A2, 2C9, 2C19, 2D6, 2E1, 3A4)
│   ├── Enzyme induction/inhibition
│   └── Michaelis-Menten kinetics
└── Hepatotoxicity
    ├── Mitochondrial dysfunction
    ├── Oxidative stress (ROS/GSH)
    ├── Cholestasis (bile stasis)
    ├── Immune activation
    └── Direct cytotoxicity
│
Organ Scale - Cardiac
├── Cardiomyocyte Model
│   ├── Electrophysiology (Van der Pol oscillator)
│   ├── Calcium dynamics
│   ├── Contractility (Ca-dependent force)
│   └── ATP metabolism
└── Cardiotoxicity
    ├── hERG K+ channel blockade (QT prolongation)
    ├── L-type Ca channel effects
    ├── Mitochondrial dysfunction
    ├── Oxidative damage
    └── Troponin release (cell death)
│
Systemic Scale
└── Circulation
    ├── Blood flow distribution (cardiac output)
    ├── Organ perfusion (liver, heart, brain, kidneys)
    ├── Drug pharmacokinetics (ADME)
    └── Tissue partition coefficients
```

### Bidirectional Coupling

```
    Molecular ↔ Cellular ↔ Organ ↔ Systemic

Examples:
- Drug → Receptor → Immune → Liver/Heart dysfunction → Altered circulation
- Stress → Autonomic → Heart rate → Cardiac output → Organ perfusion
- Hepatotoxicity → Metabolite accumulation → Cardiotoxicity
- Heart failure → Reduced perfusion → Liver congestion → Impaired metabolism
```

## Mathematical Framework

### Recursive Planck Operator (RPO)

Unified memory kernel for biological processes:

```
ż(t) = -λz(t) + β∫₀^∞ αe^(-ατ) z(t-τ) dτ + S(t)
```

Equivalent ODE pair (numerically stable):
```
ż = -λz + βm + S(t)
ṁ = α(z - m)
```

Where:
- `z`: Current state variable
- `m`: Exponentially weighted memory
- `λ`: Decay/forgetting rate
- `β`: Memory feedback strength
- `α`: Memory formation rate (1/α = memory timescale)
- `S(t)`: External stimulus

### Primal Logic Accumulation-Decay Dynamics

Every biological variable follows:

```
dx/dt = α(θ, state) - λ(state) · x
```

Where:
- `x`: State variable (drug concentration, cell viability, ATP, etc.)
- `α`: Accumulation/production term (context-dependent)
- `θ`: External input/stimulus
- `λ`: Decay/clearance/consumption rate

## Key Components

### 1. Ligand-Receptor Binding (`primal_logic/molecular/ligand_receptor.py`)

**Purpose**: Model drug-receptor interactions at the molecular scale.

**Equations**:
```
Ṙ(t) = k_on·L(t)·(R_T - R(t)) - k_off·R(t) + γ·F(t)
```

**Parameters**:
- `k_on`: Association rate constant (M⁻¹s⁻¹)
- `k_off`: Dissociation rate constant (s⁻¹)
- `R_T`: Total receptor pool
- `K_d = k_off/k_on`: Dissociation constant

**Example**:
```python
from primal_logic.molecular import LigandReceptor

lr = LigandReceptor()
lr.set_ligand_function(lambda t: 10.0 * np.exp(-0.5*t))
times, occupancy = lr.simulate(t_span=(0, 20), dt=0.01)
```

### 2. Immune Signaling (`primal_logic/cellular/immune_signaling.py`)

**Purpose**: Model cytokine dynamics and inflammatory response.

**Equations**:
```
İ_pro(t) = ρ·damage(t) - δ·I_pro(t) - α·I_anti(t)
İ_anti(t) = β·I_pro(t) - δ_anti·I_anti(t)
```

**Features**:
- Pro-inflammatory (TNF-α, IL-6) and anti-inflammatory balance
- Damage signal integration
- Modulation of organ function (λ_b, λ_h)

**Example**:
```python
from primal_logic.cellular import ImmuneSignaling, CytokineProfiles

immune = CytokineProfiles.acute_inflammatory()
immune.set_damage_signal(lambda t: receptor_occupancy)
times, pro, anti = immune.simulate(t_span=(0, 100), dt=0.01)
```

### 3. Liver Subsystem (`primal_logic/organ/liver/`)

**Components**:

a) **Hepatocyte Population** (`hepatocyte.py`)
   - Viable, damaged, dead cell states
   - ATP and GSH metabolism
   - Biomarkers: ALT, AST, LDH, albumin

b) **Drug Metabolism** (`metabolism.py`)
   - CYP450 enzyme system (1A2, 2C9, 2C19, 2D6, 2E1, 3A4)
   - Michaelis-Menten kinetics: `v = Vmax·[S]/(Km + [S])`
   - Enzyme induction (Hill equation)
   - Competitive inhibition

c) **Hepatotoxicity** (`toxicity.py`)
   - 5 mechanisms: mitochondrial, oxidative, cholestatic, immune, direct
   - Weighted toxicity score
   - Cumulative damage tracking

**Example**:
```python
from primal_logic.organ.liver import HepatocytePopulation, LiverMetabolism

hep = HepatocytePopulation()
hep.set_toxicity_function(lambda t: drug_concentration * 0.01)
times, states = hep.simulate(t_span=(0, 100), dt=0.1)

biomarkers = hep.get_biomarkers()
print(f"ALT: {biomarkers['ALT']}, Viability: {biomarkers['Viability']}")
```

### 4. Cardiac Subsystem (`primal_logic/organ/cardiac/`)

**Components**:

a) **Cardiomyocyte Model** (`cardiomyocyte.py`)
   - Van der Pol oscillator (electrophysiology)
   - Calcium dynamics (EC coupling)
   - Contractility: `F = Fmax·[Ca]^n/(EC50^n + [Ca]^n)`
   - Drug effects: hERG, Ca/Na channels, mitochondria

b) **Cardiotoxicity** (`toxicity.py`)
   - hERG K+ channel blockade (QT prolongation)
   - Ca dysregulation
   - Mitochondrial dysfunction
   - Troponin/BNP biomarkers

**Example**:
```python
from primal_logic.organ.cardiac import CardiomyocyteModel, CardiacToxicity

cardio = CardiomyocyteModel()
cardio.set_drug_effect(lambda t: {'hERG_block': 0.5})
times, states = cardio.simulate(t_span=(0, 10), dt=0.01)

metrics = cardio.get_cardiac_metrics(times, states)
print(f"HR: {metrics['heart_rate']} BPM, APD: {metrics['APD']} s")
```

### 5. Systemic Circulation (`primal_logic/systemic/circulation.py`)

**Purpose**: Blood flow distribution and pharmacokinetics.

**Compartments**:
- Arterial
- Venous
- Liver
- Heart
- Brain
- Other tissues

**Equations**: Compartmental PK model with organ-specific flows.

**Features**:
- Cardiac output modulation (heart failure effects)
- Hepatic metabolism integration
- Renal clearance
- Tissue partition coefficients (Kp)
- PK metrics: Cmax, Tmax, AUC, T1/2

**Example**:
```python
from primal_logic.systemic import SystemicCirculation

circ = SystemicCirculation()
circ.set_drug_input(lambda t: 100.0 if t < 0.1 else 0.0)
circ.set_metabolism_function(lambda C_liver, t: 0.1 * C_liver)
times, states = circ.simulate(t_span=(0, 24), dt=0.01)

pk_metrics = circ.get_pk_metrics(times, states)
print(f"Cmax: {pk_metrics['Cmax']} μM, T1/2: {pk_metrics['T_half']} hr")
```

### 6. Multiscale Integration (`primal_logic/integration/`)

**a) Multiscale Coupling** (`multiscale_coupling.py`)

Orchestrates bidirectional feedback across all scales:

```python
from primal_logic.integration import MultiscaleCoupling

coupling = MultiscaleCoupling()
coupling.configure_drug_pathway(
    drug_name="dofetilide",
    cyp_isoform="CYP3A4",
    hERG_IC50=5.0
)
coupling.set_drug_dosing(lambda t: 500.0 if t < 0.05 else 0.0)
times, results = coupling.simulate(t_span=(0, 24), dt=0.1)
```

**b) Organ Chip Suite** (`organ_chip_suite.py`)

Complete drug screening platform:

```python
from primal_logic.integration import OrganChipSuite

suite = OrganChipSuite()

# Run drug screen
times, results = suite.run_drug_screen(
    drug_name="doxorubicin",
    dose=50.0,  # mg
    duration=48.0,
    dosing_schedule="bolus"
)

# Assess toxicity
report = suite.assess_toxicity(times, results)
print(suite.generate_report(report))
```

## Validation Drugs

### Pre-configured Drug Library

1. **Acetaminophen** (Hepatotoxic)
   - CYP2E1 metabolism
   - Dose-dependent liver injury
   - GSH depletion, NAPQI metabolite
   - Therapeutic: 325-1000 mg
   - Toxic: >4000 mg/day

2. **Doxorubicin** (Dual Toxicity)
   - CYP3A4 metabolism
   - Cardiotoxicity: mitochondrial damage, oxidative stress
   - Hepatotoxicity: metabolite accumulation
   - Clinical dose: 50-75 mg/m²

3. **Dofetilide** (Cardiotoxic)
   - Potent hERG K+ channel blocker
   - QT prolongation, Torsades de Pointes risk
   - IC50: 2-5 μM
   - Therapeutic: 0.5 mg

4. **Amiodarone** (Dual Toxicity)
   - Hepatotoxicity and cardiotoxicity
   - Long half-life (~58 days)
   - CYP3A4 metabolism
   - Loading: 400-800 mg/day

5. **Aspirin** (Reference Safe)
   - CYP2C9 metabolism
   - Minimal toxicity at therapeutic doses
   - Therapeutic: 75-325 mg/day

## Output Metrics

### Liver Biomarkers
- **ALT** (Alanine Aminotransferase): Liver damage
- **AST** (Aspartate Aminotransferase): Cell death
- **LDH** (Lactate Dehydrogenase): Necrosis
- **Albumin**: Synthetic function
- **Bilirubin**: Bile flow
- **GSH** (Glutathione): Antioxidant capacity
- **ATP**: Energy state

### Cardiac Biomarkers
- **Heart Rate**: Beats per minute
- **APD** (Action Potential Duration): QT interval proxy
- **QTc**: Corrected QT interval
- **Contractility**: Force generation
- **Troponin**: Myocyte damage
- **BNP** (Brain Natriuretic Peptide): Heart failure
- **ATP**: Myocardial energy

### Pharmacokinetic Metrics
- **Cmax**: Peak plasma concentration
- **Tmax**: Time to peak concentration
- **AUC**: Area under curve (exposure)
- **T1/2**: Elimination half-life
- **Clearance**: Metabolic rate
- **V_d**: Volume of distribution

### Toxicity Scores
- **Hepatotoxicity Score**: 0-2+ (Weighted sum of 5 mechanisms)
- **Cardiotoxicity Score**: 0-2+ (Weighted sum of 5 mechanisms)
- **Overall Severity**: Safe, Low, Moderate, High, Severe

## Applications

1. **Pre-clinical Drug Screening**
   - Toxicity prediction before animal studies
   - Dose optimization
   - Safety margin determination

2. **Drug-Drug Interaction Prediction**
   - CYP450 inhibition/induction
   - Synergistic toxicity
   - Pharmacokinetic changes

3. **Personalized Medicine**
   - Patient-specific parameters (CYP polymorphisms)
   - Disease state effects (heart failure, liver disease)
   - Dose adjustment recommendations

4. **Clinical Trial Design**
   - Biomarker selection
   - Monitoring strategies
   - Safety endpoint definition

5. **Regulatory Submissions**
   - Mechanistic toxicity assessment
   - Risk-benefit analysis
   - Label warnings

## References

### Mathematical Framework
- Lightfoot, D. (2025). "Recursive Planck Operator: Unified Memory Kernel for Biological Systems"
- Lightfoot, D. (2025). "Primal Logic: α - λx Dynamics in Physiology"

### Organ-on-Chip Validation
- Zhang et al. (2018). "Multiorgan chip for recapitulating organ interactions" *Lab Chip*
- Skardal et al. (2017). "Multi-tissue interactions in an integrated three-tissue organ-on-a-chip platform" *Sci Rep*

### Hepatotoxicity
- Weaver et al. (2020). "Managing the challenge of drug-induced liver injury" *Toxicol Sci*
- Yuan & Kaplowitz (2013). "Mechanisms of drug-induced liver injury" *Clin Liver Dis*

### Cardiotoxicity
- Gintant et al. (2016). "Evolution of strategies to improve preclinical cardiac safety testing" *Nat Rev Drug Discov*
- Redfern et al. (2003). "Relationships between preclinical cardiac electrophysiology, clinical QT interval prolongation and torsade de pointes" *J Pharmacol Toxicol Methods*
