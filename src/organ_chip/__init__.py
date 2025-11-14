"""
Organ-on-Chip Multiscale Modeling Suite

This package provides a comprehensive organ-on-chip modeling framework
integrating molecular, cellular, tissue, organ, and systemic scales.

Modules:
--------
- molecular: Ligand-receptor binding dynamics
- immune: Cytokine signaling and immune response
- liver: Hepatocyte model with drug metabolism and toxicity
- cardiac_enhanced: Enhanced cardiac model with drug effects
- circulation: Pharmacokinetics and drug distribution
- multiscale: Coupling infrastructure for multiscale integration
- orchestrator: High-level orchestration for complete simulations

Quick Start:
------------
```python
from organ_chip.orchestrator import OrganChipSuite

# Create acetaminophen toxicity simulation
suite = OrganChipSuite.create_acetaminophen_toxicity()

# Run simulation (24 hours, dose at t=0)
results = suite.run(duration=24.0, dt=0.1, dose=1000.0)

# Get summary
summary = suite.get_summary()
print(f"Max liver damage: {summary['liver']['max_damage']:.2%}")

# Export results
suite.export_results('results.csv', format='csv')
```

Architecture:
-------------
The organ chip suite integrates models across five spatial/temporal scales:

1. Molecular (us-ms): Ligand-receptor binding
2. Cellular (ms-s): Immune signaling, ion channels
3. Tissue (s-min): Hepatocyte populations
4. Organ (min-h): Liver function, cardiac electrophysiology
5. Systemic (h-days): Pharmacokinetics, circulation

Models are coupled through the multiscale coupling layer, which handles:
- Signal routing between models
- Time scale synchronization
- Adaptive time-stepping
- Feedback loops
"""

# Molecular models
from .molecular import (
    LigandReceptorModel,
    create_growth_factor_receptor,
    create_cytokine_receptor,
)

# Immune models
from .immune import (
    CytokineSignalingModel,
    create_acute_inflammation_model,
    create_chronic_inflammation_model,
)

# Liver models
from .liver import (
    HepatocyteModel,
    create_acetaminophen_model,
    create_doxorubicin_model,
)

# Cardiac models
from .cardiac_enhanced import (
    DrugCardiacModel,
    create_doxorubicin_cardiac_model,
    create_quinidine_cardiac_model,
)

# Circulation models
from .circulation import (
    PharmacokineticsModel,
    create_standard_drug_pk,
    create_high_clearance_drug_pk,
    create_lipophilic_drug_pk,
)

# Multiscale coupling
from .multiscale import (
    MultiscaleCoupler,
    CouplingSignal,
    TimeScale,
    drug_circulation_to_organ,
    organ_damage_to_immune,
    immune_to_organ_feedback,
    hepatic_clearance_to_pk,
)

# Orchestrator
from .orchestrator import (
    OrganChipSuite,
    OrganChipConfig,
)

__version__ = '0.1.0'

__all__ = [
    # Molecular
    'LigandReceptorModel',
    'create_growth_factor_receptor',
    'create_cytokine_receptor',
    # Immune
    'CytokineSignalingModel',
    'create_acute_inflammation_model',
    'create_chronic_inflammation_model',
    # Liver
    'HepatocyteModel',
    'create_acetaminophen_model',
    'create_doxorubicin_model',
    # Cardiac
    'DrugCardiacModel',
    'create_doxorubicin_cardiac_model',
    'create_quinidine_cardiac_model',
    # Circulation
    'PharmacokineticsModel',
    'create_standard_drug_pk',
    'create_high_clearance_drug_pk',
    'create_lipophilic_drug_pk',
    # Multiscale
    'MultiscaleCoupler',
    'CouplingSignal',
    'TimeScale',
    'drug_circulation_to_organ',
    'organ_damage_to_immune',
    'immune_to_organ_feedback',
    'hepatic_clearance_to_pk',
    # Orchestrator
    'OrganChipSuite',
    'OrganChipConfig',
]
