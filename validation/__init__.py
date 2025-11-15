"""
Validation Framework for Multi-Heart-Model

Comprehensive testing suite for BCI repository integration.
"""

from .framework import (
    ValidationTestBase,
    BenchmarkResult,
    CompatibilityCheck,
    CompatibilityMatrix,
    PerformanceBenchmark,
    RegressionTester
)

__version__ = "1.0.0"

__all__ = [
    "ValidationTestBase",
    "BenchmarkResult",
    "CompatibilityCheck",
    "CompatibilityMatrix",
    "PerformanceBenchmark",
    "RegressionTester",
]
