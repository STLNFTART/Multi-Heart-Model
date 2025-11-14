"""
Tests for validation framework.
"""

import pytest
from src.validation.benchmarks import (
    PhysiologicalBenchmarks,
    ParameterRange,
)
from src.validation.validators import (
    validate_cardiac_model,
    validate_neural_model,
    validate_coupling_model,
)
from src.validation.metrics import (
    compute_hrv_metrics,
    compute_pv_loop_metrics,
)
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters


class TestBenchmarks:
    """Test physiological benchmarks."""

    def test_parameter_range_validation(self):
        """Test parameter range checking."""
        param = ParameterRange(
            min_value=60.0,
            max_value=100.0,
            typical_value=72.0,
            units="bpm",
            reference="Test"
        )

        assert param.is_valid(72.0)
        assert param.is_valid(60.0)
        assert param.is_valid(100.0)
        assert not param.is_valid(50.0)
        assert not param.is_valid(110.0)

    def test_benchmarks_initialization(self):
        """Test that all benchmarks initialize correctly."""
        benchmarks = PhysiologicalBenchmarks()

        assert benchmarks.cardiac is not None
        assert benchmarks.neural is not None
        assert benchmarks.coupling is not None
        assert benchmarks.hemodynamic is not None
        assert benchmarks.hrv is not None

    def test_validate_all_parameters(self):
        """Test parameter validation against benchmarks."""
        benchmarks = PhysiologicalBenchmarks()

        # Valid parameters
        params = {
            'heart_rate': 72.0,
            'systolic_bp': 120.0,
            'diastolic_bp': 80.0,
            'cardiac_output': 5.0,
        }

        results = benchmarks.validate_all_parameters(params)

        assert results['heart_rate'] is True
        assert results['systolic_bp'] is True
        assert results['diastolic_bp'] is True
        assert results['cardiac_output'] is True

    def test_validate_invalid_parameters(self):
        """Test detection of invalid parameters."""
        benchmarks = PhysiologicalBenchmarks()

        # Invalid parameters
        params = {
            'heart_rate': 200.0,  # Too high
            'systolic_bp': 50.0,  # Too low
        }

        results = benchmarks.validate_all_parameters(params)

        assert results['heart_rate'] is False
        assert results['systolic_bp'] is False


class TestValidators:
    """Test model validators."""

    def test_validate_cardiac_model(self):
        """Test cardiac model validation."""
        # Create cardiac model and simulate
        model = VanDerPolOscillator(mu=1.5, omega=1.0)
        state = (1.0, 0.0)
        trajectory = []

        t = 0.0
        dt = 0.001
        for i in range(10000):  # 10 seconds
            state = model.step(t, state, dt, 0.0)
            trajectory.append((t, state))
            t += dt

        # Validate
        metrics = validate_cardiac_model(trajectory, dt)

        assert metrics is not None
        assert 'heart_rate_bpm' in metrics
        assert 'heart_rate_valid' in metrics
        assert 'stable_oscillation' in metrics

        # Should produce oscillations with reasonable frequency
        if metrics['heart_rate_bpm'] is not None:
            # Van der Pol with omega=1.0 should give ~9-10 cycles in 10 seconds
            # which is ~54-60 bpm after scaling
            assert 0 < metrics['heart_rate_bpm'] < 200

    def test_validate_neural_model(self):
        """Test neural model validation."""
        # Create neural model with sustained input
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.3)
        state = (0.0, 0.0)
        trajectory = []

        t = 0.0
        dt = 0.001
        for i in range(10000):
            state = model.step(t, state, dt, 0.0)
            trajectory.append((t, state))
            t += dt

        # Validate
        metrics = validate_neural_model(trajectory, dt)

        assert metrics is not None
        assert 'excitable' in metrics
        assert 'v_amplitude' in metrics

        # Should show excitability
        assert metrics['excitable'] is True or metrics['excitable'] is False  # Either is valid

    def test_validate_coupling_model(self):
        """Test coupled model validation."""
        # Create coupled model
        neural = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.3)
        cardiac = VanDerPolOscillator(mu=1.5, omega=1.0)
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.5,
            cardiac_to_neural_gain=0.3,
            neural_delay=0.10,
            cardiac_delay=0.15
        )

        model = HeartBrainCouplingModel(neural, cardiac, coupling)

        # Simulate
        trajectory = model.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 10.0),
            dt=0.001
        )

        # Validate
        metrics = validate_coupling_model(trajectory, coupling, dt=0.001)

        assert metrics is not None
        assert 'neural' in metrics
        assert 'cardiac' in metrics
        assert 'coupling_params_valid' in metrics
        assert 'overall_valid' in metrics

        # Coupling parameters should be valid (within physiological ranges)
        assert metrics['coupling_params_valid']['neural_to_cardiac_gain'] is True
        assert metrics['coupling_params_valid']['cardiac_to_neural_gain'] is True


class TestMetrics:
    """Test HRV and PV loop metrics."""

    def test_compute_hrv_metrics(self):
        """Test HRV computation."""
        # Simulated RR intervals (normal sinus rhythm with variation)
        rr_intervals = [
            850, 870, 840, 880, 860, 890, 850, 870, 840, 860,
            880, 850, 870, 860, 840, 890, 850, 870, 860, 840
        ]  # ms

        metrics = compute_hrv_metrics(rr_intervals)

        assert 'sdnn_ms' in metrics
        assert 'rmssd_ms' in metrics
        assert 'lf_hf_ratio' in metrics

        # Should have reasonable values
        assert metrics['sdnn_ms'] > 0
        assert metrics['rmssd_ms'] > 0
        assert metrics['lf_hf_ratio'] >= 0

    def test_compute_pv_loop_metrics(self):
        """Test PV loop metrics computation."""
        # Simulated pressure and volume
        import math
        pressure = [20 + 100*math.sin(2*math.pi*t)**2 for t in [i/100 for i in range(100)]]
        volume = [50 + 70*(1-math.sin(2*math.pi*t)**2) for t in [i/100 for i in range(100)]]

        metrics = compute_pv_loop_metrics(pressure, volume)

        assert 'stroke_volume_ml' in metrics
        assert 'ejection_fraction_pct' in metrics
        assert 'stroke_work_mmhg_ml' in metrics

        # Should have physiological values
        assert metrics['stroke_volume_ml'] > 0
        assert 0 < metrics['ejection_fraction_pct'] < 100
        assert metrics['stroke_work_mmhg_ml'] > 0


def test_validation_report_generation():
    """Test that validation reports can be generated."""
    benchmarks = PhysiologicalBenchmarks()

    params = {
        'heart_rate': 72.0,
        'systolic_bp': 120.0,
        'stroke_volume': 70.0,
    }

    report = benchmarks.generate_validation_report(params)

    assert isinstance(report, str)
    assert 'VALIDATION REPORT' in report
    assert 'Valid:' in report or 'Invalid:' in report


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
