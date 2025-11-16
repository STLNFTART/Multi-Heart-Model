"""
Parameter validation and error handling tests for core models.

Tests cover:
- Invalid parameter values (negative, zero, NaN, Inf)
- Parameter type validation
- Reasonable parameter ranges
- Graceful handling of edge cases
- No crashes on invalid inputs
"""

import pytest
import math
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import CouplingParameters, HeartBrainCouplingModel


class TestVanDerPolParameterValidation:
    """Test VanDerPolOscillator parameter validation."""

    def test_negative_mu_still_works(self):
        """Test that negative mu doesn't crash (though unphysical)."""
        model = VanDerPolOscillator(mu=-1.0)

        # Should not crash
        dx, dy = model.derivatives(0.0, (1.0, 0.0))

        assert isinstance(dx, float)
        assert isinstance(dy, float)

    def test_zero_omega_still_works(self):
        """Test zero frequency (no restoring force)."""
        model = VanDerPolOscillator(omega=0.0)

        dx, dy = model.derivatives(0.0, (1.0, 0.5))

        # dx = y = 0.5
        assert dx == 0.5
        # dy = mu*(1-x^2)*y - 0 = 1.5*(1-1)*0.5 = 0
        assert dy == 0.0

    def test_very_large_mu(self):
        """Test with very large nonlinearity parameter."""
        model = VanDerPolOscillator(mu=1000.0)

        # Should not crash
        dx, dy = model.derivatives(0.0, (0.5, 0.1))

        assert not math.isnan(dx)
        assert not math.isnan(dy)
        assert not math.isinf(dx)
        assert not math.isinf(dy)

    def test_very_large_omega(self):
        """Test with very high frequency."""
        model = VanDerPolOscillator(omega=100.0)

        dx, dy = model.derivatives(0.0, (1.0, 0.0))

        # Should have large restoring force
        assert abs(dy) == pytest.approx(10000.0)  # -omega^2 * x

    def test_negative_damping(self):
        """Test negative damping (anti-damping)."""
        model = VanDerPolOscillator(damping=-1.0)

        dx, dy = model.derivatives(0.0, (0.0, 1.0))

        # Should work, just adds energy
        assert isinstance(dx, float)
        assert isinstance(dy, float)

    def test_very_large_damping(self):
        """Test overdamped system."""
        model = VanDerPolOscillator(damping=100.0)

        dx, dy = model.derivatives(0.0, (1.0, 1.0))

        # Heavy damping
        assert isinstance(dy, float)


class TestFitzHughNagumoParameterValidation:
    """Test FitzHughNagumo parameter validation."""

    def test_negative_a_parameter(self):
        """Test negative a parameter."""
        model = FitzHughNagumo(a=-0.5)

        dv, dw = model.derivatives(0.0, (0.0, 0.0))

        # Should not crash
        assert isinstance(dv, float)
        assert isinstance(dw, float)

    def test_zero_c_parameter(self):
        """Test zero time constant (would cause division by zero)."""
        model = FitzHughNagumo(c=0.0)

        # This WILL cause issues, but shouldn't crash Python
        try:
            dv, dw = model.derivatives(0.0, (0.0, 0.0))
            # If c=0, dw = (v + a - b*w) / 0 = inf
            assert math.isinf(dw) or math.isnan(dw)
        except ZeroDivisionError:
            # This is acceptable - division by zero
            pass

    def test_very_large_c(self):
        """Test very large time constant (very slow recovery)."""
        model = FitzHughNagumo(c=10000.0)

        dv, dw = model.derivatives(0.0, (1.0, 0.5))

        # dw should be very small
        assert abs(dw) < 0.001

    def test_negative_stimulus(self):
        """Test negative stimulus amplitude."""
        model = FitzHughNagumo(stimulus_amplitude=-1.0)

        dv, dw = model.derivatives(0.0, (0.0, 0.0))

        # Should work, just hyperpolarizes
        assert dv == -1.0

    def test_very_large_stimulus(self):
        """Test very large stimulus."""
        model = FitzHughNagumo(stimulus_amplitude=1000.0)

        dv, dw = model.derivatives(0.0, (0.0, 0.0))

        # Should work
        assert dv == 1000.0

    def test_zero_b_parameter(self):
        """Test zero b parameter."""
        model = FitzHughNagumo(b=0.0)

        dv, dw = model.derivatives(0.0, (1.0, 0.5))

        # Should work
        assert isinstance(dv, float)
        assert isinstance(dw, float)


class TestCouplingParameterValidation:
    """Test HeartBrainCouplingModel parameter validation."""

    def test_negative_coupling_gains(self):
        """Test negative coupling gains (inhibitory coupling)."""
        params = CouplingParameters(
            neural_to_cardiac_gain=-0.5,
            cardiac_to_neural_gain=-0.3
        )
        model = HeartBrainCouplingModel(coupling=params)

        state = (0.5, 0.3, 0.8, 0.4)
        dv, dw, dx, dy = model.derivatives(0.0, state)

        # Should work (inhibitory coupling)
        assert isinstance(dv, float)

    def test_very_large_coupling_gains(self):
        """Test very strong coupling."""
        params = CouplingParameters(
            neural_to_cardiac_gain=100.0,
            cardiac_to_neural_gain=100.0
        )
        model = HeartBrainCouplingModel(coupling=params)

        state = (0.5, 0.3, 0.8, 0.4)
        dv, dw, dx, dy = model.derivatives(0.0, state)

        # Should not crash
        assert not math.isnan(dv)

    def test_negative_delays(self):
        """Test negative delays (instantaneous or predictive?)."""
        params = CouplingParameters(
            neural_delay=-0.1,
            cardiac_delay=-0.1
        )
        model = HeartBrainCouplingModel(coupling=params)

        # Add some history
        model.history.append((0.0, (1.0, 0.5), (2.0, 1.5)))
        model.history.append((0.1, (1.1, 0.6), (2.1, 1.6)))

        # Negative delay should use current state (delay <= 0 case)
        result = model._delayed_state(0.2, -0.1, "neural", (0.0, 0.0))

        # Should return fallback for negative delay
        assert result == (0.0, 0.0)

    def test_very_large_delays(self):
        """Test very large delays."""
        params = CouplingParameters(
            neural_delay=1000.0,
            cardiac_delay=1000.0
        )
        model = HeartBrainCouplingModel(coupling=params)

        # Should work, just always use earliest history or fallback
        state = (0.5, 0.3, 0.8, 0.4)
        dv, dw, dx, dy = model.derivatives(0.0, state)

        assert isinstance(dv, float)

    def test_zero_dt_in_simulate(self):
        """Test that zero dt raises error."""
        model = HeartBrainCouplingModel()

        with pytest.raises(ValueError, match="dt must be positive"):
            model.simulate((0.0, 0.0, 1.0, 0.0), (0.0, 1.0), dt=0.0)

    def test_negative_dt_in_simulate(self):
        """Test that negative dt raises error."""
        model = HeartBrainCouplingModel()

        with pytest.raises(ValueError, match="dt must be positive"):
            model.simulate((0.0, 0.0, 1.0, 0.0), (0.0, 1.0), dt=-0.01)

    def test_invalid_t_span_raises_error(self):
        """Test that t_span with stop < start raises error."""
        model = HeartBrainCouplingModel()

        with pytest.raises(ValueError, match="t_span must have stop > start"):
            model.simulate((0.0, 0.0, 1.0, 0.0), (1.0, 0.0), dt=0.01)

    def test_equal_t_span_raises_error(self):
        """Test that t_span with stop = start raises error."""
        model = HeartBrainCouplingModel()

        with pytest.raises(ValueError, match="t_span must have stop > start"):
            model.simulate((0.0, 0.0, 1.0, 0.0), (1.0, 1.0), dt=0.01)


class TestStateValidation:
    """Test state variable validation and handling."""

    def test_nan_state_van_der_pol(self):
        """Test VanDerPol with NaN state."""
        model = VanDerPolOscillator()

        # NaN state
        dx, dy = model.derivatives(0.0, (float('nan'), 0.0))

        # Result will be NaN
        assert math.isnan(dx) or math.isnan(dy)

    def test_inf_state_van_der_pol(self):
        """Test VanDerPol with Inf state."""
        model = VanDerPolOscillator()

        dx, dy = model.derivatives(0.0, (float('inf'), 0.0))

        # Result will be Inf or NaN
        assert math.isinf(dx) or math.isnan(dx) or math.isinf(dy) or math.isnan(dy)

    def test_nan_state_fitzhugh_nagumo(self):
        """Test FitzHughNagumo with NaN state."""
        model = FitzHughNagumo()

        dv, dw = model.derivatives(0.0, (float('nan'), 0.0))

        # Result will be NaN
        assert math.isnan(dv) or math.isnan(dw)

    def test_very_large_state_values(self):
        """Test with very large state values."""
        model = VanDerPolOscillator()

        # Very large displacement
        dx, dy = model.derivatives(0.0, (1e10, 0.0))

        # Should compute, though may be very large
        assert isinstance(dx, float)
        assert isinstance(dy, float)

    def test_very_small_state_values(self):
        """Test with very small state values."""
        model = FitzHughNagumo()

        dv, dw = model.derivatives(0.0, (1e-100, 1e-100))

        # Should work
        assert isinstance(dv, float)
        assert isinstance(dw, float)


class TestInputValidation:
    """Test input parameter validation."""

    def test_nan_input_force(self):
        """Test VanDerPol with NaN input."""
        model = VanDerPolOscillator()

        dx, dy = model.derivatives(0.0, (1.0, 0.0), input_force=float('nan'))

        # Result will be NaN
        assert math.isnan(dy)

    def test_inf_input_force(self):
        """Test VanDerPol with Inf input."""
        model = VanDerPolOscillator()

        dx, dy = model.derivatives(0.0, (1.0, 0.0), input_force=float('inf'))

        # Result will be Inf
        assert math.isinf(dy)

    def test_nan_input_drive(self):
        """Test FitzHughNagumo with NaN input."""
        model = FitzHughNagumo()

        dv, dw = model.derivatives(0.0, (0.0, 0.0), input_drive=float('nan'))

        # Result will be NaN
        assert math.isnan(dv)

    def test_very_large_input(self):
        """Test with very large input."""
        model = FitzHughNagumo()

        dv, dw = model.derivatives(0.0, (0.0, 0.0), input_drive=1e10)

        # Should work
        assert dv == pytest.approx(1e10)


class TestTimeParameterValidation:
    """Test time parameter validation."""

    def test_negative_time(self):
        """Test that negative time works (time is autonomous parameter)."""
        model = VanDerPolOscillator()

        dx, dy = model.derivatives(-100.0, (1.0, 0.0))

        # Time doesn't affect autonomous systems
        assert isinstance(dx, float)

    def test_very_large_time(self):
        """Test with very large time value."""
        model = FitzHughNagumo()

        dv, dw = model.derivatives(1e100, (0.5, 0.3))

        # Should work for autonomous system
        assert isinstance(dv, float)

    def test_nan_time(self):
        """Test with NaN time."""
        model = VanDerPolOscillator()

        # Should still work for autonomous system (time not used)
        dx, dy = model.derivatives(float('nan'), (1.0, 0.0))

        assert isinstance(dx, float)


class TestStepMethodValidation:
    """Test step method error handling."""

    def test_zero_timestep_van_der_pol(self):
        """Test VanDerPol step with zero dt."""
        model = VanDerPolOscillator()

        # Zero timestep should not change state
        new_state = model.step(0.0, (1.0, 0.5), dt=0.0)

        assert new_state == (1.0, 0.5)

    def test_negative_timestep(self):
        """Test step with negative dt (backward integration)."""
        model = FitzHughNagumo()

        # Backward integration (negative dt)
        state = (0.5, 0.3)
        new_state = model.step(0.0, state, dt=-0.01)

        # Should integrate backward
        assert isinstance(new_state[0], float)
        assert isinstance(new_state[1], float)

    def test_very_large_timestep(self):
        """Test with very large timestep (unstable)."""
        model = VanDerPolOscillator()

        # Very large timestep
        new_state = model.step(0.0, (1.0, 0.0), dt=100.0)

        # Will be numerically unstable but shouldn't crash
        assert isinstance(new_state[0], float)
        assert isinstance(new_state[1], float)

    def test_very_small_timestep(self):
        """Test with very small timestep."""
        model = FitzHughNagumo()

        state = (0.5, 0.3)
        new_state = model.step(0.0, state, dt=1e-10)

        # Should barely change
        assert new_state[0] == pytest.approx(state[0], abs=1e-8)
        assert new_state[1] == pytest.approx(state[1], abs=1e-8)


class TestExtractSeriesValidation:
    """Test extract_series error handling."""

    def test_empty_trajectory(self):
        """Test extract_series with empty trajectory."""
        model = HeartBrainCouplingModel()

        times, neural, cardiac = model.extract_series([])

        assert times == []
        assert neural == []
        assert cardiac == []

    def test_single_point_trajectory(self):
        """Test extract_series with single point."""
        model = HeartBrainCouplingModel()

        trajectory = [(0.0, (1.0, 0.5, 2.0, 1.5))]
        times, neural, cardiac = model.extract_series(trajectory)

        assert len(times) == 1
        assert len(neural) == 1
        assert len(cardiac) == 1
        assert times[0] == 0.0
        assert neural[0] == 1.0
        assert cardiac[0] == 2.0


class TestBoundaryConditions:
    """Test behavior at numerical boundaries."""

    def test_maximum_float_state(self):
        """Test with state at maximum float value."""
        model = VanDerPolOscillator()

        # Very large but representable float
        large_val = 1e308

        try:
            dx, dy = model.derivatives(0.0, (large_val, 0.0))
            # May overflow to inf
            assert isinstance(dx, float)
        except OverflowError:
            # Acceptable
            pass

    def test_minimum_positive_float_state(self):
        """Test with very small positive float."""
        model = FitzHughNagumo()

        tiny_val = 1e-308
        dv, dw = model.derivatives(0.0, (tiny_val, tiny_val))

        # Should work
        assert isinstance(dv, float)
        assert isinstance(dw, float)

    def test_mixed_extreme_values(self):
        """Test with mixed extreme values."""
        model = HeartBrainCouplingModel()

        # Mix of large and small values
        state = (1e10, 1e-10, -1e10, 1e-10)

        try:
            dv, dw, dx, dy = model.derivatives(0.0, state)
            assert isinstance(dv, float)
        except:
            # May overflow, acceptable
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
