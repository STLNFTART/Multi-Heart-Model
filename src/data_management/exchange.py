"""
Data Exchange Utilities for Bidirectional Data Flow

Handles data exchange between Multi-Heart-Model and Quantro-Heart-Heart repositories.
"""

import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
import json

from .metadata import DataMetadata, load_metadata, save_metadata, get_metadata_path
from .identifiers import DataSourceType, DataOrigin


# Standard data paths
DATA_ROOT = Path(__file__).parent.parent.parent / "data"
EXCHANGE_TO_QUANTRO = DATA_ROOT / "exchange" / "to_quantro"
EXCHANGE_FROM_QUANTRO = DATA_ROOT / "exchange" / "from_quantro"
SIMULATED_RESULTS = DATA_ROOT / "simulated" / "results"
REALWORLD_RESULTS = DATA_ROOT / "realworld" / "results"


class DataExchange:
    """
    Manages bidirectional data exchange between repositories
    """

    def __init__(self, data_root: Optional[Path] = None):
        self.data_root = data_root or DATA_ROOT
        self.to_quantro = self.data_root / "exchange" / "to_quantro"
        self.from_quantro = self.data_root / "exchange" / "from_quantro"
        self.simulated_results = self.data_root / "simulated" / "results"
        self.realworld_results = self.data_root / "realworld" / "results"

        # Ensure directories exist
        for directory in [self.to_quantro, self.from_quantro,
                         self.simulated_results, self.realworld_results]:
            directory.mkdir(parents=True, exist_ok=True)

    def prepare_for_export(
        self,
        data_file: Path,
        metadata: DataMetadata,
        description: str = ""
    ) -> Tuple[bool, str]:
        """
        Prepare a dataset for export to Quantro-Heart-Heart

        Args:
            data_file: Path to data file
            metadata: Associated metadata
            description: Export description

        Returns:
            (success, message)
        """
        try:
            if not data_file.exists():
                return False, f"Data file not found: {data_file}"

            # Enable bidirectional sync for export
            if not metadata.bidirectional_sync.enabled:
                metadata.enable_bidirectional_sync(direction="to_quantro")

            # Generate export filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            export_name = f"export_{timestamp}_{data_file.name}"
            export_file = self.to_quantro / export_name
            export_metadata = self.to_quantro / f"{export_file.stem}_metadata.json"

            # Copy data file
            shutil.copy2(data_file, export_file)

            # Update and save metadata
            metadata.add_processing_step(f"Prepared for export to Quantro-Heart-Heart: {description}")
            metadata.data_file = export_name

            if not save_metadata(metadata, export_metadata):
                return False, "Failed to save export metadata"

            # Create export manifest
            manifest = {
                "export_timestamp": timestamp,
                "source_file": str(data_file),
                "export_file": export_name,
                "description": description,
                "data_id": metadata.identifier.data_id,
                "source_type": metadata.identifier.source_type.value,
            }

            manifest_file = self.to_quantro / f"manifest_{timestamp}.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)

            return True, f"Data prepared for export: {export_file}"

        except Exception as e:
            return False, f"Export preparation failed: {e}"

    def import_from_quantro(
        self,
        validate_only: bool = False
    ) -> List[Tuple[bool, str, Optional[Path]]]:
        """
        Import datasets from Quantro-Heart-Heart

        Args:
            validate_only: Only validate, don't actually import

        Returns:
            List of (success, message, imported_file_path) tuples
        """
        results = []

        # Find all data files in from_quantro directory
        data_files = [
            f for f in self.from_quantro.iterdir()
            if f.is_file() and not f.name.endswith('_metadata.json')
            and not f.name.startswith('manifest_')
            and not f.name == '.gitkeep'
        ]

        if not data_files:
            results.append((True, "No files to import", None))
            return results

        for data_file in data_files:
            try:
                # Load metadata
                metadata_file = get_metadata_path(data_file)
                if not metadata_file.exists():
                    results.append((
                        False,
                        f"Missing metadata for {data_file.name}",
                        None
                    ))
                    continue

                metadata = load_metadata(metadata_file)
                if metadata is None:
                    results.append((
                        False,
                        f"Invalid metadata for {data_file.name}",
                        None
                    ))
                    continue

                # Determine destination based on source type
                if metadata.identifier.is_simulated():
                    dest_dir = self.simulated_results
                else:
                    dest_dir = self.realworld_results

                dest_file = dest_dir / data_file.name
                dest_metadata = get_metadata_path(dest_file)

                if validate_only:
                    results.append((
                        True,
                        f"Validation passed: {data_file.name} -> {dest_dir.name}/",
                        None
                    ))
                    continue

                # Copy files to destination
                shutil.copy2(data_file, dest_file)

                # Update metadata
                metadata.add_processing_step("Imported from Quantro-Heart-Heart")
                metadata.mark_synced()
                save_metadata(metadata, dest_metadata)

                # Archive original files (don't delete, for safety)
                archive_dir = self.from_quantro / "imported"
                archive_dir.mkdir(exist_ok=True)
                shutil.move(str(data_file), str(archive_dir / data_file.name))
                shutil.move(str(metadata_file), str(archive_dir / metadata_file.name))

                results.append((
                    True,
                    f"Imported: {data_file.name} -> {dest_dir.name}/",
                    dest_file
                ))

            except Exception as e:
                results.append((
                    False,
                    f"Import failed for {data_file.name}: {e}",
                    None
                ))

        return results

    def sync_bidirectional(
        self,
        dry_run: bool = False
    ) -> dict:
        """
        Perform bidirectional sync with Quantro-Heart-Heart

        Args:
            dry_run: Only check what would be synced, don't actually sync

        Returns:
            Dictionary with sync statistics and results
        """
        stats = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dry_run": dry_run,
            "outgoing": [],
            "incoming": [],
            "conflicts": [],
            "errors": [],
        }

        # Find files marked for bidirectional sync in results directories
        for results_dir in [self.simulated_results, self.realworld_results]:
            if not results_dir.exists():
                continue

            for metadata_file in results_dir.glob("*_metadata.json"):
                try:
                    metadata = load_metadata(metadata_file)
                    if metadata is None:
                        continue

                    # Check if bidirectional sync is enabled
                    if not metadata.bidirectional_sync.enabled:
                        continue

                    sync_dir = metadata.bidirectional_sync.sync_direction
                    if sync_dir in ["to_quantro", "bidirectional"]:
                        data_file = results_dir / metadata.data_file
                        if data_file.exists():
                            if not dry_run:
                                success, msg = self.prepare_for_export(
                                    data_file, metadata,
                                    "Bidirectional sync"
                                )
                                stats["outgoing"].append({
                                    "file": metadata.data_file,
                                    "success": success,
                                    "message": msg
                                })
                            else:
                                stats["outgoing"].append({
                                    "file": metadata.data_file,
                                    "would_sync": True
                                })

                except Exception as e:
                    stats["errors"].append({
                        "file": str(metadata_file),
                        "error": str(e)
                    })

        # Import incoming data
        if not dry_run:
            import_results = self.import_from_quantro(validate_only=False)
        else:
            import_results = self.import_from_quantro(validate_only=True)

        for success, message, file_path in import_results:
            stats["incoming"].append({
                "success": success,
                "message": message,
                "file": str(file_path) if file_path else None
            })

        return stats

    def get_exchange_status(self) -> dict:
        """
        Get current status of exchange directories

        Returns:
            Dictionary with counts and file lists
        """
        def count_files(directory: Path) -> Tuple[int, List[str]]:
            if not directory.exists():
                return 0, []
            files = [
                f.name for f in directory.iterdir()
                if f.is_file() and f.name != '.gitkeep'
            ]
            return len(files), files

        to_count, to_files = count_files(self.to_quantro)
        from_count, from_files = count_files(self.from_quantro)

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "to_quantro": {
                "count": to_count,
                "files": to_files
            },
            "from_quantro": {
                "count": from_count,
                "files": from_files
            }
        }


def prepare_for_export(
    data_file: Path,
    metadata: DataMetadata,
    description: str = ""
) -> Tuple[bool, str]:
    """
    Convenience function to prepare a dataset for export

    Args:
        data_file: Path to data file
        metadata: Associated metadata
        description: Export description

    Returns:
        (success, message)
    """
    exchange = DataExchange()
    return exchange.prepare_for_export(data_file, metadata, description)


def import_from_quantro(validate_only: bool = False) -> List[Tuple[bool, str, Optional[Path]]]:
    """
    Convenience function to import from Quantro-Heart-Heart

    Args:
        validate_only: Only validate, don't actually import

    Returns:
        List of (success, message, imported_file_path) tuples
    """
    exchange = DataExchange()
    return exchange.import_from_quantro(validate_only)


def sync_bidirectional(dry_run: bool = False) -> dict:
    """
    Convenience function for bidirectional sync

    Args:
        dry_run: Only check what would be synced

    Returns:
        Dictionary with sync statistics
    """
    exchange = DataExchange()
    return exchange.sync_bidirectional(dry_run)
