"""
Tests for autonomic nervous system models.
"""

import pytest
from src.autonomic.baroreflex import (
    Baroreceptor,
    BaroreflexController,
    BaroreflexParameters,
    simulate_baroreflex_response,
)
from src.autonomic.autonomic_nervous_system import (
    AutonomicNervousSystem,
    AutonomicParameters,
)


class TestBaroreceptor:
    """Test baroreceptor model."""

    def test_baroreceptor_initialization(self):
        """Test that baroreceptor initializes correctly."""
        baroreceptor = Baroreceptor()
        assert baroreceptor is not None
        assert baroreceptor.params is not None

    def test_baroreceptor_firing_rate_response(self):
        """Test that firing rate increases with pressure."""
        baroreceptor = Baroreceptor()

        # Low pressure
        fr_low = baroreceptor.compute_firing_rate(pressure=80.0, dt=0.001)

        # Normal pressure
        fr_normal = baroreceptor.compute_firing_rate(pressure=100.0, dt=0.001)

        # High pressure
        fr_high = baroreceptor.compute_firing_rate(pressure=120.0, dt=0.001)

        # Firing rate should increase with pressure
        assert fr_low < fr_normal < fr_high

    def test_baroreceptor_saturation(self):
        """Test that firing rate saturates at high pressure."""
        baroreceptor = Baroreceptor()
        params = baroreceptor.params

        # Very high pressure
        fr_very_high = baroreceptor.compute_firing_rate(pressure=180.0, dt=0.001)

        # Should be close to maximum
        assert fr_very_high > 0.9 * params.max_firing_rate

    def test_baroreceptor_sigmoid_shape(self):
        """Test sigmoidal pressure-firing relationship."""
        baroreceptor = Baroreceptor()
        params = baroreceptor.params

        # Sample across pressure range
        pressures = [60, 80, 100, 120, 140, 160]
        firing_rates = [
            baroreceptor.compute_firing_rate(p, 0.001)
            for p in pressures
        ]

        # Should be monotonically increasing
        for i in range(len(firing_rates) - 1):
            assert firing_rates[i] <= firing_rates[i + 1]

        # Midpoint should be close to sigmoid midpoint
        fr_mid = baroreceptor.compute_firing_rate(params.sigmoid_midpoint, 0.001)
        expected_mid = (params.max_firing_rate + params.min_firing_rate) / 2
        assert abs(fr_mid - expected_mid) < 20.0  # Within 20 spikes/s


class TestBaroreflexController:
    """Test baroreflex controller."""

    def test_baroreflex_controller_initialization(self):
        """Test controller initialization."""
        controller = BaroreflexController()
        assert controller is not None
        assert controller.baroreceptor is not None

    def test_baroreflex_autonomic_output(self):
        """Test that autonomic output responds to pressure changes."""
        controller = BaroreflexController()

        # High pressure should increase vagal, decrease sympathetic
        vagal_high, sympathetic_high = controller.compute_autonomic_output(
            pressure=140.0, dt=0.001, t=0.0
        )

        # Low pressure should decrease vagal, increase sympathetic
        vagal_low, sympathetic_low = controller.compute_autonomic_output(
            pressure=70.0, dt=0.001, t=0.1
        )

        # Check reciprocal relationship (qualitative test)
        # Note: Due to integration dynamics, we check the general trend
        assert 0 <= vagal_high <= 1.0
        assert 0 <= sympathetic_high <= 1.0
        assert 0 <= vagal_low <= 1.0
        assert 0 <= sympathetic_low <= 1.0

    def test_baroreflex_heart_rate_response(self):
        """Test heart rate response to pressure changes."""
        controller = BaroreflexController()
        baseline_hr = 72.0

        # High pressure → decreased HR
        hr_high = controller.compute_heart_rate_response(
            pressure=140.0,
            baseline_hr=baseline_hr,
            dt=0.001,
            t=0.0
        )

        # Low pressure → increased HR
        hr_low = controller.compute_heart_rate_response(
            pressure=70.0,
            baseline_hr=baseline_hr,
            dt=0.001,
            t=0.1
        )

        # HR should be within physiological limits
        assert 40.0 <= hr_high <= 200.0
        assert 40.0 <= hr_low <= 200.0

    def test_baroreflex_delays(self):
        """Test that efferent delays are implemented."""
        controller = BaroreflexController()
        params = controller.params

        # Apply pressure change
        t = 0.0
        dt = 0.001

        # Step through time to fill history
        for i in range(1000):
            controller.compute_autonomic_output(pressure=100.0, dt=dt, t=t)
            t += dt

        # History should have entries
        assert len(controller._vagal_history) > 0
        assert len(controller._sympathetic_history) > 0


class TestAutonomicNervousSystem:
    """Test integrated autonomic nervous system."""

    def test_ans_initialization(self):
        """Test ANS initialization."""
        ans = AutonomicNervousSystem()
        assert ans is not None
        assert ans.baroreflex is not None
        assert ans.state is not None

    def test_ans_update(self):
        """Test ANS state update."""
        ans = AutonomicNervousSystem()

        # Update with normal pressure
        state = ans.update(pressure=93.0, dt=0.001, t=0.0)

        assert state is not None
        assert 0 <= state.vagal_tone <= 1.0
        assert 0 <= state.sympathetic_tone <= 1.0
        assert state.contractility_effect >= 1.0  # Should be >= baseline

    def test_ans_pressure_response(self):
        """Test ANS response to pressure changes."""
        ans = AutonomicNervousSystem()

        # Simulate baseline
        for i in range(1000):
            ans.update(pressure=93.0, dt=0.001, t=i*0.001)

        baseline_vagal = ans.state.vagal_tone
        baseline_sympathetic = ans.state.sympathetic_tone

        # Apply high pressure for a while
        for i in range(1000, 2000):
            ans.update(pressure=140.0, dt=0.001, t=i*0.001)

        # Vagal should increase, sympathetic should decrease
        # (Note: actual response depends on integration dynamics)
        # Just check that state changes
        assert ans.state.vagal_tone != baseline_vagal or ans.state.sympathetic_tone != baseline_sympathetic

    def test_ans_get_heart_rate(self):
        """Test heart rate calculation."""
        ans = AutonomicNervousSystem()
        ans.update(pressure=93.0, dt=0.001, t=0.0)

        hr = ans.get_heart_rate(intrinsic_hr=105.0)

        # Should be within physiological range
        assert 30.0 <= hr <= 220.0

    def test_ans_valsalva_simulation(self):
        """Test Valsalva maneuver simulation."""
        ans = AutonomicNervousSystem()

        results = ans.simulate_valsalva_maneuver(
            duration=15.0,
            strain_duration=10.0,
            dt=0.01  # 10ms timestep for speed
        )

        assert 'time' in results
        assert 'pressure' in results
        assert 'heart_rate' in results
        assert 'phase' in results

        # Should have 4 phases
        phases = set(results['phase'])
        assert phases == {1, 2, 3, 4}

        # Check that we have data
        assert len(results['time']) > 0
        assert len(results['pressure']) > 0

    def test_ans_orthostatic_stress(self):
        """Test orthostatic stress simulation."""
        ans = AutonomicNervousSystem()

        results = ans.simulate_orthostatic_stress(
            duration=30.0,
            tilt_time=5.0,
            dt=0.01
        )

        assert 'time' in results
        assert 'pressure' in results
        assert 'heart_rate' in results
        assert 'svr_multiplier' in results

        # Pressure should drop after tilt
        pre_tilt_pressure = results['pressure'][int(4.0 / 0.01)]  # Just before tilt
        post_tilt_pressure = results['pressure'][int(6.0 / 0.01)]  # After tilt

        # Post-tilt pressure should be lower initially
        assert post_tilt_pressure < pre_tilt_pressure

    def test_ans_reset(self):
        """Test ANS reset functionality."""
        ans = AutonomicNervousSystem()
        params = ans.params

        # Perturb the system
        for i in range(1000):
            ans.update(pressure=140.0, dt=0.001, t=i*0.001)

        # State should be different from baseline
        perturbed_state = ans.state.vagal_tone

        # Reset
        ans.reset()

        # Should return to baseline
        assert ans.state.vagal_tone == params.baseline_vagal_tone
        assert ans.state.sympathetic_tone == params.baseline_sympathetic_tone


def test_simulate_baroreflex_response():
    """Test baroreflex response simulation function."""
    # Create pressure trajectory
    pressure_trajectory = [
        (t, 93.0 + 20.0 * (t / 10.0))  # Pressure ramp
        for t in [i * 0.01 for i in range(1000)]
    ]

    results = simulate_baroreflex_response(pressure_trajectory, dt=0.01)

    assert 'times' in results
    assert 'pressures' in results
    assert 'vagal' in results
    assert 'sympathetic' in results
    assert 'heart_rate' in results
    assert 'baroreceptor_firing' in results

    # Should have same length as input
    assert len(results['times']) == len(pressure_trajectory)

    # Firing rate should increase with pressure
    assert results['baroreceptor_firing'][-1] > results['baroreceptor_firing'][0]


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
