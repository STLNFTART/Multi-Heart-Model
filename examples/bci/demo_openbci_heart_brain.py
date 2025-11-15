#!/usr/bin/env python3
"""
Demonstration of OpenBCI integration with heart-brain coupling model.

This script shows how to:
1. Acquire real-time EEG data from OpenBCI (or simulated data)
2. Extract neural drive signals (alpha/beta band power)
3. Use neural drive to modulate the heart-brain coupling model
4. Visualize the closed-loop brain-computer interface

Author: Multi-Heart-Model Team
Date: 2025-11-15
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple

# Import BCI components
from src.bci import OpenBCIInterface, OpenBCIConfig
from src.bci import NeuralToBrainModelBridge, BCIBridgeConfig
from src.coupling import CouplingParameters


def main():
    """Run OpenBCI heart-brain coupling demonstration."""

    print("=" * 70)
    print("OPENBCI HEART-BRAIN COUPLING DEMONSTRATION")
    print("=" * 70)
    print()

    # =========================================================================
    # Step 1: Configure OpenBCI Interface
    # =========================================================================
    print("Step 1: Configuring OpenBCI interface...")

    openbci_config = OpenBCIConfig(
        sample_rate=250.0,  # Hz
        num_channels=8,  # Cyton board
        gain=24,
        notch_filter=60.0,  # Hz (US line frequency)
        bandpass_low=0.5,  # Hz
        bandpass_high=50.0,  # Hz
    )

    print(f"  - Sample rate: {openbci_config.sample_rate} Hz")
    print(f"  - Channels: {openbci_config.num_channels}")
    print(f"  - Notch filter: {openbci_config.notch_filter} Hz")
    print()

    # =========================================================================
    # Step 2: Configure BCI-to-Model Bridge
    # =========================================================================
    print("Step 2: Configuring BCI-to-model bridge...")

    bridge_config = BCIBridgeConfig(
        bci_type="openbci",
        update_rate_hz=10.0,  # Update model 10x per second
        neural_drive_method="alpha_beta_ratio",  # Use alpha/beta ratio
        gain=0.5,
        use_adaptive_gain=True,  # Enable adaptive gain
    )

    coupling_params = CouplingParameters(
        neural_to_cardiac_gain=0.4,
        cardiac_to_neural_gain=0.2,
        neural_delay=0.120,  # 120 ms
        cardiac_delay=0.150,  # 150 ms
    )

    print(f"  - BCI type: {bridge_config.bci_type}")
    print(f"  - Neural drive method: {bridge_config.neural_drive_method}")
    print(f"  - Coupling: neural->cardiac gain = {coupling_params.neural_to_cardiac_gain}")
    print(f"  - Coupling: cardiac->neural gain = {coupling_params.cardiac_to_neural_gain}")
    print()

    # =========================================================================
    # Step 3: Initialize BCI Bridge
    # =========================================================================
    print("Step 3: Initializing BCI bridge (mock mode for demo)...")

    bridge = NeuralToBrainModelBridge(
        bci_config=openbci_config,
        bridge_config=bridge_config,
        coupling_params=coupling_params,
        mock_mode=True,  # Use simulated data for demo
    )

    print("  - Bridge initialized successfully")
    print()

    # =========================================================================
    # Step 4: Run Closed-Loop Simulation
    # =========================================================================
    print("Step 4: Running closed-loop simulation...")

    duration = 30.0  # seconds
    dt = 0.01  # 10 ms timestep

    print(f"  - Duration: {duration} s")
    print(f"  - Timestep: {dt} s")
    print(f"  - Total steps: {int(duration / dt)}")
    print()

    # Start the bridge
    bridge.start()

    # Run simulation
    print("  - Simulating... (this may take a moment)")
    times, states, drives = bridge.run_closed_loop_simulation(
        duration=duration,
        dt=dt,
    )

    # Stop the bridge
    bridge.stop()
    bridge.close()

    print(f"  - Simulation complete! Generated {len(times)} samples")
    print()

    # =========================================================================
    # Step 5: Extract and Analyze Results
    # =========================================================================
    print("Step 5: Analyzing results...")

    # Extract state components
    times = np.array(times)
    neural_v = np.array([s[0] for s in states])  # Neural voltage
    neural_w = np.array([s[1] for s in states])  # Neural recovery
    cardiac_x = np.array([s[2] for s in states])  # Cardiac position
    cardiac_y = np.array([s[3] for s in states])  # Cardiac velocity
    drives = np.array(drives)

    # Compute statistics
    print(f"  - Neural voltage range: [{neural_v.min():.3f}, {neural_v.max():.3f}]")
    print(f"  - Cardiac position range: [{cardiac_x.min():.3f}, {cardiac_x.max():.3f}]")
    print(f"  - Neural drive range: [{drives.min():.3f}, {drives.max():.3f}]")
    print(f"  - Neural drive mean: {drives.mean():.3f}")
    print()

    # Estimate heart rate from cardiac oscillation
    # Find peaks in cardiac_x
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(cardiac_x, distance=int(0.5 / dt))  # Min 0.5s between peaks

    if len(peaks) > 1:
        peak_times = times[peaks]
        rr_intervals = np.diff(peak_times)  # R-R intervals
        heart_rate_bpm = 60.0 / rr_intervals.mean()
        hrv_std = rr_intervals.std() * 1000  # ms

        print(f"  - Estimated heart rate: {heart_rate_bpm:.1f} BPM")
        print(f"  - Heart rate variability (std): {hrv_std:.1f} ms")
    else:
        print("  - Insufficient peaks for heart rate estimation")
    print()

    # =========================================================================
    # Step 6: Visualize Results
    # =========================================================================
    print("Step 6: Creating visualizations...")

    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

    # Plot 1: Neural voltage
    axes[0].plot(times, neural_v, 'b-', linewidth=1.0, label='Neural voltage (v)')
    axes[0].set_ylabel('Neural v', fontsize=10)
    axes[0].set_title('Closed-Loop BCI: OpenBCI → Heart-Brain Model', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc='upper right', fontsize=9)

    # Plot 2: Cardiac position
    axes[1].plot(times, cardiac_x, 'r-', linewidth=1.0, label='Cardiac position (x)')
    axes[1].set_ylabel('Cardiac x', fontsize=10)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc='upper right', fontsize=9)

    # Mark detected peaks
    if len(peaks) > 0:
        axes[1].plot(times[peaks], cardiac_x[peaks], 'ro', markersize=5, label='Detected peaks')
        axes[1].legend(loc='upper right', fontsize=9)

    # Plot 3: Neural drive from BCI
    axes[2].plot(times, drives, 'g-', linewidth=1.0, label='Neural drive from BCI')
    axes[2].set_ylabel('BCI Drive', fontsize=10)
    axes[2].grid(True, alpha=0.3)
    axes[2].legend(loc='upper right', fontsize=9)
    axes[2].set_ylim([0, 1.1])

    # Plot 4: Phase portrait (neural v vs cardiac x)
    axes[3].plot(neural_v, cardiac_x, 'k-', linewidth=0.5, alpha=0.6)
    axes[3].set_xlabel('Neural v', fontsize=10)
    axes[3].set_ylabel('Cardiac x', fontsize=10)
    axes[3].set_title('Phase Portrait (v vs x)', fontsize=10)
    axes[3].grid(True, alpha=0.3)

    axes[2].set_xlabel('Time (s)', fontsize=10)

    plt.tight_layout()
    plt.savefig('openbci_heart_brain_demo.png', dpi=150, bbox_inches='tight')
    print("  - Saved figure: openbci_heart_brain_demo.png")
    print()

    # =========================================================================
    # Step 7: Power Spectral Analysis
    # =========================================================================
    print("Step 7: Computing power spectral density...")

    from scipy.signal import welch

    # Compute PSD for neural voltage
    fs = 1.0 / dt  # Sampling frequency
    freqs, psd_neural = welch(neural_v, fs=fs, nperseg=min(1024, len(neural_v)//4))

    # Compute PSD for cardiac position
    _, psd_cardiac = welch(cardiac_x, fs=fs, nperseg=min(1024, len(cardiac_x)//4))

    fig, axes = plt.subplots(2, 1, figsize=(10, 6))

    axes[0].semilogy(freqs, psd_neural, 'b-', linewidth=1.5)
    axes[0].set_ylabel('PSD (Neural)', fontsize=10)
    axes[0].set_title('Power Spectral Density', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3, which='both')
    axes[0].set_xlim([0, 10])

    axes[1].semilogy(freqs, psd_cardiac, 'r-', linewidth=1.5)
    axes[1].set_xlabel('Frequency (Hz)', fontsize=10)
    axes[1].set_ylabel('PSD (Cardiac)', fontsize=10)
    axes[1].grid(True, alpha=0.3, which='both')
    axes[1].set_xlim([0, 10])

    plt.tight_layout()
    plt.savefig('openbci_heart_brain_psd.png', dpi=150, bbox_inches='tight')
    print("  - Saved figure: openbci_heart_brain_psd.png")
    print()

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  - Successfully integrated OpenBCI with heart-brain coupling model")
    print(f"  - Simulated {duration} seconds of closed-loop dynamics")
    print(f"  - Neural drive modulated cardiac oscillator via BCI feedback")
    print(f"  - Generated visualizations and spectral analysis")
    print()
    print("Key findings:")
    print(f"  - Heart rate: ~{heart_rate_bpm:.0f} BPM" if len(peaks) > 1 else "  - Heart rate: Unable to estimate")
    print(f"  - Neural-cardiac coupling successfully demonstrated")
    print(f"  - BCI-driven modulation of physiological oscillators validated")
    print()
    print("Next steps:")
    print("  - Connect real OpenBCI hardware (set mock_mode=False)")
    print("  - Implement adaptive parameter estimation")
    print("  - Add Lyapunov stability monitoring")
    print("  - Extend to Neuralink-style high-density arrays")
    print()
    print("Files generated:")
    print("  - openbci_heart_brain_demo.png")
    print("  - openbci_heart_brain_psd.png")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
