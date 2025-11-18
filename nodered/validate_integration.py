#!/usr/bin/env python3
"""
Node-RED Integration Validation Script

Tests the Phase 1 Node-RED integration with FastAPI backend.

Author: Multi-Heart-Model Team
Date: 2025-11-15
"""

import sys
import time
import json
import requests
import subprocess
from pathlib import Path
from typing import Tuple, Optional

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def print_header(text: str):
    """Print section header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print('=' * 60)


def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}✓ {text}{NC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{NC}")


def print_error(text: str):
    """Print error message."""
    print(f"{RED}✗ {text}{NC}")


def print_info(text: str):
    """Print info message."""
    print(f"{BLUE}ℹ {text}{NC}")


def check_fastapi_running() -> Tuple[bool, str]:
    """Check if FastAPI backend is running."""
    try:
        response = requests.get('http://localhost:8000/api/status', timeout=2)
        if response.status_code == 200:
            return True, f"FastAPI running: {response.json()}"
        else:
            return False, f"FastAPI returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to http://localhost:8000"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_nodered_running() -> Tuple[bool, str]:
    """Check if Node-RED is running."""
    try:
        response = requests.get('http://localhost:1880', timeout=2)
        if response.status_code == 200:
            return True, "Node-RED editor accessible"
        else:
            return False, f"Node-RED returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to http://localhost:1880"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_nodered_dashboard() -> Tuple[bool, str]:
    """Check if Node-RED dashboard is accessible."""
    try:
        response = requests.get('http://localhost:1880/ui', timeout=2)
        if response.status_code == 200:
            return True, "Dashboard UI accessible"
        else:
            return False, f"Dashboard returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to http://localhost:1880/ui"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_files_exist() -> Tuple[bool, list]:
    """Check if required files exist."""
    required_files = [
        'flows.json',
        'package.json',
        'setup.sh',
        'README.md'
    ]

    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)

    return len(missing) == 0, missing


def test_fastapi_control_endpoint() -> Tuple[bool, str]:
    """Test FastAPI control endpoint."""
    try:
        # Test status endpoint first
        response = requests.post(
            'http://localhost:8000/api/control',
            json={'command': 'status'},
            timeout=2
        )
        if response.status_code in [200, 400]:  # 400 might be "not running" which is OK
            return True, f"Control endpoint responsive (status: {response.status_code})"
        else:
            return False, f"Control endpoint returned {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def test_simulation_workflow() -> Tuple[bool, str]:
    """Test complete simulation workflow via API."""
    try:
        print_info("Testing complete simulation workflow...")

        # 1. Configure simulation
        print("  1. Configuring simulation...")
        config_response = requests.post(
            'http://localhost:8000/api/config/simulation',
            json={
                'initial_state': [0.0, 0.0, 1.0, 0.0],
                't_start': 0.0,
                't_end': 1.0,
                'dt': 0.01,
                'neural_params': {'a': 0.7, 'b': 0.8, 'c': 3.0},
                'cardiac_params': {'mu': 1.5, 'omega': 1.0}
            },
            timeout=5
        )

        if config_response.status_code != 200:
            return False, f"Config failed: {config_response.status_code}"

        # 2. Start simulation
        print("  2. Starting simulation...")
        start_response = requests.post(
            'http://localhost:8000/api/control',
            json={'command': 'start'},
            timeout=5
        )

        if start_response.status_code != 200:
            return False, f"Start failed: {start_response.status_code}"

        # 3. Wait a bit for simulation to run
        print("  3. Waiting for simulation...")
        time.sleep(2)

        # 4. Get data
        print("  4. Fetching simulation data...")
        data_response = requests.get(
            'http://localhost:8000/api/data/latest',
            timeout=5
        )

        if data_response.status_code != 200:
            return False, f"Data fetch failed: {data_response.status_code}"

        data = data_response.json()

        # Validate data structure
        if 'neural' not in data or 'cardiac' not in data:
            return False, "Data missing neural or cardiac fields"

        # 5. Stop simulation
        print("  5. Stopping simulation...")
        stop_response = requests.post(
            'http://localhost:8000/api/control',
            json={'command': 'stop'},
            timeout=5
        )

        return True, f"Workflow complete (data points: {len(data.get('time', []))})"

    except Exception as e:
        return False, f"Error: {str(e)}"


def check_node_modules() -> Tuple[bool, list]:
    """Check if Node-RED nodes are installed."""
    required_modules = [
        'node-red-dashboard'
    ]

    missing = []
    package_json = Path('package.json')

    if not package_json.exists():
        return False, required_modules

    try:
        with open(package_json) as f:
            pkg = json.load(f)
            deps = pkg.get('dependencies', {})

            for module in required_modules:
                if module not in deps:
                    missing.append(module)
    except Exception as e:
        return False, [f"Error reading package.json: {e}"]

    return len(missing) == 0, missing


def run_validation():
    """Run complete validation suite."""
    print_header("Node-RED Phase 1 Integration Validation")

    print_info("Validating Node-RED setup for Multi-Heart-Model HBCM...")
    print()

    results = []

    # Test 1: Check files exist
    print_header("Test 1: File Structure")
    files_ok, missing_files = check_files_exist()
    if files_ok:
        print_success("All required files present")
        results.append(True)
    else:
        print_error(f"Missing files: {', '.join(missing_files)}")
        results.append(False)

    # Test 2: Check node modules
    print_header("Test 2: Node-RED Dependencies")
    modules_ok, missing_modules = check_node_modules()
    if modules_ok:
        print_success("All required Node-RED nodes configured")
        results.append(True)
    else:
        print_warning(f"Missing modules: {', '.join(missing_modules)}")
        print_info("Run: npm install")
        results.append(False)

    # Test 3: Check FastAPI
    print_header("Test 3: FastAPI Backend")
    fastapi_ok, fastapi_msg = check_fastapi_running()
    if fastapi_ok:
        print_success(fastapi_msg)
        results.append(True)
    else:
        print_error(fastapi_msg)
        print_info("Start FastAPI: cd ../web_control_panel/backend && uvicorn main:app --reload")
        results.append(False)

    # Test 4: Check Node-RED
    print_header("Test 4: Node-RED Server")
    nodered_ok, nodered_msg = check_nodered_running()
    if nodered_ok:
        print_success(nodered_msg)
        results.append(True)
    else:
        print_error(nodered_msg)
        print_info("Start Node-RED: npm start (or: node-red --userDir .)")
        results.append(False)

    # Test 5: Check Dashboard
    print_header("Test 5: Node-RED Dashboard")
    dashboard_ok, dashboard_msg = check_nodered_dashboard()
    if dashboard_ok:
        print_success(dashboard_msg)
        print_info("Access at: http://localhost:1880/ui")
        results.append(True)
    else:
        print_warning(dashboard_msg)
        if nodered_ok:
            print_info("Dashboard might not be deployed. Check Node-RED editor.")
        results.append(False)

    # Test 6: Test control endpoint (only if FastAPI is running)
    if fastapi_ok:
        print_header("Test 6: FastAPI Control Endpoint")
        control_ok, control_msg = test_fastapi_control_endpoint()
        if control_ok:
            print_success(control_msg)
            results.append(True)
        else:
            print_error(control_msg)
            results.append(False)
    else:
        print_header("Test 6: FastAPI Control Endpoint")
        print_warning("Skipped (FastAPI not running)")
        results.append(False)

    # Test 7: Full workflow test (only if both services running)
    if fastapi_ok and nodered_ok:
        print_header("Test 7: End-to-End Workflow")
        workflow_ok, workflow_msg = test_simulation_workflow()
        if workflow_ok:
            print_success(workflow_msg)
            results.append(True)
        else:
            print_error(workflow_msg)
            results.append(False)
    else:
        print_header("Test 7: End-to-End Workflow")
        print_warning("Skipped (services not running)")
        results.append(False)

    # Summary
    print_header("Validation Summary")

    total_tests = len(results)
    passed_tests = sum(results)

    print(f"\nTests Passed: {passed_tests}/{total_tests}")

    if passed_tests == total_tests:
        print_success("All tests passed! ✓")
        print()
        print("Phase 1 Integration is ready to use:")
        print(f"  - Node-RED Editor: http://localhost:1880")
        print(f"  - HBCM Dashboard:  http://localhost:1880/ui")
        print()
        return 0
    elif passed_tests >= total_tests - 2:
        print_warning(f"Most tests passed ({passed_tests}/{total_tests})")
        print()
        print("Integration is partially functional.")
        print("Check warnings above and ensure all services are running.")
        print()
        return 1
    else:
        print_error(f"Multiple tests failed ({total_tests - passed_tests} failures)")
        print()
        print("Recommended actions:")
        if not fastapi_ok:
            print("  1. Start FastAPI backend")
        if not nodered_ok:
            print("  2. Start Node-RED")
        if not modules_ok:
            print("  3. Install Node-RED dependencies: npm install")
        print()
        return 2


if __name__ == "__main__":
    # Change to script directory
    script_dir = Path(__file__).parent
    import os
    os.chdir(script_dir)

    exit_code = run_validation()
    sys.exit(exit_code)
