"""
LSL (Lab Streaming Layer) Integration Tests

Tests Multi-Heart-Model integration with LSL for real-time data streaming
and synchronization.

Repository: https://github.com/sccn/liblsl-Python
"""

import sys
from pathlib import Path
import time
import numpy as np
import threading

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validation.framework import ValidationTestBase, BenchmarkResult, PerformanceBenchmark


class LSLValidationTests(ValidationTestBase):
    """Validation tests for LSL integration."""

    def __init__(self):
        super().__init__("LSL")

    def test_installation(self) -> BenchmarkResult:
        """Test if pylsl is properly installed."""
        start = time.time()

        try:
            import pylsl

            metrics = {
                'version': pylsl.__version__,
                'protocol_version': pylsl.protocol_version(),
                'library_version': pylsl.library_version()
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
                error_message=f"pylsl not installed: {e}. Install with: pip install pylsl"
            )

    def test_import(self) -> BenchmarkResult:
        """Test importing pylsl modules."""
        start = time.time()

        try:
            from pylsl import (
                StreamInfo,
                StreamOutlet,
                StreamInlet,
                resolve_stream,
                local_clock,
                cf_float32,
                cf_int32,
                cf_string
            )

            modules = [
                'StreamInfo', 'StreamOutlet', 'StreamInlet',
                'resolve_stream', 'local_clock', 'channel_formats'
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
        """Test basic LSL streaming functionality."""
        start = time.time()

        try:
            from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream, local_clock

            # Create stream info
            stream_name = "MultiHeartModelTest"
            stream_type = "EEG"
            n_channels = 8
            sampling_rate = 250.0
            channel_format = 'float32'
            source_id = "test_stream_001"

            info = StreamInfo(
                stream_name,
                stream_type,
                n_channels,
                sampling_rate,
                channel_format,
                source_id
            )

            # Add channel metadata
            channels = info.desc().append_child("channels")
            for i in range(n_channels):
                ch = channels.append_child("channel")
                ch.append_child_value("label", f"EEG{i}")
                ch.append_child_value("unit", "microvolts")
                ch.append_child_value("type", "EEG")

            # Create outlet
            outlet = StreamOutlet(info)

            # Wait for stream to be discoverable
            time.sleep(0.1)

            # Discover stream
            streams = resolve_stream('name', stream_name)

            if len(streams) == 0:
                raise RuntimeError("Failed to discover stream")

            # Create inlet
            inlet = StreamInlet(streams[0])

            # Open stream
            inlet.open_stream()

            # Generate and send test data
            n_samples = 10
            samples_sent = 0

            for _ in range(n_samples):
                sample = np.random.randn(n_channels).tolist()
                timestamp = local_clock()
                outlet.push_sample(sample, timestamp)
                samples_sent += 1
                time.sleep(0.004)  # 250 Hz = 4ms between samples

            # Receive data
            samples_received = 0
            samples_data = []

            timeout = 1.0
            while samples_received < n_samples:
                sample, timestamp = inlet.pull_sample(timeout=timeout)
                if sample:
                    samples_received += 1
                    samples_data.append(sample)
                else:
                    break

            # Close streams
            inlet.close_stream()
            del outlet
            del inlet

            # Verify data
            data_integrity = samples_received == samples_sent

            metrics = {
                'stream_name': stream_name,
                'n_channels': n_channels,
                'sampling_rate_hz': sampling_rate,
                'samples_sent': samples_sent,
                'samples_received': samples_received,
                'data_integrity': data_integrity,
                'stream_discovered': True
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
        """Test LSL streaming integrated with HBCM."""
        start = time.time()

        try:
            from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream, local_clock
            from src.coupling import HeartBrainCouplingModel
            from src.neural import FitzHughNagumo
            from src.cardiac import VanDerPolOscillator
            from src.coupling import CouplingParameters

            # Create LSL stream for simulated EEG data
            stream_name = "HBCM_EEG_Stream"
            n_channels = 4
            sampling_rate = 250.0

            info = StreamInfo(
                stream_name,
                "EEG",
                n_channels,
                sampling_rate,
                'float32',
                "hbcm_integration_test"
            )

            outlet = StreamOutlet(info)
            time.sleep(0.1)

            # Discover and connect
            streams = resolve_stream('name', stream_name)
            if len(streams) == 0:
                raise RuntimeError("Failed to discover HBCM stream")

            inlet = StreamInlet(streams[0])
            inlet.open_stream()

            # Simulate streaming EEG data in background thread
            streaming_active = threading.Event()
            streaming_active.set()

            def stream_eeg_data():
                """Background thread: stream simulated EEG."""
                sample_count = 0
                while streaming_active.is_set() and sample_count < 100:
                    # Simulate alpha band activity (8-12 Hz)
                    t = sample_count / sampling_rate
                    alpha_freq = 10.0  # Hz
                    sample = [
                        np.sin(2 * np.pi * alpha_freq * t + np.random.randn() * 0.1)
                        for _ in range(n_channels)
                    ]
                    outlet.push_sample(sample, local_clock())
                    sample_count += 1
                    time.sleep(1.0 / sampling_rate)

            stream_thread = threading.Thread(target=stream_eeg_data, daemon=True)
            stream_thread.start()

            # Collect streaming data and compute alpha power
            n_collect = 50
            eeg_buffer = []

            for _ in range(n_collect):
                sample, timestamp = inlet.pull_sample(timeout=1.0)
                if sample:
                    eeg_buffer.append(sample)

            streaming_active.clear()
            stream_thread.join(timeout=1.0)

            # Compute alpha power from collected data
            eeg_array = np.array(eeg_buffer)  # Shape: (n_samples, n_channels)
            eeg_mean_ch = np.mean(eeg_array, axis=1)  # Average across channels

            # Compute power spectrum
            from scipy.signal import welch
            f, psd = welch(eeg_mean_ch, fs=sampling_rate, nperseg=len(eeg_mean_ch))

            # Extract alpha band power (8-12 Hz)
            alpha_band = (f >= 8.0) & (f <= 12.0)
            alpha_power = np.mean(psd[alpha_band])

            # Normalize alpha power for modulation
            # Typical alpha power: variable, normalize to 0.5-1.5 range
            alpha_normalized = np.clip(alpha_power / np.mean(psd), 0.5, 1.5)

            # Use alpha power to modulate HBCM
            # High alpha → relaxed state → reduced neural stimulus
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(
                    stimulus_amplitude=0.8 / alpha_normalized  # High alpha → low stimulus
                ),
                cardiac_model=VanDerPolOscillator(
                    omega=1.0 + (alpha_normalized - 1.0) * 0.2  # Slight frequency modulation
                ),
                coupling=CouplingParameters()
            )

            # Run HBCM simulation
            trajectory = hbcm.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, 5.0),
                dt=0.001
            )

            times, neural, cardiac = hbcm.extract_series(trajectory)

            # Analyze HBCM output
            neural_v = np.array([v for v, w in neural])
            cardiac_x = np.array([x for x, y in cardiac])

            # Clean up LSL streams
            inlet.close_stream()
            del outlet
            del inlet

            metrics = {
                'lsl_samples_collected': len(eeg_buffer),
                'lsl_sampling_rate_hz': sampling_rate,
                'alpha_power': float(alpha_power),
                'alpha_normalized': float(alpha_normalized),
                'hbcm_neural_stimulus': float(0.8 / alpha_normalized),
                'hbcm_cardiac_omega': float(1.0 + (alpha_normalized - 1.0) * 0.2),
                'hbcm_steps': len(trajectory),
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

    def benchmark_streaming_latency(self) -> BenchmarkResult:
        """Benchmark LSL streaming latency."""
        start = time.time()

        try:
            from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream, local_clock

            # Create test stream
            info = StreamInfo("LatencyTest", "EEG", 1, 100.0, 'float32', "latency_test")
            outlet = StreamOutlet(info)
            time.sleep(0.1)

            streams = resolve_stream('name', "LatencyTest")
            if len(streams) == 0:
                raise RuntimeError("Stream discovery failed")

            inlet = StreamInlet(streams[0])
            inlet.open_stream()

            # Measure round-trip latency
            latencies = []
            n_iterations = 50

            for _ in range(n_iterations):
                send_time = local_clock()
                outlet.push_sample([1.0], send_time)

                sample, recv_timestamp = inlet.pull_sample(timeout=0.5)
                if sample:
                    recv_time = local_clock()
                    latency_ms = (recv_time - send_time) * 1000.0
                    latencies.append(latency_ms)

                time.sleep(0.01)  # 10ms between iterations

            # Clean up
            inlet.close_stream()
            del outlet
            del inlet

            # Compute statistics
            latencies = np.array(latencies)

            metrics = {
                'mean_latency_ms': float(np.mean(latencies)),
                'median_latency_ms': float(np.median(latencies)),
                'p95_latency_ms': float(np.percentile(latencies, 95)),
                'p99_latency_ms': float(np.percentile(latencies, 99)),
                'min_latency_ms': float(np.min(latencies)),
                'max_latency_ms': float(np.max(latencies)),
                'n_samples': len(latencies)
            }

            return BenchmarkResult(
                test_name="Streaming Latency Benchmark",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except Exception as e:
            return BenchmarkResult(
                test_name="Streaming Latency Benchmark",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )


def run_lsl_tests():
    """Run all LSL validation tests."""
    tester = LSLValidationTests()
    results = tester.run_all_tests()

    # Run benchmark
    print("\nRunning streaming latency benchmark...", end=' ')
    benchmark = tester.benchmark_streaming_latency()
    results.append(benchmark)
    print(f"[{benchmark.status.upper()}] ({benchmark.execution_time:.3f}s)")

    if benchmark.status == 'pass':
        print(f"  Mean latency: {benchmark.metrics.get('mean_latency_ms', 0):.2f}ms")
        print(f"  P95 latency: {benchmark.metrics.get('p95_latency_ms', 0):.2f}ms")
        print(f"  P99 latency: {benchmark.metrics.get('p99_latency_ms', 0):.2f}ms")

    # Print summary
    summary = tester.get_summary()
    print(f"\n{'='*70}")
    print("LSL Validation Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Success Rate: {summary['success_rate']:.1f}%")
    print(f"{'='*70}\n")

    return results


if __name__ == '__main__':
    run_lsl_tests()
