#!/usr/bin/env python3
"""
Heart-Liver Organ-on-Chip Digital Twin Demo

Demonstrates the complete multiscale framework with drug toxicity screening.
Tests multiple drugs with known toxic profiles.

Usage:
    python demos/demo_heart_liver_organ_chip.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from primal_logic.integration.organ_chip_suite import OrganChipSuite


def main():
    print("=" * 80)
    print("HEART-LIVER ORGAN-ON-CHIP DIGITAL TWIN")
    print("Multi-scale Drug Toxicity Screening Platform")
    print("=" * 80)

    # Initialize suite
    print("\nInitializing organ-on-chip digital twin...")
    suite = OrganChipSuite()

    # Test drugs with known profiles
    test_drugs = {
        "dofetilide": {
            "description": "Potent hERG K+ channel blocker (cardiotoxic)",
            "expected": "High cardiac toxicity, QT prolongation"
        },
        "acetaminophen": {
            "description": "Dose-dependent hepatotoxic drug",
            "expected": "Moderate-high hepatotoxicity"
        },
        "doxorubicin": {
            "description": "Chemotherapy agent (dual toxicity)",
            "expected": "Both cardiac and hepatic toxicity"
        },
        "aspirin": {
            "description": "Reference safe drug",
            "expected": "Low toxicity at therapeutic doses"
        }
    }

    results_summary = []

    for drug_name, info in test_drugs.items():
        print("\n" + "=" * 80)
        print(f"SCREENING: {drug_name.upper()}")
        print(f"Description: {info['description']}")
        print(f"Expected outcome: {info['expected']}")
        print("=" * 80)

        # Run simulation
        print(f"\nRunning 48-hour simulation...")
        times, results = suite.run_drug_screen(
            drug_name=drug_name,
            duration=48.0,
            dosing_schedule="bolus",
            dt=0.1
        )

        # Assess toxicity
        report = suite.assess_toxicity(times, results)

        # Print report
        print(suite.generate_report(report))

        # Store summary
        results_summary.append({
            'drug': drug_name,
            'severity': report.overall_severity.value,
            'liver_tox': report.peak_liver_toxicity,
            'cardiac_tox': report.peak_cardiac_toxicity,
            'hERG_block': report.peak_hERG_block
        })

    # Final summary
    print("\n" + "=" * 80)
    print("SCREENING SUMMARY")
    print("=" * 80)
    print(f"\n{'Drug':<20} {'Severity':<15} {'Liver':<10} {'Cardiac':<10} {'hERG':<10}")
    print("-" * 80)

    for summary in results_summary:
        print(f"{summary['drug']:<20} "
              f"{summary['severity']:<15} "
              f"{summary['liver_tox']:<10.3f} "
              f"{summary['cardiac_tox']:<10.3f} "
              f"{summary['hERG_block']:<10.1%}")

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  ✓ Molecular-scale drug-receptor binding")
    print("  ✓ Cellular-scale immune response")
    print("  ✓ Organ-scale liver metabolism and cardiac electrophysiology")
    print("  ✓ Systemic-scale circulation and pharmacokinetics")
    print("  ✓ Bidirectional multiscale coupling")
    print("  ✓ Automated toxicity assessment")
    print("\nApplications:")
    print("  • Pre-clinical drug screening")
    print("  • Dose optimization")
    print("  • Drug-drug interaction prediction")
    print("  • Personalized medicine")
    print("=" * 80)


if __name__ == "__main__":
    main()
