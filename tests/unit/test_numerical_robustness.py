"""
Numerical robustness and stress tests.

Tests cover:
- Numerical overflow and underflow handling
- Precision and rounding errors
- Catastrophic cancellation
- Stress tests with extreme parameters
- Long-term numerical drift
- Stiff system handling
"""

import pytest
import math
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import CouplingParameters, HeartBrainCouplingModel


class TestNumericalOverflow:
    """Test handling of numerical overflow."""

    def test_overflow_in_cubic_term(self):
        """Test FitzHughNagumo cubic term with large v."""
        model = FitzHughNagumo()

        # Very large v will cause v^3 to overflow
        v_large = 1e200
        try:
            dv, dw = model.derivatives(0.0, (v_large, 0.0))
            # If it doesn't overflow, result should be negative (cubic dominates)
            if not math.isinf(dv) and not math.isnan(dv):
                assert dv < 0  # -v^3/3 dominates
        except OverflowError:
            # Acceptable - overflow detected
            pass

    def test_overflow_in_exponential_terms(self):
        """Test Van der Pol with values causing exponential overflow."""
        model = VanDerPolOscillator(mu=1000.0)

        # Large nonlinearity with large state
        v_large = 1000.0
        try:
            dx, dy = model.derivatives(0.0, (v_large, 10.0))
            # mu*(1-x^2)*y will be very large
            assert isinstance(dx, float)
        except OverflowError:
            pass

    def test_overflow_in_product_terms(self):
        """Test overflow in coupled system."""
        params = CouplingParameters(
            neural_to_cardiac_gain=1e100,
            cardiac_to_neural_gain=1e100
        )
        model = HeartBrainCouplingModel(coupling=params)

        state = (1e100, 0.0, 1e100, 0.0)
        try:
            dv, dw, dx, dy = model.derivatives(0.0, state)
            # May overflow
            assert isinstance(dv, float)
        except OverflowError:
            pass


class TestNumericalUnderflow:
    """Test handling of numerical underflow."""

    def test_underflow_with_tiny_values(self):
        """Test with values near underflow threshold."""
        model = FitzHughNagumo()

        # Very small values
        tiny = 1e-320
        dv, dw = model.derivatives(0.0, (tiny, tiny))

        # Should not underflow to exact zero unexpectedly
        assert isinstance(dv, float)
        assert isinstance(dw, float)

    def test_underflow_in_step_integration(self):
        """Test underflow in time stepping."""
        model = VanDerPolOscillator()

        # Very small timestep with very small state
        tiny_state = (1e-300, 1e-300)
        tiny_dt = 1e-300

        new_state = model.step(0.0, tiny_state, tiny_dt)

        # Should not crash
        assert isinstance(new_state[0], float)
        assert isinstance(new_state[1], float)


class TestPrecisionLoss:
    """Test precision loss and rounding errors."""

    def test_catastrophic_cancellation(self):
        """Test subtraction of nearly equal numbers."""
        model = FitzHughNagumo()

        # State where terms nearly cancel
        # dv = v - v^3/3 - w
        # At v = 1, v - v^3/3 = 1 - 1/3 = 2/3
        v = 1.0
        w = 2.0/3.0 - 1e-15  # Nearly cancels first two terms

        dv, dw = model.derivatives(0.0, (v, w))

        # dv should be very small but not exactly zero
        assert abs(dv) < 1e-10

    def test_precision_in_long_simulation(self):
        """Test precision degradation over many steps."""
        model = VanDerPolOscillator(mu=0.0, omega=1.0, damping=0.0)

        # Harmonic oscillator should conserve energy
        state = (1.0, 0.0)
        initial_energy = state[0]**2 + state[1]**2

        # Many small steps
        for _ in range(10000):
            state = model.step(0.0, state, dt=0.001)

        final_energy = state[0]**2 + state[1]**2

        # Energy should be approximately conserved
        # (within numerical precision limits of Euler integration)
        rel_error = abs(final_energy - initial_energy) / initial_energy

        # Euler method will have some drift, but shouldn't be catastrophic
        assert rel_error < 0.5  # Within 50% (Euler is not energy conserving)

    def test_accumulation_of_rounding_errors(self):
        """Test accumulation of rounding errors."""
        model = FitzHughNagumo()

        # Sum many small numbers (classic precision test)
        state = (0.1, 0.1)
        sum_states_0 = 0.0
        sum_states_1 = 0.0

        for _ in range(1000):
            state = model.step(0.0, state, dt=0.001)
            sum_states_0 += state[0]
            sum_states_1 += state[1]

        # Should not lose too much precision
        assert not math.isnan(sum_states_0)
        assert not math.isnan(sum_states_1)


class TestStiffnessHandling:
    """Test handling of stiff differential equations."""

    def test_fast_slow_dynamics(self):
        """Test system with widely separated time scales."""
        # FitzHugh-Nagumo with large c is a fast-slow system
        model = FitzHughNagumo(c=1000.0)

        # w changes very slowly
        state = (1.0, 0.5)

        # Multiple steps should be stable
        for _ in range(100):
            state = model.step(0.0, state, dt=0.01)

        # Should remain bounded
        assert abs(state[0]) < 10.0
        assert abs(state[1]) < 10.0

    def test_stiff_coupling(self):
        """Test stiff coupled system."""
        # Very strong, fast coupling
        params = CouplingParameters(
            neural_to_cardiac_gain=10.0,
            cardiac_to_neural_gain=10.0
        )
        model = HeartBrainCouplingModel(coupling=params)

        # May require small timestep for stability
        state = (0.1, 0.1, 0.1, 0.1)

        for _ in range(100):
            state = model.step(0.0, state, dt=0.0001)  # Small dt

        # Should remain stable
        assert all(abs(x) < 100.0 for x in state)


class TestNumericalDrift:
    """Test long-term numerical drift."""

    def test_long_simulation_drift(self):
        """Test that state doesn't drift to unrealistic values."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)

        state = (1.0, 0.0)

        # Very long simulation
        for _ in range(100000):
            state = model.step(0.0, state, dt=0.001)

        # Should still be bounded
        assert abs(state[0]) < 10.0
        assert abs(state[1]) < 10.0

    def test_mean_reversion(self):
        """Test that oscillators stay near origin on average."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.0)

        state = (1.0, 0.5)
        states_v = []

        for _ in range(10000):
            state = model.step(0.0, state, dt=0.01)
            states_v.append(state[0])

        # Mean should be in reasonable range (model may have offset equilibrium)
        mean_v = sum(states_v[-1000:]) / 1000.0  # Last 1000 points

        assert abs(mean_v) < 3.0  # Reasonable mean (not drifting to infinity)


class TestStressTests:
    """Stress tests with extreme conditions."""

    def test_rapid_parameter_changes(self):
        """Test with rapidly changing parameters (via input)."""
        model = VanDerPolOscillator()

        state = (1.0, 0.0)

        # Alternate between large positive and negative inputs
        for i in range(1000):
            input_force = 10.0 if i % 2 == 0 else -10.0
            state = model.step(0.0, state, dt=0.001, input_force=input_force)

        # Should remain bounded
        assert abs(state[0]) < 50.0
        assert abs(state[1]) < 50.0

    def test_high_frequency_oscillations(self):
        """Test high-frequency oscillator."""
        model = VanDerPolOscillator(omega=100.0)

        state = (1.0, 0.0)

        # Very small timestep needed for stability
        for _ in range(1000):
            state = model.step(0.0, state, dt=0.0001)

        # Should oscillate rapidly but remain bounded
        assert abs(state[0]) < 5.0

    def test_mixed_time_scales(self):
        """Test coupling of fast and slow systems."""
        # Fast cardiac oscillator
        cardiac = VanDerPolOscillator(omega=10.0)
        # Slow neural oscillator
        neural = FitzHughNagumo(c=100.0)

        model = HeartBrainCouplingModel(
            neural_model=neural,
            cardiac_model=cardiac,
            coupling=CouplingParameters()
        )

        state = (0.1, 0.1, 1.0, 0.0)

        # Small timestep for fast component
        for _ in range(1000):
            state = model.step(0.0, state, dt=0.0001)

        # Should remain stable
        assert all(abs(x) < 10.0 for x in state)


class TestEdgeCaseCombinations:
    """Test combinations of edge cases."""

    def test_zero_state_with_zero_parameters(self):
        """Test all zeros."""
        model = VanDerPolOscillator(mu=0.0, omega=0.0, damping=0.0)

        dx, dy = model.derivatives(0.0, (0.0, 0.0))

        # Everything should be zero
        assert dx == 0.0
        assert dy == 0.0

    def test_alternating_signs(self):
        """Test with alternating positive/negative values."""
        model = FitzHughNagumo()

        states = [
            (1.0, -1.0),
            (-1.0, 1.0),
            (1.0, 1.0),
            (-1.0, -1.0),
        ]

        for state in states:
            dv, dw = model.derivatives(0.0, state)
            # Should all produce valid results
            assert isinstance(dv, float)
            assert isinstance(dw, float)

    def test_extreme_parameter_combinations(self):
        """Test with multiple extreme parameters."""
        model = VanDerPolOscillator(mu=1000.0, omega=0.001, damping=500.0)

        # Extreme parameters but should not crash
        try:
            dx, dy = model.derivatives(0.0, (10.0, 10.0))
            assert isinstance(dx, float)
        except (OverflowError, FloatingPointError):
            # Acceptable for extreme cases
            pass


class TestDelayBufferRobustness:
    """Test robustness of delay buffer in coupled model."""

    def test_delay_longer_than_history(self):
        """Test delay longer than available history."""
        model = HeartBrainCouplingModel()

        # Add minimal history
        model.history.append((0.0, (1.0, 0.5), (2.0, 1.5)))

        # Request delay longer than history
        result = model._delayed_state(0.1, delay=10.0, component="neural", fallback=(0.0, 0.0))

        # Should return earliest history entry
        assert result == (1.0, 0.5)

    def test_empty_history_with_delay(self):
        """Test delay lookup with empty history."""
        model = HeartBrainCouplingModel()

        # Empty history
        result = model._delayed_state(1.0, delay=0.5, component="neural", fallback=(3.0, 2.0))

        # Should return fallback
        assert result == (3.0, 2.0)

    def test_many_delay_lookups(self):
        """Test many successive delay lookups."""
        model = HeartBrainCouplingModel()

        # Populate history
        for i in range(1000):
            t = i * 0.01
            model.history.append((t, (i * 0.01, i * 0.02), (i * 0.03, i * 0.04)))

        # Many lookups should not slow down significantly
        for i in range(100):
            result = model._delayed_state(5.0, delay=2.0, component="neural", fallback=(0.0, 0.0))
            assert isinstance(result[0], float)


class TestSimulationRobustness:
    """Test robustness of full simulation."""

    def test_simulation_with_extreme_initial_conditions(self):
        """Test simulation starting from extreme state."""
        model = HeartBrainCouplingModel()

        # Extreme initial conditions
        initial = (100.0, -100.0, 100.0, -100.0)

        try:
            trajectory = model.simulate(initial, t_span=(0.0, 1.0), dt=0.0001)
            # May be unstable but shouldn't crash
            assert len(trajectory) > 0
        except (OverflowError, ValueError):
            # Acceptable for extreme initial conditions
            pass

    def test_simulation_recovery_from_perturbation(self):
        """Test that simulation recovers from large perturbation."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)

        # Start near limit cycle
        state = (1.0, 0.0)

        # Simulate to get on limit cycle
        for _ in range(1000):
            state = model.step(0.0, state, dt=0.01)

        # Large perturbation
        state = (state[0] + 5.0, state[1])

        # Should recover back to limit cycle
        for _ in range(5000):
            state = model.step(0.0, state, dt=0.01)

        # Should be back near limit cycle (amplitude ~2)
        amplitude = (state[0]**2 + state[1]**2)**0.5
        assert amplitude < 5.0  # Recovered from perturbation

    def test_simulation_with_varying_timestep(self):
        """Test simulation robustness to timestep changes."""
        model = FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.5)

        state = (0.0, 0.0)

        # Vary timestep
        timesteps = [0.001, 0.01, 0.001, 0.005, 0.01, 0.001]

        for dt in timesteps * 100:
            state = model.step(0.0, state, dt)

        # Should remain bounded
        assert abs(state[0]) < 10.0
        assert abs(state[1]) < 10.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
