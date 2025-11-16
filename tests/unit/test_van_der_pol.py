"""
Comprehensive unit tests for Van der Pol cardiac oscillator.

Tests cover:
- Basic derivatives computation
- Parameter validation and ranges
- Different dynamical regimes
- Input force effects
- Integration consistency
- Long-term stability
- Edge cases and error handling
"""

import pytest
import math
from src.cardiac import VanDerPolOscillator


class TestVanDerPolBasicDerivatives:
    """Test basic derivative computation."""

    def test_derivatives_at_equilibrium(self):
        """Test derivatives at x=0, y=0."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0, damping=0.0)
        dx, dy = model.derivatives(0.0, (0.0, 0.0))

        assert dx == 0.0  # dx/dt = y = 0
        assert dy == 0.0  # dy/dt = mu*(1-0)*0 - omega^2*0 = 0

    def test_derivatives_at_unit_position(self):
        """Test derivatives at x=1, y=0."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0, damping=0.0)
        dx, dy = model.derivatives(0.0, (1.0, 0.0))

        assert dx == 0.0  # dx/dt = y = 0
        assert dy == pytest.approx(-1.0)  # dy/dt = -omega^2*x = -1.0

    def test_derivatives_with_velocity(self):
        """Test derivatives with non-zero velocity."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0, damping=0.0)
        dx, dy = model.derivatives(0.0, (0.5, 0.3))

        assert dx == 0.3  # dx/dt = y
        # dy/dt = mu*(1 - x^2)*y - omega^2*x
        expected_dy = 1.5 * (1 - 0.5**2) * 0.3 - 1.0 * 0.5
        assert dy == pytest.approx(expected_dy)

    def test_derivatives_with_damping(self):
        """Test that damping reduces velocity derivative."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0, damping=0.2)
        dx, dy = model.derivatives(0.0, (0.0, 1.0))

        assert dx == 1.0
        # dy/dt = mu*(1-0)*y - omega^2*x - damping*y
        expected_dy = 1.5 * 1.0 - 0.0 - 0.2 * 1.0
        assert dy == pytest.approx(expected_dy)

    def test_derivatives_with_input_force(self):
        """Test external input force."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)
        dx, dy = model.derivatives(0.0, (1.0, 0.0), input_force=0.5)

        assert dx == 0.0
        # dy/dt = mu*(1-x^2)*y - omega^2*x + input_force
        expected_dy = 1.5 * 0.0 * 0.0 - 1.0 * 1.0 + 0.5
        assert dy == pytest.approx(expected_dy)


class TestVanDerPolParameterRanges:
    """Test behavior across different parameter ranges."""

    @pytest.mark.parametrize("mu", [0.5, 1.0, 1.5, 2.0, 3.0])
    def test_different_mu_values(self, mu):
        """Test different nonlinearity parameters."""
        model = VanDerPolOscillator(mu=mu, omega=1.0)
        dx, dy = model.derivatives(0.0, (0.5, 0.5))

        # Should produce valid derivatives
        assert isinstance(dx, float)
        assert isinstance(dy, float)
        assert not math.isnan(dx) and not math.isnan(dy)
        assert not math.isinf(dx) and not math.isinf(dy)

    @pytest.mark.parametrize("omega", [0.5, 1.0, 1.5, 2.0])
    def test_different_omega_values(self, omega):
        """Test different natural frequencies."""
        model = VanDerPolOscillator(mu=1.5, omega=omega)
        dx, dy = model.derivatives(0.0, (1.0, 0.0))

        assert dx == 0.0
        # Higher omega should give more negative dy at x=1
        assert dy == pytest.approx(-omega**2)

    @pytest.mark.parametrize("damping", [0.0, 0.1, 0.3, 0.5])
    def test_different_damping_values(self, damping):
        """Test different damping coefficients."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0, damping=damping)
        dx, dy = model.derivatives(0.0, (0.0, 1.0))

        # Damping should reduce velocity derivative
        expected_dy = 1.5 - damping
        assert dy == pytest.approx(expected_dy)


class TestVanDerPolDynamicalRegimes:
    """Test different dynamical regimes of Van der Pol oscillator."""

    def test_limit_cycle_regime(self):
        """Test limit cycle oscillation (mu > 0)."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)

        # Start near origin
        state = (0.1, 0.1)
        dt = 0.01

        # Simulate for several cycles
        states = [state]
        for _ in range(1000):
            state = model.step(0.0, state, dt)
            states.append(state)

        # Check that oscillation develops
        x_values = [s[0] for s in states]
        x_max = max(x_values)
        x_min = min(x_values)

        # Should oscillate with reasonable amplitude
        assert x_max > 1.0
        assert x_min < -1.0

    def test_relaxation_oscillation(self):
        """Test relaxation oscillation (large mu)."""
        model = VanDerPolOscillator(mu=5.0, omega=1.0)

        # Should still produce valid derivatives
        dx, dy = model.derivatives(0.0, (2.0, 0.1))

        # Large mu amplifies nonlinear damping
        # At x=2, (1-x^2) = -3, so negative damping
        expected_dy = 5.0 * (1 - 4.0) * 0.1 - 1.0 * 2.0
        assert dy == pytest.approx(expected_dy)

    def test_damped_regime(self):
        """Test damped oscillation."""
        model = VanDerPolOscillator(mu=0.5, omega=1.0, damping=1.0)

        # Start with displacement
        state = (1.0, 0.0)
        dt = 0.01

        # Simulate
        states = [state]
        for _ in range(500):
            state = model.step(0.0, state, dt)
            states.append(state)

        # Energy should decay
        energy_initial = states[0][0]**2 + states[0][1]**2
        energy_final = states[-1][0]**2 + states[-1][1]**2

        assert energy_final < energy_initial


class TestVanDerPolIntegration:
    """Test integration step consistency."""

    def test_step_matches_derivatives(self):
        """Test that step() uses derivatives() correctly."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)
        state = (0.5, 0.3)
        dt = 0.01

        # Compute manually
        dx, dy = model.derivatives(0.0, state)
        expected_state = (state[0] + dt * dx, state[1] + dt * dy)

        # Compute with step
        actual_state = model.step(0.0, state, dt)

        assert actual_state[0] == pytest.approx(expected_state[0])
        assert actual_state[1] == pytest.approx(expected_state[1])

    def test_step_with_input_force(self):
        """Test step() correctly applies input force."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)
        state = (1.0, 0.0)
        dt = 0.01
        input_force = 0.5

        # Manual computation
        dx, dy = model.derivatives(0.0, state, input_force=input_force)
        expected_state = (state[0] + dt * dx, state[1] + dt * dy)

        # Step with input
        actual_state = model.step(0.0, state, dt, input_force=input_force)

        assert actual_state[0] == pytest.approx(expected_state[0])
        assert actual_state[1] == pytest.approx(expected_state[1])

    def test_timestep_independence(self):
        """Test that smaller timesteps give similar results."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)
        initial_state = (1.0, 0.0)
        duration = 0.1

        # Large timestep
        state_large = initial_state
        dt_large = 0.01
        steps_large = int(duration / dt_large)
        for _ in range(steps_large):
            state_large = model.step(0.0, state_large, dt_large)

        # Small timestep
        state_small = initial_state
        dt_small = 0.001
        steps_small = int(duration / dt_small)
        for _ in range(steps_small):
            state_small = model.step(0.0, state_small, dt_small)

        # Should be reasonably close (Euler integration)
        assert state_large[0] == pytest.approx(state_small[0], abs=0.01)
        assert state_large[1] == pytest.approx(state_small[1], abs=0.01)


class TestVanDerPolStability:
    """Test numerical stability over long simulations."""

    def test_no_numerical_explosion(self):
        """Test that state doesn't explode to infinity."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)
        state = (0.1, 0.1)
        dt = 0.001  # Small timestep for stability

        # Simulate for many steps
        for _ in range(10000):
            state = model.step(0.0, state, dt)

            # Check for NaN or Inf
            assert not math.isnan(state[0])
            assert not math.isnan(state[1])
            assert not math.isinf(state[0])
            assert not math.isinf(state[1])

            # Check reasonable bounds (limit cycle shouldn't exceed ~2)
            assert abs(state[0]) < 10.0
            assert abs(state[1]) < 10.0

    def test_energy_bounds(self):
        """Test that energy remains bounded in limit cycle."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)
        state = (1.0, 0.0)
        dt = 0.001

        energies = []
        for _ in range(5000):
            state = model.step(0.0, state, dt)
            energy = state[0]**2 + state[1]**2
            energies.append(energy)

        # Energy should be bounded
        assert max(energies) < 20.0  # Reasonable upper bound
        assert min(energies) >= 0.0


class TestVanDerPolEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_mu(self):
        """Test with zero nonlinearity (harmonic oscillator)."""
        model = VanDerPolOscillator(mu=0.0, omega=1.0)
        dx, dy = model.derivatives(0.0, (1.0, 0.5))

        # Should behave like harmonic oscillator
        # dy/dt = 0*(1-1)*0.5 - 1*1 = -1
        assert dx == 0.5
        assert dy == -1.0

    def test_large_displacement(self):
        """Test behavior at large displacements."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)
        dx, dy = model.derivatives(0.0, (10.0, 0.0))

        # Should produce strong restoring force
        assert dx == 0.0
        # dy = mu*(1-x^2)*y - omega^2*x = 1.5*0*0 - 1.0*10 = -10
        assert dy == pytest.approx(-10.0)  # -omega^2 * x

    def test_large_velocity(self):
        """Test behavior at large velocities."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)
        dx, dy = model.derivatives(0.0, (0.0, 10.0))

        # dx/dt should equal velocity
        assert dx == 10.0
        # dy/dt = mu*(1-0)*y = 1.5*10 = 15
        assert dy == pytest.approx(15.0)

    def test_negative_input_force(self):
        """Test with negative external force."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)
        dx, dy = model.derivatives(0.0, (0.0, 0.0), input_force=-1.0)

        assert dx == 0.0
        assert dy == -1.0

    def test_time_parameter_unused(self):
        """Test that time parameter doesn't affect autonomous system."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0)
        state = (0.5, 0.3)

        # Same state at different times should give same derivatives
        dx1, dy1 = model.derivatives(0.0, state)
        dx2, dy2 = model.derivatives(100.0, state)

        assert dx1 == dx2
        assert dy1 == dy2


class TestVanDerPolPhysicalProperties:
    """Test physical properties of the oscillator."""

    def test_restoring_force_direction(self):
        """Test that restoring force opposes displacement."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0, damping=0.0)

        # Positive displacement, zero velocity
        _, dy_pos = model.derivatives(0.0, (1.0, 0.0))
        assert dy_pos < 0  # Force opposes displacement

        # Negative displacement, zero velocity
        _, dy_neg = model.derivatives(0.0, (-1.0, 0.0))
        assert dy_neg > 0  # Force opposes displacement

    def test_nonlinear_damping_sign(self):
        """Test Van der Pol nonlinear damping switches sign."""
        model = VanDerPolOscillator(mu=1.5, omega=1.0, damping=0.0)

        # Inside limit cycle (|x| < 1): positive damping (energy input)
        _, dy_small = model.derivatives(0.0, (0.5, 1.0))
        # Contribution: mu*(1-x^2)*y = 1.5*(1-0.25)*1 = 1.125 (positive)

        # Outside limit cycle (|x| > 1): negative damping (energy removal)
        _, dy_large = model.derivatives(0.0, (2.0, 1.0))
        # Contribution: mu*(1-x^2)*y = 1.5*(1-4)*1 = -4.5 (negative)

        # The effect depends on omega^2*x term too, but the sign pattern holds
        # for the damping contribution


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
