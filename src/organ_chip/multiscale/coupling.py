"""
Multiscale Coupling Integration Layer

This module provides infrastructure for coupling models across different
spatial and temporal scales in the organ-on-chip system.

Coupling Mechanisms:
--------------------
1. **Molecular → Cellular**: Ligand-receptor → Immune signaling
   - Cytokine binding activates macrophages
   - Receptor occupancy triggers downstream cascades

2. **Cellular → Tissue**: Hepatocyte → Liver metabolism
   - Individual cell damage → Tissue-level toxicity
   - Metabolite production → Systemic exposure

3. **Tissue → Organ**: Cardiac cells → Heart function
   - Myocyte contractility → Cardiac output
   - Ion channel block → ECG changes

4. **Organ → System**: Liver/Heart → Circulation
   - Hepatic clearance → Blood concentrations
   - Cardiac output → Tissue perfusion

5. **System → Molecular**: Circulation → Ligand-receptor
   - Drug distribution → Target engagement
   - Metabolite feedback → Cellular responses

Design Patterns:
----------------
- **Observer Pattern**: Organs observe circulation changes
- **Mediator Pattern**: Circulation mediates inter-organ communication
- **Strategy Pattern**: Different coupling strategies for different scales

Time Scale Separation:
----------------------
- Molecular: microseconds to milliseconds
- Cellular: milliseconds to seconds
- Tissue: seconds to minutes
- Organ: minutes to hours
- System: hours to days

We use operator splitting and adaptive time-stepping to handle these
disparate scales efficiently.
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TimeScale(Enum):
    """Enumeration of time scales."""
    MOLECULAR = 1e-3    # milliseconds
    CELLULAR = 1e0      # seconds
    TISSUE = 60.0       # minutes
    ORGAN = 3600.0      # hours
    SYSTEM = 86400.0    # days


@dataclass
class CouplingSignal:
    """
    A signal passed between models.

    Attributes
    ----------
    source : str
        Source model identifier
    target : str
        Target model identifier
    signal_type : str
        Type of signal (e.g., 'drug_conc', 'cytokine', 'damage')
    value : float
        Signal value
    time : float
        Time of signal generation
    metadata : dict
        Additional metadata
    """
    source: str
    target: str
    signal_type: str
    value: float
    time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class MultiscaleCoupler:
    """
    Multiscale coupling manager for organ-on-chip models.

    This class manages:
    - Model registration and dependencies
    - Signal routing between models
    - Time scale synchronization
    - Operator splitting for efficiency

    Models can be coupled through:
    1. Direct coupling: Model A directly affects Model B
    2. Mediated coupling: Model A → Mediator → Model B
    3. Feedback coupling: Bidirectional effects
    """

    def __init__(self):
        """Initialize multiscale coupler."""
        # Registered models
        self.models: Dict[str, Any] = {}

        # Model time scales
        self.time_scales: Dict[str, float] = {}

        # Coupling functions: (source, target) → coupling_func
        self.couplings: Dict[Tuple[str, str], Callable] = {}

        # Signal buffer for inter-model communication
        self.signals: List[CouplingSignal] = []

        # Current time
        self.time = 0.0

        # History
        self.history = {
            't': [0.0],
            'signals': [],
        }

    def register_model(
        self,
        name: str,
        model: Any,
        time_scale: float = 1.0
    ) -> None:
        """
        Register a model with the coupler.

        Parameters
        ----------
        name : str
            Model identifier
        model : Any
            Model instance (must have 'step' method)
        time_scale : float
            Characteristic time scale (seconds)
        """
        if not hasattr(model, 'step'):
            raise ValueError(f"Model {name} must have a 'step' method")

        self.models[name] = model
        self.time_scales[name] = time_scale

    def add_coupling(
        self,
        source: str,
        target: str,
        coupling_func: Callable[[Any, Any, float], Dict[str, float]]
    ) -> None:
        """
        Add a coupling between two models.

        Parameters
        ----------
        source : str
            Source model name
        target : str
            Target model name
        coupling_func : callable
            Function that takes (source_model, target_model, dt) and returns
            a dict of inputs to target model
        """
        if source not in self.models:
            raise ValueError(f"Source model {source} not registered")
        if target not in self.models:
            raise ValueError(f"Target model {target} not registered")

        self.couplings[(source, target)] = coupling_func

    def send_signal(
        self,
        source: str,
        target: str,
        signal_type: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a signal from one model to another.

        Parameters
        ----------
        source : str
            Source model name
        target : str
            Target model name
        signal_type : str
            Signal type identifier
        value : float
            Signal value
        metadata : dict, optional
            Additional metadata
        """
        signal = CouplingSignal(
            source=source,
            target=target,
            signal_type=signal_type,
            value=value,
            time=self.time,
            metadata=metadata or {}
        )
        self.signals.append(signal)

    def get_signals(
        self,
        target: str,
        signal_type: Optional[str] = None
    ) -> List[CouplingSignal]:
        """
        Get signals for a specific target.

        Parameters
        ----------
        target : str
            Target model name
        signal_type : str, optional
            Filter by signal type

        Returns
        -------
        list
            List of signals
        """
        signals = [s for s in self.signals if s.target == target]
        if signal_type is not None:
            signals = [s for s in signals if s.signal_type == signal_type]
        return signals

    def clear_signals(self) -> None:
        """Clear all buffered signals."""
        self.signals.clear()

    def step(self, dt: float, adaptive: bool = False) -> Dict[str, Any]:
        """
        Advance all coupled models by one time step.

        Parameters
        ----------
        dt : float
            Global time step (seconds)
        adaptive : bool
            Use adaptive time-stepping based on model time scales

        Returns
        -------
        dict
            States of all models
        """
        # Determine sub-steps for each model if adaptive
        if adaptive:
            sub_steps = {}
            for name, time_scale in self.time_scales.items():
                # Use multiple sub-steps for fast dynamics
                sub_steps[name] = max(1, int(dt / time_scale))
        else:
            sub_steps = {name: 1 for name in self.models}

        # Execute couplings to generate inputs
        coupling_inputs = {name: {} for name in self.models}

        for (source, target), coupling_func in self.couplings.items():
            source_model = self.models[source]
            target_model = self.models[target]
            inputs = coupling_func(source_model, target_model, dt)
            coupling_inputs[target].update(inputs)

        # Step each model with appropriate sub-stepping
        states = {}
        for name, model in self.models.items():
            n_sub = sub_steps[name]
            dt_sub = dt / n_sub

            # Get coupling inputs for this model
            inputs = coupling_inputs.get(name, {})

            # Sub-step
            for _ in range(n_sub):
                model.step(dt_sub, **inputs)

            # Store state
            if hasattr(model, 'get_state'):
                states[name] = model.get_state()
            else:
                states[name] = {'state': model.state.copy() if hasattr(model, 'state') else None}

        # Update time
        self.time += dt

        # Update history
        self.history['t'].append(self.time)
        self.history['signals'].append(len(self.signals))

        return states

    def get_model(self, name: str) -> Any:
        """
        Get a registered model.

        Parameters
        ----------
        name : str
            Model name

        Returns
        -------
        Any
            Model instance
        """
        return self.models.get(name)

    def get_state(self) -> Dict[str, Any]:
        """
        Get states of all models.

        Returns
        -------
        dict
            Dictionary of model states
        """
        states = {}
        for name, model in self.models.items():
            if hasattr(model, 'get_state'):
                states[name] = model.get_state()
            else:
                states[name] = {'state': model.state.copy() if hasattr(model, 'state') else None}
        return states


# Predefined coupling functions

def drug_circulation_to_organ(
    pk_model: Any,
    organ_model: Any,
    dt: float,
    organ_compartment: str = 'C_liver'
) -> Dict[str, float]:
    """
    Couple drug concentration from PK model to organ.

    Parameters
    ----------
    pk_model : PharmacokineticsModel
        Pharmacokinetics model
    organ_model : Any
        Organ model
    dt : float
        Time step
    organ_compartment : str
        PK compartment name

    Returns
    -------
    dict
        Inputs for organ model
    """
    # Get drug concentration from PK model
    if hasattr(pk_model, 'get_state'):
        state = pk_model.get_state()
        drug_conc = state.get(organ_compartment, 0.0)
    else:
        drug_conc = 0.0

    return {'drug_conc': drug_conc}


def organ_damage_to_immune(
    organ_model: Any,
    immune_model: Any,
    dt: float,
    damage_threshold: float = 0.1
) -> Dict[str, float]:
    """
    Couple organ damage to immune response.

    Parameters
    ----------
    organ_model : Any
        Organ model with damage state
    immune_model : Any
        Immune signaling model
    dt : float
        Time step
    damage_threshold : float
        Threshold for immune activation

    Returns
    -------
    dict
        Inputs for immune model
    """
    # Get damage level
    if hasattr(organ_model, 'get_state'):
        state = organ_model.get_state()
        damage = state.get('Damage', 0.0)
    else:
        damage = 0.0

    # Activate immune response if damage exceeds threshold
    if damage > damage_threshold:
        damage_signal = (damage - damage_threshold) * 10.0
    else:
        damage_signal = 0.0

    return {'external_stimulus': {'damage': damage_signal}}


def immune_to_organ_feedback(
    immune_model: Any,
    organ_model: Any,
    dt: float,
    sensitivity: float = 0.01
) -> Dict[str, float]:
    """
    Couple immune inflammation back to organ damage.

    Parameters
    ----------
    immune_model : Any
        Immune signaling model
    organ_model : Any
        Organ model
    dt : float
        Time step
    sensitivity : float
        Sensitivity to inflammatory signals

    Returns
    -------
    dict
        Additional damage from inflammation
    """
    # Get inflammatory index
    if hasattr(immune_model, 'get_state'):
        state = immune_model.get_state()
        inflammatory_index = state.get('inflammatory_index', 0.0)
    else:
        inflammatory_index = 0.0

    # Convert inflammation to additional damage
    # This would be applied as an additional term in organ dynamics
    damage_increment = sensitivity * inflammatory_index * dt

    return {'inflammation_damage': damage_increment}


def hepatic_clearance_to_pk(
    liver_model: Any,
    pk_model: Any,
    dt: float,
    viability_effect: bool = True
) -> Dict[str, float]:
    """
    Couple liver function to pharmacokinetic clearance.

    Parameters
    ----------
    liver_model : HepatocyteModel
        Liver model
    pk_model : PharmacokineticsModel
        PK model
    dt : float
        Time step
    viability_effect : bool
        Whether to modulate clearance by viability

    Returns
    -------
    dict
        Adjusted clearance parameters
    """
    if not viability_effect:
        return {}

    # Get liver viability
    if hasattr(liver_model, 'get_state'):
        state = liver_model.get_state()
        viability = state.get('viability', 1.0)
    else:
        viability = 1.0

    # Reduce clearance if liver is damaged
    # This would require modifying PK model clearance dynamically
    clearance_multiplier = viability

    return {'clearance_multiplier': clearance_multiplier}
