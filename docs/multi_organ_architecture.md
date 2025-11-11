# Multi-Organ Digital Twin Architecture

## Overview

The Multi-Organ Digital Twin system extends the original Heart-Brain Coupling Model (HBCM) to create a comprehensive, physiologically-based platform for drug toxicity testing and systems pharmacology. The architecture integrates multiple organ-on-chip systems with systemic circulation, immune response, and advanced receptor-protein-organ (RPO) dynamics.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MULTI-ORGAN DIGITAL TWIN                         │
│                      Orchestrator Layer                             │
└────────────────────┬────────────────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ▼               ▼               ▼
┌─────────┐   ┌─────────────┐   ┌──────────┐
│ HEART   │   │ LIVER       │   │ BRAIN    │
│ CHIP    │   │ CHIP        │   │ (HBCM)   │
└────┬────┘   └──────┬──────┘   └─────┬────┘
     │               │                 │
     └───────────────┼─────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌─────────────────┐
│   SYSTEMIC       │    │  IMMUNE SYSTEM  │
│  CIRCULATION     │◄───┤  & INFLAMMATION │
└──────────────────┘    └─────────────────┘
         │
         │ Drug Distribution
         │ PK/PD Modeling
         │
    ┌────┴────┐
    │  DRUG   │
    │ LIBRARY │
    └─────────┘
```

## Core Components

### 1. RPO (Receptor-Protein-Organ) Framework

**File:** `src/organ_chips/rpo_organ_chip.py`

The RPO framework provides the foundational cellular and molecular dynamics:

- **Receptors:** Ion channels, GPCRs, nuclear receptors, tyrosine kinases
- **Ligands:** Drugs, metabolites, signaling molecules
- **Signal Transduction:** Second messengers, kinase cascades, transcription factors
- **Protein Expression:** mRNA and protein dynamics with regulation
- **Cellular Stress:** Oxidative stress, mitochondrial dysfunction, DNA damage
- **Cell Populations:** Generic cell population with metabolic state

**Key Classes:**
```python
Receptor(name, receptor_type, density, k_on, k_off)
Ligand(name, concentration, molecular_weight, clearance_rate)
SignalTransduction(pathway_name, receptors, amplification)
CellPopulation(cell_type, cell_count, receptors, signaling, proteins)
OrganChip(organ_name, cell_populations)
```

**Drug-Receptor Interactions:**
- Hill equation for dose-response
- Competitive inhibition
- Allosteric modulation
- Receptor occupancy dynamics

### 2. Heart-on-Chip

**File:** `src/organ_chips/heart_chip.py`

Comprehensive cardiac model with:

**Electrophysiology:**
- Action potential generation (phases 0-4)
- Ion channels: Na+, Ca2+, K+ (voltage-gated)
- QT interval calculation
- Arrhythmia detection

**Calcium Dynamics:**
- L-type Ca2+ channels
- Ca2+-induced Ca2+ release (CICR)
- Sarcoplasmic reticulum (SR) dynamics
- SERCA pump, NCX, PMCA

**Contractility:**
- Excitation-contraction coupling
- Troponin C binding
- Force generation

**Biomarkers:**
- Troponin I (myocardial injury)
- CK-MB (cell death)
- BNP (cardiac stress)

**Integration:**
- Van der Pol oscillator (from existing HBCM)
- Beta-adrenergic and muscarinic receptors
- Heart rate variability

**Cardiotoxicity Models:**
```python
CardiacToxicity.doxorubicin_toxicity(heart_chip, dose, duration)
CardiacToxicity.qt_prolonging_drug(heart_chip, drug, herg_ic50, duration)
```

### 3. Liver-on-Chip

**File:** `src/organ_chips/liver_chip.py`

Hepatocyte metabolism and liver function:

**Drug Metabolism:**
- **Phase I:** CYP450 enzymes (CYP3A4, CYP2D6, CYP2C9, CYP1A2)
  - Michaelis-Menten kinetics
  - ROS production
  - Reactive metabolite formation
- **Phase II:** Conjugation enzymes (UGT, GST, SULT)
  - Glucuronidation
  - Glutathione conjugation
  - Sulfation

**Liver Function:**
- Bile acid synthesis and transport
- Albumin synthesis
- Clotting factor production
- Glucose metabolism

**Liver Function Tests (LFTs):**
- ALT, AST (hepatocyte damage)
- ALP (cholestasis)
- Bilirubin (conjugation/excretion)

**Hepatotoxicity Models:**
```python
LiverToxicity.acetaminophen_toxicity(liver_chip, dose, duration)
LiverToxicity.alcohol_toxicity(liver_chip, concentration, duration)
```

**DILI Classification:**
- Hepatocellular (ALT predominant)
- Cholestatic (ALP predominant)
- Mixed pattern
- Severity grading (mild, moderate, severe)

### 4. Systemic Circulation

**File:** `src/organ_chips/circulation.py`

Physiologically-based pharmacokinetic (PBPK) modeling:

**Blood Compartments:**
- Arterial (oxygenated)
- Venous (deoxygenated)
- Organ-specific perfusion

**Organ Perfusion:**
```
Organ          Blood Flow    % Cardiac Output
-----------------------------------------------
Liver          1500 mL/min   25%
Heart          250 mL/min    5%
Kidney         1200 mL/min   24%
Brain          750 mL/min    15%
Muscle         750 mL/min    15%
```

**Drug Distribution:**
- Multi-compartment PK
- Tissue-blood partitioning
- First-pass metabolism
- Protein binding

**Hemodynamics:**
- Cardiac output
- Mean arterial pressure
- Systemic vascular resistance

**PK Analysis Tools:**
```python
PharmacokineticsModel.calculate_auc(concentrations, times)
PharmacokineticsModel.calculate_cmax_tmax(concentrations, times)
PharmacokineticsModel.calculate_half_life(concentrations, times)
```

### 5. Immune System

**File:** `src/organ_chips/immune_system.py`

Systemic inflammatory response:

**Cytokine Network:**
- Pro-inflammatory: TNF-α, IL-1β, IL-6, IL-8
- Anti-inflammatory: IL-10, IL-4, TGF-β
- Chemokines: MCP-1, CCL5
- Acute phase proteins: CRP, SAA

**Immune Cells:**
- Neutrophils, monocytes, macrophages
- T cells (CD4+, CD8+), B cells, NK cells
- Activation states (M1/M2 polarization)

**SIRS/Sepsis Assessment:**
- SIRS criteria (0-4)
- Inflammation score
- Cytokine storm detection

**Integration:**
- Organ damage signals trigger immune response
- Cytokines modulate organ function
- Immunopathology (neutrophil-mediated tissue damage)

### 6. Digital Twin Orchestrator

**File:** `src/organ_chips/digital_twin.py`

Master controller for multi-organ simulations:

**Simulation Configuration:**
```python
SimulationConfig(
    duration=24.0,      # hours
    dt=0.01,            # seconds
    drug_name="...",
    dose_mg=100.0,
    route="IV",         # IV, PO, IM
    enable_heart=True,
    enable_liver=True,
    enable_immune=True
)
```

**Core Functions:**
```python
twin = MultiOrganDigitalTwin(config)
twin.administer_drug(drug, dose, route)
time_points = twin.simulate(drug)
toxicity = twin.assess_toxicity()
twin.export_results("output.json")
twin.export_csv("output.csv")
```

**Toxicity Assessment:**
- Overall safety classification
- Organ-specific toxicity
- Biomarker analysis
- Clinical-grade reporting

## Integration with Existing HBCM

The new architecture seamlessly integrates with the existing Heart-Brain Coupling Model:

```python
# Existing HBCM components
from src.neural import FitzHughNagumo
from src.cardiac import VanDerPolOscillator
from src.coupling import HeartBrainCouplingModel, CouplingParameters

# New multi-organ components
from src.organ_chips import MultiOrganDigitalTwin, HeartChip

# Integration in digital twin
hbcm = HeartBrainCouplingModel(
    neural_model=FitzHughNagumo(),
    cardiac_model=VanDerPolOscillator(),
    coupling=CouplingParameters(
        neural_to_cardiac_gain=0.5,
        cardiac_to_neural_gain=0.3
    )
)

# Heart chip uses Van der Pol oscillator internally
heart_chip.cardiomyocytes.oscillator = VanDerPolOscillator()
```

**Immune-Brain Axis:**
```python
ImmuneSignalingBridge.immune_to_neural_signal(immune_response)
ImmuneSignalingBridge.immune_to_cardiac_signal(immune_response)
```

## Data Flow

```
1. Drug Administration
   ↓
2. Circulation (Distribution)
   ↓
3. Organ Uptake
   ├→ Heart: Receptor binding, ion channel effects
   ├→ Liver: Phase I/II metabolism
   └→ Brain: Neural modulation (via HBCM)
   ↓
4. Cellular Effects
   ├→ Signal transduction
   ├→ Protein expression changes
   ├→ Metabolic alterations
   └→ Cellular stress
   ↓
5. Organ-Level Responses
   ├→ Heart: Contractility, rhythm, biomarkers
   ├→ Liver: LFTs, synthetic function
   └→ Immune: Cytokine release
   ↓
6. Systemic Effects
   ├→ Hemodynamics
   ├→ Inflammatory response
   └→ Inter-organ crosstalk
   ↓
7. Toxicity Assessment
   └→ Clinical decision support
```

## Validation Drugs

The system is validated against known toxicological profiles:

| Drug | Primary Target | Mechanism | Expected Outcome |
|------|---------------|-----------|------------------|
| Doxorubicin | Heart | Mitochondrial damage, ROS | Dose-dependent cardiomyopathy |
| Acetaminophen | Liver | NAPQI → GSH depletion | Hepatocellular necrosis |
| Sotalol | Heart | hERG block | QT prolongation, TdP risk |
| Amiodarone | Multi-organ | Phospholipidosis | Heart + liver toxicity |
| Isoniazid | Liver | Reactive metabolites | DILI |
| Cisplatin | Kidney | DNA damage | Nephrotoxicity |

## Usage Examples

### Basic Simulation

```python
from src.organ_chips import MultiOrganDigitalTwin, SimulationConfig, Ligand

# Configure
config = SimulationConfig(
    duration=24.0,
    drug_name="test_drug",
    dose_mg=100.0,
    route="IV"
)

# Create twin
twin = MultiOrganDigitalTwin(config)

# Create drug
drug = Ligand(
    name="test_drug",
    molecular_weight=400.0,
    clearance_rate=0.2
)

# Run simulation
results = twin.simulate(drug)

# Assess toxicity
toxicity = twin.assess_toxicity()
print(toxicity['overall_safety'])

# Export
twin.export_results("results.json")
```

### Cardiotoxicity Testing

```python
from src.organ_chips import HeartChip, CardiacToxicity

heart = HeartChip()
results = CardiacToxicity.doxorubicin_toxicity(
    heart_chip=heart,
    dose_mg_m2=300.0,
    duration_hours=6.0
)

# Analyze cardiac function over time
for state in results:
    print(f"t={state['time']:.1f}h: "
          f"EF={state['cardiac_function']['ejection_fraction']:.3f}, "
          f"Troponin={state['biomarkers']['troponin_I']:.3f}")
```

### Hepatotoxicity Testing

```python
from src.organ_chips import LiverChip, LiverToxicity

liver = LiverChip()
results = LiverToxicity.acetaminophen_toxicity(
    liver_chip=liver,
    dose_mg_kg=200.0,
    duration_hours=8.0
)

# Assess liver injury
assessment = liver.assess_hepatotoxicity()
print(f"Injury pattern: {assessment['injury_pattern']}")
print(f"Severity: {assessment['severity']}")
print(f"ALT: {assessment['ALT_fold_elevation']:.1f}x elevated")
```

## Output Formats

### JSON Output
```json
{
  "config": { ... },
  "time_points": [
    {
      "time": 0.0,
      "drug_concentration_arterial": 50.0,
      "heart_viability": 1.0,
      "liver_viability": 1.0,
      "troponin_i": 0.01,
      "alt": 20.0,
      ...
    }
  ],
  "toxicity_assessment": {
    "overall_safety": "Safe",
    "cardiac_toxicity": { ... },
    "hepatotoxicity": { ... }
  },
  "pharmacokinetics": {
    "AUC": 850.5,
    "Cmax": 52.3,
    "Tmax": 0.5,
    "half_life": 4.2
  }
}
```

### CSV Output
```csv
time,drug_concentration_arterial,heart_rate,ejection_fraction,troponin_i,alt,ast,il6,...
0.0,50.0,70.0,0.60,0.01,20.0,25.0,0.0,...
60.0,45.2,71.5,0.59,0.01,20.5,25.2,2.1,...
...
```

## Performance Considerations

- **Time step:** 0.01s provides balance between accuracy and speed
- **Output interval:** Save every 60-300s to manage data volume
- **Simulation duration:**
  - Acute toxicity: 2-8 hours
  - PK studies: 24-48 hours
  - Chronic toxicity: Days (with larger dt)

## Future Extensions

1. **Additional Organs:**
   - Kidney (glomerular filtration, tubular secretion)
   - Lung (gas exchange, pulmonary toxicity)
   - GI tract (absorption, first-pass metabolism)

2. **Advanced Features:**
   - Drug-drug interactions
   - Genetic polymorphisms (CYP450 variants)
   - Disease states (heart failure, cirrhosis)
   - Combination therapy

3. **Machine Learning:**
   - Toxicity prediction
   - Dose optimization
   - Biomarker discovery

4. **Clinical Integration:**
   - Patient-specific parameterization
   - Real-time monitoring
   - Clinical decision support

## References

1. **HBCM Foundation:** docs/hbcm_overview.md
2. **Validation Suite:** examples/validate_drug_toxicity.py
3. **Demonstrations:** examples/demo_multi_organ_system.py
4. **API Documentation:** See module docstrings

## License

MIT License - See LICENSE file for details

---

**Authors:** Multi-Organ Chip Architecture Team
**Version:** 1.0
**Date:** 2025
