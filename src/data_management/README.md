# Data Management Module

Python module for managing data identification, metadata, and bidirectional data flow between Multi-Heart-Model and Quantro-Heart-Heart repositories.

## Features

- **Data Identifiers**: Clear separation between simulated and real-world data with comprehensive flags
- **Metadata Management**: Structured metadata schema with validation
- **Bidirectional Sync**: Tools for exchanging data between repositories
- **Type Safety**: Enums and dataclasses for type-safe data handling

## Module Structure

```
data_management/
├── __init__.py        # Module exports
├── identifiers.py     # Data identifier flags and types
├── metadata.py        # Metadata schema and management
└── exchange.py        # Bidirectional data exchange utilities
```

## Quick Start

### Creating Data Identifiers

```python
from src.data_management import (
    create_simulated_identifier,
    create_realworld_identifier,
    ModelType,
    DataCategory,
    DataOrigin,
    DataQuality,
)

# Simulated data identifier
sim_id = create_simulated_identifier(
    data_id="experiment_001",
    model_type=ModelType.HBCM,
    category=DataCategory.COUPLED,
    quality=DataQuality.PROCESSED,
)

# Real-world data identifier
real_id = create_realworld_identifier(
    data_id="patient_001_ecg",
    origin=DataOrigin.QUANTRO,
    category=DataCategory.ECG,
    quality=DataQuality.VALIDATED,
)
```

### Creating and Saving Metadata

```python
from pathlib import Path
from src.data_management import (
    create_metadata,
    save_metadata,
    get_metadata_path,
)

# Create metadata
metadata = create_metadata(
    identifier=sim_id,
    data_file="experiment_001.csv",
    description="HBCM simulation with varying coupling strength",
    model_parameters={
        "coupling_strength": 0.5,
        "simulation_time": 100.0,
    },
    enable_sync=True,
    sync_direction="to_quantro",
)

# Save metadata
data_file = Path("data/simulated/results/experiment_001.csv")
metadata_file = get_metadata_path(data_file)
save_metadata(metadata, metadata_file)
```

### Loading Metadata

```python
from src.data_management import load_metadata

metadata = load_metadata(metadata_file)
if metadata:
    print(f"Loaded: {metadata.identifier.data_id}")
    print(f"Source: {metadata.identifier.source_type.value}")
```

### Exporting Data

```python
from src.data_management import prepare_for_export

success, message = prepare_for_export(
    data_file=Path("data/simulated/results/experiment_001.csv"),
    metadata=metadata,
    description="Experimental results for validation",
)
print(message)
```

### Importing Data

```python
from src.data_management import import_from_quantro

# Validate first
results = import_from_quantro(validate_only=True)
for success, message, _ in results:
    print(f"{'✓' if success else '✗'} {message}")

# Actually import
results = import_from_quantro(validate_only=False)
```

### Bidirectional Sync

```python
from src.data_management import sync_bidirectional

# Dry run
stats = sync_bidirectional(dry_run=True)
print(f"Would sync: {len(stats['outgoing'])} outgoing, {len(stats['incoming'])} incoming")

# Actual sync
stats = sync_bidirectional(dry_run=False)
```

## API Reference

### Identifiers Module (`identifiers.py`)

#### Enums

- `DataSourceType`: `SIMULATED`, `REALWORLD`
- `DataOrigin`: `HBCM_SIMULATION`, `QUANTRO`, `CLINICAL`, `ECG_DEVICE`, etc.
- `DataQuality`: `RAW`, `PROCESSED`, `VALIDATED`, `CLEANED`, `ANALYZED`
- `ModelType`: `HBCM`, `FITZHUGH_NAGUMO`, `VAN_DER_POL`, `COUPLED_OSCILLATOR`
- `DataCategory`: `CARDIAC`, `NEURAL`, `COUPLED`, `ECG`, `EEG`, `HRV`, `BRAIN_ACTIVITY`

#### Classes

**`DataIdentifier`**

Complete data identifier with all flags.

Properties:
- `data_id: str`
- `source_type: DataSourceType`
- `origin: DataOrigin`
- `quality: DataQuality`
- `category: DataCategory`
- `model_type: Optional[ModelType]`
- `version: str`

Methods:
- `is_simulated() -> bool`: Check if simulated data
- `is_realworld() -> bool`: Check if real-world data
- `to_dict() -> dict`: Convert to dictionary
- `from_dict(data: dict) -> DataIdentifier`: Create from dictionary
- `generate_filename(extension: str) -> str`: Generate standardized filename

#### Functions

- `create_simulated_identifier(...)`: Create identifier for simulated data
- `create_realworld_identifier(...)`: Create identifier for real-world data

### Metadata Module (`metadata.py`)

#### Classes

**`BidirectionalSync`**

Bidirectional synchronization metadata.

Properties:
- `enabled: bool`
- `last_sync: Optional[str]`
- `sync_direction: str` ("to_quantro", "from_quantro", "bidirectional")
- `sync_status: str` ("pending", "synced", "conflict", "failed")
- `conflict_resolution: str` ("manual", "latest_wins", "merge")

**`DataMetadata`**

Complete metadata schema.

Properties:
- `identifier: DataIdentifier`
- `timestamp: str`
- `source_repo: str`
- `data_file: str`
- `description: str`
- `model_parameters: Dict[str, Any]`
- `processing_pipeline: List[str]`
- `bidirectional_sync: BidirectionalSync`
- `custom_fields: Dict[str, Any]`

Methods:
- `add_processing_step(step: str)`: Add processing step
- `enable_bidirectional_sync(direction: str, conflict_resolution: str)`: Enable sync
- `mark_synced()`: Mark as successfully synced
- `to_dict() -> dict`: Convert to dictionary
- `from_dict(data: dict) -> DataMetadata`: Create from dictionary

#### Functions

- `create_metadata(...)`: Create new metadata object
- `validate_metadata(metadata: DataMetadata) -> tuple[bool, List[str]]`: Validate metadata
- `save_metadata(metadata: DataMetadata, metadata_file: Path) -> bool`: Save to JSON
- `load_metadata(metadata_file: Path) -> Optional[DataMetadata]`: Load from JSON
- `get_metadata_path(data_file: Path) -> Path`: Get metadata file path

### Exchange Module (`exchange.py`)

#### Classes

**`DataExchange`**

Manages bidirectional data exchange.

Methods:
- `prepare_for_export(data_file: Path, metadata: DataMetadata, description: str) -> Tuple[bool, str]`
- `import_from_quantro(validate_only: bool) -> List[Tuple[bool, str, Optional[Path]]]`
- `sync_bidirectional(dry_run: bool) -> dict`
- `get_exchange_status() -> dict`

#### Functions

- `prepare_for_export(...)`: Convenience function for export
- `import_from_quantro(...)`: Convenience function for import
- `sync_bidirectional(...)`: Convenience function for sync

## CLI Tool

Command-line interface at `scripts/data_exchange_cli.py`:

```bash
# Show status
python scripts/data_exchange_cli.py status

# Create metadata
python scripts/data_exchange_cli.py create-metadata <file> --type simulated|realworld

# Export data
python scripts/data_exchange_cli.py export <file> --description "..."

# Import data
python scripts/data_exchange_cli.py import [--validate-only]

# Sync
python scripts/data_exchange_cli.py sync [--dry-run]
```

## Documentation

- [Cross-Repository Collaboration Guide](../../docs/cross_repo_collaboration.md) - Complete guide
- [Data Structure Documentation](../../data/DATA_STRUCTURE.md) - Data organization
- [Configuration Guide](../../config/data_exchange.yaml) - Configuration options

## Examples

See the [Cross-Repository Collaboration Guide](../../docs/cross_repo_collaboration.md) for complete workflow examples.
