#!/usr/bin/env python3
"""
MotorHandPro Live Leaderboard Dashboard

One-liner to run:
    streamlit run motorhand_dashboard.py

Or with custom results directory:
    RESULTS_DIR=~/drive_links/ALL_MY_WORK/SimResults streamlit run motorhand_dashboard.py

Author: Lightfoot Technology
"""

import os
import csv
import json
from pathlib import Path
from datetime import datetime

try:
    import streamlit as st
except ImportError:
    print("⚠ Streamlit not installed")
    print("Install with: pip install streamlit")
    print("Then run with: streamlit run motorhand_dashboard.py")
    exit(1)


# Configuration
RESULTS_BASE = os.getenv('RESULTS_DIR', os.path.expanduser('~/Multi-Heart-Model-Results'))


def load_latest_results(category: str):
    """Load latest results for a given category"""
    category_dir = Path(RESULTS_BASE) / category

    if not category_dir.exists():
        return None, None

    # Find latest run
    runs = sorted([d for d in category_dir.iterdir() if d.is_dir()])
    if not runs:
        return None, None

    latest_run = runs[-1]
    csv_path = latest_run / 'summary' / 'summary.csv'

    if not csv_path.exists():
        return None, latest_run.name

    # Load CSV
    results = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)

    return results, latest_run.name


def load_metadata(category: str, run_name: str):
    """Load metadata for a specific run"""
    metadata_path = Path(RESULTS_BASE) / category / run_name / 'metadata.json'

    if not metadata_path.exists():
        return None

    with open(metadata_path, 'r') as f:
        return json.load(f)


def main():
    st.set_page_config(
        page_title="MotorHandPro Leaderboard",
        page_icon="🏁",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🏁 MotorHandPro Parameter Sweep Leaderboard")
    st.markdown("**Real-time results from Google Drive**")

    # Sidebar
    st.sidebar.header("Dashboard Controls")

    # Check results availability
    if not Path(RESULTS_BASE).exists():
        st.error(f"❌ Results directory not found: {RESULTS_BASE}")
        st.info("Run parameter sweeps first:\n```bash\npython sweep_motorhand_drive.py --quick\n```")
        return

    # Category selection
    categories = {
        'motorhand_control_params': 'Control Parameters',
        'motorhand_emergency_scenarios': 'Emergency Scenarios',
        'motorhand_throttle_conversion': 'Throttle Conversion',
        'motorhand_ipu_scaling': 'IPU Scaling',
        'motorhand_closed_loop': 'Closed-Loop Integration'
    }

    selected_category = st.sidebar.selectbox(
        "Select Category",
        list(categories.keys()),
        format_func=lambda x: categories[x]
    )

    # Load results
    results, run_name = load_latest_results(selected_category)

    if results is None:
        st.warning(f"⚠ No results found for: {categories[selected_category]}")
        st.info("Run sweeps to generate data")
        return

    # Display metadata
    metadata = load_metadata(selected_category, run_name)
    if metadata:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Run ID", run_name[:16] + "...")
        with col2:
            st.metric("Total Results", metadata['parameters'].get('total_results', len(results)))
        with col3:
            start_time = datetime.fromisoformat(metadata['start_time'])
            st.metric("Date", start_time.strftime("%Y-%m-%d"))
        with col4:
            st.metric("Git Branch", metadata.get('git_branch', 'N/A')[:20])

    # Main content based on category
    if selected_category == 'motorhand_control_params':
        display_control_params_leaderboard(results)
    elif selected_category == 'motorhand_emergency_scenarios':
        display_emergency_scenarios_leaderboard(results)
    elif selected_category == 'motorhand_throttle_conversion':
        display_throttle_conversion(results)
    elif selected_category == 'motorhand_ipu_scaling':
        display_ipu_scaling(results)
    elif selected_category == 'motorhand_closed_loop':
        display_closed_loop(results)


def display_control_params_leaderboard(results):
    """Display control parameters leaderboard"""
    st.header("🎯 Control Parameters Leaderboard")

    # Convert to numeric
    for r in results:
        r['comfort_index'] = float(r['comfort_index'])
        r['settling_time'] = float(r['settling_time'])
        r['rms_jerk'] = float(r['rms_jerk'])
        r['smoothness'] = float(r['smoothness'])
        r['stable'] = r['stable'].lower() == 'true'

    # Filter stable
    stable = [r for r in results if r['stable']]
    unstable_count = len(results) - len(stable)

    st.info(f"**Stable Configurations:** {len(stable)}/{len(results)} ({len(stable)/len(results)*100:.1f}%)")
    if unstable_count > 0:
        st.warning(f"⚠ {unstable_count} unstable configurations filtered out")

    # Tabs for different rankings
    tab1, tab2, tab3 = st.tabs(["🏆 Best Comfort", "⚡ Fastest Settling", "📊 Overall"])

    with tab1:
        st.subheader("Top 10 - Maximum Comfort")
        top_comfort = sorted(stable, key=lambda x: x['comfort_index'], reverse=True)[:10]

        for i, config in enumerate(top_comfort, 1):
            with st.expander(f"#{i} - Comfort: {config['comfort_index']:.1f}/100"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Parameters:**")
                    st.write(f"- K_gain: {config['K_gain']}")
                    st.write(f"- lambda_decay: {config['lambda_decay']}")
                    st.write(f"- num_IPUs: {config['num_ipus']}")
                with col2:
                    st.write("**Metrics:**")
                    st.write(f"- Settling Time: {config['settling_time']:.2f}s")
                    st.write(f"- RMS Jerk: {config['rms_jerk']:.3f}")
                    st.write(f"- Smoothness: {config['smoothness']:.3f}")

    with tab2:
        st.subheader("Top 10 - Fastest Settling")
        top_speed = sorted(stable, key=lambda x: x['settling_time'])[:10]

        for i, config in enumerate(top_speed, 1):
            with st.expander(f"#{i} - Settling: {config['settling_time']:.2f}s"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Parameters:**")
                    st.write(f"- K_gain: {config['K_gain']}")
                    st.write(f"- lambda_decay: {config['lambda_decay']}")
                    st.write(f"- num_IPUs: {config['num_ipus']}")
                with col2:
                    st.write("**Metrics:**")
                    st.write(f"- Comfort Index: {config['comfort_index']:.1f}/100")
                    st.write(f"- RMS Jerk: {config['rms_jerk']:.3f}")
                    st.write(f"- Smoothness: {config['smoothness']:.3f}")

    with tab3:
        st.subheader("Top 10 - Balanced Score (70% Comfort + 30% Speed)")

        # Compute composite score
        for r in stable:
            r['composite'] = (r['comfort_index'] * 0.7) - (r['settling_time'] * 3.0)

        top_balanced = sorted(stable, key=lambda x: x['composite'], reverse=True)[:10]

        for i, config in enumerate(top_balanced, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"#{i}"
            with st.expander(f"{medal} - Score: {config['composite']:.1f}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Parameters:**")
                    st.write(f"- K_gain: {config['K_gain']}")
                    st.write(f"- lambda_decay: {config['lambda_decay']}")
                    st.write(f"- num_IPUs: {config['num_ipus']}")
                with col2:
                    st.write("**Metrics:**")
                    st.write(f"- Comfort Index: {config['comfort_index']:.1f}/100")
                    st.write(f"- Settling Time: {config['settling_time']:.2f}s")
                    st.write(f"- RMS Jerk: {config['rms_jerk']:.3f}")


def display_emergency_scenarios_leaderboard(results):
    """Display emergency scenarios leaderboard"""
    st.header("🚨 Emergency Scenarios Performance")

    # Convert to numeric
    for r in results:
        r['tracking_error'] = float(r['tracking_error'])
        r['avg_comfort'] = float(r['avg_comfort'])
        r['success'] = r['success'].lower() == 'true'

    success_count = sum(1 for r in results if r['success'])
    st.success(f"**Success Rate:** {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")

    # Group by scenario
    scenarios = {}
    for r in results:
        scenario_key = f"{r['initial_velocity']}→{r['target_velocity']} m/s"
        if scenario_key not in scenarios:
            scenarios[scenario_key] = []
        scenarios[scenario_key].append(r)

    for scenario, runs in scenarios.items():
        with st.expander(f"📋 {scenario}"):
            avg_error = sum(r['tracking_error'] for r in runs) / len(runs)
            avg_comfort = sum(r['avg_comfort'] for r in runs) / len(runs)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Tracking Error", f"{avg_error:.3f} m/s")
            with col2:
                st.metric("Avg Comfort", f"{avg_comfort:.1f}/100")
            with col3:
                st.metric("Runs", len(runs))


def display_throttle_conversion(results):
    """Display throttle conversion validation"""
    st.header("🔧 Throttle Conversion Validation")

    # Convert to numeric
    for r in results:
        r['conversion_error'] = int(r['conversion_error'])
        r['accurate_conversion'] = r['accurate_conversion'].lower() == 'true'

    accurate_count = sum(1 for r in results if r['accurate_conversion'])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tests", len(results))
    with col2:
        st.metric("Accurate", accurate_count)
    with col3:
        st.metric("Accuracy", f"{accurate_count/len(results)*100:.1f}%")

    if accurate_count == len(results):
        st.success("✓ 100% conversion accuracy - QUANT interface validated!")
    else:
        st.warning(f"⚠ {len(results) - accurate_count} conversions with errors")

    # Show error distribution
    max_error = max(r['conversion_error'] for r in results)
    st.write(f"**Maximum Conversion Error:** {max_error} throttle units")


def display_ipu_scaling(results):
    """Display IPU scaling performance"""
    st.header("⚙️ IPU Scaling Performance")

    # Convert to numeric
    for r in results:
        r['num_ipus'] = int(r['num_ipus'])
        r['comfort_index'] = float(r['comfort_index'])
        r['power_consumption_w'] = float(r['power_consumption_w'])
        r['efficiency'] = float(r['efficiency'])

    # Sort by IPU count
    sorted_results = sorted(results, key=lambda x: x['num_ipus'])

    for config in sorted_results:
        with st.expander(f"🔢 {config['num_ipus']} IPUs"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Comfort Index", f"{config['comfort_index']:.1f}/100")
            with col2:
                st.metric("Power", f"{config['power_consumption_w']:.1f} W")
            with col3:
                st.metric("Efficiency", f"{config['efficiency']:.2f}")


def display_closed_loop(results):
    """Display closed-loop integration results"""
    st.header("🔁 Closed-Loop Integration")

    # Convert to numeric
    for r in results:
        r['tracking_error'] = float(r['tracking_error'])
        r['comfort_index'] = float(r['comfort_index'])
        r['success'] = r['success'].lower() == 'true'

    success_count = sum(1 for r in results if r['success'])
    st.success(f"**Success Rate:** {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")

    for scenario in results:
        status = "✓" if scenario['success'] else "✗"
        with st.expander(f"{status} {scenario['scenario']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**v0 → vf:** {scenario['initial_velocity']} → {scenario['target_velocity']} m/s")
                st.write(f"**Duration:** {scenario['duration']}s")
            with col2:
                st.metric("Tracking Error", f"{scenario['tracking_error']:.3f} m/s")
                st.metric("Comfort", f"{scenario['comfort_index']:.1f}/100")
            with col3:
                st.write(f"**Settling Time:** {scenario['settling_time']:.2f}s")
                st.write(f"**RMS Jerk:** {scenario['rms_jerk']:.3f}")


if __name__ == '__main__':
    main()
