"""
Primal Logic Microprocessor Integration Module

Implements the integral control system with exponential memory weighting
for autonomous vehicle control and motor actuation.

Author: Donte Lightfoot - Lightfoot Technology
Patent Pending: U.S. Provisional Patent Application No. 63/842,846
"""

from .primal_processor import PrimalLogicProcessor, IntegralProcessingUnit, ProcessorConfig
from .control_system import IntegralControlSystem, ExponentialMemoryWeighting

__all__ = [
    'PrimalLogicProcessor',
    'IntegralProcessingUnit',
    'ProcessorConfig',
    'IntegralControlSystem',
    'ExponentialMemoryWeighting'
]

__version__ = '1.0.0'
__author__ = 'Donte Lightfoot'
