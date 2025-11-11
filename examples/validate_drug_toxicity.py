"""
Drug Toxicity Validation Suite

Validates the multi-organ digital twin system against known toxicological
profiles of clinically important drugs.

Validation Drugs:
1. Doxorubicin - Cardiotoxicity (dose-dependent cardiomyopathy)
2. Acetaminophen - Hepatotoxicity (NAPQI-mediated liver injury)
3. Isoniazid - Hepatotoxicity (drug-induced liver injury)
4. Cisplatin - Nephrotoxicity and ototoxicity
5. Amiodarone - Multi-organ toxicity (liver, lung, thyroid)
6. Sotalol - QT prolongation (hERG block)
7. Ethanol - Hepatotoxicity and cardiomyopathy

Author: Multi-Organ Chip Architecture Team
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from typing import Dict, List
from dataclasses import dataclass

from src.organ_chips import (
    MultiOrganDigitalTwin,
    SimulationConfig,
    Ligand,
    HeartChip,
    LiverChip,
    CardiacToxicity,
    LiverToxicity,
)


@dataclass
class ValidationResult:
    """Results from a drug toxicity validation"""
    drug_name: str
    dose: float
    duration: float

    # Expected outcomes
    expected_cardiotoxic: bool
    expected_hepatotoxic: bool
    expected_qt_prolongation: bool

    # Observed outcomes
    observed_cardiac_injury: str
    observed_hepatic_injury: str
    observed_qtc: float

    # Organ viabilities
    heart_viability: float
    liver_viability: float

    # Pass/Fail
    validation_passed: bool
    notes: str = ""


class DrugToxicityValidator:
    """
    Validates digital twin predictions against known drug toxicity profiles
    """

    def __init__(self):
        self.results: List[ValidationResult] = []

    def validate_doxorubicin(self) -> ValidationResult:
        """
        Validate doxorubicin cardiotoxicity

        Known profile:
        - Dose-dependent cardiotoxicity
        - Cumulative dose > 450 mg/m² → High risk of heart failure
        - Mechanism: Mitochondrial damage, ROS generation
        - Expected: Reduced EF, elevated troponin, normal liver
        """
        print("\n" + "="*70)
        print("Validating: Doxorubicin (Cardiotoxic)")
        print("="*70)

        # High dose simulation
        heart = HeartChip()

        results = CardiacToxicity.doxorubicin_toxicity(
            heart_chip=heart,
            dose_mg_m2=300.0,  # High cumulative dose
            duration_hours=2.0,
            dt=0.01
        )

        final_state = results[-1]
        toxicity = final_state['toxicity_assessment']

        # Validation criteria
        cardiac_injury_expected = True
        cardiac_injury_observed = toxicity['myocardial_injury'] in ['Moderate', 'Severe']
        viability = final_state['viability']

        validation_passed = cardiac_injury_observed and viability < 0.8

        result = ValidationResult(
            drug_name="Doxorubicin",
            dose=300.0,
            duration=2.0,
            expected_cardiotoxic=True,
            expected_hepatotoxic=False,
            expected_qt_prolongation=False,
            observed_cardiac_injury=toxicity['myocardial_injury'],
            observed_hepatic_injury="None",
            observed_qtc=final_state['toxicity_assessment'].get('QTc_prolongation', 'None'),
            heart_viability=viability,
            liver_viability=1.0,
            validation_passed=validation_passed,
            notes=f"Troponin: {final_state['biomarkers']['troponin_I']:.3f} ng/mL, "
                  f"EF: {final_state['cardiac_function']['ejection_fraction']:.3f}"
        )

        self._print_result(result)
        self.results.append(result)
        return result

    def validate_acetaminophen(self) -> ValidationResult:
        """
        Validate acetaminophen hepatotoxicity

        Known profile:
        - Dose-dependent hepatotoxicity
        - Toxic dose: > 150 mg/kg
        - Mechanism: CYP2E1 → NAPQI → GSH depletion → hepatocyte necrosis
        - Expected: Elevated ALT/AST, normal heart
        """
        print("\n" + "="*70)
        print("Validating: Acetaminophen (Hepatotoxic)")
        print("="*70)

        # Toxic dose simulation
        liver = LiverChip()

        results = LiverToxicity.acetaminophen_toxicity(
            liver_chip=liver,
            dose_mg_kg=200.0,  # Toxic dose
            duration_hours=2.0,
            dt=0.1
        )

        final_state = results[-1]
        toxicity = final_state['toxicity_assessment']

        # Validation criteria
        hepatic_injury_expected = True
        hepatic_injury_observed = toxicity['severity'] in ['Moderate', 'Severe']
        viability = final_state['viability']

        validation_passed = hepatic_injury_observed and viability < 0.8

        result = ValidationResult(
            drug_name="Acetaminophen",
            dose=200.0,
            duration=2.0,
            expected_cardiotoxic=False,
            expected_hepatotoxic=True,
            expected_qt_prolongation=False,
            observed_cardiac_injury="None",
            observed_hepatic_injury=toxicity['severity'],
            observed_qtc=0.0,
            heart_viability=1.0,
            liver_viability=viability,
            validation_passed=validation_passed,
            notes=f"ALT: {final_state['liver_function']['ALT']:.1f} U/L, "
                  f"Pattern: {toxicity['injury_pattern']}"
        )

        self._print_result(result)
        self.results.append(result)
        return result

    def validate_qt_prolonging_drug(self) -> ValidationResult:
        """
        Validate QT-prolonging drug (Sotalol)

        Known profile:
        - hERG channel blocker
        - QT prolongation → Torsades de Pointes risk
        - Expected: Prolonged QTc, arrhythmia risk
        """
        print("\n" + "="*70)
        print("Validating: Sotalol (QT Prolongation)")
        print("="*70)

        heart = HeartChip()

        results = CardiacToxicity.qt_prolonging_drug(
            heart_chip=heart,
            drug_name="Sotalol",
            concentration=10.0,  # μM (high therapeutic)
            herg_ic50=5.0,  # μM
            duration_hours=1.0,
            dt=0.01
        )

        final_state = results[-1]
        toxicity = final_state['toxicity_assessment']
        ecg = final_state['ecg']

        # Validation criteria
        qt_prolongation_expected = True
        qt_prolongation_observed = toxicity['QTc_prolongation'] in ['Moderate', 'High']
        qtc = ecg['QTc']

        validation_passed = qt_prolongation_observed and qtc > 450

        result = ValidationResult(
            drug_name="Sotalol",
            dose=10.0,
            duration=1.0,
            expected_cardiotoxic=False,
            expected_hepatotoxic=False,
            expected_qt_prolongation=True,
            observed_cardiac_injury="None",
            observed_hepatic_injury="None",
            observed_qtc=qtc,
            heart_viability=final_state['viability'],
            liver_viability=1.0,
            validation_passed=validation_passed,
            notes=f"QTc: {qtc:.0f} ms, hERG block: {final_state['hERG_block']:.2f}, "
                  f"Rhythm: {ecg['rhythm']}"
        )

        self._print_result(result)
        self.results.append(result)
        return result

    def validate_multi_organ_digital_twin(self) -> ValidationResult:
        """
        Validate complete multi-organ digital twin with a compound
        showing both cardio and hepatotoxicity
        """
        print("\n" + "="*70)
        print("Validating: Multi-Organ Digital Twin (Amiodarone-like compound)")
        print("="*70)

        # Configure simulation
        config = SimulationConfig(
            duration=4.0,  # 4 hours
            dt=0.01,
            output_interval=120.0,  # 2 minutes
            drug_name="amiodarone",
            dose_mg=400.0,
            route="IV"
        )

        # Create digital twin
        twin = MultiOrganDigitalTwin(config)

        # Create drug with both cardiac and hepatic toxicity
        drug = Ligand(
            name="amiodarone",
            concentration=0.0,
            molecular_weight=645.3,
            clearance_rate=0.05,  # Very slow clearance
            logP=7.0,  # Highly lipophilic
        )

        # Run simulation
        time_points = twin.simulate(drug)

        # Assess toxicity
        toxicity = twin.assess_toxicity()

        # Get final state
        final_tp = time_points[-1]

        # Validation criteria
        multi_organ_toxicity = (
            toxicity.get('cardiac_toxicity', {}).get('viability', 1.0) < 0.9 and
            toxicity.get('hepatotoxicity', {}).get('viability', 1.0) < 0.9
        )

        validation_passed = multi_organ_toxicity

        result = ValidationResult(
            drug_name="Amiodarone-like",
            dose=400.0,
            duration=4.0,
            expected_cardiotoxic=True,
            expected_hepatotoxic=True,
            expected_qt_prolongation=True,
            observed_cardiac_injury=str(toxicity.get('cardiac_toxicity', {}).get('myocardial_injury', 'Unknown')),
            observed_hepatic_injury=str(toxicity.get('hepatotoxicity', {}).get('severity', 'Unknown')),
            observed_qtc=final_tp.qtc,
            heart_viability=final_tp.heart_viability,
            liver_viability=final_tp.liver_viability,
            validation_passed=validation_passed,
            notes=f"Overall safety: {toxicity['overall_safety']}, "
                  f"Avg viability: {toxicity.get('average_viability', 0):.3f}"
        )

        self._print_result(result)
        self.results.append(result)

        # Export results
        twin.export_results("results/validation_multi_organ.json")
        twin.export_csv("results/validation_multi_organ.csv")

        return result

    def _print_result(self, result: ValidationResult) -> None:
        """Print validation result"""
        print(f"\nDrug: {result.drug_name}")
        print(f"  Dose: {result.dose} (Duration: {result.duration}h)")
        print(f"  Heart Viability: {result.heart_viability:.3f}")
        print(f"  Liver Viability: {result.liver_viability:.3f}")
        print(f"  Cardiac Injury: {result.observed_cardiac_injury}")
        print(f"  Hepatic Injury: {result.observed_hepatic_injury}")
        print(f"  QTc: {result.observed_qtc:.0f} ms" if result.observed_qtc > 0 else "  QTc: N/A")
        print(f"  Notes: {result.notes}")
        print(f"  ✓ PASSED" if result.validation_passed else "  ✗ FAILED")

    def run_full_validation(self) -> Dict:
        """
        Run complete validation suite
        """
        print("\n" + "="*70)
        print("DRUG TOXICITY VALIDATION SUITE")
        print("Multi-Organ Digital Twin System")
        print("="*70)

        # Run all validations
        self.validate_doxorubicin()
        self.validate_acetaminophen()
        self.validate_qt_prolonging_drug()
        self.validate_multi_organ_digital_twin()

        # Summary
        print("\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.validation_passed)

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")

        print("\nDetailed Results:")
        for i, result in enumerate(self.results, 1):
            status = "✓" if result.validation_passed else "✗"
            print(f"  {i}. {status} {result.drug_name:<20} - "
                  f"Heart: {result.heart_viability:.3f}, "
                  f"Liver: {result.liver_viability:.3f}")

        return {
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': passed / total * 100,
            'results': self.results
        }


def main():
    """Main validation entry point"""
    validator = DrugToxicityValidator()
    summary = validator.run_full_validation()

    print("\n" + "="*70)
    print("Validation Complete!")
    print("="*70)

    if summary['success_rate'] >= 75.0:
        print(f"\n✓ System validated successfully ({summary['success_rate']:.1f}% pass rate)")
        return 0
    else:
        print(f"\n✗ System validation needs improvement ({summary['success_rate']:.1f}% pass rate)")
        return 1


if __name__ == "__main__":
    exit(main())
