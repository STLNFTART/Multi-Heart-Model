"""
Tests for Physiological Controller
"""

import pytest
import numpy as np
from src.surgical_robotics import (
    PhysiologicalController,
    SurgicalFeedbackState,
    PhysiologicalConstraints,
    SurgicalPhase,
    PhysiologicalAlertLevel,
)


@pytest.fixture
def physio_controller():
    """Create physiological controller instance"""
    return PhysiologicalController(
        baseline_heart_rate=70.0,
        baseline_blood_pressure=90.0
    )


def test_controller_initialization(physio_controller):
    """Test controller initialization"""
    assert physio_controller is not None
    assert physio_controller.baseline_hr == 70.0
    assert physio_controller.baseline_bp == 90.0


def test_surgical_phase_setting(physio_controller):
    """Test setting surgical phase"""
    physio_controller.set_surgical_phase(SurgicalPhase.APPROACH)
    assert physio_controller.current_phase == SurgicalPhase.APPROACH


def test_physiological_state_stability():
    """Test physiological state stability check"""
    # Stable state
    stable_state = SurgicalFeedbackState(
        heart_rate=75.0,
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
    )
    assert stable_state.is_stable() is True

    # Unstable state (high HR)
    unstable_state = SurgicalFeedbackState(
        heart_rate=125.0,
        blood_pressure_systolic=120.0,
        blood_pressure_diastolic=80.0,
        cardiac_output=5.0,
        stroke_volume=70.0,
        respiratory_rate=16.0,
        oxygen_saturation=98.0,
        end_tidal_co2=38.0,
        bispectral_index=45.0,
        pupil_diameter=3.5,
        mean_arterial_pressure=0.0,
        stress_index=0.2,
        pain_index=0.1,
    )
    assert unstable_state.is_stable() is False


def test_alert_level_determination():
    """Test alert level computation"""
    # Normal state
    normal_state = SurgicalFeedbackState(
        heart_rate=75.0,
        blood_pressure_systolic=120.0,
        blood_pressure_diastolic=80.0,
        cardiac_output=5.0,
        stroke_volume=70.0,
        respiratory_rate=16.0,
        oxygen_saturation=98.0,
        end_tidal_co2=38.0,
        bispectral_index=45.0,
        pupil_diameter=3.5,
        mean_arterial_pressure=0.0,
        stress_index=0.2,
        pain_index=0.1,
    )
    assert normal_state.get_alert_level() == PhysiologicalAlertLevel.NORMAL

    # Critical state
    critical_state = SurgicalFeedbackState(
        heart_rate=160.0,  # Severe tachycardia
        blood_pressure_systolic=70.0,  # Hypotension
        blood_pressure_diastolic=50.0,
        cardiac_output=3.0,
        stroke_volume=50.0,
        respiratory_rate=30.0,
        oxygen_saturation=82.0,  # Severe hypoxemia
        end_tidal_co2=45.0,
        bispectral_index=15.0,  # Very deep anesthesia
        pupil_diameter=2.0,
        mean_arterial_pressure=0.0,
        stress_index=0.8,
        pain_index=0.1,
    )
    assert critical_state.get_alert_level() == PhysiologicalAlertLevel.CRITICAL


def test_control_constraints_normal(physio_controller):
    """Test control constraints for normal state"""
    # Get normal state
    physio_state = physio_controller.get_physiological_feedback()

    # Compute constraints
    constraints = physio_controller.compute_control_constraints(physio_state)

    assert 0.5 <= constraints.max_velocity_scale <= 1.0
    assert 0.5 <= constraints.max_force_scale <= 1.0
    assert constraints.emergency_stop is False


def test_control_constraints_critical(physio_controller):
    """Test control constraints for critical state"""
    # Create critical state
    critical_data = {
        'heart_rate': 160.0,
        'bp_systolic': 70.0,
        'bp_diastolic': 50.0,
        'spo2': 82.0,
        'stress': 0.9,
    }

    physio_state = physio_controller.get_physiological_feedback(critical_data)
    constraints = physio_controller.compute_control_constraints(physio_state)

    assert constraints.max_velocity_scale == 0.0
    assert constraints.max_force_scale == 0.0
    assert constraints.emergency_stop is True


def test_hrv_metrics_computation(physio_controller):
    """Test HRV metrics computation"""
    # Generate some physiological states
    for _ in range(20):
        physio_controller.get_physiological_feedback()

    # Compute HRV
    hrv_metrics = physio_controller.compute_hrv_metrics(duration_seconds=60.0)

    assert 'sdnn' in hrv_metrics
    assert 'rmssd' in hrv_metrics
    assert 'mean_hr' in hrv_metrics
    assert hrv_metrics['sdnn'] >= 0.0
    assert hrv_metrics['rmssd'] >= 0.0


def test_physio_history(physio_controller):
    """Test physiological state history"""
    # Generate states
    for _ in range(10):
        physio_controller.get_physiological_feedback()

    # Get history
    history = physio_controller.get_physio_history()
    assert len(history) == 10

    # Get recent history
    recent = physio_controller.get_physio_history(duration_seconds=1.0)
    assert len(recent) <= len(history)
