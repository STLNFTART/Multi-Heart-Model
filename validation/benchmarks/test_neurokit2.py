"""
NeuroKit2 Integration Tests

Tests Multi-Heart-Model integration with NeuroKit2 for physiological signal
processing (ECG, EDA, PPG, RSP).

Repository: https://github.com/neuropsychology/NeuroKit
"""

import sys
from pathlib import Path
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validation.framework import ValidationTestBase, BenchmarkResult, PerformanceBenchmark


class NeuroKit2ValidationTests(ValidationTestBase):
    """Validation tests for NeuroKit2 integration."""

    def __init__(self):
        super().__init__("NeuroKit2")

    def test_installation(self) -> BenchmarkResult:
        """Test if NeuroKit2 is properly installed."""
        start = time.time()

        try:
            import neurokit2 as nk

            metrics = {
                'version': nk.__version__
            }

            return BenchmarkResult(
                test_name="Installation Check",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except ImportError as e:
            return BenchmarkResult(
                test_name="Installation Check",
                repository=self.repository_name,
                status='skip',
                execution_time=time.time() - start,
                error_message=f"NeuroKit2 not installed: {e}. Install with: pip install neurokit2"
            )

    def test_import(self) -> BenchmarkResult:
        """Test importing NeuroKit2 modules."""
        start = time.time()

        try:
            import neurokit2 as nk

            # Test that key signal processing modules are available
            _ = nk.ecg_process
            _ = nk.eda_process
            _ = nk.ppg_process
            _ = nk.rsp_process
            _ = nk.emg_process
            _ = nk.signal_rate
            _ = nk.hrv_time
            _ = nk.hrv_frequency

            modules = [
                'ecg', 'eda', 'ppg', 'rsp', 'emg', 'signal', 'hrv'
            ]

            return BenchmarkResult(
                test_name="Import Test",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics={'modules_imported': len(modules)}
            )

        except (ImportError, AttributeError) as e:
            return BenchmarkResult(
                test_name="Import Test",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )

    def test_basic_functionality(self) -> BenchmarkResult:
        """Test basic NeuroKit2 functionality."""
        start = time.time()

        try:
            import neurokit2 as nk

            # Simulate ECG signal
            sampling_rate = 1000
            duration = 10  # seconds
            ecg_signal = nk.ecg_simulate(
                duration=duration,
                sampling_rate=sampling_rate,
                heart_rate=70
            )

            # Process ECG signal
            ecg_cleaned = nk.ecg_clean(ecg_signal, sampling_rate=sampling_rate)

            # Detect R-peaks
            _, rpeaks = nk.ecg_peaks(ecg_cleaned, sampling_rate=sampling_rate)

            # Compute heart rate
            heart_rate = nk.signal_rate(
                rpeaks,
                sampling_rate=sampling_rate,
                desired_length=len(ecg_signal)
            )

            # Compute HRV metrics
            hrv_time = nk.hrv_time(rpeaks, sampling_rate=sampling_rate)

            # Simulate EDA signal
            eda_signal = nk.eda_simulate(
                duration=duration,
                sampling_rate=sampling_rate,
                scr_number=3
            )

            # Process EDA
            eda_cleaned = nk.eda_clean(eda_signal, sampling_rate=sampling_rate)

            metrics = {
                'ecg_duration_s': duration,
                'sampling_rate_hz': sampling_rate,
                'n_rpeaks_detected': len(rpeaks['ECG_R_Peaks']),
                'mean_heart_rate_bpm': float(np.mean(heart_rate)),
                'hrv_rmssd_ms': float(hrv_time['HRV_RMSSD'].values[0]),
                'hrv_sdnn_ms': float(hrv_time['HRV_SDNN'].values[0]),
                'eda_processed': len(eda_cleaned) > 0
            }

            return BenchmarkResult(
                test_name="Basic Functionality",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except Exception as e:
            return BenchmarkResult(
                test_name="Basic Functionality",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )

    def test_integration_with_hbcm(self) -> BenchmarkResult:
        """Test NeuroKit2 physiological signal processing integrated with HBCM."""
        start = time.time()

        try:
            import neurokit2 as nk
            from src.coupling import HeartBrainCouplingModel
            from src.neural import FitzHughNagumo
            from src.cardiac import VanDerPolOscillator
            from src.coupling import CouplingParameters

            # Simulate ECG with NeuroKit2
            sampling_rate = 500
            duration = 30  # seconds

            # Simulate stressed heart rate (elevated, variable)
            ecg_signal = nk.ecg_simulate(
                duration=duration,
                sampling_rate=sampling_rate,
                heart_rate=85,  # Elevated HR
                heart_rate_std=10  # Variable HR
            )

            # Process ECG
            ecg_cleaned = nk.ecg_clean(ecg_signal, sampling_rate=sampling_rate)
            _, rpeaks = nk.ecg_peaks(ecg_cleaned, sampling_rate=sampling_rate)

            # Compute HRV metrics
            hrv_time = nk.hrv_time(rpeaks, sampling_rate=sampling_rate)
            hrv_freq = nk.hrv_frequency(rpeaks, sampling_rate=sampling_rate)

            # Extract key HRV metrics
            rmssd = float(hrv_time['HRV_RMSSD'].values[0])  # Root mean square of successive differences
            sdnn = float(hrv_time['HRV_SDNN'].values[0])  # Standard deviation of NN intervals
            lf_hf_ratio = float(hrv_freq['HRV_LFHF'].values[0])  # LF/HF ratio (autonomic balance)

            # Compute instantaneous heart rate
            heart_rate = nk.signal_rate(
                rpeaks,
                sampling_rate=sampling_rate,
                desired_length=len(ecg_signal)
            )
            mean_hr = np.mean(heart_rate)

            # Use HRV metrics to modulate HBCM parameters
            # Low HRV (low RMSSD) suggests stress → increase neural stimulus
            # High LF/HF ratio suggests sympathetic dominance → increase cardiac frequency

            # Normalize metrics for modulation
            rmssd_normalized = np.clip(rmssd / 50.0, 0.5, 1.5)  # Typical RMSSD: 20-100ms
            lf_hf_normalized = np.clip(lf_hf_ratio / 2.0, 0.8, 1.2)  # Typical LF/HF: 0.5-3.0

            # Map mean heart rate to cardiac omega
            # Normal resting HR: 60-100 bpm → omega: 0.8-1.5
            cardiac_omega = (mean_hr / 60.0) * 1.0

            # Create HBCM with HRV-modulated parameters
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(
                    stimulus_amplitude=0.5 / rmssd_normalized  # Low HRV → high stimulus
                ),
                cardiac_model=VanDerPolOscillator(
                    omega=cardiac_omega * lf_hf_normalized  # LF/HF modulates frequency
                ),
                coupling=CouplingParameters()
            )

            # Run HBCM simulation
            trajectory = hbcm.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, 10.0),
                dt=0.001
            )

            times, neural, cardiac = hbcm.extract_series(trajectory)

            # Analyze HBCM output
            neural_v = np.array([v for v, w in neural])
            cardiac_x = np.array([x for x, y in cardiac])

            # Compute HBCM metrics
            from scipy.signal import welch
            f_hbcm, psd_hbcm = welch(cardiac_x, fs=1.0/0.001, nperseg=1024)
            dominant_freq_idx = np.argmax(psd_hbcm[1:100]) + 1
            hbcm_dominant_freq = f_hbcm[dominant_freq_idx]

            metrics = {
                'nk_mean_hr_bpm': float(mean_hr),
                'nk_hrv_rmssd_ms': rmssd,
                'nk_hrv_sdnn_ms': sdnn,
                'nk_lf_hf_ratio': lf_hf_ratio,
                'hbcm_cardiac_omega': float(cardiac_omega),
                'hbcm_neural_stimulus': 0.5 / rmssd_normalized,
                'hbcm_dominant_freq_hz': float(hbcm_dominant_freq),
                'n_rpeaks': len(rpeaks['ECG_R_Peaks']),
                'integration_successful': True
            }

            return BenchmarkResult(
                test_name="HBCM Integration",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except Exception as e:
            return BenchmarkResult(
                test_name="HBCM Integration",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )

    def benchmark_ecg_processing(self) -> BenchmarkResult:
        """Benchmark ECG processing performance."""
        start = time.time()

        try:
            import neurokit2 as nk

            # Create test ECG signal
            sampling_rate = 1000
            duration = 10
            ecg_signal = nk.ecg_simulate(
                duration=duration,
                sampling_rate=sampling_rate,
                heart_rate=70
            )

            # Benchmark ECG cleaning
            def clean_ecg():
                return nk.ecg_clean(ecg_signal, sampling_rate=sampling_rate)

            clean_latency = PerformanceBenchmark.measure_latency(
                clean_ecg,
                iterations=20
            )

            # Benchmark R-peak detection
            ecg_cleaned = clean_ecg()

            def detect_peaks():
                return nk.ecg_peaks(ecg_cleaned, sampling_rate=sampling_rate)

            peak_latency = PerformanceBenchmark.measure_latency(
                detect_peaks,
                iterations=20
            )

            # Benchmark HRV computation
            _, rpeaks = detect_peaks()

            def compute_hrv():
                return nk.hrv_time(rpeaks, sampling_rate=sampling_rate)

            hrv_latency = PerformanceBenchmark.measure_latency(
                compute_hrv,
                iterations=20
            )

            metrics = {
                'ecg_clean_mean_ms': clean_latency['mean_ms'],
                'ecg_clean_p95_ms': clean_latency['p95_ms'],
                'peak_detect_mean_ms': peak_latency['mean_ms'],
                'peak_detect_p95_ms': peak_latency['p95_ms'],
                'hrv_compute_mean_ms': hrv_latency['mean_ms'],
                'hrv_compute_p95_ms': hrv_latency['p95_ms']
            }

            return BenchmarkResult(
                test_name="ECG Processing Benchmark",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except Exception as e:
            return BenchmarkResult(
                test_name="ECG Processing Benchmark",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )


def run_neurokit2_tests():
    """Run all NeuroKit2 validation tests."""
    tester = NeuroKit2ValidationTests()
    results = tester.run_all_tests()

    # Run benchmark
    print("\nRunning ECG processing benchmark...", end=' ')
    benchmark = tester.benchmark_ecg_processing()
    results.append(benchmark)
    print(f"[{benchmark.status.upper()}] ({benchmark.execution_time:.3f}s)")

    if benchmark.status == 'pass':
        print(f"  ECG cleaning: {benchmark.metrics.get('ecg_clean_mean_ms', 0):.2f}ms")
        print(f"  Peak detection: {benchmark.metrics.get('peak_detect_mean_ms', 0):.2f}ms")
        print(f"  HRV computation: {benchmark.metrics.get('hrv_compute_mean_ms', 0):.2f}ms")

    # Print summary
    summary = tester.get_summary()
    print(f"\n{'='*70}")
    print("NeuroKit2 Validation Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Success Rate: {summary['success_rate']:.1f}%")
    print(f"{'='*70}\n")

    return results


if __name__ == '__main__':
    run_neurokit2_tests()
