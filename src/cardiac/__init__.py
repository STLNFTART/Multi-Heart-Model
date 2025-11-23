"""
Cardiac Models Module

Comprehensive collection of cardiac electrophysiology and hemodynamics models:

**Electrophysiology Models:**
- Van der Pol: Relaxation oscillator for cardiac rhythm
- Luo-Rudy Dynamic (LRd): Comprehensive guinea pig ventricular model
- Ten Tusscher-Panfilov 2006: Human ventricular action potential
- O'Hara-Rudy 2011 (ORd): CiPA standard for drug safety
- Courtemanche: Human atrial model for AF studies

**Hemodynamics Models:**
- Windkessel: Arterial pressure-flow dynamics (2, 3, and 4-element models)

All models follow standard interface:
- get_initial_state() -> initial conditions
- derivatives(t, state, stimulus) -> state derivatives
- step(t, state, dt, stimulus) -> next state
"""

# Simple oscillator model
from .van_der_pol import VanDerPolOscillator

# Detailed ionic models
from .luo_rudy import LuoRudyModel, LuoRudyParameters
from .ten_tusscher import TenTusscherModel, TenTusscherParameters
from .ohara_rudy import OHaraRudyModel, OHaraRudyParameters
from .courtemanche import CourtemancheModel, CourtemancheParameters

# Hemodynamics models
from .windkessel import (
    Windkessel2Model,
    Windkessel2Parameters,
    Windkessel3Model,
    Windkessel3Parameters,
    Windkessel4Model,
    Windkessel4Parameters,
    couple_windkessel_to_heart,
)

__all__ = [
    # Simple model
    "VanDerPolOscillator",

    # Luo-Rudy Dynamic
    "LuoRudyModel",
    "LuoRudyParameters",

    # Ten Tusscher-Panfilov 2006
    "TenTusscherModel",
    "TenTusscherParameters",

    # O'Hara-Rudy 2011 (CiPA)
    "OHaraRudyModel",
    "OHaraRudyParameters",

    # Courtemanche atrial
    "CourtemancheModel",
    "CourtemancheParameters",

    # Windkessel hemodynamics
    "Windkessel2Model",
    "Windkessel2Parameters",
    "Windkessel3Model",
    "Windkessel3Parameters",
    "Windkessel4Model",
    "Windkessel4Parameters",
    "couple_windkessel_to_heart",
]
