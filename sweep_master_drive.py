#!/usr/bin/env python3
"""
Master Parameter Sweep Orchestrator with Google Drive Integration
Runs comprehensive parameter sweeps across all models and subsystems
Results automatically save to Google Drive

Author: Lightfoot Technology
"""

import sys
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from itertools import product
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import unified framework
from framework import RunLogger

# Import models
from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel
from src.microprocessor import PrimalLogicProcessor, ProcessorConfig
from src.organchip.orchestrator import create_default_organ_chip_suite


class MasterSweepOrchestrator:
    """Orchestrates all parameter sweeps with Google Drive integration"""

    def __init__(self):
        self.sweep_results = []

    def run_all_sweeps(self, quick_mode: bool = False):
        """Run all parameter sweeps"""
        print("=" * 80)
        print("MASTER PARAMETER SWEEP ORCHESTRATOR")
        print("Google Drive Integration Active")
        print("=" * 80)

        sweeps = [
            ("Cardiac Models", self.sweep_cardiac_models),
            ("Heart-Brain Coupling", self.sweep_hbcm),
            ("Primal Logic Processor", self.sweep_plp),
            ("Organ-On-Chip", self.sweep_organchip),
        ]

        for name, sweep_func in sweeps:
            print(f"\n{'=' * 80}")
            print(f"SWEEP: {name}")
            print("=" * 80)
            try:
                sweep_func(quick_mode=quick_mode)
                print(f"✓ {name} sweep completed successfully")
            except Exception as e:
                print(f"✗ {name} sweep failed: {e}")
                import traceback
                traceback.print_exc()

        print("\n" + "=" * 80)
        print("✓ ALL PARAMETER SWEEPS COMPLETED")
        print("=" * 80)

    def sweep_cardiac_models(self, quick_mode: bool = False):
        """Sweep Van der Pol Oscillator parameters"""
        logger = RunLogger("cardiac_vanderpol", tag="param_sweep")

        print("\n[1/4] Van der Pol Oscillator...")

        # Define parameter space
        if quick_mode:
            mu_values = np.linspace(0.5, 3.0, 5)
            omega_values = np.linspace(0.5, 2.0, 5)
            damping_values = np.linspace(0.05, 0.3, 5)
        else:
            mu_values = np.linspace(0.5, 3.0, 10)
            omega_values = np.linspace(0.5, 2.0, 10)
            damping_values = np.linspace(0.05, 0.3, 10)

        logger.log_parameters({
            'mu_range': mu_values.tolist(),
            'omega_range': omega_values.tolist(),
            'damping_range': damping_values.tolist(),
        })

        total = len(mu_values) * len(omega_values) * len(damping_values)
        print(f"   Testing {total} parameter combinations...")

        successful = 0
        for i, (mu, omega, damping) in enumerate(product(mu_values, omega_values, damping_values)):
            if i % 100 == 0:
                print(f"   Progress: {i}/{total} ({100*i/total:.1f}%)")

            try:
                model = VanDerPolOscillator(mu=mu, omega=omega, damping=damping)

                # Run short simulation
                state = (1.0, 0.0)
                trajectory = []
                t = 0.0
                dt = 0.001
                duration = 2.0

                while t < duration:
                    state = model.step(t, state, dt)
                    trajectory.append((t, state))
                    t += dt

                # Calculate metrics
                positions = [s[0] for _, s in trajectory]
                velocities = [s[1] for _, s in trajectory]

                amplitude = max(positions) - min(positions)
                mean_energy = np.mean([p**2 + v**2 for p, v in zip(positions, velocities)])

                # Detect oscillations
                zero_crossings = sum(1 for i in range(1, len(positions))
                                    if positions[i-1] * positions[i] < 0)
                frequency = zero_crossings / (2 * duration)

                # Log result
                logger.add_result(
                    params={
                        'mu': float(mu),
                        'omega': float(omega),
                        'damping': float(damping)
                    },
                    metrics={
                        'amplitude': float(amplitude),
                        'frequency': float(frequency),
                        'mean_energy': float(mean_energy),
                        'stable': bool(not np.isnan(amplitude) and not np.isinf(amplitude)),
                        'final_position': float(positions[-1]),
                        'final_velocity': float(velocities[-1])
                    }
                )
                successful += 1

            except Exception as e:
                logger.add_result(
                    params={'mu': float(mu), 'omega': float(omega), 'damping': float(damping)},
                    metrics={'error': str(e), 'stable': False}
                )

            # Periodic checkpoints
            if (i + 1) % 250 == 0:
                logger.save_checkpoint(f"checkpoint_{i+1}")

        print(f"   ✓ Van der Pol sweep: {successful}/{total} successful ({100*successful/total:.1f}%)")
        logger.finalize(generate_report=True)

    def sweep_hbcm(self, quick_mode: bool = False):
        """Sweep Heart-Brain Coupling Model parameters"""
        logger = RunLogger("heart_brain_coupling", tag="param_sweep")

        print("\n[2/4] Heart-Brain Coupling Model...")

        # Define parameter space
        if quick_mode:
            gain_values = np.linspace(0.0, 1.0, 5)
            delay_values = np.linspace(0.05, 0.3, 5)
        else:
            gain_values = np.linspace(0.0, 1.0, 10)
            delay_values = np.linspace(0.05, 0.3, 10)

        logger.log_parameters({
            'gain_range': gain_values.tolist(),
            'delay_range': delay_values.tolist(),
        })

        total = len(gain_values) ** 2 * len(delay_values)
        print(f"   Testing {total} coupling configurations...")

        successful = 0
        for i, (nc_gain, cn_gain, delay) in enumerate(product(gain_values, gain_values, delay_values)):
            if i % 50 == 0:
                print(f"   Progress: {i}/{total} ({100*i/total:.1f}%)")

            try:
                neural = FitzHughNagumo(stimulus_amplitude=0.5)
                cardiac = VanDerPolOscillator(mu=1.5, omega=1.0)
                hbcm = HeartBrainCouplingModel(
                    neural_model=neural,
                    cardiac_model=cardiac
                )

                # Override coupling parameters
                hbcm.neural_to_cardiac_gain = nc_gain
                hbcm.cardiac_to_neural_gain = cn_gain
                hbcm.neural_to_cardiac_delay = delay
                hbcm.cardiac_to_neural_delay = delay

                # Run simulation
                initial_state = (0.0, 0.0, 1.0, 0.0)
                trajectory = hbcm.simulate(initial_state, t_span=(0.0, 10.0), dt=0.001)

                # Extract time series
                times = [t for t, state in trajectory]
                neural_v = [state[0] for t, state in trajectory]
                cardiac_x = [state[2] for t, state in trajectory]
                neural_states = [(state[0], state[1]) for t, state in trajectory]
                cardiac_states = [(state[2], state[3]) for t, state in trajectory]

                # Calculate metrics
                correlation = np.corrcoef(neural_v, cardiac_x)[0, 1] if len(neural_v) > 1 else 0
                neural_energy = np.mean([v**2 + w**2 for v, w in neural_states])
                cardiac_energy = np.mean([x**2 + y**2 for x, y in cardiac_states])

                logger.add_result(
                    params={
                        'neural_to_cardiac_gain': float(nc_gain),
                        'cardiac_to_neural_gain': float(cn_gain),
                        'delay': float(delay)
                    },
                    metrics={
                        'correlation': float(correlation) if not np.isnan(correlation) else 0.0,
                        'neural_energy': float(neural_energy),
                        'cardiac_energy': float(cardiac_energy),
                        'stable': bool(not np.isnan(correlation)),
                        'timesteps': int(len(times))
                    }
                )
                successful += 1

            except Exception as e:
                logger.add_result(
                    params={'neural_to_cardiac_gain': float(nc_gain), 'cardiac_to_neural_gain': float(cn_gain), 'delay': float(delay)},
                    metrics={'error': str(e), 'stable': False}
                )

            # Periodic checkpoints
            if (i + 1) % 100 == 0:
                logger.save_checkpoint(f"checkpoint_{i+1}")

        print(f"   ✓ HBCM sweep: {successful}/{total} successful ({100*successful/total:.1f}%)")
        logger.finalize(generate_report=True)

    def sweep_plp(self, quick_mode: bool = False):
        """Sweep Primal Logic Processor parameters"""
        logger = RunLogger("primal_logic", tag="param_sweep")

        print("\n[3/4] Primal Logic Processor...")

        # Define parameter space
        if quick_mode:
            k_gain_values = np.linspace(0.1, 2.0, 5)
            lambda_values = np.linspace(0.5, 5.0, 5)
            dt_values = [0.001, 0.01, 0.1]
        else:
            k_gain_values = np.linspace(0.1, 2.0, 10)
            lambda_values = np.linspace(0.5, 5.0, 10)
            dt_values = [0.0001, 0.001, 0.01, 0.1]

        logger.log_parameters({
            'K_gain_range': k_gain_values.tolist(),
            'lambda_range': lambda_values.tolist(),
            'dt_values': dt_values,
        })

        total = len(k_gain_values) * len(lambda_values) * len(dt_values)
        print(f"   Testing {total} control configurations...")

        successful = 0
        for i, (k_gain, lambda_decay, dt) in enumerate(product(k_gain_values, lambda_values, dt_values)):
            if i % 20 == 0:
                print(f"   Progress: {i}/{total} ({100*i/total:.1f}%)")

            try:
                config = ProcessorConfig(
                    K_gain=k_gain,
                    lambda_decay=lambda_decay,
                    dt=dt
                )
                processor = PrimalLogicProcessor(config)

                # Simulate step response
                target = 0.0
                current_value = 30.0
                t = 0.0
                duration = 5.0

                trajectory = []
                controls = []

                while t < duration:
                    control, state = processor.compute_control(
                        current_value=current_value,
                        target_value=target,
                        timestamp=t
                    )

                    current_value += control * dt
                    current_value = max(0.0, current_value)

                    trajectory.append(current_value)
                    controls.append(control)
                    t += dt

                # Calculate metrics
                settling_time = None
                for j, val in enumerate(trajectory):
                    if abs(val - target) < 0.05 * 30.0:
                        settling_time = j * dt
                        break

                overshoot = max(0, min(trajectory) - target) if target < trajectory[0] else max(0, max(trajectory) - target)
                steady_state_error = abs(trajectory[-1] - target)
                control_effort = np.sum(np.abs(controls))

                logger.add_result(
                    params={
                        'K_gain': float(k_gain),
                        'lambda_decay': float(lambda_decay),
                        'dt': float(dt)
                    },
                    metrics={
                        'settling_time': float(settling_time) if settling_time else float(duration),
                        'overshoot': float(overshoot),
                        'steady_state_error': float(steady_state_error),
                        'control_effort': float(control_effort),
                        'stable': bool(not np.isnan(steady_state_error) and steady_state_error < 5.0),
                        'final_value': float(trajectory[-1])
                    }
                )
                successful += 1

            except Exception as e:
                logger.add_result(
                    params={'K_gain': float(k_gain), 'lambda_decay': float(lambda_decay), 'dt': float(dt)},
                    metrics={'error': str(e), 'stable': False}
                )

            # Periodic checkpoints
            if (i + 1) % 50 == 0:
                logger.save_checkpoint(f"checkpoint_{i+1}")

        print(f"   ✓ PLP sweep: {successful}/{total} successful ({100*successful/total:.1f}%)")
        logger.finalize(generate_report=True)

    def sweep_organchip(self, quick_mode: bool = False):
        """Sweep Organ-On-Chip parameters"""
        logger = RunLogger("organ_chip", tag="param_sweep")

        print("\n[4/4] Organ-On-Chip Suite...")

        # Define parameter space
        if quick_mode:
            dose_values = [10.0, 50.0, 100.0, 200.0, 500.0]
            duration_values = [24.0, 48.0]
        else:
            dose_values = [1.0, 10.0, 50.0, 100.0, 200.0, 500.0, 1000.0]
            duration_values = [12.0, 24.0, 48.0, 72.0]

        logger.log_parameters({
            'dose_mg_values': dose_values,
            'duration_hours_values': duration_values,
        })

        total = len(dose_values) * len(duration_values)
        print(f"   Testing {total} drug exposure scenarios...")

        successful = 0
        for i, (dose, duration) in enumerate(product(dose_values, duration_values)):
            print(f"   Progress: {i+1}/{total} ({100*(i+1)/total:.1f}%) - Dose: {dose} mg, Duration: {duration} h")

            try:
                suite = create_default_organ_chip_suite()
                suite.verbose = False

                # Run simulation
                trajectory, toxicity = suite.run_complete_study(
                    dose_mg=dose,
                    duration_hours=duration,
                    dt=0.5,
                    export_file=None
                )

                logger.add_result(
                    params={
                        'dose_mg': float(dose),
                        'duration_hours': float(duration)
                    },
                    metrics={
                        'overall_toxicity_score': float(toxicity['overall_toxicity_score']),
                        'overall_severity': str(toxicity['overall_severity']),
                        'liver_severity': str(toxicity['liver']['severity']),
                        'cardiac_severity': str(toxicity['cardiac']['severity']),
                        'inflammatory_index': float(toxicity.get('inflammatory_index', 0.0)),
                        'stable': True,
                        'timesteps': int(len(trajectory))
                    }
                )
                successful += 1

            except Exception as e:
                logger.add_result(
                    params={'dose_mg': float(dose), 'duration_hours': float(duration)},
                    metrics={'error': str(e), 'stable': False}
                )

        print(f"   ✓ Organ chip sweep: {successful}/{total} successful ({100*successful/total:.1f}%)")
        logger.finalize(generate_report=True)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Master Parameter Sweep with Drive Integration")
    parser.add_argument('--quick', action='store_true', help='Run quick mode with fewer parameter combinations')

    args = parser.parse_args()

    orchestrator = MasterSweepOrchestrator()
    orchestrator.run_all_sweeps(quick_mode=args.quick)


if __name__ == "__main__":
    main()
