"""
Physiological benchmarks from published literature.

This module contains reference values, parameter ranges, and validation
criteria from peer-reviewed publications for validating model outputs.

References:
    See docs/REFERENCES.md for complete citations
"""

from dataclasses import dataclass
from typing import Tuple, Dict, Any
import math


@dataclass
class ParameterRange:
    """Valid range for a physiological parameter."""
    min_value: float
    max_value: float
    typical_value: float
    units: str
    reference: str

    def is_valid(self, value: float) -> bool:
        """Check if value is within physiological range."""
        return self.min_value <= value <= self.max_value

    def is_typical(self, value: float, tolerance: float = 0.2) -> bool:
        """Check if value is within tolerance of typical value."""
        return abs(value - self.typical_value) / self.typical_value <= tolerance


@dataclass
class CardiacBenchmarks:
    """
    Cardiac physiology reference values.

    Based on:
    - Ten Tusscher et al. (2004) - Human ventricular model
    - O'Hara et al. (2011) - Undiseased human ventricle
    - Jose & Collison (1970) - Intrinsic heart rate
    """

    # Heart Rate (beats per minute)
    heart_rate_rest = ParameterRange(
        min_value=60.0,
        max_value=100.0,
        typical_value=72.0,
        units="bpm",
        reference="Jose & Collison (1970)"
    )

    heart_rate_intrinsic = ParameterRange(
        min_value=100.0,
        max_value=110.0,
        typical_value=105.0,
        units="bpm",
        reference="Jose & Collison (1970)"
    )

    # Action Potential Duration (milliseconds)
    apd90 = ParameterRange(
        min_value=250.0,
        max_value=450.0,
        typical_value=320.0,
        units="ms",
        reference="Ten Tusscher et al. (2004)"
    )

    # Resting Membrane Potential (millivolts)
    resting_potential = ParameterRange(
        min_value=-95.0,
        max_value=-80.0,
        typical_value=-86.0,
        units="mV",
        reference="Ten Tusscher et al. (2004)"
    )

    # Peak Action Potential (millivolts)
    peak_potential = ParameterRange(
        min_value=20.0,
        max_value=50.0,
        typical_value=35.0,
        units="mV",
        reference="Ten Tusscher et al. (2004)"
    )

    # Conduction Velocity (m/s)
    conduction_velocity = ParameterRange(
        min_value=0.3,
        max_value=1.0,
        typical_value=0.6,
        units="m/s",
        reference="Ten Tusscher et al. (2004)"
    )

    # QT Interval (milliseconds)
    qt_interval = ParameterRange(
        min_value=350.0,
        max_value=440.0,
        typical_value=400.0,
        units="ms",
        reference="CiPA Initiative (2016)"
    )

    # Corrected QT (Bazett formula)
    qtc_interval = ParameterRange(
        min_value=350.0,
        max_value=460.0,  # 460 for women, 450 for men
        typical_value=410.0,
        units="ms",
        reference="CiPA Initiative (2016)"
    )


@dataclass
class NeuralBenchmarks:
    """
    Neural oscillator and autonomic reference values.

    Based on:
    - FitzHugh (1961) - Neural excitability
    - Izhikevich (2007) - Dynamical systems in neuroscience
    - Malliani et al. (1991) - Cardiovascular neural regulation
    """

    # Autonomic Tone (normalized 0-1)
    sympathetic_tone_rest = ParameterRange(
        min_value=0.2,
        max_value=0.4,
        typical_value=0.3,
        units="normalized",
        reference="Malliani et al. (1991)"
    )

    parasympathetic_tone_rest = ParameterRange(
        min_value=0.6,
        max_value=0.8,
        typical_value=0.7,
        units="normalized",
        reference="Malliani et al. (1991)"
    )

    # Firing Rate (Hz)
    vagal_firing_rate = ParameterRange(
        min_value=0.5,
        max_value=5.0,
        typical_value=2.0,
        units="Hz",
        reference="Levy & Martin (1979)"
    )

    sympathetic_firing_rate = ParameterRange(
        min_value=0.5,
        max_value=10.0,
        typical_value=2.0,
        units="Hz",
        reference="Levy & Martin (1979)"
    )

    # FitzHugh-Nagumo Parameters
    fhn_a = ParameterRange(
        min_value=0.5,
        max_value=1.0,
        typical_value=0.7,
        units="dimensionless",
        reference="FitzHugh (1961)"
    )

    fhn_b = ParameterRange(
        min_value=0.5,
        max_value=1.0,
        typical_value=0.8,
        units="dimensionless",
        reference="FitzHugh (1961)"
    )

    fhn_c = ParameterRange(
        min_value=1.0,
        max_value=5.0,
        typical_value=3.0,
        units="dimensionless",
        reference="Izhikevich (2007)"
    )


@dataclass
class CouplingBenchmarks:
    """
    Heart-brain coupling reference values.

    Based on:
    - Eckberg (1997) - Sympathovagal balance
    - Silvani et al. (2016) - Brain-heart interactions
    - Thayer & Lane (2009) - Neurovisceral integration
    """

    # Neural Transmission Delays (seconds)
    sympathetic_delay = ParameterRange(
        min_value=0.150,
        max_value=0.300,
        typical_value=0.200,
        units="seconds",
        reference="Eckberg (1997)"
    )

    parasympathetic_delay = ParameterRange(
        min_value=0.050,
        max_value=0.150,
        typical_value=0.100,
        units="seconds",
        reference="Eckberg (1997)"
    )

    # Afferent (cardiac to brain) delay
    afferent_delay = ParameterRange(
        min_value=0.100,
        max_value=0.200,
        typical_value=0.150,
        units="seconds",
        reference="Silvani et al. (2016)"
    )

    # Coupling Strength (normalized)
    neural_to_cardiac_gain = ParameterRange(
        min_value=0.0,
        max_value=1.0,
        typical_value=0.5,
        units="normalized",
        reference="Thayer & Lane (2009)"
    )

    cardiac_to_neural_gain = ParameterRange(
        min_value=0.0,
        max_value=1.0,
        typical_value=0.3,
        units="normalized",
        reference="Thayer & Lane (2009)"
    )


@dataclass
class HemodynamicBenchmarks:
    """
    Clinical hemodynamic reference values.

    Based on:
    - Guyton et al. (1955) - Cardiac output regulation
    - Suga et al. (1973) - Pressure-volume relationships
    - Swan et al. (1970) - Pulmonary artery catheterization
    """

    # Blood Pressure (mmHg)
    systolic_bp = ParameterRange(
        min_value=100.0,
        max_value=140.0,
        typical_value=120.0,
        units="mmHg",
        reference="Standard clinical"
    )

    diastolic_bp = ParameterRange(
        min_value=60.0,
        max_value=90.0,
        typical_value=80.0,
        units="mmHg",
        reference="Standard clinical"
    )

    mean_arterial_pressure = ParameterRange(
        min_value=70.0,
        max_value=105.0,
        typical_value=93.0,
        units="mmHg",
        reference="Standard clinical"
    )

    # Central Venous Pressure (mmHg)
    cvp = ParameterRange(
        min_value=2.0,
        max_value=8.0,
        typical_value=5.0,
        units="mmHg",
        reference="Swan et al. (1970)"
    )

    # Pulmonary Artery Pressure (mmHg)
    pa_systolic = ParameterRange(
        min_value=15.0,
        max_value=30.0,
        typical_value=25.0,
        units="mmHg",
        reference="Swan et al. (1970)"
    )

    pa_diastolic = ParameterRange(
        min_value=4.0,
        max_value=12.0,
        typical_value=10.0,
        units="mmHg",
        reference="Swan et al. (1970)"
    )

    # Pulmonary Capillary Wedge Pressure (mmHg)
    pcwp = ParameterRange(
        min_value=4.0,
        max_value=12.0,
        typical_value=8.0,
        units="mmHg",
        reference="Swan et al. (1970)"
    )

    # Cardiac Output (L/min)
    cardiac_output = ParameterRange(
        min_value=4.0,
        max_value=8.0,
        typical_value=5.0,
        units="L/min",
        reference="Guyton et al. (1955)"
    )

    # Stroke Volume (mL)
    stroke_volume = ParameterRange(
        min_value=55.0,
        max_value=100.0,
        typical_value=70.0,
        units="mL",
        reference="Guyton et al. (1955)"
    )

    # Ejection Fraction (%)
    ejection_fraction = ParameterRange(
        min_value=55.0,
        max_value=75.0,
        typical_value=65.0,
        units="%",
        reference="Standard clinical"
    )

    # Systemic Vascular Resistance (dyn·s/cm⁵)
    svr = ParameterRange(
        min_value=800.0,
        max_value=1200.0,
        typical_value=1000.0,
        units="dyn·s/cm⁵",
        reference="Standard clinical"
    )


@dataclass
class HRVBenchmarks:
    """
    Heart Rate Variability reference values.

    Based on:
    - Task Force (1996) - HRV standards
    - Kleiger et al. (1987) - Clinical significance
    """

    # Time Domain Measures
    sdnn = ParameterRange(
        min_value=100.0,
        max_value=250.0,
        typical_value=141.0,
        units="ms",
        reference="Task Force (1996)"
    )

    rmssd = ParameterRange(
        min_value=20.0,
        max_value=100.0,
        typical_value=42.0,
        units="ms",
        reference="Task Force (1996)"
    )

    # Frequency Domain Measures (ms²)
    lf_power = ParameterRange(
        min_value=500.0,
        max_value=2000.0,
        typical_value=1170.0,
        units="ms²",
        reference="Task Force (1996)"
    )

    hf_power = ParameterRange(
        min_value=300.0,
        max_value=1500.0,
        typical_value=975.0,
        units="ms²",
        reference="Task Force (1996)"
    )

    # LF/HF Ratio (sympathovagal balance)
    lf_hf_ratio = ParameterRange(
        min_value=0.5,
        max_value=2.5,
        typical_value=1.5,
        units="ratio",
        reference="Task Force (1996)"
    )


@dataclass
class DrugBenchmarks:
    """
    Drug toxicity reference values.

    Based on:
    - CiPA Initiative - Cardiotoxicity
    - Xu et al. (2008) - Hepatotoxicity
    """

    # hERG IC50 values (μM) for known cardiotoxic drugs
    herg_ic50_dofetilide = ParameterRange(
        min_value=0.01,
        max_value=0.05,
        typical_value=0.015,
        units="μM",
        reference="CiPA reference drugs"
    )

    herg_ic50_sotalol = ParameterRange(
        min_value=40.0,
        max_value=80.0,
        typical_value=50.0,
        units="μM",
        reference="CiPA reference drugs"
    )

    herg_ic50_quinidine = ParameterRange(
        min_value=0.5,
        max_value=1.5,
        typical_value=0.7,
        units="μM",
        reference="CiPA reference drugs"
    )

    # Hepatotoxicity - ALT elevation (U/L)
    alt_normal = ParameterRange(
        min_value=7.0,
        max_value=56.0,
        typical_value=30.0,
        units="U/L",
        reference="Standard clinical"
    )

    alt_hepatotoxic_threshold = ParameterRange(
        min_value=168.0,  # 3x ULN
        max_value=500.0,
        typical_value=250.0,
        units="U/L",
        reference="Hy's Law criteria"
    )


class PhysiologicalBenchmarks:
    """
    Comprehensive physiological validation benchmarks.

    This class aggregates all benchmark categories and provides
    convenience methods for validation.
    """

    def __init__(self):
        self.cardiac = CardiacBenchmarks()
        self.neural = NeuralBenchmarks()
        self.coupling = CouplingBenchmarks()
        self.hemodynamic = HemodynamicBenchmarks()
        self.hrv = HRVBenchmarks()
        self.drug = DrugBenchmarks()

    def validate_all_parameters(self, params: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate a parameter dictionary against all benchmarks.

        Args:
            params: Dictionary of parameter names and values

        Returns:
            Dictionary mapping parameter names to validation status
        """
        results = {}

        # Check each parameter against appropriate benchmark
        for name, value in params.items():
            benchmark = self._get_benchmark(name)
            if benchmark is not None:
                results[name] = benchmark.is_valid(value)
            else:
                results[name] = None  # No benchmark available

        return results

    def _get_benchmark(self, param_name: str) -> ParameterRange:
        """Get appropriate benchmark for a parameter name."""
        # Map parameter names to benchmarks
        benchmark_map = {
            'heart_rate': self.cardiac.heart_rate_rest,
            'apd90': self.cardiac.apd90,
            'qt_interval': self.cardiac.qt_interval,
            'systolic_bp': self.hemodynamic.systolic_bp,
            'diastolic_bp': self.hemodynamic.diastolic_bp,
            'cardiac_output': self.hemodynamic.cardiac_output,
            'stroke_volume': self.hemodynamic.stroke_volume,
            'ejection_fraction': self.hemodynamic.ejection_fraction,
            'cvp': self.hemodynamic.cvp,
            'pcwp': self.hemodynamic.pcwp,
            'sympathetic_delay': self.coupling.sympathetic_delay,
            'parasympathetic_delay': self.coupling.parasympathetic_delay,
            'sdnn': self.hrv.sdnn,
            'rmssd': self.hrv.rmssd,
            'lf_hf_ratio': self.hrv.lf_hf_ratio,
        }

        return benchmark_map.get(param_name)

    def generate_validation_report(self, params: Dict[str, Any]) -> str:
        """
        Generate a human-readable validation report.

        Args:
            params: Dictionary of parameters to validate

        Returns:
            Formatted validation report string
        """
        results = self.validate_all_parameters(params)

        report = ["=" * 60]
        report.append("PHYSIOLOGICAL PARAMETER VALIDATION REPORT")
        report.append("=" * 60)
        report.append("")

        valid_count = sum(1 for v in results.values() if v is True)
        invalid_count = sum(1 for v in results.values() if v is False)
        unknown_count = sum(1 for v in results.values() if v is None)

        report.append(f"Total parameters: {len(results)}")
        report.append(f"Valid: {valid_count}")
        report.append(f"Invalid: {invalid_count}")
        report.append(f"No benchmark: {unknown_count}")
        report.append("")

        report.append("Parameter Details:")
        report.append("-" * 60)

        for name, is_valid in results.items():
            value = params[name]
            benchmark = self._get_benchmark(name)

            if benchmark:
                status = "✓ VALID" if is_valid else "✗ INVALID"
                report.append(f"{name}: {value} {benchmark.units}")
                report.append(f"  {status}")
                report.append(f"  Range: [{benchmark.min_value}, {benchmark.max_value}]")
                report.append(f"  Typical: {benchmark.typical_value}")
                report.append(f"  Reference: {benchmark.reference}")
            else:
                report.append(f"{name}: {value}")
                report.append(f"  No benchmark available")

            report.append("")

        report.append("=" * 60)

        return "\n".join(report)
