"""
Demo: Acetaminophen (APAP) Hepatotoxicity Simulation

This demo simulates acetaminophen-induced liver toxicity using the
complete organ-on-chip suite.

Scenario:
---------
- Drug: Acetaminophen (APAP)
- Dose: 2000 μM·L (toxic overdose)
- Duration: 48 hours
- Mechanism: NAPQI formation → GSH depletion → oxidative stress → hepatotoxicity

Expected Outcomes:
------------------
1. Rapid drug absorption and distribution
2. Hepatic metabolism to toxic NAPQI metabolite
3. Glutathione (GSH) depletion
4. Reactive oxygen species (ROS) accumulation
5. Progressive hepatocellular damage
6. Immune activation (inflammatory response)
7. Potential for recovery if GSH regenerates

Run this demo:
--------------
```bash
python examples/organ_chip/demo_acetaminophen_toxicity.py
```
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from organ_chip.orchestrator import OrganChipSuite


def main():
    print("=" * 70)
    print("Acetaminophen Hepatotoxicity Simulation")
    print("=" * 70)
    print()

    # Create suite configured for APAP toxicity
    print("Setting up organ-on-chip system...")
    suite = OrganChipSuite.create_acetaminophen_toxicity()
    print("✓ Molecular models initialized")
    print("✓ Immune signaling model initialized")
    print("✓ Liver model configured for APAP metabolism")
    print("✓ Cardiac model initialized")
    print("✓ Pharmacokinetics model initialized")
    print("✓ Multiscale coupling established")
    print()

    # Simulation parameters
    dose = 2000.0  # μM·L (toxic overdose, ~4x therapeutic)
    duration = 48.0  # hours
    dt = 0.1  # hours

    print(f"Simulation Parameters:")
    print(f"  Dose: {dose} μM·L (toxic overdose)")
    print(f"  Duration: {duration} hours")
    print(f"  Time step: {dt} hours")
    print()

    # Run simulation
    print("Running simulation...")
    print("Time (h)  | C_blood (μM) | Liver Damage | GSH (mM) | Viability")
    print("-" * 70)

    results = suite.run(
        duration=duration,
        dt=dt,
        dose=dose,
        dose_time=0.0,
        adaptive=True,
        save_interval=10  # Save every hour
    )

    # Display progress
    for i, t in enumerate(results['time']):
        if i % 10 == 0:  # Every 10 steps (1 hour)
            pk_state = results['pk'][i]
            liver_state = results['liver'][i]

            print(f"{t:8.1f}  | {pk_state['C_blood']:12.2f} | "
                  f"{liver_state['Damage']:12.1%} | "
                  f"{liver_state['GSH']:8.2f} | "
                  f"{liver_state['viability']:9.1%}")

    print()

    # Get summary statistics
    summary = suite.get_summary()

    print("=" * 70)
    print("Summary Statistics")
    print("=" * 70)
    print()

    # Pharmacokinetics
    print("Pharmacokinetics:")
    print(f"  Cmax (blood): {summary['pk']['Cmax_blood']:.2f} μM")
    print(f"  AUC: {summary['pk']['AUC']:.2f} μM·h")
    print(f"  Half-life: {summary['pk']['half_life']:.2f} h")
    print()

    # Liver toxicity
    print("Liver Toxicity:")
    print(f"  Maximum damage: {summary['liver']['max_damage']:.1%}")
    print(f"  Minimum viability: {summary['liver']['min_viability']:.1%}")
    print(f"  Final GSH/GSSG ratio: {summary['liver']['final_GSH_GSSG_ratio']:.2f}")
    print()

    # Immune response
    print("Immune Response:")
    print(f"  Max inflammatory index: {summary['immune']['max_inflammatory_index']:.2f}")
    print()

    # Cardiac effects
    print("Cardiac Effects:")
    print(f"  Max hERG block: {summary['heart']['max_hERG_block']:.1%}")
    print(f"  Final contractile force: {summary['heart']['final_force']:.3f}")
    print()

    # Interpretation
    print("=" * 70)
    print("Interpretation")
    print("=" * 70)
    print()

    if summary['liver']['max_damage'] > 0.7:
        print("⚠️  SEVERE HEPATOTOXICITY DETECTED")
        print("   The toxic dose caused severe liver damage (>70%).")
        print("   This level of damage would be life-threatening.")
    elif summary['liver']['max_damage'] > 0.3:
        print("⚠️  MODERATE HEPATOTOXICITY DETECTED")
        print("   The dose caused significant liver damage (>30%).")
        print("   Clinical intervention would be required.")
    else:
        print("✓  Minimal hepatotoxicity")
        print("   The dose caused limited liver damage (<30%).")

    print()

    if summary['liver']['final_GSH_GSSG_ratio'] < 5.0:
        print("⚠️  OXIDATIVE STRESS DETECTED")
        print(f"   GSH/GSSG ratio ({summary['liver']['final_GSH_GSSG_ratio']:.1f}) "
              "indicates oxidative stress.")
    else:
        print("✓  Normal redox status maintained")

    print()

    # Export results
    output_file = "acetaminophen_toxicity_results.csv"
    suite.export_results(output_file, format='csv')
    print(f"Results exported to: {output_file}")
    print()

    # Recommendations
    print("=" * 70)
    print("Clinical Recommendations")
    print("=" * 70)
    print()
    print("For acetaminophen overdose:")
    print("  1. Administer N-acetylcysteine (NAC) to replenish GSH")
    print("  2. Monitor liver function (ALT, AST, bilirubin)")
    print("  3. Consider activated charcoal if within 1-2 hours")
    print("  4. Supportive care and fluid management")
    print()

    print("Simulation complete!")


if __name__ == '__main__':
    main()
