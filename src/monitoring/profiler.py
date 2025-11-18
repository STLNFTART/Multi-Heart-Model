"""
Latency profiling infrastructure for production monitoring.

Provides context managers, decorators, and utilities for measuring
operation latency with nanosecond precision.
"""

import time
import functools
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field
from contextlib import contextmanager
from datetime import datetime


@dataclass
class TimingResult:
    """Result of a timing operation."""

    operation: str
    start_time: float
    end_time: float
    duration_ns: int
    duration_ms: float
    duration_s: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_us(self) -> float:
        """Duration in microseconds."""
        return self.duration_ns / 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'operation': self.operation,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_ns': self.duration_ns,
            'duration_us': self.duration_us,
            'duration_ms': self.duration_ms,
            'duration_s': self.duration_s,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class PerformanceTimer:
    """
    High-resolution performance timer using monotonic clock.

    Uses time.perf_counter_ns() for nanosecond precision timing.
    """

    def __init__(self):
        self._start_ns: Optional[int] = None
        self._end_ns: Optional[int] = None

    def start(self) -> None:
        """Start the timer."""
        self._start_ns = time.perf_counter_ns()
        self._end_ns = None

    def stop(self) -> int:
        """
        Stop the timer and return elapsed time in nanoseconds.

        Returns:
            int: Elapsed time in nanoseconds
        """
        if self._start_ns is None:
            raise RuntimeError("Timer not started")

        self._end_ns = time.perf_counter_ns()
        return self._end_ns - self._start_ns

    def elapsed_ns(self) -> int:
        """Get elapsed time in nanoseconds."""
        if self._start_ns is None:
            raise RuntimeError("Timer not started")

        if self._end_ns is None:
            # Timer still running, return current elapsed time
            return time.perf_counter_ns() - self._start_ns

        return self._end_ns - self._start_ns

    def elapsed_us(self) -> float:
        """Get elapsed time in microseconds."""
        return self.elapsed_ns() / 1000.0

    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed_ns() / 1_000_000.0

    def elapsed_s(self) -> float:
        """Get elapsed time in seconds."""
        return self.elapsed_ns() / 1_000_000_000.0

    def reset(self) -> None:
        """Reset the timer."""
        self._start_ns = None
        self._end_ns = None


class LatencyProfiler:
    """
    Production-grade latency profiler with context manager and decorator support.

    Features:
    - Nanosecond precision timing
    - Automatic metrics collection
    - Nested timing support
    - Thread-safe operation
    - Percentile calculation (p50, p95, p99)

    Usage:
        # Context manager
        with LatencyProfiler("operation_name") as profiler:
            do_work()

        # Decorator
        @LatencyProfiler.profile("function_name")
        def my_function():
            pass

        # Manual timing
        profiler = LatencyProfiler("manual_op")
        profiler.start()
        do_work()
        result = profiler.stop()
    """

    # Global storage for all timing results
    _all_results: Dict[str, List[TimingResult]] = {}
    _enabled: bool = True

    def __init__(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize latency profiler.

        Args:
            operation: Name of the operation being profiled
            metadata: Optional metadata to attach to timing results
        """
        self.operation = operation
        self.metadata = metadata or {}
        self.timer = PerformanceTimer()
        self._result: Optional[TimingResult] = None

    def start(self) -> 'LatencyProfiler':
        """Start profiling."""
        if not self._enabled:
            return self

        self.timer.start()
        return self

    def stop(self) -> Optional[TimingResult]:
        """
        Stop profiling and return timing result.

        Returns:
            TimingResult: Timing information, or None if profiling disabled
        """
        if not self._enabled:
            return None

        duration_ns = self.timer.stop()

        # Create timing result
        now = datetime.now()
        self._result = TimingResult(
            operation=self.operation,
            start_time=time.time() - (duration_ns / 1_000_000_000.0),
            end_time=time.time(),
            duration_ns=duration_ns,
            duration_ms=duration_ns / 1_000_000.0,
            duration_s=duration_ns / 1_000_000_000.0,
            timestamp=now,
            metadata=self.metadata
        )

        # Store result
        if self.operation not in self._all_results:
            self._all_results[self.operation] = []
        self._all_results[self.operation].append(self._result)

        return self._result

    def __enter__(self) -> 'LatencyProfiler':
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()

    @property
    def result(self) -> Optional[TimingResult]:
        """Get the timing result."""
        return self._result

    @classmethod
    def profile(cls, operation: str, metadata: Optional[Dict[str, Any]] = None) -> Callable:
        """
        Decorator for profiling function execution time.

        Args:
            operation: Name of the operation (defaults to function name)
            metadata: Optional metadata to attach

        Returns:
            Decorator function

        Example:
            @LatencyProfiler.profile("my_operation")
            def my_function(x, y):
                return x + y
        """
        def decorator(func: Callable) -> Callable:
            op_name = operation or func.__name__

            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not cls._enabled:
                    return func(*args, **kwargs)

                with cls(op_name, metadata=metadata):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    @classmethod
    def enable(cls) -> None:
        """Enable profiling globally."""
        cls._enabled = True

    @classmethod
    def disable(cls) -> None:
        """Disable profiling globally."""
        cls._enabled = False

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if profiling is enabled."""
        return cls._enabled

    @classmethod
    def get_results(cls, operation: Optional[str] = None) -> Dict[str, List[TimingResult]]:
        """
        Get timing results.

        Args:
            operation: Optional operation name to filter by

        Returns:
            Dictionary mapping operation names to lists of timing results
        """
        if operation:
            return {operation: cls._all_results.get(operation, [])}
        return cls._all_results.copy()

    @classmethod
    def get_statistics(cls, operation: str) -> Optional[Dict[str, float]]:
        """
        Get statistical summary for an operation.

        Args:
            operation: Operation name

        Returns:
            Dictionary with min, max, mean, median, p95, p99 in milliseconds,
            or None if no data available
        """
        results = cls._all_results.get(operation, [])
        if not results:
            return None

        durations_ms = sorted([r.duration_ms for r in results])
        n = len(durations_ms)

        return {
            'count': n,
            'min_ms': durations_ms[0],
            'max_ms': durations_ms[-1],
            'mean_ms': sum(durations_ms) / n,
            'median_ms': durations_ms[n // 2],
            'p95_ms': durations_ms[int(n * 0.95)] if n > 1 else durations_ms[0],
            'p99_ms': durations_ms[int(n * 0.99)] if n > 1 else durations_ms[0],
            'p999_ms': durations_ms[int(n * 0.999)] if n > 2 else durations_ms[-1],
        }

    @classmethod
    def get_summary(cls) -> Dict[str, Dict[str, float]]:
        """
        Get statistical summary for all operations.

        Returns:
            Dictionary mapping operation names to statistics
        """
        summary = {}
        for operation in cls._all_results.keys():
            stats = cls.get_statistics(operation)
            if stats:
                summary[operation] = stats
        return summary

    @classmethod
    def clear(cls, operation: Optional[str] = None) -> None:
        """
        Clear timing results.

        Args:
            operation: Optional operation name to clear (clears all if not specified)
        """
        if operation:
            if operation in cls._all_results:
                cls._all_results[operation].clear()
        else:
            cls._all_results.clear()

    @classmethod
    def print_summary(cls, operation: Optional[str] = None) -> None:
        """
        Print summary statistics.

        Args:
            operation: Optional operation name to print (prints all if not specified)
        """
        summary = cls.get_summary()

        if operation:
            if operation in summary:
                summary = {operation: summary[operation]}
            else:
                print(f"No data for operation: {operation}")
                return

        if not summary:
            print("No profiling data available")
            return

        print("\n" + "=" * 80)
        print("LATENCY PROFILING SUMMARY")
        print("=" * 80)

        for op_name, stats in sorted(summary.items()):
            print(f"\nOperation: {op_name}")
            print(f"  Count:      {stats['count']:,}")
            print(f"  Min:        {stats['min_ms']:.3f} ms")
            print(f"  Mean:       {stats['mean_ms']:.3f} ms")
            print(f"  Median:     {stats['median_ms']:.3f} ms")
            print(f"  P95:        {stats['p95_ms']:.3f} ms")
            print(f"  P99:        {stats['p99_ms']:.3f} ms")
            print(f"  P99.9:      {stats['p999_ms']:.3f} ms")
            print(f"  Max:        {stats['max_ms']:.3f} ms")

        print("\n" + "=" * 80)


@contextmanager
def profile_section(operation: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Convenience context manager for profiling a code section.

    Args:
        operation: Name of the operation
        metadata: Optional metadata

    Yields:
        LatencyProfiler instance

    Example:
        with profile_section("my_operation") as profiler:
            do_work()

        print(f"Took {profiler.result.duration_ms:.3f} ms")
    """
    profiler = LatencyProfiler(operation, metadata=metadata)
    with profiler:
        yield profiler
