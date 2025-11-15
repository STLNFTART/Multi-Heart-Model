"""
Production-scale performance benchmarking suite.

Comprehensive benchmarks for:
- HBCM simulation performance
- Node.js API load testing
- OpenSim coupling overhead
- Control loop latency
- Memory profiling
- End-to-end system throughput

Usage:
    # Run all benchmarks
    python -m benchmarks.run_all

    # Run specific benchmark
    python -m benchmarks.hbcm_benchmark

    # Generate report
    python -m benchmarks.generate_report
"""

from .hbcm_benchmark import HBCMBenchmark
from .api_benchmark import APIBenchmark
from .control_loop_benchmark import ControlLoopBenchmark
from .opensim_benchmark import OpenSimBenchmark
from .memory_benchmark import MemoryBenchmark

__all__ = [
    'HBCMBenchmark',
    'APIBenchmark',
    'ControlLoopBenchmark',
    'OpenSimBenchmark',
    'MemoryBenchmark',
]
