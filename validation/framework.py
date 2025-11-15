"""
Validation Framework for Multi-Heart-Model

Comprehensive testing suite to validate against industry-standard BCI repositories:
1. OpenBCI
2. BrainFlow
3. MNE-Python
4. MOABB
5. PyRiemann
6. NeuroDSP
7. NeuroKit2
8. EEGNet
9. Bcipy
10. Lab Streaming Layer (LSL)

Provides:
- Automated compatibility testing
- Performance benchmarking (latency, accuracy)
- Regression testing
- Continuous validation
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import time
import json
import numpy as np
from datetime import datetime
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Results from a single benchmark test."""
    test_name: str
    repository: str
    status: str  # 'pass', 'fail', 'skip', 'error'
    execution_time: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'test_name': self.test_name,
            'repository': self.repository,
            'status': self.status,
            'execution_time': self.execution_time,
            'metrics': self.metrics,
            'error_message': self.error_message,
            'timestamp': self.timestamp
        }


@dataclass
class CompatibilityCheck:
    """Compatibility check result."""
    component: str
    repository: str
    version: str
    compatible: bool
    issues: List[str] = field(default_factory=list)
    notes: str = ""


class ValidationTestBase(ABC):
    """
    Base class for all validation tests.

    Each BCI repository integration should inherit from this class.
    """

    def __init__(self, repository_name: str):
        """
        Initialize validation test.

        Args:
            repository_name: Name of the BCI repository being tested
        """
        self.repository_name = repository_name
        self.results: List[BenchmarkResult] = []

    @abstractmethod
    def test_installation(self) -> BenchmarkResult:
        """Test if the repository is properly installed."""
        pass

    @abstractmethod
    def test_import(self) -> BenchmarkResult:
        """Test if main modules can be imported."""
        pass

    @abstractmethod
    def test_basic_functionality(self) -> BenchmarkResult:
        """Test basic functionality of the repository."""
        pass

    @abstractmethod
    def test_integration_with_hbcm(self) -> BenchmarkResult:
        """Test integration with Multi-Heart-Model HBCM."""
        pass

    def run_all_tests(self) -> List[BenchmarkResult]:
        """Run all tests for this repository."""
        print(f"\n{'='*70}")
        print(f"Running validation tests for: {self.repository_name}")
        print(f"{'='*70}\n")

        tests = [
            ('Installation Check', self.test_installation),
            ('Import Test', self.test_import),
            ('Basic Functionality', self.test_basic_functionality),
            ('HBCM Integration', self.test_integration_with_hbcm)
        ]

        for test_name, test_func in tests:
            print(f"Running: {test_name}...", end=' ')
            try:
                result = test_func()
                self.results.append(result)
                print(f"[{result.status.upper()}] ({result.execution_time:.3f}s)")
                if result.error_message:
                    print(f"  Error: {result.error_message}")
            except Exception as e:
                print(f"[ERROR]")
                print(f"  Exception: {e}")
                self.results.append(BenchmarkResult(
                    test_name=test_name,
                    repository=self.repository_name,
                    status='error',
                    execution_time=0.0,
                    error_message=str(e)
                ))

        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of test results."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == 'pass')
        failed = sum(1 for r in self.results if r.status == 'fail')
        errors = sum(1 for r in self.results if r.status == 'error')
        skipped = sum(1 for r in self.results if r.status == 'skip')

        return {
            'repository': self.repository_name,
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'skipped': skipped,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'total_time': sum(r.execution_time for r in self.results)
        }


class PerformanceBenchmark:
    """
    Performance benchmarking utilities.

    Measures latency, throughput, accuracy, and resource usage.
    """

    @staticmethod
    def measure_latency(func, *args, iterations: int = 100, **kwargs) -> Dict[str, float]:
        """
        Measure function execution latency.

        Args:
            func: Function to benchmark
            iterations: Number of iterations
            *args, **kwargs: Function arguments

        Returns:
            Dictionary with latency statistics
        """
        latencies = []

        # Warmup
        for _ in range(min(10, iterations // 10)):
            func(*args, **kwargs)

        # Measure
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        return {
            'mean_ms': np.mean(latencies),
            'std_ms': np.std(latencies),
            'min_ms': np.min(latencies),
            'max_ms': np.max(latencies),
            'p50_ms': np.percentile(latencies, 50),
            'p95_ms': np.percentile(latencies, 95),
            'p99_ms': np.percentile(latencies, 99)
        }

    @staticmethod
    def measure_throughput(func, duration: float = 1.0, *args, **kwargs) -> Dict[str, float]:
        """
        Measure function throughput (operations per second).

        Args:
            func: Function to benchmark
            duration: Duration to run in seconds
            *args, **kwargs: Function arguments

        Returns:
            Throughput metrics
        """
        start = time.perf_counter()
        count = 0

        while (time.perf_counter() - start) < duration:
            func(*args, **kwargs)
            count += 1

        elapsed = time.perf_counter() - start

        return {
            'operations': count,
            'duration_s': elapsed,
            'ops_per_sec': count / elapsed
        }

    @staticmethod
    def measure_accuracy(predictions: np.ndarray, ground_truth: np.ndarray) -> Dict[str, float]:
        """
        Measure classification/prediction accuracy.

        Args:
            predictions: Predicted values
            ground_truth: True values

        Returns:
            Accuracy metrics
        """
        predictions = np.array(predictions)
        ground_truth = np.array(ground_truth)

        # Classification metrics
        if predictions.dtype in [np.int32, np.int64]:
            accuracy = np.mean(predictions == ground_truth)
            return {
                'accuracy': accuracy,
                'error_rate': 1 - accuracy
            }

        # Regression metrics
        else:
            mse = np.mean((predictions - ground_truth) ** 2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(predictions - ground_truth))

            # R² score
            ss_res = np.sum((ground_truth - predictions) ** 2)
            ss_tot = np.sum((ground_truth - np.mean(ground_truth)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            return {
                'mse': mse,
                'rmse': rmse,
                'mae': mae,
                'r2_score': r2
            }


class CompatibilityMatrix:
    """
    Generates compatibility matrix showing which components work together.
    """

    def __init__(self):
        """Initialize compatibility matrix."""
        self.checks: List[CompatibilityCheck] = []

    def add_check(self, check: CompatibilityCheck):
        """Add a compatibility check result."""
        self.checks.append(check)

    def check_component(self, component: str, repository: str) -> CompatibilityCheck:
        """
        Check if a component is compatible with a repository.

        Args:
            component: Component name (e.g., 'HBCM', 'BCI Adapter')
            repository: Repository name

        Returns:
            CompatibilityCheck result
        """
        try:
            # Try to import and check version
            if repository == 'OpenBCI':
                try:
                    import brainflow
                    version = brainflow.__version__
                    compatible = True
                    issues = []
                except ImportError:
                    version = 'Not installed'
                    compatible = False
                    issues = ['Package not installed']

            elif repository == 'MNE-Python':
                try:
                    import mne
                    version = mne.__version__
                    compatible = True
                    issues = []
                except ImportError:
                    version = 'Not installed'
                    compatible = False
                    issues = ['Package not installed']

            # Add more repositories...
            else:
                version = 'Unknown'
                compatible = False
                issues = ['Repository not implemented']

            check = CompatibilityCheck(
                component=component,
                repository=repository,
                version=version,
                compatible=compatible,
                issues=issues
            )

            self.add_check(check)
            return check

        except Exception as e:
            return CompatibilityCheck(
                component=component,
                repository=repository,
                version='Error',
                compatible=False,
                issues=[str(e)]
            )

    def generate_matrix(self) -> Dict[str, Dict[str, bool]]:
        """
        Generate compatibility matrix.

        Returns:
            Nested dict: {component: {repository: compatible}}
        """
        matrix = {}

        for check in self.checks:
            if check.component not in matrix:
                matrix[check.component] = {}
            matrix[check.component][check.repository] = check.compatible

        return matrix

    def to_markdown(self) -> str:
        """Generate markdown table of compatibility matrix."""
        matrix = self.generate_matrix()

        if not matrix:
            return "No compatibility checks performed."

        # Get all repositories
        repos = set()
        for comp_checks in matrix.values():
            repos.update(comp_checks.keys())
        repos = sorted(repos)

        # Build table
        lines = []
        lines.append("| Component | " + " | ".join(repos) + " |")
        lines.append("|" + "---|" * (len(repos) + 1))

        for component, checks in sorted(matrix.items()):
            row = f"| {component} |"
            for repo in repos:
                compatible = checks.get(repo, False)
                symbol = "✅" if compatible else "❌"
                row += f" {symbol} |"
            lines.append(row)

        return "\n".join(lines)


class RegressionTester:
    """
    Regression testing framework to ensure changes don't break existing functionality.
    """

    def __init__(self, baseline_file: Optional[Path] = None):
        """
        Initialize regression tester.

        Args:
            baseline_file: Path to baseline results JSON file
        """
        self.baseline_file = baseline_file or Path("validation/reports/baseline_results.json")
        self.baseline: Dict[str, Any] = {}
        self.current_results: Dict[str, Any] = {}

        if self.baseline_file.exists():
            with open(self.baseline_file, 'r') as f:
                self.baseline = json.load(f)

    def save_baseline(self, results: Dict[str, Any]):
        """Save current results as new baseline."""
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Baseline saved to: {self.baseline_file}")

    def compare_with_baseline(self, current: Dict[str, Any],
                             tolerance: float = 0.05) -> Dict[str, Any]:
        """
        Compare current results with baseline.

        Args:
            current: Current test results
            tolerance: Acceptable variation (5% by default)

        Returns:
            Comparison report
        """
        if not self.baseline:
            return {
                'status': 'no_baseline',
                'message': 'No baseline to compare against'
            }

        regressions = []
        improvements = []
        stable = []

        # Compare metrics
        for key in current.keys():
            if key not in self.baseline:
                continue

            baseline_val = self.baseline[key]
            current_val = current[key]

            if isinstance(baseline_val, (int, float)) and isinstance(current_val, (int, float)):
                change = (current_val - baseline_val) / baseline_val if baseline_val != 0 else 0

                if abs(change) <= tolerance:
                    stable.append(key)
                elif change < 0:  # Worse performance
                    regressions.append({
                        'metric': key,
                        'baseline': baseline_val,
                        'current': current_val,
                        'change_pct': change * 100
                    })
                else:  # Better performance
                    improvements.append({
                        'metric': key,
                        'baseline': baseline_val,
                        'current': current_val,
                        'change_pct': change * 100
                    })

        has_regression = len(regressions) > 0

        return {
            'status': 'regression_detected' if has_regression else 'pass',
            'regressions': regressions,
            'improvements': improvements,
            'stable': stable,
            'total_metrics': len(current)
        }
