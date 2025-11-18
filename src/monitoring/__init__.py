"""
Production-grade performance monitoring and latency profiling.

This module provides instrumentation for measuring and tracking performance
metrics across the Multi-Heart-Model system.

Key Components:
- LatencyProfiler: Context manager and decorator for timing operations
- MetricsCollector: Prometheus-compatible metrics collection
- PerformanceLogger: Structured logging for performance data
- EndToEndTracer: Distributed tracing support

Usage:
    from src.monitoring import LatencyProfiler, MetricsCollector

    # Context manager
    with LatencyProfiler("hbcm_simulation"):
        result = hbcm.simulate(...)

    # Decorator
    @LatencyProfiler.profile("control_loop")
    def control_loop(state):
        return compute_control(state)

    # Get metrics
    metrics = MetricsCollector.get_summary()
"""

from .profiler import LatencyProfiler, PerformanceTimer
from .metrics import MetricsCollector, Metric, MetricType
from .logger import PerformanceLogger, LogLevel
from .tracer import EndToEndTracer, TraceContext

__all__ = [
    'LatencyProfiler',
    'PerformanceTimer',
    'MetricsCollector',
    'Metric',
    'MetricType',
    'PerformanceLogger',
    'LogLevel',
    'EndToEndTracer',
    'TraceContext',
]
