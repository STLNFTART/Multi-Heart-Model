"""
Comprehensive unit tests for HeartBrainCouplingModel.

Tests cover:
- Coupling parameter validation
- History buffer management
- Delayed state lookups
- Different coupling strengths
- Different delay values
- Synchronization and desynchronization
- Integration consistency
- extract_series() functionality
- Edge cases and error handling
"""

import pytest
import math
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import CouplingParameters, HeartBrainCouplingModel


class TestCouplingParameters:
    """Test CouplingParameters dataclass."""

    def test_default_parameters(self):
        """Test default coupling parameters."""
        params = CouplingParameters()

        assert params.neural_to_cardiac_gain == 0.4
        assert params.cardiac_to_neural_gain == 0.2
        assert params.neural_delay == 0.0
        assert params.cardiac_delay == 0.0
        assert params.neural_bias == 0.0
        assert params.cardiac_bias == 0.0

    def test_custom_parameters(self):
        """Test custom coupling parameters."""
        params = CouplingParameters(
            neural_to_cardiac_gain=0.6,
            cardiac_to_neural_gain=0.4,
            neural_delay=0.1,
            cardiac_delay=0.15,
            neural_bias=0.1,
            cardiac_bias=0.05
        )

        assert params.neural_to_cardiac_gain == 0.6
        assert params.cardiac_to_neural_gain == 0.4
        assert params.neural_delay == 0.1
        assert params.cardiac_delay == 0.15
        assert params.neural_bias == 0.1
        assert params.cardiac_bias == 0.05


class TestHeartBrainCouplingModelInitialization:
    """Test model initialization."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        model = HeartBrainCouplingModel()

        assert isinstance(model.neural_model, FitzHughNagumo)
        assert isinstance(model.cardiac_model, VanDerPolOscillator)
        assert isinstance(model.coupling, CouplingParameters)
        assert len(model.history) == 0

    def test_custom_models(self):
        """Test initialization with custom models."""
        neural = FitzHughNagumo(a=0.5, b=0.5, c=2.0)
        cardiac = VanDerPolOscillator(mu=2.0, omega=1.5)
        coupling = CouplingParameters(neural_to_cardiac_gain=0.8)

        model = HeartBrainCouplingModel(
            neural_model=neural,
            cardiac_model=cardiac,
            coupling=coupling
        )

        assert model.neural_model.a == 0.5
        assert model.cardiac_model.mu == 2.0
        assert model.coupling.neural_to_cardiac_gain == 0.8


class TestHistoryManagement:
    """Test history buffer management."""

    def test_history_initially_empty(self):
        """Test that history starts empty."""
        model = HeartBrainCouplingModel()
        assert len(model.history) == 0

    def test_reset_history(self):
        """Test reset_history() clears buffer."""
        model = HeartBrainCouplingModel()

        # Add some history
        model.history.append((0.0, (1.0, 0.5), (2.0, 1.5)))
        model.history.append((0.1, (1.1, 0.6), (2.1, 1.6)))

        assert len(model.history) == 2

        # Reset
        model.reset_history()
        assert len(model.history) == 0

    def test_history_populated_during_simulation(self):
        """Test that simulate() populates history."""
        model = HeartBrainCouplingModel()
        initial_state = (0.0, 0.0, 1.0, 0.0)

        model.simulate(initial_state, t_span=(0.0, 0.1), dt=0.01)

        # Should have history entries
        assert len(model.history) > 0

    def test_history_cleared_on_new_simulation(self):
        """Test that new simulation resets history."""
        model = HeartBrainCouplingModel()
        initial_state = (0.0, 0.0, 1.0, 0.0)

        # First simulation
        model.simulate(initial_state, t_span=(0.0, 0.1), dt=0.01)
        first_len = len(model.history)

        # Second simulation
        model.simulate(initial_state, t_span=(0.0, 0.05), dt=0.01)
        second_len = len(model.history)

        # Second simulation should be shorter
        assert second_len < first_len


class TestDelayedStateLookup:
    """Test delayed state lookup functionality."""

    def test_delayed_state_with_zero_delay(self):
        """Test that zero delay returns fallback."""
        model = HeartBrainCouplingModel()
        fallback = (1.0, 0.5)

        result = model._delayed_state(1.0, delay=0.0, component="neural", fallback=fallback)

        assert result == fallback

    def test_delayed_state_with_empty_history(self):
        """Test delayed state with empty history."""
        model = HeartBrainCouplingModel()
        fallback = (1.0, 0.5)

        result = model._delayed_state(1.0, delay=0.1, component="neural", fallback=fallback)

        assert result == fallback

    def test_delayed_state_lookup_neural(self):
        """Test looking up delayed neural state."""
        model = HeartBrainCouplingModel()

        # Add history
        model.history.append((0.0, (1.0, 0.5), (2.0, 1.5)))
        model.history.append((0.1, (1.1, 0.6), (2.1, 1.6)))
        model.history.append((0.2, (1.2, 0.7), (2.2, 1.7)))

        # Look up state 0.1 seconds ago at t=0.2
        result = model._delayed_state(0.2, delay=0.1, component="neural", fallback=(0.0, 0.0))

        # Should get the entry at t=0.1
        assert result == (1.1, 0.6)

    def test_delayed_state_lookup_cardiac(self):
        """Test looking up delayed cardiac state."""
        model = HeartBrainCouplingModel()

        # Add history
        model.history.append((0.0, (1.0, 0.5), (2.0, 1.5)))
        model.history.append((0.1, (1.1, 0.6), (2.1, 1.6)))

        # Look up cardiac state
        result = model._delayed_state(0.1, delay=0.1, component="cardiac", fallback=(0.0, 0.0))

        # Should get the entry at t=0.0
        assert result == (2.0, 1.5)

    def test_delayed_state_before_history_start(self):
        """Test delayed state when requested time is before history."""
        model = HeartBrainCouplingModel()

        # Add history starting at t=1.0
        model.history.append((1.0, (1.0, 0.5), (2.0, 1.5)))
        model.history.append((1.1, (1.1, 0.6), (2.1, 1.6)))

        # Request state at t=1.1 with delay=0.5 (would need t=0.6)
        result = model._delayed_state(1.1, delay=0.5, component="neural", fallback=(0.0, 0.0))

        # Should return earliest history entry
        assert result == (1.0, 0.5)


class TestCouplingDerivatives:
    """Test coupled system derivatives."""

    def test_derivatives_no_coupling(self):
        """Test derivatives with zero coupling gains."""
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.0,
            cardiac_to_neural_gain=0.0
        )
        model = HeartBrainCouplingModel(coupling=coupling)
        state = (0.0, 0.0, 1.0, 0.0)

        dv, dw, dx, dy = model.derivatives(0.0, state)

        # Should match uncoupled models
        neural_dv, neural_dw = model.neural_model.derivatives(0.0, (0.0, 0.0))
        cardiac_dx, cardiac_dy = model.cardiac_model.derivatives(0.0, (1.0, 0.0))

        assert dv == neural_dv
        assert dw == neural_dw
        assert dx == cardiac_dx
        assert dy == cardiac_dy

    def test_derivatives_with_neural_to_cardiac(self):
        """Test neural-to-cardiac coupling."""
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.5,
            cardiac_to_neural_gain=0.0
        )
        model = HeartBrainCouplingModel(coupling=coupling)
        state = (1.0, 0.5, 0.5, 0.3)

        dv, dw, dx, dy = model.derivatives(0.0, state)

        # Neural should be uncoupled
        neural_dv, neural_dw = model.neural_model.derivatives(0.0, (1.0, 0.5))
        assert dv == neural_dv
        assert dw == neural_dw

        # Cardiac should receive input from neural v
        cardiac_input = 0.5 * 1.0  # gain * neural_v
        cardiac_dx, cardiac_dy = model.cardiac_model.derivatives(
            0.0, (0.5, 0.3), input_force=cardiac_input
        )
        assert dx == cardiac_dx
        assert dy == cardiac_dy

    def test_derivatives_with_cardiac_to_neural(self):
        """Test cardiac-to-neural coupling."""
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.0,
            cardiac_to_neural_gain=0.3
        )
        model = HeartBrainCouplingModel(coupling=coupling)
        state = (0.5, 0.2, 1.0, 0.5)

        dv, dw, dx, dy = model.derivatives(0.0, state)

        # Cardiac should be uncoupled
        cardiac_dx, cardiac_dy = model.cardiac_model.derivatives(0.0, (1.0, 0.5))
        assert dx == cardiac_dx
        assert dy == cardiac_dy

        # Neural should receive input from cardiac x
        neural_input = 0.3 * 1.0  # gain * cardiac_x
        neural_dv, neural_dw = model.neural_model.derivatives(
            0.0, (0.5, 0.2), input_drive=neural_input
        )
        assert dv == neural_dv
        assert dw == neural_dw

    def test_derivatives_with_bidirectional_coupling(self):
        """Test bidirectional coupling."""
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.4,
            cardiac_to_neural_gain=0.2
        )
        model = HeartBrainCouplingModel(coupling=coupling)
        state = (0.8, 0.4, 0.6, 0.3)

        dv, dw, dx, dy = model.derivatives(0.0, state)

        # Both should receive coupling
        neural_input = 0.2 * 0.6  # cardiac_to_neural_gain * cardiac_x
        cardiac_input = 0.4 * 0.8  # neural_to_cardiac_gain * neural_v

        neural_dv, neural_dw = model.neural_model.derivatives(
            0.0, (0.8, 0.4), input_drive=neural_input
        )
        cardiac_dx, cardiac_dy = model.cardiac_model.derivatives(
            0.0, (0.6, 0.3), input_force=cardiac_input
        )

        assert dv == pytest.approx(neural_dv)
        assert dw == pytest.approx(neural_dw)
        assert dx == pytest.approx(cardiac_dx)
        assert dy == pytest.approx(cardiac_dy)

    def test_derivatives_with_bias(self):
        """Test coupling with bias terms."""
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.0,
            cardiac_to_neural_gain=0.0,
            neural_bias=0.2,
            cardiac_bias=0.1
        )
        model = HeartBrainCouplingModel(coupling=coupling)
        state = (0.0, 0.0, 0.0, 0.0)

        dv, dw, dx, dy = model.derivatives(0.0, state)

        # Check that bias is applied
        neural_dv, neural_dw = model.neural_model.derivatives(
            0.0, (0.0, 0.0), input_drive=0.2
        )
        cardiac_dx, cardiac_dy = model.cardiac_model.derivatives(
            0.0, (0.0, 0.0), input_force=0.1
        )

        assert dv == neural_dv
        assert dw == neural_dw
        assert dx == cardiac_dx
        assert dy == cardiac_dy


class TestSimulation:
    """Test simulation functionality."""

    def test_simulate_basic(self):
        """Test basic simulation."""
        model = HeartBrainCouplingModel()
        initial_state = (0.0, 0.0, 1.0, 0.0)

        trajectory = model.simulate(initial_state, t_span=(0.0, 0.1), dt=0.01)

        assert len(trajectory) > 0
        assert trajectory[0][0] == 0.0  # First time
        assert trajectory[0][1] == initial_state  # First state

    def test_simulate_time_steps(self):
        """Test correct number of time steps."""
        model = HeartBrainCouplingModel()
        initial_state = (0.0, 0.0, 1.0, 0.0)

        trajectory = model.simulate(initial_state, t_span=(0.0, 0.5), dt=0.1)

        times = [t for t, _ in trajectory]
        assert times[0] == pytest.approx(0.0)
        assert times[-1] == pytest.approx(0.5)
        assert len(times) == 6  # 0.0, 0.1, 0.2, 0.3, 0.4, 0.5

    def test_simulate_invalid_t_span(self):
        """Test that invalid t_span raises error."""
        model = HeartBrainCouplingModel()
        initial_state = (0.0, 0.0, 1.0, 0.0)

        with pytest.raises(ValueError, match="t_span must have stop > start"):
            model.simulate(initial_state, t_span=(1.0, 0.0), dt=0.01)

    def test_simulate_invalid_dt(self):
        """Test that invalid dt raises error."""
        model = HeartBrainCouplingModel()
        initial_state = (0.0, 0.0, 1.0, 0.0)

        with pytest.raises(ValueError, match="dt must be positive"):
            model.simulate(initial_state, t_span=(0.0, 1.0), dt=0.0)

        with pytest.raises(ValueError, match="dt must be positive"):
            model.simulate(initial_state, t_span=(0.0, 1.0), dt=-0.01)

    def test_simulate_state_evolution(self):
        """Test that state evolves during simulation."""
        model = HeartBrainCouplingModel()
        initial_state = (0.0, 0.0, 1.0, 0.0)

        trajectory = model.simulate(initial_state, t_span=(0.0, 1.0), dt=0.01)

        # State should change
        final_state = trajectory[-1][1]
        assert final_state != initial_state


class TestStepFunction:
    """Test step function."""

    def test_step_basic(self):
        """Test basic step functionality."""
        model = HeartBrainCouplingModel()
        state = (0.0, 0.0, 1.0, 0.0)
        dt = 0.01

        new_state = model.step(0.0, state, dt)

        # Should return 4-tuple
        assert len(new_state) == 4
        assert all(isinstance(x, float) for x in new_state)

    def test_step_uses_derivatives(self):
        """Test that step uses derivatives correctly."""
        model = HeartBrainCouplingModel()
        state = (0.5, 0.3, 0.8, 0.4)
        dt = 0.01

        # Manual computation
        dv, dw, dx, dy = model.derivatives(0.0, state)
        expected = (
            state[0] + dt * dv,
            state[1] + dt * dw,
            state[2] + dt * dx,
            state[3] + dt * dy
        )

        # Step computation
        actual = model.step(0.0, state, dt)

        assert actual[0] == pytest.approx(expected[0])
        assert actual[1] == pytest.approx(expected[1])
        assert actual[2] == pytest.approx(expected[2])
        assert actual[3] == pytest.approx(expected[3])


class TestExtractSeries:
    """Test extract_series functionality."""

    def test_extract_series_basic(self):
        """Test basic series extraction."""
        model = HeartBrainCouplingModel()
        initial_state = (0.0, 0.0, 1.0, 0.0)

        trajectory = model.simulate(initial_state, t_span=(0.0, 0.1), dt=0.01)
        times, neural, cardiac = model.extract_series(trajectory)

        assert len(times) == len(trajectory)
        assert len(neural) == len(trajectory)
        assert len(cardiac) == len(trajectory)

    def test_extract_series_values(self):
        """Test that extracted values are correct."""
        model = HeartBrainCouplingModel()

        # Create simple trajectory
        trajectory = [
            (0.0, (0.1, 0.2, 0.3, 0.4)),
            (0.1, (0.5, 0.6, 0.7, 0.8)),
        ]

        times, neural, cardiac = model.extract_series(trajectory)

        assert times == [0.0, 0.1]
        assert neural == [0.1, 0.5]  # v values
        assert cardiac == [0.3, 0.7]  # x values

    def test_extract_series_from_simulation(self):
        """Test extraction from actual simulation."""
        model = HeartBrainCouplingModel()
        initial_state = (0.0, 0.0, 1.0, 0.0)

        trajectory = model.simulate(initial_state, t_span=(0.0, 0.5), dt=0.01)
        times, neural, cardiac = model.extract_series(trajectory)

        # Check lengths match
        assert len(times) == len(neural) == len(cardiac)

        # Check time values
        assert times[0] == pytest.approx(0.0)
        assert times[-1] == pytest.approx(0.5)

        # Check initial values
        assert neural[0] == 0.0
        assert cardiac[0] == 1.0


class TestCouplingStrengths:
    """Test different coupling strength scenarios."""

    def test_weak_coupling(self):
        """Test weak coupling scenario."""
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.1,
            cardiac_to_neural_gain=0.1
        )
        model = HeartBrainCouplingModel(coupling=coupling)

        trajectory = model.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 10.0),
            dt=0.01
        )

        # Should produce valid trajectory
        assert len(trajectory) > 0

    def test_strong_coupling(self):
        """Test strong coupling scenario."""
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.8,
            cardiac_to_neural_gain=0.6
        )
        model = HeartBrainCouplingModel(coupling=coupling)

        trajectory = model.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 10.0),
            dt=0.01
        )

        # Should produce valid trajectory
        assert len(trajectory) > 0

    def test_asymmetric_coupling(self):
        """Test asymmetric coupling."""
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.8,
            cardiac_to_neural_gain=0.1
        )
        model = HeartBrainCouplingModel(coupling=coupling)

        trajectory = model.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 5.0),
            dt=0.01
        )

        # Should produce valid trajectory
        assert len(trajectory) > 0


class TestDelayEffects:
    """Test different delay scenarios."""

    def test_small_delay(self):
        """Test small coupling delays."""
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.4,
            cardiac_to_neural_gain=0.2,
            neural_delay=0.01,
            cardiac_delay=0.01
        )
        model = HeartBrainCouplingModel(coupling=coupling)

        trajectory = model.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 1.0),
            dt=0.001
        )

        # Should complete without issues
        assert len(trajectory) > 0

    def test_moderate_delay(self):
        """Test moderate coupling delays."""
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.4,
            cardiac_to_neural_gain=0.2,
            neural_delay=0.12,
            cardiac_delay=0.15
        )
        model = HeartBrainCouplingModel(coupling=coupling)

        trajectory = model.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 2.0),
            dt=0.01
        )

        # Should complete without issues
        assert len(trajectory) > 0

    def test_asymmetric_delays(self):
        """Test asymmetric delays."""
        coupling = CouplingParameters(
            neural_to_cardiac_gain=0.4,
            cardiac_to_neural_gain=0.2,
            neural_delay=0.05,
            cardiac_delay=0.2
        )
        model = HeartBrainCouplingModel(coupling=coupling)

        trajectory = model.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 1.0),
            dt=0.01
        )

        # Should complete
        assert len(trajectory) > 0


class TestNumericalStability:
    """Test numerical stability of coupled system."""

    def test_long_simulation_stability(self):
        """Test stability over long simulations."""
        model = HeartBrainCouplingModel()

        trajectory = model.simulate(
            initial_state=(0.1, 0.1, 0.1, 0.1),
            t_span=(0.0, 50.0),
            dt=0.001
        )

        # Check no NaN or Inf
        for t, state in trajectory:
            assert not math.isnan(t)
            for val in state:
                assert not math.isnan(val)
                assert not math.isinf(val)

    def test_bounded_oscillations(self):
        """Test that oscillations remain bounded."""
        model = HeartBrainCouplingModel()

        trajectory = model.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 20.0),
            dt=0.001
        )

        times, neural, cardiac = model.extract_series(trajectory)

        # Should remain in reasonable bounds
        assert all(abs(v) < 10.0 for v in neural)
        assert all(abs(x) < 10.0 for x in cardiac)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
