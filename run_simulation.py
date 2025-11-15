#!/usr/bin/env python3
"""
Run Heart-Brain Coupling Simulation

Simple CLI script for running HBCM simulations.
Designed to be called from Node.js or other external processes.

Usage:
    python run_simulation.py '{"duration": 10.0, "dt": 0.001}'
    echo '{"duration": 10.0}' | python run_simulation.py
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters


def main():
    """Run simulation based on JSON config."""
    # Read config
    if len(sys.argv) > 1:
        config = json.loads(sys.argv[1])
    else:
        config = json.load(sys.stdin)

    # Extract parameters with defaults
    duration = config.get('duration', 10.0)
    dt = config.get('dt', 0.001)
    initial_state = tuple(config.get('initial_state', [0.0, 0.0, 1.0, 0.0]))

    # Neural parameters
    neural_params = config.get('neural_params', {})
    neural_model = FitzHughNagumo(
        a=neural_params.get('a', 0.7),
        b=neural_params.get('b', 0.8),
        c=neural_params.get('c', 3.0),
        stimulus_amplitude=neural_params.get('stimulus_amplitude', 0.5)
    )

    # Cardiac parameters
    cardiac_params = config.get('cardiac_params', {})
    cardiac_model = VanDerPolOscillator(
        mu=cardiac_params.get('mu', 1.5),
        omega=cardiac_params.get('omega', 1.0),
        damping=cardiac_params.get('damping', 0.1)
    )

    # Coupling parameters
    coupling_params = config.get('coupling_params', {})
    coupling = CouplingParameters(
        neural_to_cardiac_gain=coupling_params.get('neural_to_cardiac_gain', 0.5),
        cardiac_to_neural_gain=coupling_params.get('cardiac_to_neural_gain', 0.3),
        neural_to_cardiac_delay=coupling_params.get('neural_to_cardiac_delay', 0.12),
        cardiac_to_neural_delay=coupling_params.get('cardiac_to_neural_delay', 0.15)
    )

    # Create model
    hbcm = HeartBrainCouplingModel(
        neural_model=neural_model,
        cardiac_model=cardiac_model,
        coupling=coupling
    )

    # Run simulation
    trajectory = hbcm.simulate(
        initial_state=initial_state,
        t_span=(0.0, duration),
        dt=dt
    )

    # Extract time series
    times, neural, cardiac = hbcm.extract_series(trajectory)

    # Calculate statistics
    neural_v = [v for v, w in neural]
    neural_w = [w for v, w in neural]
    cardiac_x = [x for x, y in cardiac]
    cardiac_y = [y for x, y in cardiac]

    # Build result
    result = {
        'success': True,
        'duration': duration,
        'dt': dt,
        'n_steps': len(times),
        'trajectory': [
            {
                'time': t,
                'state': list(s)
            }
            for t, s in trajectory[::max(1, len(trajectory) // 1000)]  # Subsample to 1000 points
        ],
        'metrics': {
            'neural': {
                'v_mean': sum(neural_v) / len(neural_v),
                'v_max': max(neural_v),
                'v_min': min(neural_v),
                'v_std': (sum([(v - sum(neural_v) / len(neural_v)) ** 2 for v in neural_v]) / len(neural_v)) ** 0.5,
                'w_mean': sum(neural_w) / len(neural_w),
                'w_max': max(neural_w),
                'w_min': min(neural_w)
            },
            'cardiac': {
                'x_mean': sum(cardiac_x) / len(cardiac_x),
                'x_max': max(cardiac_x),
                'x_min': min(cardiac_x),
                'x_std': (sum([(x - sum(cardiac_x) / len(cardiac_x)) ** 2 for x in cardiac_x]) / len(cardiac_x)) ** 0.5,
                'y_mean': sum(cardiac_y) / len(cardiac_y),
                'y_max': max(cardiac_y),
                'y_min': min(cardiac_y)
            }
        },
        'config': config
    }

    # Output as JSON
    print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        error_result = {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
