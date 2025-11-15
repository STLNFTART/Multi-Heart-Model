"""
PyRiemann Integration Tests

Tests Multi-Heart-Model integration with PyRiemann for Riemannian geometry-based
BCI feature extraction and classification.

Repository: https://github.com/pyRiemann/pyRiemann
"""

import sys
from pathlib import Path
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validation.framework import ValidationTestBase, BenchmarkResult, PerformanceBenchmark


class PyRiemannValidationTests(ValidationTestBase):
    """Validation tests for PyRiemann integration."""

    def __init__(self):
        super().__init__("PyRiemann")

    def test_installation(self) -> BenchmarkResult:
        """Test if PyRiemann is properly installed."""
        start = time.time()

        try:
            import pyriemann

            metrics = {
                'version': pyriemann.__version__
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
                error_message=f"PyRiemann not installed: {e}. Install with: pip install pyriemann"
            )

    def test_import(self) -> BenchmarkResult:
        """Test importing PyRiemann modules."""
        start = time.time()

        try:
            from pyriemann.estimation import Covariances
            from pyriemann.tangentspace import TangentSpace
            from pyriemann.classification import MDM, TSclassifier
            from pyriemann.utils.mean import mean_riemann
            from pyriemann.utils.distance import distance_riemann

            modules = [
                'estimation', 'tangentspace', 'classification',
                'utils.mean', 'utils.distance'
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
        """Test basic PyRiemann functionality."""
        start = time.time()

        try:
            from pyriemann.estimation import Covariances
            from pyriemann.tangentspace import TangentSpace
            from pyriemann.utils.mean import mean_riemann
            from sklearn.pipeline import make_pipeline
            from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

            # Create synthetic EEG data
            n_trials = 100
            n_channels = 8
            n_samples = 256

            X = np.random.randn(n_trials, n_channels, n_samples)
            y = np.random.randint(0, 2, n_trials)

            # Estimate covariance matrices
            cov_estimator = Covariances(estimator='lwf')
            covs = cov_estimator.transform(X)

            # Compute Riemannian mean
            mean_cov = mean_riemann(covs)

            # Create tangent space projection
            ts = TangentSpace()
            X_ts = ts.fit_transform(covs, y)

            # Build pipeline
            pipeline = make_pipeline(
                Covariances(estimator='lwf'),
                TangentSpace(),
                LinearDiscriminantAnalysis()
            )

            # Fit pipeline
            pipeline.fit(X, y)

            metrics = {
                'n_trials': n_trials,
                'n_channels': n_channels,
                'covariance_matrices_shape': covs.shape,
                'tangent_space_shape': X_ts.shape,
                'pipeline_fitted': True
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
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )

    def test_integration_with_hbcm(self) -> BenchmarkResult:
        """Test PyRiemann feature extraction integrated with HBCM."""
        start = time.time()

        try:
            from pyriemann.estimation import Covariances
            from pyriemann.tangentspace import TangentSpace
            from pyriemann.utils.distance import distance_riemann
            from src.coupling import HeartBrainCouplingModel
            from src.neural import FitzHughNagumo
            from src.cardiac import VanDerPolOscillator
            from src.coupling import CouplingParameters

            # Generate synthetic EEG trials
            n_trials = 20
            n_channels = 8
            n_samples = 256

            X = np.random.randn(n_trials, n_channels, n_samples)

            # Estimate covariance matrices
            cov_estimator = Covariances(estimator='lwf')
            covs = cov_estimator.transform(X)

            # Compute distance to mean (as a feature)
            from pyriemann.utils.mean import mean_riemann
            mean_cov = mean_riemann(covs)

            distances = np.array([distance_riemann(cov, mean_cov) for cov in covs])

            # Use distance as modulation parameter for HBCM
            # Normalize to [0, 1] range
            normalized_distance = (distances - distances.min()) / (distances.max() - distances.min() + 1e-10)

            # Run HBCM with different modulation strengths
            hbcm_results = []

            for dist in normalized_distance[:5]:  # Test with first 5 trials
                hbcm = HeartBrainCouplingModel(
                    neural_model=FitzHughNagumo(stimulus_amplitude=0.5 + dist * 0.5),
                    cardiac_model=VanDerPolOscillator(),
                    coupling=CouplingParameters()
                )

                trajectory = hbcm.simulate(
                    initial_state=(0.0, 0.0, 1.0, 0.0),
                    t_span=(0.0, 1.0),
                    dt=0.01
                )

                hbcm_results.append(len(trajectory))

            metrics = {
                'n_covariance_matrices': len(covs),
                'riemannian_distances_mean': float(np.mean(distances)),
                'riemannian_distances_std': float(np.std(distances)),
                'hbcm_simulations_run': len(hbcm_results),
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

    def benchmark_covariance_estimation(self) -> BenchmarkResult:
        """Benchmark covariance matrix estimation performance."""
        start = time.time()

        try:
            from pyriemann.estimation import Covariances

            # Create test data
            n_trials = 100
            n_channels = 16
            n_samples = 512

            X = np.random.randn(n_trials, n_channels, n_samples)

            # Benchmark different estimators
            estimators = ['scm', 'lwf', 'oas', 'corr']
            results = {}

            for est in estimators:
                cov_est = Covariances(estimator=est)

                # Measure latency
                latency = PerformanceBenchmark.measure_latency(
                    cov_est.transform,
                    X,
                    iterations=10
                )

                results[est] = latency['mean_ms']

            metrics = {
                'estimators_tested': len(estimators),
                'latency_scm_ms': results.get('scm', 0),
                'latency_lwf_ms': results.get('lwf', 0),
                'latency_oas_ms': results.get('oas', 0),
                'latency_corr_ms': results.get('corr', 0),
                'fastest_estimator': min(results, key=results.get)
            }

            return BenchmarkResult(
                test_name="Covariance Estimation Benchmark",
                repository=self.repository_name,
                status='pass',
                execution_time=time.time() - start,
                metrics=metrics
            )

        except Exception as e:
            return BenchmarkResult(
                test_name="Covariance Estimation Benchmark",
                repository=self.repository_name,
                status='fail',
                execution_time=time.time() - start,
                error_message=str(e)
            )


def run_pyriemann_tests():
    """Run all PyRiemann validation tests."""
    tester = PyRiemannValidationTests()
    results = tester.run_all_tests()

    # Run benchmark
    print("\nRunning covariance estimation benchmark...", end=' ')
    benchmark = tester.benchmark_covariance_estimation()
    results.append(benchmark)
    print(f"[{benchmark.status.upper()}] ({benchmark.execution_time:.3f}s)")

    if benchmark.status == 'pass':
        print(f"  Fastest estimator: {benchmark.metrics.get('fastest_estimator', 'N/A')}")

    # Print summary
    summary = tester.get_summary()
    print(f"\n{'='*70}")
    print("PyRiemann Validation Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Success Rate: {summary['success_rate']:.1f}%")
    print(f"{'='*70}\n")

    return results


if __name__ == '__main__':
    run_pyriemann_tests()
