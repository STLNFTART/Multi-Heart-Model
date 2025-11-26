#!/usr/bin/env python3
"""
Unified Simulation Framework for Multi-Heart-Model
Automatically saves all results to Google Drive

All simulations write to: ~/drive_links/ALL_MY_WORK/SimResults/
Organized by simulation type and run ID.

Author: Multi-Heart-Model Team
Date: 2025-11-26
"""

import os
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# ============================================================================
# GOOGLE DRIVE CONFIGURATION
# ============================================================================

# Everything goes into Google Drive → "All My Work" → "SimResults"
BASE_RESULTS_DIR = os.path.expanduser(
    "~/drive_links/ALL_MY_WORK/SimResults"
)

# Fallback to local directory if Drive not available
LOCAL_FALLBACK_DIR = os.path.expanduser(
    "~/Multi-Heart-Model-Results"
)


def ensure_dir(path: str) -> str:
    """Ensure directory exists, create if needed"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def get_results_base_dir() -> str:
    """Get base results directory, with fallback"""
    if os.path.exists(os.path.dirname(BASE_RESULTS_DIR)):
        try:
            ensure_dir(BASE_RESULTS_DIR)
            return BASE_RESULTS_DIR
        except Exception as e:
            print(f"⚠️  Warning: Cannot access Drive ({e})")
            print(f"   Falling back to: {LOCAL_FALLBACK_DIR}")
            ensure_dir(LOCAL_FALLBACK_DIR)
            return LOCAL_FALLBACK_DIR
    else:
        print(f"⚠️  Warning: Drive not mounted")
        print(f"   Using local: {LOCAL_FALLBACK_DIR}")
        ensure_dir(LOCAL_FALLBACK_DIR)
        return LOCAL_FALLBACK_DIR


def timestamp_tag() -> str:
    """Generate timestamp tag for run ID"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ============================================================================
# RUN LOGGER - Automatic Google Drive Integration
# ============================================================================

@dataclass
class RunMetadata:
    """Metadata for a simulation run"""
    run_id: str
    sim_name: str
    tag: str
    start_time: str
    base_dir: str
    parameters: Dict[str, Any]
    git_commit: Optional[str] = None
    git_branch: Optional[str] = None


class RunLogger:
    """
    Unified logger for all simulation runs.
    Automatically saves to Google Drive.

    Usage:
        logger = RunLogger("primal_kernel", tag="full_sweep")
        logger.log_parameters({"mu": 1.5, "omega": 1.0})

        for params in parameter_space:
            result = run_simulation(params)
            logger.add_result(params, result)

        logger.finalize(generate_report=True)
    """

    def __init__(self, sim_name: str, tag: str = "sweep"):
        self.sim_name = sim_name
        self.tag = tag
        self.run_id = f"{timestamp_tag()}_{tag}"
        self.start_time = datetime.now().isoformat()

        # All results under Google Drive / All My Work / SimResults
        results_base = get_results_base_dir()
        self.base_dir = os.path.join(
            results_base,
            sim_name,
            self.run_id,
        )

        # Directory structure
        self.raw_dir = os.path.join(self.base_dir, "raw")
        self.summary_dir = os.path.join(self.base_dir, "summary")
        self.plots_dir = os.path.join(self.base_dir, "plots")

        # Create directories
        ensure_dir(self.raw_dir)
        ensure_dir(self.summary_dir)
        ensure_dir(self.plots_dir)

        # Storage
        self.summary_rows = []
        self.metadata = RunMetadata(
            run_id=self.run_id,
            sim_name=sim_name,
            tag=tag,
            start_time=self.start_time,
            base_dir=self.base_dir,
            parameters={},
        )

        # Try to get git info
        self._capture_git_info()

        print("=" * 80)
        print(f"🚀 Starting {sim_name} sweep: {self.run_id}")
        print("=" * 80)
        print(f"📁 Results will save to:")
        print(f"   {self.base_dir}")
        if BASE_RESULTS_DIR in self.base_dir:
            print(f"   ✓ Google Drive sync active!")
        print("=" * 80)

    def _capture_git_info(self):
        """Capture git commit and branch info"""
        try:
            import subprocess
            commit = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode().strip()[:8]
            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            self.metadata.git_commit = commit
            self.metadata.git_branch = branch
        except:
            pass

    def log_parameters(self, params: Dict[str, Any]):
        """Log sweep parameters"""
        self.metadata.parameters = params
        params_file = os.path.join(self.base_dir, "parameters.json")
        with open(params_file, 'w') as f:
            json.dump(params, f, indent=2)

    def add_result(self, params: Dict[str, Any], metrics: Dict[str, Any]):
        """Add a single result row"""
        row = {**params, **metrics}
        self.summary_rows.append(row)

        # Also save individual result
        result_id = len(self.summary_rows)
        result_file = os.path.join(
            self.raw_dir,
            f"result_{result_id:06d}.json"
        )
        with open(result_file, 'w') as f:
            json.dump(row, f, indent=2)

    def save_checkpoint(self, checkpoint_name: str = "checkpoint"):
        """Save current state as checkpoint"""
        checkpoint_file = os.path.join(
            self.summary_dir,
            f"{checkpoint_name}.csv"
        )
        self._write_csv(checkpoint_file, self.summary_rows)
        print(f"  💾 Checkpoint saved: {checkpoint_name} ({len(self.summary_rows)} results)")

    def _write_csv(self, filepath: str, rows: List[Dict[str, Any]]):
        """Write rows to CSV"""
        if not rows:
            return

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def finalize(self, generate_report: bool = True):
        """Finalize the run and generate outputs"""
        end_time = datetime.now().isoformat()

        print(f"\n{'=' * 80}")
        print(f"✅ Sweep complete: {len(self.summary_rows)} results")
        print(f"{'=' * 80}")

        # Save final summary CSV
        summary_file = os.path.join(self.summary_dir, "summary.csv")
        self._write_csv(summary_file, self.summary_rows)
        print(f"  📊 Summary saved: summary.csv")

        # Save metadata
        self.metadata.parameters['end_time'] = end_time
        self.metadata.parameters['total_results'] = len(self.summary_rows)

        metadata_file = os.path.join(self.base_dir, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(asdict(self.metadata), f, indent=2)
        print(f"  📋 Metadata saved: metadata.json")

        # Generate report if requested
        if generate_report:
            self._generate_report()

        print(f"\n{'=' * 80}")
        print(f"📁 All results saved to:")
        print(f"   {self.base_dir}")
        if BASE_RESULTS_DIR in self.base_dir:
            print(f"   ✓ Synced to Google Drive!")
        print(f"{'=' * 80}\n")

    def _generate_report(self):
        """Generate markdown report"""
        report_file = os.path.join(self.base_dir, "REPORT.md")

        with open(report_file, 'w') as f:
            f.write(f"# {self.sim_name} - {self.tag}\n\n")
            f.write(f"**Run ID:** {self.run_id}\n\n")
            f.write(f"**Started:** {self.metadata.start_time}\n\n")

            if self.metadata.git_commit:
                f.write(f"**Git Commit:** {self.metadata.git_commit}\n\n")
                f.write(f"**Git Branch:** {self.metadata.git_branch}\n\n")

            f.write(f"## Summary\n\n")
            f.write(f"- Total Results: {len(self.summary_rows)}\n")
            f.write(f"- Output Directory: `{self.base_dir}`\n\n")

            f.write(f"## Parameters\n\n")
            f.write("```json\n")
            json.dump(self.metadata.parameters, f, indent=2)
            f.write("\n```\n\n")

            f.write(f"## Files\n\n")
            f.write(f"- `summary/summary.csv` - Complete results\n")
            f.write(f"- `raw/result_*.json` - Individual results\n")
            f.write(f"- `plots/` - Visualizations\n")
            f.write(f"- `metadata.json` - Run metadata\n\n")

        print(f"  📄 Report generated: REPORT.md")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def test_drive_access():
    """Test if Google Drive is accessible"""
    drive_path = os.path.expanduser("~/drive_links/ALL_MY_WORK")

    print("Testing Google Drive Access...")
    print(f"  Checking: {drive_path}")

    if os.path.exists(drive_path):
        print(f"  ✓ Drive accessible!")

        # Try to create test file
        test_file = os.path.join(drive_path, ".test_write_access")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"  ✓ Write access confirmed!")
            return True
        except Exception as e:
            print(f"  ✗ Cannot write to Drive: {e}")
            return False
    else:
        print(f"  ✗ Drive not accessible")
        print(f"  Run: bash setup_drive_symlink.sh")
        return False


def list_recent_runs(sim_name: Optional[str] = None, limit: int = 10):
    """List recent simulation runs"""
    results_base = get_results_base_dir()

    print(f"\n{'=' * 80}")
    print(f"Recent Simulation Runs")
    print(f"{'=' * 80}")
    print(f"Base Directory: {results_base}\n")

    if sim_name:
        sim_dirs = [os.path.join(results_base, sim_name)]
    else:
        sim_dirs = [
            os.path.join(results_base, d)
            for d in os.listdir(results_base)
            if os.path.isdir(os.path.join(results_base, d))
        ]

    all_runs = []
    for sim_dir in sim_dirs:
        if not os.path.exists(sim_dir):
            continue

        sim_name_local = os.path.basename(sim_dir)

        for run_id in os.listdir(sim_dir):
            run_path = os.path.join(sim_dir, run_id)
            if os.path.isdir(run_path):
                metadata_file = os.path.join(run_path, "metadata.json")
                if os.path.exists(metadata_file):
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    all_runs.append((sim_name_local, run_id, metadata, run_path))

    # Sort by start time
    all_runs.sort(key=lambda x: x[2].get('start_time', ''), reverse=True)

    # Display
    for i, (sim, run_id, meta, path) in enumerate(all_runs[:limit]):
        print(f"{i+1}. {sim} / {run_id}")
        print(f"   Started: {meta.get('start_time', 'Unknown')}")
        print(f"   Path: {path}")
        if 'parameters' in meta and 'total_results' in meta['parameters']:
            print(f"   Results: {meta['parameters']['total_results']}")
        print()

    print(f"{'=' * 80}\n")


# ============================================================================
# MAIN - Demo/Test
# ============================================================================

def main():
    """Demo the framework"""
    print("\n" + "=" * 80)
    print("UNIFIED SIMULATION FRAMEWORK")
    print("=" * 80 + "\n")

    # Test Drive access
    test_drive_access()

    print("\n" + "=" * 80)
    print("DEMO: Creating Test Run")
    print("=" * 80 + "\n")

    # Create demo logger
    logger = RunLogger("demo_simulation", tag="test")

    # Log parameters
    logger.log_parameters({
        "param1_range": [1.0, 2.0, 3.0],
        "param2_range": [0.5, 1.0, 1.5],
    })

    # Add some results
    import numpy as np
    for i in range(10):
        logger.add_result(
            params={"param1": 1.0 + i*0.1, "param2": 0.5 + i*0.05},
            metrics={
                "output": np.random.randn(),
                "success": True,
                "iteration": i
            }
        )

    # Save checkpoint
    logger.save_checkpoint("midpoint")

    # Finalize
    logger.finalize(generate_report=True)

    # List recent runs
    list_recent_runs(limit=5)


if __name__ == "__main__":
    main()
