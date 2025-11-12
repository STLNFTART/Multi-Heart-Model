"""
Primal Logic Framework

Unified mathematical framework for multiscale biological modeling based on
the Recursive Planck Operator (RPO) and accumulation-decay dynamics (α - λx).

Modules:
- core: RPO mathematical framework
- molecular: Ligand-receptor binding
- cellular: Immune signaling, cell populations
- organ: Liver and cardiac subsystems
- systemic: Circulation and whole-body distribution
- integration: Multiscale coupling and organ-chip suite

Author: Donte Lightfoot (Lightfoot Technology / Primal Logic)
"""

__version__ = "1.0.0"
__author__ = "Donte Lightfoot"

# Core framework
from .core.rpo import RPOVariable, RPOParameters
from .core.rpo_organ_chip import (
    RPO_HeartBrainCoupling,
    RPO_LiverMetabolism,
    RPO_ImmuneResponse,
    RPO_MetabolicStress,
    RPO_OrganChipSuite
)

# Molecular level
from .molecular.ligand_receptor import LigandReceptor, LigandReceptorParameters, DrugReceptorBinding

# Cellular level
from .cellular.immune_signaling import ImmuneSignaling, ImmuneParameters, CytokineProfiles

# Organ level - Liver
from .organ.liver import (
    HepatocytePopulation,
    HepatocyteParameters,
    LiverMetabolism,
    MetabolismParameters,
    CYP450System,
    LiverToxicity,
    ToxicityParameters,
    ToxicityMechanism
)

# Organ level - Cardiac
from .organ.cardiac import (
    CardiomyocyteModel,
    CardiomyocyteParameters,
    CardiacToxicity,
    CardiacToxicityParameters,
    CardiacToxicityMechanism
)

# Systemic level
from .systemic.circulation import SystemicCirculation, CirculationParameters

# Integration
from .integration.multiscale_coupling import MultiscaleCoupling, MultiscaleCouplingParameters
from .integration.organ_chip_suite import OrganChipSuite, DrugProfile, ToxicityReport, ToxicitySeverity

__all__ = [
    # Core
    'RPOVariable',
    'RPOParameters',
    'RPO_HeartBrainCoupling',
    'RPO_LiverMetabolism',
    'RPO_ImmuneResponse',
    'RPO_MetabolicStress',
    'RPO_OrganChipSuite',

    # Molecular
    'LigandReceptor',
    'LigandReceptorParameters',
    'DrugReceptorBinding',

    # Cellular
    'ImmuneSignaling',
    'ImmuneParameters',
    'CytokineProfiles',

    # Liver
    'HepatocytePopulation',
    'HepatocyteParameters',
    'LiverMetabolism',
    'MetabolismParameters',
    'CYP450System',
    'LiverToxicity',
    'ToxicityParameters',
    'ToxicityMechanism',

    # Cardiac
    'CardiomyocyteModel',
    'CardiomyocyteParameters',
    'CardiacToxicity',
    'CardiacToxicityParameters',
    'CardiacToxicityMechanism',

    # Systemic
    'SystemicCirculation',
    'CirculationParameters',

    # Integration
    'MultiscaleCoupling',
    'MultiscaleCouplingParameters',
    'OrganChipSuite',
    'DrugProfile',
    'ToxicityReport',
    'ToxicitySeverity',
]
