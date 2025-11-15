"""BCI Data Acquisition Adapters."""

from .bci_adapter_base import (
    BCIAdapterBase,
    BCIDataPacket,
    BCIStreamConfig,
    CircularBuffer,
    DataQualityMetrics,
    SignalType
)
from .openbci_adapter import OpenBCIAdapter
from .synthetic_adapter import SyntheticAdapter

__all__ = [
    "BCIAdapterBase",
    "BCIDataPacket",
    "BCIStreamConfig",
    "CircularBuffer",
    "DataQualityMetrics",
    "SignalType",
    "OpenBCIAdapter",
    "SyntheticAdapter",
]
