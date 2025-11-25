"""
Physiological Controller for Surgical Robotics

Integrates Multi-Heart-Model physiological simulations with surgical
robotics control systems. Provides physiologically-aware robot control
that adapts to patient state.

This module bridges:
- Heart-Brain Coupling Model (HBCM) physiological simulation
- Surgical robot control (dVRK, CRTK, AMBF)
- Real-time adaptation based on physiological feedback
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List
from enum import Enum
import time


class SurgicalPhase(Enum):
    """Phases of surgical procedure"""
    IDLE = "IDLE"
    APPROACH = "APPROACH"
    MANIPULATION = "MANIPULATION"
    RETRACTION = "RETRACTION"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class PhysiologicalAlertLevel(Enum):
    """Alert levels based on physiological state"""
    NORMAL = 0
    CAUTION = 1
    WARNING = 2
    CRITICAL = 3


@dataclass
class SurgicalFeedbackState:
    """
    Complete physiological feedback state during surgery

    Based on standard patient monitoring metrics
    """
    # Cardiovascular
    heart_rate: float  # bpm
    blood_pressure_systolic: float  # mmHg
    blood_pressure_diastolic: float  # mmHg
    cardiac_output: float  # L/min
    stroke_volume: float  # mL

    # Respiratory
    respiratory_rate: float  # breaths/min
    oxygen_saturation: float  # % (SpO2)
    end_tidal_co2: float  # mmHg

    # Neurological
    bispectral_index: float  # BIS (0-100, anesthesia depth)
    pupil_diameter: float  # mm

    # Derived metrics
    mean_arterial_pressure: float  # mmHg
    stress_index: float  # 0-1 normalized
    pain_index: float  # 0-1 normalized

    # Metadata
    timestamp: float = 0.0
    alert_level: PhysiologicalAlertLevel = PhysiologicalAlertLevel.NORMAL

    def __post_init__(self):
        # Compute MAP if not set
        if self.mean_arterial_pressure == 0:
            self.mean_arterial_pressure = (
                self.blood_pressure_diastolic +
                (self.blood_pressure_systolic - self.blood_pressure_diastolic) / 3
            )

    def is_stable(self) -> bool:
        """Check if physiological state is stable"""
        return (
            60 <= self.heart_rate <= 100 and
            90 <= self.blood_pressure_systolic <= 140 and
            60 <= self.blood_pressure_diastolic <= 90 and
            94 <= self.oxygen_saturation <= 100 and
            12 <= self.respiratory_rate <= 20
        )

    def get_alert_level(self) -> PhysiologicalAlertLevel:
        """Determine alert level based on vitals"""
        critical_flags = [
            self.heart_rate > 150 or self.heart_rate < 40,
            self.blood_pressure_systolic > 180 or self.blood_pressure_systolic < 80,
            self.oxygen_saturation < 85,
            self.bispectral_index < 20,
        ]

        warning_flags = [
            self.heart_rate > 120 or self.heart_rate < 50,
            self.blood_pressure_systolic > 160 or self.blood_pressure_systolic < 90,
            self.oxygen_saturation < 90,
            self.respiratory_rate > 25 or self.respiratory_rate < 8,
        ]

        caution_flags = [
            self.heart_rate > 100 or self.heart_rate < 60,
            self.blood_pressure_systolic > 140 or self.blood_pressure_systolic < 100,
            self.oxygen_saturation < 94,
        ]

        if any(critical_flags):
            return PhysiologicalAlertLevel.CRITICAL
        elif any(warning_flags):
            return PhysiologicalAlertLevel.WARNING
        elif any(caution_flags):
            return PhysiologicalAlertLevel.CAUTION
        else:
            return PhysiologicalAlertLevel.NORMAL


@dataclass
class PhysiologicalConstraints:
    """
    Safety constraints for robot control based on physiology

    These limits are automatically adjusted based on patient state
    """
    # Velocity limits (scale factors, 0-1)
    max_velocity_scale: float = 1.0
    max_acceleration_scale: float = 1.0

    # Force limits (scale factors, 0-1)
    max_force_scale: float = 1.0
    max_torque_scale: float = 1.0

    # Safety margins
    workspace_margin: float = 0.0  # Additional margin from workspace boundary (meters)
    collision_threshold: float = 0.05  # Minimum distance to obstacles (meters)

    # Pause/stop conditions
    pause_required: bool = False
    emergency_stop: bool = False

    # Explanation
    constraint_reason: str = "Normal operation"


class PhysiologicalController:
    """
    Physiologically-aware surgical robot controller

    Integrates Multi-Heart-Model HBCM simulation with surgical robot control
    to provide adaptive, physiologically-aware robot behavior.

    Key features:
    - Real-time physiological monitoring integration
    - Adaptive control parameter modulation
    - Safety constraint enforcement
    - Multi-level alerting system

    Example usage:
        >>> from src.cardiac import VanDerPolOscillator
        >>> from src.neural import FitzHughNagumo
        >>> from src.coupling import HeartBrainCouplingModel
        >>>
        >>> # Create physiological model
        >>> hbcm = HeartBrainCouplingModel(
        ...     neural_model=FitzHughNagumo(),
        ...     cardiac_model=VanDerPolOscillator()
        ... )
        >>>
        >>> # Create controller
        >>> controller = PhysiologicalController(hbcm_model=hbcm)
        >>>
        >>> # Get current physiological state
        >>> physio_state = controller.get_physiological_feedback()
        >>>
        >>> # Compute robot control constraints
        >>> constraints = controller.compute_control_constraints(physio_state)
        >>>
        >>> # Apply to robot (example with dVRK)
        >>> from src.surgical_robotics import DVRKInterface
        >>> dvrk = DVRKInterface(config)
        >>> velocity_scale = constraints.max_velocity_scale
        >>> # ... apply scaling to robot commands
    """

    def __init__(
        self,
        hbcm_model=None,
        baseline_heart_rate: float = 70.0,
        baseline_blood_pressure: float = 90.0
    ):
        """
        Initialize physiological controller

        Args:
            hbcm_model: HeartBrainCouplingModel instance (optional)
            baseline_heart_rate: Baseline HR for comparison
            baseline_blood_pressure: Baseline MAP for comparison
        """
        self.hbcm_model = hbcm_model

        # Baseline values
        self.baseline_hr = baseline_heart_rate
        self.baseline_bp = baseline_blood_pressure

        # Current state
        self.current_phase = SurgicalPhase.IDLE
        self.current_physio_state: Optional[SurgicalFeedbackState] = None

        # History
        self.physio_history: List[SurgicalFeedbackState] = []
        self.constraint_history: List[PhysiologicalConstraints] = []

        # Configuration
        self.enable_adaptive_control = True
        self.enable_emergency_stop = True

        print("Physiological Controller initialized")
        print(f"  Baseline HR: {baseline_heart_rate} bpm")
        print(f"  Baseline BP: {baseline_blood_pressure} mmHg")

    def set_surgical_phase(self, phase: SurgicalPhase):
        """Set current surgical phase"""
        print(f"Surgical phase: {self.current_phase.value} -> {phase.value}")
        self.current_phase = phase

    def get_physiological_feedback(
        self,
        measured_data: Optional[Dict] = None
    ) -> SurgicalFeedbackState:
        """
        Get current physiological feedback state

        Args:
            measured_data: Optional measured patient data

        Returns:
            Complete physiological feedback state
        """
        if measured_data:
            # Use measured data from patient monitors
            state = SurgicalFeedbackState(
                heart_rate=measured_data.get('heart_rate', 70.0),
                blood_pressure_systolic=measured_data.get('bp_systolic', 120.0),
                blood_pressure_diastolic=measured_data.get('bp_diastolic', 80.0),
                cardiac_output=measured_data.get('cardiac_output', 5.0),
                stroke_volume=measured_data.get('stroke_volume', 70.0),
                respiratory_rate=measured_data.get('resp_rate', 16.0),
                oxygen_saturation=measured_data.get('spo2', 98.0),
                end_tidal_co2=measured_data.get('etco2', 38.0),
                bispectral_index=measured_data.get('bis', 45.0),
                pupil_diameter=measured_data.get('pupil', 3.5),
                mean_arterial_pressure=0.0,  # Will be computed
                stress_index=measured_data.get('stress', 0.0),
                pain_index=measured_data.get('pain', 0.0),
                timestamp=time.time(),
            )
        else:
            # Use simulated data from HBCM model
            if self.hbcm_model:
                # Extract from HBCM simulation
                # This would require running HBCM.step() or simulate()
                # For now, use placeholder values
                state = self._simulate_physiological_state()
            else:
                # Default stable state
                state = self._get_default_state()

        # Compute alert level
        state.alert_level = state.get_alert_level()

        # Store in history
        self.current_physio_state = state
        self.physio_history.append(state)

        return state

    def compute_control_constraints(
        self,
        physio_state: SurgicalFeedbackState
    ) -> PhysiologicalConstraints:
        """
        Compute robot control constraints based on physiological state

        Modulates control parameters to ensure patient safety

        Args:
            physio_state: Current physiological state

        Returns:
            Control constraints
        """
        # Initialize with no constraints
        constraints = PhysiologicalConstraints()

        # Check alert level
        alert_level = physio_state.alert_level

        if alert_level == PhysiologicalAlertLevel.CRITICAL:
            # Critical state - emergency stop
            constraints.max_velocity_scale = 0.0
            constraints.max_force_scale = 0.0
            constraints.emergency_stop = True
            constraints.constraint_reason = "CRITICAL physiological state - emergency stop"
            return constraints

        elif alert_level == PhysiologicalAlertLevel.WARNING:
            # Warning state - major slowdown
            constraints.max_velocity_scale = 0.3
            constraints.max_acceleration_scale = 0.4
            constraints.max_force_scale = 0.5
            constraints.workspace_margin = 0.02  # 2cm additional margin
            constraints.pause_required = True
            constraints.constraint_reason = "WARNING physiological state - reduced control"

        elif alert_level == PhysiologicalAlertLevel.CAUTION:
            # Caution state - moderate slowdown
            constraints.max_velocity_scale = 0.6
            constraints.max_acceleration_scale = 0.7
            constraints.max_force_scale = 0.8
            constraints.workspace_margin = 0.01
            constraints.constraint_reason = "CAUTION physiological state"

        else:
            # Normal state - fine-tune based on specific vitals
            constraints = self._compute_normal_constraints(physio_state)

        # Store in history
        self.constraint_history.append(constraints)

        return constraints

    def _compute_normal_constraints(
        self,
        physio_state: SurgicalFeedbackState
    ) -> PhysiologicalConstraints:
        """
        Compute constraints for normal physiological state

        Fine-tunes based on individual vital signs
        """
        constraints = PhysiologicalConstraints(
            constraint_reason="Normal operation with adaptive scaling"
        )

        # Modulate based on heart rate
        hr_deviation = abs(physio_state.heart_rate - self.baseline_hr)
        if hr_deviation > 20:
            constraints.max_velocity_scale *= 0.8
        elif hr_deviation > 10:
            constraints.max_velocity_scale *= 0.9

        # Modulate based on blood pressure
        bp_deviation = abs(physio_state.mean_arterial_pressure - self.baseline_bp)
        if bp_deviation > 15:
            constraints.max_force_scale *= 0.8
        elif bp_deviation > 10:
            constraints.max_force_scale *= 0.9

        # Modulate based on stress index
        if physio_state.stress_index > 0.5:
            constraints.max_velocity_scale *= (1.0 - 0.3 * physio_state.stress_index)
            constraints.max_acceleration_scale *= (1.0 - 0.2 * physio_state.stress_index)

        # Modulate based on pain index
        if physio_state.pain_index > 0.5:
            constraints.max_force_scale *= (1.0 - 0.4 * physio_state.pain_index)

        # Surgical phase considerations
        if self.current_phase == SurgicalPhase.APPROACH:
            # Slower during approach
            constraints.max_velocity_scale *= 0.7
            constraints.collision_threshold = 0.08  # 8cm

        elif self.current_phase == SurgicalPhase.MANIPULATION:
            # Finer control during manipulation
            constraints.max_velocity_scale *= 0.5
            constraints.max_force_scale *= 0.7
            constraints.collision_threshold = 0.10  # 10cm

        return constraints

    def _simulate_physiological_state(self) -> SurgicalFeedbackState:
        """
        Simulate physiological state from HBCM model

        Extracts heart rate and estimates other vitals
        """
        # This would integrate with HBCM simulation
        # For now, return simulated values

        # Simulate with some variation
        hr = self.baseline_hr + np.random.normal(0, 5)
        bp_sys = 120 + np.random.normal(0, 8)
        bp_dia = 80 + np.random.normal(0, 5)

        return SurgicalFeedbackState(
            heart_rate=hr,
            blood_pressure_systolic=bp_sys,
            blood_pressure_diastolic=bp_dia,
            cardiac_output=5.0 + np.random.normal(0, 0.5),
            stroke_volume=70.0 + np.random.normal(0, 5),
            respiratory_rate=16.0 + np.random.normal(0, 2),
            oxygen_saturation=98.0 + np.random.normal(0, 1),
            end_tidal_co2=38.0 + np.random.normal(0, 2),
            bispectral_index=45.0 + np.random.normal(0, 5),
            pupil_diameter=3.5 + np.random.normal(0, 0.3),
            mean_arterial_pressure=0.0,
            stress_index=0.2 + 0.1 * np.random.random(),
            pain_index=0.1 + 0.05 * np.random.random(),
            timestamp=time.time(),
        )

    def _get_default_state(self) -> SurgicalFeedbackState:
        """Get default stable physiological state"""
        return SurgicalFeedbackState(
            heart_rate=70.0,
            blood_pressure_systolic=120.0,
            blood_pressure_diastolic=80.0,
            cardiac_output=5.0,
            stroke_volume=70.0,
            respiratory_rate=16.0,
            oxygen_saturation=98.0,
            end_tidal_co2=38.0,
            bispectral_index=45.0,
            pupil_diameter=3.5,
            mean_arterial_pressure=93.3,
            stress_index=0.2,
            pain_index=0.1,
            timestamp=time.time(),
        )

    def get_physio_history(
        self,
        duration_seconds: Optional[float] = None
    ) -> List[SurgicalFeedbackState]:
        """
        Get physiological state history

        Args:
            duration_seconds: Return history for last N seconds (None = all)

        Returns:
            List of physiological states
        """
        if duration_seconds is None:
            return self.physio_history

        cutoff_time = time.time() - duration_seconds
        return [
            state for state in self.physio_history
            if state.timestamp >= cutoff_time
        ]

    def compute_hrv_metrics(
        self,
        duration_seconds: float = 300.0
    ) -> Dict[str, float]:
        """
        Compute heart rate variability metrics

        Args:
            duration_seconds: Analysis window (default 5 minutes)

        Returns:
            HRV metrics dictionary
        """
        history = self.get_physio_history(duration_seconds)

        if len(history) < 2:
            return {'sdnn': 0.0, 'rmssd': 0.0, 'mean_hr': 0.0}

        # Extract RR intervals from heart rate
        heart_rates = np.array([state.heart_rate for state in history])
        rr_intervals = 60000.0 / heart_rates  # Convert HR (bpm) to RR (ms)

        # Compute metrics
        sdnn = np.std(rr_intervals)
        rmssd = np.sqrt(np.mean(np.diff(rr_intervals) ** 2))
        mean_hr = np.mean(heart_rates)

        return {
            'sdnn': float(sdnn),
            'rmssd': float(rmssd),
            'mean_hr': float(mean_hr),
            'samples': len(history),
        }


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("Physiological Controller for Surgical Robotics Demo")
    print("=" * 60)

    # Create controller
    controller = PhysiologicalController(
        baseline_heart_rate=70.0,
        baseline_blood_pressure=90.0
    )

    # Set surgical phase
    print("\n1. Setting surgical phase...")
    controller.set_surgical_phase(SurgicalPhase.APPROACH)

    # Get physiological state
    print("\n2. Getting physiological feedback...")
    physio_state = controller.get_physiological_feedback()
    print(f"   HR: {physio_state.heart_rate:.1f} bpm")
    print(f"   BP: {physio_state.blood_pressure_systolic:.0f}/{physio_state.blood_pressure_diastolic:.0f} mmHg")
    print(f"   SpO2: {physio_state.oxygen_saturation:.1f}%")
    print(f"   Alert level: {physio_state.alert_level.name}")

    # Compute control constraints
    print("\n3. Computing control constraints...")
    constraints = controller.compute_control_constraints(physio_state)
    print(f"   Velocity scale: {constraints.max_velocity_scale:.2f}")
    print(f"   Force scale: {constraints.max_force_scale:.2f}")
    print(f"   Reason: {constraints.constraint_reason}")

    # Simulate abnormal state
    print("\n4. Simulating WARNING state...")
    abnormal_data = {
        'heart_rate': 125.0,  # Tachycardia
        'bp_systolic': 165.0,  # Hypertension
        'bp_diastolic': 95.0,
        'spo2': 91.0,  # Low oxygen
        'stress': 0.7,
    }
    abnormal_state = controller.get_physiological_feedback(abnormal_data)
    abnormal_constraints = controller.compute_control_constraints(abnormal_state)
    print(f"   Alert level: {abnormal_state.alert_level.name}")
    print(f"   Velocity scale: {abnormal_constraints.max_velocity_scale:.2f}")
    print(f"   Pause required: {abnormal_constraints.pause_required}")

    # Simulate multiple states
    print("\n5. Simulating surgery progression...")
    for i in range(10):
        state = controller.get_physiological_feedback()
        constraints = controller.compute_control_constraints(state)
        if i % 3 == 0:
            print(f"   t={i}: HR={state.heart_rate:.0f}, velocity_scale={constraints.max_velocity_scale:.2f}")

    # Compute HRV metrics
    print("\n6. Computing HRV metrics...")
    hrv = controller.compute_hrv_metrics(duration_seconds=60.0)
    print(f"   SDNN: {hrv['sdnn']:.2f} ms")
    print(f"   RMSSD: {hrv['rmssd']:.2f} ms")
    print(f"   Mean HR: {hrv['mean_hr']:.1f} bpm")
    print(f"   Samples: {hrv['samples']}")

    print("\n" + "=" * 60)
    print("Physiological Controller demonstration complete!")
    print("=" * 60)
