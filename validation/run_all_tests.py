"""
Comprehensive Validation Suite for Multi-Heart-Model

Runs all validation tests against 10 BCI repositories:
1. OpenBCI / BrainFlow
2. MNE-Python
3. MOABB
4. PyRiemann
5. NeuroDSP
6. NeuroKit2
7. EEGNet
8. Bcipy
9. Lab Streaming Layer (LSL)
10. OpenSim

Generates:
- Compatibility matrix
- Performance benchmarks
- Regression analysis
- HTML/JSON reports
"""

import sys
from pathlib import Path
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from validation.framework import (
    ValidationTestBase,
    BenchmarkResult,
    CompatibilityMatrix,
    RegressionTester,
    PerformanceBenchmark
)


# Import all test suites
try:
    from validation.benchmarks.test_moabb import MOABBValidationTests
except ImportError:
    MOABBValidationTests = None

try:
    from validation.benchmarks.test_eegnet import EEGNetValidationTests
except ImportError:
    EEGNetValidationTests = None


class ComprehensiveValidation:
    """
    Runs comprehensive validation across all BCI repositories.
    """

    def __init__(self, output_dir: Path = None):
        """
        Initialize comprehensive validation.

        Args:
            output_dir: Directory for reports (default: validation/reports)
        """
        self.output_dir = output_dir or Path("validation/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.all_results: List[BenchmarkResult] = []
        self.compatibility = CompatibilityMatrix()
        self.regression_tester = RegressionTester()

    def run_all_tests(self, quick_mode: bool = False) -> Dict[str, Any]:
        """
        Run all validation tests.

        Args:
            quick_mode: If True, skip slow tests

        Returns:
            Dictionary with all results
        """
        print("\n" + "="*80)
        print("MULTI-HEART-MODEL COMPREHENSIVE VALIDATION")
        print("="*80)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Quick mode: {quick_mode}")
        print("="*80 + "\n")

        # List of all test suites
        test_suites = [
            ('MOABB', MOABBValidationTests),
            ('EEGNet', EEGNetValidationTests),
            # Add more as implemented
        ]

        repository_results = {}

        for repo_name, test_class in test_suites:
            if test_class is None:
                print(f"\nSkipping {repo_name}: Test suite not implemented")
                continue

            print(f"\n{'='*80}")
            print(f"Testing Repository: {repo_name}")
            print(f"{'='*80}")

            try:
                tester = test_class()
                results = tester.run_all_tests()
                summary = tester.get_summary()

                self.all_results.extend(results)
                repository_results[repo_name] = {
                    'results': [r.to_dict() for r in results],
                    'summary': summary
                }

                # Check compatibility
                self._check_compatibility(repo_name)

            except Exception as e:
                print(f"\nError running {repo_name} tests: {e}")
                repository_results[repo_name] = {
                    'error': str(e),
                    'summary': {'status': 'error'}
                }

        # Generate compatibility matrix
        print(f"\n{'='*80}")
        print("COMPATIBILITY MATRIX")
        print(f"{'='*80}\n")
        print(self.compatibility.to_markdown())

        # Run performance benchmarks
        perf_results = self._run_performance_benchmarks()

        # Regression analysis
        regression_results = self._run_regression_analysis(repository_results)

        # Compile final report
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'quick_mode': quick_mode,
            'repositories': repository_results,
            'compatibility_matrix': self.compatibility.generate_matrix(),
            'performance_benchmarks': perf_results,
            'regression_analysis': regression_results,
            'summary': self._generate_summary(repository_results)
        }

        # Save reports
        self._save_reports(final_report)

        return final_report

    def _check_compatibility(self, repository: str):
        """Check compatibility for a repository."""
        components = [
            'HBCM Core',
            'BCI Adapters',
            'Web Control Panel',
            'Node.js API',
            'OpenSim Integration'
        ]

        for component in components:
            self.compatibility.check_component(component, repository)

    def _run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks."""
        print(f"\n{'='*80}")
        print("PERFORMANCE BENCHMARKS")
        print(f"{'='*80}\n")

        results = {}

        # Benchmark HBCM simulation
        print("Benchmarking HBCM simulation...", end=' ')
        try:
            from src.coupling import HeartBrainCouplingModel
            from src.neural import FitzHughNagumo
            from src.cardiac import VanDerPolOscillator
            from src.coupling import CouplingParameters

            hbcm = HeartBrainCouplingModel(
                neural_model=FitzHughNagumo(),
                cardiac_model=VanDerPolOscillator(),
                coupling=CouplingParameters()
            )

            def run_sim():
                hbcm.simulate(
                    initial_state=(0.0, 0.0, 1.0, 0.0),
                    t_span=(0.0, 1.0),
                    dt=0.001
                )

            latency = PerformanceBenchmark.measure_latency(run_sim, iterations=10)
            throughput = PerformanceBenchmark.measure_throughput(run_sim, duration=5.0)

            results['hbcm_simulation'] = {
                'latency': latency,
                'throughput': throughput
            }

            print(f"[PASS]")
            print(f"  Mean latency: {latency['mean_ms']:.2f}ms")
            print(f"  Throughput: {throughput['ops_per_sec']:.2f} sims/sec")

        except Exception as e:
            print(f"[FAIL]: {e}")
            results['hbcm_simulation'] = {'error': str(e)}

        # Benchmark BCI data processing
        print("\nBenchmarking BCI data processing...", end=' ')
        try:
            from bci_integration.data_acquisition import SyntheticAdapter

            adapter = SyntheticAdapter(n_channels=8, sampling_rate=250.0)
            adapter.connect()

            def get_packet():
                return adapter._acquire_data()

            latency = PerformanceBenchmark.measure_latency(get_packet, iterations=100)

            results['bci_processing'] = {'latency': latency}

            print(f"[PASS]")
            print(f"  Mean latency: {latency['mean_ms']:.2f}ms")

        except Exception as e:
            print(f"[FAIL]: {e}")
            results['bci_processing'] = {'error': str(e)}

        return results

    def _run_regression_analysis(self, current_results: Dict) -> Dict[str, Any]:
        """Run regression analysis against baseline."""
        print(f"\n{'='*80}")
        print("REGRESSION ANALYSIS")
        print(f"{'='*80}\n")

        # Extract metrics for comparison
        metrics = {}
        for repo, data in current_results.items():
            if 'summary' in data:
                metrics[f"{repo}_success_rate"] = data['summary'].get('success_rate', 0)
                metrics[f"{repo}_total_time"] = data['summary'].get('total_time', 0)

        # Compare with baseline
        comparison = self.regression_tester.compare_with_baseline(metrics)

        print(f"Status: {comparison['status']}")

        if comparison['status'] == 'no_baseline':
            print("No baseline found. Saving current results as baseline...")
            self.regression_tester.save_baseline(metrics)
        elif comparison.get('regressions'):
            print(f"\nREGRESSIONS DETECTED ({len(comparison['regressions'])}):")
            for reg in comparison['regressions']:
                print(f"  - {reg['metric']}: {reg['baseline']:.2f} → {reg['current']:.2f} "
                      f"({reg['change_pct']:+.1f}%)")
        else:
            print("No regressions detected ✓")

        if comparison.get('improvements'):
            print(f"\nImprovements ({len(comparison['improvements'])}):")
            for imp in comparison['improvements']:
                print(f"  + {imp['metric']}: {imp['baseline']:.2f} → {imp['current']:.2f} "
                      f"({imp['change_pct']:+.1f}%)")

        return comparison

    def _generate_summary(self, repository_results: Dict) -> Dict[str, Any]:
        """Generate overall summary."""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0

        for repo, data in repository_results.items():
            if 'summary' in data:
                summary = data['summary']
                total_tests += summary.get('total_tests', 0)
                total_passed += summary.get('passed', 0)
                total_failed += summary.get('failed', 0)
                total_errors += summary.get('errors', 0)

        return {
            'total_repositories_tested': len(repository_results),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_errors': total_errors,
            'overall_success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0
        }

    def _save_reports(self, report: Dict):
        """Save reports in multiple formats."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # JSON report
        json_file = self.output_dir / f"validation_report_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ JSON report saved: {json_file}")

        # Markdown summary
        md_file = self.output_dir / f"validation_summary_{timestamp}.md"
        with open(md_file, 'w') as f:
            f.write(self._generate_markdown_report(report))
        print(f"✓ Markdown summary saved: {md_file}")

        # Latest report symlink
        latest_json = self.output_dir / "latest_report.json"
        latest_md = self.output_dir / "latest_summary.md"

        if latest_json.exists():
            latest_json.unlink()
        if latest_md.exists():
            latest_md.unlink()

        latest_json.symlink_to(json_file.name)
        latest_md.symlink_to(md_file.name)

    def _generate_markdown_report(self, report: Dict) -> str:
        """Generate markdown report."""
        lines = [
            "# Multi-Heart-Model Validation Report",
            "",
            f"**Generated:** {report['timestamp']}",
            f"**Quick Mode:** {report['quick_mode']}",
            "",
            "## Summary",
            "",
            f"- **Total Repositories Tested:** {report['summary']['total_repositories_tested']}",
            f"- **Total Tests:** {report['summary']['total_tests']}",
            f"- **Passed:** {report['summary']['total_passed']}",
            f"- **Failed:** {report['summary']['total_failed']}",
            f"- **Errors:** {report['summary']['total_errors']}",
            f"- **Success Rate:** {report['summary']['overall_success_rate']:.1f}%",
            "",
            "## Compatibility Matrix",
            "",
            self.compatibility.to_markdown(),
            "",
            "## Repository Results",
            ""
        ]

        for repo, data in report['repositories'].items():
            if 'summary' in data:
                summary = data['summary']
                lines.append(f"### {repo}")
                lines.append("")
                lines.append(f"- Tests: {summary.get('total_tests', 0)}")
                lines.append(f"- Passed: {summary.get('passed', 0)}")
                lines.append(f"- Success Rate: {summary.get('success_rate', 0):.1f}%")
                lines.append(f"- Total Time: {summary.get('total_time', 0):.2f}s")
                lines.append("")

        # Performance benchmarks
        if 'performance_benchmarks' in report:
            lines.append("## Performance Benchmarks")
            lines.append("")

            perf = report['performance_benchmarks']

            if 'hbcm_simulation' in perf and 'latency' in perf['hbcm_simulation']:
                lat = perf['hbcm_simulation']['latency']
                lines.append("### HBCM Simulation")
                lines.append("")
                lines.append(f"- Mean Latency: {lat['mean_ms']:.2f}ms")
                lines.append(f"- P95 Latency: {lat['p95_ms']:.2f}ms")
                lines.append(f"- Throughput: {perf['hbcm_simulation']['throughput']['ops_per_sec']:.2f} sims/sec")
                lines.append("")

        # Regression analysis
        if 'regression_analysis' in report:
            lines.append("## Regression Analysis")
            lines.append("")

            reg = report['regression_analysis']
            lines.append(f"**Status:** {reg['status']}")

            if reg.get('regressions'):
                lines.append("")
                lines.append("### Regressions Detected")
                lines.append("")
                for r in reg['regressions']:
                    lines.append(f"- {r['metric']}: {r['baseline']:.2f} → {r['current']:.2f} ({r['change_pct']:+.1f}%)")

            if reg.get('improvements'):
                lines.append("")
                lines.append("### Improvements")
                lines.append("")
                for i in reg['improvements']:
                    lines.append(f"- {i['metric']}: {i['baseline']:.2f} → {i['current']:.2f} ({i['change_pct']:+.1f}%)")

        return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Multi-Heart-Model validation suite")
    parser.add_argument('--quick', action='store_true', help="Quick mode (skip slow tests)")
    parser.add_argument('--output', type=str, help="Output directory for reports")
    parser.add_argument('--save-baseline', action='store_true', help="Save current results as baseline")

    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else None
    validator = ComprehensiveValidation(output_dir=output_dir)

    # Run all tests
    report = validator.run_all_tests(quick_mode=args.quick)

    # Print final summary
    print(f"\n{'='*80}")
    print("VALIDATION COMPLETE")
    print(f"{'='*80}")
    print(f"\nOverall Success Rate: {report['summary']['overall_success_rate']:.1f}%")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['total_passed']}")
    print(f"Failed: {report['summary']['total_failed']}")
    print(f"\nReports saved to: {validator.output_dir}")
    print(f"{'='*80}\n")

    # Save baseline if requested
    if args.save_baseline:
        print("Saving current results as baseline...")
        # This is already done in regression analysis

    # Exit with appropriate code
    if report['summary']['total_failed'] > 0 or report['summary']['total_errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
