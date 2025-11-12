#!/usr/bin/env python3
"""Quick validation script for organ chip suite.

Tests basic functionality of all modules.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from organchip.ligand_receptor.binding import LigandReceptorBinding
        print("  ✓ Ligand-receptor module")
    except Exception as e:
        print(f"  ✗ Ligand-receptor module: {e}")
        return False

    try:
        from organchip.immune.cytokines import CytokineNetwork
        print("  ✓ Immune module")
    except Exception as e:
        print(f"  ✗ Immune module: {e}")
        return False

    try:
        from organchip.liver.hepatocyte import Hepatocyte
        print("  ✓ Liver module")
    except Exception as e:
        print(f"  ✗ Liver module: {e}")
        return False

    try:
        from organchip.cardiac.cardiotoxicity import CardiacCell
        print("  ✓ Cardiac module")
    except Exception as e:
        print(f"  ✗ Cardiac module: {e}")
        return False

    try:
        from organchip.circulation.pbpk import MultiOrganPBPK
        print("  ✓ Circulation module")
    except Exception as e:
        print(f"  ✗ Circulation module: {e}")
        return False

    try:
        from organchip.multiscale.integration import MultiscaleCoupling
        print("  ✓ Multiscale coupling module")
    except Exception as e:
        print(f"  ✗ Multiscale coupling module: {e}")
        return False

    try:
        from organchip.orchestrator import OrganChipSuite
        print("  ✓ Orchestrator module")
    except Exception as e:
        print(f"  ✗ Orchestrator module: {e}")
        return False

    return True


def test_basic_functionality():
    """Test basic functionality of key modules."""
    print("\nTesting basic functionality...")

    # Test ligand-receptor binding
    try:
        from organchip.ligand_receptor.binding import LigandReceptorBinding

        model = LigandReceptorBinding()
        state = (10.0, 100.0, 0.0, 0.0)  # (L, R, LR, Rint)
        derivs = model.derivatives(0.0, state, ligand_input=0.0)
        assert len(derivs) == 4
        print("  ✓ Ligand-receptor binding works")
    except Exception as e:
        print(f"  ✗ Ligand-receptor binding: {e}")
        return False

    # Test cytokine network
    try:
        from organchip.immune.cytokines import CytokineNetwork

        network = CytokineNetwork()
        state = (0.5, 0.3, 0.4, 1.0, 0.8)  # Cytokines
        derivs = network.derivatives(0.0, state, stimulus=0.0)
        assert len(derivs) == 5
        print("  ✓ Cytokine network works")
    except Exception as e:
        print(f"  ✗ Cytokine network: {e}")
        return False

    # Test circulation
    try:
        from organchip.circulation.pbpk import MultiOrganPBPK

        pbpk = MultiOrganPBPK()
        state = {'plasma': 100.0, 'liver': 0.0, 'heart': 0.0,
                 'brain': 0.0, 'kidney': 0.0, 'muscle': 0.0,
                 'adipose': 0.0, 'gut': 0.0}
        derivs = pbpk.derivatives(0.0, state, dose_rate=0.0)
        assert 'plasma' in derivs
        print("  ✓ PBPK circulation works")
    except Exception as e:
        print(f"  ✗ PBPK circulation: {e}")
        return False

    return True


def test_orchestrator():
    """Test the complete orchestrator."""
    print("\nTesting orchestrator...")

    try:
        from organchip.orchestrator import create_default_organ_chip_suite

        # Create suite
        suite = create_default_organ_chip_suite()
        suite.verbose = False  # Suppress output

        # Initialize state
        state = suite.initialize_state(drug_amount_mg=100.0)
        assert 'circulation' in state
        assert 'liver' in state
        assert 'cardiac' in state
        assert 'immune' in state
        print("  ✓ State initialization works")

        # Run short simulation
        trajectory = suite.simulate_drug_exposure(
            dose_mg=50.0,
            duration_hours=1.0,
            dt=0.1
        )
        assert len(trajectory) > 0
        print(f"  ✓ Simulation works ({len(trajectory)} time points)")

        # Assess toxicity
        tox = suite.assess_toxicity(trajectory)
        assert 'overall_toxicity_score' in tox
        assert 'liver' in tox
        assert 'cardiac' in tox
        print(f"  ✓ Toxicity assessment works (score={tox['overall_toxicity_score']:.3f})")

    except Exception as e:
        print(f"  ✗ Orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_complete_study():
    """Test a complete end-to-end study."""
    print("\nTesting complete study workflow...")

    try:
        from organchip.orchestrator import create_default_organ_chip_suite

        suite = create_default_organ_chip_suite()
        suite.verbose = False

        # Run complete study
        trajectory, tox = suite.run_complete_study(
            dose_mg=100.0,
            duration_hours=2.0,
            dt=0.2,
            export_file=None
        )

        # Validate results
        assert len(trajectory) > 0
        assert tox['overall_toxicity_score'] >= 0.0
        assert tox['overall_toxicity_score'] <= 1.0

        print(f"  ✓ Complete study works")
        print(f"    - Duration: {trajectory[-1][0]:.1f} hours")
        print(f"    - Overall toxicity: {tox['overall_toxicity_score']:.3f}")
        print(f"    - Severity: {tox['overall_severity']}")
        print(f"    - Liver: {tox['liver']['severity']}")
        print(f"    - Cardiac: {tox['cardiac']['severity']}")

    except Exception as e:
        print(f"  ✗ Complete study: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def main():
    """Run all validation tests."""
    print("="*70)
    print("ORGAN CHIP SUITE VALIDATION")
    print("="*70)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Basic Functionality", test_basic_functionality()))
    results.append(("Orchestrator", test_orchestrator()))
    results.append(("Complete Study", test_complete_study()))

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:<30} {status}")
        if not passed:
            all_passed = False

    print("="*70)

    if all_passed:
        print("\n✓ ALL VALIDATION TESTS PASSED\n")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
