#!/usr/bin/env python3
"""
Demonstration of HBCM → OpenSim Biomechanical Integration

This script shows the complete workflow for coupling the Heart-Brain Coupling Model
with OpenSim biomechanical simulation.

Workflow:
1. Run HBCM simulation (cardiac + neural coupling)
2. Extract cardiac trajectory
3. Convert cardiac dynamics to muscle activation patterns
4. Generate OpenSim motion file (.mot)
5. Run OpenSim forward dynamics (if OpenSim installed)
6. Parse biomechanical results
7. Extract feedback for closed-loop coupling

Author: Multi-Heart-Model Team
License: MIT
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters
from src.integration import (
    OpenSimBridge,
    CardiacForceExtractor,
    OpenSimConfig,
    run_hbcm_opensim_integration
)


def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demonstrate_basic_extraction():
    """Demonstrate basic cardiac force extraction and motion file generation."""
    print_section("PART 1: Cardiac Force Extraction")

    # Create HBCM model
    print("\n1. Creating Heart-Brain Coupling Model...")
    hbcm = HeartBrainCouplingModel(
        neural_model=FitzHughNagumo(stimulus_amplitude=0.2),
        cardiac_model=VanDerPolOscillator(mu=1.5, omega=1.0),
        coupling=CouplingParameters(
            neural_to_cardiac_gain=0.5,
            cardiac_to_neural_gain=0.3,
            neural_to_cardiac_delay=0.12,
            cardiac_to_neural_delay=0.15
        )
    )

    # Run simulation
    print("2. Running HBCM simulation (10 seconds)...")
    initial_state = (0.0, 0.0, 1.0, 0.0)  # (v, w, x, y)
    t_span = (0.0, 10.0)
    dt = 0.001

    trajectory = hbcm.simulate(
        initial_state=initial_state,
        t_span=t_span,
        dt=dt
    )

    print(f"   Simulation complete: {len(trajectory)} timesteps")

    # Extract series
    times, neural, cardiac = hbcm.extract_series(trajectory)

    # Create cardiac trajectory for OpenSim
    cardiac_trajectory = [(t, (x, y)) for t, (x, y) in zip(times, cardiac)]

    print(f"   Cardiac trajectory: {len(cardiac_trajectory)} points")
    print(f"   Time range: {times[0]:.3f} - {times[-1]:.3f} seconds")

    # Extract muscle activations
    print("\n3. Extracting muscle activation patterns...")
    config = OpenSimConfig(
        n_muscles=8,
        mapping_function="phase_distributed"
    )
    extractor = CardiacForceExtractor(config)

    activation_times, activations = extractor.cardiac_state_to_muscle_activation(
        cardiac_trajectory,
        mapping_strategy="phase_distributed"
    )

    print(f"   Generated activations: {activations.shape}")
    print(f"   Muscles: {config.muscle_names}")
    print(f"   Activation range: [{activations.min():.3f}, {activations.max():.3f}]")

    # Export motion file
    print("\n4. Exporting OpenSim motion file...")
    motion_file = extractor.export_opensim_motion(
        times=activation_times,
        activations=activations
    )
    print(f"   Motion file: {motion_file}")

    # Verify file exists and show preview
    if os.path.exists(motion_file):
        print("\n   File preview (first 15 lines):")
        with open(motion_file, 'r') as f:
            for i, line in enumerate(f):
                if i < 15:
                    print(f"   {line.rstrip()}")
                else:
                    break

    return cardiac_trajectory, activations, config


def demonstrate_mapping_strategies():
    """Compare different cardiac-to-muscle mapping strategies."""
    print_section("PART 2: Mapping Strategy Comparison")

    # Simple cardiac trajectory for demonstration
    print("\n1. Creating synthetic cardiac trajectory...")
    t = np.linspace(0, 5, 500)
    x = np.cos(2 * np.pi * 1.0 * t)
    y = -np.sin(2 * np.pi * 1.0 * t)
    cardiac_traj = [(ti, (xi, yi)) for ti, xi, yi in zip(t, x, y)]

    print(f"   Trajectory: {len(cardiac_traj)} points, 5 seconds")

    # Test different mapping strategies
    strategies = ["phase_distributed", "direct", "fatigue_model"]
    config = OpenSimConfig(n_muscles=4)
    extractor = CardiacForceExtractor(config)

    results = {}

    print("\n2. Testing mapping strategies...")
    for strategy in strategies:
        print(f"\n   Strategy: {strategy}")
        times, activations = extractor.cardiac_state_to_muscle_activation(
            cardiac_traj,
            mapping_strategy=strategy
        )
        results[strategy] = activations
        print(f"      Shape: {activations.shape}")
        print(f"      Range: [{activations.min():.3f}, {activations.max():.3f}]")
        print(f"      Mean: {activations.mean():.3f}")

    # Visualize comparison
    print("\n3. Visualizing mapping strategies...")
    try:
        fig, axes = plt.subplots(len(strategies), 1, figsize=(12, 8))

        for idx, strategy in enumerate(strategies):
            ax = axes[idx]
            activations = results[strategy]

            # Plot each muscle's activation
            for muscle_idx in range(activations.shape[1]):
                ax.plot(t, activations[:, muscle_idx],
                       label=f'Muscle {muscle_idx + 1}', alpha=0.7)

            ax.set_title(f'{strategy.replace("_", " ").title()} Mapping')
            ax.set_ylabel('Activation')
            ax.set_ylim([0, 1])
            ax.legend(loc='upper right', fontsize=8)
            ax.grid(True, alpha=0.3)

        axes[-1].set_xlabel('Time (seconds)')
        plt.tight_layout()

        output_file = 'results/mapping_comparison.png'
        os.makedirs('results', exist_ok=True)
        plt.savefig(output_file, dpi=150)
        print(f"   Saved: {output_file}")

        plt.close()

    except Exception as e:
        print(f"   Visualization skipped: {e}")


def demonstrate_full_pipeline():
    """Demonstrate complete HBCM → OpenSim pipeline (requires OpenSim installed)."""
    print_section("PART 3: Full OpenSim Integration Pipeline")

    print("\n1. Running HBCM simulation...")
    hbcm = HeartBrainCouplingModel(
        neural_model=FitzHughNagumo(a=0.7, b=0.8, c=3.0),
        cardiac_model=VanDerPolOscillator(mu=2.0, omega=1.1),
        coupling=CouplingParameters()
    )

    trajectory = hbcm.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, 5.0),
        dt=0.001
    )

    times, neural, cardiac = hbcm.extract_series(trajectory)
    cardiac_trajectory = [(t, (x, y)) for t, (x, y) in zip(times, cardiac)]

    print(f"   Simulation complete: {len(trajectory)} timesteps")

    # Option 1: Use convenience function
    print("\n2. Running full pipeline with convenience function...")
    try:
        results = run_hbcm_opensim_integration(
            cardiac_trajectory,
            config=OpenSimConfig(
                model_file="models/gait2392.osim",  # Update path as needed
                n_muscles=8
            )
        )

        if results.success:
            print("   OpenSim simulation SUCCESS!")
            print(f"   Output file: {results.output_file}")
            print(f"\n   Biomechanical Results:")
            print(f"      Kinematics variables: {len(results.kinematics)}")
            print(f"      Force variables: {len(results.forces)}")

            if results.summary:
                print(f"\n   Feedback Parameters:")
                print(f"      Cardiac afterload factor: {results.summary.get('cardiac_afterload_factor', 'N/A'):.3f}")
                print(f"      Total mechanical power: {results.summary.get('total_mechanical_power', 'N/A'):.2f} W")
                print(f"      Peak GRF: {results.summary.get('peak_ground_reaction_force', 'N/A'):.2f} N")
                print(f"      Metabolic cost: {results.summary.get('metabolic_cost', 'N/A'):.2f} W")

        else:
            print("   OpenSim simulation FAILED")
            print(f"   Error: {results.stderr}")

    except Exception as e:
        print(f"   Pipeline execution failed: {e}")
        print("   This is expected if OpenSim is not installed or not in PATH")

    # Option 2: Step-by-step manual pipeline
    print("\n3. Alternative: Manual step-by-step pipeline...")
    try:
        config = OpenSimConfig()
        bridge = OpenSimBridge(config)

        # Generate motion file
        print("   a) Generating muscle activations...")
        extractor = bridge.extractor
        activation_times, activations = extractor.cardiac_state_to_muscle_activation(
            cardiac_trajectory
        )

        print("   b) Exporting motion file...")
        motion_file = extractor.export_opensim_motion(activation_times, activations)
        print(f"      Motion file: {motion_file}")

        # Would run OpenSim here if installed
        print("   c) OpenSim execution (skipped - requires installation)")
        print("      Command would be:")
        print(f"      opensim-cmd run-tool setup.xml -model model.osim -motion {motion_file}")

    except Exception as e:
        print(f"   Manual pipeline error: {e}")


def demonstrate_closed_loop_feedback():
    """Demonstrate closed-loop feedback from biomechanics to cardiac model."""
    print_section("PART 4: Closed-Loop Feedback Simulation")

    print("\n1. Simulating biomechanical load feedback...")

    # Initial HBCM simulation
    hbcm = HeartBrainCouplingModel(
        cardiac_model=VanDerPolOscillator(mu=1.5, omega=1.0),
        neural_model=FitzHughNagumo(),
        coupling=CouplingParameters()
    )

    # Run baseline simulation
    print("\n2. Baseline simulation (no biomechanical load)...")
    trajectory_baseline = hbcm.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, 10.0),
        dt=0.001
    )

    times_baseline, _, cardiac_baseline = hbcm.extract_series(trajectory_baseline)

    # Simulate increased afterload (e.g., from running)
    print("\n3. Increased afterload simulation (simulated exercise)...")

    # Increase cardiac damping to simulate afterload
    hbcm_loaded = HeartBrainCouplingModel(
        cardiac_model=VanDerPolOscillator(mu=2.0, omega=1.0),  # Increased mu
        neural_model=FitzHughNagumo(),
        coupling=CouplingParameters()
    )

    trajectory_loaded = hbcm_loaded.simulate(
        initial_state=(0.0, 0.0, 1.0, 0.0),
        t_span=(0.0, 10.0),
        dt=0.001
    )

    times_loaded, _, cardiac_loaded = hbcm_loaded.extract_series(trajectory_loaded)

    # Compare cardiac outputs
    print("\n4. Comparing baseline vs loaded cardiac dynamics...")

    baseline_amplitude = np.max([x for x, _ in cardiac_baseline])
    loaded_amplitude = np.max([x for x, _ in cardiac_loaded])

    print(f"   Baseline cardiac amplitude: {baseline_amplitude:.3f}")
    print(f"   Loaded cardiac amplitude: {loaded_amplitude:.3f}")
    print(f"   Amplitude change: {((loaded_amplitude - baseline_amplitude) / baseline_amplitude * 100):.1f}%")

    # Visualize comparison
    print("\n5. Visualizing closed-loop effects...")
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Cardiac trajectories
        cardiac_x_baseline = [x for x, _ in cardiac_baseline]
        cardiac_x_loaded = [x for x, _ in cardiac_loaded]

        ax1.plot(times_baseline, cardiac_x_baseline, label='Baseline', linewidth=2)
        ax1.plot(times_loaded, cardiac_x_loaded, label='With Biomechanical Load', linewidth=2, alpha=0.8)
        ax1.set_ylabel('Cardiac Position (x)')
        ax1.set_title('Cardiac Dynamics: Baseline vs Loaded')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Phase portraits
        cardiac_y_baseline = [y for _, y in cardiac_baseline]
        cardiac_y_loaded = [y for _, y in cardiac_loaded]

        ax2.plot(cardiac_x_baseline, cardiac_y_baseline, label='Baseline', linewidth=1.5, alpha=0.7)
        ax2.plot(cardiac_x_loaded, cardiac_y_loaded, label='With Load', linewidth=1.5, alpha=0.7)
        ax2.set_xlabel('Cardiac Position (x)')
        ax2.set_ylabel('Cardiac Velocity (y)')
        ax2.set_title('Phase Portrait Comparison')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        output_file = 'results/closed_loop_feedback.png'
        os.makedirs('results', exist_ok=True)
        plt.savefig(output_file, dpi=150)
        print(f"   Saved: {output_file}")

        plt.close()

    except Exception as e:
        print(f"   Visualization skipped: {e}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  HBCM → OpenSim Integration Demonstration")
    print("  Multi-Heart-Model")
    print("=" * 70)

    # Part 1: Basic extraction
    cardiac_trajectory, activations, config = demonstrate_basic_extraction()

    # Part 2: Mapping strategies
    demonstrate_mapping_strategies()

    # Part 3: Full pipeline (requires OpenSim)
    demonstrate_full_pipeline()

    # Part 4: Closed-loop feedback
    demonstrate_closed_loop_feedback()

    # Summary
    print_section("SUMMARY")
    print("\nDemonstration complete!")
    print("\nKey Files Generated:")
    print(f"  - Motion files: {config.motion_output_dir}/*.mot")
    print(f"  - Biomechanics results: {config.results_output_dir}/*.sto")
    print(f"  - Visualizations: results/*.png")

    print("\nNext Steps:")
    print("  1. Install OpenSim to run full biomechanical simulations")
    print("  2. Configure OpenSim model files (.osim) for your use case")
    print("  3. Adjust muscle mappings in OpenSimConfig")
    print("  4. Integrate feedback into closed-loop HBCM simulations")

    print("\nNote:")
    print("  If OpenSim is not installed, motion files can still be generated")
    print("  and imported into OpenSim GUI for manual analysis.")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
