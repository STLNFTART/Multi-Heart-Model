#!/usr/bin/env python3
"""
Run OpenSim Co-Simulation

Command-line script for running HBCM-OpenSim coupled simulations.
Can be called from Node.js API or standalone.
"""

import sys
import json
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cardiac import VanDerPolOscillator
from src.neural import FitzHughNagumo
from src.coupling import HeartBrainCouplingModel, CouplingParameters
from integrations.opensim.opensim_bridge import (
    OpenSimBridge,
    OpenSimConfig,
    HBCMOpenSimCoSimulator
)


def main():
    """Main entry point."""
    # Read config from command line or stdin
    if len(sys.argv) > 1:
        config = json.loads(sys.argv[1])
    else:
        config = json.load(sys.stdin)

    # Extract parameters
    duration = config.get('duration', 10.0)
    dt = config.get('dt', 0.001)
    opensim_model = config.get('opensim_model', None)
    coupling_gain = config.get('coupling_gain', 0.1)

    # Neural params
    neural_params = config.get('neural_params', {})
    neural_model = FitzHughNagumo(
        a=neural_params.get('a', 0.7),
        b=neural_params.get('b', 0.8),
        c=neural_params.get('c', 3.0),
        stimulus_amplitude=neural_params.get('stimulus_amplitude', 0.5)
    )

    # Cardiac params
    cardiac_params = config.get('cardiac_params', {})
    cardiac_model = VanDerPolOscillator(
        mu=cardiac_params.get('mu', 1.5),
        omega=cardiac_params.get('omega', 1.0),
        damping=cardiac_params.get('damping', 0.1)
    )

    # Coupling params
    coupling_params = config.get('coupling_params', {})
    coupling = CouplingParameters(
        neural_to_cardiac_gain=coupling_params.get('neural_to_cardiac_gain', 0.5),
        cardiac_to_neural_gain=coupling_params.get('cardiac_to_neural_gain', 0.3),
        neural_to_cardiac_delay=coupling_params.get('neural_to_cardiac_delay', 0.12),
        cardiac_to_neural_delay=coupling_params.get('cardiac_to_neural_delay', 0.15)
    )

    # Create HBCM
    hbcm = HeartBrainCouplingModel(
        neural_model=neural_model,
        cardiac_model=cardiac_model,
        coupling=coupling
    )

    # Create OpenSim bridge
    opensim_config = OpenSimConfig(
        model_file=opensim_model,
        dt=dt
    )
    opensim_bridge = OpenSimBridge(opensim_config)

    if opensim_model and opensim_bridge.opensim_available:
        # Run co-simulation
        cosim = HBCMOpenSimCoSimulator(
            hbcm_model=hbcm,
            opensim_bridge=opensim_bridge,
            coupling_gain=coupling_gain
        )

        initial_state = config.get('initial_state', (0.0, 0.0, 1.0, 0.0))

        results = cosim.simulate(
            initial_hbcm_state=tuple(initial_state),
            duration=duration,
            dt=dt
        )

        # Export if requested
        if config.get('export_dir'):
            cosim.export_to_opensim(config['export_dir'])

        # Return results as JSON
        output = {
            'success': True,
            'mode': 'co-simulation',
            'opensim_available': True,
            'duration': duration,
            'n_steps': results['n_steps'],
            'metrics': {
                'final_state': results['hbcm_states'][-1] if results['hbcm_states'] else None,
                'muscle_activation_range': [
                    min([min(a.values()) for a in results['muscle_activations']]) if results['muscle_activations'] else 0,
                    max([max(a.values()) for a in results['muscle_activations']]) if results['muscle_activations'] else 0
                ]
            }
        }

    else:
        # OpenSim not available, just run HBCM
        print("OpenSim not available, running HBCM only", file=sys.stderr)

        initial_state = config.get('initial_state', (0.0, 0.0, 1.0, 0.0))

        trajectory = hbcm.simulate(
            initial_state=tuple(initial_state),
            t_span=(0.0, duration),
            dt=dt
        )

        times, neural, cardiac = hbcm.extract_series(trajectory)

        output = {
            'success': True,
            'mode': 'hbcm-only',
            'opensim_available': False,
            'duration': duration,
            'n_steps': len(times),
            'metrics': {
                'final_state': trajectory[-1][1] if trajectory else None,
                'neural_max': max([v for v, w in neural]) if neural else 0,
                'cardiac_max': max([x for x, y in cardiac]) if cardiac else 0
            }
        }

    print(json.dumps(output))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        error_output = {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
        print(json.dumps(error_output))
        sys.exit(1)
