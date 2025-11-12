"""
Integration Tests: Primal Logic Processor + MotorHandPro

Tests the complete integration between microprocessor control and motor system.

Author: Donte Lightfoot - Lightfoot Technology
"""

import pytest
import numpy as np

from microprocessor import PrimalLogicProcessor, ProcessorConfig
from microprocessor.control_system import (
    ExponentialMemoryWeighting,
    IntegralControlSystem,
    compute_jerk_reduction,
    compute_comfort_metrics
)
from integration import MotorHandBridge, QuantInterface, QuantParameters


class TestPrimalLogicProcessor:
    """Test suite for Primal Logic Processor"""

    def test_processor_initialization(self):
        """Test processor initializes correctly"""
        processor = PrimalLogicProcessor()

        assert len(processor.ipus) == 8  # 8 IPUs
        assert processor.config.lambda_decay == 2.0
        assert processor.config.K_gain == 0.5

    def test_compute_control(self):
        """Test control computation"""
        processor = PrimalLogicProcessor()

        control, state = processor.compute_control(
            current_value=30.0,
            target_value=0.0,
            timestamp=0.0
        )

        # Control should be bounded
        assert -10.0 <= control <= 10.0
        assert state.error == 30.0  # error = current - target
        assert 0.0 <= state.comfort_index <= 100.0

    def test_emergency_braking_converges(self):
        """Test emergency braking converges to zero velocity"""
        processor = PrimalLogicProcessor()

        states = processor.simulate_emergency_braking(
            initial_velocity=30.0,
            target_velocity=0.0,
            duration=10.0
        )

        # Should reach near-zero velocity
        final_velocity = states[-1].velocity
        assert final_velocity < 1.0, f"Final velocity {final_velocity} too high"

        # Control should be bounded throughout
        for state in states:
            assert -10.0 <= state.bounded_control <= 10.0

    def test_bounded_control_enforcement(self):
        """Test that control outputs are always bounded"""
        processor = PrimalLogicProcessor()

        # Extreme error case
        control, state = processor.compute_control(
            current_value=1000.0,
            target_value=0.0,
            timestamp=0.0
        )

        assert -10.0 <= control <= 10.0, "Control not properly bounded"

    def test_comfort_index_calculation(self):
        """Test comfort index is computed correctly"""
        processor = PrimalLogicProcessor()

        # Low control magnitude = high comfort
        low_comfort = processor._compute_comfort_index(8.0)

        # High control magnitude = low comfort
        high_comfort = processor._compute_comfort_index(2.0)

        assert high_comfort > low_comfort

    def test_parallel_ipu_usage(self):
        """Test round-robin IPU scheduling"""
        processor = PrimalLogicProcessor()

        initial_ipu = processor.current_ipu

        # Make 8 calls (one full round)
        for i in range(8):
            processor.compute_control(10.0, 0.0, float(i))

        # Should be back to initial IPU
        assert processor.current_ipu == initial_ipu


class TestExponentialMemoryWeighting:
    """Test suite for exponential memory weighting"""

    def test_weight_decay(self):
        """Test weight decays exponentially"""
        memory = ExponentialMemoryWeighting(lambda_decay=2.0)

        w0 = memory.weight(0.0)
        w1 = memory.weight(1.0)
        w2 = memory.weight(2.0)

        assert w0 == 1.0  # No decay at t=0
        assert w1 < w0  # Decayed
        assert w2 < w1  # Further decayed
        assert w1 / w0 == pytest.approx(np.exp(-2.0))

    def test_weighted_integral(self):
        """Test weighted integral computation"""
        memory = ExponentialMemoryWeighting(lambda_decay=1.0)

        errors = [1.0, 2.0, 3.0, 2.0, 1.0]
        times = [0.0, 0.1, 0.2, 0.3, 0.4]
        current_time = 0.5

        integral = memory.weighted_integral(errors, times, current_time)

        # Should be positive (positive errors)
        assert integral > 0.0

        # Recent errors should dominate
        recent_integral = memory.weighted_integral(
            errors[-2:],
            times[-2:],
            current_time
        )
        # Recent portion should be significant fraction
        assert recent_integral / integral > 0.3


class TestQuantInterface:
    """Test suite for QUANT interface"""

    def test_quant_parameters(self):
        """Test QUANT parameters match MotorHandPro"""
        quant = QuantInterface()

        assert quant.params.PLANCK_D == pytest.approx(149.9992314000)
        assert quant.params.PLANCK_I3 == pytest.approx(6.4939394023)
        assert quant.params.KERNEL_MU == pytest.approx(0.169050000000)

    def test_throttle_conversion(self):
        """Test control to throttle conversion"""
        quant = QuantInterface()

        # Minimum control
        throttle_min = quant.control_to_throttle(-10.0)
        assert 0 <= throttle_min <= 255

        # Maximum control
        throttle_max = quant.control_to_throttle(10.0)
        assert 0 <= throttle_max <= 255

        # Zero control should map to middle
        throttle_zero = quant.control_to_throttle(0.0)
        assert throttle_zero == pytest.approx(127, abs=5)

        # Higher control = higher throttle
        assert throttle_max > throttle_zero > throttle_min

    def test_throttle_bounds(self):
        """Test throttle is always in valid range"""
        quant = QuantInterface()

        # Test extreme values
        for control in [-100, -10, 0, 10, 100]:
            throttle = quant.control_to_throttle(control)
            assert 0 <= throttle <= 255

    def test_feedback_parsing(self):
        """Test parsing of MotorHandPro CSV feedback"""
        quant = QuantInterface()

        # Valid line
        feedback = quant.parse_motorhand_feedback("0.100,1.234,5.678,0.912")
        assert feedback is not None
        assert feedback.timestamp == pytest.approx(0.100)
        assert feedback.psi == pytest.approx(1.234)
        assert feedback.gamma == pytest.approx(5.678)
        assert feedback.Ec == pytest.approx(0.912)

        # Comment line
        feedback = quant.parse_motorhand_feedback("# Comment")
        assert feedback is None

        # Invalid line
        feedback = quant.parse_motorhand_feedback("invalid,data")
        assert feedback is None


class TestMotorHandBridge:
    """Test suite for MotorHandPro integration bridge"""

    def test_bridge_initialization(self):
        """Test bridge initializes correctly"""
        bridge = MotorHandBridge()

        assert bridge.quant is not None
        assert len(bridge.control_history) == 0

    def test_control_integration(self):
        """Test integration of control signal"""
        bridge = MotorHandBridge()

        throttle, data = bridge.integrate_control_signal(
            primal_control=5.0,
            feedback=None
        )

        assert 0 <= throttle <= 255
        assert data['primal_control'] == 5.0
        assert data['throttle'] == throttle

    def test_closed_loop_simulation(self):
        """Test closed-loop simulation with both systems"""
        processor = PrimalLogicProcessor()
        bridge = MotorHandBridge()

        states = bridge.simulate_closed_loop(
            primal_processor=processor,
            initial_state=30.0,
            target_state=0.0,
            duration=5.0
        )

        assert len(states) > 0

        # Should converge towards target
        final_state = states[-1]['state']
        initial_state = states[0]['state']
        assert final_state < initial_state

        # All throttle values should be valid
        for state in states:
            assert 0 <= state['throttle'] <= 255

    def test_csv_export(self, tmp_path):
        """Test CSV export functionality"""
        processor = PrimalLogicProcessor()
        bridge = MotorHandBridge()

        states = bridge.simulate_closed_loop(
            primal_processor=processor,
            initial_state=20.0,
            target_state=0.0,
            duration=2.0
        )

        csv_file = tmp_path / "test_integration.csv"
        bridge.export_integration_csv(states, str(csv_file))

        assert csv_file.exists()

        # Verify CSV content
        with open(csv_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 3  # Header + data
            assert 'Primal Logic' in lines[0]


class TestComfortMetrics:
    """Test suite for comfort and performance metrics"""

    def test_jerk_reduction(self):
        """Test jerk reduction computation"""
        # Traditional: sudden changes
        traditional = [0, 10, 10, 0, 0, 10]

        # Primal: smooth changes
        primal = [0, 2, 4, 6, 8, 10]

        reduction = compute_jerk_reduction(traditional, primal, dt=0.1)

        # Primal should have lower jerk
        assert reduction > 0, "Primal should reduce jerk"

    def test_comfort_metrics(self):
        """Test comfort metrics computation"""
        # Smooth signal
        smooth = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        smooth_metrics = compute_comfort_metrics(smooth, dt=0.1)

        # Jagged signal
        jagged = [1.0, 5.0, 1.0, 5.0, 1.0, 5.0]
        jagged_metrics = compute_comfort_metrics(jagged, dt=0.1)

        # Smooth should have better comfort
        assert smooth_metrics['comfort_index'] > jagged_metrics['comfort_index']
        assert smooth_metrics['smoothness'] > jagged_metrics['smoothness']
        assert smooth_metrics['rms_jerk'] < jagged_metrics['rms_jerk']


class TestIntegration:
    """End-to-end integration tests"""

    def test_full_system_integration(self):
        """Test complete system integration"""
        # Initialize both systems
        processor = PrimalLogicProcessor(ProcessorConfig(
            K_gain=0.5,
            lambda_decay=2.0
        ))
        bridge = MotorHandBridge()

        # Run emergency braking scenario
        states = bridge.simulate_closed_loop(
            primal_processor=processor,
            initial_state=30.0,  # 30 m/s (~67 mph)
            target_state=0.0,     # Stop
            duration=10.0
        )

        # Verify convergence
        final_state = states[-1]['state']
        assert final_state < 2.0, "Should nearly stop"

        # Verify bounded control throughout
        max_control = max(abs(s['primal_control']) for s in states)
        assert max_control <= 10.0, "Control exceeded bounds"

        # Verify comfort
        avg_comfort = np.mean([s['comfort'] for s in states])
        assert avg_comfort > 50.0, "Average comfort too low"

        # Verify throttle validity
        for state in states:
            assert 0 <= state['throttle'] <= 255

    def test_performance_vs_traditional(self):
        """Compare Primal Logic vs traditional control"""
        # Primal Logic
        primal_processor = PrimalLogicProcessor(ProcessorConfig(
            K_gain=0.5,
            lambda_decay=2.0
        ))
        bridge = MotorHandBridge()

        primal_states = bridge.simulate_closed_loop(
            primal_processor=primal_processor,
            initial_state=30.0,
            target_state=0.0,
            duration=10.0
        )

        # Extract primal controls
        primal_controls = [s['primal_control'] for s in primal_states]

        # Traditional (simulated as proportional control)
        traditional_controls = []
        velocity = 30.0
        K_traditional = 1.0

        for _ in primal_states:
            error = velocity - 0.0
            control = -K_traditional * error
            control = np.clip(control, -10.0, 10.0)
            traditional_controls.append(control)
            velocity += control * 0.01
            velocity = max(0.0, velocity)

        # Compute metrics
        primal_metrics = compute_comfort_metrics(primal_controls, dt=0.01)
        trad_metrics = compute_comfort_metrics(traditional_controls, dt=0.01)

        # Primal should be better
        assert primal_metrics['comfort_index'] > trad_metrics['comfort_index']
        assert primal_metrics['rms_jerk'] < trad_metrics['rms_jerk']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
