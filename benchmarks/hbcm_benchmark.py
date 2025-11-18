"""
HBCM Simulation Performance Benchmark.

Measures:
- Simulation step latency
- Throughput (simulated seconds per wall-clock second)
- Memory usage during simulation
- Scaling with different parameters

Target: <1ms per step for real-time performance (1000 Hz control loop)
"""

import sys
import time
import statistics
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, '/home/user/Multi-Heart-Model')

from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters
from src.monitoring import LatencyProfiler, MetricsCollector


@dataclass
class BenchmarkResult:
    """Result from a benchmark run."""

    test_name: str
    duration_s: float
    iterations: int
    mean_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    throughput_ops_per_sec: float
    memory_mb: float = 0.0
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'test_name': self.test_name,
            'duration_s': self.duration_s,
            'iterations': self.iterations,
            'mean_latency_ms': self.mean_latency_ms,
            'median_latency_ms': self.median_latency_ms,
            'p95_latency_ms': self.p95_latency_ms,
            'p99_latency_ms': self.p99_latency_ms,
            'min_latency_ms': self.min_latency_ms,
            'max_latency_ms': self.max_latency_ms,
            'throughput_ops_per_sec': self.throughput_ops_per_sec,
            'memory_mb': self.memory_mb,
            'metadata': self.metadata or {}
        }

    def print_summary(self) -> None:
        """Print formatted summary."""
        print(f"\n{'=' * 70}")
        print(f"Benchmark: {self.test_name}")
        print(f"{'=' * 70}")
        print(f"Iterations:     {self.iterations:,}")
        print(f"Duration:       {self.duration_s:.3f} s")
        print(f"Throughput:     {self.throughput_ops_per_sec:,.0f} ops/sec")
        print(f"\nLatency Statistics (ms):")
        print(f"  Min:          {self.min_latency_ms:.6f}")
        print(f"  Mean:         {self.mean_latency_ms:.6f}")
        print(f"  Median:       {self.median_latency_ms:.6f}")
        print(f"  P95:          {self.p95_latency_ms:.6f}")
        print(f"  P99:          {self.p99_latency_ms:.6f}")
        print(f"  Max:          {self.max_latency_ms:.6f}")

        if self.memory_mb > 0:
            print(f"\nMemory Usage:   {self.memory_mb:.2f} MB")

        if self.metadata:
            print(f"\nMetadata:")
            for key, value in self.metadata.items():
                print(f"  {key}: {value}")

        # Performance assessment
        print(f"\n{'Performance Assessment:':}")
        if self.p99_latency_ms < 1.0:
            print(f"  ✅ EXCELLENT - Suitable for 1000 Hz control loop (P99 < 1ms)")
        elif self.p99_latency_ms < 10.0:
            print(f"  ✅ GOOD - Suitable for 100 Hz control loop (P99 < 10ms)")
        elif self.p99_latency_ms < 100.0:
            print(f"  ⚠️  ACCEPTABLE - Suitable for 10 Hz monitoring (P99 < 100ms)")
        else:
            print(f"  ❌ NEEDS OPTIMIZATION - Too slow for real-time control (P99 > 100ms)")


class HBCMBenchmark:
    """
    Benchmark suite for Heart-Brain Coupling Model performance.

    Tests:
    1. Single step latency
    2. Short simulation (100 steps)
    3. Long simulation (10,000 steps)
    4. High-frequency simulation (100,000 steps)
    5. Parameter sensitivity
    6. Memory usage scaling
    """

    def __init__(self):
        """Initialize benchmark suite."""
        self.results: List[BenchmarkResult] = []

    def benchmark_single_step(self, iterations: int = 10000) -> BenchmarkResult:
        """
        Benchmark single simulation step.

        Args:
            iterations: Number of iterations

        Returns:
            BenchmarkResult
        """
        print(f"\n[1/6] Benchmarking single HBCM step ({iterations:,} iterations)...")

        # Create model
        hbcm = HeartBrainCouplingModel(
            neural_model=FitzHughNagumo(),
            cardiac_model=VanDerPolOscillator(),
            coupling=CouplingParameters()
        )

        # Initial state
        state = (0.0, 0.0, 1.0, 0.0)
        dt = 0.001

        # Warm-up
        for _ in range(100):
            state = hbcm.step(0.0, state, dt)

        # Benchmark
        latencies = []
        start_time = time.perf_counter()

        for i in range(iterations):
            step_start = time.perf_counter_ns()
            state = hbcm.step(i * dt, state, dt)
            step_end = time.perf_counter_ns()

            latencies.append((step_end - step_start) / 1_000_000.0)  # Convert to ms

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Calculate statistics
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        result = BenchmarkResult(
            test_name="HBCM Single Step",
            duration_s=duration,
            iterations=iterations,
            mean_latency_ms=statistics.mean(latencies),
            median_latency_ms=latencies_sorted[n // 2],
            p95_latency_ms=latencies_sorted[int(n * 0.95)],
            p99_latency_ms=latencies_sorted[int(n * 0.99)],
            min_latency_ms=latencies_sorted[0],
            max_latency_ms=latencies_sorted[-1],
            throughput_ops_per_sec=iterations / duration,
            metadata={'dt': dt, 'state_size': 4}
        )

        self.results.append(result)
        return result

    def benchmark_short_simulation(self, steps: int = 100) -> BenchmarkResult:
        """
        Benchmark short simulation run.

        Args:
            steps: Number of simulation steps

        Returns:
            BenchmarkResult
        """
        print(f"\n[2/6] Benchmarking short simulation ({steps} steps)...")

        iterations = 100
        latencies = []

        for _ in range(iterations):
            # Create fresh model each time
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(),
                cardiac_model=VanDerPolOscillator(),
                coupling=CouplingParameters()
            )

            sim_start = time.perf_counter_ns()

            trajectory = hbcm.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, steps * 0.001),
                dt=0.001
            )

            sim_end = time.perf_counter_ns()
            latencies.append((sim_end - sim_start) / 1_000_000.0)

        # Calculate statistics
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)
        total_duration = sum(latencies) / 1000.0  # Convert to seconds

        result = BenchmarkResult(
            test_name=f"HBCM Short Simulation ({steps} steps)",
            duration_s=total_duration,
            iterations=iterations,
            mean_latency_ms=statistics.mean(latencies),
            median_latency_ms=latencies_sorted[n // 2],
            p95_latency_ms=latencies_sorted[int(n * 0.95)],
            p99_latency_ms=latencies_sorted[int(n * 0.99)],
            min_latency_ms=latencies_sorted[0],
            max_latency_ms=latencies_sorted[-1],
            throughput_ops_per_sec=iterations / total_duration,
            metadata={'steps': steps, 'simulated_time_s': steps * 0.001}
        )

        self.results.append(result)
        return result

    def benchmark_long_simulation(self, steps: int = 10000) -> BenchmarkResult:
        """
        Benchmark long simulation run.

        Args:
            steps: Number of simulation steps

        Returns:
            BenchmarkResult
        """
        print(f"\n[3/6] Benchmarking long simulation ({steps:,} steps)...")

        iterations = 10
        latencies = []

        for i in range(iterations):
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(),
                cardiac_model=VanDerPolOscillator(),
                coupling=CouplingParameters()
            )

            sim_start = time.perf_counter_ns()

            trajectory = hbcm.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, steps * 0.001),
                dt=0.001
            )

            sim_end = time.perf_counter_ns()
            latencies.append((sim_end - sim_start) / 1_000_000.0)

            print(f"  Iteration {i+1}/{iterations}: {latencies[-1]:.2f} ms")

        # Calculate statistics
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)
        total_duration = sum(latencies) / 1000.0

        result = BenchmarkResult(
            test_name=f"HBCM Long Simulation ({steps:,} steps)",
            duration_s=total_duration,
            iterations=iterations,
            mean_latency_ms=statistics.mean(latencies),
            median_latency_ms=latencies_sorted[n // 2],
            p95_latency_ms=latencies_sorted[int(n * 0.95)],
            p99_latency_ms=latencies_sorted[int(n * 0.99)],
            min_latency_ms=latencies_sorted[0],
            max_latency_ms=latencies_sorted[-1],
            throughput_ops_per_sec=iterations / total_duration,
            metadata={'steps': steps, 'simulated_time_s': steps * 0.001}
        )

        self.results.append(result)
        return result

    def benchmark_realtime_capability(self, target_hz: int = 1000,
                                     duration_s: float = 10.0) -> BenchmarkResult:
        """
        Benchmark real-time control loop capability.

        Measures if system can maintain target frequency.

        Args:
            target_hz: Target frequency (Hz)
            duration_s: Test duration (seconds)

        Returns:
            BenchmarkResult
        """
        print(f"\n[4/6] Benchmarking real-time capability ({target_hz} Hz for {duration_s}s)...")

        hbcm = HeartBrainCouplingModel(
            neural_model=FitzHughNagumo(),
            cardiac_model=VanDerPolOscillator(),
            coupling=CouplingParameters()
        )

        state = (0.0, 0.0, 1.0, 0.0)
        dt = 1.0 / target_hz

        iterations = int(target_hz * duration_s)
        latencies = []

        start_time = time.perf_counter()

        for i in range(iterations):
            step_start = time.perf_counter_ns()
            state = hbcm.step(i * dt, state, dt)
            step_end = time.perf_counter_ns()

            latencies.append((step_end - step_start) / 1_000_000.0)

        end_time = time.perf_counter()
        actual_duration = end_time - start_time

        # Calculate statistics
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        # Real-time factor (simulated time / wall-clock time)
        simulated_time = iterations * dt
        realtime_factor = simulated_time / actual_duration

        result = BenchmarkResult(
            test_name=f"Real-Time Capability ({target_hz} Hz)",
            duration_s=actual_duration,
            iterations=iterations,
            mean_latency_ms=statistics.mean(latencies),
            median_latency_ms=latencies_sorted[n // 2],
            p95_latency_ms=latencies_sorted[int(n * 0.95)],
            p99_latency_ms=latencies_sorted[int(n * 0.99)],
            min_latency_ms=latencies_sorted[0],
            max_latency_ms=latencies_sorted[-1],
            throughput_ops_per_sec=iterations / actual_duration,
            metadata={
                'target_hz': target_hz,
                'target_dt_ms': dt * 1000,
                'simulated_time_s': simulated_time,
                'realtime_factor': realtime_factor,
                'can_run_realtime': realtime_factor >= 1.0
            }
        )

        self.results.append(result)
        return result

    def benchmark_parameter_scaling(self) -> List[BenchmarkResult]:
        """
        Benchmark performance scaling with different parameters.

        Tests different timesteps and coupling strengths.

        Returns:
            List of BenchmarkResults
        """
        print(f"\n[5/6] Benchmarking parameter scaling...")

        timesteps = [0.0001, 0.0005, 0.001, 0.005, 0.01]
        results = []

        for dt in timesteps:
            print(f"  Testing dt = {dt}s...")

            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(),
                cardiac_model=VanDerPolOscillator(),
                coupling=CouplingParameters()
            )

            state = (0.0, 0.0, 1.0, 0.0)
            iterations = 1000
            latencies = []

            for i in range(iterations):
                step_start = time.perf_counter_ns()
                state = hbcm.step(i * dt, state, dt)
                step_end = time.perf_counter_ns()

                latencies.append((step_end - step_start) / 1_000_000.0)

            latencies_sorted = sorted(latencies)
            n = len(latencies_sorted)
            duration = sum(latencies) / 1000.0

            result = BenchmarkResult(
                test_name=f"Parameter Scaling (dt={dt}s)",
                duration_s=duration,
                iterations=iterations,
                mean_latency_ms=statistics.mean(latencies),
                median_latency_ms=latencies_sorted[n // 2],
                p95_latency_ms=latencies_sorted[int(n * 0.95)],
                p99_latency_ms=latencies_sorted[int(n * 0.99)],
                min_latency_ms=latencies_sorted[0],
                max_latency_ms=latencies_sorted[-1],
                throughput_ops_per_sec=iterations / duration,
                metadata={'dt': dt}
            )

            results.append(result)
            self.results.append(result)

        return results

    def benchmark_memory_usage(self) -> BenchmarkResult:
        """
        Benchmark memory usage during simulation.

        Returns:
            BenchmarkResult
        """
        print(f"\n[6/6] Benchmarking memory usage...")

        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())

            # Get baseline memory
            baseline_mb = process.memory_info().rss / 1024 / 1024

            # Create model
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(),
                cardiac_model=VanDerPolOscillator(),
                coupling=CouplingParameters()
            )

            # Run simulation
            steps = 100000
            start_time = time.perf_counter()

            trajectory = hbcm.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, steps * 0.001),
                dt=0.001
            )

            end_time = time.perf_counter()
            duration = end_time - start_time

            # Get peak memory
            peak_mb = process.memory_info().rss / 1024 / 1024
            memory_delta = peak_mb - baseline_mb

            result = BenchmarkResult(
                test_name=f"Memory Usage ({steps:,} steps)",
                duration_s=duration,
                iterations=1,
                mean_latency_ms=duration * 1000,
                median_latency_ms=duration * 1000,
                p95_latency_ms=duration * 1000,
                p99_latency_ms=duration * 1000,
                min_latency_ms=duration * 1000,
                max_latency_ms=duration * 1000,
                throughput_ops_per_sec=1.0 / duration,
                memory_mb=memory_delta,
                metadata={
                    'steps': steps,
                    'baseline_mb': baseline_mb,
                    'peak_mb': peak_mb,
                    'trajectory_points': len(trajectory)
                }
            )

            self.results.append(result)
            return result

        except ImportError:
            print("  ⚠️  psutil not available, skipping memory benchmark")
            return None

    def run_all(self) -> List[BenchmarkResult]:
        """
        Run all benchmarks.

        Returns:
            List of all benchmark results
        """
        print("\n" + "=" * 70)
        print("HBCM PERFORMANCE BENCHMARK SUITE")
        print("=" * 70)

        self.results.clear()

        # Run benchmarks
        self.benchmark_single_step(iterations=10000)
        self.benchmark_short_simulation(steps=100)
        self.benchmark_long_simulation(steps=10000)
        self.benchmark_realtime_capability(target_hz=1000, duration_s=10.0)
        self.benchmark_parameter_scaling()
        self.benchmark_memory_usage()

        # Print summary
        print("\n" + "=" * 70)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 70)

        for result in self.results:
            result.print_summary()

        return self.results


def main():
    """Run HBCM benchmarks."""
    benchmark = HBCMBenchmark()
    results = benchmark.run_all()

    # Save results
    import json
    from datetime import datetime

    output = {
        'timestamp': datetime.now().isoformat(),
        'benchmark_suite': 'HBCM Performance',
        'results': [r.to_dict() for r in results]
    }

    output_file = f"/home/user/Multi-Heart-Model/benchmarks/results/hbcm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")


if __name__ == '__main__':
    main()
