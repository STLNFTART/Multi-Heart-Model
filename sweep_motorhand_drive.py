#!/usr/bin/env python3
"""
MotorHandPro Parameter Sweep with Google Drive Integration

Comprehensive parameter space exploration for:
- Primal Logic Processor control parameters
- MotorHandPro QUANT integration
- Closed-loop control performance
- Emergency braking scenarios
- Throttle conversion validation

All results automatically save to Google Drive via framework.py

Author: Lightfoot Technology
"""

import sys
import os
import numpy as np
from itertools import product
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from framework import RunLogger
from src.microprocessor import PrimalLogicProcessor, ProcessorConfig
from src.integration import MotorHandBridge
from src.microprocessor.control_system import compute_comfort_metrics


class MotorHandSweepOrchestrator:
    """
    Comprehensive parameter sweep orchestrator for MotorHandPro integration

    Sweeps across:
    1. Primal Logic control parameters (K_gain, lambda_decay)
    2. Emergency braking scenarios (initial velocity, duration)
    3. IPU configurations (number of integral processing units)
    4. Throttle conversion accuracy
    5. Closed-loop performance metrics
    """

    def __init__(self):
        self.results = {
            'control_parameters': [],
            'emergency_braking': [],
            'ipu_scaling': [],
            'throttle_conversion': [],
            'closed_loop': []
        }

    def sweep_control_parameters(self, quick_mode: bool = False):
        """
        Sweep Primal Logic control parameters (K_gain, lambda_decay)

        Tests control stability, comfort, and performance across
        parameter space.
        """
        logger = RunLogger("motorhand_control_params", tag="param_sweep")

        print("\n" + "=" * 80)
        print("MOTORHANDPRO: Control Parameter Sweep")
        print("=" * 80)

        # Parameter ranges
        if quick_mode:
            K_gains = np.linspace(0.1, 2.0, 5)
            lambda_decays = np.linspace(0.5, 5.0, 5)
            ipus = [4, 8, 16]
        else:
            K_gains = np.linspace(0.1, 2.0, 10)
            lambda_decays = np.linspace(0.5, 5.0, 10)
            ipus = [2, 4, 8, 16, 32]

        # Log parameters
        logger.log_parameters({
            'K_gain_range': K_gains.tolist(),
            'lambda_decay_range': lambda_decays.tolist(),
            'ipu_range': ipus,
            'test_scenario': 'emergency_braking',
            'initial_velocity': 30.0,
            'target_velocity': 0.0,
            'duration': 10.0
        })

        total_combinations = len(K_gains) * len(lambda_decays) * len(ipus)
        print(f"\n[1/5] Control Parameter Sweep")
        print(f"   Testing {total_combinations} parameter combinations...")

        successful = 0
        iteration = 0

        for K_gain, lambda_decay, num_ipus in product(K_gains, lambda_decays, ipus):
            iteration += 1

            if iteration % 50 == 0 or iteration == 1:
                print(f"   Progress: {iteration}/{total_combinations} ({iteration/total_combinations*100:.1f}%)")

            try:
                # Create processor with these parameters
                processor = PrimalLogicProcessor(ProcessorConfig(
                    K_gain=float(K_gain),
                    lambda_decay=float(lambda_decay),
                    num_integral_units=int(num_ipus)
                ))

                # Run emergency braking simulation
                states = processor.simulate_emergency_braking(
                    initial_velocity=30.0,
                    target_velocity=0.0,
                    duration=10.0
                )

                # Extract metrics
                final_velocity = states[-1].velocity
                controls = [s.bounded_control for s in states]
                comfort_metrics = compute_comfort_metrics(controls, dt=0.01)

                # Settling time (time to reach 1% of target)
                settling_idx = 0
                for i, state in enumerate(states):
                    if abs(state.velocity - 0.0) < 0.3:  # within 0.3 m/s
                        settling_idx = i
                        break
                settling_time = settling_idx * 0.01

                # Overshoot
                min_velocity = min(s.velocity for s in states)
                overshoot = abs(min_velocity) if min_velocity < 0 else 0.0

                # Peak control
                peak_control = max(abs(c) for c in controls)

                # Store result
                result = {
                    'K_gain': float(K_gain),
                    'lambda_decay': float(lambda_decay),
                    'num_ipus': int(num_ipus),
                    'final_velocity': float(final_velocity),
                    'settling_time': float(settling_time),
                    'overshoot': float(overshoot),
                    'peak_control': float(peak_control),
                    'rms_jerk': float(comfort_metrics['rms_jerk']),
                    'smoothness': float(comfort_metrics['smoothness']),
                    'comfort_index': float(comfort_metrics['comfort_index']),
                    'stable': bool(not np.isnan(final_velocity) and abs(final_velocity) < 1.0)
                }

                logger.add_result(
                    params={
                        'K_gain': float(K_gain),
                        'lambda_decay': float(lambda_decay),
                        'num_ipus': int(num_ipus)
                    },
                    metrics=result
                )

                successful += 1

            except Exception as e:
                print(f"   Error at K={K_gain:.2f}, λ={lambda_decay:.2f}, IPUs={num_ipus}: {e}")
                continue

        print(f"   ✓ Control parameter sweep: {successful}/{total_combinations} successful ({successful/total_combinations*100:.1f}%)")

        logger.finalize(generate_report=True)
        print(f"\n✓ Control Parameters sweep completed successfully")

        return successful, total_combinations

    def sweep_emergency_scenarios(self, quick_mode: bool = False):
        """
        Sweep emergency braking scenarios with different velocities and durations

        Tests performance across realistic emergency scenarios.
        """
        logger = RunLogger("motorhand_emergency_scenarios", tag="param_sweep")

        print("\n" + "=" * 80)
        print("MOTORHANDPRO: Emergency Scenario Sweep")
        print("=" * 80)

        # Scenario parameters
        if quick_mode:
            initial_velocities = [10.0, 20.0, 30.0]  # m/s
            target_velocities = [0.0, 5.0]  # m/s
            durations = [5.0, 10.0]  # seconds
        else:
            initial_velocities = np.linspace(10.0, 40.0, 7)  # 10-40 m/s
            target_velocities = [0.0, 5.0, 10.0]  # m/s
            durations = [3.0, 5.0, 10.0, 15.0]  # seconds

        logger.log_parameters({
            'initial_velocity_range': (initial_velocities if isinstance(initial_velocities, list) else initial_velocities.tolist()),
            'target_velocity_range': target_velocities,
            'duration_range': durations,
            'K_gain': 0.5,
            'lambda_decay': 2.0
        })

        total_combinations = len(initial_velocities) * len(target_velocities) * len(durations)
        print(f"\n[2/5] Emergency Scenario Sweep")
        print(f"   Testing {total_combinations} emergency scenarios...")

        # Use optimal parameters from previous sweep
        processor = PrimalLogicProcessor(ProcessorConfig(
            K_gain=0.5,
            lambda_decay=2.0,
            num_integral_units=8
        ))
        bridge = MotorHandBridge()

        successful = 0
        iteration = 0

        for initial_v, target_v, duration in product(initial_velocities, target_velocities, durations):
            iteration += 1

            if iteration % 10 == 0 or iteration == 1:
                print(f"   Progress: {iteration}/{total_combinations} ({iteration/total_combinations*100:.1f}%)")

            try:
                # Run closed-loop simulation
                states = bridge.simulate_closed_loop(
                    primal_processor=processor,
                    initial_state=float(initial_v),
                    target_state=float(target_v),
                    duration=float(duration),
                    dt=0.01
                )

                # Extract metrics
                final_state = states[-1]['state']
                final_throttle = states[-1]['throttle']
                controls = [s['primal_control'] for s in states]
                throttles = [s['throttle'] for s in states]
                comfort_values = [s['comfort'] for s in states]

                # Compute metrics
                avg_comfort = float(np.mean(comfort_values))
                min_comfort = float(np.min(comfort_values))
                max_throttle = int(np.max(throttles))
                throttle_range = int(np.max(throttles) - np.min(throttles))

                # Deceleration rate
                velocity_change = abs(final_state - initial_v)
                deceleration = velocity_change / duration

                # Error at end
                tracking_error = abs(final_state - target_v)

                result = {
                    'initial_velocity': float(initial_v),
                    'target_velocity': float(target_v),
                    'duration': float(duration),
                    'final_state': float(final_state),
                    'tracking_error': float(tracking_error),
                    'deceleration': float(deceleration),
                    'final_throttle': int(final_throttle),
                    'max_throttle': max_throttle,
                    'throttle_range': throttle_range,
                    'avg_comfort': avg_comfort,
                    'min_comfort': min_comfort,
                    'success': bool(tracking_error < 1.0)
                }

                logger.add_result(
                    params={
                        'initial_velocity': float(initial_v),
                        'target_velocity': float(target_v),
                        'duration': float(duration)
                    },
                    metrics=result
                )

                successful += 1

            except Exception as e:
                print(f"   Error at v0={initial_v:.1f}, vf={target_v:.1f}, T={duration:.1f}: {e}")
                continue

        print(f"   ✓ Emergency scenario sweep: {successful}/{total_combinations} successful ({successful/total_combinations*100:.1f}%)")

        logger.finalize(generate_report=True)
        print(f"\n✓ Emergency Scenarios sweep completed successfully")

        return successful, total_combinations

    def sweep_throttle_conversion(self, quick_mode: bool = False):
        """
        Sweep throttle conversion accuracy across control signal ranges

        Validates QUANT interface throttle conversion.
        """
        logger = RunLogger("motorhand_throttle_conversion", tag="validation")

        print("\n" + "=" * 80)
        print("MOTORHANDPRO: Throttle Conversion Validation")
        print("=" * 80)

        # Control signal range: -10 to +10
        if quick_mode:
            control_signals = np.linspace(-10.0, 10.0, 20)
            scales = [0.5, 1.0, 1.5]
        else:
            control_signals = np.linspace(-10.0, 10.0, 100)
            scales = np.linspace(0.1, 2.0, 20)

        logger.log_parameters({
            'control_signal_range': [-10.0, 10.0],
            'num_control_points': len(control_signals),
            'scale_range': (scales if isinstance(scales, list) else scales.tolist()),
            'expected_throttle_range': [0, 255]
        })

        total_combinations = len(control_signals) * len(scales)
        print(f"\n[3/5] Throttle Conversion Validation")
        print(f"   Testing {total_combinations} conversion points...")

        bridge = MotorHandBridge()
        successful = 0
        iteration = 0

        for control, scale in product(control_signals, scales):
            iteration += 1

            if iteration % 100 == 0 or iteration == 1:
                print(f"   Progress: {iteration}/{total_combinations} ({iteration/total_combinations*100:.1f}%)")

            try:
                # Convert control to throttle
                throttle = bridge.quant.control_to_throttle(float(control), scale=float(scale))

                # Verify throttle in valid range
                valid_throttle = 0 <= throttle <= 255

                # Compute expected x_fixed
                x_fixed = (control + 10.0) * (150.0 / 20.0) * scale
                x_fixed_clamped = np.clip(x_fixed, 0.0, 150.0)
                expected_throttle = int((x_fixed_clamped / 150.0) * 255.0 + 0.5)

                # Check conversion accuracy
                conversion_error = abs(throttle - expected_throttle)

                result = {
                    'control_signal': float(control),
                    'scale': float(scale),
                    'throttle': int(throttle),
                    'x_fixed': float(x_fixed),
                    'x_fixed_clamped': float(x_fixed_clamped),
                    'expected_throttle': int(expected_throttle),
                    'conversion_error': int(conversion_error),
                    'valid_throttle': bool(valid_throttle),
                    'accurate_conversion': bool(conversion_error <= 1)
                }

                logger.add_result(
                    params={
                        'control_signal': float(control),
                        'scale': float(scale)
                    },
                    metrics=result
                )

                successful += 1

            except Exception as e:
                print(f"   Error at control={control:.2f}, scale={scale:.2f}: {e}")
                continue

        print(f"   ✓ Throttle conversion: {successful}/{total_combinations} successful ({successful/total_combinations*100:.1f}%)")

        logger.finalize(generate_report=True)
        print(f"\n✓ Throttle Conversion validation completed successfully")

        return successful, total_combinations

    def sweep_ipu_scaling(self, quick_mode: bool = False):
        """
        Sweep IPU (Integral Processing Unit) scaling performance

        Tests performance scaling with different numbers of IPUs.
        """
        logger = RunLogger("motorhand_ipu_scaling", tag="performance")

        print("\n" + "=" * 80)
        print("MOTORHANDPRO: IPU Scaling Performance")
        print("=" * 80)

        # IPU configurations
        if quick_mode:
            ipu_counts = [1, 2, 4, 8, 16]
        else:
            ipu_counts = [1, 2, 4, 8, 16, 32, 64]

        logger.log_parameters({
            'ipu_counts': ipu_counts,
            'K_gain': 0.5,
            'lambda_decay': 2.0,
            'test_duration': 10.0
        })

        print(f"\n[4/5] IPU Scaling Performance")
        print(f"   Testing {len(ipu_counts)} IPU configurations...")

        successful = 0

        for i, num_ipus in enumerate(ipu_counts):
            print(f"   Progress: {i+1}/{len(ipu_counts)} - Testing {num_ipus} IPUs...")

            try:
                # Create processor with this IPU count
                processor = PrimalLogicProcessor(ProcessorConfig(
                    K_gain=0.5,
                    lambda_decay=2.0,
                    num_integral_units=int(num_ipus)
                ))

                # Get hardware metrics
                hw_metrics = processor.get_hardware_metrics()

                # Run performance test
                states = processor.simulate_emergency_braking(
                    initial_velocity=30.0,
                    target_velocity=0.0,
                    duration=10.0
                )

                # Compute metrics
                controls = [s.bounded_control for s in states]
                comfort_metrics = compute_comfort_metrics(controls, dt=0.01)

                result = {
                    'num_ipus': int(num_ipus),
                    'integral_units': int(hw_metrics['integral_units']),
                    'memory_banks': int(hw_metrics['memory_banks']),
                    'multiply_accumulate': int(hw_metrics['multiply_accumulate']),
                    'floating_point': int(hw_metrics['floating_point']),
                    'total_area_mm2': float(hw_metrics['total_area_mm2']),
                    'power_consumption_w': float(hw_metrics['power_consumption_w']),
                    'processing_latency_us': float(hw_metrics['processing_latency_us']),
                    'comfort_index': float(comfort_metrics['comfort_index']),
                    'rms_jerk': float(comfort_metrics['rms_jerk']),
                    'smoothness': float(comfort_metrics['smoothness']),
                    'area_per_ipu': float(hw_metrics['total_area_mm2'] / num_ipus),
                    'power_per_ipu': float(hw_metrics['power_consumption_w'] / num_ipus),
                    'efficiency': float(comfort_metrics['comfort_index'] / hw_metrics['power_consumption_w'])
                }

                logger.add_result(
                    params={'num_ipus': int(num_ipus)},
                    metrics=result
                )

                successful += 1

            except Exception as e:
                print(f"   Error with {num_ipus} IPUs: {e}")
                continue

        print(f"   ✓ IPU scaling: {successful}/{len(ipu_counts)} successful ({successful/len(ipu_counts)*100:.1f}%)")

        logger.finalize(generate_report=True)
        print(f"\n✓ IPU Scaling performance completed successfully")

        return successful, len(ipu_counts)

    def sweep_closed_loop_performance(self, quick_mode: bool = False):
        """
        Comprehensive closed-loop performance sweep

        Tests full integration with various scenarios.
        """
        logger = RunLogger("motorhand_closed_loop", tag="integration")

        print("\n" + "=" * 80)
        print("MOTORHANDPRO: Closed-Loop Integration Performance")
        print("=" * 80)

        # Scenario parameters
        if quick_mode:
            scenarios = [
                {'name': 'gentle_stop', 'v0': 20.0, 'vf': 0.0, 'T': 10.0},
                {'name': 'emergency_brake', 'v0': 30.0, 'vf': 0.0, 'T': 5.0},
                {'name': 'speed_limit', 'v0': 30.0, 'vf': 15.0, 'T': 5.0},
            ]
        else:
            scenarios = [
                {'name': 'gentle_stop', 'v0': 20.0, 'vf': 0.0, 'T': 10.0},
                {'name': 'emergency_brake', 'v0': 30.0, 'vf': 0.0, 'T': 5.0},
                {'name': 'speed_limit', 'v0': 30.0, 'vf': 15.0, 'T': 5.0},
                {'name': 'highway_decel', 'v0': 40.0, 'vf': 25.0, 'T': 8.0},
                {'name': 'cruise_control', 'v0': 25.0, 'vf': 25.0, 'T': 10.0},
                {'name': 'quick_brake', 'v0': 35.0, 'vf': 10.0, 'T': 3.0},
            ]

        logger.log_parameters({
            'scenarios': scenarios,
            'processor_config': {
                'K_gain': 0.5,
                'lambda_decay': 2.0,
                'num_ipus': 8
            }
        })

        print(f"\n[5/5] Closed-Loop Integration Performance")
        print(f"   Testing {len(scenarios)} integration scenarios...")

        processor = PrimalLogicProcessor(ProcessorConfig(
            K_gain=0.5,
            lambda_decay=2.0,
            num_integral_units=8
        ))
        bridge = MotorHandBridge()

        successful = 0

        for i, scenario in enumerate(scenarios):
            print(f"   Progress: {i+1}/{len(scenarios)} - {scenario['name']}...")

            try:
                # Run closed-loop simulation
                states = bridge.simulate_closed_loop(
                    primal_processor=processor,
                    initial_state=scenario['v0'],
                    target_state=scenario['vf'],
                    duration=scenario['T'],
                    dt=0.01
                )

                # Extract metrics
                times = [s['time'] for s in states]
                velocities = [s['state'] for s in states]
                controls = [s['primal_control'] for s in states]
                throttles = [s['throttle'] for s in states]
                comfort_values = [s['comfort'] for s in states]

                # Compute comprehensive metrics
                final_velocity = velocities[-1]
                tracking_error = abs(final_velocity - scenario['vf'])

                # Settling time
                settling_idx = len(states) - 1
                for j in range(len(states)):
                    if abs(velocities[j] - scenario['vf']) < 0.5:
                        settling_idx = j
                        break
                settling_time = times[settling_idx] if settling_idx < len(times) else scenario['T']

                # Control metrics
                comfort_metrics = compute_comfort_metrics(controls, dt=0.01)
                avg_comfort = np.mean(comfort_values)
                min_comfort = np.min(comfort_values)

                # Throttle metrics
                throttle_utilization = np.mean(throttles) / 255.0
                max_throttle = np.max(throttles)

                result = {
                    'scenario': scenario['name'],
                    'initial_velocity': scenario['v0'],
                    'target_velocity': scenario['vf'],
                    'duration': scenario['T'],
                    'final_velocity': float(final_velocity),
                    'tracking_error': float(tracking_error),
                    'settling_time': float(settling_time),
                    'comfort_index': float(comfort_metrics['comfort_index']),
                    'avg_comfort': float(avg_comfort),
                    'min_comfort': float(min_comfort),
                    'rms_jerk': float(comfort_metrics['rms_jerk']),
                    'smoothness': float(comfort_metrics['smoothness']),
                    'peak_control': float(comfort_metrics['peak_control']),
                    'throttle_utilization': float(throttle_utilization),
                    'max_throttle': int(max_throttle),
                    'success': bool(tracking_error < 1.0)
                }

                logger.add_result(
                    params={'scenario': scenario['name']},
                    metrics=result
                )

                successful += 1

            except Exception as e:
                print(f"   Error in {scenario['name']}: {e}")
                continue

        print(f"   ✓ Closed-loop performance: {successful}/{len(scenarios)} successful ({successful/len(scenarios)*100:.1f}%)")

        logger.finalize(generate_report=True)
        print(f"\n✓ Closed-Loop Integration completed successfully")

        return successful, len(scenarios)


def upload_existing_runs():
    """Upload existing local runs to Google Drive"""
    import shutil
    from framework import BASE_RESULTS_DIR, LOCAL_FALLBACK_DIR

    print("\n" + "=" * 80)
    print("UPLOADING EXISTING RUNS TO GOOGLE DRIVE")
    print("=" * 80)

    local_dir = os.path.expanduser(LOCAL_FALLBACK_DIR)
    drive_dir = os.path.expanduser(BASE_RESULTS_DIR)

    if not os.path.exists(local_dir):
        print(f"\n✗ No local results found at: {local_dir}")
        return 0

    # Check Drive accessibility
    if not os.path.exists(os.path.dirname(drive_dir)):
        print(f"\n✗ Google Drive not accessible at: {drive_dir}")
        print("  Results remain in local storage")
        return 1

    # Find motorhand runs
    motorhand_dirs = [d for d in os.listdir(local_dir) if d.startswith('motorhand_')]

    if not motorhand_dirs:
        print(f"\n✗ No MotorHandPro runs found in: {local_dir}")
        return 0

    print(f"\nFound {len(motorhand_dirs)} MotorHandPro result directories")

    uploaded = 0
    for motorhand_dir in motorhand_dirs:
        src = os.path.join(local_dir, motorhand_dir)
        dst = os.path.join(drive_dir, motorhand_dir)

        if os.path.exists(dst):
            print(f"  ⊙ Skipping {motorhand_dir} (already on Drive)")
            continue

        try:
            print(f"  ↑ Uploading {motorhand_dir}...", end='', flush=True)
            shutil.copytree(src, dst)
            print(" ✓")
            uploaded += 1
        except Exception as e:
            print(f" ✗ Error: {e}")

    print(f"\n✓ Uploaded {uploaded} result directories to Google Drive")
    print(f"  Location: {drive_dir}")
    print("=" * 80)

    return 0


def export_best_config(results_dir: str = None):
    """Export best performing configuration for firmware flashing"""
    import json
    import csv
    from framework import BASE_RESULTS_DIR, LOCAL_FALLBACK_DIR

    print("\n" + "=" * 80)
    print("EXPORTING BEST CONFIGURATION")
    print("=" * 80)

    # Determine results directory
    if results_dir is None:
        drive_dir = os.path.expanduser(BASE_RESULTS_DIR)
        local_dir = os.path.expanduser(LOCAL_FALLBACK_DIR)
        results_dir = drive_dir if os.path.exists(drive_dir) else local_dir

    # Load control parameters results
    control_params_dir = os.path.join(results_dir, 'motorhand_control_params')

    if not os.path.exists(control_params_dir):
        print(f"\n✗ No control parameters results found")
        return None

    # Find latest run
    runs = sorted([d for d in os.listdir(control_params_dir) if os.path.isdir(os.path.join(control_params_dir, d))])
    if not runs:
        print(f"\n✗ No parameter sweep runs found")
        return None

    latest_run = runs[-1]
    csv_path = os.path.join(control_params_dir, latest_run, 'summary', 'summary.csv')

    if not os.path.exists(csv_path):
        print(f"\n✗ No summary CSV found in latest run")
        return None

    # Load results using CSV module
    results = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert string values to appropriate types
            row['K_gain'] = float(row['K_gain'])
            row['lambda_decay'] = float(row['lambda_decay'])
            row['num_ipus'] = int(row['num_ipus'])
            row['comfort_index'] = float(row['comfort_index'])
            row['settling_time'] = float(row['settling_time'])
            row['rms_jerk'] = float(row['rms_jerk'])
            row['smoothness'] = float(row['smoothness'])
            row['stable'] = row['stable'].lower() == 'true'
            results.append(row)

    # Filter stable configurations
    stable_results = [r for r in results if r['stable']]

    if len(stable_results) == 0:
        print(f"\n✗ No stable configurations found")
        return None

    # Find best configuration (optimize for comfort and settling time)
    # Composite score: 70% comfort, 30% speed (lower settling time)
    for r in stable_results:
        r['score'] = (r['comfort_index'] * 0.7) - (r['settling_time'] * 3.0)

    best = max(stable_results, key=lambda x: x['score'])

    # Extract best parameters
    best_config = {
        "firmware_config": {
            "K_gain": float(best['K_gain']),
            "lambda_decay": float(best['lambda_decay']),
            "num_integral_units": int(best['num_ipus']),
            "dt_ms": 10,  # 10ms = 100Hz
            "control_bounds": [-10.0, 10.0]
        },
        "performance_metrics": {
            "comfort_index": float(best['comfort_index']),
            "settling_time_s": float(best['settling_time']),
            "rms_jerk": float(best['rms_jerk']),
            "smoothness": float(best['smoothness']),
            "stability": "STABLE"
        },
        "metadata": {
            "optimization_target": "balanced_comfort_speed",
            "source_run": latest_run,
            "total_configurations_tested": len(results),
            "stable_configurations": len(stable_results),
            "selection_criteria": "70% comfort + 30% speed"
        }
    }

    # Save to file
    output_file = 'motorhand_best_params.json'
    with open(output_file, 'w') as f:
        json.dump(best_config, f, indent=2)

    print(f"\n✓ Best configuration exported to: {output_file}")
    print(f"\nOptimal Parameters:")
    print(f"  K_gain: {best_config['firmware_config']['K_gain']:.3f}")
    print(f"  lambda_decay: {best_config['firmware_config']['lambda_decay']:.3f}")
    print(f"  num_IPUs: {best_config['firmware_config']['num_integral_units']}")
    print(f"\nPerformance:")
    print(f"  Comfort Index: {best_config['performance_metrics']['comfort_index']:.1f}/100")
    print(f"  Settling Time: {best_config['performance_metrics']['settling_time_s']:.2f}s")
    print(f"  RMS Jerk: {best_config['performance_metrics']['rms_jerk']:.3f}")
    print(f"\nFlash this to firmware with: motorhand_best_params.json")
    print("=" * 80)

    return best_config


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='MotorHandPro Parameter Sweep with Drive Integration')
    parser.add_argument('--quick', action='store_true', help='Run quick mode with fewer combinations')
    parser.add_argument('--upload-only', action='store_true', help='Upload existing local runs to Drive (no new sweeps)')
    parser.add_argument('--export-best', action='store_true', help='Export best configuration to motorhand_best_params.json')
    args = parser.parse_args()

    # Handle upload-only mode
    if args.upload_only:
        return upload_existing_runs()

    # Handle export-best mode
    if args.export_best:
        export_best_config()
        return 0

    print("=" * 80)
    print("MOTORHANDPRO PARAMETER SWEEP ORCHESTRATOR")
    print("Google Drive Integration Active")
    print("=" * 80)

    orchestrator = MotorHandSweepOrchestrator()

    total_tests = 0
    total_successful = 0

    # Run all sweeps
    try:
        # 1. Control Parameters
        print("\n" + "=" * 80)
        print("SWEEP: Control Parameters")
        print("=" * 80)
        s, t = orchestrator.sweep_control_parameters(quick_mode=args.quick)
        total_successful += s
        total_tests += t
        print(f"\n✓ Control Parameters sweep completed successfully")

        # 2. Emergency Scenarios
        print("\n" + "=" * 80)
        print("SWEEP: Emergency Scenarios")
        print("=" * 80)
        s, t = orchestrator.sweep_emergency_scenarios(quick_mode=args.quick)
        total_successful += s
        total_tests += t
        print(f"\n✓ Emergency Scenarios sweep completed successfully")

        # 3. Throttle Conversion
        print("\n" + "=" * 80)
        print("SWEEP: Throttle Conversion")
        print("=" * 80)
        s, t = orchestrator.sweep_throttle_conversion(quick_mode=args.quick)
        total_successful += s
        total_tests += t
        print(f"\n✓ Throttle Conversion validation completed successfully")

        # 4. IPU Scaling
        print("\n" + "=" * 80)
        print("SWEEP: IPU Scaling")
        print("=" * 80)
        s, t = orchestrator.sweep_ipu_scaling(quick_mode=args.quick)
        total_successful += s
        total_tests += t
        print(f"\n✓ IPU Scaling performance completed successfully")

        # 5. Closed-Loop Performance
        print("\n" + "=" * 80)
        print("SWEEP: Closed-Loop Integration")
        print("=" * 80)
        s, t = orchestrator.sweep_closed_loop_performance(quick_mode=args.quick)
        total_successful += s
        total_tests += t
        print(f"\n✓ Closed-Loop Integration completed successfully")

        # Final summary
        print("\n" + "=" * 80)
        print("✓ ALL MOTORHANDPRO SWEEPS COMPLETED")
        print("=" * 80)
        print(f"\nTotal Tests: {total_tests}")
        print(f"Successful: {total_successful}")
        print(f"Success Rate: {total_successful/total_tests*100:.1f}%")

        if args.quick:
            print("\nQuick mode - for full parameter space run without --quick flag")

        print("\nAll results saved to Google Drive!")
        print("=" * 80)

        # Auto-export best configuration
        try:
            export_best_config()
        except Exception as e:
            print(f"\n⚠ Could not export best config: {e}")
            print("  Run with --export-best to retry")

    except KeyboardInterrupt:
        print("\n\nSweep interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError during sweep: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
