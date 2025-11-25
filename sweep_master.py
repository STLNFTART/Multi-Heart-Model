#!/usr/bin/env python3
"""
Master Parameter Sweep Orchestrator
Runs comprehensive parameter sweeps across all models and subsystems
Author: Lightfoot Technology
"""

import sys
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from itertools import product
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

@dataclass
class SweepResults:
    """Container for sweep results"""
    timestamp: str
    model_name: str
    parameter_space: Dict[str, List[float]]
    results: List[Dict[str, Any]]
    summary_stats: Dict[str, Any]
    total_combinations: int
    successful_runs: int
    failed_runs: int
    execution_time_s: float


class MasterSweepOrchestrator:
    """Orchestrates all parameter sweeps across all models"""

    def __init__(self, output_dir: str = "sweep_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.all_results = []

    def run_all_sweeps(self, quick_mode: bool = False):
        """Run all parameter sweeps"""
        print("=" * 80)
        print("MASTER PARAMETER SWEEP ORCHESTRATOR")
        print("Comprehensive Multi-Domain Physiological Model Analysis")
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
                result = sweep_func(quick_mode=quick_mode)
                self.all_results.append(result)
                print(f"✓ {name} sweep completed successfully")
            except Exception as e:
                print(f"✗ {name} sweep failed: {e}")
                import traceback
                traceback.print_exc()

        # Generate master summary
        self.generate_master_summary()

    def sweep_cardiac_models(self, quick_mode: bool = False) -> SweepResults:
        """Sweep all cardiac model parameters"""
        from src.cardiac import VanDerPolOscillator

        print("\n[1/6] Van der Pol Oscillator...")

        # Define parameter space
        if quick_mode:
            mu_values = np.linspace(0.5, 3.0, 5)
            omega_values = np.linspace(0.5, 2.0, 5)
            damping_values = np.linspace(0.05, 0.3, 5)
        else:
            mu_values = np.linspace(0.5, 3.0, 10)
            omega_values = np.linspace(0.5, 2.0, 10)
            damping_values = np.linspace(0.05, 0.3, 10)

        param_space = {
            'mu': mu_values.tolist(),
            'omega': omega_values.tolist(),
            'damping': damping_values.tolist()
        }

        results = []
        total = len(mu_values) * len(omega_values) * len(damping_values)
        successful = 0
        failed = 0

        start_time = time.time()

        print(f"   Testing {total} parameter combinations...")

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

                results.append({
                    'mu': float(mu),
                    'omega': float(omega),
                    'damping': float(damping),
                    'amplitude': float(amplitude),
                    'frequency': float(frequency),
                    'mean_energy': float(mean_energy),
                    'stable': bool(not np.isnan(amplitude) and not np.isinf(amplitude)),
                    'final_position': float(positions[-1]),
                    'final_velocity': float(velocities[-1])
                })
                successful += 1

            except Exception as e:
                results.append({
                    'mu': mu,
                    'omega': omega,
                    'damping': damping,
                    'error': str(e),
                    'stable': False
                })
                failed += 1

        execution_time = time.time() - start_time

        # Calculate summary statistics
        stable_results = [r for r in results if r.get('stable', False)]
        summary = {
            'total_combinations': total,
            'successful_runs': successful,
            'failed_runs': failed,
            'stability_rate': successful / total if total > 0 else 0,
            'mean_amplitude': np.mean([r['amplitude'] for r in stable_results]) if stable_results else 0,
            'mean_frequency': np.mean([r['frequency'] for r in stable_results]) if stable_results else 0,
            'execution_time_s': execution_time
        }

        print(f"   ✓ Van der Pol sweep: {successful}/{total} successful ({100*successful/total:.1f}%)")
        print(f"   Mean amplitude: {summary['mean_amplitude']:.3f}")
        print(f"   Mean frequency: {summary['mean_frequency']:.3f} Hz")

        sweep_result = SweepResults(
            timestamp=datetime.now().isoformat(),
            model_name="VanDerPolOscillator",
            parameter_space=param_space,
            results=results,
            summary_stats=summary,
            total_combinations=total,
            successful_runs=successful,
            failed_runs=failed,
            execution_time_s=execution_time
        )

        # Save results
        output_file = self.output_dir / f"cardiac_vanderpol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(asdict(sweep_result), f, indent=2)
        print(f"   Results saved to: {output_file}")

        return sweep_result

    def sweep_hbcm(self, quick_mode: bool = False) -> SweepResults:
        """Sweep Heart-Brain Coupling Model parameters"""
        from src.cardiac import VanDerPolOscillator
        from src.neural import FitzHughNagumo
        from src.coupling import HeartBrainCouplingModel

        print("\n[2/6] Heart-Brain Coupling Model...")

        # Define parameter space
        if quick_mode:
            gain_values = np.linspace(0.0, 1.0, 5)
            delay_values = np.linspace(0.05, 0.3, 5)
        else:
            gain_values = np.linspace(0.0, 1.0, 10)
            delay_values = np.linspace(0.05, 0.3, 10)

        param_space = {
            'neural_to_cardiac_gain': gain_values.tolist(),
            'cardiac_to_neural_gain': gain_values.tolist(),
            'delay': delay_values.tolist()
        }

        results = []
        total = len(gain_values) ** 2 * len(delay_values)
        successful = 0
        failed = 0

        start_time = time.time()

        print(f"   Testing {total} coupling configurations...")

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
                if len(trajectory) == 0:
                    raise ValueError("Empty trajectory")

                times = [t for t, state in trajectory]
                neural_v = [state[0] for t, state in trajectory]
                cardiac_x = [state[2] for t, state in trajectory]
                neural_states = [(state[0], state[1]) for t, state in trajectory]
                cardiac_states = [(state[2], state[3]) for t, state in trajectory]

                # Synchronization metric (correlation)
                correlation = np.corrcoef(neural_v, cardiac_x)[0, 1] if len(neural_v) > 1 else 0

                # Energy metrics
                neural_energy = np.mean([v**2 + w**2 for v, w in neural_states])
                cardiac_energy = np.mean([x**2 + y**2 for x, y in cardiac_states])

                results.append({
                    'neural_to_cardiac_gain': float(nc_gain),
                    'cardiac_to_neural_gain': float(cn_gain),
                    'delay': float(delay),
                    'correlation': float(correlation) if not np.isnan(correlation) else 0.0,
                    'neural_energy': float(neural_energy),
                    'cardiac_energy': float(cardiac_energy),
                    'stable': bool(not np.isnan(correlation)),
                    'timesteps': int(len(times))
                })
                successful += 1

            except Exception as e:
                results.append({
                    'neural_to_cardiac_gain': float(nc_gain),
                    'cardiac_to_neural_gain': float(cn_gain),
                    'delay': float(delay),
                    'error': str(e),
                    'stable': False
                })
                failed += 1

        execution_time = time.time() - start_time

        # Summary statistics
        stable_results = [r for r in results if r.get('stable', False)]
        summary = {
            'total_combinations': total,
            'successful_runs': successful,
            'failed_runs': failed,
            'mean_correlation': np.mean([r['correlation'] for r in stable_results]) if stable_results else 0,
            'max_correlation': max([r['correlation'] for r in stable_results]) if stable_results else 0,
            'execution_time_s': execution_time
        }

        print(f"   ✓ HBCM sweep: {successful}/{total} successful ({100*successful/total:.1f}%)")
        print(f"   Mean neural-cardiac correlation: {summary['mean_correlation']:.3f}")
        print(f"   Max correlation: {summary['max_correlation']:.3f}")

        sweep_result = SweepResults(
            timestamp=datetime.now().isoformat(),
            model_name="HeartBrainCouplingModel",
            parameter_space=param_space,
            results=results,
            summary_stats=summary,
            total_combinations=total,
            successful_runs=successful,
            failed_runs=failed,
            execution_time_s=execution_time
        )

        # Save results
        output_file = self.output_dir / f"hbcm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(asdict(sweep_result), f, indent=2)
        print(f"   Results saved to: {output_file}")

        return sweep_result

    def sweep_plp(self, quick_mode: bool = False) -> SweepResults:
        """Sweep Primal Logic Processor parameters"""
        from src.microprocessor import PrimalLogicProcessor, ProcessorConfig

        print("\n[3/6] Primal Logic Processor...")

        # Define parameter space
        if quick_mode:
            k_gain_values = np.linspace(0.1, 2.0, 5)
            lambda_values = np.linspace(0.5, 5.0, 5)
            dt_values = [0.001, 0.01, 0.1]
        else:
            k_gain_values = np.linspace(0.1, 2.0, 10)
            lambda_values = np.linspace(0.5, 5.0, 10)
            dt_values = [0.0001, 0.001, 0.01, 0.1]

        param_space = {
            'K_gain': k_gain_values.tolist(),
            'lambda_decay': lambda_values.tolist(),
            'dt': dt_values
        }

        results = []
        total = len(k_gain_values) * len(lambda_values) * len(dt_values)
        successful = 0
        failed = 0

        start_time = time.time()

        print(f"   Testing {total} control configurations...")

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
                current_value = 30.0  # Initial error
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

                    # Simple integration
                    current_value += control * dt
                    current_value = max(0.0, current_value)

                    trajectory.append(current_value)
                    controls.append(control)
                    t += dt

                # Calculate metrics
                settling_time = None
                for j, val in enumerate(trajectory):
                    if abs(val - target) < 0.05 * 30.0:  # 5% of initial
                        settling_time = j * dt
                        break

                overshoot = max(0, min(trajectory) - target) if target < trajectory[0] else max(0, max(trajectory) - target)
                steady_state_error = abs(trajectory[-1] - target)
                control_effort = np.sum(np.abs(controls))

                results.append({
                    'K_gain': float(k_gain),
                    'lambda_decay': float(lambda_decay),
                    'dt': float(dt),
                    'settling_time': float(settling_time) if settling_time else float(duration),
                    'overshoot': float(overshoot),
                    'steady_state_error': float(steady_state_error),
                    'control_effort': float(control_effort),
                    'stable': bool(not np.isnan(steady_state_error) and steady_state_error < 5.0),
                    'final_value': float(trajectory[-1])
                })
                successful += 1

            except Exception as e:
                results.append({
                    'K_gain': k_gain,
                    'lambda_decay': lambda_decay,
                    'dt': dt,
                    'error': str(e),
                    'stable': False
                })
                failed += 1

        execution_time = time.time() - start_time

        # Summary statistics
        stable_results = [r for r in results if r.get('stable', False)]
        summary = {
            'total_combinations': total,
            'successful_runs': successful,
            'failed_runs': failed,
            'mean_settling_time': np.mean([r['settling_time'] for r in stable_results]) if stable_results else 0,
            'mean_steady_state_error': np.mean([r['steady_state_error'] for r in stable_results]) if stable_results else 0,
            'execution_time_s': execution_time
        }

        print(f"   ✓ PLP sweep: {successful}/{total} successful ({100*successful/total:.1f}%)")
        print(f"   Mean settling time: {summary['mean_settling_time']:.3f} s")
        print(f"   Mean steady-state error: {summary['mean_steady_state_error']:.3f}")

        sweep_result = SweepResults(
            timestamp=datetime.now().isoformat(),
            model_name="PrimalLogicProcessor",
            parameter_space=param_space,
            results=results,
            summary_stats=summary,
            total_combinations=total,
            successful_runs=successful,
            failed_runs=failed,
            execution_time_s=execution_time
        )

        # Save results
        output_file = self.output_dir / f"plp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(asdict(sweep_result), f, indent=2)
        print(f"   Results saved to: {output_file}")

        return sweep_result

    def sweep_organchip(self, quick_mode: bool = False) -> SweepResults:
        """Sweep Organ-On-Chip parameters"""
        from src.organchip.orchestrator import create_default_organ_chip_suite

        print("\n[4/6] Organ-On-Chip Suite...")

        # Define parameter space
        if quick_mode:
            dose_values = [10.0, 50.0, 100.0, 200.0, 500.0]
            duration_values = [24.0, 48.0]
        else:
            dose_values = [1.0, 10.0, 50.0, 100.0, 200.0, 500.0, 1000.0]
            duration_values = [12.0, 24.0, 48.0, 72.0]

        param_space = {
            'dose_mg': dose_values,
            'duration_hours': duration_values
        }

        results = []
        total = len(dose_values) * len(duration_values)
        successful = 0
        failed = 0

        start_time = time.time()

        print(f"   Testing {total} drug exposure scenarios...")

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

                results.append({
                    'dose_mg': float(dose),
                    'duration_hours': float(duration),
                    'overall_toxicity_score': float(toxicity['overall_toxicity_score']),
                    'overall_severity': str(toxicity['overall_severity']),
                    'liver_severity': str(toxicity['liver']['severity']),
                    'cardiac_severity': str(toxicity['cardiac']['severity']),
                    'inflammatory_index': float(toxicity.get('inflammatory_index', 0.0)),
                    'stable': True,
                    'timesteps': int(len(trajectory))
                })
                successful += 1

            except Exception as e:
                results.append({
                    'dose_mg': dose,
                    'duration_hours': duration,
                    'error': str(e),
                    'stable': False
                })
                failed += 1

        execution_time = time.time() - start_time

        # Summary statistics
        stable_results = [r for r in results if r.get('stable', False)]
        summary = {
            'total_combinations': total,
            'successful_runs': successful,
            'failed_runs': failed,
            'mean_toxicity_score': np.mean([r['overall_toxicity_score'] for r in stable_results]) if stable_results else 0,
            'max_toxicity_score': max([r['overall_toxicity_score'] for r in stable_results]) if stable_results else 0,
            'execution_time_s': execution_time
        }

        print(f"   ✓ Organ chip sweep: {successful}/{total} successful ({100*successful/total:.1f}%)")
        print(f"   Mean toxicity score: {summary['mean_toxicity_score']:.3f}")
        print(f"   Max toxicity score: {summary['max_toxicity_score']:.3f}")

        sweep_result = SweepResults(
            timestamp=datetime.now().isoformat(),
            model_name="OrganChipSuite",
            parameter_space=param_space,
            results=results,
            summary_stats=summary,
            total_combinations=total,
            successful_runs=successful,
            failed_runs=failed,
            execution_time_s=execution_time
        )

        # Save results
        output_file = self.output_dir / f"organchip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(asdict(sweep_result), f, indent=2)
        print(f"   Results saved to: {output_file}")

        return sweep_result

    def generate_master_summary(self):
        """Generate comprehensive summary of all sweeps"""
        print("\n" + "=" * 80)
        print("MASTER SUMMARY - ALL PARAMETER SWEEPS")
        print("=" * 80)

        summary_file = self.output_dir / f"master_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(summary_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("COMPREHENSIVE PARAMETER SWEEP SUMMARY\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")

            total_combinations = 0
            total_successful = 0
            total_failed = 0
            total_time = 0.0

            for result in self.all_results:
                f.write(f"\n{'-' * 80}\n")
                f.write(f"Model: {result.model_name}\n")
                f.write(f"{'-' * 80}\n")
                f.write(f"Total combinations tested: {result.total_combinations}\n")
                f.write(f"Successful runs: {result.successful_runs} ({100*result.successful_runs/result.total_combinations:.1f}%)\n")
                f.write(f"Failed runs: {result.failed_runs}\n")
                f.write(f"Execution time: {result.execution_time_s:.2f} seconds\n")
                f.write(f"\nSummary Statistics:\n")
                for key, value in result.summary_stats.items():
                    f.write(f"  {key}: {value}\n")

                total_combinations += result.total_combinations
                total_successful += result.successful_runs
                total_failed += result.failed_runs
                total_time += result.execution_time_s

            f.write(f"\n{'=' * 80}\n")
            f.write("OVERALL TOTALS\n")
            f.write(f"{'=' * 80}\n")
            f.write(f"Total parameter combinations: {total_combinations}\n")
            f.write(f"Total successful runs: {total_successful} ({100*total_successful/total_combinations:.1f}%)\n")
            f.write(f"Total failed runs: {total_failed}\n")
            f.write(f"Total execution time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)\n")
            f.write(f"Average throughput: {total_combinations/total_time:.2f} combinations/second\n")

        print(f"\n✓ Master summary saved to: {summary_file}")
        print(f"\nOVERALL STATISTICS:")
        print(f"  Total combinations: {total_combinations}")
        print(f"  Successful: {total_successful} ({100*total_successful/total_combinations:.1f}%)")
        print(f"  Failed: {total_failed}")
        print(f"  Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print(f"  Throughput: {total_combinations/total_time:.2f} combinations/second")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Master Parameter Sweep Orchestrator")
    parser.add_argument('--quick', action='store_true', help='Run quick mode with fewer parameter combinations')
    parser.add_argument('--output-dir', type=str, default='sweep_results', help='Output directory for results')

    args = parser.parse_args()

    orchestrator = MasterSweepOrchestrator(output_dir=args.output_dir)
    orchestrator.run_all_sweeps(quick_mode=args.quick)

    print("\n" + "=" * 80)
    print("✓ ALL PARAMETER SWEEPS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
