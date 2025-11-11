#!/usr/bin/env python3
"""
Quick integration test for multi-organ system
Tests basic imports and functionality
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all modules import successfully"""
    print("Testing imports...")

    try:
        from src.organ_chips import (
            Receptor,
            ReceptorType,
            Ligand,
            HeartChip,
            LiverChip,
            SystemicCirculation,
            SystemicImmuneResponse,
            MultiOrganDigitalTwin,
            SimulationConfig,
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality of each component"""
    print("\nTesting basic functionality...")

    try:
        from src.organ_chips import (
            Ligand,
            HeartChip,
            LiverChip,
            SystemicCirculation,
        )

        # Test ligand creation
        drug = Ligand(name="test", molecular_weight=300.0)
        assert drug.name == "test"
        print("✓ Ligand creation works")

        # Test heart chip
        heart = HeartChip()
        assert heart.organ_name == "heart"
        assert "cardiomyocyte" in heart.cell_populations
        print("✓ Heart chip creation works")

        # Test liver chip
        liver = LiverChip()
        assert liver.organ_name == "liver"
        assert "hepatocyte" in liver.cell_populations
        print("✓ Liver chip creation works")

        # Test circulation
        circulation = SystemicCirculation()
        assert circulation.cardiac_output > 0
        assert "heart" in circulation.perfusions
        assert "liver" in circulation.perfusions
        print("✓ Circulation creation works")

        return True

    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simulation():
    """Test a minimal simulation"""
    print("\nTesting simulation...")

    try:
        from src.organ_chips import (
            MultiOrganDigitalTwin,
            SimulationConfig,
            Ligand,
        )

        # Very short simulation
        config = SimulationConfig(
            duration=0.1,  # 6 minutes
            dt=0.01,
            output_interval=60.0,
            drug_name="test_drug",
            dose_mg=10.0,
            route="IV"
        )

        twin = MultiOrganDigitalTwin(config)
        drug = Ligand(name="test_drug", molecular_weight=300.0)

        # Run simulation
        results = twin.simulate(drug)

        assert len(results) > 0
        assert results[0].time == 0.0

        print(f"✓ Simulation works ({len(results)} time points)")

        # Test toxicity assessment
        toxicity = twin.assess_toxicity()
        assert 'overall_safety' in toxicity
        print(f"✓ Toxicity assessment works (Safety: {toxicity['overall_safety']})")

        return True

    except Exception as e:
        print(f"✗ Simulation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cardiac_toxicity():
    """Test cardiac toxicity model"""
    print("\nTesting cardiac toxicity...")

    try:
        from src.organ_chips import HeartChip, CardiacToxicity

        heart = HeartChip()
        results = CardiacToxicity.doxorubicin_toxicity(
            heart_chip=heart,
            dose_mg_m2=50.0,  # Low dose
            duration_hours=0.1,  # 6 minutes
            dt=0.01
        )

        assert len(results) > 0
        final = results[-1]
        assert 'viability' in final
        assert 'cardiac_function' in final

        print(f"✓ Cardiac toxicity model works (Viability: {final['viability']:.3f})")
        return True

    except Exception as e:
        print(f"✗ Cardiac toxicity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_liver_toxicity():
    """Test liver toxicity model"""
    print("\nTesting liver toxicity...")

    try:
        from src.organ_chips import LiverChip, LiverToxicity

        liver = LiverChip()
        results = LiverToxicity.acetaminophen_toxicity(
            liver_chip=liver,
            dose_mg_kg=15.0,  # Therapeutic dose
            duration_hours=0.1,  # 6 minutes
            dt=0.1
        )

        assert len(results) > 0
        final = results[-1]
        assert 'viability' in final
        assert 'liver_function' in final

        print(f"✓ Liver toxicity model works (Viability: {final['viability']:.3f})")
        return True

    except Exception as e:
        print(f"✗ Liver toxicity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*70)
    print("Multi-Organ Digital Twin - Integration Test Suite")
    print("="*70)

    tests = [
        test_imports,
        test_basic_functionality,
        test_simulation,
        test_cardiac_toxicity,
        test_liver_toxicity,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
