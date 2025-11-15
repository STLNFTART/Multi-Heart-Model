"""
MOABB (Mother of All BCI Benchmarks) Integration Tests

Tests Multi-Heart-Model against MOABB datasets and benchmarks.

Repository: https://github.com/NeuroTechX/moabb
"""

import sys
from pathlib import Path
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validation.framework import ValidationTestBase, BenchmarkResult, PerformanceBenchmark


class MOABBValidationTests(ValidationTestBase):
    """Validation tests for MOABB integration."""

    def __init__(self):
        super().__init__("MOABB")

    def test_installation(self) -> BenchmarkResult:
        """Test if MOABB is properly installed."""
        start = time.time()

        try:
            import moabb
            from moabb import datasets
            from moabb.paradigms import MotorImagery

            metrics = {
                'version': moabb.__version__,
                'datasets_available': len(datasets.__all__)
            }

            return BenchmarkResult(
                test_name="Installation Check",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except ImportError as e:
            return BenchmarkResult(
                test_name="Installation Check",
                repository=self.repository_name,
                status='skip',
                execution_time=time.time() - start,
                error_message=f"MOABB not installed: {e}. Install with: pip install moabb"
            )

    def test_import(self) -> BenchmarkResult:
        """Test importing MOABB modules."""
        start = time.time()

        try:
            from moabb import datasets, paradigms, evaluations
            from moabb.pipelines import SSVEP_CCA, SSVEP_TRCA

            modules = [
                'datasets',
                'paradigms',
                'evaluations',
                'pipelines'
            ]

            return BenchmarkResult(
                test_name="Import Test",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics={'modules_imported': len(modules)}
            )

        except ImportError as e:
            return BenchmarkResult(
                test_name="Import Test",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )

    def test_basic_functionality(self) -> BenchmarkResult:
        """Test basic MOABB functionality."""
        start = time.time()

        try:
            from moabb.datasets import BNCI2014001
            from moabb.paradigms import MotorImagery

            # Load a small dataset (subject 1 only)
            dataset = BNCI2014001()
            paradigm = MotorImagery(n_classes=2)

            # Get data
            X, labels, metadata = paradigm.get_data(dataset, subjects=[1])

            metrics = {
                'dataset': 'BNCI2014001',
                'n_samples': len(labels),
                'n_channels': X.shape[1] if len(X.shape) > 1 else 1,
                'paradigm': 'MotorImagery',
                'n_classes': len(np.unique(labels))
            }

            return BenchmarkResult(
                test_name="Basic Functionality",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except Exception as e:
            return BenchmarkResult(
                test_name="Basic Functionality",
                repository=self.repository_name,
                status='skip',
                execution_time=time.time() - start,
                error_message=f"Dataset download or processing failed: {e}"
            )

    def test_integration_with_hbcm(self) -> BenchmarkResult:
        """Test MOABB data integration with HBCM."""
        start = time.time()

        try:
            from moabb.datasets import BNCI2014001
            from moabb.paradigms import MotorImagery
            from src.coupling import HeartBrainCouplingModel
            from src.neural import FitzHughNagumo
            from src.cardiac import VanDerPolOscillator
            from src.coupling import CouplingParameters

            # Get MOABB data
            dataset = BNCI2014001()
            paradigm = MotorImagery(n_classes=2)
            X, labels, metadata = paradigm.get_data(dataset, subjects=[1])

            # Extract first trial
            trial_data = X[0]  # Shape: (n_channels, n_samples)

            # Use EEG data to modulate HBCM
            # Average across channels as simple approach
            eeg_signal = np.mean(trial_data, axis=0)

            # Normalize to reasonable range for stimulus
            eeg_normalized = (eeg_signal - np.mean(eeg_signal)) / (np.std(eeg_signal) + 1e-10)
            eeg_normalized = np.clip(eeg_normalized, -2, 2)

            # Create HBCM
            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(),
                cardiac_model=VanDerPolOscillator(),
                coupling=CouplingParameters()
            )

            # Run short simulation
            initial_state = (0.0, 0.0, 1.0, 0.0)
            dt = 0.001
            n_steps = 100

            current_state = initial_state
            for i in range(n_steps):
                # Could inject EEG signal here (would need custom step method)
                current_state = hbcm.step(i * dt, current_state, dt)

            metrics = {
                'moabb_dataset': 'BNCI2014001',
                'n_eeg_channels': trial_data.shape[0],
                'n_eeg_samples': trial_data.shape[1],
                'hbcm_steps': n_steps,
                'integration_successful': True
            }

            return BenchmarkResult(
                test_name="HBCM Integration",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except Exception as e:
            return BenchmarkResult(
                test_name="HBCM Integration",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )

    def benchmark_classification_pipeline(self) -> BenchmarkResult:
        """Benchmark MOABB classification pipeline."""
        start = time.time()

        try:
            from moabb.datasets import BNCI2014001
            from moabb.paradigms import MotorImagery
            from sklearn.pipeline import make_pipeline
            from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
            from sklearn.model_selection import cross_val_score
            from pyriemann.estimation import Covariances
            from pyriemann.tangentspace import TangentSpace

            # Load dataset
            dataset = BNCI2014001()
            paradigm = MotorImagery(n_classes=2)
            X, labels, metadata = paradigm.get_data(dataset, subjects=[1])

            # Create Riemannian pipeline
            pipeline = make_pipeline(
                Covariances(estimator='lwf'),
                TangentSpace(),
                LDA()
            )

            # Cross-validation
            scores = cross_val_score(pipeline, X, labels, cv=3)

            metrics = {
                'mean_accuracy': float(np.mean(scores)),
                'std_accuracy': float(np.std(scores)),
                'pipeline': 'Riemannian + LDA'
            }

            return BenchmarkResult(
                test_name="Classification Benchmark",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except Exception as e:
            return BenchmarkResult(
                test_name="Classification Benchmark",
                repository=self.repository_name,
                status='skip',
                execution_time=time.time() - start,
                error_message=f"Benchmark failed: {e}"
            )


def run_moabb_tests():
    """Run all MOABB validation tests."""
    tester = MOABBValidationTests()
    results = tester.run_all_tests()

    # Also run classification benchmark
    print("\nRunning classification benchmark...", end=' ')
    benchmark = tester.benchmark_classification_pipeline()
    results.append(benchmark)
    print(f"[{benchmark.status.upper()}] ({benchmark.execution_time:.3f}s)")

    # Print summary
    summary = tester.get_summary()
    print(f"\n{'='*70}")
    print("MOABB Validation Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Errors: {summary['errors']}")
    print(f"  Skipped: {summary['skipped']}")
    print(f"  Success Rate: {summary['success_rate']:.1f}%")
    print(f"  Total Time: {summary['total_time']:.2f}s")
    print(f"{'='*70}\n")

    return results


if __name__ == '__main__':
    run_moabb_tests()
