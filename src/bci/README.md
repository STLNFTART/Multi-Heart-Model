# Brain-Computer Interface Integration for Multi-Heart-Model

This module provides integration between brain-computer interfaces (BCIs) and the heart-brain coupling model, enabling closed-loop neural control of physiological oscillators.

## Features

- **OpenBCI Interface**: Real-time EEG acquisition from OpenBCI hardware (Cyton, Ganglion)
- **Neuralink-Style Interface**: High-bandwidth neural recording for invasive BCIs
- **Signal Processing**: Bandpass filtering, spike detection, spectral analysis
- **Neural Bridge**: Seamless integration with FitzHugh-Nagumo and Van der Pol oscillators
- **Adaptive Control**: Lyapunov-based adaptive control with stability guarantees

## Requirements

### Python Dependencies

```bash
pip install numpy scipy matplotlib
```

For actual hardware interfacing:
```bash
pip install brainflow  # For OpenBCI hardware
```

### Hardware (Optional)

- **OpenBCI**: Cyton (8-channel) or Ganglion (4-channel) board
- **Neuralink**: N1 chip (1024 channels) or compatible high-density arrays

## Usage

### Mock Mode (No Hardware Required)

The BCI interfaces can run in mock mode for testing and development:

```python
from src.bci import OpenBCIInterface, OpenBCIConfig

# Create interface in mock mode
config = OpenBCIConfig(sample_rate=250.0, num_channels=8)
bci = OpenBCIInterface(config=config, mock_mode=True)

# Start data stream
bci.start_stream()

# Get data samples
timestamps, data = bci.get_latest_samples(n_samples=100)

# Compute neural drive signal
neural_drive = bci.compute_neural_drive(channel=0, method="alpha_beta_ratio")

# Stop stream
bci.stop_stream()
bci.close()
```

### Hardware Mode (OpenBCI)

```python
from src.bci import OpenBCIInterface, OpenBCIConfig

# Configure for real hardware
config = OpenBCIConfig(
    sample_rate=250.0,
    num_channels=8,
    notch_filter=60.0,  # US line frequency
)

# Connect to hardware (requires brainflow)
bci = OpenBCIInterface(
    config=config,
    port='/dev/ttyUSB0',  # Adjust for your system
    mock_mode=False
)

bci.start_stream()
# ... use as above
```

### Closed-Loop Brain-Heart Coupling

```python
from src.bci import NeuralToBrainModelBridge, BCIBridgeConfig, OpenBCIConfig
from src.coupling import CouplingParameters

# Configure BCI
bci_config = OpenBCIConfig(sample_rate=250.0, num_channels=8)

# Configure bridge
bridge_config = BCIBridgeConfig(
    bci_type='openbci',
    neural_drive_method='alpha_beta_ratio',
    gain=0.5,
)

# Configure coupling
coupling_params = CouplingParameters(
    neural_to_cardiac_gain=0.4,
    cardiac_to_neural_gain=0.2,
    neural_delay=0.120,  # 120 ms
)

# Create bridge
bridge = NeuralToBrainModelBridge(
    bci_config=bci_config,
    bridge_config=bridge_config,
    coupling_params=coupling_params,
    mock_mode=True,
)

# Run closed-loop simulation
bridge.start()
times, states, drives = bridge.run_closed_loop_simulation(
    duration=30.0,
    dt=0.01,
)
bridge.stop()
bridge.close()
```

## Examples

See `examples/bci/` for complete demonstrations:

- `demo_openbci_heart_brain.py`: OpenBCI integration with heart-brain model
- `demo_neuralink_adaptive_control.py`: Adaptive control with Lyapunov monitoring

## Architecture

```
BCI Hardware → Interface Module → Signal Processor → Neural Bridge → Coupling Model
                                                                          ↓
                                                                    FitzHugh-Nagumo
                                                                    Van der Pol
```

## Module Structure

```
src/bci/
├── __init__.py                 # Public API
├── openbci_interface.py        # OpenBCI hardware interface
├── neuralink_adapter.py        # Neuralink-style interface
├── signal_processor.py         # Signal processing utilities
├── neural_bridge.py            # BCI-to-model bridge
└── README.md                   # This file
```

## Neural Drive Extraction

Several methods are available for extracting control signals from BCI data:

### OpenBCI (EEG)

- **`alpha_beta_ratio`**: α/(α+β) power ratio (relaxation vs. arousal)
- **`alpha_power`**: Raw alpha band (8-12 Hz) power
- **`raw`**: Raw EEG amplitude

### Neuralink (Spikes)

- **`firing_rate`**: Population firing rate (spikes/second)
- **`theta_power`**: LFP theta band (4-8 Hz) power
- **`beta_power`**: LFP beta band (13-30 Hz) power
- **`gamma_power`**: LFP gamma band (30-100 Hz) power

## Integration with Adaptive Control

The neural bridge supports Lyapunov-based adaptive control:

```python
# Compute Lyapunov function
V = e^T P e + θ̃^T Γ^{-1} θ̃

# Adaptive parameter update
dθ̂/dt = Γ φ(x,t) e^T P B

# Stability: V̇ ≤ 0 under PE condition
```

See `docs/thesis/` for complete mathematical derivations.

## Safety Considerations

- **Projection**: Parameter estimates constrained to safe bounds
- **Saturation**: Control signals clipped to maximum amplitude
- **Monitoring**: Real-time Lyapunov function monitoring for stability
- **Deadzone**: Robustness to measurement noise

## References

- **OpenBCI**: https://openbci.com/
- **Neuralink**: https://neuralink.com/
- **BrainFlow**: https://brainflow.org/

## License

MIT License (see repository root)

## Citation

If you use this module in your research, please cite:

```bibtex
@software{multi_heart_model_bci,
  title={Brain-Computer Interface Integration for Heart-Brain Coupling Models},
  author={Multi-Heart-Model Team},
  year={2025},
  url={https://github.com/STLNFTART/Multi-Heart-Model}
}
```

## Contact

For questions or issues, please open an issue on GitHub or consult the documentation in `docs/`.
