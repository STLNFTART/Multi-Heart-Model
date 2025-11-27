"""
Integration Module

Bridges between different systems:
- Primal Logic Processor with MotorHandPro QUANT control system
- HBCM with OpenSim biomechanical simulation

Author: Donte Lightfoot - Lightfoot Technology
"""

from .motorhand_bridge import MotorHandBridge, QuantInterface, QuantParameters
from .opensim_hooks import (
    OpenSimBridge,
    CardiacForceExtractor,
    OpenSimConfig,
    BiomechanicalResults,
    run_hbcm_opensim_integration
)

__all__ = [
    'MotorHandBridge',
    'QuantInterface',
    'QuantParameters',
    'OpenSimBridge',
    'CardiacForceExtractor',
    'OpenSimConfig',
    'BiomechanicalResults',
    'run_hbcm_opensim_integration'
]
