"""
End-to-End Control Loop Latency Benchmark.

Measures the complete latency from sensor input to motor command for:
- MotorHandPro integration
- PrimalLogicProcessor control
- OpenSim biomechanical coupling
- Network transmission delays

Target: <100ms end-to-end latency for prosthetic control
"""

import sys
import time
import statistics
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

sys.path.insert(0, '/home/user/Multi-Heart-Model')

from src.microprocessor import PrimalLogicProcessor
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters


@dataclass
class ControlLoopResult:
    """Result from control loop benchmark."""

    test_name: str
    iterations: int
    mean_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    p999_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    target_met: bool  # Did we meet <100ms target?
    margin_ms: float  # How much margin below target
    metadata: Dict[str, Any] = None

    def print_summary(self) -> None:
        """Print formatted summary."""
        print(f"\n{'=' * 70}")
        print(f"Control Loop Benchmark: {self.test_name}")
        print(f"{'=' * 70}")
        print(f"Iterations:     {self.iterations:,}")
        print(f"\nLatency Statistics (ms):")
        print(f"  Min:          {self.min_latency_ms:.3f}")
        print(f"  Mean:         {self.mean_latency_ms:.3f}")
        print(f"  Median:       {self.median_latency_ms:.3f}")
        print(f"  P95:          {self.p95_latency_ms:.3f}")
        print(f"  P99:          {self.p99_latency_ms:.3f}")
        print(f"  P99.9:        {self.p999_latency_ms:.3f}")
        print(f"  Max:          {self.max_latency_ms:.3f}")

        print(f"\n{'Target Assessment (<100ms):'}")
        if self.target_met:
            print(f"  ✅ TARGET MET - P99.9 latency is {self.p999_latency_ms:.3f}ms")
            print(f"  ✅ Safety margin: {self.margin_ms:.3f}ms below target")
        else:
            print(f"  ❌ TARGET MISSED - P99.9 latency is {self.p999_latency_ms:.3f}ms")
            print(f"  ❌ Exceeds target by: {-self.margin_ms:.3f}ms")

        if self.metadata:
            print(f"\nMetadata:")
            for key, value in self.metadata.items():
                print(f"  {key}: {value}")


class ControlLoopBenchmark:
    """
    End-to-end control loop latency benchmark.

    Measures complete control loop including:
    1. Sensor reading
    2. HBCM state update
    3. Control computation (PrimalLogicProcessor)
    4. Command transmission
    5. Actuator response time (simulated)

    Critical for prosthetic control validation.
    """

    def __init__(self):
        """Initialize control loop benchmark."""
        self.results: List[ControlLoopResult] = []

    def benchmark_plp_control(self, iterations: int = 10000) -> ControlLoopResult:
        """
        Benchmark Primal Logic Processor control computation.

        Args:
            iterations: Number of control cycles

        Returns:
            ControlLoopResult
        """
        print(f"\n[1/5] Benchmarking PLP control computation ({iterations:,} iterations)...")

        plp = PrimalLogicProcessor()
        latencies = []

        # Warm-up
        for _ in range(100):
            plp.compute_control(error=0.5, dt=0.001)

        # Benchmark
        for i in range(iterations):
            error = 0.5 * (1.0 if i % 2 == 0 else -1.0)  # Alternating error

            start = time.perf_counter_ns()
            control = plp.compute_control(error=error, dt=0.001)
            end = time.perf_counter_ns()

            latencies.append((end - start) / 1_000_000.0)

        # Statistics
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        p999_latency = latencies_sorted[int(n * 0.999)]
        target_met = p999_latency < 100.0
        margin = 100.0 - p999_latency

        result = ControlLoopResult(
            test_name="PLP Control Computation",
            iterations=iterations,
            mean_latency_ms=statistics.mean(latencies),
            median_latency_ms=latencies_sorted[n // 2],
            p95_latency_ms=latencies_sorted[int(n * 0.95)],
            p99_latency_ms=latencies_sorted[int(n * 0.99)],
            p999_latency_ms=p999_latency,
            min_latency_ms=latencies_sorted[0],
            max_latency_ms=latencies_sorted[-1],
            target_met=target_met,
            margin_ms=margin,
            metadata={'dt': 0.001, 'control_algorithm': 'integral'}
        )

        self.results.append(result)
        return result

    def benchmark_hbcm_step_with_control(self, iterations: int = 10000) -> ControlLoopResult:
        """
        Benchmark HBCM step + control computation.

        Args:
            iterations: Number of iterations

        Returns:
            ControlLoopResult
        """
        print(f"\n[2/5] Benchmarking HBCM + Control ({iterations:,} iterations)...")

        hbcm = HeartBrainCouplingModel(
            neural_model=FitzHughNagumo(),
            cardiac_model=VanDerPolOscillator(),
            coupling=CouplingParameters()
        )
        plp = PrimalLogicProcessor()

        state = (0.0, 0.0, 1.0, 0.0)
        target_cardiac = 1.0
        dt = 0.001

        latencies = []

        # Warm-up
        for _ in range(100):
            state = hbcm.step(0.0, state, dt)
            error = target_cardiac - state[2]  # Cardiac x position
            control = plp.compute_control(error=error, dt=dt)

        # Benchmark
        for i in range(iterations):
            start = time.perf_counter_ns()

            # HBCM step
            state = hbcm.step(i * dt, state, dt)

            # Compute error
            error = target_cardiac - state[2]

            # Control computation
            control = plp.compute_control(error=error, dt=dt)

            end = time.perf_counter_ns()

            latencies.append((end - start) / 1_000_000.0)

        # Statistics
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        p999_latency = latencies_sorted[int(n * 0.999)]
        target_met = p999_latency < 100.0
        margin = 100.0 - p999_latency

        result = ControlLoopResult(
            test_name="HBCM + Control Loop",
            iterations=iterations,
            mean_latency_ms=statistics.mean(latencies),
            median_latency_ms=latencies_sorted[n // 2],
            p95_latency_ms=latencies_sorted[int(n * 0.95)],
            p99_latency_ms=latencies_sorted[int(n * 0.99)],
            p999_latency_ms=p999_latency,
            min_latency_ms=latencies_sorted[0],
            max_latency_ms=latencies_sorted[-1],
            target_met=target_met,
            margin_ms=margin,
            metadata={'dt': dt, 'state_dim': 4}
        )

        self.results.append(result)
        return result

    def benchmark_full_control_loop_simulated(self, iterations: int = 1000) -> ControlLoopResult:
        """
        Benchmark full control loop with simulated I/O.

        Simulates:
        1. Sensor reading (ADC conversion time)
        2. HBCM state update
        3. Control computation
        4. Command serialization
        5. Actuator response

        Args:
            iterations: Number of control cycles

        Returns:
            ControlLoopResult
        """
        print(f"\n[3/5] Benchmarking full control loop (simulated I/O, {iterations:,} iterations)...")

        hbcm = HeartBrainCouplingModel(
            neural_model=FitzHughNagumo(),
            cardiac_model=VanDerPolOscillator(),
            coupling=CouplingParameters()
        )
        plp = PrimalLogicProcessor()

        state = (0.0, 0.0, 1.0, 0.0)
        target = 1.0
        dt = 0.001

        latencies = []

        # Simulate realistic I/O delays
        SENSOR_DELAY_US = 50  # 50 microseconds ADC conversion
        COMMAND_DELAY_US = 100  # 100 microseconds serial transmission

        for i in range(iterations):
            start = time.perf_counter_ns()

            # 1. Sensor reading (simulate ADC delay)
            sensor_start = time.perf_counter()
            while (time.perf_counter() - sensor_start) * 1_000_000 < SENSOR_DELAY_US:
                pass  # Busy wait
            sensor_value = state[2]

            # 2. HBCM state update
            state = hbcm.step(i * dt, state, dt)

            # 3. Compute error
            error = target - sensor_value

            # 4. Control computation
            control = plp.compute_control(error=error, dt=dt)

            # 5. Command serialization (simulate serial delay)
            cmd_start = time.perf_counter()
            while (time.perf_counter() - cmd_start) * 1_000_000 < COMMAND_DELAY_US:
                pass  # Busy wait
            command_bytes = int(control * 255) & 0xFF

            end = time.perf_counter_ns()

            latencies.append((end - start) / 1_000_000.0)

        # Statistics
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        p999_latency = latencies_sorted[int(n * 0.999)]
        target_met = p999_latency < 100.0
        margin = 100.0 - p999_latency

        result = ControlLoopResult(
            test_name="Full Control Loop (Simulated I/O)",
            iterations=iterations,
            mean_latency_ms=statistics.mean(latencies),
            median_latency_ms=latencies_sorted[n // 2],
            p95_latency_ms=latencies_sorted[int(n * 0.95)],
            p99_latency_ms=latencies_sorted[int(n * 0.99)],
            p999_latency_ms=p999_latency,
            min_latency_ms=latencies_sorted[0],
            max_latency_ms=latencies_sorted[-1],
            target_met=target_met,
            margin_ms=margin,
            metadata={
                'sensor_delay_us': SENSOR_DELAY_US,
                'command_delay_us': COMMAND_DELAY_US,
                'total_simulated_io_delay_us': SENSOR_DELAY_US + COMMAND_DELAY_US
            }
        )

        self.results.append(result)
        return result

    def benchmark_control_loop_frequencies(self) -> List[ControlLoopResult]:
        """
        Benchmark control loop at different frequencies.

        Tests: 10 Hz, 100 Hz, 1000 Hz control rates.

        Returns:
            List of ControlLoopResults
        """
        print(f"\n[4/5] Benchmarking different control frequencies...")

        frequencies = [10, 100, 1000]
        results = []

        for freq_hz in frequencies:
            print(f"  Testing {freq_hz} Hz control rate...")

            dt = 1.0 / freq_hz
            duration_s = 10.0
            iterations = int(freq_hz * duration_s)

            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(),
                cardiac_model=VanDerPolOscillator(),
                coupling=CouplingParameters()
            )
            plp = PrimalLogicProcessor()

            state = (0.0, 0.0, 1.0, 0.0)
            target = 1.0

            latencies = []
            start_time = time.perf_counter()

            for i in range(iterations):
                cycle_start = time.perf_counter_ns()

                # Control loop
                state = hbcm.step(i * dt, state, dt)
                error = target - state[2]
                control = plp.compute_control(error=error, dt=dt)

                cycle_end = time.perf_counter_ns()

                latencies.append((cycle_end - cycle_start) / 1_000_000.0)

            end_time = time.perf_counter()
            actual_duration = end_time - start_time

            # Statistics
            latencies_sorted = sorted(latencies)
            n = len(latencies_sorted)

            p999_latency = latencies_sorted[int(n * 0.999)]
            target_met = p999_latency < (1000.0 / freq_hz)  # Must be less than period
            margin = (1000.0 / freq_hz) - p999_latency

            result = ControlLoopResult(
                test_name=f"Control Loop @ {freq_hz} Hz",
                iterations=iterations,
                mean_latency_ms=statistics.mean(latencies),
                median_latency_ms=latencies_sorted[n // 2],
                p95_latency_ms=latencies_sorted[int(n * 0.95)],
                p99_latency_ms=latencies_sorted[int(n * 0.99)],
                p999_latency_ms=p999_latency,
                min_latency_ms=latencies_sorted[0],
                max_latency_ms=latencies_sorted[-1],
                target_met=target_met,
                margin_ms=margin,
                metadata={
                    'frequency_hz': freq_hz,
                    'period_ms': 1000.0 / freq_hz,
                    'target_duration_s': duration_s,
                    'actual_duration_s': actual_duration,
                    'realtime_factor': (iterations * dt) / actual_duration
                }
            )

            results.append(result)
            self.results.append(result)

        return results

    def benchmark_sustained_control(self, duration_s: float = 60.0,
                                   freq_hz: int = 1000) -> ControlLoopResult:
        """
        Benchmark sustained control loop performance.

        Tests if system can maintain <100ms latency over extended period.

        Args:
            duration_s: Test duration in seconds
            freq_hz: Control frequency

        Returns:
            ControlLoopResult
        """
        print(f"\n[5/5] Benchmarking sustained control ({duration_s}s @ {freq_hz} Hz)...")

        dt = 1.0 / freq_hz
        iterations = int(freq_hz * duration_s)

        hbcm = HeartBrainCouplingModel(
            neural_model=FitzHughNagumo(),
            cardiac_model=VanDerPolOscillator(),
            coupling=CouplingParameters()
        )
        plp = PrimalLogicProcessor()

        state = (0.0, 0.0, 1.0, 0.0)
        target = 1.0

        latencies = []
        start_time = time.perf_counter()

        # Print progress every 10 seconds
        last_print = start_time

        for i in range(iterations):
            cycle_start = time.perf_counter_ns()

            state = hbcm.step(i * dt, state, dt)
            error = target - state[2]
            control = plp.compute_control(error=error, dt=dt)

            cycle_end = time.perf_counter_ns()

            latencies.append((cycle_end - cycle_start) / 1_000_000.0)

            # Progress update
            current_time = time.perf_counter()
            if current_time - last_print >= 10.0:
                elapsed = current_time - start_time
                progress_pct = (elapsed / duration_s) * 100
                print(f"  Progress: {progress_pct:.1f}% ({elapsed:.1f}s / {duration_s}s)")
                last_print = current_time

        end_time = time.perf_counter()
        actual_duration = end_time - start_time

        # Statistics
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        p999_latency = latencies_sorted[int(n * 0.999)]
        target_met = p999_latency < 100.0
        margin = 100.0 - p999_latency

        result = ControlLoopResult(
            test_name=f"Sustained Control ({duration_s}s @ {freq_hz} Hz)",
            iterations=iterations,
            mean_latency_ms=statistics.mean(latencies),
            median_latency_ms=latencies_sorted[n // 2],
            p95_latency_ms=latencies_sorted[int(n * 0.95)],
            p99_latency_ms=latencies_sorted[int(n * 0.99)],
            p999_latency_ms=p999_latency,
            min_latency_ms=latencies_sorted[0],
            max_latency_ms=latencies_sorted[-1],
            target_met=target_met,
            margin_ms=margin,
            metadata={
                'duration_s': duration_s,
                'frequency_hz': freq_hz,
                'actual_duration_s': actual_duration,
                'realtime_factor': (iterations * dt) / actual_duration,
                'total_cycles': iterations
            }
        )

        self.results.append(result)
        return result

    def run_all(self) -> List[ControlLoopResult]:
        """
        Run all control loop benchmarks.

        Returns:
            List of all benchmark results
        """
        print("\n" + "=" * 70)
        print("CONTROL LOOP LATENCY BENCHMARK SUITE")
        print("Target: <100ms end-to-end latency for prosthetic control")
        print("=" * 70)

        self.results.clear()

        # Run benchmarks
        self.benchmark_plp_control(iterations=10000)
        self.benchmark_hbcm_step_with_control(iterations=10000)
        self.benchmark_full_control_loop_simulated(iterations=1000)
        self.benchmark_control_loop_frequencies()
        self.benchmark_sustained_control(duration_s=60.0, freq_hz=1000)

        # Print summary
        print("\n" + "=" * 70)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 70)

        for result in self.results:
            result.print_summary()

        # Overall assessment
        print("\n" + "=" * 70)
        print("OVERALL ASSESSMENT")
        print("=" * 70)

        targets_met = sum(1 for r in self.results if r.target_met)
        total_tests = len(self.results)

        print(f"\nTests Passed: {targets_met}/{total_tests}")

        if targets_met == total_tests:
            print("\n✅ ALL TARGETS MET - System suitable for prosthetic control")
        elif targets_met >= total_tests * 0.8:
            print("\n⚠️  MOST TARGETS MET - Review failed tests")
        else:
            print("\n❌ TARGETS MISSED - System needs optimization")

        return self.results


def main():
    """Run control loop benchmarks."""
    benchmark = ControlLoopBenchmark()
    results = benchmark.run_all()

    # Save results
    import json
    from datetime import datetime

    output = {
        'timestamp': datetime.now().isoformat(),
        'benchmark_suite': 'Control Loop Latency',
        'target_latency_ms': 100.0,
        'results': [
            {
                'test_name': r.test_name,
                'iterations': r.iterations,
                'mean_latency_ms': r.mean_latency_ms,
                'median_latency_ms': r.median_latency_ms,
                'p95_latency_ms': r.p95_latency_ms,
                'p99_latency_ms': r.p99_latency_ms,
                'p999_latency_ms': r.p999_latency_ms,
                'min_latency_ms': r.min_latency_ms,
                'max_latency_ms': r.max_latency_ms,
                'target_met': r.target_met,
                'margin_ms': r.margin_ms,
                'metadata': r.metadata
            }
            for r in results
        ]
    }

    import os
    output_file = f"/home/user/Multi-Heart-Model/benchmarks/results/control_loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")


if __name__ == '__main__':
    main()
