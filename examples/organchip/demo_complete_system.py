"""Complete organ chip suite demonstration.

This demo shows end-to-end drug toxicity screening using the full
multi-organ platform.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from organchip.orchestrator import create_default_organ_chip_suite


def main():
    """Run complete organ chip demonstration."""
    print("\n" + "="*70)
    print("ORGAN CHIP SUITE - COMPLETE DEMONSTRATION")
    print("="*70)

    # Create organ chip suite
    suite = create_default_organ_chip_suite()

    # === SCENARIO 1: Therapeutic Dose ===
    print("\n" + "-"*70)
    print("SCENARIO 1: Therapeutic Dose (100 mg)")
    print("-"*70)

    traj1, tox1 = suite.run_complete_study(
        dose_mg=100.0,
        duration_hours=48.0,
        dt=0.1,
        export_file="therapeutic_dose_results.json"
    )

    # === SCENARIO 2: High Dose (Potential Toxicity) ===
    print("\n" + "-"*70)
    print("SCENARIO 2: High Dose (500 mg)")
    print("-"*70)

    suite2 = create_default_organ_chip_suite()
    traj2, tox2 = suite2.run_complete_study(
        dose_mg=500.0,
        duration_hours=48.0,
        dt=0.1,
        export_file="high_dose_results.json"
    )

    # === SCENARIO 3: Cardiotoxic Drug (hERG Blocker) ===
    print("\n" + "-"*70)
    print("SCENARIO 3: Cardiotoxic Drug (hERG IC50 = 1.0 μM)")
    print("-"*70)

    suite3 = create_default_organ_chip_suite()
    suite3.cardiac.ion_channels.IC50_hERG = 1.0  # Potent hERG blocker
    traj3, tox3 = suite3.run_complete_study(
        dose_mg=200.0,
        duration_hours=48.0,
        dt=0.1,
        export_file="cardiotoxic_drug_results.json"
    )

    # === SCENARIO 4: Hepatotoxic Drug (Reactive Metabolite) ===
    print("\n" + "-"*70)
    print("SCENARIO 4: Hepatotoxic Drug (High Reactive Metabolite)")
    print("-"*70)

    suite4 = create_default_organ_chip_suite()
    suite4.liver.metabolism.frac_phase1_to_reactive = 0.4  # 40% to reactive metabolite
    traj4, tox4 = suite4.run_complete_study(
        dose_mg=300.0,
        duration_hours=72.0,
        dt=0.1,
        export_file="hepatotoxic_drug_results.json"
    )

    # === COMPARATIVE SUMMARY ===
    print("\n" + "="*70)
    print("COMPARATIVE TOXICITY SUMMARY")
    print("="*70)

    scenarios = [
        ("Therapeutic Dose", tox1),
        ("High Dose", tox2),
        ("Cardiotoxic Drug", tox3),
        ("Hepatotoxic Drug", tox4),
    ]

    print(f"\n{'Scenario':<20} {'Overall':<10} {'Liver':<12} {'Cardiac':<12} {'Immune':<10}")
    print("-"*70)

    for name, tox in scenarios:
        overall = f"{tox['overall_toxicity_score']:.3f}"
        liver_sev = tox['liver']['severity'][:8]
        cardiac_sev = tox['cardiac']['severity'][:8]
        immune_idx = f"{tox['immune']['inflammatory_index']:.2f}"

        print(f"{name:<20} {overall:<10} {liver_sev:<12} {cardiac_sev:<12} {immune_idx:<10}")

    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nResults exported to:")
    print("  - therapeutic_dose_results.json")
    print("  - high_dose_results.json")
    print("  - cardiotoxic_drug_results.json")
    print("  - hepatotoxic_drug_results.json")
    print("\n")


if __name__ == "__main__":
    main()
