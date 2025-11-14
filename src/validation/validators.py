"""
Model validation against physiological benchmarks.

This module provides functions to validate model outputs against
published physiological data and established reference models.
"""

from typing import Tuple, List, Dict, Any
import math
from .benchmarks import PhysiologicalBenchmarks


def validate_cardiac_model(
    trajectory: List[Tuple[float, Tuple[float, float]]],
    dt: float = 0.001,
) -> Dict[str, Any]:
    """
    Validate cardiac model outputs against physiological benchmarks.

    Args:
        trajectory: List of (time, (x, y)) tuples from cardiac simulation
        dt: Time step size in seconds

    Returns:
        Dictionary with validation results and metrics
    """
    benchmarks = PhysiologicalBenchmarks()

    # Extract cardiac state
    times = [t for t, _ in trajectory]
    x_values = [state[0] for _, state in trajectory]
    y_values = [state[1] for _, state in trajectory]

    # Compute cardiac metrics
    metrics = {}

    # 1. Estimate frequency/heart rate
    # Find zero crossings of x (upward)
    crossings = []
    for i in range(1, len(x_values)):
        if x_values[i-1] <= 0 and x_values[i] > 0:
            # Linear interpolation for crossing time
            t_cross = times[i-1] + (times[i] - times[i-1]) * (
                -x_values[i-1] / (x_values[i] - x_values[i-1])
            )
            crossings.append(t_cross)

    if len(crossings) >= 2:
        intervals = [crossings[i+1] - crossings[i] for i in range(len(crossings)-1)]
        avg_interval = sum(intervals) / len(intervals)
        frequency_hz = 1.0 / avg_interval
        heart_rate_bpm = frequency_hz * 60.0

        metrics['heart_rate_bpm'] = heart_rate_bpm
        metrics['heart_rate_valid'] = benchmarks.cardiac.heart_rate_rest.is_valid(
            heart_rate_bpm
        )
    else:
        metrics['heart_rate_bpm'] = None
        metrics['heart_rate_valid'] = False

    # 2. Amplitude analysis
    x_amplitude = max(x_values) - min(x_values)
    y_amplitude = max(y_values) - min(y_values)

    metrics['x_amplitude'] = x_amplitude
    metrics['y_amplitude'] = y_amplitude

    # 3. Oscillation stability (coefficient of variation of intervals)
    if len(crossings) >= 3:
        intervals = [crossings[i+1] - crossings[i] for i in range(len(crossings)-1)]
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((x - mean_interval)**2 for x in intervals) / len(intervals)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_interval if mean_interval > 0 else 0

        metrics['interval_cv'] = cv
        metrics['stable_oscillation'] = cv < 0.1  # Less than 10% variation
    else:
        metrics['interval_cv'] = None
        metrics['stable_oscillation'] = False

    # 4. Energy/phase space analysis
    # Compute total energy (approximate)
    energies = [0.5 * (x**2 + y**2) for x, y in zip(x_values, y_values)]
    avg_energy = sum(energies) / len(energies)

    metrics['avg_energy'] = avg_energy

    # Overall validation
    metrics['overall_valid'] = (
        metrics.get('heart_rate_valid', False) and
        metrics.get('stable_oscillation', False) and
        x_amplitude > 0.1  # Meaningful oscillation
    )

    return metrics


def validate_neural_model(
    trajectory: List[Tuple[float, Tuple[float, float]]],
    dt: float = 0.001,
) -> Dict[str, Any]:
    """
    Validate neural model outputs against physiological benchmarks.

    Args:
        trajectory: List of (time, (v, w)) tuples from neural simulation
        dt: Time step size in seconds

    Returns:
        Dictionary with validation results and metrics
    """
    benchmarks = PhysiologicalBenchmarks()

    # Extract neural state
    times = [t for t, _ in trajectory]
    v_values = [state[0] for _, state in trajectory]
    w_values = [state[1] for _, state in trajectory]

    metrics = {}

    # 1. Estimate firing rate (for spiking behavior)
    # Find local maxima in v above threshold
    threshold = 0.5
    spikes = []
    for i in range(1, len(v_values)-1):
        if (v_values[i] > v_values[i-1] and
            v_values[i] > v_values[i+1] and
            v_values[i] > threshold):
            spikes.append(times[i])

    if len(spikes) >= 2:
        intervals = [spikes[i+1] - spikes[i] for i in range(len(spikes)-1)]
        avg_interval = sum(intervals) / len(intervals)
        firing_rate_hz = 1.0 / avg_interval if avg_interval > 0 else 0

        metrics['firing_rate_hz'] = firing_rate_hz

        # Check if in vagal firing rate range
        # (Adjust based on whether this represents vagal or sympathetic)
        metrics['firing_rate_valid'] = benchmarks.neural.vagal_firing_rate.is_valid(
            firing_rate_hz
        )
    else:
        metrics['firing_rate_hz'] = 0.0
        metrics['firing_rate_valid'] = False

    # 2. Amplitude analysis
    v_amplitude = max(v_values) - min(v_values)
    w_amplitude = max(w_values) - min(w_values)

    metrics['v_amplitude'] = v_amplitude
    metrics['w_amplitude'] = w_amplitude

    # 3. Excitability check
    # A healthy neural model should be excitable
    metrics['excitable'] = v_amplitude > 0.1

    # 4. Phase space analysis
    # Check for limit cycle behavior
    # Compute distance from origin in phase space
    radii = [math.sqrt(v**2 + w**2) for v, w in zip(v_values, w_values)]
    avg_radius = sum(radii) / len(radii)
    radius_variance = sum((r - avg_radius)**2 for r in radii) / len(radii)
    radius_std = math.sqrt(radius_variance)

    # Stable limit cycle has low variance in radius
    metrics['avg_radius'] = avg_radius
    metrics['radius_cv'] = radius_std / avg_radius if avg_radius > 0 else 0
    metrics['limit_cycle'] = metrics['radius_cv'] < 0.3

    # Overall validation
    metrics['overall_valid'] = (
        metrics.get('excitable', False) and
        v_amplitude > 0.1
    )

    return metrics


def validate_coupling_model(
    trajectory: List[Tuple[float, Tuple[float, float, float, float]]],
    coupling_params: Any,
    dt: float = 0.001,
) -> Dict[str, Any]:
    """
    Validate coupled heart-brain model against physiological benchmarks.

    Args:
        trajectory: List of (time, (v, w, x, y)) tuples
        coupling_params: CouplingParameters instance
        dt: Time step size in seconds

    Returns:
        Dictionary with validation results and metrics
    """
    benchmarks = PhysiologicalBenchmarks()

    # Split trajectory into neural and cardiac components
    neural_trajectory = [(t, (s[0], s[1])) for t, s in trajectory]
    cardiac_trajectory = [(t, (s[2], s[3])) for t, s in trajectory]

    # Validate individual subsystems
    neural_metrics = validate_neural_model(neural_trajectory, dt)
    cardiac_metrics = validate_cardiac_model(cardiac_trajectory, dt)

    metrics = {
        'neural': neural_metrics,
        'cardiac': cardiac_metrics,
    }

    # Validate coupling parameters
    metrics['coupling_params_valid'] = {
        'neural_to_cardiac_gain': benchmarks.coupling.neural_to_cardiac_gain.is_valid(
            coupling_params.neural_to_cardiac_gain
        ),
        'cardiac_to_neural_gain': benchmarks.coupling.cardiac_to_neural_gain.is_valid(
            coupling_params.cardiac_to_neural_gain
        ),
        'neural_delay': benchmarks.coupling.parasympathetic_delay.is_valid(
            coupling_params.neural_delay
        ),
        'cardiac_delay': benchmarks.coupling.afferent_delay.is_valid(
            coupling_params.cardiac_delay
        ),
    }

    # Check for synchronization/coordination
    # Extract peak times from both systems
    neural_v = [s[0] for _, s in trajectory]
    cardiac_x = [s[2] for _, s in trajectory]
    times = [t for t, _ in trajectory]

    # Find neural peaks
    neural_peaks = []
    for i in range(1, len(neural_v)-1):
        if neural_v[i] > neural_v[i-1] and neural_v[i] > neural_v[i+1]:
            neural_peaks.append(times[i])

    # Find cardiac peaks
    cardiac_peaks = []
    for i in range(1, len(cardiac_x)-1):
        if cardiac_x[i] > cardiac_x[i-1] and cardiac_x[i] > cardiac_x[i+1]:
            cardiac_peaks.append(times[i])

    # Compute phase coherence (simplified)
    if len(neural_peaks) >= 2 and len(cardiac_peaks) >= 2:
        neural_period = (neural_peaks[-1] - neural_peaks[0]) / (len(neural_peaks) - 1)
        cardiac_period = (cardiac_peaks[-1] - cardiac_peaks[0]) / (len(cardiac_peaks) - 1)

        frequency_ratio = neural_period / cardiac_period if cardiac_period > 0 else 0

        metrics['frequency_ratio'] = frequency_ratio
        metrics['synchronized'] = 0.5 <= frequency_ratio <= 2.0
    else:
        metrics['frequency_ratio'] = None
        metrics['synchronized'] = False

    # Overall validation
    metrics['overall_valid'] = (
        neural_metrics['overall_valid'] and
        cardiac_metrics['overall_valid'] and
        all(metrics['coupling_params_valid'].values())
    )

    return metrics


def validate_hemodynamics(
    pressure_data: Dict[str, List[float]],
    volume_data: Dict[str, List[float]],
    time_data: List[float],
) -> Dict[str, Any]:
    """
    Validate hemodynamic data against clinical benchmarks.

    Args:
        pressure_data: Dictionary with pressure time series
            (keys: 'lv', 'aorta', 'pa', 'cvp', etc.)
        volume_data: Dictionary with volume time series
            (keys: 'lv', 'rv', etc.)
        time_data: Time points

    Returns:
        Dictionary with validation results and metrics
    """
    benchmarks = PhysiologicalBenchmarks()
    metrics = {}

    # Validate blood pressures
    if 'aorta' in pressure_data:
        aortic_pressure = pressure_data['aorta']
        systolic = max(aortic_pressure)
        diastolic = min(aortic_pressure)
        mean_pressure = sum(aortic_pressure) / len(aortic_pressure)

        metrics['systolic_bp'] = systolic
        metrics['diastolic_bp'] = diastolic
        metrics['mean_arterial_pressure'] = mean_pressure

        metrics['bp_valid'] = {
            'systolic': benchmarks.hemodynamic.systolic_bp.is_valid(systolic),
            'diastolic': benchmarks.hemodynamic.diastolic_bp.is_valid(diastolic),
            'mean': benchmarks.hemodynamic.mean_arterial_pressure.is_valid(mean_pressure),
        }

    # Validate CVP
    if 'cvp' in pressure_data:
        cvp_mean = sum(pressure_data['cvp']) / len(pressure_data['cvp'])
        metrics['cvp'] = cvp_mean
        metrics['cvp_valid'] = benchmarks.hemodynamic.cvp.is_valid(cvp_mean)

    # Validate PA pressures
    if 'pa' in pressure_data:
        pa_pressure = pressure_data['pa']
        pa_systolic = max(pa_pressure)
        pa_diastolic = min(pa_pressure)

        metrics['pa_systolic'] = pa_systolic
        metrics['pa_diastolic'] = pa_diastolic

        metrics['pa_valid'] = {
            'systolic': benchmarks.hemodynamic.pa_systolic.is_valid(pa_systolic),
            'diastolic': benchmarks.hemodynamic.pa_diastolic.is_valid(pa_diastolic),
        }

    # Validate stroke volume and cardiac output
    if 'lv' in volume_data:
        lv_volume = volume_data['lv']
        edv = max(lv_volume)  # End-diastolic volume
        esv = min(lv_volume)  # End-systolic volume
        stroke_volume = edv - esv

        # Calculate ejection fraction
        ejection_fraction = (stroke_volume / edv * 100) if edv > 0 else 0

        metrics['stroke_volume_ml'] = stroke_volume
        metrics['ejection_fraction_pct'] = ejection_fraction

        metrics['sv_valid'] = benchmarks.hemodynamic.stroke_volume.is_valid(
            stroke_volume
        )
        metrics['ef_valid'] = benchmarks.hemodynamic.ejection_fraction.is_valid(
            ejection_fraction
        )

        # Calculate cardiac output (need heart rate)
        if len(time_data) >= 2:
            # Estimate cycles
            n_samples = len(time_data)
            duration = time_data[-1] - time_data[0]

            # Count volume maxima (end-diastole markers)
            maxima = 0
            for i in range(1, len(lv_volume)-1):
                if lv_volume[i] > lv_volume[i-1] and lv_volume[i] > lv_volume[i+1]:
                    maxima += 1

            if maxima >= 2 and duration > 0:
                heart_rate_bpm = (maxima / duration) * 60.0
                cardiac_output = (stroke_volume / 1000.0) * heart_rate_bpm  # L/min

                metrics['cardiac_output_lpm'] = cardiac_output
                metrics['co_valid'] = benchmarks.hemodynamic.cardiac_output.is_valid(
                    cardiac_output
                )

    # Overall validation
    all_valid = []
    if 'bp_valid' in metrics:
        all_valid.extend(metrics['bp_valid'].values())
    if 'cvp_valid' in metrics:
        all_valid.append(metrics['cvp_valid'])
    if 'sv_valid' in metrics:
        all_valid.append(metrics['sv_valid'])
    if 'ef_valid' in metrics:
        all_valid.append(metrics['ef_valid'])

    metrics['overall_valid'] = all(all_valid) if all_valid else False

    return metrics


def compare_with_reference_model(
    our_output: List[float],
    reference_output: List[float],
    tolerance: float = 0.1,
) -> Dict[str, Any]:
    """
    Compare our model output with a reference model.

    Args:
        our_output: Time series from our model
        reference_output: Time series from reference model (same length)
        tolerance: Relative tolerance for comparison (default 10%)

    Returns:
        Dictionary with comparison metrics
    """
    if len(our_output) != len(reference_output):
        raise ValueError("Output lengths must match")

    n = len(our_output)

    # Compute metrics
    absolute_errors = [abs(a - b) for a, b in zip(our_output, reference_output)]
    relative_errors = [
        abs(a - b) / abs(b) if abs(b) > 1e-10 else 0
        for a, b in zip(our_output, reference_output)
    ]

    mean_absolute_error = sum(absolute_errors) / n
    max_absolute_error = max(absolute_errors)
    mean_relative_error = sum(relative_errors) / n
    max_relative_error = max(relative_errors)

    # Root mean square error
    squared_errors = [(a - b)**2 for a, b in zip(our_output, reference_output)]
    rmse = math.sqrt(sum(squared_errors) / n)

    # Normalized RMSE (divide by range of reference)
    ref_range = max(reference_output) - min(reference_output)
    nrmse = rmse / ref_range if ref_range > 0 else 0

    # Correlation coefficient
    mean_our = sum(our_output) / n
    mean_ref = sum(reference_output) / n

    cov = sum((a - mean_our) * (b - mean_ref) for a, b in zip(our_output, reference_output)) / n
    std_our = math.sqrt(sum((a - mean_our)**2 for a in our_output) / n)
    std_ref = math.sqrt(sum((b - mean_ref)**2 for b in reference_output) / n)

    correlation = cov / (std_our * std_ref) if (std_our * std_ref) > 0 else 0

    return {
        'mean_absolute_error': mean_absolute_error,
        'max_absolute_error': max_absolute_error,
        'mean_relative_error': mean_relative_error,
        'max_relative_error': max_relative_error,
        'rmse': rmse,
        'nrmse': nrmse,
        'correlation': correlation,
        'within_tolerance': mean_relative_error <= tolerance,
    }
