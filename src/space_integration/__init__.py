"""
Space Integration Module

Clean interface layer between api_integrations (external data) and
Multi-Heart-Model internal systems.

Key Principle: api_integrations is NEVER called from control kernels.
This module provides domain-specific dataclasses and integration functions.

Author: Multi-Heart-Model Team
"""

from .context import EnvContext, CommsProfile, ScenarioConfig
from .integration import (
    build_environment_context,
    get_comms_profile,
    generate_space_scenario
)

__all__ = [
    'EnvContext',
    'CommsProfile',
    'ScenarioConfig',
    'build_environment_context',
    'get_comms_profile',
    'generate_space_scenario'
]
