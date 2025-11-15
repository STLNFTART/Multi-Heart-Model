"""
NeuroDSP Integration Tests

Tests Multi-Heart-Model integration with NeuroDSP for neural signal processing
and oscillation analysis.

Repository: https://github.com/neurodsp-tools/neurodsp
"""

import sys
from pathlib import Path
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validation.framework import ValidationTestBase, BenchmarkResult, PerformanceBenchmark


class NeuroDSPValidationTests(ValidationTestBase):
    """Validation tests for NeuroDSP integration."""

    def __init__(self):
        super().__init__("NeuroDSP")

    def test_installation(self) -> BenchmarkResult:
        """Test if NeuroDSP is properly installed."""
        start = time.time()

        try:
            import neurodsp

            metrics = {
                'version': neurodsp.__version__
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
                error_message=f"NeuroDSP not installed: {e}. Install with: pip install neurodsp"
            )

    def test_import(self) -> BenchmarkResult:
        """Test importing NeuroDSP modules."""
        start = time.time()

        try:
            from neurodsp.filt import filter_signal
            from neurodsp.spectral import compute_spectrum
            from neurodsp.timefrequency import compute_wavelet_transform
            from neurodsp.rhythm import detect_bursts_dual_threshold
            from neurodsp.sim import sim_combined

            modules = [
                'filt', 'spectral', 'timefrequency', 'rhythm', 'sim'
            ]

            return BenchmarkResult(
                test_name="Import Test",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics={'modules_imported': len(modules)}
            )

        except ImportError as e:
            return BenchmarkResult(
                test_name="Import Test",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )

    def test_basic_functionality(self) -> BenchmarkResult:
        """Test basic NeuroDSP functionality."""
        start = time.time()

        try:
            from neurodsp.sim import sim_oscillation, sim_combined
            from neurodsp.filt import filter_signal
            from neurodsp.spectral import compute_spectrum
            from neurodsp.rhythm import detect_bursts_dual_threshold

            # Simulation parameters
            fs = 500  # Sampling rate
            n_seconds = 2

            # Simulate oscillatory signal (alpha band)
            sig_osc = sim_oscillation(n_seconds, fs, freq=10)

            # Filter signal
            sig_filt = filter_signal(sig_osc, fs, 'bandpass', (8, 12))

            # Compute power spectrum
            freqs, powers = compute_spectrum(sig_osc, fs, method='welch')

            # Detect bursts
            is_burst = detect_bursts_dual_threshold(sig_filt, fs, (8, 12),
                                                    avg_type='median')

            metrics = {
                'signal_duration_s': n_seconds,
                'sampling_rate_hz': fs,
                'n_samples': len(sig_osc),
                'n_bursts_detected': int(np.sum(np.diff(is_burst.astype(int)) == 1)),
                'spectrum_computed': len(freqs) > 0,
                'filtering_successful': np.any(sig_filt != sig_osc)
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
        """Test NeuroDSP oscillation analysis integrated with HBCM."""
        start = time.time()

        try:
            from neurodsp.sim import sim_oscillation
            from neurodsp.spectral import compute_spectrum
            from neurodsp.rhythm import detect_bursts_dual_threshold
            from neurodsp.filt import filter_signal
            from src.coupling import HeartBrainCouplingModel
            from src.neural import FitzHughNagumo
            from src.cardiac import VanDerPolOscillator
            from src.coupling import CouplingParameters

            # Simulate EEG-like signal with NeuroDSP
            fs = 250
            n_seconds = 10

            eeg_signal = sim_oscillation(n_seconds, fs, freq=10, variance=0.5)

            # Detect oscillatory bursts
            eeg_filt = filter_signal(eeg_signal, fs, 'bandpass', (8, 12))
            bursts = detect_bursts_dual_threshold(eeg_filt, fs, (8, 12))

            # Compute burst rate (bursts per second)
            burst_starts = np.where(np.diff(bursts.astype(int)) == 1)[0]
            burst_rate = len(burst_starts) / n_seconds

            # Use burst rate to modulate HBCM cardiac frequency
            # Normal heart rate: ~1 Hz, modulate based on burst rate
            cardiac_omega = 1.0 + (burst_rate - 1.0) * 0.2  # Slight modulation

            # Run HBCM
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(),
                cardiac_model=VanDerPolOscillator(omega=cardiac_omega),
                coupling=CouplingParameters()
            )

            trajectory = hbcm.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, 5.0),
                dt=0.001
            )

            times, neural, cardiac = hbcm.extract_series(trajectory)

            # Extract cardiac oscillation frequency from HBCM
            cardiac_x = np.array([x for x, y in cardiac])

            # Compute power spectrum of HBCM cardiac output
            from scipy.signal import welch
            f_cardiac, psd_cardiac = welch(cardiac_x, fs=1.0/0.001, nperseg=1024)

            # Find dominant frequency
            dominant_freq_idx = np.argmax(psd_cardiac[1:100]) + 1  # Avoid DC
            dominant_freq = f_cardiac[dominant_freq_idx]

            metrics = {
                'neurodsp_burst_rate': float(burst_rate),
                'hbcm_cardiac_omega': float(cardiac_omega),
                'hbcm_dominant_freq': float(dominant_freq),
                'n_bursts_detected': len(burst_starts),
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

    def benchmark_oscillation_detection(self) -> BenchmarkResult:
        """Benchmark oscillation detection performance."""
        start = time.time()

        try:
            from neurodsp.sim import sim_oscillation
            from neurodsp.rhythm import detect_bursts_dual_threshold
            from neurodsp.filt import filter_signal

            # Create test signal
            fs = 500
            n_seconds = 10
            sig = sim_oscillation(n_seconds, fs, freq=10, variance=0.5)
            sig_filt = filter_signal(sig, fs, 'bandpass', (8, 12))

            # Benchmark burst detection
            def detect_bursts():
                return detect_bursts_dual_threshold(sig_filt, fs, (8, 12))

            latency = PerformanceBenchmark.measure_latency(
                detect_bursts,
                iterations=50
            )

            # Benchmark spectral analysis
            from neurodsp.spectral import compute_spectrum

            def compute_spec():
                return compute_spectrum(sig, fs, method='welch')

            spec_latency = PerformanceBenchmark.measure_latency(
                compute_spec,
                iterations=50
            )

            metrics = {
                'burst_detection_mean_ms': latency['mean_ms'],
                'burst_detection_p95_ms': latency['p95_ms'],
                'spectrum_computation_mean_ms': spec_latency['mean_ms'],
                'spectrum_computation_p95_ms': spec_latency['p95_ms']
            }

            return BenchmarkResult(
                test_name="Oscillation Detection Benchmark",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except Exception as e:
            return BenchmarkResult(
                test_name="Oscillation Detection Benchmark",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )


def run_neurodsp_tests():
    """Run all NeuroDSP validation tests."""
    tester = NeuroDSPValidationTests()
    results = tester.run_all_tests()

    # Run benchmark
    print("\nRunning oscillation detection benchmark...", end=' ')
    benchmark = tester.benchmark_oscillation_detection()
    results.append(benchmark)
    print(f"[{benchmark.status.upper()}] ({benchmark.execution_time:.3f}s)")

    if benchmark.status == 'pass':
        print(f"  Burst detection: {benchmark.metrics.get('burst_detection_mean_ms', 0):.2f}ms")
        print(f"  Spectrum: {benchmark.metrics.get('spectrum_computation_mean_ms', 0):.2f}ms")

    # Print summary
    summary = tester.get_summary()
    print(f"\n{'='*70}")
    print("NeuroDSP Validation Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Success Rate: {summary['success_rate']:.1f}%")
    print(f"{'='*70}\n")

    return results


if __name__ == '__main__':
    run_neurodsp_tests()
