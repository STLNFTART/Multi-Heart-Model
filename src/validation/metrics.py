"""
Physiological metrics computation for validation.

This module provides tools for computing clinical metrics like HRV,
pressure-volume loops, and waveform analysis.
"""

from typing import List, Tuple, Dict, Any
import math


def compute_hrv_metrics(
    rr_intervals: List[float],
    sampling_rate: float = 1000.0,
) -> Dict[str, float]:
    """
    Compute Heart Rate Variability metrics.

    Implements standards from Task Force (1996) and Kleiger et al. (1987).

    Args:
        rr_intervals: R-R intervals in milliseconds
        sampling_rate: Sampling rate in Hz (default 1000 Hz)

    Returns:
        Dictionary with HRV metrics:
        - Time domain: SDNN, RMSSD, pNN50
        - Frequency domain: LF power, HF power, LF/HF ratio
    """
    if len(rr_intervals) < 2:
        raise ValueError("Need at least 2 RR intervals for HRV analysis")

    metrics = {}

    # ===== TIME DOMAIN METRICS =====

    # SDNN: Standard deviation of NN intervals
    mean_rr = sum(rr_intervals) / len(rr_intervals)
    variance = sum((rr - mean_rr)**2 for rr in rr_intervals) / (len(rr_intervals) - 1)
    sdnn = math.sqrt(variance)
    metrics['sdnn_ms'] = sdnn

    # RMSSD: Root mean square of successive differences
    successive_diffs = [
        rr_intervals[i+1] - rr_intervals[i]
        for i in range(len(rr_intervals) - 1)
    ]
    squared_diffs = [d**2 for d in successive_diffs]
    rmssd = math.sqrt(sum(squared_diffs) / len(squared_diffs))
    metrics['rmssd_ms'] = rmssd

    # pNN50: Percentage of successive differences > 50 ms
    nn50 = sum(1 for d in successive_diffs if abs(d) > 50)
    pnn50 = (nn50 / len(successive_diffs)) * 100 if successive_diffs else 0
    metrics['pnn50_pct'] = pnn50

    # Mean heart rate
    mean_hr = 60000.0 / mean_rr if mean_rr > 0 else 0  # Convert to bpm
    metrics['mean_hr_bpm'] = mean_hr

    # ===== FREQUENCY DOMAIN METRICS =====
    # Simplified implementation using Welch-like approach

    # Convert RR intervals to evenly sampled heart rate signal
    # This is a simplification; full implementation would use interpolation
    # and proper spectral estimation

    n_samples = len(rr_intervals)

    # Compute power spectral density (simplified)
    # Using autocorrelation-based approach

    # Detrend (remove mean)
    rr_detrended = [rr - mean_rr for rr in rr_intervals]

    # Compute autocorrelation for lags 0 to n_samples//2
    max_lag = min(n_samples // 2, 100)
    autocorr = []
    for lag in range(max_lag):
        acf = sum(
            rr_detrended[i] * rr_detrended[i + lag]
            for i in range(n_samples - lag)
        ) / (n_samples - lag)
        autocorr.append(acf)

    # Estimate PSD using autocorrelation (Blackman-Tukey method)
    # Apply simple triangular window
    windowed_acf = [
        autocorr[i] * (1 - i / max_lag)
        for i in range(max_lag)
    ]

    # Compute FFT (simplified DFT for low frequencies)
    # We only need VLF (0-0.04 Hz), LF (0.04-0.15 Hz), HF (0.15-0.4 Hz)

    # Frequency resolution
    dt_avg = mean_rr / 1000.0  # Average interval in seconds
    freq_res = 1.0 / (max_lag * dt_avg)

    # Compute power in frequency bands
    vlf_power = 0.0  # 0.003 - 0.04 Hz
    lf_power = 0.0   # 0.04 - 0.15 Hz
    hf_power = 0.0   # 0.15 - 0.4 Hz

    for k in range(1, max_lag):
        freq = k * freq_res

        # Compute DFT coefficient magnitude squared (power)
        # P(f) = |sum(acf * exp(-2πikf))|²
        # Simplified: use autocorrelation value as approximation
        power_component = abs(windowed_acf[k])

        if 0.003 <= freq < 0.04:
            vlf_power += power_component
        elif 0.04 <= freq < 0.15:
            lf_power += power_component
        elif 0.15 <= freq <= 0.4:
            hf_power += power_component

    # Normalize by frequency resolution
    vlf_power *= freq_res
    lf_power *= freq_res
    hf_power *= freq_res

    metrics['vlf_power_ms2'] = vlf_power
    metrics['lf_power_ms2'] = lf_power
    metrics['hf_power_ms2'] = hf_power

    # Total power
    total_power = vlf_power + lf_power + hf_power
    metrics['total_power_ms2'] = total_power

    # LF/HF ratio (sympathovagal balance)
    lf_hf_ratio = lf_power / hf_power if hf_power > 0 else 0
    metrics['lf_hf_ratio'] = lf_hf_ratio

    # Normalized units
    metrics['lf_nu'] = (lf_power / (lf_power + hf_power)) * 100 if (lf_power + hf_power) > 0 else 0
    metrics['hf_nu'] = (hf_power / (lf_power + hf_power)) * 100 if (lf_power + hf_power) > 0 else 0

    return metrics


def compute_pv_loop_metrics(
    pressure_lv: List[float],
    volume_lv: List[float],
) -> Dict[str, float]:
    """
    Compute pressure-volume loop metrics.

    Based on Suga et al. (1973) and Sunagawa et al. (1983).

    Args:
        pressure_lv: Left ventricular pressure (mmHg)
        volume_lv: Left ventricular volume (mL)

    Returns:
        Dictionary with PV loop metrics:
        - Stroke work (area of loop)
        - End-systolic volume (ESV)
        - End-diastolic volume (EDV)
        - Stroke volume (SV)
        - Ejection fraction (EF)
        - Contractility indices
    """
    if len(pressure_lv) != len(volume_lv):
        raise ValueError("Pressure and volume arrays must have same length")

    if len(pressure_lv) < 4:
        raise ValueError("Need at least one complete cardiac cycle")

    metrics = {}

    # Find end-diastolic point (maximum volume)
    edv_idx = volume_lv.index(max(volume_lv))
    edv = volume_lv[edv_idx]
    edp = pressure_lv[edv_idx]

    # Find end-systolic point (minimum volume during ejection)
    # Approximate as global minimum after EDV
    esv_idx = volume_lv.index(min(volume_lv))
    esv = volume_lv[esv_idx]
    esp = pressure_lv[esv_idx]

    # Basic metrics
    stroke_volume = edv - esv
    ejection_fraction = (stroke_volume / edv * 100) if edv > 0 else 0

    metrics['edv_ml'] = edv
    metrics['esv_ml'] = esv
    metrics['edp_mmhg'] = edp
    metrics['esp_mmhg'] = esp
    metrics['stroke_volume_ml'] = stroke_volume
    metrics['ejection_fraction_pct'] = ejection_fraction

    # Stroke work (area of PV loop)
    # Use shoelace formula for polygon area
    n = len(pressure_lv)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += volume_lv[i] * pressure_lv[j]
        area -= volume_lv[j] * pressure_lv[i]
    stroke_work = abs(area) / 2.0

    metrics['stroke_work_mmhg_ml'] = stroke_work

    # Convert to Joules (1 mmHg·mL = 0.133322 J)
    metrics['stroke_work_j'] = stroke_work * 0.133322

    # End-systolic elastance (Ees) - slope of ESPVR
    # Simplified: single point estimate
    # Ees = ESP / (ESV - V0), assume V0 ≈ 0 for simplification
    ees = esp / esv if esv > 0 else 0
    metrics['ees_mmhg_ml'] = ees

    # Arterial elastance (Ea) - effective arterial elastance
    # Ea = ESP / SV
    ea = esp / stroke_volume if stroke_volume > 0 else 0
    metrics['ea_mmhg_ml'] = ea

    # Ventricular-arterial coupling ratio
    coupling_ratio = ees / ea if ea > 0 else 0
    metrics['va_coupling_ratio'] = coupling_ratio

    # Contractility index: dP/dt max (requires time derivative)
    # Approximate using finite differences
    if len(pressure_lv) > 1:
        dp_dt = [
            pressure_lv[i+1] - pressure_lv[i]
            for i in range(len(pressure_lv) - 1)
        ]
        dp_dt_max = max(dp_dt) if dp_dt else 0
        metrics['dp_dt_max_mmhg_per_sample'] = dp_dt_max

    return metrics


def extract_rr_intervals_from_trajectory(
    trajectory: List[Tuple[float, Any]],
    cardiac_component_index: int = 2,
    threshold: float = 0.0,
) -> List[float]:
    """
    Extract R-R intervals from cardiac trajectory.

    Args:
        trajectory: List of (time, state) tuples
        cardiac_component_index: Index of cardiac variable to use (default 2 for x in (v,w,x,y))
        threshold: Threshold for peak detection

    Returns:
        List of R-R intervals in milliseconds
    """
    times = [t for t, _ in trajectory]
    values = [state[cardiac_component_index] for _, state in trajectory]

    # Find peaks (R-wave analogs)
    peaks = []
    for i in range(1, len(values) - 1):
        if (values[i] > values[i-1] and
            values[i] > values[i+1] and
            values[i] > threshold):
            peaks.append(times[i])

    # Compute RR intervals
    rr_intervals = [
        (peaks[i+1] - peaks[i]) * 1000.0  # Convert to milliseconds
        for i in range(len(peaks) - 1)
    ]

    return rr_intervals


def compare_waveforms(
    signal1: List[float],
    signal2: List[float],
    time1: List[float] = None,
    time2: List[float] = None,
) -> Dict[str, float]:
    """
    Compare two physiological waveforms.

    Args:
        signal1: First signal
        signal2: Second signal
        time1: Time points for signal1 (optional)
        time2: Time points for signal2 (optional)

    Returns:
        Dictionary with comparison metrics
    """
    # Ensure same length (truncate to shorter)
    n = min(len(signal1), len(signal2))
    s1 = signal1[:n]
    s2 = signal2[:n]

    # Amplitude comparison
    amplitude1 = max(s1) - min(s1)
    amplitude2 = max(s2) - min(s2)

    # Mean and variance
    mean1 = sum(s1) / n
    mean2 = sum(s2) / n

    var1 = sum((x - mean1)**2 for x in s1) / n
    var2 = sum((x - mean2)**2 for x in s2) / n

    # Correlation
    cov = sum((x - mean1) * (y - mean2) for x, y in zip(s1, s2)) / n
    correlation = cov / math.sqrt(var1 * var2) if (var1 * var2) > 0 else 0

    # RMSE
    rmse = math.sqrt(sum((x - y)**2 for x, y in zip(s1, s2)) / n)

    # Normalized RMSE
    nrmse = rmse / amplitude1 if amplitude1 > 0 else 0

    # Peak detection and frequency comparison
    peaks1 = []
    for i in range(1, len(s1) - 1):
        if s1[i] > s1[i-1] and s1[i] > s1[i+1]:
            peaks1.append(i)

    peaks2 = []
    for i in range(1, len(s2) - 1):
        if s2[i] > s2[i-1] and s2[i] > s2[i+1]:
            peaks2.append(i)

    freq_ratio = len(peaks1) / len(peaks2) if len(peaks2) > 0 else 0

    return {
        'amplitude1': amplitude1,
        'amplitude2': amplitude2,
        'amplitude_ratio': amplitude1 / amplitude2 if amplitude2 > 0 else 0,
        'mean1': mean1,
        'mean2': mean2,
        'correlation': correlation,
        'rmse': rmse,
        'nrmse': nrmse,
        'num_peaks1': len(peaks1),
        'num_peaks2': len(peaks2),
        'frequency_ratio': freq_ratio,
    }


def classify_hrv_status(hrv_metrics: Dict[str, float]) -> str:
    """
    Classify autonomic status based on HRV metrics.

    Based on clinical guidelines from Task Force (1996) and
    Kleiger et al. (1987).

    Args:
        hrv_metrics: Dictionary from compute_hrv_metrics()

    Returns:
        String classification: 'normal', 'reduced', 'severely_reduced'
    """
    sdnn = hrv_metrics.get('sdnn_ms', 0)
    rmssd = hrv_metrics.get('rmssd_ms', 0)
    lf_hf_ratio = hrv_metrics.get('lf_hf_ratio', 0)

    # SDNN < 50 ms is severely reduced (associated with increased mortality)
    # SDNN < 100 ms is moderately reduced
    # SDNN > 100 ms is normal

    if sdnn < 50:
        status = 'severely_reduced'
    elif sdnn < 100:
        status = 'reduced'
    else:
        status = 'normal'

    # Add autonomic balance assessment
    if lf_hf_ratio > 2.5:
        balance = 'sympathetic_dominance'
    elif lf_hf_ratio < 0.5:
        balance = 'parasympathetic_dominance'
    else:
        balance = 'balanced'

    return f"{status}_{balance}"


def estimate_baroreflex_sensitivity(
    rr_intervals: List[float],
    systolic_bp: List[float],
) -> float:
    """
    Estimate baroreflex sensitivity (BRS).

    Based on sequence method from La Rovere et al. (1998).

    Args:
        rr_intervals: R-R intervals in ms
        systolic_bp: Systolic blood pressure values in mmHg

    Returns:
        BRS in ms/mmHg
    """
    if len(rr_intervals) != len(systolic_bp):
        raise ValueError("RR and SBP arrays must have same length")

    if len(rr_intervals) < 3:
        return 0.0

    # Find sequences where both RR and SBP increase/decrease together
    # Minimum sequence length: 3 beats

    sequences = []
    for start in range(len(rr_intervals) - 3):
        # Check for increasing sequence
        rr_increasing = all(
            rr_intervals[start + i] < rr_intervals[start + i + 1]
            for i in range(3)
        )
        sbp_increasing = all(
            systolic_bp[start + i] < systolic_bp[start + i + 1]
            for i in range(3)
        )

        if rr_increasing and sbp_increasing:
            # Compute slope
            rr_seq = rr_intervals[start:start+4]
            sbp_seq = systolic_bp[start:start+4]

            # Linear regression
            n = len(rr_seq)
            mean_rr = sum(rr_seq) / n
            mean_sbp = sum(sbp_seq) / n

            cov = sum((rr - mean_rr) * (sbp - mean_sbp)
                     for rr, sbp in zip(rr_seq, sbp_seq))
            var_sbp = sum((sbp - mean_sbp)**2 for sbp in sbp_seq)

            slope = cov / var_sbp if var_sbp > 0 else 0
            sequences.append(slope)

    # Average slopes from all sequences
    if sequences:
        brs = sum(sequences) / len(sequences)
    else:
        brs = 0.0

    return brs
