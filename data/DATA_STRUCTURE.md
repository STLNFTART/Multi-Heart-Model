# Data Structure Documentation

This directory contains all data for the Multi-Heart-Model project, with clear separation between simulated and real-world data.

## Directory Structure

```
data/
├── simulated/          # Simulation-generated data (computational models)
│   ├── raw/           # Raw simulation outputs
│   ├── processed/     # Post-processed simulation data
│   └── results/       # Final simulation results ready for analysis
├── realworld/         # Real-world experimental/clinical data
│   ├── raw/           # Raw measurement data from physical devices
│   ├── processed/     # Cleaned and preprocessed real-world data
│   └── results/       # Final real-world analysis results
├── exchange/          # Bidirectional data flow with Quantro-Heart-Heart
│   ├── to_quantro/    # Outgoing data to Quantro-Heart-Heart repository
│   └── from_quantro/  # Incoming data from Quantro-Heart-Heart repository
└── archive/           # Historical/archived datasets
```

## Data Type Identifiers

All data files must include appropriate identifier flags in their metadata:

### Simulated Data Flags
- **Source**: `SIMULATED`
- **Model**: `HBCM` (Heart-Brain Coupling Model)
- **Generator**: `Multi-Heart-Model`
- **Version**: Model version (e.g., `v1.0.0`)

### Real-World Data Flags
- **Source**: `REALWORLD`
- **Origin**: `QUANTRO` or specific device/institution name
- **Type**: `CLINICAL`, `EXPERIMENTAL`, `DEVICE_MEASUREMENT`
- **Quality**: Data quality indicator (`RAW`, `VALIDATED`, `PROCESSED`)

## File Naming Conventions

### Simulated Data
```
sim_<model>_<timestamp>_<identifier>.<ext>
Example: sim_hbcm_20251111_143025_run001.csv
```

### Real-World Data
```
real_<source>_<timestamp>_<identifier>.<ext>
Example: real_quantro_20251111_143025_ecg001.csv
```

### Exchange Data
```
exchange_<direction>_<timestamp>_<identifier>.<ext>
Example: exchange_to_quantro_20251111_143025_dataset001.json
```

## Metadata Schema

All datasets should include a companion JSON metadata file with the following structure:

```json
{
  "data_id": "unique-identifier",
  "source_type": "SIMULATED | REALWORLD",
  "source_repo": "Multi-Heart-Model | Quantro-Heart-Heart",
  "timestamp": "ISO-8601 timestamp",
  "data_flags": {
    "origin": "simulation | device | clinical",
    "quality": "raw | processed | validated",
    "version": "semantic version"
  },
  "model_parameters": {},
  "processing_pipeline": [],
  "bidirectional_sync": {
    "enabled": true,
    "last_sync": "ISO-8601 timestamp",
    "sync_direction": "to_quantro | from_quantro | bidirectional"
  }
}
```

## Cross-Repository Collaboration

This repository is linked to **Quantro-Heart-Heart** via git remote for cross-repository collaboration:

```bash
git remote: quantro-heart
URL: http://local_proxy@127.0.0.1:35344/git/STLNFTART/Quantro-Heart-Heart
```

### Data Exchange Protocol

1. **Outgoing Data (to Quantro-Heart-Heart)**:
   - Place data files in `exchange/to_quantro/`
   - Include metadata JSON file
   - Use data sync utility to transfer

2. **Incoming Data (from Quantro-Heart-Heart)**:
   - Received data appears in `exchange/from_quantro/`
   - Validate metadata and flags
   - Move to appropriate simulated/ or realworld/ directory after validation

3. **Bidirectional Sync**:
   - Automated sync checks metadata `bidirectional_sync` flags
   - Only files marked for sync are transferred
   - Maintains synchronization logs in exchange directory

## Best Practices

1. **Always include metadata** with every dataset
2. **Use clear identifiers** to distinguish simulated vs real-world data
3. **Document processing steps** in metadata pipeline field
4. **Validate data** before moving from exchange to main directories
5. **Archive old data** regularly to keep working directories clean
6. **Maintain separation** between simulated and real-world data at all times
