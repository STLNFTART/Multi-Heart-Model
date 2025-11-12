"""
Demo: Doxorubicin Cardiotoxicity Simulation

This demo simulates doxorubicin-induced cardiotoxicity using the
complete organ-on-chip suite.

Scenario:
---------
- Drug: Doxorubicin (anthracycline chemotherapy)
- Dose: 500 μM·L (therapeutic cancer dose)
- Duration: 72 hours
- Mechanism: Mitochondrial dysfunction → ROS → Ca2+ dysregulation → cardiotoxicity

Expected Outcomes:
------------------
1. Drug distribution to heart tissue
2. hERG channel block (QT prolongation)
3. Calcium handling dysfunction
4. Reduced cardiac contractility
5. Mitochondrial damage
6. Potential arrhythmias

Run this demo:
--------------
```bash
python examples/organ_chip/demo_doxorubicin_cardiotoxicity.py
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
    print("Doxorubicin Cardiotoxicity Simulation")
    print("=" * 70)
    print()

    # Create suite configured for doxorubicin cardiotoxicity
    print("Setting up organ-on-chip system...")
    suite = OrganChipSuite.create_doxorubicin_cardiotoxicity()
    print("✓ Molecular models initialized")
    print("✓ Immune signaling model initialized")
    print("✓ Liver model configured for doxorubicin")
    print("✓ Cardiac model configured for cardiotoxicity")
    print("✓ Pharmacokinetics model initialized")
    print("✓ Multiscale coupling established")
    print()

    # Simulation parameters
    dose = 500.0  # μM·L (therapeutic dose)
    duration = 72.0  # hours (3 days)
    dt = 0.1  # hours

    print(f"Simulation Parameters:")
    print(f"  Dose: {dose} μM·L (therapeutic chemotherapy dose)")
    print(f"  Duration: {duration} hours")
    print(f"  Time step: {dt} hours")
    print()

    # Run simulation
    print("Running simulation...")
    print("Time (h)  | C_heart (μM) | hERG Block | Force  | Liver Viability")
    print("-" * 70)

    results = suite.run(
        duration=duration,
        dt=dt,
        dose=dose,
        dose_time=0.0,
        adaptive=True,
        save_interval=10
    )

    # Display progress
    for i, t in enumerate(results['time']):
        if i % 10 == 0:
            pk_state = results['pk'][i]
            heart_state = results['heart'][i]
            liver_state = results['liver'][i]

            print(f"{t:8.1f}  | {pk_state['C_heart']:12.2f} | "
                  f"{heart_state.get('hERG_block', 0.0):10.1%} | "
                  f"{heart_state.get('force', 0.0):6.3f} | "
                  f"{liver_state['viability']:15.1%}")

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

    # Cardiac toxicity
    print("Cardiac Toxicity:")
    print(f"  Maximum hERG block: {summary['heart']['max_hERG_block']:.1%}")
    print(f"  Final contractile force: {summary['heart']['final_force']:.3f}")
    print()

    # Liver effects
    print("Liver Effects:")
    print(f"  Maximum damage: {summary['liver']['max_damage']:.1%}")
    print(f"  Minimum viability: {summary['liver']['min_viability']:.1%}")
    print()

    # Interpretation
    print("=" * 70)
    print("Interpretation")
    print("=" * 70)
    print()

    if summary['heart']['max_hERG_block'] > 0.5:
        print("⚠️  SIGNIFICANT QT PROLONGATION RISK")
        print(f"   hERG block of {summary['heart']['max_hERG_block']:.1%} "
              "indicates high arrhythmia risk.")
        print("   ECG monitoring is strongly recommended.")
    elif summary['heart']['max_hERG_block'] > 0.2:
        print("⚠️  MODERATE QT PROLONGATION RISK")
        print(f"   hERG block of {summary['heart']['max_hERG_block']:.1%} "
              "indicates moderate risk.")
    else:
        print("✓  Low QT prolongation risk")

    print()

    force_reduction = 1.0 - summary['heart']['final_force']
    if force_reduction > 0.3:
        print("⚠️  SIGNIFICANT CONTRACTILITY REDUCTION")
        print(f"   Contractile force reduced by {force_reduction:.1%}.")
        print("   This indicates impaired cardiac function.")
    elif force_reduction > 0.1:
        print("⚠️  MODERATE CONTRACTILITY REDUCTION")
        print(f"   Contractile force reduced by {force_reduction:.1%}.")
    else:
        print("✓  Contractility preserved")

    print()

    # Export results
    output_file = "doxorubicin_cardiotoxicity_results.csv"
    suite.export_results(output_file, format='csv')
    print(f"Results exported to: {output_file}")
    print()

    # Recommendations
    print("=" * 70)
    print("Clinical Recommendations")
    print("=" * 70)
    print()
    print("For doxorubicin cardiotoxicity prevention/management:")
    print("  1. Monitor cardiac function (LVEF) regularly")
    print("  2. Consider dexrazoxane as cardioprotectant")
    print("  3. Limit cumulative dose (<450-550 mg/m²)")
    print("  4. ECG monitoring for QT prolongation")
    print("  5. Monitor troponin and BNP biomarkers")
    print("  6. Consider liposomal formulations to reduce toxicity")
    print()

    print("Simulation complete!")


if __name__ == '__main__':
    main()
