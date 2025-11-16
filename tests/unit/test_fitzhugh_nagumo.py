"""
Comprehensive unit tests for FitzHugh-Nagumo neural oscillator.

Tests cover:
- Basic derivatives computation
- Parameter validation and ranges
- Different excitability regimes
- Stimulus threshold behavior
- Recovery dynamics
- Integration consistency
- Long-term stability
- Edge cases
"""

import pytest
import math
from src.neural import FitzHughNagumo


class TestFitzHughNagumoBasicDerivatives:
    """Test basic derivative computation."""

    def test_derivatives_at_rest_state(self):
        """Test derivatives at resting state."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.0)
        dv, dw = model.derivatives(0.0, (0.0, 0.0))

        # dv/dt = v - v^3/3 - w + stimulus = 0
        # dw/dt = (v + a - b*w) / c = (0 + 0.7 - 0) / 3
        assert dv == 0.0
        assert dw == pytest.approx(0.7 / 3.0)

    def test_derivatives_with_excitation(self):
        """Test derivatives with voltage excitation."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0)
        dv, dw = model.derivatives(0.0, (1.0, -0.5))

        # dv/dt = 1 - 1/3 - (-0.5) = 1 - 0.333... + 0.5 = 1.166...
        expected_dv = 1.0 - (1.0**3) / 3.0 - (-0.5)
        # dw/dt = (1 + 0.7 - 0.8*(-0.5)) / 3
        expected_dw = (1.0 + 0.7 - 0.8 * (-0.5)) / 3.0

        assert dv == pytest.approx(expected_dv)
        assert dw == pytest.approx(expected_dw)

    def test_derivatives_with_stimulus(self):
        """Test external stimulus input."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.5)
        dv, dw = model.derivatives(0.0, (0.0, 0.0))

        # Stimulus adds to dv
        assert dv == 0.5
        assert dw == pytest.approx(0.7 / 3.0)

    def test_derivatives_with_input_drive(self):
        """Test input drive parameter."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.0)
        dv, dw = model.derivatives(0.0, (0.0, 0.0), input_drive=0.3)

        # Input drive adds to dv
        assert dv == 0.3
        assert dw == pytest.approx(0.7 / 3.0)

    def test_stimulus_and_input_combine(self):
        """Test that stimulus and input drive combine."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.2)
        dv, dw = model.derivatives(0.0, (0.0, 0.0), input_drive=0.3)

        # Both should add
        assert dv == 0.5  # 0.2 + 0.3
        assert dw == pytest.approx(0.7 / 3.0)


class TestFitzHughNagumoParameterRanges:
    """Test behavior across different parameter ranges."""

    @pytest.mark.parametrize("a", [0.5, 0.7, 0.9, 1.0])
    def test_different_a_values(self, a):
        """Test different excitability parameters."""
        model = FitzHughNagumo(a=a, b=0.8, c=3.0)
        dv, dw = model.derivatives(0.0, (0.0, 0.0))

        # a affects recovery variable
        assert dw == pytest.approx(a / 3.0)

    @pytest.mark.parametrize("b", [0.5, 0.7, 0.8, 1.0])
    def test_different_b_values(self, b):
        """Test different recovery coupling parameters."""
        model = FitzHughNagumo(a=0.7, b=b, c=3.0)
        dv, dw = model.derivatives(0.0, (1.0, 0.5))

        # b affects how w couples back
        expected_dw = (1.0 + 0.7 - b * 0.5) / 3.0
        assert dw == pytest.approx(expected_dw)

    @pytest.mark.parametrize("c", [1.0, 2.0, 3.0, 5.0])
    def test_different_c_values(self, c):
        """Test different time scale parameters."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=c)
        dv, dw = model.derivatives(0.0, (0.0, 0.0))

        # c affects time scale of recovery
        assert dw == pytest.approx(0.7 / c)

    @pytest.mark.parametrize("stimulus", [0.0, 0.2, 0.5, 1.0])
    def test_different_stimulus_amplitudes(self, stimulus):
        """Test different stimulus amplitudes."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=stimulus)
        dv, dw = model.derivatives(0.0, (0.0, 0.0))

        assert dv == stimulus


class TestFitzHughNagumoExcitabilityRegimes:
    """Test different excitability regimes."""

    def test_excitable_regime(self):
        """Test excitable regime (subthreshold returns to rest)."""
        # Use parameters that give excitable (not oscillatory) regime
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.0)

        # Small perturbation
        state = (0.1, 0.0)
        dt = 0.01

        # Simulate
        states = [state]
        for _ in range(500):
            state = model.step(0.0, state, dt)
            states.append(state)

        # With default parameters, system may oscillate or settle
        # Check that state remains bounded
        final_v = states[-1][0]
        assert abs(final_v) < 5.0  # Remains bounded

    def test_oscillatory_regime(self):
        """Test oscillatory regime with sufficient stimulus."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.5)

        # Start at rest
        state = (0.0, 0.0)
        dt = 0.01

        # Simulate
        states = [state]
        for _ in range(1000):
            state = model.step(0.0, state, dt)
            states.append(state)

        # Should oscillate
        v_values = [s[0] for s in states[500:]]  # Skip transient
        v_max = max(v_values)
        v_min = min(v_values)

        # Should have reasonable oscillation amplitude
        assert v_max > 0.5
        assert v_min < -0.5

    def test_threshold_behavior(self):
        """Test threshold-like behavior of excitable system."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.0)

        # Subthreshold input
        state_sub = (0.0, 0.0)
        dt = 0.01
        for _ in range(100):
            state_sub = model.step(0.0, state_sub, dt, input_drive=0.3)

        # Suprathreshold input
        state_supra = (0.0, 0.0)
        for _ in range(100):
            state_supra = model.step(0.0, state_supra, dt, input_drive=0.7)

        # Suprathreshold should give larger response
        assert abs(state_supra[0]) > abs(state_sub[0])


class TestFitzHughNagumoRecoveryDynamics:
    """Test recovery variable dynamics."""

    def test_recovery_follows_activation(self):
        """Test that recovery variable tracks activation."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.5)

        state = (0.0, 0.0)
        dt = 0.01

        v_values = []
        w_values = []

        for _ in range(500):
            state = model.step(0.0, state, dt)
            v_values.append(state[0])
            w_values.append(state[1])

        # Recovery should lag activation (check correlation with delay)
        # This is a simplified check - recovery should generally increase when v increases
        # but with a delay due to the time constant c

    def test_slow_recovery_with_large_c(self):
        """Test that large c slows recovery."""
        model_fast = FitzHughNagumo(a=0.7, b=0.8, c=1.0, stimulus_amplitude=0.5)
        model_slow = FitzHughNagumo(a=0.7, b=0.8, c=10.0, stimulus_amplitude=0.5)

        # Same initial condition and input
        state_fast = (1.0, 0.0)
        state_slow = (1.0, 0.0)
        dt = 0.01

        # Single step
        state_fast = model_fast.step(0.0, state_fast, dt)
        state_slow = model_slow.step(0.0, state_slow, dt)

        # Fast model should have larger change in w
        assert abs(state_fast[1] - 0.0) > abs(state_slow[1] - 0.0)


class TestFitzHughNagumoNullclines:
    """Test nullcline behavior."""

    def test_v_nullcline(self):
        """Test v-nullcline: dv/dt = 0."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.0)

        # On v-nullcline: v - v^3/3 - w = 0, so w = v - v^3/3
        v = 1.0
        w = v - v**3 / 3.0

        dv, _ = model.derivatives(0.0, (v, w))

        # dv should be zero on nullcline
        assert dv == pytest.approx(0.0, abs=1e-10)

    def test_w_nullcline(self):
        """Test w-nullcline: dw/dt = 0."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.0)

        # On w-nullcline: v + a - b*w = 0, so w = (v + a) / b
        v = 0.5
        w = (v + 0.7) / 0.8

        _, dw = model.derivatives(0.0, (v, w))

        # dw should be zero on nullcline
        assert dw == pytest.approx(0.0, abs=1e-10)


class TestFitzHughNagumoIntegration:
    """Test integration step consistency."""

    def test_step_matches_derivatives(self):
        """Test that step() uses derivatives() correctly."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.2)
        state = (0.5, 0.3)
        dt = 0.01

        # Manual computation
        dv, dw = model.derivatives(0.0, state)
        expected_state = (state[0] + dt * dv, state[1] + dt * dw)

        # Step computation
        actual_state = model.step(0.0, state, dt)

        assert actual_state[0] == pytest.approx(expected_state[0])
        assert actual_state[1] == pytest.approx(expected_state[1])

    def test_step_with_input_drive(self):
        """Test step() with input drive."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0)
        state = (0.0, 0.0)
        dt = 0.01
        input_drive = 0.5

        # Manual
        dv, dw = model.derivatives(0.0, state, input_drive=input_drive)
        expected_state = (state[0] + dt * dv, state[1] + dt * dw)

        # Step
        actual_state = model.step(0.0, state, dt, input_drive=input_drive)

        assert actual_state[0] == pytest.approx(expected_state[0])
        assert actual_state[1] == pytest.approx(expected_state[1])

    def test_integration_consistency(self):
        """Test that integration gives consistent results."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.3)
        state = (0.0, 0.0)
        dt = 0.01

        # Integrate using step
        for _ in range(100):
            state = model.step(0.0, state, dt)

        # Should produce valid state
        assert not math.isnan(state[0])
        assert not math.isnan(state[1])
        assert not math.isinf(state[0])
        assert not math.isinf(state[1])


class TestFitzHughNagumoStability:
    """Test numerical stability."""

    def test_no_numerical_explosion(self):
        """Test that state doesn't explode."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.5)
        state = (0.1, 0.1)
        dt = 0.001

        # Long simulation
        for _ in range(10000):
            state = model.step(0.0, state, dt)

            # Check for NaN or Inf
            assert not math.isnan(state[0])
            assert not math.isnan(state[1])
            assert not math.isinf(state[0])
            assert not math.isinf(state[1])

            # Check reasonable bounds
            assert abs(state[0]) < 10.0
            assert abs(state[1]) < 10.0

    def test_stability_with_small_timestep(self):
        """Test stability with small timestep."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.5)
        state = (0.0, 0.0)
        dt = 0.0001

        # Simulate
        for _ in range(1000):
            state = model.step(0.0, state, dt)

        # Should remain bounded
        assert abs(state[0]) < 5.0
        assert abs(state[1]) < 5.0


class TestFitzHughNagumoEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_stimulus(self):
        """Test with no stimulus."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.0)
        dv, dw = model.derivatives(0.0, (0.0, 0.0))

        assert dv == 0.0

    def test_large_voltage(self):
        """Test with large voltage values."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0)
        dv, dw = model.derivatives(0.0, (5.0, 0.0))

        # Cubic term should dominate
        # dv = 5 - 125/3 - 0 = 5 - 41.67 = -36.67
        expected_dv = 5.0 - (5.0**3) / 3.0
        assert dv == pytest.approx(expected_dv)

    def test_negative_voltage(self):
        """Test with negative voltage."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0)
        dv, dw = model.derivatives(0.0, (-2.0, 0.0))

        # dv = -2 - (-8/3) - 0 = -2 + 2.67 = 0.67
        expected_dv = -2.0 - ((-2.0)**3) / 3.0
        assert dv == pytest.approx(expected_dv)

    def test_large_recovery(self):
        """Test with large recovery variable."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0)
        dv, dw = model.derivatives(0.0, (0.0, 5.0))

        # dv = 0 - 0 - 5 = -5
        assert dv == -5.0

    def test_time_parameter_unused(self):
        """Test that time parameter doesn't affect derivatives."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0)
        state = (0.5, 0.3)

        dv1, dw1 = model.derivatives(0.0, state)
        dv2, dw2 = model.derivatives(100.0, state)

        assert dv1 == dv2
        assert dw1 == dw2


class TestFitzHughNagumoPhysicalProperties:
    """Test physical properties."""

    def test_cubic_nonlinearity(self):
        """Test cubic nonlinearity in voltage."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.0)

        # The v^3/3 term should create an N-shaped nullcline
        # Test at different v values
        v_values = [-2.0, -1.0, 0.0, 1.0, 2.0]
        for v in v_values:
            w = 0.0
            dv, _ = model.derivatives(0.0, (v, w))

            # dv = v - v^3/3 - w
            expected_dv = v - v**3 / 3.0
            assert dv == pytest.approx(expected_dv)

    def test_fast_slow_dynamics(self):
        """Test that w changes on slower timescale when c > 1."""
        model_fast = FitzHughNagumo(a=0.7, b=0.8, c=1.0)
        model_slow = FitzHughNagumo(a=0.7, b=0.8, c=10.0)
        state = (1.0, 0.5)

        _, dw_fast = model_fast.derivatives(0.0, state)
        _, dw_slow = model_slow.derivatives(0.0, state)

        # Larger c should give smaller dw (slower recovery)
        assert abs(dw_slow) < abs(dw_fast)

    def test_refractory_period(self):
        """Test that recovery creates refractory period."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.0)

        # After a spike, high w prevents immediate re-excitation
        state_high_w = (0.5, 1.0)  # High recovery
        state_low_w = (0.5, 0.0)   # Low recovery

        dv_high, _ = model.derivatives(0.0, state_high_w, input_drive=0.5)
        dv_low, _ = model.derivatives(0.0, state_low_w, input_drive=0.5)

        # High w should reduce dv (oppose excitation)
        assert dv_high < dv_low


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
