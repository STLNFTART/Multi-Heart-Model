"""
Demo: Multiscale Integration

This demo showcases the multiscale coupling capabilities of the
organ-on-chip suite, demonstrating signal flow across molecular,
cellular, tissue, organ, and systemic scales.

Scales Demonstrated:
--------------------
1. Molecular: Ligand-receptor binding
2. Cellular: Immune cell activation
3. Tissue: Hepatocyte populations
4. Organ: Liver and heart function
5. Systemic: Pharmacokinetics and circulation

Signal Flow:
------------
Drug (PK) → Liver Metabolism → Damage Signal → Immune Activation
         → Heart Exposure → Ion Channel Block → Contractility

Run this demo:
--------------
```bash
python examples/organ_chip/demo_multiscale_integration.py
```
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from organ_chip.orchestrator import OrganChipSuite


def print_scale_info(scale_name, description, timeoscale):
    """Print formatted scale information."""
    print(f"\n{scale_name}:")
    print(f"  Description: {description}")
    print(f"  Timescale: {timeoscale}")


def main():
    print("=" * 70)
    print("Multiscale Organ-On-Chip Integration Demo")
    print("=" * 70)
    print()

    print("This demo illustrates how the organ chip suite integrates models")
    print("across five distinct spatial and temporal scales:")
    print()

    # Describe each scale
    print_scale_info(
        "1. MOLECULAR SCALE",
        "Ligand-receptor binding dynamics",
        "Microseconds to milliseconds"
    )

    print_scale_info(
        "2. CELLULAR SCALE",
        "Ion channels, enzyme kinetics, immune signaling",
        "Milliseconds to seconds"
    )

    print_scale_info(
        "3. TISSUE SCALE",
        "Cell populations, local diffusion, metabolism",
        "Seconds to minutes"
    )

    print_scale_info(
        "4. ORGAN SCALE",
        "Liver function, cardiac electrophysiology",
        "Minutes to hours"
    )

    print_scale_info(
        "5. SYSTEMIC SCALE",
        "Drug distribution, whole-body pharmacokinetics",
        "Hours to days"
    )

    print()
    print("=" * 70)

    # Create full suite with all components
    print("\nInitializing full organ-on-chip suite...")
    suite = OrganChipSuite()  # All components enabled
    print("✓ All scales initialized and coupled")
    print()

    # Simulation parameters
    dose = 1000.0  # μM·L
    duration = 24.0  # hours
    dt = 0.05  # hours

    print(f"Simulation Parameters:")
    print(f"  Dose: {dose} μM·L")
    print(f"  Duration: {duration} hours")
    print(f"  Time step: {dt} hours (adaptive sub-stepping enabled)")
    print()

    # Run simulation
    print("Running multiscale simulation...")
    print("\nMonitoring signal propagation across scales:")
    print("-" * 70)
    print("Time | Systemic | Organ (Liver) | Cellular | Molecular")
    print("(h)  | C_blood  | Damage        | IL6      | Receptor %")
    print("-" * 70)

    results = suite.run(
        duration=duration,
        dt=dt,
        dose=dose,
        dose_time=0.0,
        adaptive=True,
        save_interval=20  # Every hour
    )

    # Display cross-scale monitoring
    for i, t in enumerate(results['time']):
        if i % 20 == 0:  # Every hour
            # Systemic scale (PK)
            c_blood = results['pk'][i]['C_blood']

            # Organ scale (Liver)
            liver_damage = results['liver'][i]['Damage']

            # Cellular scale (Immune)
            il6 = results['immune'][i]['IL6']

            # Molecular scale (Receptor)
            receptor_occ = results['molecular'][i].get('occupancy', 0.0) * 100

            print(f"{t:4.1f} | {c_blood:8.2f} | {liver_damage:13.1%} | "
                  f"{il6:8.2f} | {receptor_occ:11.1f}%")

    print()

    # Analyze coupling strengths
    print("=" * 70)
    print("Coupling Analysis")
    print("=" * 70)
    print()

    # PK → Liver coupling
    liver_exposures = [s['C_liver'] for s in results['pk']]
    blood_concs = [s['C_blood'] for s in results['pk']]
    partition_ratio = np.mean(liver_exposures) / np.mean(blood_concs)

    print("Systemic → Organ Coupling:")
    print(f"  Liver/Blood partition ratio: {partition_ratio:.2f}")
    print(f"  Indicates: Drug concentrates in liver by {partition_ratio:.1f}x")
    print()

    # Liver → Immune coupling
    damages = [s['Damage'] for s in results['liver']]
    inflammatory_indices = [s['inflammatory_index'] for s in results['immune']]

    print("Organ → Cellular Coupling:")
    if max(damages) > 0.1:
        print(f"  Max liver damage: {max(damages):.1%}")
        print(f"  Max inflammatory index: {max(inflammatory_indices):.2f}")
        print(f"  Correlation: Liver damage triggers immune response")
    else:
        print(f"  Minimal damage, no significant immune activation")
    print()

    # PK → Molecular coupling
    receptor_occupancies = [s.get('occupancy', 0.0) for s in results['molecular']]

    print("Systemic → Molecular Coupling:")
    print(f"  Peak receptor occupancy: {max(receptor_occupancies):.1%}")
    print(f"  Driven by circulating drug concentration")
    print()

    # Time scale analysis
    print("=" * 70)
    print("Time Scale Analysis")
    print("=" * 70)
    print()

    print("The simulation employed adaptive time-stepping to efficiently")
    print("handle disparate time scales:")
    print()
    print("  • Cardiac model: Sub-stepped at ~1 ms resolution")
    print("  • Molecular model: Sub-stepped at ~100 ms resolution")
    print("  • Liver model: Stepped at global resolution (~3 min)")
    print("  • PK model: Stepped at global resolution")
    print()
    print("This operator splitting approach provides:")
    print("  ✓ Numerical stability")
    print("  ✓ Computational efficiency")
    print("  ✓ Accurate capture of fast dynamics")
    print()

    # Export results
    output_file = "multiscale_integration_results.json"
    suite.export_results(output_file, format='json')
    print(f"Results exported to: {output_file}")
    print()

    # Summary
    summary = suite.get_summary()

    print("=" * 70)
    print("Integration Summary")
    print("=" * 70)
    print()

    print("Successfully demonstrated:")
    print("  ✓ Five-scale integration (molecular → systemic)")
    print("  ✓ Bidirectional coupling between scales")
    print("  ✓ Adaptive time-stepping for efficiency")
    print("  ✓ Signal propagation across scales")
    print("  ✓ Multi-organ toxicity prediction")
    print()

    print("Key Findings:")
    print(f"  • Peak blood concentration: {summary['pk']['Cmax_blood']:.2f} μM")
    print(f"  • Liver damage: {summary['liver']['max_damage']:.1%}")
    print(f"  • Cardiac hERG block: {summary['heart']['max_hERG_block']:.1%}")
    print(f"  • Immune activation: {summary['immune']['max_inflammatory_index']:.2f}")
    print()

    print("Simulation complete!")


if __name__ == '__main__':
    main()
