"""Multiscale integration coupling organ chips via circulation and signaling.

This module provides:
- Organ-organ coupling via blood circulation
- Cytokine and hormone signaling between organs
- Multiscale temporal integration
- Feedback loops (liver metabolism → cardiac toxicity, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Dict, List, Optional
import math


@dataclass
class IntegrationParameters:
    """Parameters for multiscale organ integration.

    Attributes
    ----------
    time_scale_factors : Dict[str, float]
        Relative time scales for different processes
    coupling_strengths : Dict[str, float]
        Inter-organ coupling strengths
    """

    # Time scale factors (relative to base dt)
    time_scale_factors: Dict[str, float] = field(default_factory=lambda: {
        'cardiac_electrical': 0.001,     # ms scale
        'cardiac_mechanical': 0.01,      # 10ms scale
        'metabolism': 1.0,               # minute-hour scale
        'immune': 1.0,                   # hour scale
        'circulation': 0.1,              # fast mixing
    })

    # Coupling strength parameters
    coupling_strengths: Dict[str, float] = field(default_factory=lambda: {
        'liver_to_cardiac': 1.0,         # Metabolite effects on heart
        'cardiac_to_liver': 0.5,         # Hemodynamic effects on liver
        'immune_to_cardiac': 0.8,        # Cytokine effects on heart
        'immune_to_liver': 0.7,          # Cytokine effects on liver
        'circulation_mixing': 1.0,        # Blood flow coupling
    })


@dataclass
class OrganInteractions:
    """Models interactions between different organ systems.

    Captures:
    - Metabolite transport via circulation
    - Cytokine signaling
    - Hemodynamic coupling
    - Feedback mechanisms
    """

    params: IntegrationParameters = field(default_factory=IntegrationParameters)

    def liver_cardiac_coupling(
        self,
        liver_metabolite: float,
        cardiac_state: Dict[str, float],
        dt: float
    ) -> Dict[str, float]:
        """Compute liver metabolite effects on cardiac function.

        Parameters
        ----------
        liver_metabolite : float
            Concentration of cardiotoxic metabolite (μM)
        cardiac_state : dict
            Current cardiac state variables
        dt : float
            Time step (h)

        Returns
        -------
        dict
            Cardiac state updates
        """
        # Metabolite-induced ion channel modulation
        IC50_cardiac = 10.0  # μM
        inhibition = liver_metabolite / (IC50_cardiac + liver_metabolite)

        coupling_strength = self.params.coupling_strengths['liver_to_cardiac']

        # Effects on cardiac parameters
        updates = {
            'hERG_inhibition': inhibition * coupling_strength,
            'contractility_reduction': 0.5 * inhibition * coupling_strength,
            'troponin_release_rate': 0.1 * liver_metabolite * coupling_strength,
        }

        return updates

    def cardiac_liver_coupling(
        self,
        cardiac_output: float,
        normal_cardiac_output: float,
        liver_state: Dict[str, float]
    ) -> Dict[str, float]:
        """Compute cardiac hemodynamic effects on liver function.

        Parameters
        ----------
        cardiac_output : float
            Current cardiac output (L/h)
        normal_cardiac_output : float
            Normal cardiac output (L/h)
        liver_state : dict
            Current liver state

        Returns
        -------
        dict
            Liver state updates
        """
        # Reduced cardiac output → reduced hepatic perfusion
        perfusion_ratio = cardiac_output / normal_cardiac_output

        coupling_strength = self.params.coupling_strengths['cardiac_to_liver']

        # Effects on liver metabolism
        updates = {
            'metabolism_scaling': perfusion_ratio * coupling_strength + (1.0 - coupling_strength),
            'hypoxia_factor': max(0.0, 1.0 - perfusion_ratio) * coupling_strength,
        }

        return updates

    def immune_organ_coupling(
        self,
        cytokine_levels: Dict[str, float],
        organ: str
    ) -> Dict[str, float]:
        """Compute cytokine effects on organ function.

        Parameters
        ----------
        cytokine_levels : dict
            Current cytokine concentrations (pg/mL)
        organ : str
            Target organ ('cardiac', 'liver', etc.)

        Returns
        -------
        dict
            Organ-specific cytokine effects
        """
        # Pro-inflammatory cytokines
        TNFa = cytokine_levels.get('TNFa', 0.0)
        IL6 = cytokine_levels.get('IL6', 0.0)

        # Get coupling strength
        coupling_key = f'immune_to_{organ}'
        coupling_strength = self.params.coupling_strengths.get(coupling_key, 0.5)

        if organ == 'cardiac':
            # Cytokines can cause cardiac dysfunction
            return {
                'contractility_reduction': 0.01 * TNFa * coupling_strength,
                'electrical_remodeling': 0.005 * (TNFa + IL6) * coupling_strength,
                'inflammation_score': (TNFa + IL6) * 0.1,
            }
        elif organ == 'liver':
            # Cytokines modulate liver metabolism
            return {
                'acute_phase_response': IL6 * 0.1 * coupling_strength,
                'metabolism_inhibition': 0.02 * TNFa * coupling_strength,
                'hepatocyte_stress': (TNFa + IL6) * 0.05,
            }
        else:
            return {}

    def circulation_mediated_coupling(
        self,
        organ_outputs: Dict[str, float],
        blood_flows: Dict[str, float],
        mixing_time: float = 0.1
    ) -> Dict[str, float]:
        """Compute circulation-mediated substance transport between organs.

        Parameters
        ----------
        organ_outputs : dict
            Substance release from each organ (mg/h)
        blood_flows : dict
            Blood flow to each organ (L/h)
        mixing_time : float
            Characteristic mixing time (h)

        Returns
        -------
        dict
            Substance delivery to each organ (mg/h)
        """
        # Simple well-mixed model
        total_output = sum(organ_outputs.values())
        total_flow = sum(blood_flows.values())

        if total_flow <= 0:
            return {organ: 0.0 for organ in blood_flows}

        # Distribute proportional to blood flow
        deliveries = {}
        for organ, flow in blood_flows.items():
            flow_fraction = flow / total_flow
            deliveries[organ] = total_output * flow_fraction

        return deliveries


@dataclass
class MultiscaleCoupling:
    """Complete multiscale coupling framework.

    Integrates:
    - Circulation model
    - Organ models (cardiac, liver, immune)
    - Inter-organ signaling
    - Temporal coupling
    """

    interactions: OrganInteractions = field(default_factory=OrganInteractions)

    # Organ model references (to be set externally)
    cardiac_model: Optional[any] = None
    liver_model: Optional[any] = None
    immune_model: Optional[any] = None
    circulation_model: Optional[any] = None

    def integrate_step(
        self,
        t: float,
        state: Dict[str, any],
        dt: float,
        drug_dose: float = 0.0
    ) -> Dict[str, any]:
        """Perform one integrated time step across all organ systems.

        Parameters
        ----------
        t : float
            Current time (h)
        state : dict
            Complete system state containing:
            - 'circulation': plasma and organ drug amounts
            - 'liver': hepatocyte state
            - 'cardiac': cardiac cell state
            - 'immune': cytokine levels
        dt : float
            Time step (h)
        drug_dose : float
            Drug dosing rate (mg/h)

        Returns
        -------
        dict
            Updated system state
        """
        # Extract current states
        circ_state = state.get('circulation', {})
        liver_state = state.get('liver', {})
        cardiac_state = state.get('cardiac', {})
        immune_state = state.get('immune', {})

        # --- Circulation Update ---
        # Drug distribution through organs
        if self.circulation_model is not None:
            circ_derivs = self.circulation_model.derivatives(
                t, circ_state, dose_rate=drug_dose
            )
            circ_state_new = {
                key: max(0.0, val + dt * circ_derivs.get(key, 0.0))
                for key, val in circ_state.items()
            }
        else:
            circ_state_new = circ_state

        # Get organ concentrations
        plasma_drug = circ_state_new.get('plasma', 0.0) / 3.0  # Vplasma = 3L
        liver_drug = circ_state_new.get('liver', 0.0) / 1.8   # Vliver = 1.8L
        heart_drug = circ_state_new.get('heart', 0.0) / 0.3   # Vheart = 0.3L

        # --- Liver Update ---
        # Liver exposed to plasma drug concentration
        if self.liver_model is not None:
            # Simplified: use reactive metabolite as coupling variable
            liver_reactive = liver_state.get('Reactive', 0.0)

            # Check if liver has hemodynamic modulation
            cardiac_output = cardiac_state.get('cardiac_output', 300.0)
            liver_coupling = self.interactions.cardiac_liver_coupling(
                cardiac_output, 300.0, liver_state
            )
            metabolism_scaling = liver_coupling.get('metabolism_scaling', 1.0)

            # Update liver (simplified - would call liver_model.derivatives)
            liver_state_new = liver_state.copy()
            # In full implementation, call liver model with scaled metabolism
        else:
            liver_state_new = liver_state
            liver_reactive = 0.0

        # --- Cardiac Update ---
        # Cardiac exposed to drug + reactive metabolite
        if self.cardiac_model is not None:
            effective_cardiotoxic = heart_drug + 0.5 * liver_reactive

            # Cytokine effects on cardiac function
            immune_effects = self.interactions.immune_organ_coupling(
                immune_state, 'cardiac'
            )

            # Update cardiac state (simplified)
            cardiac_state_new = cardiac_state.copy()
            cardiac_state_new['drug_exposure'] = effective_cardiotoxic
            cardiac_state_new['inflammation_effect'] = immune_effects.get('inflammation_score', 0.0)
        else:
            cardiac_state_new = cardiac_state

        # --- Immune Update ---
        # Immune response to organ damage
        if self.immune_model is not None:
            # Damage signals from organs
            liver_damage = liver_state.get('Cell_viability', 1.0)
            cardiac_damage = cardiac_state.get('Troponin', 0.0)

            damage_stimulus = (1.0 - liver_damage) + 0.1 * cardiac_damage

            # Update immune state (simplified)
            immune_state_new = immune_state.copy()
            # In full implementation, call immune_model.step with damage_stimulus
        else:
            immune_state_new = immune_state

        # Return integrated state
        return {
            'circulation': circ_state_new,
            'liver': liver_state_new,
            'cardiac': cardiac_state_new,
            'immune': immune_state_new,
        }

    def simulate_integrated_system(
        self,
        initial_state: Dict[str, any],
        t_span: Tuple[float, float],
        dt: float,
        dosing_schedule: Optional[List[Tuple[float, float]]] = None
    ) -> List[Tuple[float, Dict[str, any]]]:
        """Simulate complete integrated multi-organ system.

        Parameters
        ----------
        initial_state : dict
            Initial state for all subsystems
        t_span : tuple
            (start_time, end_time) in hours
        dt : float
            Time step (hours)
        dosing_schedule : list, optional
            List of (time, dose_rate) tuples

        Returns
        -------
        list
            Time series of (time, state) tuples
        """
        t_start, t_end = t_span
        trajectory = [(t_start, initial_state.copy())]

        state = initial_state.copy()
        t = t_start

        # Parse dosing schedule
        dose_dict = {}
        if dosing_schedule:
            for dose_time, dose_rate in dosing_schedule:
                dose_dict[dose_time] = dose_rate

        while t < t_end:
            # Get current dose
            dose = dose_dict.get(round(t, 3), 0.0)

            # Integrate one step
            state = self.integrate_step(t, state, dt, drug_dose=dose)

            t += dt
            trajectory.append((t, state.copy()))

        return trajectory

    def extract_key_metrics(
        self,
        trajectory: List[Tuple[float, Dict[str, any]]]
    ) -> Dict[str, List[float]]:
        """Extract key metrics from simulation trajectory.

        Parameters
        ----------
        trajectory : list
            Simulation time series

        Returns
        -------
        dict
            Time series of key biomarkers and metrics
        """
        metrics = {
            'time': [],
            'plasma_drug': [],
            'liver_viability': [],
            'cardiac_APD': [],
            'TNFa': [],
            'troponin': [],
        }

        for t, state in trajectory:
            metrics['time'].append(t)

            # Circulation
            circ = state.get('circulation', {})
            plasma = circ.get('plasma', 0.0) / 3.0
            metrics['plasma_drug'].append(plasma)

            # Liver
            liver = state.get('liver', {})
            metrics['liver_viability'].append(liver.get('Cell_viability', 1.0))

            # Cardiac
            cardiac = state.get('cardiac', {})
            metrics['cardiac_APD'].append(cardiac.get('APD', 300.0))
            metrics['troponin'].append(cardiac.get('Troponin', 0.01))

            # Immune
            immune = state.get('immune', {})
            metrics['TNFa'].append(immune.get('TNFa', 0.5))

        return metrics
