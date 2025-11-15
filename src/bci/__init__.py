"""Brain-Computer Interface integration for Multi-Heart-Model.

This module provides interfaces to:
- OpenBCI hardware for real-time EEG/neural signal acquisition
- Neuralink-style high-bandwidth neural interfaces
- Signal processing pipelines for neural data
"""

from .openbci_interface import OpenBCIInterface, OpenBCIConfig
from .neuralink_adapter import NeuralinkAdapter, NeuralinkConfig
from .signal_processor import SignalProcessor, BandpassFilter
from .neural_bridge import NeuralToBrainModelBridge

__all__ = [
    "OpenBCIInterface",
    "OpenBCIConfig",
    "NeuralinkAdapter",
    "NeuralinkConfig",
    "SignalProcessor",
    "BandpassFilter",
    "NeuralToBrainModelBridge",
]
