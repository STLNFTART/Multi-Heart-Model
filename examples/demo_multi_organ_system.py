"""
Multi-Organ Digital Twin System - Comprehensive Demonstration

This demo showcases the complete multi-organ chip architecture integrating:
- Heart-on-chip with electrophysiology and contractility
- Liver-on-chip with metabolism and detoxification
- Systemic circulation with drug distribution
- Immune system with inflammatory response
- Heart-brain coupling (from existing HBCM)
- Multiple drug toxicity scenarios

Author: Multi-Organ Chip Architecture Team
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import time as time_module

from src.organ_chips import (
    MultiOrganDigitalTwin,
    SimulationConfig,
    Ligand,
    HeartChip,
    LiverChip,
    CardiacToxicity,
    LiverToxicity,
)


def demo_1_basic_heart_liver_coupling():
    """
    Demo 1: Basic heart-liver coupling with safe drug
    """
    print("\n" + "="*80)
    print("DEMO 1: Basic Heart-Liver Coupling with Safe Therapeutic Drug")
    print("="*80)

    config = SimulationConfig(
        duration=4.0,  # 4 hours
        dt=0.01,
        output_interval=120.0,  # Save every 2 minutes
        drug_name="metoprolol",
        dose_mg=50.0,
        route="IV",
        enable_heart=True,
        enable_liver=True,
        enable_immune=True,
    )

    twin = MultiOrganDigitalTwin(config)

    # Metoprolol: Beta-blocker, therapeutic at this dose
    metoprolol = Ligand(
        name="metoprolol",
        concentration=0.0,
        molecular_weight=267.4,
        clearance_rate=0.3,  # Moderate clearance
        logP=1.88,
    )

    print("\nAdministering metoprolol (beta-blocker) 50 mg IV...")
    time_points = twin.simulate(metoprolol)

    # Results
    toxicity = twin.assess_toxicity()
    final_tp = time_points[-1]

    print("\n" + "-"*80)
    print("RESULTS:")
    print(f"  Overall Safety: {toxicity['overall_safety']}")
    print(f"  Heart Viability: {final_tp.heart_viability:.3f}")
    print(f"  Liver Viability: {final_tp.liver_viability:.3f}")
    print(f"  Heart Rate: {final_tp.heart_rate:.1f} bpm")
    print(f"  Ejection Fraction: {final_tp.ejection_fraction:.3f}")
    print(f"  ALT: {final_tp.alt:.1f} U/L")
    print(f"  Troponin: {final_tp.troponin_i:.3f} ng/mL")

    twin.export_results("results/demo1_safe_drug.json")
    twin.export_csv("results/demo1_safe_drug.csv")

    print("\n✓ Demo 1 complete - Results saved to results/demo1_safe_drug.*")


def demo_2_cardiotoxicity():
    """
    Demo 2: Doxorubicin cardiotoxicity with real-time monitoring
    """
    print("\n" + "="*80)
    print("DEMO 2: Doxorubicin-Induced Cardiotoxicity")
    print("="*80)

    config = SimulationConfig(
        duration=6.0,  # 6 hours
        dt=0.01,
        output_interval=180.0,  # Save every 3 minutes
        drug_name="doxorubicin",
        dose_mg=100.0,  # High dose (cumulative toxicity)
        route="IV",
        enable_heart=True,
        enable_liver=True,
        enable_immune=True,
    )

    twin = MultiOrganDigitalTwin(config)

    # Doxorubicin: Anthracycline chemotherapy
    doxorubicin = Ligand(
        name="doxorubicin",
        concentration=0.0,
        molecular_weight=543.5,
        clearance_rate=0.05,  # Slow clearance
        logP=1.27,
    )

    print("\nAdministering doxorubicin (anthracycline) 100 mg IV...")
    print("Monitoring cardiac function and biomarkers...\n")

    time_points = twin.simulate(doxorubicin)

    # Time-series analysis
    print("\nTime-Series Analysis:")
    print(f"{'Time (h)':<10} {'HR (bpm)':<12} {'EF':<8} {'Trop (ng/mL)':<15} {'Viability':<10}")
    print("-"*60)

    for i, tp in enumerate(time_points[::5]):  # Every 5th point
        print(f"{tp.time/3600:<10.1f} {tp.heart_rate:<12.1f} {tp.ejection_fraction:<8.3f} "
              f"{tp.troponin_i:<15.3f} {tp.heart_viability:<10.3f}")

    # Final assessment
    toxicity = twin.assess_toxicity()
    final_tp = time_points[-1]

    print("\n" + "-"*80)
    print("FINAL CARDIOTOXICITY ASSESSMENT:")
    print(f"  Overall Safety: {toxicity['overall_safety']}")
    print(f"  Cardiac Injury: {toxicity.get('cardiac_toxicity', {}).get('myocardial_injury', 'N/A')}")
    print(f"  Heart Viability: {final_tp.heart_viability:.3f}")
    print(f"  Ejection Fraction: {final_tp.ejection_fraction:.3f}")
    print(f"  Troponin I: {final_tp.troponin_i:.3f} ng/mL (Normal < 0.04)")
    print(f"  BNP: {final_tp.bnp:.1f} pg/mL (Normal < 100)")
    print(f"  Oxidative Stress: {final_tp.oxidative_stress_heart:.2f}")

    twin.export_results("results/demo2_cardiotoxicity.json")
    twin.export_csv("results/demo2_cardiotoxicity.csv")

    print("\n✓ Demo 2 complete - Results saved to results/demo2_cardiotoxicity.*")


def demo_3_hepatotoxicity():
    """
    Demo 3: Acetaminophen hepatotoxicity with metabolism tracking
    """
    print("\n" + "="*80)
    print("DEMO 3: Acetaminophen-Induced Hepatotoxicity")
    print("="*80)

    config = SimulationConfig(
        duration=8.0,  # 8 hours (acute toxicity)
        dt=0.01,
        output_interval=240.0,  # Save every 4 minutes
        drug_name="acetaminophen",
        dose_mg=15000.0,  # 15g overdose
        route="PO",
        enable_heart=True,
        enable_liver=True,
        enable_immune=True,
    )

    twin = MultiOrganDigitalTwin(config)

    # Acetaminophen overdose
    acetaminophen = Ligand(
        name="acetaminophen",
        concentration=0.0,
        molecular_weight=151.16,
        clearance_rate=0.25,
        logP=0.46,
    )

    print("\nAdministering acetaminophen overdose (15g oral)...")
    print("Tracking Phase I/II metabolism and liver injury...\n")

    time_points = twin.simulate(acetaminophen)

    # Time-series analysis
    print("\nHepatotoxicity Timeline:")
    print(f"{'Time (h)':<10} {'ALT (U/L)':<12} {'AST (U/L)':<12} {'Bilirubin':<12} {'Viability':<10}")
    print("-"*60)

    for i, tp in enumerate(time_points[::5]):
        print(f"{tp.time/3600:<10.1f} {tp.alt:<12.1f} {tp.ast:<12.1f} "
              f"{tp.bilirubin:<12.2f} {tp.liver_viability:<10.3f}")

    # Final assessment
    toxicity = twin.assess_toxicity()
    final_tp = time_points[-1]

    print("\n" + "-"*80)
    print("FINAL HEPATOTOXICITY ASSESSMENT:")
    print(f"  Overall Safety: {toxicity['overall_safety']}")
    print(f"  Hepatic Injury: {toxicity.get('hepatotoxicity', {}).get('severity', 'N/A')}")
    print(f"  Injury Pattern: {toxicity.get('hepatotoxicity', {}).get('injury_pattern', 'N/A')}")
    print(f"  Liver Viability: {final_tp.liver_viability:.3f}")
    print(f"  ALT: {final_tp.alt:.1f} U/L (Normal < 40)")
    print(f"  AST: {final_tp.ast:.1f} U/L (Normal < 40)")
    print(f"  Bilirubin: {final_tp.bilirubin:.2f} mg/dL (Normal < 1.2)")
    print(f"  ALT Fold Elevation: {final_tp.alt/40:.1f}x")
    print(f"  Oxidative Stress: {final_tp.oxidative_stress_liver:.2f}")

    twin.export_results("results/demo3_hepatotoxicity.json")
    twin.export_csv("results/demo3_hepatotoxicity.csv")

    print("\n✓ Demo 3 complete - Results saved to results/demo3_hepatotoxicity.*")


def demo_4_qt_prolongation():
    """
    Demo 4: QT interval prolongation and arrhythmia risk
    """
    print("\n" + "="*80)
    print("DEMO 4: Drug-Induced QT Prolongation (Proarrhythmic Risk)")
    print("="*80)

    heart = HeartChip()

    print("\nSimulating hERG channel blockade with Class III antiarrhythmic...")
    print("(Similar to dofetilide, sotalol, or azithromycin)\n")

    results = CardiacToxicity.qt_prolonging_drug(
        heart_chip=heart,
        drug_name="QT_prolonging_agent",
        concentration=8.0,  # μM
        herg_ic50=3.0,  # μM (potent hERG block)
        duration_hours=2.0,
        dt=0.01
    )

    # Time series
    print("ECG Parameter Timeline:")
    print(f"{'Time (min)':<12} {'QT (ms)':<10} {'QTc (ms)':<10} {'HR (bpm)':<10} {'hERG Block':<12}")
    print("-"*60)

    for i, state in enumerate(results[::10]):
        t_min = state['time'] * 60
        ecg = state['ecg']
        print(f"{t_min:<12.0f} {ecg['QT_interval']:<10.0f} {ecg['QTc']:<10.0f} "
              f"{ecg['heart_rate']:<10.1f} {state['hERG_block']:<12.2%}")

    final = results[-1]
    ecg = final['ecg']
    tox = final['toxicity_assessment']

    print("\n" + "-"*80)
    print("ARRHYTHMIA RISK ASSESSMENT:")
    print(f"  QT Interval: {ecg['QT_interval']:.0f} ms")
    print(f"  QTc (Corrected): {ecg['QTc']:.0f} ms")
    print(f"  QTc Risk Category: {tox['QTc_prolongation']}")
    print(f"  Rhythm: {ecg['rhythm']}")
    print(f"  hERG Block: {final['hERG_block']:.1%}")

    if ecg['QTc'] > 500:
        print(f"  ⚠ HIGH RISK: Torsades de Pointes (Life-threatening arrhythmia)")
    elif ecg['QTc'] > 450:
        print(f"  ⚠ MODERATE RISK: QTc prolongation")
    else:
        print(f"  ✓ LOW RISK: Normal QTc")

    print("\n✓ Demo 4 complete")


def demo_5_multi_organ_with_immune_response():
    """
    Demo 5: Multi-organ toxicity with systemic inflammatory response
    """
    print("\n" + "="*80)
    print("DEMO 5: Multi-Organ Toxicity with Immune/Inflammatory Response")
    print("="*80)

    config = SimulationConfig(
        duration=12.0,  # 12 hours
        dt=0.01,
        output_interval=300.0,  # Save every 5 minutes
        drug_name="toxic_compound",
        dose_mg=500.0,
        route="IV",
        enable_heart=True,
        enable_liver=True,
        enable_immune=True,
    )

    twin = MultiOrganDigitalTwin(config)

    # Hypothetical toxic compound with multi-organ effects
    toxic_drug = Ligand(
        name="toxic_compound",
        concentration=0.0,
        molecular_weight=450.0,
        clearance_rate=0.08,
        logP=4.5,
    )

    print("\nAdministering experimental compound (multi-organ toxicity)...")
    print("Monitoring organs and immune response...\n")

    time_points = twin.simulate(toxic_drug)

    # Multi-parameter timeline
    print("Integrated Multi-Organ Status:")
    print(f"{'Time':<8} {'Heart V':<10} {'Liver V':<10} {'IL-6':<12} {'TNF-α':<12} {'CRP':<10}")
    print("-"*70)

    for tp in time_points[::8]:
        print(f"{tp.time/3600:<8.1f} {tp.heart_viability:<10.3f} {tp.liver_viability:<10.3f} "
              f"{tp.il6:<12.1f} {tp.tnf_alpha:<12.1f} {tp.crp:<10.2f}")

    # Final assessment
    toxicity = twin.assess_toxicity()
    final_tp = time_points[-1]

    print("\n" + "-"*80)
    print("MULTI-ORGAN TOXICITY ASSESSMENT:")
    print(f"\nOverall Safety: {toxicity['overall_safety']}")
    print(f"Average Organ Viability: {toxicity.get('average_viability', 0):.3f}")

    print(f"\nCardiac Status:")
    cardiac_tox = toxicity.get('cardiac_toxicity', {})
    print(f"  - Viability: {final_tp.heart_viability:.3f}")
    print(f"  - Injury: {cardiac_tox.get('myocardial_injury', 'N/A')}")
    print(f"  - Troponin: {final_tp.troponin_i:.3f} ng/mL")

    print(f"\nHepatic Status:")
    hepatic_tox = toxicity.get('hepatotoxicity', {})
    print(f"  - Viability: {final_tp.liver_viability:.3f}")
    print(f"  - Severity: {hepatic_tox.get('severity', 'N/A')}")
    print(f"  - ALT: {final_tp.alt:.1f} U/L")

    print(f"\nImmune/Inflammatory Response:")
    immune_tox = toxicity.get('immune_toxicity', {})
    print(f"  - Severity: {immune_tox.get('severity', 'N/A')}")
    print(f"  - SIRS Criteria: {immune_tox.get('SIRS_criteria_met', 0)}/4")
    print(f"  - IL-6: {final_tp.il6:.1f} pg/mL")
    print(f"  - TNF-α: {final_tp.tnf_alpha:.1f} pg/mL")
    print(f"  - CRP: {final_tp.crp:.2f} mg/L")
    print(f"  - WBC: {final_tp.wbc:.0f} cells/μL")

    if immune_tox.get('cytokine_storm', False):
        print(f"  ⚠ CYTOKINE STORM DETECTED")

    twin.export_results("results/demo5_multi_organ.json")
    twin.export_csv("results/demo5_multi_organ.csv")

    print("\n✓ Demo 5 complete - Results saved to results/demo5_multi_organ.*")


def demo_6_pharmacokinetics():
    """
    Demo 6: Detailed pharmacokinetic/pharmacodynamic analysis
    """
    print("\n" + "="*80)
    print("DEMO 6: Pharmacokinetic/Pharmacodynamic (PK/PD) Analysis")
    print("="*80)

    config = SimulationConfig(
        duration=24.0,  # Full 24-hour PK profile
        dt=0.01,
        output_interval=600.0,  # Every 10 minutes
        drug_name="pk_test_drug",
        dose_mg=100.0,
        route="IV",
        enable_heart=True,
        enable_liver=True,
        enable_immune=False,
    )

    twin = MultiOrganDigitalTwin(config)

    pk_drug = Ligand(
        name="pk_test_drug",
        concentration=0.0,
        molecular_weight=350.0,
        clearance_rate=0.15,
        volume_distribution=1.2,
        protein_binding=0.85,
    )

    print("\nRunning 24-hour PK/PD simulation...")
    time_points = twin.simulate(pk_drug)

    # Extract PK parameters
    times = np.array([tp.time / 3600.0 for tp in time_points])
    concentrations = np.array([tp.drug_concentration_arterial for tp in time_points])

    from src.organ_chips.circulation import PharmacokineticsModel
    pk_model = PharmacokineticsModel()

    auc = pk_model.calculate_auc(concentrations, times)
    cmax, tmax = pk_model.calculate_cmax_tmax(concentrations, times)
    t_half = pk_model.calculate_half_life(concentrations, times)

    print("\n" + "-"*80)
    print("PHARMACOKINETIC PARAMETERS:")
    print(f"  Dose: 100 mg IV bolus")
    print(f"  Cmax: {cmax:.2f} μM")
    print(f"  Tmax: {tmax:.2f} hours")
    print(f"  AUC₀₋₂₄: {auc:.2f} μM·h")
    print(f"  Half-life (t½): {t_half:.2f} hours")
    print(f"  Clearance: 0.15 /h")
    print(f"  Volume of Distribution: 1.2 L/kg")
    print(f"  Protein Binding: 85%")

    print("\n✓ Demo 6 complete - PK parameters calculated")


def main():
    """Run all demonstrations"""
    print("\n" + "="*80)
    print(" "*20 + "MULTI-ORGAN DIGITAL TWIN")
    print(" "*15 + "Comprehensive System Demonstration")
    print("="*80)

    start_time = time_module.time()

    # Create results directory
    Path("results").mkdir(exist_ok=True)

    # Run demonstrations
    try:
        demo_1_basic_heart_liver_coupling()
        demo_2_cardiotoxicity()
        demo_3_hepatotoxicity()
        demo_4_qt_prolongation()
        demo_5_multi_organ_with_immune_response()
        demo_6_pharmacokinetics()

        elapsed = time_module.time() - start_time

        print("\n" + "="*80)
        print("ALL DEMONSTRATIONS COMPLETE")
        print("="*80)
        print(f"\nTotal execution time: {elapsed:.1f} seconds")
        print(f"\nResults saved to ./results/ directory:")
        print("  - demo1_safe_drug.*")
        print("  - demo2_cardiotoxicity.*")
        print("  - demo3_hepatotoxicity.*")
        print("  - demo5_multi_organ.*")

        print("\n" + "="*80)
        print("✓ Multi-Organ Digital Twin System Successfully Demonstrated")
        print("="*80)

        return 0

    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
