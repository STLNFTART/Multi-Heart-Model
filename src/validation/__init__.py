"""
Validation framework for physiological model benchmarks.

This module provides tools for validating the Multi-Heart-Model against
published physiological data, established computational models, and
clinical observations.
"""

from .benchmarks import (
    PhysiologicalBenchmarks,
    CardiacBenchmarks,
    NeuralBenchmarks,
    HemodynamicBenchmarks,
)
from .validators import (
    validate_cardiac_model,
    validate_neural_model,
    validate_coupling_model,
    validate_hemodynamics,
)
from .metrics import (
    compute_hrv_metrics,
    compute_pv_loop_metrics,
    compare_waveforms,
)

__all__ = [
    "PhysiologicalBenchmarks",
    "CardiacBenchmarks",
    "NeuralBenchmarks",
    "HemodynamicBenchmarks",
    "validate_cardiac_model",
    "validate_neural_model",
    "validate_coupling_model",
    "validate_hemodynamics",
    "compute_hrv_metrics",
    "compute_pv_loop_metrics",
    "compare_waveforms",
]
