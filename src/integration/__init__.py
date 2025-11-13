"""
Microprocessor-Motor Integration Module

Bridges Primal Logic Processor with MotorHandPro QUANT control system.

Author: Donte Lightfoot - Lightfoot Technology
"""

from .motorhand_bridge import MotorHandBridge, QuantInterface, QuantParameters

__all__ = [
    'MotorHandBridge',
    'QuantInterface',
    'QuantParameters'
]
