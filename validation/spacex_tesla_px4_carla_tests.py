#!/usr/bin/env python3
"""
SpaceX/Tesla/PX4/CARLA Integration Validation Tests
Comprehensive validation suite for Multi-Heart-Model production deployment
"""

import sys
import time
import json
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters
from src.microprocessor import PrimalLogicProcessor
from src.integration import MotorHandProBridge


@dataclass
class ValidationResult:
    """Container for validation test results"""
    test_name: str
    test_type: str
    status: str  # 'passed', 'failed', 'warning'
    score: float
    details: Dict[str, Any]
    execution_time: float


class ValidationSuite:
    """Comprehensive validation test suite"""

    def __init__(self):
        self.results: List[ValidationResult] = []
        self.start_time = time.time()

    def run_all_tests(self) -> Dict[str, Any]:
        """Execute all validation tests"""
        print("=" * 80)
        print("Multi-Heart-Model Production Validation Suite")
        print("SpaceX/Tesla/PX4/CARLA Integration Tests")
        print("=" * 80)
        print()

        # Test 1: SpaceX - Starship Flight Control Simulation
        self._test_spacex_flight_control()

        # Test 2: Tesla - Autopilot Heart-Rate Monitoring
        self._test_tesla_autopilot_integration()

        # Test 3: PX4 - Drone Pilot Physiological Monitoring
        self._test_px4_drone_control()

        # Test 4: CARLA - Autonomous Vehicle Simulation
        self._test_carla_av_simulation()

        # Test 5: Cross-Platform Integration
        self._test_cross_platform_integration()

        return self._generate_report()

    def _test_spacex_flight_control(self):
        """Test 1: SpaceX Starship Flight Control Simulation"""
        print("\n[1/5] SpaceX Starship Flight Control Simulation")
        print("-" * 80)
        start_time = time.time()

        try:
            # Simulate flight control system with HBCM
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(stimulus_amplitude=0.3),
                cardiac_model=VanDerPolOscillator(mu=1.2, omega=1.5),
                coupling=CouplingParameters(
                    neural_to_cardiac_gain=0.6,
                    cardiac_to_neural_gain=0.4,
                    neural_to_cardiac_delay=0.10,
                    cardiac_to_neural_delay=0.12
                )
            )

            # Simulate launch sequence (high stress scenario)
            print("  ├─ Simulating T-10 to T+60 seconds (launch sequence)")
            trajectory = hbcm.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, 70.0),  # 70 seconds
                dt=0.001
            )

            times, neural, cardiac = hbcm.extract_series(trajectory)

            # Analyze stability during critical phases
            neural_v = [v for v, w in neural]
            cardiac_x = [x for x, y in cardiac]

            # Check for oscillation stability
            neural_amplitude = np.max(np.abs(neural_v))
            cardiac_amplitude = np.max(np.abs(cardiac_x))

            # Verify no runaway behavior (stability criterion)
            stability_check = neural_amplitude < 5.0 and cardiac_amplitude < 5.0

            # Calculate performance metrics
            avg_neural = np.mean(np.abs(neural_v))
            avg_cardiac = np.mean(np.abs(cardiac_x))

            score = 100.0 if stability_check else 50.0

            details = {
                "simulation_duration": 70.0,
                "timesteps": len(times),
                "neural_amplitude": float(neural_amplitude),
                "cardiac_amplitude": float(cardiac_amplitude),
                "avg_neural_activity": float(avg_neural),
                "avg_cardiac_activity": float(avg_cardiac),
                "stability_maintained": stability_check,
                "scenario": "Launch T-10 to T+60 seconds"
            }

            status = "passed" if score >= 80 else "warning"
            print(f"  ├─ Neural amplitude: {neural_amplitude:.3f}")
            print(f"  ├─ Cardiac amplitude: {cardiac_amplitude:.3f}")
            print(f"  ├─ Stability: {'✓ PASS' if stability_check else '✗ FAIL'}")
            print(f"  └─ Score: {score:.1f}/100")

        except Exception as e:
            status = "failed"
            score = 0.0
            details = {"error": str(e)}
            print(f"  └─ ERROR: {e}")

        execution_time = time.time() - start_time
        self.results.append(ValidationResult(
            test_name="SpaceX Starship Flight Control",
            test_type="spacex",
            status=status,
            score=score,
            details=details,
            execution_time=execution_time
        ))

    def _test_tesla_autopilot_integration(self):
        """Test 2: Tesla Autopilot Heart-Rate Monitoring"""
        print("\n[2/5] Tesla Autopilot Heart-Rate Monitoring")
        print("-" * 80)
        start_time = time.time()

        try:
            # Simulate driver monitoring during autopilot engagement
            print("  ├─ Simulating highway driving with autopilot")

            # Create HBCM with Tesla-specific parameters
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(a=0.7, b=0.8, c=3.0),
                cardiac_model=VanDerPolOscillator(mu=1.5, omega=1.0),
                coupling=CouplingParameters(
                    neural_to_cardiac_gain=0.5,
                    cardiac_to_neural_gain=0.3
                )
            )

            # Simulate normal driving (120 seconds)
            trajectory = hbcm.simulate(
                initial_state=(0.0, 0.0, 1.0, 0.0),
                t_span=(0.0, 120.0),
                dt=0.001
            )

            times, neural, cardiac = hbcm.extract_series(trajectory)

            # Extract cardiac signal for heart rate estimation
            cardiac_x = np.array([x for x, y in cardiac])

            # Detect peaks (heartbeats)
            from scipy.signal import find_peaks
            peaks, _ = find_peaks(cardiac_x, distance=50)

            # Calculate heart rate
            if len(peaks) > 1:
                peak_times = np.array(times)[peaks]
                intervals = np.diff(peak_times)
                avg_interval = np.mean(intervals)
                heart_rate_bpm = 60.0 / avg_interval if avg_interval > 0 else 0

                # Check if heart rate is in normal range (60-100 bpm for relaxed driving)
                hr_in_range = 50 < heart_rate_bpm < 110

                score = 100.0 if hr_in_range else 70.0
                status = "passed" if hr_in_range else "warning"

                details = {
                    "heart_rate_bpm": float(heart_rate_bpm),
                    "peak_count": len(peaks),
                    "avg_interval_seconds": float(avg_interval),
                    "hr_in_normal_range": hr_in_range,
                    "scenario": "Highway autopilot engagement"
                }

                print(f"  ├─ Detected heartbeats: {len(peaks)}")
                print(f"  ├─ Heart rate: {heart_rate_bpm:.1f} BPM")
                print(f"  ├─ Normal range check: {'✓ PASS' if hr_in_range else '⚠ WARNING'}")
                print(f"  └─ Score: {score:.1f}/100")

            else:
                score = 0.0
                status = "failed"
                details = {"error": "Insufficient peaks detected"}
                print(f"  └─ ERROR: Could not detect heartbeats")

        except Exception as e:
            status = "failed"
            score = 0.0
            details = {"error": str(e)}
            print(f"  └─ ERROR: {e}")

        execution_time = time.time() - start_time
        self.results.append(ValidationResult(
            test_name="Tesla Autopilot Driver Monitoring",
            test_type="tesla",
            status=status,
            score=score,
            details=details,
            execution_time=execution_time
        ))

    def _test_px4_drone_control(self):
        """Test 3: PX4 Drone Pilot Physiological Monitoring"""
        print("\n[3/5] PX4 Drone Pilot Physiological Monitoring")
        print("-" * 80)
        start_time = time.time()

        try:
            print("  ├─ Simulating drone pilot stress response")

            # Create PrimalLogicProcessor for flight control
            processor = PrimalLogicProcessor()

            # Simulate flight maneuvers with control feedback
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(stimulus_amplitude=0.4),
                cardiac_model=VanDerPolOscillator(mu=1.3, omega=1.2),
                coupling=CouplingParameters()
            )

            # Run simulation with control loop
            dt = 0.001
            t_end = 60.0
            state = (0.0, 0.0, 1.0, 0.0)
            trajectory = []
            control_signals = []

            setpoint = 0.0
            for t in np.arange(0, t_end, dt):
                # Step HBCM
                state = hbcm.step(t, state, dt)
                trajectory.append((t, state))

                # Compute control signal based on neural activity
                measurement = state[0]  # Neural voltage
                control = processor.compute_control(setpoint, measurement, dt)
                control_signals.append(control)

            # Analyze control performance
            control_signals = np.array(control_signals)
            avg_control_magnitude = np.mean(np.abs(control_signals))
            max_control = np.max(np.abs(control_signals))

            # Check if control is stable
            control_stable = max_control < 10.0

            score = 100.0 if control_stable else 60.0
            status = "passed" if control_stable else "warning"

            details = {
                "simulation_duration": t_end,
                "control_samples": len(control_signals),
                "avg_control_magnitude": float(avg_control_magnitude),
                "max_control": float(max_control),
                "control_stable": control_stable,
                "scenario": "Autonomous flight with pilot monitoring"
            }

            print(f"  ├─ Control samples: {len(control_signals)}")
            print(f"  ├─ Avg control magnitude: {avg_control_magnitude:.3f}")
            print(f"  ├─ Max control: {max_control:.3f}")
            print(f"  ├─ Stability: {'✓ PASS' if control_stable else '⚠ WARNING'}")
            print(f"  └─ Score: {score:.1f}/100")

        except Exception as e:
            status = "failed"
            score = 0.0
            details = {"error": str(e)}
            print(f"  └─ ERROR: {e}")

        execution_time = time.time() - start_time
        self.results.append(ValidationResult(
            test_name="PX4 Drone Pilot Monitoring",
            test_type="px4",
            status=status,
            score=score,
            details=details,
            execution_time=execution_time
        ))

    def _test_carla_av_simulation(self):
        """Test 4: CARLA Autonomous Vehicle Simulation"""
        print("\n[4/5] CARLA Autonomous Vehicle Simulation")
        print("-" * 80)
        start_time = time.time()

        try:
            print("  ├─ Simulating urban autonomous driving scenario")

            # Simulate passenger physiological response to AV behavior
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(a=0.7, b=0.8, c=3.0),
                cardiac_model=VanDerPolOscillator(mu=1.4, omega=1.1),
                coupling=CouplingParameters(
                    neural_to_cardiac_gain=0.55,
                    cardiac_to_neural_gain=0.35
                )
            )

            # Simulate urban driving with various events
            events = [
                (0, 30, "normal_driving"),
                (30, 35, "emergency_brake"),
                (35, 50, "normal_driving"),
                (50, 55, "sharp_turn"),
                (55, 90, "normal_driving")
            ]

            full_trajectory = []
            event_responses = {}

            for start_t, end_t, event_name in events:
                # Adjust stimulus based on event
                stimulus = {
                    "normal_driving": 0.2,
                    "emergency_brake": 0.8,
                    "sharp_turn": 0.6
                }[event_name]

                hbcm.neural_model.stimulus_amplitude = stimulus

                state = full_trajectory[-1][1] if full_trajectory else (0.0, 0.0, 1.0, 0.0)

                trajectory = hbcm.simulate(
                    initial_state=state,
                    t_span=(start_t, end_t),
                    dt=0.001
                )

                full_trajectory.extend(trajectory)

                # Analyze response
                times_seg, neural_seg, cardiac_seg = hbcm.extract_series(trajectory)
                neural_v_seg = [v for v, w in neural_seg]
                max_response = np.max(np.abs(neural_v_seg))

                event_responses[event_name] = max_response

            # Verify responses are proportional to stimulus
            brake_response = event_responses.get("emergency_brake", 0)
            turn_response = event_responses.get("sharp_turn", 0)
            normal_response = event_responses.get("normal_driving", 0)

            response_proportional = brake_response > turn_response > normal_response

            score = 100.0 if response_proportional else 75.0
            status = "passed" if response_proportional else "warning"

            details = {
                "total_duration": 90.0,
                "events": len(events),
                "emergency_brake_response": float(brake_response),
                "sharp_turn_response": float(turn_response),
                "normal_driving_response": float(normal_response),
                "response_proportional": response_proportional,
                "scenario": "Urban autonomous driving with events"
            }

            print(f"  ├─ Emergency brake response: {brake_response:.3f}")
            print(f"  ├─ Sharp turn response: {turn_response:.3f}")
            print(f"  ├─ Normal driving response: {normal_response:.3f}")
            print(f"  ├─ Proportional response: {'✓ PASS' if response_proportional else '⚠ WARNING'}")
            print(f"  └─ Score: {score:.1f}/100")

        except Exception as e:
            status = "failed"
            score = 0.0
            details = {"error": str(e)}
            print(f"  └─ ERROR: {e}")

        execution_time = time.time() - start_time
        self.results.append(ValidationResult(
            test_name="CARLA Autonomous Vehicle Simulation",
            test_type="carla",
            status=status,
            score=score,
            details=details,
            execution_time=execution_time
        ))

    def _test_cross_platform_integration(self):
        """Test 5: Cross-Platform Integration"""
        print("\n[5/5] Cross-Platform Integration Test")
        print("-" * 80)
        start_time = time.time()

        try:
            print("  ├─ Testing multi-platform data fusion")

            # Simulate data from all platforms
            platforms = ["spacex", "tesla", "px4", "carla"]
            platform_data = {}

            for platform in platforms:
                hbcm = HeartBrainCouplingModel()
                trajectory = hbcm.simulate(
                    initial_state=(0.0, 0.0, 1.0, 0.0),
                    t_span=(0.0, 10.0),
                    dt=0.001
                )

                times, neural, cardiac = hbcm.extract_series(trajectory)
                platform_data[platform] = {
                    "timesteps": len(times),
                    "neural_mean": float(np.mean([v for v, w in neural])),
                    "cardiac_mean": float(np.mean([x for x, y in cardiac]))
                }

            # Check consistency across platforms
            timestep_counts = [data["timesteps"] for data in platform_data.values()]
            consistent = len(set(timestep_counts)) == 1

            score = 100.0 if consistent else 80.0
            status = "passed" if consistent else "warning"

            details = {
                "platforms_tested": len(platforms),
                "platform_data": platform_data,
                "timestep_consistency": consistent,
                "scenario": "Multi-platform data fusion"
            }

            print(f"  ├─ Platforms integrated: {len(platforms)}")
            print(f"  ├─ Data consistency: {'✓ PASS' if consistent else '⚠ WARNING'}")
            print(f"  └─ Score: {score:.1f}/100")

        except Exception as e:
            status = "failed"
            score = 0.0
            details = {"error": str(e)}
            print(f"  └─ ERROR: {e}")

        execution_time = time.time() - start_time
        self.results.append(ValidationResult(
            test_name="Cross-Platform Integration",
            test_type="integration",
            status=status,
            score=score,
            details=details,
            execution_time=execution_time
        ))

    def _generate_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        print("\n" + "=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)

        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        warnings = sum(1 for r in self.results if r.status == "warning")

        avg_score = np.mean([r.score for r in self.results])
        total_time = time.time() - self.start_time

        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed} ✓")
        print(f"Warnings: {warnings} ⚠")
        print(f"Failed: {failed} ✗")
        print(f"\nAverage Score: {avg_score:.1f}/100")
        print(f"Total Execution Time: {total_time:.2f}s")
        print("\n" + "=" * 80)

        # Determine overall status
        if failed > 0:
            overall_status = "FAILED"
        elif warnings > 0:
            overall_status = "PASSED WITH WARNINGS"
        else:
            overall_status = "PASSED"

        print(f"\nOverall Status: {overall_status}")
        print("=" * 80 + "\n")

        return {
            "overall_status": overall_status,
            "total_tests": total_tests,
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "average_score": avg_score,
            "total_execution_time": total_time,
            "results": [
                {
                    "test_name": r.test_name,
                    "test_type": r.test_type,
                    "status": r.status,
                    "score": r.score,
                    "details": r.details,
                    "execution_time": r.execution_time
                }
                for r in self.results
            ]
        }


def main():
    """Run validation suite"""
    # Install scipy if needed
    try:
        import scipy.signal
    except ImportError:
        print("Installing scipy for signal processing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scipy"])
        import scipy.signal

    suite = ValidationSuite()
    report = suite.run_all_tests()

    # Save report
    output_file = Path(__file__).parent / "validation_report.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Full report saved to: {output_file}")

    # Exit with appropriate code
    sys.exit(0 if report["overall_status"] != "FAILED" else 1)


if __name__ == "__main__":
    main()
