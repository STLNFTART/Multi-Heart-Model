"""
Integrated autonomic nervous system model.

This module provides a comprehensive model of autonomic cardiovascular
control, integrating:
- Baroreflex control
- Chemoreflex responses
- Central command (exercise, stress)
- Circadian variations

Based on neurovisceral integration theory (Thayer & Lane 2009).
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import math
from .baroreflex import BaroreflexController, BaroreflexParameters


@dataclass
class AutonomicState:
    """Current state of autonomic nervous system."""
    vagal_tone: float  # 0-1, higher = more parasympathetic activity
    sympathetic_tone: float  # 0-1, higher = more sympathetic activity
    baroreceptor_firing: float  # spikes/s
    heart_rate_effect: float  # bpm change from baseline
    contractility_effect: float  # fractional change in contractility
    vascular_resistance_effect: float  # fractional change in SVR


@dataclass
class AutonomicParameters:
    """Parameters for integrated autonomic nervous system."""

    # Baseline states (resting conditions)
    baseline_vagal_tone: float = 0.7  # Resting parasympathetic dominance
    baseline_sympathetic_tone: float = 0.3  # Resting sympathetic activity

    # Cardiac effects
    max_vagal_hr_effect: float = -30.0  # bpm - maximum HR decrease
    max_sympathetic_hr_effect: float = 60.0  # bpm - maximum HR increase
    max_sympathetic_contractility: float = 2.0  # fold increase in contractility

    # Vascular effects
    max_sympathetic_vasoconstriction: float = 3.0  # fold increase in SVR
    min_vasodilation: float = 0.3  # minimum SVR (maximal dilation)

    # Time constants
    vagal_time_constant: float = 0.5  # seconds - fast
    sympathetic_time_constant: float = 2.0  # seconds - slow
    vascular_time_constant: float = 5.0  # seconds - very slow

    # Central command gain (exercise, stress)
    central_command_gain: float = 1.0

    # Chemoreflex gain (hypoxia, hypercapnia)
    chemoreflex_gain: float = 0.5


class AutonomicNervousSystem:
    """
    Comprehensive autonomic nervous system model.

    Integrates multiple reflex arcs and central control mechanisms
    to provide realistic autonomic modulation of cardiovascular function.
    """

    def __init__(
        self,
        params: AutonomicParameters = None,
        baroreflex_params: BaroreflexParameters = None,
    ):
        """
        Initialize autonomic nervous system.

        Args:
            params: Autonomic system parameters
            baroreflex_params: Baroreflex-specific parameters
        """
        self.params = params or AutonomicParameters()
        self.baroreflex = BaroreflexController(baroreflex_params)

        # Current state
        self.state = AutonomicState(
            vagal_tone=self.params.baseline_vagal_tone,
            sympathetic_tone=self.params.baseline_sympathetic_tone,
            baroreceptor_firing=0.0,
            heart_rate_effect=0.0,
            contractility_effect=1.0,
            vascular_resistance_effect=1.0,
        )

        # Internal variables for temporal integration
        self._vagal_level = self.params.baseline_vagal_tone
        self._sympathetic_level = self.params.baseline_sympathetic_tone

    def update(
        self,
        pressure: float,
        dt: float,
        t: float,
        central_command: float = 0.0,
        chemoreflex_stimulus: float = 0.0,
    ) -> AutonomicState:
        """
        Update autonomic state based on inputs.

        Args:
            pressure: Mean arterial pressure (mmHg)
            dt: Time step (seconds)
            t: Current time (seconds)
            central_command: Central command input (0-1, e.g., exercise)
            chemoreflex_stimulus: Chemoreflex input (0-1, hypoxia/hypercapnia)

        Returns:
            Updated autonomic state
        """
        # 1. Baroreflex contribution
        vagal_baroreflex, sympathetic_baroreflex = (
            self.baroreflex.compute_autonomic_output(pressure, dt, t)
        )

        # 2. Central command contribution
        # Increases sympathetic, decreases vagal (exercise response)
        vagal_central = -central_command * self.params.central_command_gain
        sympathetic_central = central_command * self.params.central_command_gain

        # 3. Chemoreflex contribution
        # Hypoxia/hypercapnia increases sympathetic
        sympathetic_chemo = chemoreflex_stimulus * self.params.chemoreflex_gain

        # 4. Integrate contributions
        target_vagal = (
            vagal_baroreflex +
            vagal_central +
            self.params.baseline_vagal_tone
        )
        target_sympathetic = (
            sympathetic_baroreflex +
            sympathetic_central +
            sympathetic_chemo +
            self.params.baseline_sympathetic_tone
        )

        # Clamp to physiological range [0, 1]
        target_vagal = max(0.0, min(1.0, target_vagal))
        target_sympathetic = max(0.0, min(1.0, target_sympathetic))

        # 5. Apply time constants (first-order dynamics)
        alpha_vagal = dt / self.params.vagal_time_constant
        alpha_sympathetic = dt / self.params.sympathetic_time_constant

        self._vagal_level += alpha_vagal * (target_vagal - self._vagal_level)
        self._sympathetic_level += alpha_sympathetic * (
            target_sympathetic - self._sympathetic_level
        )

        # 6. Compute physiological effects

        # Heart rate effect
        hr_effect_vagal = self.params.max_vagal_hr_effect * self._vagal_level
        hr_effect_sympathetic = (
            self.params.max_sympathetic_hr_effect * self._sympathetic_level
        )
        total_hr_effect = hr_effect_vagal + hr_effect_sympathetic

        # Contractility effect (sympathetic only)
        # Ranges from 1.0 (baseline) to max_sympathetic_contractility
        contractility_effect = 1.0 + (
            (self.params.max_sympathetic_contractility - 1.0) *
            self._sympathetic_level
        )

        # Vascular resistance effect (sympathetic only)
        # Apply slower time constant for vascular smooth muscle
        alpha_vascular = dt / self.params.vascular_time_constant
        target_svr_effect = 1.0 + (
            (self.params.max_sympathetic_vasoconstriction - 1.0) *
            self._sympathetic_level
        )

        current_svr = self.state.vascular_resistance_effect
        new_svr = current_svr + alpha_vascular * (target_svr_effect - current_svr)

        # Update state
        self.state = AutonomicState(
            vagal_tone=self._vagal_level,
            sympathetic_tone=self._sympathetic_level,
            baroreceptor_firing=self.baroreflex.baroreceptor.compute_firing_rate(pressure, dt),
            heart_rate_effect=total_hr_effect,
            contractility_effect=contractility_effect,
            vascular_resistance_effect=new_svr,
        )

        return self.state

    def get_heart_rate(self, intrinsic_hr: float = 105.0) -> float:
        """
        Compute actual heart rate given intrinsic rate.

        Args:
            intrinsic_hr: Intrinsic (denervated) heart rate (bpm)
                         Default 105 bpm from Jose & Collison (1970)

        Returns:
            Actual heart rate (bpm)
        """
        hr = intrinsic_hr + self.state.heart_rate_effect

        # Physiological limits
        return max(30.0, min(220.0, hr))

    def get_contractility_multiplier(self) -> float:
        """
        Get contractility multiplier for cardiac model.

        Returns:
            Contractility scaling factor (1.0 = baseline)
        """
        return self.state.contractility_effect

    def get_svr_multiplier(self) -> float:
        """
        Get systemic vascular resistance multiplier.

        Returns:
            SVR scaling factor (1.0 = baseline)
        """
        return self.state.vascular_resistance_effect

    def simulate_valsalva_maneuver(
        self,
        duration: float = 15.0,
        strain_duration: float = 10.0,
        strain_pressure: float = 40.0,  # mmHg increase in intrathoracic pressure
        dt: float = 0.001,
    ) -> dict:
        """
        Simulate Valsalva maneuver and autonomic response.

        The Valsalva maneuver has 4 phases:
        1. Onset of strain: BP increases briefly
        2. Continued strain: BP decreases, HR increases (baroreflex)
        3. Release: BP drops further
        4. Recovery: BP overshoots, HR decreases

        Args:
            duration: Total simulation duration (seconds)
            strain_duration: Duration of strain phase (seconds)
            strain_pressure: Intrathoracic pressure increase (mmHg)
            dt: Time step

        Returns:
            Dictionary with time series
        """
        results = {
            'time': [],
            'pressure': [],
            'heart_rate': [],
            'vagal_tone': [],
            'sympathetic_tone': [],
            'phase': [],
        }

        baseline_pressure = 93.0  # mmHg
        intrinsic_hr = 105.0  # bpm

        t = 0.0
        while t < duration:
            # Determine Valsalva phase
            if t < 1.0:
                # Phase 1: Onset
                pressure = baseline_pressure + strain_pressure * (t / 1.0)
                phase = 1
            elif t < strain_duration:
                # Phase 2: Continued strain
                # Venous return decreases → CO decreases → BP decreases
                time_in_phase = t - 1.0
                pressure_drop = 20.0 * (1.0 - math.exp(-time_in_phase / 2.0))
                pressure = baseline_pressure + strain_pressure - pressure_drop
                phase = 2
            elif t < strain_duration + 2.0:
                # Phase 3: Release
                time_since_release = t - strain_duration
                pressure = baseline_pressure - 30.0 * math.exp(-time_since_release / 0.5)
                phase = 3
            else:
                # Phase 4: Recovery overshoot
                time_in_recovery = t - strain_duration - 2.0
                overshoot = 25.0 * math.exp(-time_in_recovery / 3.0)
                pressure = baseline_pressure + overshoot
                phase = 4

            # Update autonomic system
            state = self.update(pressure, dt, t)
            hr = self.get_heart_rate(intrinsic_hr)

            # Store results
            results['time'].append(t)
            results['pressure'].append(pressure)
            results['heart_rate'].append(hr)
            results['vagal_tone'].append(state.vagal_tone)
            results['sympathetic_tone'].append(state.sympathetic_tone)
            results['phase'].append(phase)

            t += dt

        return results

    def simulate_orthostatic_stress(
        self,
        duration: float = 60.0,
        tilt_time: float = 5.0,
        pressure_drop: float = 20.0,  # mmHg
        dt: float = 0.001,
    ) -> dict:
        """
        Simulate orthostatic stress (tilt table test) and compensation.

        Args:
            duration: Total duration (seconds)
            tilt_time: Time point of tilt (seconds)
            pressure_drop: Initial pressure drop from venous pooling (mmHg)
            dt: Time step

        Returns:
            Dictionary with time series
        """
        results = {
            'time': [],
            'pressure': [],
            'heart_rate': [],
            'vagal_tone': [],
            'sympathetic_tone': [],
            'svr_multiplier': [],
        }

        baseline_pressure = 93.0
        intrinsic_hr = 105.0

        t = 0.0
        while t < duration:
            if t < tilt_time:
                # Supine
                pressure = baseline_pressure
            else:
                # Upright - venous pooling causes pressure drop
                time_since_tilt = t - tilt_time

                # Initial drop with partial compensation
                compensation = 1.0 - math.exp(-time_since_tilt / 5.0)
                pressure = baseline_pressure - pressure_drop * (1.0 - 0.7 * compensation)

            state = self.update(pressure, dt, t)
            hr = self.get_heart_rate(intrinsic_hr)
            svr = self.get_svr_multiplier()

            results['time'].append(t)
            results['pressure'].append(pressure)
            results['heart_rate'].append(hr)
            results['vagal_tone'].append(state.vagal_tone)
            results['sympathetic_tone'].append(state.sympathetic_tone)
            results['svr_multiplier'].append(svr)

            t += dt

        return results

    def reset(self):
        """Reset autonomic system to baseline state."""
        self._vagal_level = self.params.baseline_vagal_tone
        self._sympathetic_level = self.params.baseline_sympathetic_tone
        self.state = AutonomicState(
            vagal_tone=self.params.baseline_vagal_tone,
            sympathetic_tone=self.params.baseline_sympathetic_tone,
            baroreceptor_firing=0.0,
            heart_rate_effect=0.0,
            contractility_effect=1.0,
            vascular_resistance_effect=1.0,
        )
        self.baroreflex.baroreceptor.reset_adaptation()
