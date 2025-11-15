"""
Run all performance benchmarks and generate comprehensive report.

Usage:
    python -m benchmarks.run_all
    python -m benchmarks.run_all --quick  # Run quick benchmarks only
    python -m benchmarks.run_all --save-report report.json
"""

import sys
import argparse
import json
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, '/home/user/Multi-Heart-Model')

from benchmarks.hbcm_benchmark import HBCMBenchmark
from benchmarks.control_loop_benchmark import ControlLoopBenchmark


def generate_html_report(results: Dict[str, Any], output_file: str) -> None:
    """
    Generate HTML report from benchmark results.

    Args:
        results: Benchmark results dictionary
        output_file: Output HTML file path
    """
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Heart-Model Performance Benchmarks</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }}
        .metric-card {{
            background-color: #ecf0f1;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        .metric-name {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .metric-value {{
            font-size: 24px;
            color: #27ae60;
            margin: 5px 0;
        }}
        .metric-value.warning {{
            color: #f39c12;
        }}
        .metric-value.error {{
            color: #e74c3c;
        }}
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .stats-table th {{
            background-color: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .stats-table td {{
            padding: 10px;
            border-bottom: 1px solid #ecf0f1;
        }}
        .stats-table tr:hover {{
            background-color: #f8f9fa;
        }}
        .pass {{
            color: #27ae60;
            font-weight: bold;
        }}
        .fail {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .metadata {{
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 3px;
            font-size: 0.9em;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Multi-Heart-Model Performance Benchmarks</h1>
        <p><strong>Generated:</strong> {results['timestamp']}</p>
        <p><strong>System:</strong> {results.get('system_info', {}).get('platform', 'Unknown')}</p>

        <h2>Executive Summary</h2>
        <div class="metric-card">
            <div class="metric-name">Total Benchmarks Run</div>
            <div class="metric-value">{results['summary']['total_tests']}</div>
        </div>

        <div class="metric-card">
            <div class="metric-name">Targets Met</div>
            <div class="metric-value {'pass' if results['summary'].get('all_passed', False) else 'fail'}">
                {results['summary'].get('passed', 0)} / {results['summary']['total_tests']}
            </div>
        </div>
"""

    # Add HBCM results
    if 'hbcm' in results:
        html += """
        <h2>HBCM Simulation Performance</h2>
        <table class="stats-table">
            <tr>
                <th>Test</th>
                <th>Mean (ms)</th>
                <th>Median (ms)</th>
                <th>P95 (ms)</th>
                <th>P99 (ms)</th>
                <th>Throughput</th>
                <th>Status</th>
            </tr>
"""
        for test in results['hbcm']:
            html += f"""
            <tr>
                <td>{test['test_name']}</td>
                <td>{test['mean_latency_ms']:.3f}</td>
                <td>{test['median_latency_ms']:.3f}</td>
                <td>{test['p95_latency_ms']:.3f}</td>
                <td>{test['p99_latency_ms']:.3f}</td>
                <td>{test['throughput_ops_per_sec']:.0f} ops/s</td>
                <td class="{'pass' if test.get('p99_latency_ms', 999) < 10 else 'fail'}">
                    {'✅ PASS' if test.get('p99_latency_ms', 999) < 10 else '⚠️ SLOW'}
                </td>
            </tr>
"""
        html += "</table>"

    # Add control loop results
    if 'control_loop' in results:
        html += """
        <h2>Control Loop Latency (<100ms Target)</h2>
        <table class="stats-table">
            <tr>
                <th>Test</th>
                <th>Mean (ms)</th>
                <th>P99 (ms)</th>
                <th>P99.9 (ms)</th>
                <th>Target Met</th>
                <th>Margin (ms)</th>
            </tr>
"""
        for test in results['control_loop']:
            html += f"""
            <tr>
                <td>{test['test_name']}</td>
                <td>{test['mean_latency_ms']:.3f}</td>
                <td>{test['p99_latency_ms']:.3f}</td>
                <td>{test['p999_latency_ms']:.3f}</td>
                <td class="{'pass' if test.get('target_met', False) else 'fail'}">
                    {'✅ YES' if test.get('target_met', False) else '❌ NO'}
                </td>
                <td>{test.get('margin_ms', 0):.3f}</td>
            </tr>
"""
        html += "</table>"

    html += """
        <h2>Recommendations</h2>
        <div class="metadata">
"""

    # Add recommendations based on results
    recommendations = []

    if 'control_loop' in results:
        passed = sum(1 for t in results['control_loop'] if t.get('target_met', False))
        total = len(results['control_loop'])

        if passed == total:
            recommendations.append("✅ All control loop targets met - System ready for prosthetic control deployment")
        elif passed >= total * 0.8:
            recommendations.append("⚠️ Most control loop targets met - Review and optimize failed tests before deployment")
        else:
            recommendations.append("❌ Control loop optimization required - Consider algorithm improvements or hardware upgrade")

    if 'hbcm' in results:
        max_p99 = max(t.get('p99_latency_ms', 0) for t in results['hbcm'])

        if max_p99 < 1.0:
            recommendations.append("✅ Excellent HBCM performance - Suitable for 1000 Hz control loops")
        elif max_p99 < 10.0:
            recommendations.append("✅ Good HBCM performance - Suitable for 100 Hz control loops")
        else:
            recommendations.append("⚠️ HBCM optimization recommended for real-time applications")

    for rec in recommendations:
        html += f"<p>{rec}</p>"

    html += """
        </div>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)


def main():
    """Run all benchmarks."""
    parser = argparse.ArgumentParser(description='Run Multi-Heart-Model performance benchmarks')
    parser.add_argument('--quick', action='store_true', help='Run quick benchmarks only')
    parser.add_argument('--save-report', type=str, help='Save HTML report to file')
    parser.add_argument('--save-json', type=str, help='Save JSON results to file')
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("MULTI-HEART-MODEL COMPREHENSIVE PERFORMANCE BENCHMARK SUITE")
    print("=" * 80)

    # Collect system info
    import platform
    system_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'processor': platform.processor(),
    }

    all_results = {
        'timestamp': datetime.now().isoformat(),
        'system_info': system_info,
        'quick_mode': args.quick,
        'hbcm': [],
        'control_loop': [],
        'summary': {}
    }

    # Run HBCM benchmarks
    print("\n[1/2] Running HBCM Performance Benchmarks...")
    hbcm_benchmark = HBCMBenchmark()

    if args.quick:
        hbcm_benchmark.benchmark_single_step(iterations=1000)
        hbcm_benchmark.benchmark_short_simulation(steps=100)
    else:
        hbcm_benchmark.run_all()

    all_results['hbcm'] = [r.to_dict() for r in hbcm_benchmark.results]

    # Run control loop benchmarks
    print("\n[2/2] Running Control Loop Latency Benchmarks...")
    control_benchmark = ControlLoopBenchmark()

    if args.quick:
        control_benchmark.benchmark_plp_control(iterations=1000)
        control_benchmark.benchmark_hbcm_step_with_control(iterations=1000)
    else:
        control_benchmark.run_all()

    all_results['control_loop'] = [
        {
            'test_name': r.test_name,
            'iterations': r.iterations,
            'mean_latency_ms': r.mean_latency_ms,
            'median_latency_ms': r.median_latency_ms,
            'p95_latency_ms': r.p95_latency_ms,
            'p99_latency_ms': r.p99_latency_ms,
            'p999_latency_ms': r.p999_latency_ms,
            'min_latency_ms': r.min_latency_ms,
            'max_latency_ms': r.max_latency_ms,
            'target_met': r.target_met,
            'margin_ms': r.margin_ms,
            'metadata': r.metadata
        }
        for r in control_benchmark.results
    ]

    # Calculate summary
    total_tests = len(all_results['hbcm']) + len(all_results['control_loop'])
    control_passed = sum(1 for r in control_benchmark.results if r.target_met)

    all_results['summary'] = {
        'total_tests': total_tests,
        'passed': control_passed,
        'all_passed': control_passed == len(all_results['control_loop']),
        'control_loop_pass_rate': control_passed / len(all_results['control_loop']) if all_results['control_loop'] else 0
    }

    # Save JSON results
    if args.save_json:
        with open(args.save_json, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n✅ JSON results saved to: {args.save_json}")

    # Generate HTML report
    if args.save_report:
        generate_html_report(all_results, args.save_report)
        print(f"\n✅ HTML report saved to: {args.save_report}")

    # Print final summary
    print("\n" + "=" * 80)
    print("BENCHMARK SUITE COMPLETE")
    print("=" * 80)
    print(f"\nTotal Benchmarks Run: {total_tests}")
    print(f"Control Loop Targets Met: {control_passed}/{len(all_results['control_loop'])}")

    if all_results['summary']['all_passed']:
        print("\n✅ ALL TARGETS MET - System ready for production deployment")
    elif all_results['summary']['control_loop_pass_rate'] >= 0.8:
        print("\n⚠️  MOST TARGETS MET - Review failed tests before deployment")
    else:
        print("\n❌ OPTIMIZATION REQUIRED - System needs performance improvements")

    print("\nFor detailed results, see HTML report or JSON output.")


if __name__ == '__main__':
    main()
