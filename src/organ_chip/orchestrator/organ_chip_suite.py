"""
Organ Chip Suite Orchestrator

This module provides a high-level orchestrator for complete organ-on-chip
simulations integrating:
- Molecular models (ligand-receptor binding)
- Cellular models (immune signaling)
- Organ models (liver, heart)
- Systemic models (pharmacokinetics)
- Multiscale coupling

The orchestrator manages:
1. Model instantiation and configuration
2. Coupling setup
3. Simulation execution
4. Data collection and export
5. Visualization

Example Usage:
--------------
```python
from organ_chip.orchestrator import OrganChipSuite

# Create suite with default configuration
suite = OrganChipSuite()

# Or create with specific drug toxicity scenario
suite = OrganChipSuite.create_acetaminophen_toxicity()

# Run simulation
results = suite.run(duration=24.0, dt=0.1)  # 24 hours

# Analyze results
suite.plot_results()
suite.export_results('acetaminophen_results.csv')
```

Architecture:
-------------
┌─────────────────────────────────────────────────────────────┐
│                  Organ Chip Suite Orchestrator              │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Molecular  │  │   Cellular   │  │    Organ     │      │
│  │   Models    │→ │    Models    │→ │   Models     │      │
│  │             │  │              │  │              │      │
│  │ • Ligand-   │  │ • Immune     │  │ • Liver      │      │
│  │   Receptor  │  │   Signaling  │  │ • Heart      │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                ↓                   ↓             │
│  ┌──────────────────────────────────────────────────┐      │
│  │         Multiscale Coupling Layer               │      │
│  └──────────────────────────────────────────────────┘      │
│         ↓                                                  │
│  ┌──────────────────────────────────────────────────┐      │
│  │      Systemic Circulation (PBPK)                │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
"""

import numpy as np
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass
import json

from ..molecular.ligand_receptor import LigandReceptorModel, create_cytokine_receptor
from ..immune.cytokine_signaling import CytokineSignalingModel
from ..liver.hepatocyte import HepatocyteModel, create_acetaminophen_model, create_doxorubicin_model
from ..cardiac_enhanced.drug_cardiac_model import DrugCardiacModel, create_doxorubicin_cardiac_model
from ..circulation.pharmacokinetics import PharmacokineticsModel, create_standard_drug_pk
from ..multiscale.coupling import MultiscaleCoupler


@dataclass
class OrganChipConfig:
    """
    Configuration for organ chip suite.

    Attributes
    ----------
    include_molecular : bool
        Include molecular-scale models
    include_immune : bool
        Include immune signaling
    include_liver : bool
        Include liver model
    include_heart : bool
        Include cardiac model
    include_pk : bool
        Include pharmacokinetics
    drug_name : str
        Name of drug being tested
    """
    include_molecular: bool = True
    include_immune: bool = True
    include_liver: bool = True
    include_heart: bool = True
    include_pk: bool = True
    drug_name: str = "Unknown"


class OrganChipSuite:
    """
    Complete organ-on-chip simulation suite.

    This orchestrator integrates multiple scales and organ models to
    simulate drug-induced toxicity in a body-on-a-chip system.
    """

    def __init__(self, config: Optional[OrganChipConfig] = None):
        """
        Initialize organ chip suite.

        Parameters
        ----------
        config : OrganChipConfig, optional
            Configuration for the suite
        """
        self.config = config or OrganChipConfig()

        # Create coupler
        self.coupler = MultiscaleCoupler()

        # Model references
        self.molecular_model = None
        self.immune_model = None
        self.liver_model = None
        self.heart_model = None
        self.pk_model = None

        # Results storage
        self.results = {
            'time': [],
            'molecular': [],
            'immune': [],
            'liver': [],
            'heart': [],
            'pk': [],
        }

        # Setup models
        self._setup_models()
        self._setup_couplings()

    def _setup_models(self):
        """Initialize all models based on configuration."""
        # Molecular model (cytokine receptor)
        if self.config.include_molecular:
            self.molecular_model = create_cytokine_receptor()
            self.coupler.register_model(
                'molecular',
                self.molecular_model,
                time_scale=0.001  # Fast dynamics
            )

        # Immune model
        if self.config.include_immune:
            self.immune_model = CytokineSignalingModel()
            self.coupler.register_model(
                'immune',
                self.immune_model,
                time_scale=1.0  # Hour-scale
            )

        # Liver model
        if self.config.include_liver:
            self.liver_model = HepatocyteModel()
            self.coupler.register_model(
                'liver',
                self.liver_model,
                time_scale=1.0  # Hour-scale
            )

        # Heart model
        if self.config.include_heart:
            self.heart_model = DrugCardiacModel()
            self.coupler.register_model(
                'heart',
                self.heart_model,
                time_scale=0.001  # Millisecond-scale
            )

        # Pharmacokinetics model
        if self.config.include_pk:
            self.pk_model = create_standard_drug_pk()
            self.coupler.register_model(
                'pk',
                self.pk_model,
                time_scale=1.0  # Hour-scale
            )

    def _setup_couplings(self):
        """Setup couplings between models."""
        # PK → Liver: Drug concentration
        if self.pk_model and self.liver_model:
            def pk_to_liver(pk_model, liver_model, dt):
                state = pk_model.get_state()
                return {'drug_input': state['C_liver']}
            self.coupler.add_coupling('pk', 'liver', pk_to_liver)

        # PK → Heart: Drug concentration
        if self.pk_model and self.heart_model:
            def pk_to_heart(pk_model, heart_model, dt):
                state = pk_model.get_state()
                return {'drug_conc': state['C_heart']}
            self.coupler.add_coupling('pk', 'heart', pk_to_heart)

        # Liver → Immune: Damage signal
        if self.liver_model and self.immune_model:
            def liver_to_immune(liver_model, immune_model, dt):
                state = liver_model.get_state()
                damage = state['Damage']
                if damage > 0.1:
                    return {'external_stimulus': {'damage': (damage - 0.1) * 10.0}}
                return {}
            self.coupler.add_coupling('liver', 'immune', liver_to_immune)

        # Immune → Liver: Inflammatory feedback
        if self.immune_model and self.liver_model:
            def immune_to_liver(immune_model, liver_model, dt):
                # Inflammation can worsen liver damage
                # This would require extending the liver model
                # For now, return empty dict
                return {}
            self.coupler.add_coupling('immune', 'liver', immune_to_liver)

        # PK → Molecular: Ligand concentration
        if self.pk_model and self.molecular_model:
            def pk_to_molecular(pk_model, molecular_model, dt):
                state = pk_model.get_state()
                return {'external_ligand': state['C_blood'] * dt}
            self.coupler.add_coupling('pk', 'molecular', pk_to_molecular)

    def administer_drug(self, dose: float, route: str = 'bolus'):
        """
        Administer drug to the system.

        Parameters
        ----------
        dose : float
            Dose amount (μM·L)
        route : str
            Administration route ('bolus' or 'infusion')
        """
        if self.pk_model:
            if route == 'bolus':
                self.pk_model.state[0] += dose / self.pk_model.V_blood
            else:
                self.pk_model.dose_rate = dose

    def run(
        self,
        duration: float,
        dt: float = 0.1,
        dose: Optional[float] = None,
        dose_time: float = 0.0,
        adaptive: bool = True,
        save_interval: int = 1
    ) -> Dict[str, Any]:
        """
        Run the organ chip simulation.

        Parameters
        ----------
        duration : float
            Simulation duration (hours)
        dt : float
            Time step (hours)
        dose : float, optional
            Drug dose (μM·L)
        dose_time : float
            Time to administer dose (hours)
        adaptive : bool
            Use adaptive time-stepping
        save_interval : int
            Save results every N steps

        Returns
        -------
        dict
            Simulation results
        """
        n_steps = int(duration / dt)

        # Clear previous results
        self.results = {
            'time': [],
            'molecular': [],
            'immune': [],
            'liver': [],
            'heart': [],
            'pk': [],
        }

        for step in range(n_steps):
            current_time = step * dt

            # Administer dose at specified time
            if dose is not None and abs(current_time - dose_time) < dt / 2:
                self.administer_drug(dose, route='bolus')

            # Step all coupled models
            states = self.coupler.step(dt, adaptive=adaptive)

            # Save results at specified interval
            if step % save_interval == 0:
                self.results['time'].append(current_time)
                if self.molecular_model:
                    self.results['molecular'].append(states.get('molecular', {}))
                if self.immune_model:
                    self.results['immune'].append(states.get('immune', {}))
                if self.liver_model:
                    self.results['liver'].append(states.get('liver', {}))
                if self.heart_model:
                    self.results['heart'].append(states.get('heart', {}))
                if self.pk_model:
                    self.results['pk'].append(states.get('pk', {}))

        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics from simulation.

        Returns
        -------
        dict
            Summary statistics
        """
        summary = {
            'drug': self.config.drug_name,
            'duration': self.results['time'][-1] if self.results['time'] else 0.0,
        }

        # Liver summary
        if self.results['liver']:
            liver_states = self.results['liver']
            max_damage = max([s.get('Damage', 0.0) for s in liver_states])
            min_viability = min([s.get('viability', 1.0) for s in liver_states])
            summary['liver'] = {
                'max_damage': max_damage,
                'min_viability': min_viability,
                'final_GSH_GSSG_ratio': liver_states[-1].get('GSH_GSSG_ratio', 0.0),
            }

        # Heart summary
        if self.results['heart']:
            heart_states = self.results['heart']
            max_hERG_block = max([s.get('hERG_block', 0.0) for s in heart_states])
            summary['heart'] = {
                'max_hERG_block': max_hERG_block,
                'final_force': heart_states[-1].get('force', 0.0),
            }

        # PK summary
        if self.results['pk']:
            pk_states = self.results['pk']
            max_blood_conc = max([s.get('C_blood', 0.0) for s in pk_states])
            summary['pk'] = {
                'Cmax_blood': max_blood_conc,
                'AUC': pk_states[-1].get('AUC', 0.0),
                'half_life': pk_states[-1].get('half_life', 0.0),
            }

        # Immune summary
        if self.results['immune']:
            immune_states = self.results['immune']
            max_inflammatory_index = max([s.get('inflammatory_index', 0.0) for s in immune_states])
            summary['immune'] = {
                'max_inflammatory_index': max_inflammatory_index,
            }

        return summary

    def export_results(self, filename: str, format: str = 'json'):
        """
        Export results to file.

        Parameters
        ----------
        filename : str
            Output filename
        format : str
            Format ('json' or 'csv')
        """
        if format == 'json':
            with open(filename, 'w') as f:
                json.dump({
                    'config': self.config.__dict__,
                    'results': self.results,
                    'summary': self.get_summary(),
                }, f, indent=2)
        elif format == 'csv':
            # Flatten results for CSV
            with open(filename, 'w') as f:
                # Write header
                header = ['time']
                if self.liver_model:
                    header.extend(['liver_damage', 'liver_viability', 'liver_GSH'])
                if self.heart_model:
                    header.extend(['heart_V', 'heart_force', 'heart_hERG_block'])
                if self.pk_model:
                    header.extend(['C_blood', 'C_liver', 'C_heart'])
                if self.immune_model:
                    header.extend(['IL6', 'TNFa', 'IL10', 'inflammatory_index'])

                f.write(','.join(header) + '\n')

                # Write data
                for i, t in enumerate(self.results['time']):
                    row = [str(t)]

                    if self.liver_model and i < len(self.results['liver']):
                        ls = self.results['liver'][i]
                        row.extend([
                            str(ls.get('Damage', '')),
                            str(ls.get('viability', '')),
                            str(ls.get('GSH', ''))
                        ])

                    if self.heart_model and i < len(self.results['heart']):
                        hs = self.results['heart'][i]
                        row.extend([
                            str(hs.get('V', '')),
                            str(hs.get('force', '')),
                            str(hs.get('hERG_block', ''))
                        ])

                    if self.pk_model and i < len(self.results['pk']):
                        ps = self.results['pk'][i]
                        row.extend([
                            str(ps.get('C_blood', '')),
                            str(ps.get('C_liver', '')),
                            str(ps.get('C_heart', ''))
                        ])

                    if self.immune_model and i < len(self.results['immune']):
                        im_s = self.results['immune'][i]
                        row.extend([
                            str(im_s.get('IL6', '')),
                            str(im_s.get('TNFa', '')),
                            str(im_s.get('IL10', '')),
                            str(im_s.get('inflammatory_index', ''))
                        ])

                    f.write(','.join(row) + '\n')

    @classmethod
    def create_acetaminophen_toxicity(cls) -> 'OrganChipSuite':
        """
        Create a suite configured for acetaminophen hepatotoxicity.

        Returns
        -------
        OrganChipSuite
            Configured suite
        """
        suite = cls(OrganChipConfig(drug_name='Acetaminophen'))
        suite.liver_model = create_acetaminophen_model()
        suite.coupler.models['liver'] = suite.liver_model
        return suite

    @classmethod
    def create_doxorubicin_cardiotoxicity(cls) -> 'OrganChipSuite':
        """
        Create a suite configured for doxorubicin cardiotoxicity.

        Returns
        -------
        OrganChipSuite
            Configured suite
        """
        suite = cls(OrganChipConfig(drug_name='Doxorubicin'))
        suite.liver_model = create_doxorubicin_model()
        suite.heart_model = create_doxorubicin_cardiac_model()
        suite.coupler.models['liver'] = suite.liver_model
        suite.coupler.models['heart'] = suite.heart_model
        return suite

    @classmethod
    def create_minimal(cls, include_organs: List[str]) -> 'OrganChipSuite':
        """
        Create a minimal suite with only specified organs.

        Parameters
        ----------
        include_organs : list
            List of organs to include: ['liver', 'heart', 'immune', 'molecular', 'pk']

        Returns
        -------
        OrganChipSuite
            Configured suite
        """
        config = OrganChipConfig(
            include_molecular='molecular' in include_organs,
            include_immune='immune' in include_organs,
            include_liver='liver' in include_organs,
            include_heart='heart' in include_organs,
            include_pk='pk' in include_organs,
        )
        return cls(config)
