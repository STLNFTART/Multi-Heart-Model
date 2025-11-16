#!/usr/bin/env python3
"""
Performance Monitoring System
Real-time latency tracking and performance validation
Ensures <100ms latency requirement for production deployment
"""

import time
import statistics
from collections import deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
import json
from pathlib import Path


@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    timestamp: float
    operation: str
    latency_ms: float
    cpu_percent: float
    memory_mb: float
    metadata: Optional[Dict] = None


class PerformanceMonitor:
    """
    Real-time performance monitoring for Multi-Heart-Model
    Tracks latency, throughput, and resource usage
    """

    def __init__(self, max_history: int = 10000,
                 latency_target_ms: float = 100.0):
        """
        Initialize performance monitor

        Args:
            max_history: Maximum metrics to store
            latency_target_ms: Target latency threshold
        """
        self.max_history = max_history
        self.latency_target = latency_target_ms
        self.metrics = deque(maxlen=max_history)
        self.start_time = time.time()

        # Try to import psutil for system metrics
        try:
            import psutil
            self.psutil = psutil
            self.process = psutil.Process()
        except ImportError:
            self.psutil = None
            self.process = None
            print("Warning: psutil not available, system metrics disabled")

    def measure_operation(self, operation: str):
        """
        Context manager for measuring operation latency

        Usage:
            with monitor.measure_operation("step_hbcm"):
                result = hbcm.step(t, state, dt)
        """
        return _OperationTimer(self, operation)

    def record_metric(self, operation: str, latency_ms: float,
                     metadata: Optional[Dict] = None):
        """Record a performance metric"""
        # Get system metrics if available
        cpu_percent = self.process.cpu_percent() if self.process else 0.0
        memory_mb = self.process.memory_info().rss / 1024 / 1024 if self.process else 0.0

        metric = PerformanceMetric(
            timestamp=time.time(),
            operation=operation,
            latency_ms=latency_ms,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            metadata=metadata
        )

        self.metrics.append(metric)

    def get_statistics(self, operation: Optional[str] = None,
                      time_window_s: Optional[float] = None) -> Dict:
        """
        Get performance statistics

        Args:
            operation: Filter by operation name (None = all)
            time_window_s: Time window in seconds (None = all time)

        Returns:
            Statistics dictionary
        """
        # Filter metrics
        filtered = list(self.metrics)

        if operation:
            filtered = [m for m in filtered if m.operation == operation]

        if time_window_s:
            cutoff_time = time.time() - time_window_s
            filtered = [m for m in filtered if m.timestamp >= cutoff_time]

        if not filtered:
            return {}

        latencies = [m.latency_ms for m in filtered]
        cpu_values = [m.cpu_percent for m in filtered]
        memory_values = [m.memory_mb for m in filtered]

        stats = {
            'operation': operation or 'all',
            'sample_count': len(filtered),
            'latency': {
                'min_ms': min(latencies),
                'max_ms': max(latencies),
                'mean_ms': statistics.mean(latencies),
                'median_ms': statistics.median(latencies),
                'p95_ms': np.percentile(latencies, 95),
                'p99_ms': np.percentile(latencies, 99),
                'stdev_ms': statistics.stdev(latencies) if len(latencies) > 1 else 0,
                'under_target_pct': 100 * sum(1 for l in latencies if l < self.latency_target) / len(latencies)
            },
            'cpu': {
                'mean_percent': statistics.mean(cpu_values) if cpu_values else 0,
                'max_percent': max(cpu_values) if cpu_values else 0
            },
            'memory': {
                'mean_mb': statistics.mean(memory_values) if memory_values else 0,
                'max_mb': max(memory_values) if memory_values else 0
            },
            'throughput': {
                'operations_per_second': len(filtered) / (filtered[-1].timestamp - filtered[0].timestamp)
                                        if len(filtered) > 1 else 0
            }
        }

        return stats

    def check_performance_requirements(self) -> Tuple[bool, Dict]:
        """
        Check if performance meets requirements

        Returns:
            (meets_requirements, details)
        """
        stats = self.get_statistics()

        if not stats:
            return False, {"error": "No metrics collected"}

        latency_stats = stats['latency']

        # Requirements:
        # 1. Mean latency < 100ms
        # 2. P95 latency < 150ms
        # 3. P99 latency < 200ms
        # 4. >95% of operations under target

        meets_requirements = (
            latency_stats['mean_ms'] < 100.0 and
            latency_stats['p95_ms'] < 150.0 and
            latency_stats['p99_ms'] < 200.0 and
            latency_stats['under_target_pct'] > 95.0
        )

        details = {
            'meets_requirements': meets_requirements,
            'checks': {
                'mean_latency_ok': latency_stats['mean_ms'] < 100.0,
                'p95_latency_ok': latency_stats['p95_ms'] < 150.0,
                'p99_latency_ok': latency_stats['p99_ms'] < 200.0,
                'target_percentage_ok': latency_stats['under_target_pct'] > 95.0
            },
            'statistics': stats
        }

        return meets_requirements, details

    def print_report(self, operation: Optional[str] = None):
        """Print performance report"""
        stats = self.get_statistics(operation)

        if not stats:
            print("No metrics collected")
            return

        print("=" * 80)
        print(f"Performance Report - {stats['operation']}")
        print("=" * 80)

        print(f"\nSamples: {stats['sample_count']}")
        print(f"Duration: {time.time() - self.start_time:.2f}s")

        print(f"\nLatency Statistics:")
        lat = stats['latency']
        print(f"  ├─ Mean: {lat['mean_ms']:.2f} ms")
        print(f"  ├─ Median: {lat['median_ms']:.2f} ms")
        print(f"  ├─ Min: {lat['min_ms']:.2f} ms")
        print(f"  ├─ Max: {lat['max_ms']:.2f} ms")
        print(f"  ├─ P95: {lat['p95_ms']:.2f} ms")
        print(f"  ├─ P99: {lat['p99_ms']:.2f} ms")
        print(f"  ├─ Stdev: {lat['stdev_ms']:.2f} ms")
        print(f"  └─ <{self.latency_target}ms: {lat['under_target_pct']:.1f}%")

        if self.psutil:
            print(f"\nResource Usage:")
            cpu = stats['cpu']
            mem = stats['memory']
            print(f"  ├─ CPU Mean: {cpu['mean_percent']:.1f}%")
            print(f"  ├─ CPU Max: {cpu['max_percent']:.1f}%")
            print(f"  ├─ Memory Mean: {mem['mean_mb']:.1f} MB")
            print(f"  └─ Memory Max: {mem['max_mb']:.1f} MB")

        throughput = stats['throughput']
        print(f"\nThroughput: {throughput['operations_per_second']:.1f} ops/s")

        # Check requirements
        meets_req, details = self.check_performance_requirements()
        print(f"\nMeets Requirements: {'✓ YES' if meets_req else '✗ NO'}")

        if not meets_req:
            print("\nFailed Checks:")
            for check, passed in details['checks'].items():
                if not passed:
                    print(f"  ✗ {check}")

        print("=" * 80)

    def save_report(self, filename: Optional[str] = None):
        """Save performance report to JSON"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.json"

        stats = self.get_statistics()
        meets_req, details = self.check_performance_requirements()

        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'duration_seconds': time.time() - self.start_time,
            'meets_requirements': meets_req,
            'details': details,
            'all_metrics': [asdict(m) for m in list(self.metrics)]
        }

        output_path = Path(__file__).parent.parent / "results" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"✓ Report saved to: {output_path}")


class _OperationTimer:
    """Context manager for timing operations"""

    def __init__(self, monitor: PerformanceMonitor, operation: str):
        self.monitor = monitor
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000
        self.monitor.record_metric(self.operation, latency_ms)


def demo_performance_monitoring():
    """Demonstration of performance monitoring"""
    print("=" * 80)
    print("Performance Monitoring Demonstration")
    print("=" * 80)
    print()

    # Import HBCM
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.coupling import HeartBrainCouplingModel

    # Create monitor
    monitor = PerformanceMonitor(latency_target_ms=100.0)

    # Create HBCM
    hbcm = HeartBrainCouplingModel()
    state = (0.0, 0.0, 1.0, 0.0)

    print("Running monitored simulation for 10 seconds...")

    # Run simulation with monitoring
    t = 0.0
    dt = 0.001
    duration = 10.0

    while t < duration:
        with monitor.measure_operation("hbcm_step"):
            state = hbcm.step(t, state, dt)
        t += dt

        if int(t / dt) % 1000 == 0:
            print(f"  Progress: {t:.1f}s / {duration:.1f}s")

    print("\n✓ Simulation complete\n")

    # Print report
    monitor.print_report("hbcm_step")

    # Save report
    monitor.save_report()


if __name__ == "__main__":
    # Install numpy if needed
    try:
        import numpy
    except ImportError:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])

    demo_performance_monitoring()
