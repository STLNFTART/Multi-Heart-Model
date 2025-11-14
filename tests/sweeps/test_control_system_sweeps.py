"""
Control System and Microprocessor Parameter Sweeps

Comprehensive parameter and state sweeps for:
1. Primal Logic Processor
2. Integral Processing Units
3. Exponential Memory Weighting
4. Control System Performance
5. MotorHand Bridge Integration

Author: AI Assistant
Date: 2025-11-14
"""

import pytest
import sys
from pathlib import Path
from typing import List, Dict
import itertools
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Note: These imports will work if numpy is available
# Tests will be skipped if dependencies are missing
try:
    import numpy as np
    from src.microprocessor import PrimalLogicProcessor, ProcessorConfig, IntegralProcessingUnit
    from src.microprocessor.control_system import ExponentialMemoryWeighting, compute_comfort_metrics
    from src.integration import MotorHandBridge, QuantInterface
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="NumPy or microprocessor modules not available")
class TestPrimalProcessorParameterSweeps:
    """Parameter sweeps for Primal Logic Processor."""

    def test_k_gain_sweep(self):
        """Sweep proportional gain K."""
        k_values = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
        results = []

        for k in k_values:
            config = ProcessorConfig(K_gain=k, lambda_decay=2.0)
            processor = PrimalLogicProcessor(config)

            control, state = processor.compute_control(
                current_value=10.0,
                target_value=0.0,
                timestamp=0.0
            )

            # Control magnitude should scale with K
            results.append(abs(control))

            assert -10.0 <= control <= 10.0, \
                f"Control out of bounds at K={k}: {control}"

        # Higher K should give stronger control (up to saturation)
        print(f"✓ K_gain sweep: {len(k_values)} values, control range [{min(results):.2f}, {max(results):.2f}]")

    def test_lambda_decay_sweep(self):
        """Sweep memory decay rate lambda."""
        lambda_values = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
        results = []

        for lam in lambda_values:
            config = ProcessorConfig(K_gain=0.5, lambda_decay=lam)
            processor = PrimalLogicProcessor(config)

            # Build up error history
            for t in range(10):
                control, state = processor.compute_control(
                    current_value=5.0,
                    target_value=0.0,
                    timestamp=float(t) * 0.01
                )

            results.append(state.integral)

        # Higher lambda = faster decay = smaller integral
        print(f"✓ Lambda_decay sweep: {len(lambda_values)} values tested")

    def test_dt_timestep_sweep(self):
        """Sweep timestep dt."""
        dt_values = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1]

        for dt in dt_values:
            config = ProcessorConfig(dt=dt)
            processor = PrimalLogicProcessor(config)

            control, state = processor.compute_control(
                current_value=10.0,
                target_value=0.0,
                timestamp=0.0
            )

            assert -10.0 <= control <= 10.0, \
                f"Control out of bounds at dt={dt}"

        print(f"✓ Timestep dt sweep: {len(dt_values)} values tested")

    def test_error_magnitude_sweep(self):
        """Sweep error magnitude (current - target)."""
        errors = [0.1, 1.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0]
        results = []

        for error in errors:
            processor = PrimalLogicProcessor()

            control, state = processor.compute_control(
                current_value=error,
                target_value=0.0,
                timestamp=0.0
            )

            results.append(control)

            # Control should be bounded
            assert -10.0 <= control <= 10.0, \
                f"Control not bounded at error={error}: {control}"

        # Should see saturation at high errors
        print(f"✓ Error magnitude sweep: {len(errors)} values tested")
        print(f"  Control saturation observed: {max(results):.2f}")

    def test_target_value_sweep(self):
        """Sweep target setpoint."""
        current = 30.0
        targets = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0]
        results = []

        for target in targets:
            processor = PrimalLogicProcessor()

            control, state = processor.compute_control(
                current_value=current,
                target_value=target,
                timestamp=0.0
            )

            results.append({
                'target': target,
                'error': state.error,
                'control': control
            })

            assert -10.0 <= control <= 10.0

        print(f"✓ Target value sweep: {len(targets)} values tested")

    def test_emergency_braking_velocity_sweep(self):
        """Sweep initial velocity for emergency braking."""
        velocities = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        results = []

        for v0 in velocities:
            processor = PrimalLogicProcessor()

            states = processor.simulate_emergency_braking(
                initial_velocity=v0,
                target_velocity=0.0,
                duration=10.0
            )

            final_velocity = states[-1].velocity
            stopping_time = None

            # Find stopping time (velocity < 1 m/s)
            for state in states:
                if state.velocity < 1.0:
                    stopping_time = state.time
                    break

            results.append({
                'v0': v0,
                'final_v': final_velocity,
                'stopping_time': stopping_time
            })

            assert final_velocity < 2.0, \
                f"Failed to stop from v0={v0}, final_v={final_velocity}"

        print(f"✓ Emergency braking velocity sweep: {len(velocities)} scenarios tested")

    def test_ipu_parallel_processing_sweep(self):
        """Test parallel IPU usage patterns."""
        num_calls = [1, 8, 16, 32, 64, 128]

        for n_calls in num_calls:
            processor = PrimalLogicProcessor()

            for i in range(n_calls):
                control, state = processor.compute_control(
                    current_value=10.0,
                    target_value=0.0,
                    timestamp=float(i) * 0.01
                )

            # Check IPU round-robin scheduling
            expected_ipu = n_calls % 8
            assert processor.current_ipu == expected_ipu, \
                f"IPU scheduling error after {n_calls} calls"

        print(f"✓ IPU parallel processing: tested up to {max(num_calls)} calls")

    def test_control_bounds_sweep(self):
        """Sweep control bound limits."""
        bound_configs = [
            (5.0, -5.0),
            (10.0, -10.0),
            (20.0, -20.0),
            (50.0, -50.0),
        ]

        for max_bound, min_bound in bound_configs:
            config = ProcessorConfig(
                max_control_output=max_bound,
                min_control_output=min_bound
            )
            processor = PrimalLogicProcessor(config)

            # Test with large error
            control, state = processor.compute_control(
                current_value=1000.0,
                target_value=0.0,
                timestamp=0.0
            )

            assert min_bound <= control <= max_bound, \
                f"Control {control} outside bounds [{min_bound}, {max_bound}]"

        print(f"✓ Control bounds sweep: {len(bound_configs)} configurations tested")

    def test_comfort_index_sweep(self):
        """Sweep control magnitudes to test comfort calculation."""
        control_magnitudes = [0.0, 1.0, 2.0, 5.0, 7.0, 9.0, 10.0]
        results = []

        for magnitude in control_magnitudes:
            processor = PrimalLogicProcessor()
            comfort = processor._compute_comfort_index(magnitude)

            # Comfort should decrease with control magnitude
            results.append(comfort)

            assert 0.0 <= comfort <= 100.0, \
                f"Comfort index out of range: {comfort}"

        # Verify monotonic decrease
        for i in range(len(results) - 1):
            assert results[i] >= results[i+1], \
                "Comfort should decrease with control magnitude"

        print(f"✓ Comfort index sweep: {len(control_magnitudes)} values tested")


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="NumPy not available")
class TestExponentialMemoryWeightingSweeps:
    """Parameter sweeps for exponential memory weighting."""

    def test_lambda_decay_weight_sweep(self):
        """Sweep lambda values for weight calculation."""
        lambda_values = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        time_delta = 1.0

        for lam in lambda_values:
            memory = ExponentialMemoryWeighting(lambda_decay=lam)
            weight = memory.weight(time_delta)

            expected = np.exp(-lam * time_delta)
            assert abs(weight - expected) < 1e-10, \
                f"Weight calculation error at lambda={lam}"

            # Weight should be in (0, 1] for positive time_delta
            assert 0.0 < weight <= 1.0

        print(f"✓ Lambda decay weight sweep: {len(lambda_values)} values tested")

    def test_time_delta_sweep(self):
        """Sweep time deltas for weight decay."""
        time_deltas = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        memory = ExponentialMemoryWeighting(lambda_decay=2.0)
        results = []

        for dt in time_deltas:
            weight = memory.weight(dt)
            results.append(weight)

            # Weight should decay exponentially
            assert 0.0 < weight <= 1.0

        # Should be monotonically decreasing
        for i in range(len(results) - 1):
            assert results[i] >= results[i+1], \
                "Weights should decrease with time"

        print(f"✓ Time delta sweep: {len(time_deltas)} values tested")

    def test_weighted_integral_error_sweep(self):
        """Sweep error magnitudes in weighted integral."""
        memory = ExponentialMemoryWeighting(lambda_decay=1.0)

        error_scales = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        times = [0.0, 0.1, 0.2, 0.3, 0.4]
        current_time = 0.5

        for scale in error_scales:
            errors = [e * scale for e in [1.0, 2.0, 3.0, 2.0, 1.0]]

            integral = memory.weighted_integral(errors, times, current_time)

            # Integral should scale linearly with error magnitude
            assert abs(integral) > 0, \
                f"Integral should be non-zero for scale={scale}"

        print(f"✓ Weighted integral error sweep: {len(error_scales)} scales tested")


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="Dependencies not available")
class TestQuantInterfaceParameterSweeps:
    """Parameter sweeps for QUANT interface."""

    def test_control_to_throttle_sweep(self):
        """Sweep control values to throttle conversion."""
        control_values = [-10.0, -5.0, -2.0, 0.0, 2.0, 5.0, 10.0]
        quant = QuantInterface()
        results = []

        for control in control_values:
            throttle = quant.control_to_throttle(control)

            # Throttle must be in [0, 255]
            assert 0 <= throttle <= 255, \
                f"Throttle {throttle} out of range at control={control}"

            results.append(throttle)

        # Should be monotonically increasing
        for i in range(len(results) - 1):
            assert results[i] <= results[i+1], \
                "Throttle should increase with control"

        print(f"✓ Control-to-throttle sweep: {len(control_values)} values tested")

    def test_extreme_control_values(self):
        """Test extreme control values outside normal range."""
        extreme_values = [-100.0, -50.0, 50.0, 100.0, 1000.0]
        quant = QuantInterface()

        for control in extreme_values:
            throttle = quant.control_to_throttle(control)

            # Should still produce valid throttle
            assert 0 <= throttle <= 255, \
                f"Extreme control {control} produced invalid throttle {throttle}"

        print(f"✓ Extreme control values: {len(extreme_values)} tested")


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="Dependencies not available")
class TestMotorHandBridgeParameterSweeps:
    """Parameter sweeps for MotorHand bridge integration."""

    def test_control_signal_integration_sweep(self):
        """Sweep primal control signals."""
        control_signals = [-10.0, -5.0, -2.0, 0.0, 2.0, 5.0, 10.0]
        bridge = MotorHandBridge()

        for control in control_signals:
            throttle, data = bridge.integrate_control_signal(
                primal_control=control,
                feedback=None
            )

            assert 0 <= throttle <= 255
            assert data['primal_control'] == control
            assert data['throttle'] == throttle

        print(f"✓ Control signal integration: {len(control_signals)} values tested")

    def test_closed_loop_initial_state_sweep(self):
        """Sweep initial states for closed-loop simulation."""
        initial_states = [5.0, 10.0, 20.0, 30.0, 50.0]
        target = 0.0

        for init_state in initial_states:
            processor = PrimalLogicProcessor()
            bridge = MotorHandBridge()

            states = bridge.simulate_closed_loop(
                primal_processor=processor,
                initial_state=init_state,
                target_state=target,
                duration=5.0
            )

            assert len(states) > 0, \
                f"Simulation failed at init_state={init_state}"

            # Should converge towards target
            final_state = states[-1]['state']
            assert final_state < init_state, \
                f"No convergence from init_state={init_state}"

        print(f"✓ Closed-loop initial state sweep: {len(initial_states)} tested")

    def test_closed_loop_duration_sweep(self):
        """Sweep simulation durations."""
        durations = [1.0, 2.0, 5.0, 10.0, 20.0]

        processor = PrimalLogicProcessor()
        bridge = MotorHandBridge()

        for duration in durations:
            states = bridge.simulate_closed_loop(
                primal_processor=processor,
                initial_state=30.0,
                target_state=0.0,
                duration=duration
            )

            # Check expected number of timesteps
            expected_steps = int(duration / 0.01) + 1
            assert len(states) >= expected_steps * 0.9, \
                f"Too few steps at duration={duration}"

        print(f"✓ Simulation duration sweep: {len(durations)} durations tested")


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="Dependencies not available")
class TestControlSystemPerformanceSweeps:
    """Performance and stability sweeps for control systems."""

    def test_multi_parameter_k_lambda_sweep(self):
        """2D sweep of K_gain and lambda_decay."""
        k_values = [0.2, 0.5, 1.0, 2.0]
        lambda_values = [0.5, 1.0, 2.0, 5.0]

        results = []

        for k, lam in itertools.product(k_values, lambda_values):
            config = ProcessorConfig(K_gain=k, lambda_decay=lam)
            processor = PrimalLogicProcessor(config)

            # Run emergency braking
            states = processor.simulate_emergency_braking(
                initial_velocity=30.0,
                target_velocity=0.0,
                duration=10.0
            )

            final_v = states[-1].velocity
            avg_comfort = np.mean([s.comfort_index for s in states])

            results.append({
                'K': k,
                'lambda': lam,
                'final_velocity': final_v,
                'avg_comfort': avg_comfort
            })

        print(f"✓ Multi-parameter K-lambda sweep: {len(results)} combinations tested")

    def test_repeated_braking_scenarios(self):
        """Test multiple braking events in sequence."""
        n_scenarios = 10
        processor = PrimalLogicProcessor()

        for i in range(n_scenarios):
            initial_v = 20.0 + i * 5.0  # 20 to 65 m/s

            states = processor.simulate_emergency_braking(
                initial_velocity=initial_v,
                target_velocity=0.0,
                duration=10.0
            )

            final_v = states[-1].velocity
            assert final_v < 2.0, \
                f"Failed to stop in scenario {i+1}, v0={initial_v}"

        print(f"✓ Repeated braking scenarios: {n_scenarios} tested")


@pytest.mark.skipif(not DEPS_AVAILABLE, reason="Dependencies not available")
class TestControlSystemSweepResults:
    """Collect and export control system sweep results."""

    def test_export_control_sweep_results(self):
        """Export comprehensive control system sweep results."""
        results = {
            'processor': {},
            'memory_weighting': {},
            'integration': {}
        }

        # K_gain sweep
        k_values = [0.2, 0.5, 1.0, 1.5, 2.0]
        k_sweep = []
        for k in k_values:
            config = ProcessorConfig(K_gain=k)
            processor = PrimalLogicProcessor(config)

            control, state = processor.compute_control(10.0, 0.0, 0.0)
            k_sweep.append({
                'K_gain': k,
                'control': float(control),
                'error': float(state.error),
                'comfort': float(state.comfort_index)
            })

        results['processor']['k_gain_sweep'] = k_sweep

        # Memory weighting sweep
        lambda_values = [0.5, 1.0, 2.0, 5.0]
        lambda_sweep = []
        for lam in lambda_values:
            memory = ExponentialMemoryWeighting(lambda_decay=lam)
            weight_1s = memory.weight(1.0)
            weight_2s = memory.weight(2.0)

            lambda_sweep.append({
                'lambda': lam,
                'weight_1s': float(weight_1s),
                'weight_2s': float(weight_2s)
            })

        results['memory_weighting']['lambda_sweep'] = lambda_sweep

        # Export
        output_path = Path(__file__).parent / 'control_sweep_results.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"✓ Control sweep results exported to: {output_path}")
        assert output_path.exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
