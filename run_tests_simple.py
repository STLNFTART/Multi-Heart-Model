#!/usr/bin/env python3
"""
Simple test runner that doesn't require pytest
Runs basic functionality tests for all models
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_van_der_pol():
    """Test Van der Pol oscillator"""
    from src.cardiac import VanDerPolOscillator

    model = VanDerPolOscillator(mu=1.5, omega=1.0)
    state = (1.0, 0.0)

    # Test step
    new_state = model.step(0.0, state, 0.001)
    assert len(new_state) == 2
    assert not any(v != v for v in new_state)  # Check for NaN

    return True

def test_fitzhugh_nagumo():
    """Test FitzHugh-Nagumo model"""
    from src.neural import FitzHughNagumo

    model = FitzHughNagumo(stimulus_amplitude=0.5)
    state = (0.0, 0.0)

    # Test step
    new_state = model.step(0.0, state, 0.001)
    assert len(new_state) == 2
    assert not any(v != v for v in new_state)

    return True

def test_hbcm():
    """Test Heart-Brain Coupling Model"""
    from src.cardiac import VanDerPolOscillator
    from src.neural import FitzHughNagumo
    from src.coupling import HeartBrainCouplingModel

    neural = FitzHughNagumo()
    cardiac = VanDerPolOscillator()
    hbcm = HeartBrainCouplingModel(neural_model=neural, cardiac_model=cardiac)

    # Test simulation
    trajectory = hbcm.simulate((0.0, 0.0, 1.0, 0.0), (0.0, 1.0), 0.001)
    assert len(trajectory) > 0

    return True

def test_primal_processor():
    """Test Primal Logic Processor"""
    from src.microprocessor import PrimalLogicProcessor

    processor = PrimalLogicProcessor()
    control, state = processor.compute_control(
        current_value=30.0,
        target_value=0.0,
        timestamp=0.0
    )

    assert -10.0 <= control <= 10.0
    assert state.error == 30.0

    return True

def test_organchip():
    """Test Organ Chip Suite"""
    from src.organchip.orchestrator import create_default_organ_chip_suite

    suite = create_default_organ_chip_suite()
    suite.verbose = False

    # Test initialization
    state = suite.initialize_state(drug_amount_mg=100.0)
    assert 'circulation' in state

    return True

def main():
    """Run all tests"""
    print("=" * 70)
    print("SIMPLE TEST RUNNER - Multi-Heart-Model")
    print("=" * 70)

    tests = [
        ("Van der Pol Oscillator", test_van_der_pol),
        ("FitzHugh-Nagumo Model", test_fitzhugh_nagumo),
        ("Heart-Brain Coupling Model", test_hbcm),
        ("Primal Logic Processor", test_primal_processor),
        ("Organ Chip Suite", test_organchip),
    ]

    results = []

    for name, test_func in tests:
        try:
            print(f"\nTesting {name}...")
            result = test_func()
            print(f"  ✓ PASSED")
            results.append((name, True))
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            results.append((name, False))

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print("=" * 70)
    print(f"  Results: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
    print("=" * 70)

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
