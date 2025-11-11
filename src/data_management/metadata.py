"""
Data Metadata Schema and Management

Handles creation, validation, and persistence of dataset metadata
with bidirectional synchronization support.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .identifiers import DataIdentifier


@dataclass
class BidirectionalSync:
    """Bidirectional synchronization metadata"""
    enabled: bool = False
    last_sync: Optional[str] = None
    sync_direction: str = "none"  # "to_quantro", "from_quantro", "bidirectional"
    sync_status: str = "pending"  # "pending", "synced", "conflict", "failed"
    conflict_resolution: str = "manual"  # "manual", "latest_wins", "merge"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BidirectionalSync":
        return cls(**data)


@dataclass
class DataMetadata:
    """
    Complete metadata schema for all datasets

    Includes data identification, processing pipeline, model parameters,
    and bidirectional synchronization information.
    """
    identifier: DataIdentifier
    timestamp: str
    source_repo: str
    data_file: str
    description: str = ""
    model_parameters: Dict[str, Any] = None
    processing_pipeline: List[str] = None
    bidirectional_sync: BidirectionalSync = None
    custom_fields: Dict[str, Any] = None

    def __post_init__(self):
        if self.model_parameters is None:
            self.model_parameters = {}
        if self.processing_pipeline is None:
            self.processing_pipeline = []
        if self.bidirectional_sync is None:
            self.bidirectional_sync = BidirectionalSync()
        if self.custom_fields is None:
            self.custom_fields = {}

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "data_id": self.identifier.data_id,
            "source_type": self.identifier.source_type.value,
            "source_repo": self.source_repo,
            "timestamp": self.timestamp,
            "data_file": self.data_file,
            "description": self.description,
            "data_flags": self.identifier.to_dict(),
            "model_parameters": self.model_parameters,
            "processing_pipeline": self.processing_pipeline,
            "bidirectional_sync": self.bidirectional_sync.to_dict(),
            "custom_fields": self.custom_fields,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataMetadata":
        """Create from dictionary"""
        identifier = DataIdentifier.from_dict(data["data_flags"])
        sync = BidirectionalSync.from_dict(data.get("bidirectional_sync", {}))

        return cls(
            identifier=identifier,
            timestamp=data["timestamp"],
            source_repo=data["source_repo"],
            data_file=data["data_file"],
            description=data.get("description", ""),
            model_parameters=data.get("model_parameters", {}),
            processing_pipeline=data.get("processing_pipeline", []),
            bidirectional_sync=sync,
            custom_fields=data.get("custom_fields", {}),
        )

    def add_processing_step(self, step: str):
        """Add a processing step to the pipeline"""
        self.processing_pipeline.append({
            "step": step,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    def enable_bidirectional_sync(
        self,
        direction: str = "bidirectional",
        conflict_resolution: str = "manual"
    ):
        """Enable bidirectional synchronization"""
        self.bidirectional_sync.enabled = True
        self.bidirectional_sync.sync_direction = direction
        self.bidirectional_sync.conflict_resolution = conflict_resolution

    def mark_synced(self):
        """Mark data as successfully synced"""
        self.bidirectional_sync.last_sync = datetime.utcnow().isoformat() + "Z"
        self.bidirectional_sync.sync_status = "synced"


def create_metadata(
    identifier: DataIdentifier,
    data_file: str,
    source_repo: str = "Multi-Heart-Model",
    description: str = "",
    model_parameters: Optional[Dict[str, Any]] = None,
    enable_sync: bool = False,
    sync_direction: str = "bidirectional"
) -> DataMetadata:
    """
    Create a new metadata object with all required fields

    Args:
        identifier: DataIdentifier with all flags
        data_file: Path to the data file
        source_repo: Repository name (default: Multi-Heart-Model)
        description: Human-readable description
        model_parameters: Model configuration parameters
        enable_sync: Enable bidirectional sync
        sync_direction: Sync direction (to_quantro, from_quantro, bidirectional)

    Returns:
        DataMetadata object
    """
    timestamp = datetime.utcnow().isoformat() + "Z"

    metadata = DataMetadata(
        identifier=identifier,
        timestamp=timestamp,
        source_repo=source_repo,
        data_file=data_file,
        description=description,
        model_parameters=model_parameters or {},
    )

    if enable_sync:
        metadata.enable_bidirectional_sync(direction=sync_direction)

    return metadata


def validate_metadata(metadata: DataMetadata) -> tuple[bool, List[str]]:
    """
    Validate metadata completeness and correctness

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    # Required fields
    if not metadata.identifier.data_id:
        errors.append("Missing data_id")

    if not metadata.timestamp:
        errors.append("Missing timestamp")

    if not metadata.data_file:
        errors.append("Missing data_file")

    # Validate source type matches origin
    if metadata.identifier.is_simulated():
        if metadata.identifier.model_type is None:
            errors.append("Simulated data must specify model_type")

    if metadata.identifier.is_realworld():
        if metadata.identifier.model_type is not None:
            errors.append("Real-world data should not specify model_type")

    # Validate sync direction
    valid_directions = {"none", "to_quantro", "from_quantro", "bidirectional"}
    if metadata.bidirectional_sync.sync_direction not in valid_directions:
        errors.append(f"Invalid sync_direction: {metadata.bidirectional_sync.sync_direction}")

    return (len(errors) == 0, errors)


def save_metadata(metadata: DataMetadata, metadata_file: Path) -> bool:
    """
    Save metadata to JSON file

    Args:
        metadata: DataMetadata object
        metadata_file: Path to save metadata JSON

    Returns:
        True if successful
    """
    try:
        # Validate before saving
        is_valid, errors = validate_metadata(metadata)
        if not is_valid:
            print(f"Metadata validation errors: {errors}")
            return False

        # Ensure parent directory exists
        metadata_file.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON with pretty formatting
        with open(metadata_file, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)

        return True

    except Exception as e:
        print(f"Error saving metadata: {e}")
        return False


def load_metadata(metadata_file: Path) -> Optional[DataMetadata]:
    """
    Load metadata from JSON file

    Args:
        metadata_file: Path to metadata JSON file

    Returns:
        DataMetadata object or None if failed
    """
    try:
        with open(metadata_file, 'r') as f:
            data = json.load(f)

        metadata = DataMetadata.from_dict(data)

        # Validate loaded metadata
        is_valid, errors = validate_metadata(metadata)
        if not is_valid:
            print(f"Loaded metadata has validation errors: {errors}")
            return None

        return metadata

    except Exception as e:
        print(f"Error loading metadata: {e}")
        return None


def get_metadata_path(data_file: Path) -> Path:
    """
    Get the standard metadata file path for a data file

    Args:
        data_file: Path to data file

    Returns:
        Path to corresponding metadata JSON file
    """
    return data_file.parent / f"{data_file.stem}_metadata.json"
