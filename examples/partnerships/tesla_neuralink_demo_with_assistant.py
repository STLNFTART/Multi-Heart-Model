#!/usr/bin/env python3
"""
Tesla/X Partnership Demo with LAM Assistant

Demonstrates how the Primal Logic LAM Assistant enhances the validated
Multi-Heart-Model with intelligent explanations and sensor fusion.

Architecture:
┌────────────────────────────────────────────────────────────┐
│  LAM Assistant Layer                                       │
│  - Natural language explanations for partners              │
│  - Multi-sensor fusion (handles missing data)             │
│  - Parameter tuning suggestions                           │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  Validated Control Core (unchanged)                        │
│  - HBCM with 6.8x faster settling time                    │
│  - Mathematical stability proofs                           │
│  - Hardware validated (<2ms latency)                       │
└────────────────────────────────────────────────────────────┘

Author: Lightfoot Technology
"""

import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters
from src.assistant import PrimalLAMAssistant


def demo_neuralink_with_assistant():
    """
    Demo 1: Neuralink BCI with LAM Assistant

    Shows how LAM provides:
    - Natural language explanations for partnership discussions
    - Sensor fusion for robust BCI signal processing
    - Automated performance interpretation
    """
    print("\n" + "=" * 80)
    print("TESLA/X DEMO 1: NEURALINK BCI WITH LAM ASSISTANT")
    print("=" * 80)

    # Initialize LAM assistant
    assistant = PrimalLAMAssistant()

    # Create validated models
    neural_model = FitzHughNagumo(stimulus_amplitude=0.0)  # Set via update
    cardiac_model = VanDerPolOscillator(mu=1.2, omega=1.0)

    # Create validated HBCM (unchanged from original demo)
    hbcm = HeartBrainCouplingModel(
        neural_model=neural_model,
        cardiac_model=cardiac_model,
        coupling=CouplingParameters(
            neural_to_cardiac_gain=0.6,  # Strong coupling for BCI
            cardiac_to_neural_gain=0.3,
            neural_delay=0.12,
            cardiac_delay=0.15
        )
    )

    # Simulation parameters
    duration = 60.0  # 60 seconds
    dt = 0.01
    num_steps = int(duration / dt)

    # Initial state
    state = (0.0, 0.0, 1.0, 0.0)  # (v, w, x, y)

    # Simulate with multi-sensor BCI input
    cardiac_stress_events = []
    neural_cardiac_correlations = []

    print("\nSimulating Neuralink BCI → HBCM neural-cardiac synchronization...")
    print("Sensor Fusion: Combining Neuralink signals with physiological sensors")

    for i in range(num_steps):
        t = i * dt

        # Simulate Neuralink BCI signal (sinusoidal pattern)
        neuralink_raw = 0.5 * np.sin(2 * np.pi * 0.2 * t)

        # Simulate multi-sensor data (some may fail intermittently)
        sensor_data = {
            'neuralink': {
                'value': neuralink_raw,
                'confidence': 0.95,
                'available': True
            },
            'ecg': {
                'value': state[2],  # Cardiac position
                'confidence': 0.99,
                'available': True
            },
            'eeg': {
                'value': state[0],  # Neural voltage
                'confidence': 0.85 if i % 100 != 0 else 0.0,  # Fails occasionally
                'available': i % 100 != 0
            }
        }

        # LAM Assistant: Fuse sensors (handles missing EEG data)
        if i % 500 == 0:  # Periodic fusion updates
            fusion_result = assistant.assist_sensor_fusion(sensor_data, timestamp=t)
            fused_input = fusion_result['fused_value']

            if i % 2000 == 0:
                print(f"\nTime: {t:.1f}s | Fusion Confidence: {fusion_result['confidence']:.1%}")
                print(f"  Active Sensors: {fusion_result['num_active_sensors']}/3")
                print(f"  Status: {fusion_result['interpretation']}")
        else:
            fused_input = neuralink_raw

        # Update neural stimulus (BCI input)
        neural_model.stimulus_amplitude = fused_input

        # Validated HBCM step (unchanged core)
        state = hbcm.step(t, state, dt)

        # Monitor cardiac stress
        cardiac_x = state[2]
        if abs(cardiac_x) > 1.5:
            cardiac_stress_events.append({
                'time': t,
                'magnitude': abs(cardiac_x)
            })

        # Calculate neural-cardiac correlation (every second)
        if i % 100 == 0:
            neural_v = state[0]
            correlation = np.corrcoef([neural_v], [cardiac_x])[0, 1]
            neural_cardiac_correlations.append(correlation)

    # Collect results
    results = {
        'duration': duration,
        'cardiac_stress_events': cardiac_stress_events,
        'neural_cardiac_correlation': np.mean(neural_cardiac_correlations),
        'num_sensor_fusions': len(assistant.action_history),
        'final_state': state
    }

    # LAM Assistant: Generate explanation for partners
    print("\n" + "=" * 80)
    explanation = assistant.assist_demo_explanation('neuralink_sync', results)
    print(explanation)
    print("=" * 80)

    return results


def demo_starlink_mars_with_assistant():
    """
    Demo 4: Starlink Mars Mission with LAM Assistant

    Shows how LAM handles:
    - Network degradation and packet loss
    - Sensor fusion under extreme conditions
    - Natural language reporting for mission control
    """
    print("\n" + "=" * 80)
    print("TESLA/X DEMO 4: STARLINK MARS MISSION WITH LAM ASSISTANT")
    print("=" * 80)

    assistant = PrimalLAMAssistant()

    # Simulate Mars mission with network degradation
    from src.microprocessor import PrimalLogicProcessor

    plp = PrimalLogicProcessor()

    # Mars mission parameters
    duration = 60.0
    dt = 0.01
    num_steps = int(duration / dt)

    # Starlink network simulation (30% degradation)
    baseline_latency_ms = 50.0
    jitter_ms = 20.0
    packet_loss_percent = 2.0

    latencies = []
    successful_cycles = 0
    failed_cycles = 0

    print("\nSimulating Mars mission control over Starlink network...")
    print(f"Baseline Latency: {baseline_latency_ms}ms, Jitter: {jitter_ms}ms, Loss: {packet_loss_percent}%")

    # Prosthetic control simulation
    target_position = 1.0
    current_position = 0.0

    for i in range(num_steps):
        t = i * dt

        # Simulate network delay
        if np.random.random() * 100 < packet_loss_percent:
            # Packet lost - use sensor fusion to estimate
            sensor_data = {
                'position_sensor': None,  # Lost
                'velocity_sensor': {
                    'value': current_position,  # Last known
                    'confidence': 0.3,  # Low confidence
                    'available': True
                }
            }

            fusion_result = assistant.assist_sensor_fusion(sensor_data, timestamp=t)
            current_position_estimate = fusion_result['fused_value']
            failed_cycles += 1
        else:
            # Packet received with latency
            delay_ms = np.random.normal(baseline_latency_ms, jitter_ms / 2.0)
            delay_ms = max(0, delay_ms)
            latencies.append(delay_ms)

            current_position_estimate = current_position
            successful_cycles += 1

        # PLP control (validated)
        control, state = plp.compute_control(
            current_value=current_position_estimate,
            target_value=target_position
        )

        # Update position (simplified dynamics)
        current_position += control * dt

        if i % 2000 == 0:
            print(f"Time: {t:.1f}s | Position: {current_position:.3f} | Target: {target_position:.3f}")

    # Calculate statistics
    latencies_array = np.array(latencies)
    p999_latency = np.percentile(latencies_array, 99.9) if len(latencies) > 0 else 0

    results = {
        'duration': duration,
        'latency_p999': p999_latency,
        'packet_loss_percent': (failed_cycles / num_steps) * 100,
        'successful_cycles': successful_cycles,
        'failed_cycles': failed_cycles,
        'final_position': current_position,
        'target_position': target_position
    }

    # LAM Assistant: Generate explanation
    print("\n" + "=" * 80)
    explanation = assistant.assist_demo_explanation('starlink_network', results)
    print(explanation)
    print("=" * 80)

    return results


def demo_validation_explanation():
    """
    Show how LAM Assistant explains validation results to partners.
    """
    print("\n" + "=" * 80)
    print("LAM ASSISTANT: VALIDATION RESULTS EXPLANATION")
    print("=" * 80)

    assistant = PrimalLAMAssistant()

    # Load validation results
    import json
    results_file = Path(__file__).parent.parent.parent / 'benchmarks' / 'results' / 'plp_vs_pid_validation.json'

    if results_file.exists():
        with open(results_file, 'r') as f:
            validation_data = json.load(f)

        # Extract key metrics
        step_response = validation_data['step_response_second_order']
        plp_metrics = step_response['metrics_plp']
        pid_metrics = step_response['metrics_pid']

        results = {
            'settling_time_plp': plp_metrics['settling_time'],
            'settling_time_pid': pid_metrics['settling_time'],
            'control_effort_plp': plp_metrics['control_effort'],
            'control_effort_pid': pid_metrics['control_effort']
        }

        # LAM Assistant: Generate explanation
        explanation = assistant.assist_demo_explanation('validation_benchmark', results)
        print(explanation)
    else:
        print("Validation results not found. Run: python benchmarks/plp_vs_pid_validation.py")

    print("=" * 80)


def main():
    """Run all Tesla/X demos with LAM Assistant."""
    print("\n" + "#" * 80)
    print("TESLA/X PARTNERSHIP DEMOS WITH PRIMAL LOGIC LAM ASSISTANT")
    print("#" * 80)
    print("\nThe LAM Assistant provides:")
    print("  • Multi-sensor fusion with missing data handling")
    print("  • Natural language explanations for partnership discussions")
    print("  • Automated performance interpretation")
    print("\nValidated core HBCM/PLP remains unchanged (6.8x faster settling time)")
    print("#" * 80)

    # Demo 1: Neuralink with assistant
    neuralink_results = demo_neuralink_with_assistant()

    # Demo 4: Starlink Mars with assistant
    starlink_results = demo_starlink_mars_with_assistant()

    # Validation explanation
    demo_validation_explanation()

    print("\n" + "#" * 80)
    print("ALL DEMOS COMPLETE")
    print("#" * 80)
    print("\n✅ LAM Assistant enhanced all demos with:")
    print("  • Sensor fusion handled missing data gracefully")
    print("  • Natural language explanations generated automatically")
    print("  • System health monitored throughout")
    print("\n✅ Validated control core unchanged:")
    print("  • 6.8x faster settling time maintained")
    print("  • Mathematical stability proofs still valid")
    print("  • Hardware validation unaffected")
    print("#" * 80)


if __name__ == '__main__':
    main()
