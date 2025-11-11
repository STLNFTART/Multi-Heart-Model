"""
Metabolic Module - Drug Metabolism and Organ-on-Chip Models
Part of Multi-Heart-Model Suite

This module provides models for hepatic metabolism, drug clearance,
and hepatotoxicity assessment in organ-on-chip systems.
"""

from .liver_chip import (
    LiverParameters,
    HepatocytePopulation,
    LiverMetabolism,
    LiverBioenergetics,
    LiverChipModel
)

__all__ = [
    'LiverParameters',
    'HepatocytePopulation',
    'LiverMetabolism',
    'LiverBioenergetics',
    'LiverChipModel'
]
