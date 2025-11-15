# Multi-Heart-Model Web Control Panel

**Real-time BCI Integration, Visualization, and Control System**

## Overview

The Web Control Panel provides a comprehensive interface for:
- **BCI Data Acquisition**: Integration with OpenBCI, LSL, and other BCI hardware
- **Real-time Simulation**: Live HBCM heart-brain coupling simulations
- **Interactive Visualization**: matplotlib, Plotly, and 3D rendering
- **Automated Documentation**: LaTeX report generation
- **Remote Control**: REST API and WebSocket interfaces

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      BCI Hardware                             │
│  OpenBCI / LSL / Synthetic → Adapters → Circular Buffers    │
└───────────────┬──────────────────────────────────────────────┘
                │
                ↓
┌──────────────────────────────────────────────────────────────┐
│              Multi-Heart-Model Core (HBCM)                   │
│  Neural (FitzHugh) ↔ Cardiac (Van der Pol) ↔ Organ Chip    │
└───────────────┬──────────────────────────────────────────────┘
                │
                ↓
┌──────────────────────────────────────────────────────────────┐
│            Web Control Panel (FastAPI + WebSocket)           │
│  REST API | Real-time Data Stream | System Control          │
└───────────────┬──────────────────────────────────────────────┘
                │
                ↓
┌──────────────────────────────────────────────────────────────┐
│              Visualization & Documentation                    │
│  matplotlib | Plotly | 3D (VTK) | LaTeX Reports             │
└──────────────────────────────────────────────────────────────┘
```

## Installation

### 1. Core Dependencies

```bash
# Install Python dependencies
pip install -r requirements_web_panel.txt
```

### 2. Optional: BCI Hardware Support

**For OpenBCI hardware:**
```bash
pip install brainflow  # Recommended (supports all OpenBCI boards)
# OR
pip install pyOpenBCI  # Direct OpenBCI interface
```

**For LSL streaming:**
```bash
pip install pylsl
```

### 3. Optional: 3D Visualization

```bash
pip install pyvista
# For advanced features:
# conda install -c conda-forge mayavi
```

### 4. Optional: LaTeX Documentation

**Ubuntu/Debian:**
```bash
sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended
```

**macOS:**
```bash
brew install --cask mactex
```

**Windows:**
Download and install [MiKTeX](https://miktex.org/download)

## Quick Start

### 1. Run Demo

```bash
# Complete demonstration of all features
python examples/web_control_panel_demo.py
```

This will demonstrate:
- BCI data acquisition
- LSL streaming
- HBCM simulation with BCI integration
- Visualization generation
- LaTeX documentation

### 2. Start Web Server

```bash
# Start FastAPI backend
python web_control_panel/backend/main.py

# Or with custom settings
uvicorn web_control_panel.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at: `http://localhost:8000`

### 3. API Documentation

Once the server is running, access interactive API docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Reference

### REST Endpoints

#### System Status
```http
GET /api/status
```

Returns current system state, BCI connection status, and metrics.

**Response:**
```json
{
  "is_running": true,
  "simulation_time": 10.5,
  "bci_connected": true,
  "bci_streaming": true,
  "n_active_websockets": 2,
  "uptime_seconds": 3600.0,
  "last_update": "2025-11-15T10:30:00"
}
```

#### Configure Simulation
```http
POST /api/config/simulation
Content-Type: application/json

{
  "initial_state": [0.0, 0.0, 1.0, 0.0],
  "t_start": 0.0,
  "t_end": 120.0,
  "dt": 0.001,
  "neural_params": {
    "a": 0.7,
    "b": 0.8,
    "c": 3.0,
    "stimulus_amplitude": 0.5
  },
  "cardiac_params": {
    "mu": 1.5,
    "omega": 1.0,
    "damping": 0.1
  },
  "coupling_params": {
    "neural_to_cardiac_gain": 0.5,
    "cardiac_to_neural_gain": 0.3,
    "neural_to_cardiac_delay": 0.12,
    "cardiac_to_neural_delay": 0.15
  }
}
```

#### Configure BCI
```http
POST /api/config/bci
Content-Type: application/json

{
  "adapter_type": "openbci",
  "port": "/dev/ttyUSB0",
  "board_type": "cyton",
  "n_channels": 8,
  "sampling_rate": 250.0,
  "enable_lsl": true,
  "stream_name": "MultiHeartModel_BCI"
}
```

For synthetic testing:
```json
{
  "adapter_type": "synthetic",
  "n_channels": 8,
  "sampling_rate": 250.0,
  "enable_lsl": false
}
```

#### Control Commands
```http
POST /api/control
Content-Type: application/json

{
  "command": "start"  // start, stop, pause, resume, reset
}
```

#### Get Latest Data
```http
GET /api/data/latest?n_points=1000
```

Returns most recent simulation data points.

#### Export Data
```http
GET /api/data/export?format=json  // or format=csv
```

### WebSocket Interface

Connect to real-time data stream:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client_id_123');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'data_update') {
    const data = message.data;
    // data.time: array of timestamps
    // data.neural.v: neural voltage
    // data.neural.w: neural recovery
    // data.cardiac.x: cardiac position
    // data.cardiac.y: cardiac velocity

    updateVisualization(data);
  }
};

// Send control commands
ws.send(JSON.stringify({
  type: 'control',
  command: 'start'
}));
```

## BCI Integration Guide

### Top 10 Integrated Repositories

1. **OpenBCI** (`OpenBCI/OpenBCI_Python`)
   - Direct hardware interface
   - Ganglion, Cyton, Daisy support

2. **BrainFlow** (`brainflow-dev/brainflow`)
   - Universal BCI board interface
   - Multi-language support

3. **MNE-Python** (`mne-tools/mne-python`)
   - Signal processing and analysis
   - Industry standard for neurophysiology

4. **Lab Streaming Layer** (`sccn/liblsl`)
   - Real-time multi-device streaming
   - Network synchronization

5. **PyRiemann** (`pyRiemann/pyRiemann`)
   - Riemannian geometry for BCI
   - Advanced feature extraction

6. **NeuroDSP** (`neurodsp-tools/neurodsp`)
   - Time series analysis
   - Oscillation detection

7. **NeuroKit2** (`neuropsychology/NeuroKit`)
   - Multi-modal physiological signals
   - ECG, EEG, RSP integration

8. **MOABB** (`NeuroTechX/moabb`)
   - BCI benchmarking
   - Standardized datasets

9. **EEGNet** (`vlawhern/arl-eegmodels`)
   - Deep learning for EEG
   - CNN-based classification

10. **Bcipy** (`CAMBI-tech/bcipy`)
    - Real-time BCI experiments
    - P300 and SSVEP paradigms

### Example: OpenBCI Integration

```python
from bci_integration.data_acquisition import OpenBCIAdapter
from bci_integration.streaming import LSLBridge

# Create adapter
adapter = OpenBCIAdapter(
    port='/dev/ttyUSB0',  # or 'COM3' on Windows
    board_type='cyton'
)

# Connect
adapter.connect()

# Set up LSL bridge
bridge = LSLBridge(adapter, stream_name="OpenBCI_Stream")
bridge.start()

# Start streaming
adapter.start_stream()

# Register callback for real-time processing
def process_data(packet):
    print(f"Received {packet.n_samples} samples from {packet.n_channels} channels")
    # Your processing here

adapter.register_callback(process_data)
```

### Example: Synthetic Testing

```python
from bci_integration.data_acquisition import SyntheticAdapter

# Create synthetic EEG adapter
adapter = SyntheticAdapter(
    n_channels=8,
    sampling_rate=250.0,
    signal_type="eeg"
)

adapter.connect()
adapter.start_stream()

# Get data
packet = adapter.get_latest_data(timeout=1.0)
print(f"Data shape: {packet.data.shape}")  # (8 channels, n_samples)
```

## Visualization Examples

### matplotlib Real-time Plotting

```python
from web_control_panel.visualization.realtime_plotter import RealtimePlotter

# Create plotter
plotter = RealtimePlotter(figsize=(12, 8))

# Update with simulation data
plotter.update(times, neural, cardiac)

# Save to file
plotter.fig.savefig('results.png', dpi=150)

# Get base64 for web display
img_base64 = plotter.get_base64_image()
```

### Interactive Plotly Visualization

```python
from web_control_panel.visualization.realtime_plotter import PlotlyVisualizer
import plotly.graph_objects as go

# Create interactive plot
fig_dict = PlotlyVisualizer.create_interactive_plot(times, neural, cardiac)
fig = go.Figure(fig_dict)

# Save as HTML
fig.write_html('interactive_plot.html')

# Display in Jupyter
fig.show()
```

### 3D Trajectory Visualization

```python
from web_control_panel.visualization.realtime_plotter import Visualizer3D

# Create 3D plot
fig_3d = Visualizer3D.create_plotly_3d_surface(neural, cardiac, times)

# Save
fig = go.Figure(fig_3d)
fig.write_html('3d_trajectory.html')
```

### VTK High-Quality Rendering

```python
# Requires pyvista
html_vtk = Visualizer3D.create_3d_trajectory_vtk(neural, cardiac, times)
```

## LaTeX Documentation

### Automatic Report Generation

```python
from web_control_panel.documentation.latex_generator import LaTeXDocumentGenerator

# Prepare simulation data
simulation_data = {
    'simulation_duration': 120.0,
    'n_samples': 120000,
    'configuration': {
        'neural_params': {...},
        'cardiac_params': {...},
        'coupling_params': {...}
    },
    'results': {
        'neural_statistics': {...},
        'cardiac_statistics': {...}
    }
}

# Generate report
generator = LaTeXDocumentGenerator(output_dir="reports")
pdf_path = generator.generate_full_report(simulation_data, bci_data)

print(f"PDF generated: {pdf_path}")
```

### Manual Compilation

```bash
cd reports
pdflatex report_20251115_103000.tex
pdflatex report_20251115_103000.tex  # Run twice for references
```

## Advanced Usage

### Custom BCI Adapter

Create your own adapter by inheriting from `BCIAdapterBase`:

```python
from bci_integration.data_acquisition import BCIAdapterBase, BCIDataPacket, SignalType
import numpy as np

class MyCustomAdapter(BCIAdapterBase):
    def connect(self) -> bool:
        # Initialize hardware
        return True

    def disconnect(self) -> bool:
        # Cleanup
        return True

    def start_stream(self) -> bool:
        # Start data acquisition
        self._is_streaming = True
        return True

    def stop_stream(self) -> bool:
        # Stop acquisition
        self._is_streaming = False
        return True

    def _acquire_data(self) -> BCIDataPacket:
        # Get data from hardware
        data = np.random.randn(8, 100)  # 8 channels, 100 samples

        return BCIDataPacket(
            timestamp=time.time(),
            signal_type=SignalType.EEG,
            channels=['CH1', 'CH2', ...],
            data=data,
            sampling_rate=250.0
        )

    def get_channel_info(self) -> dict:
        return {
            'n_channels': 8,
            'sampling_rate': 250.0,
            'signal_type': 'EEG'
        }
```

### Bi-directional Data Flow

```python
# BCI → HBCM → Control Output

# 1. Get BCI data
packet = bci_adapter.get_latest_data()

# 2. Process and inject into HBCM
bci_signal = np.mean(packet.data, axis=0)  # Average across channels
external_input = bci_signal / 1000.0  # Scale appropriately

# 3. Step HBCM with BCI input
current_state = hbcm.step(t, current_state, dt, external_input)

# 4. Extract control signals
from src.microprocessor import PrimalLogicProcessor
processor = PrimalLogicProcessor()
control_signal = processor.compute_control(
    setpoint=0.0,
    measurement=current_state[0],  # Neural voltage
    dt=dt
)

# 5. Send to hardware
# motorhand_bridge.send_control(control_signal)
```

## Performance Considerations

### Latency Optimization

- **Target**: <50ms end-to-end latency
- Use circular buffers for efficient data management
- Minimize processing in critical paths
- Use async operations for I/O

### Throughput

- Supports 1000+ samples/second multi-channel
- LSL streaming handles network distribution
- WebSocket broadcasts to multiple clients

### Memory Management

- Circular buffers with fixed sizes
- Automatic old data cleanup
- Configurable buffer durations

## Production Deployment

### Security

```python
# Add authentication to FastAPI
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.get("/api/secure-endpoint")
async def secure_endpoint(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Verify JWT token
    pass
```

### HTTPS

```bash
uvicorn web_control_panel.backend.main:app \
    --host 0.0.0.0 \
    --port 443 \
    --ssl-keyfile=/path/to/key.pem \
    --ssl-certfile=/path/to/cert.pem
```

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements_web_panel.txt .
RUN pip install -r requirements_web_panel.txt

COPY . .
CMD ["uvicorn", "web_control_panel.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### BCI Connection Issues

**Problem**: Cannot connect to OpenBCI board

**Solution**:
```bash
# Check serial port permissions (Linux)
sudo usermod -a -G dialout $USER
# Log out and log back in

# List available ports
python -c "from serial.tools import list_ports; print([p.device for p in list_ports.comports()])"
```

### LSL Streams Not Found

**Problem**: Cannot find LSL streams

**Solution**:
- Check firewall settings (allow UDP port 16571)
- Verify stream is running: `python -c "from pylsl import resolve_streams; print(resolve_streams())"`

### LaTeX Compilation Fails

**Problem**: pdflatex errors

**Solution**:
- Install missing packages: `tlmgr install <package>`
- Check `.log` file for specific errors
- Compile manually to see full output

## Repository Links

### Core BCI Frameworks
- OpenBCI: https://github.com/OpenBCI/OpenBCI_Python
- BrainFlow: https://github.com/brainflow-dev/brainflow
- MNE-Python: https://github.com/mne-tools/mne-python
- LSL: https://github.com/sccn/liblsl

### Signal Processing
- PyRiemann: https://github.com/pyRiemann/pyRiemann
- NeuroDSP: https://github.com/neurodsp-tools/neurodsp
- NeuroKit2: https://github.com/neuropsychology/NeuroKit

### Machine Learning
- MOABB: https://github.com/NeuroTechX/moabb
- EEGNet: https://github.com/vlawhern/arl-eegmodels
- Bcipy: https://github.com/CAMBI-tech/bcipy

## Support

- **Documentation**: See `docs/BCI_INTEGRATION_PLAN.md`
- **Issues**: https://github.com/STLNFTART/Multi-Heart-Model/issues
- **Examples**: `examples/web_control_panel_demo.py`

## License

MIT License - See LICENSE file for details

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{multi_heart_model_2025,
  title={Multi-Heart-Model: Heart-Brain Coupling with BCI Integration},
  author={Multi-Heart-Model Contributors},
  year={2025},
  url={https://github.com/STLNFTART/Multi-Heart-Model}
}
```
