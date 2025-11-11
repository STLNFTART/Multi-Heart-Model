#!/usr/bin/env python3
"""
Simple Integration Validation Script

Validates that all integration modules load correctly and basic functionality works.
Does not require external dependencies like numpy or pytest.

Author: Donte Lightfoot - Lightfoot Technology
"""

import sys
import os
import math

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), './'))


def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")

    try:
        from src.microprocessor import PrimalLogicProcessor, IntegralProcessingUnit
        print("  ✓ Microprocessor module imported")
    except ImportError as e:
        print(f"  ✗ Failed to import microprocessor module: {e}")
        return False

    try:
        from src.integration import MotorHandBridge, QuantInterface
        print("  ✓ Integration module imported")
    except ImportError as e:
        print(f"  ✗ Failed to import integration module: {e}")
        return False

    return True


def test_primal_processor():
    """Test Primal Logic Processor basic functionality"""
    print("\nTesting Primal Logic Processor...")

    from src.microprocessor import PrimalLogicProcessor

    processor = PrimalLogicProcessor()

    # Test initialization
    assert len(processor.ipus) == 8, "Should have 8 IPUs"
    print("  ✓ Processor initialized with 8 IPUs")

    # Test control computation
    control, state = processor.compute_control(
        current_value=30.0,
        target_value=0.0,
        timestamp=0.0
    )

    assert -10.0 <= control <= 10.0, f"Control {control} out of bounds"
    print(f"  ✓ Control computed: {control:.3f} (within bounds)")

    assert state.error == 30.0, "Error calculation incorrect"
    print(f"  ✓ Error computed correctly: {state.error}")

    # Test reset
    processor.reset()
    assert len(processor.state_history) == 0, "Reset failed"
    print("  ✓ Processor reset successful")

    return True


def test_quant_interface():
    """Test QUANT interface functionality"""
    print("\nTesting QUANT Interface...")

    from src.integration import QuantInterface

    quant = QuantInterface()

    # Test parameters
    assert abs(quant.params.PLANCK_D - 149.9992314000) < 1e-6
    print(f"  ✓ QUANT parameters loaded: D={quant.params.PLANCK_D}")

    # Test throttle conversion
    throttle_min = quant.control_to_throttle(-10.0)
    throttle_max = quant.control_to_throttle(10.0)
    throttle_zero = quant.control_to_throttle(0.0)

    assert 0 <= throttle_min <= 255, "Throttle min out of range"
    assert 0 <= throttle_max <= 255, "Throttle max out of range"
    assert throttle_max > throttle_zero > throttle_min, "Throttle order incorrect"

    print(f"  ✓ Throttle conversion: {throttle_min} < {throttle_zero} < {throttle_max}")

    # Test feedback parsing
    feedback = quant.parse_motorhand_feedback("0.100,1.234,5.678,0.912")
    assert feedback is not None, "Failed to parse valid feedback"
    assert abs(feedback.timestamp - 0.100) < 1e-6
    print(f"  ✓ Feedback parsing: t={feedback.timestamp}, psi={feedback.psi}")

    return True


def test_motor_bridge():
    """Test MotorHand bridge functionality"""
    print("\nTesting MotorHand Bridge...")

    from src.integration import MotorHandBridge

    bridge = MotorHandBridge()

    # Test control integration
    throttle, data = bridge.integrate_control_signal(primal_control=5.0)

    assert 0 <= throttle <= 255, "Throttle out of range"
    assert data['primal_control'] == 5.0, "Control value mismatch"

    print(f"  ✓ Control integrated: control=5.0 → throttle={throttle}")

    return True


def test_simple_simulation():
    """Test a simple control simulation"""
    print("\nTesting Simple Simulation...")

    from src.microprocessor import PrimalLogicProcessor, ProcessorConfig
    from src.integration import MotorHandBridge

    # Create systems
    processor = PrimalLogicProcessor(ProcessorConfig(
        K_gain=0.5,
        lambda_decay=2.0,
        dt=0.1
    ))
    bridge = MotorHandBridge()

    # Simple simulation loop
    velocity = 30.0
    target = 0.0
    steps = 10

    print(f"  Simulating {steps} control steps...")

    for i in range(steps):
        # Compute control
        control, state = processor.compute_control(
            current_value=velocity,
            target_value=target,
            timestamp=i * 0.1
        )

        # Convert to throttle
        throttle, data = bridge.integrate_control_signal(control)

        # Update velocity (simple integration)
        velocity += control * 0.1
        velocity = max(0.0, velocity)

        if i == 0:
            print(f"  Step {i}: v={velocity:.2f}, control={control:.2f}, throttle={throttle}")
        elif i == steps - 1:
            print(f"  Step {i}: v={velocity:.2f}, control={control:.2f}, throttle={throttle}")

    print(f"  ✓ Simulation completed: {velocity:.2f} m/s")

    assert velocity < 30.0, "Velocity should decrease"
    print("  ✓ Control is working (velocity decreased)")

    return True


def test_file_structure():
    """Test that all expected files exist"""
    print("\nTesting File Structure...")

    expected_files = [
        'src/microprocessor/__init__.py',
        'src/microprocessor/primal_processor.py',
        'src/microprocessor/control_system.py',
        'src/integration/__init__.py',
        'src/integration/motorhand_bridge.py',
        'tests/integration/test_microprocessor_motorhand.py',
        'examples/microprocessor_motorhand_demo.py'
    ]

    all_exist = True
    for file_path in expected_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} NOT FOUND")
            all_exist = False

    return all_exist


def main():
    """Run all validation tests"""
    print("=" * 70)
    print("  PRIMAL LOGIC + MOTORHANDPRO INTEGRATION VALIDATION")
    print("  Lightfoot Technology")
    print("=" * 70)

    tests = [
        ("File Structure", test_file_structure),
        ("Module Imports", test_imports),
        ("Primal Processor", test_primal_processor),
        ("QUANT Interface", test_quant_interface),
        ("Motor Bridge", test_motor_bridge),
        ("Simple Simulation", test_simple_simulation)
    ]

    results = []
    for name, test_func in tests:
        try:
            print(f"\n{'='*70}")
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("  VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print("=" * 70)
    print(f"  Results: {passed}/{total} tests passed")

    if passed == total:
        print("  🎉 All tests passed! Integration validated successfully.")
        print("=" * 70)
        return 0
    else:
        print(f"  ⚠ {total - passed} test(s) failed.")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    exit(main())
