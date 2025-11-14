#!/usr/bin/env python3
"""
Quick validation of new modules without pytest dependency.
"""

import sys


def test_validation_imports():
    """Test that all validation modules import correctly."""
    print("Testing validation module imports...")
    try:
        from src.validation.benchmarks import PhysiologicalBenchmarks, ParameterRange
        from src.validation.validators import (
            validate_cardiac_model,
            validate_neural_model,
            validate_coupling_model,
        )
        from src.validation.metrics import (
            compute_hrv_metrics,
            compute_pv_loop_metrics,
        )
        print("✓ All validation modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Validation import failed: {e}")
        return False


def test_autonomic_imports():
    """Test that all autonomic modules import correctly."""
    print("\nTesting autonomic module imports...")
    try:
        from src.autonomic.baroreflex import (
            Baroreceptor,
            BaroreflexController,
            BaroreflexParameters,
        )
        from src.autonomic.autonomic_nervous_system import (
            AutonomicNervousSystem,
            AutonomicParameters,
        )
        print("✓ All autonomic modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Autonomic import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_benchmarks_basic():
    """Test basic benchmark functionality."""
    print("\nTesting benchmark functionality...")
    try:
        from src.validation.benchmarks import PhysiologicalBenchmarks

        benchmarks = PhysiologicalBenchmarks()

        # Test parameter validation
        params = {
            'heart_rate': 72.0,
            'systolic_bp': 120.0,
            'diastolic_bp': 80.0,
        }

        results = benchmarks.validate_all_parameters(params)

        assert results['heart_rate'] is True, "Heart rate should be valid"
        assert results['systolic_bp'] is True, "Systolic BP should be valid"
        assert results['diastolic_bp'] is True, "Diastolic BP should be valid"

        print("✓ Benchmark validation works correctly")
        return True
    except Exception as e:
        print(f"✗ Benchmark test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_baroreflex_basic():
    """Test basic baroreflex functionality."""
    print("\nTesting baroreflex functionality...")
    try:
        from src.autonomic.baroreflex import Baroreceptor, BaroreflexController

        # Test baroreceptor
        baroreceptor = Baroreceptor()
        fr_low = baroreceptor.compute_firing_rate(80.0, 0.001)
        fr_high = baroreceptor.compute_firing_rate(120.0, 0.001)

        assert fr_low < fr_high, "Firing rate should increase with pressure"
        assert 0 <= fr_low <= 200, "Firing rate should be in valid range"

        # Test controller
        controller = BaroreflexController()
        vagal, sympathetic = controller.compute_autonomic_output(93.0, 0.001, 0.0)

        assert 0 <= vagal <= 1.0, "Vagal output should be in [0,1]"
        assert 0 <= sympathetic <= 1.0, "Sympathetic output should be in [0,1]"

        print("✓ Baroreflex model works correctly")
        return True
    except Exception as e:
        print(f"✗ Baroreflex test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_autonomic_system_basic():
    """Test basic autonomic nervous system functionality."""
    print("\nTesting autonomic nervous system...")
    try:
        from src.autonomic.autonomic_nervous_system import AutonomicNervousSystem

        ans = AutonomicNervousSystem()

        # Update with normal pressure
        state = ans.update(pressure=93.0, dt=0.001, t=0.0)

        assert 0 <= state.vagal_tone <= 1.0, "Vagal tone should be in [0,1]"
        assert 0 <= state.sympathetic_tone <= 1.0, "Sympathetic tone should be in [0,1]"
        assert state.contractility_effect >= 1.0, "Contractility should be >= baseline"

        # Test heart rate calculation
        hr = ans.get_heart_rate(105.0)
        assert 30 <= hr <= 220, "Heart rate should be in physiological range"

        print("✓ Autonomic nervous system works correctly")
        return True
    except Exception as e:
        print(f"✗ Autonomic system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hrv_metrics():
    """Test HRV metrics computation."""
    print("\nTesting HRV metrics...")
    try:
        from src.validation.metrics import compute_hrv_metrics

        # Simulated RR intervals
        rr_intervals = [
            850, 870, 840, 880, 860, 890, 850, 870, 840, 860,
            880, 850, 870, 860, 840, 890, 850, 870, 860, 840
        ]

        metrics = compute_hrv_metrics(rr_intervals)

        assert 'sdnn_ms' in metrics, "Should compute SDNN"
        assert 'rmssd_ms' in metrics, "Should compute RMSSD"
        assert 'lf_hf_ratio' in metrics, "Should compute LF/HF ratio"

        assert metrics['sdnn_ms'] > 0, "SDNN should be positive"
        assert metrics['rmssd_ms'] > 0, "RMSSD should be positive"

        print(f"  SDNN: {metrics['sdnn_ms']:.1f} ms")
        print(f"  RMSSD: {metrics['rmssd_ms']:.1f} ms")
        print(f"  LF/HF: {metrics['lf_hf_ratio']:.2f}")

        print("✓ HRV metrics computed correctly")
        return True
    except Exception as e:
        print(f"✗ HRV metrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_coupling_validation():
    """Test validation of coupled heart-brain model."""
    print("\nTesting coupled model validation...")
    try:
        from src.cardiac import VanDerPolOscillator
        from src.neural import FitzHughNagumo
        from src.coupling import HeartBrainCouplingModel, CouplingParameters
        from src.validation.validators import validate_coupling_model

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
        print("  Simulating coupled model...")
        trajectory = model.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 5.0),  # 5 seconds for speed
            dt=0.001
        )

        print(f"  Simulated {len(trajectory)} timesteps")

        # Validate
        metrics = validate_coupling_model(trajectory, coupling, dt=0.001)

        assert metrics is not None, "Should return metrics"
        assert 'neural' in metrics, "Should validate neural component"
        assert 'cardiac' in metrics, "Should validate cardiac component"
        assert 'coupling_params_valid' in metrics, "Should validate coupling parameters"

        # Check coupling parameters
        param_valid = metrics['coupling_params_valid']
        assert param_valid['neural_to_cardiac_gain'] is True, "N->C gain should be valid"
        assert param_valid['cardiac_to_neural_gain'] is True, "C->N gain should be valid"

        print("✓ Coupled model validation works correctly")
        return True
    except Exception as e:
        print(f"✗ Coupling validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("TESTING NEW MODULES")
    print("="*60)

    tests = [
        test_validation_imports,
        test_autonomic_imports,
        test_benchmarks_basic,
        test_baroreflex_basic,
        test_autonomic_system_basic,
        test_hrv_metrics,
        test_coupling_validation,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
