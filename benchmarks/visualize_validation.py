"""
Visualization Tool for PLP vs PID Validation Results

Generates publication-quality plots from benchmark data for:
- Partnership presentations
- Technical briefs
- Research publications

Usage:
    python benchmarks/visualize_validation.py
    python benchmarks/visualize_validation.py --output plots/
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path


def load_results(results_file: str = "/home/user/Multi-Heart-Model/benchmarks/results/plp_vs_pid_validation.json"):
    """Load validation results from JSON."""
    with open(results_file, 'r') as f:
        return json.load(f)


def plot_step_response(results: dict, output_dir: str = "/home/user/Multi-Heart-Model/benchmarks/plots"):
    """Create step response comparison plot."""

    # Extract data
    time = np.array(results['step_response_second_order']['time'])
    output_plp = np.array(results['step_response_second_order']['output_plp'])
    output_pid = np.array(results['step_response_second_order']['output_pid'])
    control_plp = np.array(results['step_response_second_order']['control_plp'])
    control_pid = np.array(results['step_response_second_order']['control_pid'])
    setpoint = results['step_response_second_order']['setpoint']

    # Extract metrics
    metrics_plp = results['step_response_second_order']['metrics_plp']
    metrics_pid = results['step_response_second_order']['metrics_pid']

    # Create figure
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)

    # Plot 1: Output comparison
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(time, output_plp, 'b-', linewidth=2, label='PLP Output', alpha=0.8)
    ax1.plot(time, output_pid, 'r--', linewidth=2, label='PID Output', alpha=0.8)
    ax1.axhline(y=setpoint, color='k', linestyle=':', linewidth=1.5, label='Setpoint')
    ax1.axhline(y=setpoint * 1.02, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    ax1.axhline(y=setpoint * 0.98, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    ax1.fill_between([0, 10], setpoint * 0.98, setpoint * 1.02, color='green', alpha=0.1,
                      label='±2% Settling Band')
    ax1.set_xlabel('Time (s)', fontsize=12)
    ax1.set_ylabel('Output', fontsize=12)
    ax1.set_title('Step Response Comparison: PLP vs Traditional PID', fontsize=14, fontweight='bold')
    ax1.legend(loc='lower right', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, 10])

    # Add settling time annotations
    settling_plp = metrics_plp['settling_time']
    settling_pid = metrics_pid['settling_time']
    ax1.axvline(x=settling_plp, color='blue', linestyle='--', alpha=0.5, linewidth=1)
    ax1.axvline(x=settling_pid, color='red', linestyle='--', alpha=0.5, linewidth=1)
    ax1.text(settling_plp, 0.5, f'PLP: {settling_plp:.2f}s', rotation=90,
             verticalalignment='bottom', color='blue', fontsize=9)
    ax1.text(settling_pid, 0.5, f'PID: {settling_pid:.2f}s', rotation=90,
             verticalalignment='bottom', color='red', fontsize=9)

    # Plot 2: Control signals
    ax2 = fig.add_subplot(gs[1, :])
    ax2.plot(time, control_plp, 'b-', linewidth=1.5, label='PLP Control', alpha=0.8)
    ax2.plot(time, control_pid, 'r--', linewidth=1.5, label='PID Control', alpha=0.8)
    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Control Signal', fontsize=12)
    ax2.set_title('Control Signal Comparison', fontsize=13, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, 10])

    # Plot 3: Performance metrics bar chart
    ax3 = fig.add_subplot(gs[2, 0])
    metrics_to_compare = [
        ('Settling Time (s)', 'settling_time'),
        ('Rise Time (s)', 'rise_time'),
        ('Control Effort', 'control_effort')
    ]

    x_pos = np.arange(len(metrics_to_compare))
    plp_vals = [metrics_plp[m[1]] for m in metrics_to_compare]
    pid_vals = [metrics_pid[m[1]] for m in metrics_to_compare]

    width = 0.35
    ax3.bar(x_pos - width/2, plp_vals, width, label='PLP', color='blue', alpha=0.7)
    ax3.bar(x_pos + width/2, pid_vals, width, label='PID', color='red', alpha=0.7)
    ax3.set_ylabel('Value', fontsize=11)
    ax3.set_title('Performance Metrics', fontsize=12, fontweight='bold')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels([m[0] for m in metrics_to_compare], rotation=15, ha='right', fontsize=9)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Improvement percentage
    ax4 = fig.add_subplot(gs[2, 1])
    improvements = []
    labels = []
    for metric_name, metric_key in metrics_to_compare:
        plp_val = metrics_plp[metric_key]
        pid_val = metrics_pid[metric_key]

        if pid_val != 0:
            improvement = ((pid_val - plp_val) / pid_val) * 100
        else:
            improvement = 0

        improvements.append(improvement)
        labels.append(metric_name)

    colors = ['green' if imp > 0 else 'red' for imp in improvements]
    bars = ax4.barh(labels, improvements, color=colors, alpha=0.7)
    ax4.set_xlabel('Improvement (%)', fontsize=11)
    ax4.set_title('PLP Improvement Over PID', fontsize=12, fontweight='bold')
    ax4.axvline(x=0, color='black', linewidth=1, linestyle='-')
    ax4.grid(True, alpha=0.3, axis='x')

    # Add percentage labels
    for i, (bar, val) in enumerate(zip(bars, improvements)):
        if val > 0:
            ha = 'left'
            x_offset = 2
        else:
            ha = 'right'
            x_offset = -2
        ax4.text(val + x_offset, i, f'{val:+.1f}%', ha=ha, va='center', fontsize=9)

    # Save figure
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_file = f"{output_dir}/plp_vs_pid_step_response.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")

    plt.close()


def plot_disturbance_rejection(results: dict, output_dir: str = "/home/user/Multi-Heart-Model/benchmarks/plots"):
    """Create disturbance rejection comparison plot."""

    # Extract data
    time = np.array(results['disturbance_rejection']['time'])
    output_plp = np.array(results['disturbance_rejection']['output_plp'])
    output_pid = np.array(results['disturbance_rejection']['output_pid'])
    disturbance_time = results['disturbance_rejection']['disturbance_time']

    # Extract metrics
    metrics_plp = results['disturbance_rejection']['metrics_plp']
    metrics_pid = results['disturbance_rejection']['metrics_pid']

    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot 1: Full time series
    ax1.plot(time, output_plp, 'b-', linewidth=2, label='PLP Output', alpha=0.8)
    ax1.plot(time, output_pid, 'r--', linewidth=2, label='PID Output', alpha=0.8)
    ax1.axvline(x=disturbance_time, color='orange', linestyle=':', linewidth=2,
                label=f'Disturbance at t={disturbance_time}s')
    ax1.axhline(y=1.0, color='k', linestyle=':', linewidth=1, label='Setpoint')
    ax1.set_xlabel('Time (s)', fontsize=12)
    ax1.set_ylabel('Output', fontsize=12)
    ax1.set_title('Disturbance Rejection Comparison: PLP vs PID', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, 20])

    # Plot 2: Zoomed in around disturbance
    zoom_start = disturbance_time - 2
    zoom_end = disturbance_time + 8
    zoom_mask = (time >= zoom_start) & (time <= zoom_end)

    ax2.plot(time[zoom_mask], output_plp[zoom_mask], 'b-', linewidth=2, label='PLP Output', alpha=0.8)
    ax2.plot(time[zoom_mask], output_pid[zoom_mask], 'r--', linewidth=2, label='PID Output', alpha=0.8)
    ax2.axvline(x=disturbance_time, color='orange', linestyle=':', linewidth=2)
    ax2.axhline(y=1.0, color='k', linestyle=':', linewidth=1)
    ax2.axhline(y=1.02, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    ax2.axhline(y=0.98, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    ax2.fill_between(time[zoom_mask], 0.98, 1.02, color='green', alpha=0.1,
                      label='±2% Settling Band')

    # Add recovery time annotations
    recovery_plp = disturbance_time + metrics_plp['disturbance_rejection_time']
    recovery_pid = disturbance_time + metrics_pid['disturbance_rejection_time']

    if recovery_plp > zoom_start and recovery_plp < zoom_end:
        ax2.axvline(x=recovery_plp, color='blue', linestyle='--', alpha=0.5, linewidth=1)
        ax2.text(recovery_plp, 0.9, f'PLP Recovery:\n{metrics_plp["disturbance_rejection_time"]:.3f}s',
                 rotation=0, verticalalignment='top', color='blue', fontsize=9, ha='center')

    if recovery_pid > zoom_start and recovery_pid < zoom_end:
        ax2.axvline(x=recovery_pid, color='red', linestyle='--', alpha=0.5, linewidth=1)
        ax2.text(recovery_pid, 0.9, f'PID Recovery:\n{metrics_pid["disturbance_rejection_time"]:.3f}s',
                 rotation=0, verticalalignment='top', color='red', fontsize=9, ha='center')

    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Output', fontsize=12)
    ax2.set_title('Zoomed View: Recovery After Disturbance', fontsize=13, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([zoom_start, zoom_end])

    plt.tight_layout()

    # Save figure
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_file = f"{output_dir}/plp_vs_pid_disturbance_rejection.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")

    plt.close()


def create_summary_table(results: dict, output_dir: str = "/home/user/Multi-Heart-Model/benchmarks/plots"):
    """Create summary comparison table as an image."""

    metrics_plp = results['step_response_second_order']['metrics_plp']
    metrics_pid = results['step_response_second_order']['metrics_pid']

    # Prepare data for table
    metrics_list = [
        ('Settling Time (s)', 'settling_time', 'lower'),
        ('Rise Time (s)', 'rise_time', 'lower'),
        ('Overshoot (%)', 'overshoot_percent', 'lower'),
        ('Steady-State Error', 'steady_state_error', 'lower'),
        ('Control Effort', 'control_effort', 'lower'),
        ('Computation Time (μs)', 'computation_time_us', 'lower'),
        ('Disturbance Recovery (s)', 'disturbance_rejection_time', 'lower')
    ]

    # Add disturbance metrics
    dist_metrics_plp = results['disturbance_rejection']['metrics_plp']
    dist_metrics_pid = results['disturbance_rejection']['metrics_pid']

    # Build table data
    table_data = []
    headers = ['Metric', 'PLP', 'PID', 'Winner', 'Improvement']

    for i, (metric_name, metric_key, better) in enumerate(metrics_list):
        # Get values
        if metric_key == 'disturbance_rejection_time':
            plp_val = dist_metrics_plp[metric_key]
            pid_val = dist_metrics_pid[metric_key]
        else:
            plp_val = metrics_plp.get(metric_key, 0)
            pid_val = metrics_pid.get(metric_key, 0)

        # Determine winner
        if better == 'lower':
            winner = 'PLP' if plp_val < pid_val else 'PID'
        else:
            winner = 'PLP' if plp_val > pid_val else 'PID'

        # Calculate improvement
        if pid_val != 0:
            improvement = ((pid_val - plp_val) / pid_val) * 100
        else:
            improvement = 0

        table_data.append([
            metric_name,
            f'{plp_val:.4f}',
            f'{pid_val:.4f}',
            winner,
            f'{improvement:+.1f}%'
        ])

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('tight')
    ax.axis('off')

    table = ax.table(cellText=table_data, colLabels=headers, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Color code cells
    for i in range(len(table_data)):
        winner_cell = table[(i+1, 3)]
        improvement_cell = table[(i+1, 4)]

        # Color winner column
        if table_data[i][3] == 'PLP':
            winner_cell.set_facecolor('#90EE90')  # Light green
        else:
            winner_cell.set_facecolor('#FFB6C1')  # Light red

        # Color improvement column
        improvement_val = float(table_data[i][4].strip('%'))
        if improvement_val > 0:
            improvement_cell.set_facecolor('#90EE90')  # Light green
        else:
            improvement_cell.set_facecolor('#FFB6C1')  # Light red

    # Header styling
    for j in range(len(headers)):
        table[(0, j)].set_facecolor('#4472C4')
        table[(0, j)].set_text_props(weight='bold', color='white')

    plt.title('PLP vs PID: Quantitative Performance Comparison',
              fontsize=16, fontweight='bold', pad=20)

    # Save figure
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_file = f"{output_dir}/plp_vs_pid_summary_table.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")

    plt.close()


def main():
    """Generate all validation plots."""
    print("\n" + "=" * 70)
    print("PLP VS PID VALIDATION - VISUALIZATION GENERATOR")
    print("=" * 70)

    # Load results
    print("\nLoading validation results...")
    results = load_results()

    output_dir = "/home/user/Multi-Heart-Model/benchmarks/plots"

    # Generate plots
    print("\nGenerating step response plot...")
    plot_step_response(results, output_dir)

    print("Generating disturbance rejection plot...")
    plot_disturbance_rejection(results, output_dir)

    print("Generating summary table...")
    create_summary_table(results, output_dir)

    print("\n" + "=" * 70)
    print("VISUALIZATION COMPLETE")
    print("=" * 70)
    print(f"\n📊 All plots saved to: {output_dir}/")
    print("\nGenerated files:")
    print("  1. plp_vs_pid_step_response.png")
    print("  2. plp_vs_pid_disturbance_rejection.png")
    print("  3. plp_vs_pid_summary_table.png")
    print("\n✅ Ready for partnership presentations and technical briefs!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
