# Cross-Repository Collaboration Guide

## Overview

This repository is configured for **cross-repository collaboration** with **Quantro-Heart-Heart**, enabling bidirectional data flow between computational simulations (Multi-Heart-Model) and real-world physiological measurements (Quantro-Heart-Heart).

## Git Remote Configuration

The Quantro-Heart-Heart repository is added as a git remote named `quantro-heart`:

```bash
# View all remotes
git remote -v

# Fetch from Quantro-Heart-Heart
git fetch quantro-heart

# View branches from Quantro-Heart-Heart
git branch -r | grep quantro-heart
```

**Remote URLs:**
- **origin** (Multi-Heart-Model): `http://local_proxy@127.0.0.1:35344/git/STLNFTART/Multi-Heart-Model`
- **quantro-heart** (Quantro-Heart-Heart): `http://local_proxy@127.0.0.1:35344/git/STLNFTART/Quantro-Heart-Heart`

## Data Separation Architecture

### Directory Structure

All data is organized with **clear separation** between simulated and real-world data:

```
data/
├── simulated/              # Computational simulation data
│   ├── raw/               # Raw simulation outputs
│   ├── processed/         # Post-processed simulation data
│   └── results/           # Final simulation results
├── realworld/             # Real-world measurement data
│   ├── raw/               # Raw device/clinical measurements
│   ├── processed/         # Cleaned real-world data
│   └── results/           # Final real-world analysis results
├── exchange/              # Bidirectional data flow staging
│   ├── to_quantro/        # Outgoing to Quantro-Heart-Heart
│   └── from_quantro/      # Incoming from Quantro-Heart-Heart
└── archive/               # Historical/archived datasets
```

See [data/DATA_STRUCTURE.md](../data/DATA_STRUCTURE.md) for complete documentation.

## Data Identifier Flags

Every dataset must be tagged with **identifier flags** to ensure clear separation:

### Simulated Data Identifiers

```python
from src.data_management import (
    create_simulated_identifier,
    ModelType,
    DataCategory,
    DataQuality
)

identifier = create_simulated_identifier(
    data_id="run_001",
    model_type=ModelType.HBCM,
    category=DataCategory.COUPLED,
    quality=DataQuality.PROCESSED,
    version="1.0.0"
)
```

**Flags:**
- `source_type`: `SIMULATED`
- `origin`: `HBCM_SIMULATION` or `MULTI_HEART_MODEL`
- `model_type`: `HBCM`, `FITZHUGH_NAGUMO`, `VAN_DER_POL`, etc.
- `category`: `CARDIAC`, `NEURAL`, `COUPLED`
- `quality`: `RAW`, `PROCESSED`, `VALIDATED`, `ANALYZED`

### Real-World Data Identifiers

```python
from src.data_management import (
    create_realworld_identifier,
    DataOrigin,
    DataCategory,
    DataQuality
)

identifier = create_realworld_identifier(
    data_id="patient_001_ecg",
    origin=DataOrigin.QUANTRO,
    category=DataCategory.ECG,
    quality=DataQuality.VALIDATED,
    version="1.0.0"
)
```

**Flags:**
- `source_type`: `REALWORLD`
- `origin`: `QUANTRO`, `CLINICAL`, `ECG_DEVICE`, `EEG_DEVICE`, `WEARABLE_SENSOR`, etc.
- `category`: `CARDIAC`, `NEURAL`, `ECG`, `EEG`, `HRV`
- `quality`: `RAW`, `PROCESSED`, `VALIDATED`, `CLEANED`

## Metadata Schema

Every data file must have an accompanying metadata JSON file:

```json
{
  "data_id": "run_001",
  "source_type": "SIMULATED",
  "source_repo": "Multi-Heart-Model",
  "timestamp": "2025-11-11T14:30:25Z",
  "data_file": "sim_coupled_hbcm_run_001.csv",
  "description": "HBCM simulation with default coupling parameters",
  "data_flags": {
    "data_id": "run_001",
    "source_type": "SIMULATED",
    "origin": "HBCM_SIMULATION",
    "quality": "PROCESSED",
    "category": "COUPLED",
    "model_type": "HBCM",
    "version": "1.0.0"
  },
  "model_parameters": {
    "neural_freq": 0.1,
    "cardiac_freq": 1.0,
    "coupling_strength": 0.5,
    "simulation_time": 100.0
  },
  "processing_pipeline": [
    {
      "step": "Raw simulation completed",
      "timestamp": "2025-11-11T14:30:25Z"
    },
    {
      "step": "Noise filtering applied",
      "timestamp": "2025-11-11T14:31:10Z"
    }
  ],
  "bidirectional_sync": {
    "enabled": true,
    "last_sync": "2025-11-11T14:32:00Z",
    "sync_direction": "to_quantro",
    "sync_status": "synced",
    "conflict_resolution": "manual"
  }
}
```

## Bidirectional Data Flow

### Configuration

Data exchange is configured in `config/data_exchange.yaml`:

- **Auto-sync**: Disabled by default (manual sync for safety)
- **Conflict resolution**: Manual by default
- **Sync directions**: `to_quantro`, `from_quantro`, `bidirectional`

### Using the Data Exchange CLI

The repository includes a CLI utility for managing data exchange:

```bash
# Check exchange status
python scripts/data_exchange_cli.py status

# Create metadata for a data file
python scripts/data_exchange_cli.py create-metadata \
    data/simulated/results/my_simulation.csv \
    --type simulated \
    --model-type HBCM \
    --category COUPLED \
    --enable-sync

# Export data to Quantro-Heart-Heart
python scripts/data_exchange_cli.py export \
    data/simulated/results/my_simulation.csv \
    --description "Coupling strength analysis results"

# Import data from Quantro-Heart-Heart (validate first)
python scripts/data_exchange_cli.py import --validate-only

# Actually import
python scripts/data_exchange_cli.py import

# Bidirectional sync (dry run first)
python scripts/data_exchange_cli.py sync --dry-run

# Perform actual sync
python scripts/data_exchange_cli.py sync
```

### Programmatic API

You can also use the Python API directly:

```python
from pathlib import Path
from src.data_management import (
    create_simulated_identifier,
    create_metadata,
    prepare_for_export,
    import_from_quantro,
    sync_bidirectional,
    ModelType,
    DataCategory,
    DataQuality,
)

# Create identifier
identifier = create_simulated_identifier(
    data_id="experiment_001",
    model_type=ModelType.HBCM,
    category=DataCategory.COUPLED,
    quality=DataQuality.PROCESSED
)

# Create metadata
metadata = create_metadata(
    identifier=identifier,
    data_file="experiment_001.csv",
    description="HBCM coupling strength sweep",
    enable_sync=True,
    sync_direction="to_quantro"
)

# Export to Quantro-Heart-Heart
data_file = Path("data/simulated/results/experiment_001.csv")
success, message = prepare_for_export(data_file, metadata, "Experimental results")
print(message)

# Import from Quantro-Heart-Heart
results = import_from_quantro(validate_only=False)
for success, message, file_path in results:
    print(f"{'✓' if success else '✗'} {message}")

# Bidirectional sync
stats = sync_bidirectional(dry_run=False)
print(f"Synced {len(stats['outgoing'])} outgoing, {len(stats['incoming'])} incoming")
```

## File Naming Conventions

### Simulated Data

**Pattern:** `sim_{category}_{model}_{data_id}_{timestamp}.{ext}`

**Examples:**
- `sim_coupled_hbcm_run001_20251111_143025.csv`
- `sim_cardiac_vanderpol_sweep01_20251111_150000.json`
- `sim_neural_fhn_baseline_20251111_160000.npy`

### Real-World Data

**Pattern:** `real_{origin}_{category}_{data_id}_{timestamp}.{ext}`

**Examples:**
- `real_quantro_ecg_patient001_20251111_143025.csv`
- `real_clinical_hrv_study01_20251111_150000.csv`
- `real_device_eeg_session01_20251111_160000.edf`

### Exchange Data

**Pattern:** `exchange_{direction}_{timestamp}_{identifier}.{ext}`

**Examples:**
- `exchange_to_quantro_20251111_143025_dataset001.json`
- `exchange_from_quantro_20251111_150000_measurements.csv`

## Workflow Examples

### Example 1: Export Simulation Results to Quantro-Heart-Heart

```bash
# 1. Run simulation
python -m src.coupling.hbcm_simulation --output data/simulated/results/coupling_test.csv

# 2. Create metadata
python scripts/data_exchange_cli.py create-metadata \
    data/simulated/results/coupling_test.csv \
    --type simulated \
    --model-type HBCM \
    --category COUPLED \
    --description "Heart-brain coupling strength test" \
    --enable-sync

# 3. Export to Quantro-Heart-Heart
python scripts/data_exchange_cli.py export \
    data/simulated/results/coupling_test.csv \
    --description "For validation against real-world measurements"

# 4. Check status
python scripts/data_exchange_cli.py status
```

### Example 2: Import Real-World Data from Quantro-Heart-Heart

Assuming Quantro-Heart-Heart has placed data files in the shared exchange location:

```bash
# 1. Check what's available
python scripts/data_exchange_cli.py status

# 2. Validate import (dry run)
python scripts/data_exchange_cli.py import --validate-only

# 3. Perform import
python scripts/data_exchange_cli.py import

# 4. Verify imported data
ls -l data/realworld/results/
```

### Example 3: Bidirectional Sync

```bash
# 1. Check sync status (dry run)
python scripts/data_exchange_cli.py sync --dry-run

# 2. Perform sync
python scripts/data_exchange_cli.py sync

# 3. Verify results
python scripts/data_exchange_cli.py status
```

## Data Validation

All imports are validated against the metadata schema:

1. **Required fields check**: Ensures all mandatory metadata fields are present
2. **Source type validation**: Verifies simulated data has model_type, real-world data doesn't
3. **Origin validation**: Checks origin matches source type
4. **Quality level check**: Validates data quality indicators
5. **File existence**: Confirms referenced data files exist

Failed validations are logged and files are quarantined for manual review.

## Conflict Resolution

When conflicts occur during bidirectional sync:

- **Manual** (default): Human review required
- **Latest wins**: Most recent timestamp wins
- **Merge**: Attempt automatic merge (requires custom merge logic)

Configure in `config/data_exchange.yaml`:

```yaml
sync:
  conflict_resolution: "manual"  # or "latest_wins", "merge"
```

## Security and Best Practices

1. **Always validate imports** before accepting data from external sources
2. **Review metadata** to ensure proper data classification
3. **Use dry-run mode** for sync operations before committing
4. **Maintain separation** between simulated and real-world data directories
5. **Document processing steps** in metadata pipeline
6. **Archive old data** regularly to keep working directories clean
7. **Never commit sensitive data** (PHI, PII) without proper de-identification

## Troubleshooting

### Missing Metadata

```bash
# Create metadata for existing data file
python scripts/data_exchange_cli.py create-metadata \
    path/to/datafile.csv \
    --type simulated \
    --model-type HBCM \
    --category COUPLED
```

### Import Validation Failures

Check the error messages from validation and ensure:
- Metadata JSON is well-formed
- All required fields are present
- Source type and origin are consistent
- Data file exists and is accessible

### Sync Conflicts

Review conflict details in sync output:

```bash
python scripts/data_exchange_cli.py sync --dry-run
```

Resolve manually by examining the conflicting files and their metadata.

## Further Documentation

- [Data Structure Documentation](../data/DATA_STRUCTURE.md) - Complete data directory layout
- [Python API Documentation](../src/data_management/README.md) - API reference
- [Configuration Guide](../config/data_exchange.yaml) - Full configuration options

## Support

For issues or questions:
1. Check this documentation
2. Review metadata and data structure documentation
3. Examine log files in `logs/data_exchange.log`
4. Consult the repository maintainers
