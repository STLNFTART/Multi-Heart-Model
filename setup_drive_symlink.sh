#!/bin/bash
#
# Google Drive Symlink Setup Script for Termux
# Creates clean symlinks to Google Drive folders for simulation results
#
# Author: Multi-Heart-Model Team
# Date: 2025-11-26

set -e  # Exit on error

echo "=========================================="
echo "Google Drive Symlink Setup"
echo "=========================================="

# Define paths
DRIVE_PATH="/mnt/chromeos/GoogleDrive/MyDrive/All My Work"
TERMUX_LINK_DIR="$HOME/drive_links"
SYMLINK_NAME="ALL_MY_WORK"
SYMLINK_PATH="$TERMUX_LINK_DIR/$SYMLINK_NAME"

# Create drive_links directory if it doesn't exist
echo ""
echo "[1/4] Creating drive_links directory..."
mkdir -p "$TERMUX_LINK_DIR"
echo "  ✓ Created: $TERMUX_LINK_DIR"

# Check if Google Drive path exists
echo ""
echo "[2/4] Checking Google Drive access..."
if [ ! -d "$DRIVE_PATH" ]; then
    echo "  ✗ ERROR: Google Drive path not found:"
    echo "    $DRIVE_PATH"
    echo ""
    echo "  Possible solutions:"
    echo "    1. Mount Google Drive in ChromeOS Files app"
    echo "    2. Ensure Drive is syncing"
    echo "    3. Check path spelling/permissions"
    exit 1
fi
echo "  ✓ Google Drive accessible"

# Remove existing symlink if present
if [ -L "$SYMLINK_PATH" ]; then
    echo ""
    echo "[3/4] Removing existing symlink..."
    rm "$SYMLINK_PATH"
    echo "  ✓ Old symlink removed"
elif [ -e "$SYMLINK_PATH" ]; then
    echo ""
    echo "  ✗ ERROR: Path exists but is not a symlink:"
    echo "    $SYMLINK_PATH"
    echo "  Please remove it manually first."
    exit 1
fi

# Create the symlink
echo ""
echo "[3/4] Creating symlink..."
ln -s "$DRIVE_PATH" "$SYMLINK_PATH"
echo "  ✓ Symlink created:"
echo "    $SYMLINK_PATH -> $DRIVE_PATH"

# Verify symlink works
echo ""
echo "[4/4] Verifying symlink..."
if [ ! -d "$SYMLINK_PATH" ]; then
    echo "  ✗ ERROR: Symlink verification failed"
    exit 1
fi

# Test read access
if ls "$SYMLINK_PATH" > /dev/null 2>&1; then
    echo "  ✓ Read access confirmed"
else
    echo "  ✗ ERROR: Cannot read through symlink"
    exit 1
fi

# Create SimResults directory structure
SIMRESULTS_DIR="$SYMLINK_PATH/SimResults"
echo ""
echo "Creating SimResults directory structure..."
mkdir -p "$SIMRESULTS_DIR"

# Create subdirectories for all simulation types
SIM_TYPES=(
    "primal_kernel"
    "field_coupling"
    "quantum_state"
    "mars_mission"
    "consciousness"
    "uav_swarm"
    "heart_brain"
    "organ_chip"
    "surgical_robotics"
    "bci_integration"
)

for sim_type in "${SIM_TYPES[@]}"; do
    mkdir -p "$SIMRESULTS_DIR/$sim_type"
    echo "  ✓ Created: $sim_type/"
done

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Symlink Info:"
echo "  Local Path:  $SYMLINK_PATH"
echo "  Drive Path:  $DRIVE_PATH"
echo "  Results Dir: $SIMRESULTS_DIR"
echo ""
echo "Test your setup:"
echo "  ls ~/drive_links/ALL_MY_WORK"
echo "  ls ~/drive_links/ALL_MY_WORK/SimResults"
echo ""
echo "All simulation results will now save to Google Drive!"
echo ""
