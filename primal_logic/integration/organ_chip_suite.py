"""
Complete Organ-on-Chip Digital Twin Suite

Integrates all components into a unified heart-liver organ-on-chip system
with drug screening and toxicity prediction capabilities.

This is the main entry point for running complete simulations combining:
- Molecular dynamics (drug-receptor binding)
- Cellular dynamics (hepatocytes, cardiomyocytes, immune cells)
- Organ function (liver metabolism, cardiac electrophysiology)
- Systemic circulation
- Bidirectional multiscale coupling

Usage:
    >>> suite = OrganChipSuite()
    >>> results = suite.run_drug_screen("doxorubicin", dose=50.0, duration=48.0)
    >>> suite.generate_report(results)
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Dict, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from .multiscale_coupling import MultiscaleCoupling, MultiscaleCouplingParameters


class ToxicitySeverity(Enum):
    """Toxicity severity classification"""
    SAFE = "Safe"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    SEVERE = "Severe"


@dataclass
class DrugProfile:
    """Complete drug profile for simulation"""
    name: str
    dose_mg: float                      # Dose in mg
    molecular_weight: float             # g/mol
    cyp_isoform: str = "CYP3A4"        # Primary metabolic pathway
    hERG_IC50: float = 10.0            # μM
    hepatotoxic: bool = False
    cardiotoxic: bool = True
    bioavailability: float = 1.0
    protein_binding: float = 0.5


@dataclass
class ToxicityReport:
    """Comprehensive toxicity assessment"""
    drug_name: str

    # Hepatotoxicity
    peak_liver_toxicity: float
    final_hepatocyte_viability: float
    peak_ALT: float

    # Cardiotoxicity
    peak_cardiac_toxicity: float
    peak_hERG_block: float
    peak_QTc_prolongation: float
    arrhythmia_risk: str

    # Pharmacokinetics
    Cmax: float
    Tmax: float
    AUC: float

    # Overall assessment
    overall_severity: ToxicitySeverity
    recommendation: str


class OrganChipSuite:
    """
    Complete organ-on-chip digital twin for drug screening.

    Capabilities:
    - Drug toxicity prediction (hepatotoxicity, cardiotoxicity)
    - Pharmacokinetic/pharmacodynamic modeling
    - Multiscale integration (molecular → systemic)
    - Automated safety assessment

    Usage:
        >>> suite = OrganChipSuite()
        >>> results = suite.run_drug_screen("acetaminophen", dose=1000.0, duration=24.0)
        >>> report = suite.assess_toxicity(results)
        >>> print(report)
    """

    def __init__(self, params: Optional[MultiscaleCouplingParameters] = None):
        self.coupling = MultiscaleCoupling(params)

        # Drug library
        self.drug_library: Dict[str, DrugProfile] = self._initialize_drug_library()

    def _initialize_drug_library(self) -> Dict[str, DrugProfile]:
        """Initialize library of known drugs for testing"""
        return {
            # Hepatotoxic drugs
            "acetaminophen": DrugProfile(
                name="Acetaminophen",
                dose_mg=1000.0,
                molecular_weight=151.16,
                cyp_isoform="CYP2E1",
                hERG_IC50=1000.0,  # Not a hERG blocker
                hepatotoxic=True,
                cardiotoxic=False
            ),

            # Cardiotoxic drugs
            "doxorubicin": DrugProfile(
                name="Doxorubicin",
                dose_mg=50.0,
                molecular_weight=543.52,
                cyp_isoform="CYP3A4",
                hERG_IC50=50.0,
                hepatotoxic=True,
                cardiotoxic=True
            ),

            "dofetilide": DrugProfile(
                name="Dofetilide",
                dose_mg=0.5,
                molecular_weight=441.56,
                cyp_isoform="CYP3A4",
                hERG_IC50=2.0,  # Potent hERG blocker
                hepatotoxic=False,
                cardiotoxic=True
            ),

            # Dual toxicity
            "amiodarone": DrugProfile(
                name="Amiodarone",
                dose_mg=400.0,
                molecular_weight=645.31,
                cyp_isoform="CYP3A4",
                hERG_IC50=10.0,
                hepatotoxic=True,
                cardiotoxic=True
            ),

            # Reference safe drug
            "aspirin": DrugProfile(
                name="Aspirin",
                dose_mg=325.0,
                molecular_weight=180.16,
                cyp_isoform="CYP2C9",
                hERG_IC50=500.0,
                hepatotoxic=False,
                cardiotoxic=False
            ),
        }

    def compute_initial_concentration(self, drug: DrugProfile) -> float:
        """
        Compute initial plasma concentration from dose.

        C0 = (Dose * F * 1000) / (MW * V_d)

        where:
            Dose: mg
            F: bioavailability
            MW: g/mol
            V_d: volume of distribution (assumed 50 L)
        """
        V_d = 50.0  # L

        # Convert dose to moles
        dose_mmol = (drug.dose_mg * drug.bioavailability) / drug.molecular_weight

        # Convert to μmol
        dose_umol = dose_mmol * 1000.0

        # Concentration in μM
        C0 = dose_umol / V_d

        # Account for protein binding (only free drug is active)
        C0_free = C0 * (1 - drug.protein_binding)

        return C0_free

    def setup_drug_dosing(
        self,
        drug: DrugProfile,
        dosing_schedule: str = "bolus",
        duration: float = 24.0
    ) -> callable:
        """
        Create drug dosing function.

        Args:
            drug: Drug profile
            dosing_schedule: "bolus", "infusion", or "q8h" (every 8 hours)
            duration: Infusion duration (hours) if applicable

        Returns:
            Dosing function: time (hr) -> dose rate (μM*L/hr)
        """
        C0 = self.compute_initial_concentration(drug)

        if dosing_schedule == "bolus":
            # IV bolus at t=0
            def dosing_func(t):
                if t < 0.05:  # 3 minute infusion
                    return C0 * 50.0 / 0.05  # Total amount over 0.05 hr
                return 0.0

        elif dosing_schedule == "infusion":
            # Continuous infusion
            infusion_rate = C0 * 50.0 / duration
            def dosing_func(t):
                if t < duration:
                    return infusion_rate
                return 0.0

        elif dosing_schedule == "q8h":
            # Every 8 hours dosing
            def dosing_func(t):
                # Dose at t=0, 8, 16, 24, ...
                hour = int(t)
                if hour % 8 == 0 and (t - hour) < 0.05:
                    return C0 * 50.0 / 0.05
                return 0.0

        else:
            raise ValueError(f"Unknown dosing schedule: {dosing_schedule}")

        return dosing_func

    def run_drug_screen(
        self,
        drug_name: str,
        dose: Optional[float] = None,
        duration: float = 48.0,
        dosing_schedule: str = "bolus",
        dt: float = 0.1
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Run complete drug screening simulation.

        Args:
            drug_name: Name from drug library or custom
            dose: Dose in mg (overrides library default)
            duration: Simulation duration (hours)
            dosing_schedule: Dosing regimen
            dt: Integration timestep (hours)

        Returns:
            (times, results_dict)
        """
        # Reset system
        self.coupling.reset()

        # Get or create drug profile
        if drug_name in self.drug_library:
            drug = self.drug_library[drug_name]
            if dose is not None:
                drug.dose_mg = dose
        else:
            # Create default profile
            drug = DrugProfile(
                name=drug_name,
                dose_mg=dose or 100.0,
                molecular_weight=300.0,
                cyp_isoform="CYP3A4",
                hERG_IC50=10.0,
                hepatotoxic=True,
                cardiotoxic=True
            )

        # Configure coupling
        self.coupling.configure_drug_pathway(
            drug_name=drug.name,
            cyp_isoform=drug.cyp_isoform,
            hERG_IC50=drug.hERG_IC50,
            hepatotoxic=drug.hepatotoxic
        )

        # Setup dosing
        dosing_func = self.setup_drug_dosing(drug, dosing_schedule, duration)
        self.coupling.set_drug_dosing(dosing_func)

        # Run simulation
        times, results = self.coupling.simulate(t_span=(0, duration), dt=dt)

        # Add drug metadata to results
        results['drug_name'] = drug.name
        results['dose_mg'] = drug.dose_mg

        return times, results

    def assess_toxicity(
        self,
        times: np.ndarray,
        results: Dict[str, np.ndarray]
    ) -> ToxicityReport:
        """
        Generate comprehensive toxicity assessment.

        Args:
            times: Time array
            results: Simulation results

        Returns:
            ToxicityReport
        """
        drug_name = results.get('drug_name', 'Unknown')

        # Hepatotoxicity metrics
        peak_liver_tox = np.max(results['liver_toxicity'])
        final_viability = results['hepatocyte_viability'][-1]

        # Approximate ALT from damaged hepatocytes
        viability_loss = 1.0 - final_viability
        peak_ALT = viability_loss * 100.0  # Arbitrary scaling

        # Cardiotoxicity metrics
        peak_cardiac_tox = np.max(results['cardiac_toxicity'])
        peak_hERG = np.max(results['hERG_block'])

        # QTc prolongation (proxy from hERG block)
        peak_QTc_prolong = peak_hERG * 0.5  # Simplified relationship

        # Arrhythmia risk
        if peak_QTc_prolong > 0.3:
            arrhythmia_risk = "HIGH"
        elif peak_QTc_prolong > 0.15:
            arrhythmia_risk = "MODERATE"
        else:
            arrhythmia_risk = "LOW"

        # Pharmacokinetics
        C_arterial = results['C_arterial']
        Cmax = np.max(C_arterial)
        Tmax = times[np.argmax(C_arterial)]
        AUC = np.trapz(C_arterial, times)

        # Overall severity assessment
        severity_score = 0.0

        if peak_liver_tox > 1.0:
            severity_score += 2
        elif peak_liver_tox > 0.5:
            severity_score += 1

        if peak_cardiac_tox > 1.0:
            severity_score += 2
        elif peak_cardiac_tox > 0.5:
            severity_score += 1

        if peak_hERG > 0.5:
            severity_score += 2
        elif peak_hERG > 0.3:
            severity_score += 1

        if viability_loss > 0.3:
            severity_score += 2
        elif viability_loss > 0.1:
            severity_score += 1

        # Map to severity
        if severity_score >= 6:
            overall_severity = ToxicitySeverity.SEVERE
            recommendation = "DO NOT USE - High risk of organ toxicity"
        elif severity_score >= 4:
            overall_severity = ToxicitySeverity.HIGH
            recommendation = "Caution advised - Consider dose reduction or alternative"
        elif severity_score >= 2:
            overall_severity = ToxicitySeverity.MODERATE
            recommendation = "Monitor closely - May require dose adjustment"
        elif severity_score >= 1:
            overall_severity = ToxicitySeverity.LOW
            recommendation = "Acceptable safety profile with monitoring"
        else:
            overall_severity = ToxicitySeverity.SAFE
            recommendation = "Safe within tested dose range"

        report = ToxicityReport(
            drug_name=drug_name,
            peak_liver_toxicity=peak_liver_tox,
            final_hepatocyte_viability=final_viability,
            peak_ALT=peak_ALT,
            peak_cardiac_toxicity=peak_cardiac_tox,
            peak_hERG_block=peak_hERG,
            peak_QTc_prolongation=peak_QTc_prolong,
            arrhythmia_risk=arrhythmia_risk,
            Cmax=Cmax,
            Tmax=Tmax,
            AUC=AUC,
            overall_severity=overall_severity,
            recommendation=recommendation
        )

        return report

    def generate_report(self, report: ToxicityReport) -> str:
        """Generate human-readable toxicity report"""
        lines = []
        lines.append("=" * 70)
        lines.append(f"ORGAN-ON-CHIP TOXICITY REPORT: {report.drug_name}")
        lines.append("=" * 70)

        lines.append("\nHEPATOTOXICITY ASSESSMENT:")
        lines.append(f"  Peak Liver Toxicity Score: {report.peak_liver_toxicity:.3f}")
        lines.append(f"  Final Hepatocyte Viability: {report.final_hepatocyte_viability:.1%}")
        lines.append(f"  Peak ALT (estimated): {report.peak_ALT:.1f} U/L")

        lines.append("\nCARDIOTOXICITY ASSESSMENT:")
        lines.append(f"  Peak Cardiac Toxicity Score: {report.peak_cardiac_toxicity:.3f}")
        lines.append(f"  Peak hERG Channel Block: {report.peak_hERG_block:.1%}")
        lines.append(f"  Peak QTc Prolongation: {report.peak_QTc_prolongation:.1%}")
        lines.append(f"  Arrhythmia Risk: {report.arrhythmia_risk}")

        lines.append("\nPHARMACOKINETICS:")
        lines.append(f"  Cmax: {report.Cmax:.2f} μM")
        lines.append(f"  Tmax: {report.Tmax:.2f} hours")
        lines.append(f"  AUC: {report.AUC:.2f} μM·hr")

        lines.append("\n" + "=" * 70)
        lines.append(f"OVERALL SEVERITY: {report.overall_severity.value.upper()}")
        lines.append("=" * 70)
        lines.append(f"RECOMMENDATION: {report.recommendation}")
        lines.append("=" * 70)

        return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 70)
    print("ORGAN-ON-CHIP DIGITAL TWIN SUITE")
    print("=" * 70)

    suite = OrganChipSuite()

    # Screen multiple drugs
    test_drugs = ["dofetilide", "acetaminophen", "aspirin"]

    for drug_name in test_drugs:
        print(f"\n\nScreening: {drug_name.upper()}")
        print("-" * 70)

        times, results = suite.run_drug_screen(
            drug_name=drug_name,
            duration=48.0,
            dosing_schedule="bolus",
            dt=0.1
        )

        report = suite.assess_toxicity(times, results)
        print(suite.generate_report(report))

    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)
