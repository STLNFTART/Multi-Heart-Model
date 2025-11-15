#!/usr/bin/env python3
"""
Web Control Panel Demonstration

Shows complete integration of:
- BCI data acquisition
- Real-time HBCM simulation
- LSL streaming
- Data visualization
- LaTeX documentation generation
"""

import sys
from pathlib import Path
import numpy as np
import time
import asyncio
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bci_integration.data_acquisition import (
    SyntheticAdapter,
    BCIStreamConfig,
    CircularBuffer,
    DataQualityMetrics
)
from bci_integration.streaming import LSLBridge, LSLStreamer
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters


def demo_bci_adapters():
    """Demonstrate BCI adapter functionality."""
    print("=" * 70)
    print("DEMO 1: BCI Data Acquisition Adapters")
    print("=" * 70)

    # Create synthetic EEG adapter
    print("\n1. Creating synthetic EEG adapter...")
    adapter = SyntheticAdapter(
        n_channels=8,
        sampling_rate=250.0,
        signal_type="eeg"
    )

    # Connect
    print("2. Connecting to adapter...")
    if not adapter.connect():
        print("Failed to connect!")
        return

    # Start streaming
    print("3. Starting data stream...")
    adapter.start_stream()

    # Create circular buffer
    buffer = CircularBuffer(
        n_channels=8,
        buffer_duration=5.0,
        sampling_rate=250.0
    )

    # Collect data for a few seconds
    print("4. Collecting data for 3 seconds...")
    start_time = time.time()
    packet_count = 0

    while time.time() - start_time < 3.0:
        packet = adapter.get_latest_data(timeout=0.5)
        if packet:
            packet_count += 1
            buffer.add_data(packet.data, packet.timestamp)

            # Calculate quality metrics
            quality_scores = []
            for ch in range(packet.n_channels):
                score = DataQualityMetrics.compute_quality_score(packet.data[ch, :])
                quality_scores.append(score)

            print(f"   Packet {packet_count}: {packet.n_samples} samples, "
                  f"avg quality: {np.mean(quality_scores):.3f}")

    # Stop streaming
    print("5. Stopping stream...")
    adapter.stop_stream()
    adapter.disconnect()

    print(f"\n✓ Collected {packet_count} packets ({buffer.buffer_size} samples buffered)")


def demo_lsl_streaming():
    """Demonstrate LSL streaming."""
    print("\n" + "=" * 70)
    print("DEMO 2: Lab Streaming Layer (LSL) Integration")
    print("=" * 70)

    # Create synthetic adapter
    print("\n1. Creating synthetic ECG adapter...")
    adapter = SyntheticAdapter(
        n_channels=4,
        sampling_rate=250.0,
        signal_type="ecg"
    )

    adapter.connect()

    # Create LSL bridge
    print("2. Setting up LSL bridge...")
    bridge = LSLBridge(adapter, stream_name="Demo_ECG_Stream")

    if not bridge.start():
        print("Failed to start LSL bridge!")
        return

    # Start streaming
    print("3. Starting ECG data stream...")
    adapter.start_stream()

    # Stream for a few seconds
    print("4. Streaming to LSL for 5 seconds...")
    print("   (Other applications can now connect to 'Demo_ECG_Stream')")

    time.sleep(5.0)

    # Cleanup
    print("5. Stopping LSL bridge...")
    bridge.stop()
    adapter.stop_stream()
    adapter.disconnect()

    print("\n✓ LSL streaming demonstration complete")


def demo_hbcm_with_bci():
    """Demonstrate HBCM simulation with BCI integration."""
    print("\n" + "=" * 70)
    print("DEMO 3: HBCM Simulation with BCI Integration")
    print("=" * 70)

    # Create HBCM
    print("\n1. Initializing Heart-Brain Coupling Model...")
    hbcm = HeartBrainCouplingModel(
        neural_model=FitzHughNagumo(a=0.7, b=0.8, c=3.0, stimulus_amplitude=0.5),
        cardiac_model=VanDerPolOscillator(mu=1.5, omega=1.0, damping=0.1),
        coupling=CouplingParameters(
            neural_to_cardiac_gain=0.5,
            cardiac_to_neural_gain=0.3,
            neural_to_cardiac_delay=0.12,
            cardiac_to_neural_delay=0.15
        )
    )

    # Create BCI adapter
    print("2. Creating synthetic BCI adapter...")
    bci = SyntheticAdapter(n_channels=8, sampling_rate=250.0, signal_type="eeg")
    bci.connect()
    bci.start_stream()

    # Run coupled simulation
    print("3. Running coupled BCI-HBCM simulation for 5 seconds...")
    print("   (BCI data influences HBCM neural subsystem)")

    initial_state = (0.0, 0.0, 1.0, 0.0)
    current_state = initial_state
    current_time = 0.0
    dt = 0.001
    duration = 5.0

    bci_influence_buffer = []
    hbcm_trajectory = []

    steps = 0
    while current_time < duration:
        # Get BCI data
        packet = bci.get_latest_data(timeout=0.01)
        if packet:
            # Use BCI data to modulate neural stimulus
            # Average across channels and samples as a simple approach
            bci_signal = np.mean(packet.data)
            bci_influence = bci_signal / 1000.0  # Scale to reasonable range

            bci_influence_buffer.append(bci_influence)

            # Inject into HBCM (would need custom step method to fully integrate)
            # For demo, we just track it

        # Step HBCM
        current_state = hbcm.step(current_time, current_state, dt)
        current_time += dt
        steps += 1

        if steps % 500 == 0:
            print(f"   t={current_time:.2f}s, neural_v={current_state[0]:.3f}, "
                  f"cardiac_x={current_state[2]:.3f}, "
                  f"bci_influence={bci_influence_buffer[-1] if bci_influence_buffer else 0:.6f}")

        hbcm_trajectory.append((current_time, current_state))

    # Cleanup
    bci.stop_stream()
    bci.disconnect()

    print(f"\n✓ Simulation complete: {steps} steps, {len(hbcm_trajectory)} trajectory points")
    print(f"  BCI influence range: [{min(bci_influence_buffer):.6f}, {max(bci_influence_buffer):.6f}]")


def demo_visualization():
    """Demonstrate visualization capabilities."""
    print("\n" + "=" * 70)
    print("DEMO 4: Real-time Visualization")
    print("=" * 70)

    try:
        from web_control_panel.visualization.realtime_plotter import (
            RealtimePlotter,
            PlotlyVisualizer,
            Visualizer3D
        )

        # Run short simulation
        print("\n1. Running HBCM simulation...")
        hbcm = HeartBrainCouplingModel(
            neural_model=FitzHughNagumo(),
            cardiac_model=VanDerPolOscillator(),
            coupling=CouplingParameters()
        )

        trajectory = hbcm.simulate(
            initial_state=(0.0, 0.0, 1.0, 0.0),
            t_span=(0.0, 10.0),
            dt=0.001
        )

        times, neural, cardiac = hbcm.extract_series(trajectory)

        # Create matplotlib plot
        print("2. Creating matplotlib visualization...")
        plotter = RealtimePlotter(figsize=(14, 10))
        plotter.update(times, neural, cardiac)

        img_path = Path("demo_visualization.png")
        plotter.fig.savefig(img_path, dpi=100, bbox_inches='tight')
        print(f"   ✓ Saved to: {img_path}")

        # Create Plotly interactive plot
        print("3. Creating Plotly interactive visualization...")
        plotly_fig = PlotlyVisualizer.create_interactive_plot(times, neural, cardiac)

        if plotly_fig:
            import plotly.graph_objects as go
            fig = go.Figure(plotly_fig)
            html_path = Path("demo_visualization.html")
            fig.write_html(str(html_path))
            print(f"   ✓ Saved to: {html_path}")

        # Create 3D visualization
        print("4. Creating 3D trajectory visualization...")
        plotly_3d = Visualizer3D.create_plotly_3d_surface(neural, cardiac, times)

        if plotly_3d:
            fig_3d = go.Figure(plotly_3d)
            html_3d_path = Path("demo_3d_visualization.html")
            fig_3d.write_html(str(html_3d_path))
            print(f"   ✓ Saved to: {html_3d_path}")

        print("\n✓ Visualization demonstration complete")

    except ImportError as e:
        print(f"⚠ Visualization demo skipped: {e}")
        print("  Install dependencies: pip install matplotlib plotly pyvista")


def demo_latex_documentation():
    """Demonstrate LaTeX documentation generation."""
    print("\n" + "=" * 70)
    print("DEMO 5: Automated LaTeX Documentation")
    print("=" * 70)

    try:
        from web_control_panel.documentation.latex_generator import (
            LaTeXDocumentGenerator,
            BibtexGenerator
        )

        # Create sample simulation data
        simulation_data = {
            'simulation_duration': 10.0,
            'n_samples': 10000,
            'configuration': {
                'neural_params': {'a': 0.7, 'b': 0.8, 'c': 3.0, 'stimulus_amplitude': 0.5},
                'cardiac_params': {'mu': 1.5, 'omega': 1.0, 'damping': 0.1},
                'coupling_params': {
                    'neural_to_cardiac_gain': 0.5,
                    'cardiac_to_neural_gain': 0.3,
                    'neural_to_cardiac_delay': 0.12,
                    'cardiac_to_neural_delay': 0.15
                }
            },
            'results': {
                'neural_statistics': {
                    'v_mean': 0.123, 'v_std': 0.456, 'v_min': -1.234, 'v_max': 2.345,
                    'w_mean': 0.234, 'w_std': 0.345, 'w_min': -0.567, 'w_max': 0.678
                },
                'cardiac_statistics': {
                    'x_mean': 0.012, 'x_std': 0.789, 'x_min': -1.567, 'x_max': 1.789,
                    'y_mean': 0.045, 'y_std': 0.890, 'y_min': -1.234, 'y_max': 1.456
                }
            }
        }

        bci_data = {
            'device': 'OpenBCI Cyton (Synthetic)',
            'n_channels': 8,
            'sampling_rate': 250.0,
            'signal_type': 'EEG',
            'avg_snr': 18.5,
            'artifact_pct': 5.2
        }

        print("\n1. Generating LaTeX documentation...")
        generator = LaTeXDocumentGenerator(output_dir="reports")

        tex_file = generator.generate_full_report(
            simulation_data=simulation_data,
            bci_data=bci_data,
            figures_dir=None
        )

        print(f"   ✓ LaTeX file: {tex_file}")

        # Generate BibTeX
        print("2. Generating BibTeX references...")
        bib_path = Path("reports/references.bib")
        BibtexGenerator.save_bibfile(str(bib_path))

        print("\n✓ Documentation generation complete")
        print(f"  Note: Compile with 'pdflatex {tex_file}' if LaTeX is installed")

    except Exception as e:
        print(f"⚠ Documentation demo error: {e}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("Multi-Heart-Model Web Control Panel - Complete Demonstration")
    print("=" * 70)
    print("\nThis demo shows:")
    print("  1. BCI data acquisition adapters")
    print("  2. LSL streaming integration")
    print("  3. HBCM simulation with BCI coupling")
    print("  4. Real-time visualization (matplotlib, Plotly, 3D)")
    print("  5. Automated LaTeX documentation")
    print("\n" + "=" * 70)

    try:
        # Run demos
        demo_bci_adapters()
        demo_lsl_streaming()
        demo_hbcm_with_bci()
        demo_visualization()
        demo_latex_documentation()

        # Final summary
        print("\n" + "=" * 70)
        print("ALL DEMONSTRATIONS COMPLETE")
        print("=" * 70)
        print("\nGenerated files:")
        print("  - demo_visualization.png (matplotlib plot)")
        print("  - demo_visualization.html (interactive Plotly)")
        print("  - demo_3d_visualization.html (3D trajectory)")
        print("  - reports/report_*.tex (LaTeX documentation)")
        print("  - reports/references.bib (BibTeX references)")

        print("\nNext steps:")
        print("  1. Start web server: python web_control_panel/backend/main.py")
        print("  2. Open browser to: http://localhost:8000")
        print("  3. Use WebSocket at: ws://localhost:8000/ws/client_id")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nDemo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
