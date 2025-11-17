"""
Primal Logic LAM Assistant for Multi-Heart-Model

This module provides intelligent assistance for:
- Multi-sensor fusion with missing data handling
- Interactive demo explanations
- Parameter tuning suggestions
- System health monitoring

The assistant layer does NOT replace the validated PLP control core.
It handles meta-tasks: interpretation, explanation, coordination.
"""

from .primal_lam_assistant import (
    PrimalLAMAssistant,
    MultiSensorFusion,
    SensorFusionConfig
)

__all__ = [
    "PrimalLAMAssistant",
    "MultiSensorFusion",
    "SensorFusionConfig"
]
