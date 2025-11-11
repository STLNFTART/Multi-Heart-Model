"""
Data Identifier Flags and Types

Provides clear identification and separation between simulated and real-world data.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class DataSourceType(Enum):
    """Primary data source classification"""
    SIMULATED = "SIMULATED"
    REALWORLD = "REALWORLD"


class DataOrigin(Enum):
    """Detailed origin of the data"""
    # Simulated origins
    HBCM_SIMULATION = "HBCM_SIMULATION"
    MULTI_HEART_MODEL = "MULTI_HEART_MODEL"

    # Real-world origins
    QUANTRO = "QUANTRO"
    CLINICAL = "CLINICAL"
    EXPERIMENTAL = "EXPERIMENTAL"
    DEVICE_MEASUREMENT = "DEVICE_MEASUREMENT"
    ECG_DEVICE = "ECG_DEVICE"
    EEG_DEVICE = "EEG_DEVICE"
    WEARABLE_SENSOR = "WEARABLE_SENSOR"


class DataQuality(Enum):
    """Data processing and quality level"""
    RAW = "RAW"
    PROCESSED = "PROCESSED"
    VALIDATED = "VALIDATED"
    CLEANED = "CLEANED"
    ANALYZED = "ANALYZED"


class ModelType(Enum):
    """Type of computational model used"""
    HBCM = "HBCM"  # Heart-Brain Coupling Model
    FITZHUGH_NAGUMO = "FITZHUGH_NAGUMO"
    VAN_DER_POL = "VAN_DER_POL"
    COUPLED_OSCILLATOR = "COUPLED_OSCILLATOR"


class DataCategory(Enum):
    """Category of physiological data"""
    CARDIAC = "CARDIAC"
    NEURAL = "NEURAL"
    COUPLED = "COUPLED"
    ECG = "ECG"
    EEG = "EEG"
    HRV = "HRV"  # Heart Rate Variability
    BRAIN_ACTIVITY = "BRAIN_ACTIVITY"


@dataclass
class DataIdentifier:
    """
    Complete data identifier with all flags for clear separation
    between simulated and real-world data.
    """
    data_id: str
    source_type: DataSourceType
    origin: DataOrigin
    quality: DataQuality
    category: DataCategory
    model_type: Optional[ModelType] = None
    version: str = "1.0.0"

    def is_simulated(self) -> bool:
        """Check if this is simulated data"""
        return self.source_type == DataSourceType.SIMULATED

    def is_realworld(self) -> bool:
        """Check if this is real-world data"""
        return self.source_type == DataSourceType.REALWORLD

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "data_id": self.data_id,
            "source_type": self.source_type.value,
            "origin": self.origin.value,
            "quality": self.quality.value,
            "category": self.category.value,
            "model_type": self.model_type.value if self.model_type else None,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataIdentifier":
        """Create from dictionary"""
        return cls(
            data_id=data["data_id"],
            source_type=DataSourceType(data["source_type"]),
            origin=DataOrigin(data["origin"]),
            quality=DataQuality(data["quality"]),
            category=DataCategory(data["category"]),
            model_type=ModelType(data["model_type"]) if data.get("model_type") else None,
            version=data.get("version", "1.0.0"),
        )

    def generate_filename(self, extension: str = "csv") -> str:
        """
        Generate a standardized filename based on identifier flags

        Format:
        - Simulated: sim_<category>_<model>_<data_id>.<ext>
        - Real-world: real_<origin>_<category>_<data_id>.<ext>
        """
        category = self.category.value.lower()
        data_id = self.data_id.lower().replace(" ", "_")

        if self.is_simulated():
            model = self.model_type.value.lower() if self.model_type else "unknown"
            return f"sim_{category}_{model}_{data_id}.{extension}"
        else:
            origin = self.origin.value.lower()
            return f"real_{origin}_{category}_{data_id}.{extension}"

    def __str__(self) -> str:
        """String representation"""
        return (
            f"DataIdentifier({self.source_type.value}, "
            f"{self.origin.value}, {self.category.value}, "
            f"quality={self.quality.value})"
        )


def create_simulated_identifier(
    data_id: str,
    model_type: ModelType,
    category: DataCategory,
    quality: DataQuality = DataQuality.RAW,
    version: str = "1.0.0"
) -> DataIdentifier:
    """
    Create a data identifier for simulated data
    """
    return DataIdentifier(
        data_id=data_id,
        source_type=DataSourceType.SIMULATED,
        origin=DataOrigin.HBCM_SIMULATION,
        quality=quality,
        category=category,
        model_type=model_type,
        version=version,
    )


def create_realworld_identifier(
    data_id: str,
    origin: DataOrigin,
    category: DataCategory,
    quality: DataQuality = DataQuality.RAW,
    version: str = "1.0.0"
) -> DataIdentifier:
    """
    Create a data identifier for real-world data
    """
    # Validate that origin is a real-world type
    realworld_origins = {
        DataOrigin.QUANTRO,
        DataOrigin.CLINICAL,
        DataOrigin.EXPERIMENTAL,
        DataOrigin.DEVICE_MEASUREMENT,
        DataOrigin.ECG_DEVICE,
        DataOrigin.EEG_DEVICE,
        DataOrigin.WEARABLE_SENSOR,
    }

    if origin not in realworld_origins:
        raise ValueError(f"Invalid real-world origin: {origin}")

    return DataIdentifier(
        data_id=data_id,
        source_type=DataSourceType.REALWORLD,
        origin=origin,
        quality=quality,
        category=category,
        model_type=None,  # No model for real-world data
        version=version,
    )
