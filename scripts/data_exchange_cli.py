#!/usr/bin/env python3
"""
Data Exchange CLI Utility

Command-line interface for managing bidirectional data flow between
Multi-Heart-Model and Quantro-Heart-Heart repositories.

Usage:
    python data_exchange_cli.py status
    python data_exchange_cli.py export <data_file> --description "Export description"
    python data_exchange_cli.py import [--validate-only]
    python data_exchange_cli.py sync [--dry-run]
    python data_exchange_cli.py create-metadata <data_file> --type simulated|realworld
"""

import sys
import argparse
from pathlib import Path
import json

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_management import (
    DataIdentifier,
    DataMetadata,
    create_metadata,
    create_simulated_identifier,
    create_realworld_identifier,
    save_metadata,
    load_metadata,
    get_metadata_path,
    DataExchange,
    prepare_for_export,
    import_from_quantro,
    sync_bidirectional,
    DataSourceType,
    DataOrigin,
    DataQuality,
    DataCategory,
    ModelType,
)


def cmd_status(args):
    """Show exchange directory status"""
    exchange = DataExchange()
    status = exchange.get_exchange_status()

    print("\n=== Data Exchange Status ===")
    print(f"Timestamp: {status['timestamp']}\n")

    print(f"Outgoing (to Quantro-Heart-Heart):")
    print(f"  Count: {status['to_quantro']['count']}")
    if status['to_quantro']['files']:
        for file in status['to_quantro']['files']:
            print(f"    - {file}")
    else:
        print("    (none)")

    print(f"\nIncoming (from Quantro-Heart-Heart):")
    print(f"  Count: {status['from_quantro']['count']}")
    if status['from_quantro']['files']:
        for file in status['from_quantro']['files']:
            print(f"    - {file}")
    else:
        print("    (none)")

    print()


def cmd_export(args):
    """Export data to Quantro-Heart-Heart"""
    data_file = Path(args.data_file)

    if not data_file.exists():
        print(f"Error: Data file not found: {data_file}")
        return 1

    # Load or prompt for metadata
    metadata_file = get_metadata_path(data_file)

    if metadata_file.exists():
        print(f"Loading existing metadata from {metadata_file}")
        metadata = load_metadata(metadata_file)
        if metadata is None:
            print("Error: Failed to load metadata")
            return 1
    else:
        print("No metadata found. Please create metadata first using 'create-metadata' command.")
        return 1

    # Prepare for export
    success, message = prepare_for_export(
        data_file,
        metadata,
        args.description or "Manual export"
    )

    if success:
        print(f"✓ {message}")
        return 0
    else:
        print(f"✗ {message}")
        return 1


def cmd_import(args):
    """Import data from Quantro-Heart-Heart"""
    results = import_from_quantro(validate_only=args.validate_only)

    if args.validate_only:
        print("\n=== Import Validation ===")
    else:
        print("\n=== Import Results ===")

    for success, message, file_path in results:
        status = "✓" if success else "✗"
        print(f"{status} {message}")

    print()

    # Count successes and failures
    successes = sum(1 for s, _, _ in results if s)
    failures = sum(1 for s, _, _ in results if not s)

    print(f"Summary: {successes} succeeded, {failures} failed")

    return 0 if failures == 0 else 1


def cmd_sync(args):
    """Perform bidirectional sync"""
    print(f"\n=== Bidirectional Sync {'(DRY RUN)' if args.dry_run else ''} ===\n")

    stats = sync_bidirectional(dry_run=args.dry_run)

    print(f"Timestamp: {stats['timestamp']}")
    print(f"Dry run: {stats['dry_run']}\n")

    print(f"Outgoing ({len(stats['outgoing'])} items):")
    for item in stats['outgoing']:
        if args.dry_run:
            print(f"  - {item['file']} (would sync)")
        else:
            status = "✓" if item['success'] else "✗"
            print(f"  {status} {item['file']}: {item['message']}")

    print(f"\nIncoming ({len(stats['incoming'])} items):")
    for item in stats['incoming']:
        status = "✓" if item['success'] else "✗"
        print(f"  {status} {item['message']}")

    if stats['errors']:
        print(f"\nErrors ({len(stats['errors'])} items):")
        for error in stats['errors']:
            print(f"  ✗ {error['file']}: {error['error']}")

    print()
    return 0


def cmd_create_metadata(args):
    """Create metadata for a data file"""
    data_file = Path(args.data_file)

    if not data_file.exists():
        print(f"Error: Data file not found: {data_file}")
        return 1

    # Determine data type
    if args.type == "simulated":
        # Get model type
        model_type_str = args.model_type or input("Model type (HBCM/FITZHUGH_NAGUMO/VAN_DER_POL): ").upper()
        try:
            model_type = ModelType[model_type_str]
        except KeyError:
            print(f"Invalid model type: {model_type_str}")
            return 1

        # Get category
        category_str = args.category or input("Category (CARDIAC/NEURAL/COUPLED): ").upper()
        try:
            category = DataCategory[category_str]
        except KeyError:
            print(f"Invalid category: {category_str}")
            return 1

        identifier = create_simulated_identifier(
            data_id=args.data_id or data_file.stem,
            model_type=model_type,
            category=category,
            quality=DataQuality.RAW,
        )

    elif args.type == "realworld":
        # Get origin
        origin_str = args.origin or input("Origin (QUANTRO/CLINICAL/DEVICE_MEASUREMENT): ").upper()
        try:
            origin = DataOrigin[origin_str]
        except KeyError:
            print(f"Invalid origin: {origin_str}")
            return 1

        # Get category
        category_str = args.category or input("Category (CARDIAC/NEURAL/ECG/EEG): ").upper()
        try:
            category = DataCategory[category_str]
        except KeyError:
            print(f"Invalid category: {category_str}")
            return 1

        identifier = create_realworld_identifier(
            data_id=args.data_id or data_file.stem,
            origin=origin,
            category=category,
            quality=DataQuality.RAW,
        )

    else:
        print(f"Invalid type: {args.type}. Must be 'simulated' or 'realworld'")
        return 1

    # Create metadata
    metadata = create_metadata(
        identifier=identifier,
        data_file=data_file.name,
        description=args.description or "",
        enable_sync=args.enable_sync,
    )

    # Save metadata
    metadata_file = get_metadata_path(data_file)
    if save_metadata(metadata, metadata_file):
        print(f"✓ Metadata created: {metadata_file}")
        return 0
    else:
        print(f"✗ Failed to create metadata")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Data Exchange CLI for Multi-Heart-Model ↔ Quantro-Heart-Heart"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    parser_status = subparsers.add_parser("status", help="Show exchange directory status")
    parser_status.set_defaults(func=cmd_status)

    # Export command
    parser_export = subparsers.add_parser("export", help="Export data to Quantro-Heart-Heart")
    parser_export.add_argument("data_file", help="Data file to export")
    parser_export.add_argument("--description", help="Export description")
    parser_export.set_defaults(func=cmd_export)

    # Import command
    parser_import = subparsers.add_parser("import", help="Import data from Quantro-Heart-Heart")
    parser_import.add_argument("--validate-only", action="store_true",
                              help="Only validate, don't actually import")
    parser_import.set_defaults(func=cmd_import)

    # Sync command
    parser_sync = subparsers.add_parser("sync", help="Bidirectional sync")
    parser_sync.add_argument("--dry-run", action="store_true",
                            help="Show what would be synced without actually syncing")
    parser_sync.set_defaults(func=cmd_sync)

    # Create metadata command
    parser_create = subparsers.add_parser("create-metadata",
                                          help="Create metadata for a data file")
    parser_create.add_argument("data_file", help="Data file")
    parser_create.add_argument("--type", required=True,
                              choices=["simulated", "realworld"],
                              help="Data type")
    parser_create.add_argument("--data-id", help="Data identifier")
    parser_create.add_argument("--description", help="Description")
    parser_create.add_argument("--model-type", help="Model type (for simulated)")
    parser_create.add_argument("--origin", help="Origin (for realworld)")
    parser_create.add_argument("--category", help="Data category")
    parser_create.add_argument("--enable-sync", action="store_true",
                              help="Enable bidirectional sync")
    parser_create.set_defaults(func=cmd_create_metadata)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
