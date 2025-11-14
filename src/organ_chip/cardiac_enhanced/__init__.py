"""
Enhanced cardiac subsystem with drug effects.
"""
from .drug_cardiac_model import (
    DrugCardiacModel,
    create_doxorubicin_cardiac_model,
    create_quinidine_cardiac_model,
)

__all__ = [
    'DrugCardiacModel',
    'create_doxorubicin_cardiac_model',
    'create_quinidine_cardiac_model',
]
