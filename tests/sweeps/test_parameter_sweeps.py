"""
Comprehensive Parameter Sweep Tests

Executes exhaustive parameter sweeps and state variable vector testing across
all models in the Multi-Heart-Model codebase.

Tests:
1. Core oscillator models (FitzHugh-Nagumo, Van der Pol)
2. Heart-Brain Coupling Model
3. Microprocessor control systems
4. Organ chip models
5. Numerical stability analysis
6. Multi-dimensional parameter interactions

Author: AI Assistant
Date: 2025-11-14
"""

import pytest
import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any
import itertools
import json
from dataclasses import dataclass, asdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.neural import FitzHughNagumo
from src.cardiac import VanDerPolOscillator
from src.coupling import CouplingParameters, HeartBrainCouplingModel


@dataclass
class SweepResult:
    """Results from a parameter sweep."""
    parameter_name: str
    parameter_values: List[float]
    test_metric: str
    results: List[float]
    passed: bool
    failures: List[str]


class TestFitzHughNagumoParameterSweeps:
    """Comprehensive parameter sweeps for FitzHugh-Nagumo model."""

    def test_parameter_a_sweep(self):
        """Sweep parameter 'a' across physiological range."""
        a_values = [0.1, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
        results = []

        for a in a_values:
            model = FitzHughNagumo(a=a, b=0.8, c=3.0)

            # Test derivatives at state where 'a' has effect (w != 0)
            dv, dw = model.derivatives(0.0, (0.5, 0.5), input_drive=0.0)

            # Check for numerical stability
            assert not (abs(dv) > 1e6 or abs(dw) > 1e6), \
                f"Unstable derivatives at a={a}: dv={dv}, dw={dw}"

            # Store recovery rate (affected by 'a')
            results.append(dw)

        # Results should vary with parameter
        assert len(set(results)) > 1, "Parameter 'a' has no effect"
        print(f"✓ Parameter 'a' sweep: {len(a_values)} values tested")

    def test_parameter_b_sweep(self):
        """Sweep parameter 'b' across physiological range."""
        b_values = [0.1, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5]
        results = []

        for b in b_values:
            model = FitzHughNagumo(a=0.7, b=b, c=3.0)
            # Use state with non-zero w where 'b' has effect
            dv, dw = model.derivatives(0.0, (0.5, 0.5), input_drive=0.0)

            assert not (abs(dv) > 1e6 or abs(dw) > 1e6), \
                f"Unstable at b={b}"

            results.append(dw)

        assert len(set(results)) > 1, "Parameter 'b' has no effect"
        print(f"✓ Parameter 'b' sweep: {len(b_values)} values tested")

    def test_parameter_c_sweep(self):
        """Sweep parameter 'c' (timescale) across range."""
        c_values = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0]
        results = []

        for c in c_values:
            model = FitzHughNagumo(a=0.7, b=0.8, c=c)
            dv, dw = model.derivatives(0.0, (0.5, 0.0), input_drive=0.0)

            assert not (abs(dv) > 1e6 or abs(dw) > 1e6), \
                f"Unstable at c={c}"

            # Recovery rate should scale with 1/c
            results.append(dw)

        assert len(set(results)) > 1, "Parameter 'c' has no effect"
        print(f"✓ Parameter 'c' sweep: {len(c_values)} values tested")

    def test_stimulus_amplitude_sweep(self):
        """Sweep stimulus amplitude from negative to positive."""
        stimulus_values = [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
        results = []

        for stim in stimulus_values:
            model = FitzHughNagumo(stimulus_amplitude=stim)
            dv, dw = model.derivatives(0.0, (0.0, 0.0), input_drive=0.0)

            assert not (abs(dv) > 1e6 or abs(dw) > 1e6), \
                f"Unstable at stimulus={stim}"

            results.append(dv)

        # Stimulus should shift activation
        assert max(results) - min(results) > 1.0, \
            "Stimulus has insufficient effect"
        print(f"✓ Stimulus amplitude sweep: {len(stimulus_values)} values tested")

    def test_input_drive_sweep(self):
        """Sweep external input drive."""
        drive_values = [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        results = []

        for drive in drive_values:
            model = FitzHughNagumo()
            dv, dw = model.derivatives(0.0, (0.0, 0.0), input_drive=drive)

            assert not (abs(dv) > 1e6 or abs(dw) > 1e6), \
                f"Unstable at drive={drive}"

            results.append(dv)

        # Drive should have linear effect on dv
        assert max(results) - min(results) > 3.0, \
            "Input drive has insufficient effect"
        print(f"✓ Input drive sweep: {len(drive_values)} values tested")

    def test_state_vector_sweep_v(self):
        """Sweep state variable 'v' (voltage-like)."""
        v_values = [-3.0, -2.0, -1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
        results = []

        for v in v_values:
            model = FitzHughNagumo()
            dv, dw = model.derivatives(0.0, (v, 0.0), input_drive=0.0)

            # Check cubic nonlinearity
            assert not (abs(dv) > 1e6 or abs(dw) > 1e6), \
                f"Unstable at v={v}"

            results.append(dv)

        # Should see cubic nonlinearity effect
        print(f"✓ State 'v' sweep: {len(v_values)} values tested")

    def test_state_vector_sweep_w(self):
        """Sweep state variable 'w' (recovery)."""
        w_values = [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]
        results = []

        for w in w_values:
            model = FitzHughNagumo()
            dv, dw = model.derivatives(0.0, (0.5, w), input_drive=0.0)

            assert not (abs(dv) > 1e6 or abs(dw) > 1e6), \
                f"Unstable at w={w}"

            results.append(dv)

        # w should suppress activation
        assert max(results) - min(results) > 1.0, \
            "Recovery variable 'w' has insufficient effect"
        print(f"✓ State 'w' sweep: {len(w_values)} values tested")

    def test_combined_state_sweep(self):
        """Sweep both state variables in 2D grid."""
        v_values = [-2.0, -1.0, 0.0, 1.0, 2.0]
        w_values = [-1.0, 0.0, 1.0]

        count = 0
        for v, w in itertools.product(v_values, w_values):
            model = FitzHughNagumo()
            dv, dw_dot = model.derivatives(0.0, (v, w), input_drive=0.0)

            # Check stability
            assert not (abs(dv) > 1e6 or abs(dw_dot) > 1e6), \
                f"Unstable at (v={v}, w={w})"

            count += 1

        print(f"✓ Combined state sweep: {count} (v,w) combinations tested")

    def test_multi_parameter_sweep(self):
        """Test multiple parameter combinations."""
        a_values = [0.5, 0.7, 1.0]
        b_values = [0.6, 0.8, 1.0]
        c_values = [2.0, 3.0, 5.0]

        count = 0
        for a, b, c in itertools.product(a_values, b_values, c_values):
            model = FitzHughNagumo(a=a, b=b, c=c)
            dv, dw = model.derivatives(0.0, (0.5, 0.0), input_drive=0.0)

            assert not (abs(dv) > 1e6 or abs(dw) > 1e6), \
                f"Unstable at (a={a}, b={b}, c={c})"

            count += 1

        print(f"✓ Multi-parameter sweep: {count} (a,b,c) combinations tested")


class TestVanDerPolParameterSweeps:
    """Comprehensive parameter sweeps for Van der Pol oscillator."""

    def test_parameter_mu_sweep(self):
        """Sweep nonlinearity parameter 'mu'."""
        mu_values = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
        results = []

        for mu in mu_values:
            model = VanDerPolOscillator(mu=mu, omega=1.0)
            # Use state where mu has significant effect (x != ±1)
            dx, dy = model.derivatives(0.0, (0.5, 0.5), input_force=0.0)

            assert not (abs(dx) > 1e6 or abs(dy) > 1e6), \
                f"Unstable at mu={mu}"

            results.append(dy)

        assert len(set(results)) > 1, "Parameter 'mu' has no effect"
        print(f"✓ Parameter 'mu' sweep: {len(mu_values)} values tested")

    def test_parameter_omega_sweep(self):
        """Sweep frequency parameter 'omega'."""
        omega_values = [0.1, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0]
        results = []

        for omega in omega_values:
            model = VanDerPolOscillator(mu=1.5, omega=omega)
            dx, dy = model.derivatives(0.0, (1.0, 0.0), input_force=0.0)

            assert not (abs(dx) > 1e6 or abs(dy) > 1e6), \
                f"Unstable at omega={omega}"

            # omega^2 scales restoring force
            results.append(dy)

        assert max(results) - min(results) > 1.0, \
            "Parameter 'omega' has insufficient effect"
        print(f"✓ Parameter 'omega' sweep: {len(omega_values)} values tested")

    def test_parameter_damping_sweep(self):
        """Sweep damping parameter."""
        damping_values = [0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
        results = []

        for damping in damping_values:
            model = VanDerPolOscillator(mu=1.5, omega=1.0, damping=damping)
            dx, dy = model.derivatives(0.0, (1.0, 0.5), input_force=0.0)

            assert not (abs(dx) > 1e6 or abs(dy) > 1e6), \
                f"Unstable at damping={damping}"

            results.append(dy)

        # Damping should reduce velocity derivative
        assert max(results) - min(results) > 0.5, \
            "Damping parameter has insufficient effect"
        print(f"✓ Parameter 'damping' sweep: {len(damping_values)} values tested")

    def test_input_force_sweep(self):
        """Sweep external input force."""
        force_values = [-5.0, -3.0, -1.0, 0.0, 1.0, 3.0, 5.0, 10.0]
        results = []

        for force in force_values:
            model = VanDerPolOscillator()
            dx, dy = model.derivatives(0.0, (1.0, 0.0), input_force=force)

            assert not (abs(dx) > 1e6 or abs(dy) > 1e6), \
                f"Unstable at force={force}"

            results.append(dy)

        # Force should linearly affect dy
        assert max(results) - min(results) > 5.0, \
            "Input force has insufficient effect"
        print(f"✓ Input force sweep: {len(force_values)} values tested")

    def test_state_vector_sweep_x(self):
        """Sweep state variable 'x' (position)."""
        x_values = [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0]
        results = []

        for x in x_values:
            model = VanDerPolOscillator(mu=1.5)
            dx, dy = model.derivatives(0.0, (x, 0.5), input_force=0.0)

            assert not (abs(dx) > 1e6 or abs(dy) > 1e6), \
                f"Unstable at x={x}"

            results.append(dy)

        # Should see nonlinear damping effect
        print(f"✓ State 'x' sweep: {len(x_values)} values tested")

    def test_state_vector_sweep_y(self):
        """Sweep state variable 'y' (velocity)."""
        y_values = [-5.0, -3.0, -1.0, 0.0, 1.0, 3.0, 5.0]
        results = []

        for y in y_values:
            model = VanDerPolOscillator()
            dx, dy = model.derivatives(0.0, (1.0, y), input_force=0.0)

            assert not (abs(dx) > 1e6 or abs(dy) > 1e6), \
                f"Unstable at y={y}"

            # dx should equal y
            assert abs(dx - y) < 1e-10, \
                f"dx should equal y, got dx={dx}, y={y}"

            results.append(dy)

        print(f"✓ State 'y' sweep: {len(y_values)} values tested")

    def test_combined_state_sweep(self):
        """Sweep both state variables in 2D grid."""
        x_values = [-2.0, -1.0, 0.0, 1.0, 2.0]
        y_values = [-3.0, -1.0, 0.0, 1.0, 3.0]

        count = 0
        for x, y in itertools.product(x_values, y_values):
            model = VanDerPolOscillator(mu=1.5, omega=1.0)
            dx, dy = model.derivatives(0.0, (x, y), input_force=0.0)

            assert not (abs(dx) > 1e6 or abs(dy) > 1e6), \
                f"Unstable at (x={x}, y={y})"

            count += 1

        print(f"✓ Combined state sweep: {count} (x,y) combinations tested")

    def test_multi_parameter_sweep(self):
        """Test multiple parameter combinations."""
        mu_values = [0.5, 1.5, 3.0]
        omega_values = [0.5, 1.0, 2.0]
        damping_values = [0.0, 0.1, 0.5]

        count = 0
        for mu, omega, damping in itertools.product(mu_values, omega_values, damping_values):
            model = VanDerPolOscillator(mu=mu, omega=omega, damping=damping)
            dx, dy = model.derivatives(0.0, (1.0, 0.5), input_force=0.0)

            assert not (abs(dx) > 1e6 or abs(dy) > 1e6), \
                f"Unstable at (mu={mu}, omega={omega}, damping={damping})"

            count += 1

        print(f"✓ Multi-parameter sweep: {count} (mu,omega,damping) combinations tested")


class TestHeartBrainCouplingParameterSweeps:
    """Comprehensive parameter sweeps for coupled system."""

    def test_neural_to_cardiac_gain_sweep(self):
        """Sweep neural-to-cardiac coupling gain."""
        gain_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5]

        for gain in gain_values:
            coupling = CouplingParameters(
                neural_to_cardiac_gain=gain,
                cardiac_to_neural_gain=0.2
            )
            model = HeartBrainCouplingModel(coupling=coupling)

            state = (0.5, 0.0, 1.0, 0.0)
            derivatives = model.derivatives(0.0, state)

            assert len(derivatives) == 4, "Should return 4 derivatives"
            assert all(abs(d) < 1e6 for d in derivatives), \
                f"Unstable at neural_to_cardiac_gain={gain}"

        print(f"✓ Neural-to-cardiac gain sweep: {len(gain_values)} values tested")

    def test_cardiac_to_neural_gain_sweep(self):
        """Sweep cardiac-to-neural coupling gain."""
        gain_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0]

        for gain in gain_values:
            coupling = CouplingParameters(
                neural_to_cardiac_gain=0.4,
                cardiac_to_neural_gain=gain
            )
            model = HeartBrainCouplingModel(coupling=coupling)

            state = (0.5, 0.0, 1.0, 0.0)
            derivatives = model.derivatives(0.0, state)

            assert all(abs(d) < 1e6 for d in derivatives), \
                f"Unstable at cardiac_to_neural_gain={gain}"

        print(f"✓ Cardiac-to-neural gain sweep: {len(gain_values)} values tested")

    def test_neural_delay_sweep(self):
        """Sweep neural communication delay."""
        delay_values = [0.0, 0.05, 0.1, 0.12, 0.15, 0.2, 0.3, 0.5]

        for delay in delay_values:
            coupling = CouplingParameters(
                neural_delay=delay,
                cardiac_delay=0.15
            )
            model = HeartBrainCouplingModel(coupling=coupling)

            # Simulate briefly to populate history
            trajectory = model.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, 1.0),
                dt=0.01
            )

            assert len(trajectory) > 0, f"Simulation failed at neural_delay={delay}"

        print(f"✓ Neural delay sweep: {len(delay_values)} values tested")

    def test_cardiac_delay_sweep(self):
        """Sweep cardiac communication delay."""
        delay_values = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5]

        for delay in delay_values:
            coupling = CouplingParameters(
                neural_delay=0.12,
                cardiac_delay=delay
            )
            model = HeartBrainCouplingModel(coupling=coupling)

            trajectory = model.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, 1.0),
                dt=0.01
            )

            assert len(trajectory) > 0, f"Simulation failed at cardiac_delay={delay}"

        print(f"✓ Cardiac delay sweep: {len(delay_values)} values tested")

    def test_bias_parameter_sweep(self):
        """Sweep bias parameters."""
        bias_values = [-1.0, -0.5, 0.0, 0.5, 1.0, 2.0]

        for neural_bias, cardiac_bias in itertools.product(bias_values, bias_values[:3]):
            coupling = CouplingParameters(
                neural_bias=neural_bias,
                cardiac_bias=cardiac_bias
            )
            model = HeartBrainCouplingModel(coupling=coupling)

            state = (0.5, 0.0, 1.0, 0.0)
            derivatives = model.derivatives(0.0, state)

            assert all(abs(d) < 1e6 for d in derivatives), \
                f"Unstable at biases ({neural_bias}, {cardiac_bias})"

        print(f"✓ Bias parameter sweep: {len(bias_values) * 3} combinations tested")

    def test_initial_condition_sweep(self):
        """Sweep initial conditions for coupled system."""
        v_values = [-1.0, 0.0, 1.0]
        w_values = [-0.5, 0.0, 0.5]
        x_values = [0.0, 1.0, 2.0]
        y_values = [-1.0, 0.0, 1.0]

        count = 0
        for v, w, x, y in itertools.product(v_values, w_values, x_values, y_values):
            model = HeartBrainCouplingModel()

            try:
                trajectory = model.simulate(
                    initial_state=(v, w, x, y),
                    t_span=(0.0, 0.5),
                    dt=0.01
                )
                assert len(trajectory) > 0
                count += 1
            except Exception as e:
                pytest.fail(f"Failed at IC ({v},{w},{x},{y}): {e}")

        print(f"✓ Initial condition sweep: {count} combinations tested")

    def test_timestep_sweep(self):
        """Test different timestep values."""
        dt_values = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1]

        for dt in dt_values:
            model = HeartBrainCouplingModel()

            trajectory = model.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, 1.0),
                dt=dt
            )

            expected_steps = int(1.0 / dt) + 1
            assert len(trajectory) == expected_steps, \
                f"Wrong number of steps at dt={dt}"

        print(f"✓ Timestep sweep: {len(dt_values)} values tested")

    def test_simulation_duration_sweep(self):
        """Test different simulation durations."""
        durations = [0.5, 1.0, 5.0, 10.0, 20.0, 50.0]

        for duration in durations:
            model = HeartBrainCouplingModel()

            trajectory = model.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, duration),
                dt=0.01
            )

            assert len(trajectory) > 0, f"Failed at duration={duration}"
            final_time = trajectory[-1][0]
            assert abs(final_time - duration) < 0.02, \
                f"Final time {final_time} != {duration}"

        print(f"✓ Simulation duration sweep: {len(durations)} values tested")

    def test_coupling_symmetry_sweep(self):
        """Test symmetric vs asymmetric coupling."""
        gain_pairs = [
            (0.0, 0.0),  # No coupling
            (0.2, 0.2),  # Symmetric weak
            (0.5, 0.5),  # Symmetric strong
            (0.3, 0.1),  # Asymmetric 1
            (0.1, 0.3),  # Asymmetric 2
            (0.5, 0.0),  # Unidirectional 1
            (0.0, 0.5),  # Unidirectional 2
        ]

        for n2c_gain, c2n_gain in gain_pairs:
            coupling = CouplingParameters(
                neural_to_cardiac_gain=n2c_gain,
                cardiac_to_neural_gain=c2n_gain
            )
            model = HeartBrainCouplingModel(coupling=coupling)

            trajectory = model.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, 5.0),
                dt=0.01
            )

            assert len(trajectory) > 0, \
                f"Failed at coupling ({n2c_gain}, {c2n_gain})"

        print(f"✓ Coupling symmetry sweep: {len(gain_pairs)} configurations tested")


class TestNumericalStabilitySweeps:
    """Test numerical stability across parameter ranges."""

    def test_fitzhugh_nagumo_stability_limits(self):
        """Find stability limits for FitzHugh-Nagumo integration."""
        dt_values = [0.0001, 0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0]

        stable_dts = []
        unstable_dts = []

        for dt in dt_values:
            model = FitzHughNagumo(a=0.7, b=0.8, c=3.0)
            state = (0.5, 0.0)

            # Run 100 steps
            stable = True
            for i in range(100):
                state = model.step(0.0, state, dt, input_drive=0.0)

                # Check for blow-up
                if abs(state[0]) > 1e3 or abs(state[1]) > 1e3:
                    stable = False
                    break

            if stable:
                stable_dts.append(dt)
            else:
                unstable_dts.append(dt)

        print(f"✓ FHN stability: stable up to dt={max(stable_dts) if stable_dts else 'N/A'}")
        print(f"  Unstable at: {unstable_dts}")

    def test_van_der_pol_stability_limits(self):
        """Find stability limits for Van der Pol integration."""
        dt_values = [0.0001, 0.001, 0.01, 0.05, 0.1, 0.2]

        stable_dts = []

        for dt in dt_values:
            model = VanDerPolOscillator(mu=1.5, omega=1.0)
            state = (1.0, 0.0)

            stable = True
            for i in range(100):
                state = model.step(0.0, state, dt, input_force=0.0)

                if abs(state[0]) > 1e3 or abs(state[1]) > 1e3:
                    stable = False
                    break

            if stable:
                stable_dts.append(dt)

        print(f"✓ VdP stability: stable up to dt={max(stable_dts) if stable_dts else 'N/A'}")

    def test_extreme_parameter_combinations(self):
        """Test extreme but valid parameter combinations."""
        extreme_configs = [
            # (a, b, c) for FHN
            (0.01, 0.01, 0.1),   # Very small
            (2.0, 2.0, 20.0),    # Very large
            (0.1, 2.0, 10.0),    # Mismatched scales
            (1.5, 0.1, 1.0),     # High a, low b
        ]

        for a, b, c in extreme_configs:
            model = FitzHughNagumo(a=a, b=b, c=c)

            try:
                dv, dw = model.derivatives(0.0, (0.5, 0.0), input_drive=0.0)
                assert not (abs(dv) > 1e6 or abs(dw) > 1e6)
            except Exception as e:
                pytest.fail(f"Failed at extreme config ({a},{b},{c}): {e}")

        print(f"✓ Extreme parameter test: {len(extreme_configs)} configs tested")


class TestSweepResultsCollection:
    """Collect and export sweep results for analysis."""

    def test_collect_all_sweep_results(self):
        """Run comprehensive sweeps and collect results."""
        results = {
            'fitzhugh_nagumo': {},
            'van_der_pol': {},
            'coupling': {},
            'stability': {}
        }

        # FHN parameter sweeps
        a_values = [0.3, 0.5, 0.7, 0.9, 1.1]
        fhn_a_results = []
        for a in a_values:
            model = FitzHughNagumo(a=a)
            dv, dw = model.derivatives(0.0, (0.5, 0.0))
            fhn_a_results.append({'a': a, 'dv': dv, 'dw': dw})

        results['fitzhugh_nagumo']['parameter_a_sweep'] = fhn_a_results

        # VdP parameter sweeps
        mu_values = [0.5, 1.0, 1.5, 2.0, 3.0]
        vdp_mu_results = []
        for mu in mu_values:
            model = VanDerPolOscillator(mu=mu)
            dx, dy = model.derivatives(0.0, (1.0, 0.5))
            vdp_mu_results.append({'mu': mu, 'dx': dx, 'dy': dy})

        results['van_der_pol']['parameter_mu_sweep'] = vdp_mu_results

        # Coupling gain sweeps
        gain_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        coupling_results = []
        for gain in gain_values:
            coupling = CouplingParameters(
                neural_to_cardiac_gain=gain,
                cardiac_to_neural_gain=gain
            )
            model = HeartBrainCouplingModel(coupling=coupling)
            derivs = model.derivatives(0.0, (0.5, 0.0, 1.0, 0.0))
            coupling_results.append({
                'gain': gain,
                'derivatives': list(derivs)
            })

        results['coupling']['symmetric_gain_sweep'] = coupling_results

        # Export results
        output_path = Path(__file__).parent / 'sweep_results.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"✓ Results exported to: {output_path}")
        assert output_path.exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
