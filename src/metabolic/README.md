# Metabolic Module

## Overview

The metabolic module provides organ-on-chip models for drug metabolism, pharmacokinetics, and hepatotoxicity assessment. Built on the Primal Logic Framework, these models simulate the complex interplay between drug exposure, cellular metabolism, bioenergetics, and toxicity.

## Components

### Liver Chip Model (`liver_chip.py`)

A comprehensive hepatotoxicity model simulating:

- **Hepatocyte Population Dynamics**: Viable, damaged, and dead cell populations with repair mechanisms
- **Drug Metabolism**: CYP450-mediated metabolism using Michaelis-Menten kinetics
- **Bioenergetics**: ATP production/consumption and mitochondrial function
- **Antioxidant Defense**: Glutathione (GSH) dynamics and oxidative stress
- **Biomarker Extraction**: ALT, AST, LDH, albumin, and viability metrics

### Key Classes

#### `LiverParameters`
Configurable physiological parameters including:
- Hepatocyte population parameters (growth, death, repair rates)
- CYP450 kinetic constants (Vmax, Km)
- Bioenergetic parameters (ATP/GSH baseline, synthesis, consumption rates)
- Circulation parameters (blood flow, compartment volumes)

#### `HepatocytePopulation`
Models cell viability dynamics with multi-stressor toxicity assessment:
- Chemical toxicity from parent drug and metabolites
- Energy depletion toxicity (ATP levels)
- Oxidative stress toxicity (GSH depletion)

#### `LiverMetabolism`
Simulates drug biotransformation:
- Michaelis-Menten enzyme kinetics
- CYP450 induction and inhibition
- Metabolite production and clearance

#### `LiverBioenergetics`
Tracks cellular energy state:
- ATP production and consumption
- Metabolic load from drug processing
- Drug-induced mitochondrial damage
- GSH synthesis and oxidative consumption

#### `LiverChipModel`
Integrated model combining all subsystems with:
- 8-state ODE system
- RK4 numerical integration
- Biomarker extraction
- Time-varying drug dosing support

## Usage Example

```python
from src.metabolic import LiverChipModel

# Initialize model with default parameters
liver = LiverChipModel()

# Define dosing schedule
def drug_dose(t):
    if t < 24:
        return 50.0  # Therapeutic dose (μM)
    elif 24 <= t < 48:
        return 200.0  # Toxic dose (μM)
    else:
        return 0.0

# Run simulation
times, states = liver.simulate(
    t_span=(0.0, 72.0),
    drug_dose_schedule=drug_dose,
    blood_flow=1.5,  # L/hr
    dt=0.1  # 6-minute timesteps
)

# Extract biomarkers at final timepoint
biomarkers = liver.get_biomarkers(states[-1])
print(f"Viability: {biomarkers['Viability']:.1f}%")
print(f"ALT: {biomarkers['ALT']:.1f} U/L")
print(f"GSH: {biomarkers['GSH']:.2f} mM")
```

## State Vector

The model uses an 8-dimensional state vector:

| Index | Variable | Description | Units |
|-------|----------|-------------|-------|
| 0 | N_viable | Viable hepatocytes | cells |
| 1 | N_damaged | Damaged hepatocytes | cells |
| 2 | N_dead | Dead hepatocytes | cells |
| 3 | drug_conc | Drug concentration | μM |
| 4 | metabolite_conc | Metabolite concentration | μM |
| 5 | CYP450_activity | Enzyme activity (normalized) | - |
| 6 | ATP_level | Cellular ATP | mM |
| 7 | GSH_level | Glutathione | mM |

## Biomarkers

The model extracts clinically relevant biomarkers:

- **ALT/AST**: Hepatocellular injury markers (U/L)
- **LDH**: Cell death indicator (U/L)
- **Albumin**: Synthetic function surrogate (g/dL)
- **ATP**: Bioenergetic status (mM)
- **GSH**: Antioxidant capacity (mM)
- **Viability**: Percent viable cells (%)
- **Drug_clearance**: Metabolic activity (normalized)
- **Drug_conc/Metabolite_conc**: Pharmacokinetics (μM)

## Mathematical Framework

The model follows the **Primal Logic Framework**:

```
dx/dt = α*θ - λ*x
```

Where:
- **α**: Production/accumulation term (cautious by design)
- **θ**: Enabling/regulatory factor
- **λ**: Decay/clearance term (aggressive for stability)

This framework ensures:
- Physiologically plausible bounds
- Stable numerical integration
- Interpretable parameters

## Integration with Multi-Organ Systems

The liver chip model is designed for integration with:
- **Cardiac models**: Heart-liver drug-drug interactions, QT prolongation
- **Neural models**: CNS-active drug metabolism, sedative effects
- **Coupling models**: Systemic circulation, multi-organ toxicity

Example multi-organ coupling:
```python
# Future integration example
from src.metabolic import LiverChipModel
from src.cardiac import VanDerPolCardiac
from src.coupling import OrganCouplingModel

# Create multi-organ system
liver = LiverChipModel()
heart = VanDerPolCardiac()
system = OrganCouplingModel(liver=liver, heart=heart)

# Simulate cardiotoxic drug with hepatic metabolism
system.simulate_drug_exposure(drug_profile='doxorubicin')
```

## Testing

Run the standalone validation:

```bash
python -m src.metabolic.liver_chip
```

This executes an acetaminophen toxicity simulation demonstrating:
- Therapeutic dose tolerance (0-24hr)
- Toxic dose hepatotoxicity (24-48hr)
- Recovery dynamics (48-72hr)

Expected output:
- Time-resolved viability, ALT, ATP, GSH
- Toxicity classification (minimal/moderate/severe)
- Warning indicators for elevated biomarkers

## References

- **Primal Logic Framework**: Custom mathematical framework for cautious accumulation
- **Michaelis-Menten Kinetics**: Standard enzyme kinetic model
- **Acetaminophen Hepatotoxicity**: Clinical validation benchmark
- **Organ-on-Chip Technology**: Microphysiological system design principles

## Future Extensions

Planned enhancements:
- [ ] Phase II metabolism (conjugation reactions)
- [ ] Multiple drug interactions (CYP inhibition/induction)
- [ ] Oxygenation gradient modeling (periportal vs pericentral zones)
- [ ] Bile acid synthesis and secretion
- [ ] Inflammatory cytokine release
- [ ] Integration with PK/PD models
- [ ] Machine learning-based toxicity prediction

## Contributing

When extending this module:
1. Maintain the Primal Logic Framework structure
2. Ensure parameter units are clearly documented
3. Add validation examples with known drugs
4. Include unit tests for new functionality
5. Update this README with new features
