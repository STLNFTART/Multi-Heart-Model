# Node-RED and Node.js Integration Architecture

**Last Updated:** 2025-11-15
**Status:** Proposal/Design Document
**Author:** AI Assistant (Claude)

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Integration Architecture Overview](#integration-architecture-overview)
3. [Node-RED Use Cases](#node-red-use-cases)
4. [Node.js Service Layer](#nodejs-service-layer)
5. [OpenSim Integration Hooks](#opensim-integration-hooks)
6. [Implementation Roadmap](#implementation-roadmap)
7. [Example Flows](#example-flows)

---

## Executive Summary

### Current State

The Multi-Heart-Model has a **production-ready FastAPI backend** with:
- REST API endpoints (`/api/*`)
- WebSocket streaming (`/ws/{client_id}`)
- BCI integration via LSL
- Hardware interfaces (Primal Logic, MotorHandPro)

### Proposed Addition: Node-RED + Node.js

**Node-RED** serves as the **visual orchestration layer**:
- IoT/sensor aggregation (MQTT, TCP, UDP, serial, HTTP, WebSockets)
- Event routing and transformation
- Dashboard and alerting
- Workflow automation
- **NOT** part of the simulation loop

**Node.js** provides **peripheral services**:
- Authentication/authorization
- Historical data storage (MongoDB/InfluxDB)
- OpenSim biomechanical bridge
- API gateway and rate limiting
- Production monitoring

**Core Principle:** Keep Python/FastAPI as the simulation engine brain; use Node.js/Node-RED as the nervous system.

---

## Integration Architecture Overview

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│  Node-RED Dashboard | React Frontend | Grafana | TAK Client     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/WebSocket/MQTT
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                            │
│                        Node-RED                                  │
├─────────────────────────────────────────────────────────────────┤
│  [MQTT In] → [Transform] → [HTTP Request] → [Dashboard]         │
│  [Schedule] → [Loop Configs] → [POST /heart/run] → [Log DB]    │
│  [Webhook] → [Validate] → [Call API] → [TAK Alert]             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                             │
│                   Node.js Express/Fastify                        │
├─────────────────────────────────────────────────────────────────┤
│  - JWT Authentication                                            │
│  - Rate Limiting                                                 │
│  - Request Logging                                               │
│  - Reverse Proxy to FastAPI                                     │
│  - Historical Data API (MongoDB)                                 │
│  - OpenSim Bridge Service                                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────────┐
│                   SIMULATION ENGINE                              │
│                   FastAPI (Python)                               │
├─────────────────────────────────────────────────────────────────┤
│  - HBCM Simulation (/api/control, /api/config/simulation)      │
│  - BCI Integration (/api/config/bci)                            │
│  - Real-time WebSocket Streaming (/ws/{client_id})              │
│  - Data Export (/api/data/export)                               │
└───┬─────────────────┬──────────────┬──────────────┬─────────────┘
    │                 │              │              │
    ↓                 ↓              ↓              ↓
┌────────┐   ┌────────────┐   ┌──────────┐   ┌────────────┐
│  LSL   │   │ Primal     │   │ Motor    │   │ Organ      │
│ Network│   │ Logic      │   │ HandPro  │   │ Chip       │
│ (BCI)  │   │ Processor  │   │ (Hardware)│   │ Suite      │
└────────┘   └────────────┘   └──────────┘   └────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  EXTERNAL INTEGRATIONS                           │
│             Node.js OpenSim Bridge                               │
├─────────────────────────────────────────────────────────────────┤
│  - Cardiac force extraction from HBCM                            │
│  - OpenSim CLI/REST API wrapper                                 │
│  - Biomechanical simulation orchestration                       │
│  - Result parsing and feedback to HBCM                          │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Example: TAK Sensor Event → Simulation → Alert

```
┌──────────────┐
│  TAK Sensor  │
│  (Field Unit)│
└───────┬──────┘
        │ MQTT publish (topic: sensors/vitals)
        ↓
┌─────────────────────────────────────────────┐
│           Node-RED Flow                      │
├─────────────────────────────────────────────┤
│ [MQTT In: sensors/vitals]                   │
│     ↓ (msg.payload = {hr: 120, bp: 140/90}) │
│ [Function: Transform to HBCM format]        │
│     ↓ (msg.payload = {config: {...}})       │
│ [HTTP Request: POST /api/config/simulation] │
│     ↓ (start simulation)                    │
│ [HTTP Request: POST /api/control]           │
│     ↓ {"command": "start"}                  │
│ [WebSocket: ws://localhost:8000/ws/nodered] │
│     ↓ (receive real-time data)              │
│ [Switch: Check phase_drift_ms > threshold]  │
│     ↓ (if threshold exceeded)               │
│ ├─ [HTTP: POST to TAK server]               │
│ ├─ [Email: Alert medical team]              │
│ └─ [MongoDB: Store alert event]             │
└─────────────────────────────────────────────┘
```

---

## Node-RED Use Cases

### 1. Scheduled Simulation Sweeps

**Use Case:** Run parameter sweeps every hour to test model robustness

**Node-RED Flow:**
```
[Inject: cron "0 * * * *"]
    → [Function: Generate 5 configs]
    → [Split]
    → [HTTP Request: POST /api/config/simulation]
    → [HTTP Request: POST /api/control {"command":"start"}]
    → [Delay: 60s per sim]
    → [HTTP Request: GET /api/data/latest]
    → [Join]
    → [Function: Aggregate summaries]
    → [MongoDB: Store results]
    → [Dashboard: Display summary table]
```

**Implementation (Node-RED function node):**
```javascript
// Generate parameter sweep configs
const configs = [];
const mu_values = [1.0, 1.5, 2.0, 2.5, 3.0];

mu_values.forEach(mu => {
    configs.push({
        initial_state: [0.0, 0.0, 1.0, 0.0],
        t_start: 0.0,
        t_end: 60.0,
        dt: 0.001,
        cardiac_params: { mu: mu, omega: 1.0 },
        neural_params: { a: 0.7, b: 0.8, c: 3.0 }
    });
});

return configs.map(c => ({ payload: c }));
```

### 2. External Sensor Aggregation

**Use Case:** Collect data from multiple medical IoT devices

**Protocols Supported:**
- **MQTT**: Wearables, vital sign monitors
- **Serial**: Arduino sensors, ECG devices
- **HTTP**: REST APIs from hospital systems
- **WebSocket**: Real-time streaming devices
- **OPC-UA**: Industrial medical equipment

**Node-RED Flow:**
```
[MQTT In: medical/ecg]      ┐
[MQTT In: medical/bp]       ├─→ [Join: by time window]
[Serial In: /dev/ttyUSB0]   │       ↓
[HTTP Polling: vitals API]  ┘   [Function: Normalize formats]
                                    ↓
                        [HTTP: POST /api/config/bci]
                        (send aggregated sensor data as BCI input)
                                    ↓
                        [WebSocket: ws://localhost:8000/ws/sensors]
                        (receive simulation feedback)
                                    ↓
                        [Dashboard: Real-time monitoring]
```

**Example MQTT Transform:**
```javascript
// Node-RED function: Transform MQTT payload
const ecg_data = msg.payload;

// Convert to HBCM-compatible BCI packet format
const bci_packet = {
    adapter_type: "lsl",
    n_channels: 8,
    sampling_rate: 250.0,
    data: {
        timestamp: Date.now() / 1000,
        channels: ecg_data.leads  // 12-lead ECG → 8 channels
    }
};

msg.payload = bci_packet;
return msg;
```

### 3. Conditional Alerting

**Use Case:** Monitor simulation outputs and trigger alerts

**Node-RED Flow:**
```
[WebSocket In: ws://localhost:8000/ws/monitor]
    ↓ (real-time simulation data)
[Function: Extract metrics]
    ↓ (msg.payload = {phase_drift_ms, max_P_lv, comfort_index})
[Switch: Route by conditions]
    ├─ [phase_drift > 50ms]  → [TAK Alert: High drift warning]
    ├─ [max_P_lv > 180]      → [Email: Hypertension risk]
    ├─ [comfort_index < 0.3] → [SMS: Low comfort alert]
    └─ [else]                → [InfluxDB: Normal logging]
```

**Condition Function:**
```javascript
// Extract and evaluate simulation metrics
const data = msg.payload.data;

const metrics = {
    phase_drift_ms: calculatePhaseDrift(data.neural, data.cardiac),
    max_P_lv: Math.max(...data.cardiac.x),  // Peak cardiac pressure
    comfort_index: data.current_state.comfort_index
};

// Set alert level
if (metrics.phase_drift_ms > 50) {
    msg.alert_level = "critical";
    msg.topic = "tak/alerts/critical";
} else if (metrics.max_P_lv > 180) {
    msg.alert_level = "warning";
    msg.topic = "email/medical_team";
} else {
    msg.alert_level = "info";
    msg.topic = "influxdb/normal";
}

msg.payload = metrics;
return msg;
```

### 4. TAK Integration (Tactical Awareness Kit)

**Use Case:** Feed simulation results into military/emergency response systems

**Architecture:**
```
┌─────────────────────────────────────────────┐
│         Tactical Field Unit                  │
│  - Soldier vital signs (ECG, BP, SpO2)      │
└────────────┬────────────────────────────────┘
             │ MQTT/CoT (Cursor on Target)
┌─────────────────────────────────────────────┐
│            Node-RED Gateway                  │
├─────────────────────────────────────────────┤
│ [MQTT In: tak/vitals/#]                     │
│     ↓                                       │
│ [Function: Parse CoT XML]                   │
│     ↓                                       │
│ [HTTP: POST /api/config/simulation]         │
│ (run cardiac risk assessment)               │
│     ↓                                       │
│ [WebSocket: Monitor results]                │
│     ↓                                       │
│ [Function: Create CoT event]                │
│     ↓                                       │
│ [MQTT Out: tak/alerts/medical]              │
│ (send alert back to TAK server)             │
└─────────────────────────────────────────────┘
```

**CoT Event Generation:**
```javascript
// Node-RED function: Generate TAK CoT XML
const metrics = msg.payload;

const cot_event = `<?xml version="1.0"?>
<event version="2.0" uid="${msg.soldier_id}_medical_alert"
       type="b-m-p-s-p-loc" time="${new Date().toISOString()}"
       start="${new Date().toISOString()}"
       stale="${new Date(Date.now() + 300000).toISOString()}">
  <point lat="${msg.lat}" lon="${msg.lon}" hae="0.0" ce="10.0" le="10.0"/>
  <detail>
    <contact callsign="${msg.callsign}"/>
    <medical>
      <status>ALERT</status>
      <priority>IMMEDIATE</priority>
      <cardiac_risk>
        <phase_drift_ms>${metrics.phase_drift_ms}</phase_drift_ms>
        <max_pressure>${metrics.max_P_lv}</max_pressure>
        <comfort_index>${metrics.comfort_index}</comfort_index>
      </cardiac_risk>
    </medical>
  </detail>
</event>`;

msg.payload = cot_event;
return msg;
```

### 5. Dashboard and Visualization

**Node-RED Dashboard Nodes:**
```
[WebSocket In: ws://localhost:8000/ws/dashboard]
    ↓
    ├─→ [Gauge: Heart Rate] (cardiac frequency)
    ├─→ [Gauge: Neural Activity] (v-variable)
    ├─→ [Chart: Time Series] (neural + cardiac overlay)
    ├─→ [Chart: Phase Portrait] (v vs w, x vs y)
    ├─→ [Text: Status] (simulation state)
    ├─→ [Button: Start/Stop/Reset]
    └─→ [Table: Biomarkers] (comfort, phase drift, etc.)
```

**Dashboard URL:** `http://localhost:1880/ui`

---

## Node.js Service Layer

### 1. Express.js API Gateway

**Purpose:** Authentication, rate limiting, reverse proxy

**File Structure:**
```
nodejs_gateway/
├── package.json
├── server.js
├── routes/
│   ├── auth.js
│   ├── simulations.js
│   └── opensim.js
├── middleware/
│   ├── authenticate.js
│   └── ratelimit.js
├── models/
│   ├── User.js
│   └── Simulation.js
└── services/
    ├── opensimBridge.js
    └── influxdbClient.js
```

**Implementation (server.js):**
```javascript
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');

const app = express();
app.use(express.json());

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000,  // 15 minutes
    max: 100  // 100 requests per window
});
app.use('/api', limiter);

// JWT Authentication Middleware
function authenticate(req, res, next) {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) return res.status(401).json({ error: 'No token' });

    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        req.user = decoded;
        next();
    } catch (err) {
        res.status(403).json({ error: 'Invalid token' });
    }
}

// Reverse proxy to FastAPI
app.use('/api/hbcm', authenticate, createProxyMiddleware({
    target: 'http://localhost:8000',
    pathRewrite: { '^/api/hbcm': '/api' },
    onProxyReq: (proxyReq, req) => {
        proxyReq.setHeader('X-User-ID', req.user.userId);
        proxyReq.setHeader('X-User-Email', req.user.email);
    },
    onProxyRes: (proxyRes, req, res) => {
        // Log requests
        console.log(`${req.user.email} - ${req.method} ${req.path}`);
    }
}));

// Historical data API
const mongoose = require('mongoose');
const Simulation = require('./models/Simulation');

app.get('/api/simulations', authenticate, async (req, res) => {
    const { startDate, endDate, limit = 100 } = req.query;

    const query = { userId: req.user.userId };
    if (startDate) query.timestamp = { $gte: new Date(startDate) };
    if (endDate) query.timestamp = { ...query.timestamp, $lte: new Date(endDate) };

    const simulations = await Simulation.find(query)
        .sort({ timestamp: -1 })
        .limit(parseInt(limit));

    res.json(simulations);
});

// OpenSim integration endpoint
const openSimBridge = require('./services/opensimBridge');

app.post('/api/opensim/run', authenticate, async (req, res) => {
    const { neural, cardiac, config } = req.body;

    try {
        // Convert HBCM output to OpenSim motion file
        const motionFile = await openSimBridge.generateMotion({
            neural, cardiac, config
        });

        // Run OpenSim forward dynamics
        const results = await openSimBridge.runForwardDynamics({
            motionFile,
            modelFile: config.opensimModel || 'default_model.osim',
            setupFile: config.setupFile || 'forward_dynamics_setup.xml'
        });

        // Parse and return kinematics
        const kinematics = await openSimBridge.parseResults(results.outputFile);

        res.json({
            success: true,
            motion_file: motionFile,
            kinematics: kinematics,
            forces: results.forces
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(3000, () => {
    console.log('Node.js Gateway running on port 3000');
});
```

### 2. WebSocket Bridge (FastAPI → Socket.io)

**Purpose:** Bridge FastAPI WebSocket to Socket.io for broader client support

**Implementation:**
```javascript
const io = require('socket.io')(server);
const WebSocket = require('ws');
const { Influx } = require('influx');

// InfluxDB client for time-series storage
const influx = new Influx.InfluxDB({
    host: 'localhost',
    database: 'hbcm',
    schema: [{
        measurement: 'simulation',
        fields: {
            neural_v: Influx.FieldType.FLOAT,
            neural_w: Influx.FieldType.FLOAT,
            cardiac_x: Influx.FieldType.FLOAT,
            cardiac_y: Influx.FieldType.FLOAT,
            comfort_index: Influx.FieldType.FLOAT
        },
        tags: ['user_id', 'simulation_id']
    }]
});

// Connect to FastAPI WebSocket
const fastapi_ws = new WebSocket('ws://localhost:8000/ws/nodejs-bridge');

fastapi_ws.on('open', () => {
    console.log('Connected to FastAPI WebSocket');
});

fastapi_ws.on('message', async (data) => {
    const message = JSON.parse(data);

    if (message.type === 'data_update') {
        const simData = message.data;

        // Broadcast to all Socket.io clients in simulation room
        io.to('simulation-room').emit('hbcm-update', simData);

        // Store in InfluxDB for historical analysis
        await influx.writePoints([{
            measurement: 'simulation',
            tags: {
                user_id: simData.user_id || 'unknown',
                simulation_id: simData.simulation_id || 'unknown'
            },
            fields: {
                neural_v: simData.neural.v[simData.neural.v.length - 1],
                neural_w: simData.neural.w[simData.neural.w.length - 1],
                cardiac_x: simData.cardiac.x[simData.cardiac.x.length - 1],
                cardiac_y: simData.cardiac.y[simData.cardiac.y.length - 1],
                comfort_index: simData.current_state.comfort_index
            },
            timestamp: new Date()
        }]);
    }
});

// Socket.io client connections
io.on('connection', (socket) => {
    console.log('Client connected:', socket.id);

    socket.on('join-simulation', (room) => {
        socket.join(room);
        console.log(`Client ${socket.id} joined ${room}`);
    });

    socket.on('control-command', (command) => {
        // Forward to FastAPI
        fastapi_ws.send(JSON.stringify({
            type: 'control',
            command: command
        }));
    });
});
```

---

## OpenSim Integration Hooks

### Overview

OpenSim is a biomechanical simulation platform for musculoskeletal modeling. Integration allows:
1. **Cardiac mechanics → Muscle activation patterns**
2. **Neural control → Motor unit recruitment**
3. **Closed-loop feedback** (biomechanical forces → cardiac load)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              HBCM Simulation (Python)                        │
│  - Neural model (FitzHugh-Nagumo)                           │
│  - Cardiac model (Van der Pol)                              │
│  - Coupling with delays                                     │
└──────────────────┬──────────────────────────────────────────┘
                   │ (cardiac state: x, y)
                   ↓
┌─────────────────────────────────────────────────────────────┐
│          Cardiac Force Extractor (Python)                   │
│  - Convert cardiac state to force profiles                  │
│  - Time-varying pressure → muscle activation                │
│  - Export .mot (OpenSim Motion) file                        │
└──────────────────┬──────────────────────────────────────────┘
                   │ (cardiac_forces.mot)
                   ↓
┌─────────────────────────────────────────────────────────────┐
│       Node.js OpenSim Bridge Service                        │
├─────────────────────────────────────────────────────────────┤
│  1. Receive HBCM simulation results (REST API)              │
│  2. Generate OpenSim motion file from cardiac data          │
│  3. Execute OpenSim CLI:                                    │
│     - Forward dynamics simulation                           │
│     - Inverse dynamics analysis                             │
│     - Muscle optimization                                   │
│  4. Parse OpenSim outputs (.sto, .mot files)                │
│  5. Return biomechanical results to HBCM                    │
└──────────────────┬──────────────────────────────────────────┘
                   │ (joint angles, muscle forces, contact)
                   ↓
┌─────────────────────────────────────────────────────────────┐
│              OpenSim (C++ executable)                       │
│  - Musculoskeletal model (.osim file)                       │
│  - Forward/inverse dynamics solver                          │
│  - Contact mechanics                                        │
│  - Muscle physiology (Hill-type models)                     │
└──────────────────┬──────────────────────────────────────────┘
                   │ (biomechanical loads)
                   ↓
┌─────────────────────────────────────────────────────────────┐
│         Feedback to HBCM (Optional)                         │
│  - Mechanical load → cardiac afterload adjustment           │
│  - Muscle activation → neural fatigue models                │
│  - Closed-loop physiological-biomechanical coupling         │
└─────────────────────────────────────────────────────────────┘
```

### Implementation: Python OpenSim Hook

**File:** `src/integration/opensim_hooks.py`

```python
"""
OpenSim integration hooks for Multi-Heart-Model.

Converts HBCM cardiac dynamics to OpenSim-compatible motion files
and orchestrates biomechanical simulations.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict
import numpy as np


@dataclass
class OpenSimConfig:
    """OpenSim integration configuration."""
    model_file: str = "models/gait2392.osim"  # OpenSim model
    motion_output: str = "results/cardiac_forces.mot"
    results_output: str = "results/biomechanics.sto"
    time_step: float = 0.01
    cardiac_to_muscle_mapping: Dict[str, str] = None


class CardiacForceExtractor:
    """Extract muscle activation patterns from cardiac dynamics."""

    def __init__(self, config: OpenSimConfig = None):
        self.config = config or OpenSimConfig()

    def cardiac_state_to_muscle_activation(
        self,
        cardiac_trajectory: List[Tuple[float, Tuple[float, float]]]
    ) -> np.ndarray:
        """
        Convert cardiac oscillator state to muscle activation patterns.

        Args:
            cardiac_trajectory: List of (time, (x, y)) from HBCM

        Returns:
            Array of shape (n_timesteps, n_muscles) with activation levels [0, 1]
        """
        times = np.array([t for t, _ in cardiac_trajectory])
        x_values = np.array([x for _, (x, y) in cardiac_trajectory])
        y_values = np.array([y for _, (x, y) in cardiac_trajectory])

        # Example mapping: cardiac pressure (x) → muscle activation
        # Normalize to [0, 1] range
        x_norm = (x_values - x_values.min()) / (x_values.max() - x_values.min())

        # Map to multiple muscles (simplified example)
        # In reality, this would be a complex biomechanical mapping
        n_muscles = 8  # Example: 8 leg muscles
        activations = np.zeros((len(times), n_muscles))

        # Distribute cardiac phase to different muscles
        for i in range(n_muscles):
            phase_shift = 2 * np.pi * i / n_muscles
            activations[:, i] = x_norm * np.cos(2 * np.pi * times / 1.0 + phase_shift)
            activations[:, i] = np.clip(activations[:, i], 0, 1)

        return activations

    def export_opensim_motion(
        self,
        times: np.ndarray,
        activations: np.ndarray,
        muscle_names: List[str] = None
    ) -> str:
        """
        Export muscle activations to OpenSim .mot format.

        Args:
            times: Time vector (seconds)
            activations: Array of shape (n_timesteps, n_muscles)
            muscle_names: List of muscle names (default: muscle_1, muscle_2, ...)

        Returns:
            Path to generated .mot file
        """
        if muscle_names is None:
            muscle_names = [f"muscle_{i+1}" for i in range(activations.shape[1])]

        with open(self.config.motion_output, 'w') as f:
            # Header
            f.write(f"Cardiac-Derived Muscle Activations\n")
            f.write(f"nRows={len(times)}\n")
            f.write(f"nColumns={len(muscle_names) + 1}\n")
            f.write(f"inDegrees=no\n")
            f.write(f"endheader\n")

            # Column names
            f.write("time\t" + "\t".join(muscle_names) + "\n")

            # Data
            for i, t in enumerate(times):
                row = [f"{t:.6f}"] + [f"{a:.6f}" for a in activations[i, :]]
                f.write("\t".join(row) + "\n")

        return self.config.motion_output


class OpenSimBridge:
    """Bridge between HBCM and OpenSim biomechanical simulation."""

    def __init__(self, config: OpenSimConfig = None):
        self.config = config or OpenSimConfig()
        self.extractor = CardiacForceExtractor(config)

    def run_forward_dynamics(
        self,
        motion_file: str,
        setup_file: str = "setup_forward_dynamics.xml"
    ) -> Dict:
        """
        Run OpenSim forward dynamics simulation.

        Args:
            motion_file: Path to .mot file with muscle activations
            setup_file: OpenSim forward dynamics setup XML

        Returns:
            Dictionary with results paths and summary statistics
        """
        import subprocess

        # Build OpenSim command
        # Note: Requires OpenSim installed with CLI tools
        cmd = [
            "opensim-cmd",
            "run-tool",
            setup_file,
            "-model", self.config.model_file,
            "-motion", motion_file,
            "-results", self.config.results_output
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"OpenSim failed: {result.stderr}")

            # Parse results
            kinematics = self._parse_sto_file(self.config.results_output)

            return {
                "success": True,
                "output_file": self.config.results_output,
                "kinematics": kinematics,
                "stdout": result.stdout
            }

        except subprocess.TimeoutExpired:
            raise RuntimeError("OpenSim simulation timed out")
        except FileNotFoundError:
            raise RuntimeError("OpenSim CLI not found. Is OpenSim installed?")

    def _parse_sto_file(self, sto_path: str) -> Dict[str, np.ndarray]:
        """
        Parse OpenSim .sto (storage) file.

        Returns:
            Dictionary mapping column names to arrays
        """
        data = {}
        header_complete = False

        with open(sto_path, 'r') as f:
            for line in f:
                if line.startswith('endheader'):
                    header_complete = True
                    continue

                if not header_complete:
                    continue

                # First line after header is column names
                if not data:
                    columns = line.strip().split('\t')
                    data = {col: [] for col in columns}
                    continue

                # Data lines
                values = [float(v) for v in line.strip().split('\t')]
                for col, val in zip(columns, values):
                    data[col].append(val)

        # Convert to numpy arrays
        return {col: np.array(vals) for col, vals in data.items()}

    def create_closed_loop_feedback(
        self,
        biomechanical_results: Dict
    ) -> Dict[str, float]:
        """
        Extract biomechanical loads to feed back into HBCM.

        Args:
            biomechanical_results: Parsed OpenSim results

        Returns:
            Feedback parameters (e.g., cardiac afterload adjustment)
        """
        # Example: Calculate mechanical work from joint powers
        joint_powers = biomechanical_results.get('joint_powers', {})

        # Sum absolute power across all joints
        total_power = sum(
            np.abs(powers).mean()
            for joint, powers in joint_powers.items()
        )

        # Convert to cardiac afterload (simplified)
        # Higher mechanical work → higher cardiac afterload
        afterload_adjustment = total_power / 100.0  # Normalize

        return {
            "cardiac_afterload_factor": 1.0 + afterload_adjustment,
            "total_mechanical_power": total_power,
            "peak_ground_reaction_force": biomechanical_results.get('GRF_peak', 0.0)
        }
```

### Implementation: Node.js OpenSim Service

**File:** `nodejs_gateway/services/opensimBridge.js`

```javascript
/**
 * OpenSim integration service for Multi-Heart-Model
 *
 * Provides REST API endpoints for:
 * - Generating OpenSim motion files from HBCM data
 * - Running OpenSim simulations via CLI
 * - Parsing and returning biomechanical results
 */

const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const { promisify } = require('util');
const execAsync = promisify(exec);

class OpenSimBridge {
    constructor(config = {}) {
        this.config = {
            opensimBin: config.opensimBin || 'opensim-cmd',
            modelsDir: config.modelsDir || '/opt/opensim/models',
            resultsDir: config.resultsDir || '/tmp/opensim_results',
            defaultModel: config.defaultModel || 'gait2392.osim',
            ...config
        };
    }

    /**
     * Generate OpenSim motion file from HBCM cardiac trajectory
     */
    async generateMotion({ neural, cardiac, config }) {
        const times = Array.from({ length: cardiac.x.length },
                                  (_, i) => i * (config.dt || 0.001));

        // Normalize cardiac x-values to [0, 1] activation range
        const x_values = cardiac.x;
        const x_min = Math.min(...x_values);
        const x_max = Math.max(...x_values);
        const x_norm = x_values.map(x => (x - x_min) / (x_max - x_min));

        // Map to multiple muscles (example: 8 muscles)
        const n_muscles = 8;
        const muscle_names = Array.from({ length: n_muscles },
                                        (_, i) => `muscle_${i + 1}`);

        // Generate phase-shifted activations
        const activations = times.map((t, tidx) => {
            const row = [t.toFixed(6)];
            for (let m = 0; m < n_muscles; m++) {
                const phase = 2 * Math.PI * m / n_muscles;
                const activation = x_norm[tidx] * Math.cos(2 * Math.PI * t / 1.0 + phase);
                row.push(Math.max(0, Math.min(1, activation)).toFixed(6));
            }
            return row.join('\t');
        });

        // Construct .mot file content
        const motContent = [
            'Cardiac-Derived Muscle Activations',
            `nRows=${times.length}`,
            `nColumns=${n_muscles + 1}`,
            'inDegrees=no',
            'endheader',
            ['time', ...muscle_names].join('\t'),
            ...activations
        ].join('\n');

        // Write to file
        const motFilePath = path.join(this.config.resultsDir,
                                      `cardiac_${Date.now()}.mot`);
        await fs.mkdir(this.config.resultsDir, { recursive: true });
        await fs.writeFile(motFilePath, motContent);

        return motFilePath;
    }

    /**
     * Run OpenSim forward dynamics simulation
     */
    async runForwardDynamics({ motionFile, modelFile, setupFile }) {
        const model = modelFile || path.join(this.config.modelsDir,
                                            this.config.defaultModel);
        const setup = setupFile || path.join(this.config.modelsDir,
                                            'forward_dynamics_setup.xml');
        const outputFile = path.join(this.config.resultsDir,
                                    `biomechanics_${Date.now()}.sto`);

        // Construct OpenSim command
        const cmd = [
            this.config.opensimBin,
            'run-tool',
            setup,
            '-model', model,
            '-motion', motionFile,
            '-results', outputFile
        ].join(' ');

        try {
            const { stdout, stderr } = await execAsync(cmd, { timeout: 300000 });

            return {
                success: true,
                outputFile,
                stdout,
                stderr,
                forces: await this.extractForces(outputFile)
            };
        } catch (error) {
            throw new Error(`OpenSim simulation failed: ${error.message}`);
        }
    }

    /**
     * Parse OpenSim .sto results file
     */
    async parseResults(stoFilePath) {
        const content = await fs.readFile(stoFilePath, 'utf-8');
        const lines = content.split('\n');

        let headerComplete = false;
        let columns = [];
        const data = {};

        for (const line of lines) {
            if (line.startsWith('endheader')) {
                headerComplete = true;
                continue;
            }

            if (!headerComplete) continue;

            // First line after header is column names
            if (columns.length === 0) {
                columns = line.trim().split(/\s+/);
                columns.forEach(col => data[col] = []);
                continue;
            }

            // Data lines
            const values = line.trim().split(/\s+/).map(parseFloat);
            columns.forEach((col, idx) => {
                if (values[idx] !== undefined) {
                    data[col].push(values[idx]);
                }
            });
        }

        return data;
    }

    /**
     * Extract force data from biomechanical results
     */
    async extractForces(resultsFile) {
        const data = await this.parseResults(resultsFile);

        // Calculate summary statistics
        const forces = {};
        for (const [key, values] of Object.entries(data)) {
            if (key.toLowerCase().includes('force') ||
                key.toLowerCase().includes('moment')) {
                forces[key] = {
                    mean: values.reduce((a, b) => a + b, 0) / values.length,
                    max: Math.max(...values),
                    min: Math.min(...values),
                    std: this._calculateStd(values)
                };
            }
        }

        return forces;
    }

    _calculateStd(values) {
        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        const variance = values.reduce((sum, val) =>
            sum + Math.pow(val - mean, 2), 0) / values.length;
        return Math.sqrt(variance);
    }
}

module.exports = OpenSimBridge;
```

---

## Implementation Roadmap

### Phase 1: Node-RED Basics (Week 1)

**Goals:**
- Install and configure Node-RED
- Connect to existing FastAPI backend
- Create basic dashboard

**Tasks:**
1. Install Node-RED: `npm install -g --unsafe-perm node-red`
2. Start Node-RED: `node-red`
3. Access editor: `http://localhost:1880`
4. Install dashboard: `npm install node-red-dashboard`
5. Create first flow:
   - WebSocket In node → Connect to `ws://localhost:8000/ws/nodered`
   - Function node → Extract neural.v and cardiac.x
   - Dashboard gauge nodes → Display values
   - Test real-time visualization

**Validation:**
- Start HBCM simulation via FastAPI
- Verify Node-RED dashboard updates in real-time
- Screenshot dashboard and save as documentation

### Phase 2: Node.js Gateway (Week 2)

**Goals:**
- Set up Express.js API gateway
- Implement JWT authentication
- Add reverse proxy to FastAPI

**Tasks:**
1. Create `nodejs_gateway/` directory
2. Initialize: `npm init -y`
3. Install dependencies:
   ```bash
   npm install express jsonwebtoken bcryptjs
   npm install http-proxy-middleware express-rate-limit
   npm install mongoose  # For MongoDB
   ```
4. Implement `server.js` (see implementation above)
5. Create User model and auth routes
6. Test:
   - POST `/auth/register` - Create user
   - POST `/auth/login` - Get JWT token
   - GET `/api/hbcm/status` - Proxied request with auth

**Validation:**
- Use Postman/curl to test auth flow
- Verify authenticated requests reach FastAPI
- Check logs show user attribution

### Phase 3: Database Integration (Week 3)

**Goals:**
- Store simulation results in MongoDB
- Set up InfluxDB for time-series data
- Create historical query API

**Tasks:**
1. Install MongoDB: `docker run -d -p 27017:27017 mongo`
2. Install InfluxDB: `docker run -d -p 8086:8086 influxdb`
3. Create Simulation model (Mongoose schema)
4. Implement WebSocket → Database pipeline
5. Add historical query endpoints:
   - GET `/api/simulations` - List user simulations
   - GET `/api/simulations/:id` - Get specific simulation
   - GET `/api/timeseries/query` - InfluxDB queries

**Validation:**
- Run simulation and verify data stored in MongoDB
- Query time-series data from InfluxDB
- Check data retention policies

### Phase 4: OpenSim Integration (Week 4-5)

**Goals:**
- Create Python OpenSim hooks
- Implement Node.js OpenSim bridge service
- Test end-to-end HBCM → OpenSim pipeline

**Tasks:**
1. Install OpenSim: `conda install -c opensim-org opensim`
2. Create `src/integration/opensim_hooks.py`
3. Implement `CardiacForceExtractor` class
4. Create `nodejs_gateway/services/opensimBridge.js`
5. Add REST endpoint: POST `/api/opensim/run`
6. Test workflow:
   - Run HBCM simulation
   - Export cardiac trajectory
   - Generate OpenSim motion file
   - Run OpenSim forward dynamics
   - Parse and return results

**Validation:**
- Visualize OpenSim motion file in OpenSim GUI
- Verify forward dynamics runs without errors
- Check biomechanical results make physiological sense

### Phase 5: Advanced Node-RED Flows (Week 6)

**Goals:**
- Create production workflows
- Implement alerting and automation
- Add TAK integration (if applicable)

**Tasks:**
1. Scheduled parameter sweeps:
   - Inject node with cron schedule
   - Loop through configs
   - Aggregate results
2. Conditional alerting:
   - Monitor WebSocket stream
   - Evaluate thresholds
   - Send email/SMS/webhook alerts
3. MQTT integration:
   - Install Mosquitto broker
   - Create MQTT publish/subscribe nodes
   - Bridge external sensors to HBCM
4. TAK integration (optional):
   - Parse CoT XML from TAK
   - Trigger simulations
   - Generate CoT alerts

**Validation:**
- Verify scheduled sweeps run automatically
- Test alert delivery (email/SMS)
- Confirm MQTT messages trigger simulations

### Phase 6: Production Deployment (Week 7)

**Goals:**
- Containerize all services
- Set up reverse proxy (NGINX)
- Configure monitoring and logging

**Tasks:**
1. Create Dockerfiles:
   - FastAPI backend
   - Node.js gateway
   - Node-RED
2. Create `docker-compose.yml`:
   ```yaml
   version: '3.8'
   services:
     fastapi:
       build: ./web_control_panel/backend
       ports: ["8000:8000"]
     nodejs:
       build: ./nodejs_gateway
       ports: ["3000:3000"]
     nodered:
       image: nodered/node-red
       ports: ["1880:1880"]
       volumes: ["./nodered_data:/data"]
     mongo:
       image: mongo
       ports: ["27017:27017"]
     influxdb:
       image: influxdb
       ports: ["8086:8086"]
     nginx:
       image: nginx
       ports: ["80:80", "443:443"]
       volumes: ["./nginx.conf:/etc/nginx/nginx.conf"]
   ```
3. Configure NGINX reverse proxy
4. Set up SSL/TLS certificates (Let's Encrypt)
5. Configure logging (ELK stack or similar)

**Validation:**
- Access all services through NGINX
- Verify HTTPS works
- Check logs aggregation

---

## Example Flows

### Example 1: Real-Time Cardiac Risk Assessment

**Scenario:** Monitor soldier vitals, run cardiac simulation, alert if high risk

**Node-RED Flow:**
```
[MQTT In: military/vitals/soldier123]
    ↓ { hr: 145, bp_sys: 165, spo2: 94 }
[Function: Check if high-risk parameters]
    ↓ if (hr > 140 || bp_sys > 160)
[HTTP Request: POST /api/hbcm/config/simulation]
    ↓ payload: { cardiac_params: { mu: 2.5, omega: 1.2 }, ... }
[HTTP Request: POST /api/hbcm/control]
    ↓ payload: { command: "start" }
[WebSocket: ws://localhost:8000/ws/risk-monitor]
    ↓ (stream results for 10 seconds)
[Function: Calculate risk score]
    ↓ risk_score = f(phase_drift, max_pressure, comfort_index)
[Switch: Route by risk level]
    ├─ [risk > 0.8] → [MQTT Out: tak/alerts/immediate]
    │                  [Email: Medical team]
    ├─ [risk > 0.5] → [MQTT Out: tak/alerts/warning]
    └─ [else]       → [MongoDB: Log normal assessment]
```

### Example 2: Automated Model Validation

**Scenario:** Daily parameter sweep to validate model stability

**Node-RED Flow:**
```
[Inject: cron "0 2 * * *"]  # 2 AM daily
    ↓
[Function: Generate validation configs]
    ↓ configs = [{mu: 1.0}, {mu: 1.5}, ..., {mu: 3.0}]
    ↓ return [array of 20 configs]
[Split: Process one at a time]
    ↓ (for each config)
[HTTP Request: POST /api/hbcm/config/simulation]
    ↓
[HTTP Request: POST /api/hbcm/control {"command":"start"}]
    ↓
[Delay: 60 seconds]  # Wait for simulation to run
    ↓
[HTTP Request: GET /api/hbcm/data/latest]
    ↓ simulation results
[Join: Combine all results]
    ↓ (after all 20 configs complete)
[Function: Calculate statistics]
    ↓ mean_comfort, std_phase_drift, convergence_rate, etc.
[Switch: Validation check]
    ├─ [all converged] → [Email: Daily validation passed]
    │                     [MongoDB: Store validation report]
    └─ [some failed]   → [Email: Alert developers with failures]
                         [GitHub: Create issue with failure details]
```

### Example 3: OpenSim Gait Analysis

**Scenario:** Generate walking gait from cardiac rhythm

**Node-RED Flow:**
```
[Inject: Manual trigger]
    ↓
[HTTP Request: POST /api/hbcm/config/simulation]
    ↓ payload: { t_end: 10.0, cardiac_params: { omega: 1.0 } }
[HTTP Request: POST /api/hbcm/control {"command":"start"}]
    ↓
[Delay: 11 seconds]  # Wait for 10s simulation + 1s buffer
    ↓
[HTTP Request: GET /api/hbcm/data/export?format=json]
    ↓ full trajectory: { times: [...], neural: {...}, cardiac: {...} }
[Function: Extract cardiac trajectory]
    ↓ payload = { neural: msg.payload.neural, cardiac: msg.payload.cardiac }
[HTTP Request: POST /api/opensim/run]
    ↓ Node.js service generates .mot and runs OpenSim
    ↓ returns: { kinematics: {...}, forces: {...} }
[Function: Parse kinematics]
    ↓ extract: hip_angle, knee_angle, ankle_angle, GRF
[Dashboard: Chart - Joint Angles over time]
[Dashboard: Table - Force summary statistics]
[MongoDB: Store biomechanical results]
```

---

## Summary

### Key Takeaways

1. **FastAPI (Python) remains the simulation engine**
   - Core HBCM logic
   - BCI integration
   - Real-time WebSocket streaming

2. **Node.js provides peripheral services**
   - Authentication/authorization
   - Historical data storage
   - OpenSim biomechanical bridge
   - API gateway layer

3. **Node-RED is the orchestration canvas**
   - Visual workflow editor
   - IoT device aggregation (MQTT, serial, HTTP, etc.)
   - Conditional alerting
   - Dashboard and visualization
   - **NOT** involved in simulation loop

4. **OpenSim hooks enable biomechanical coupling**
   - Cardiac dynamics → Muscle activation
   - Forward/inverse dynamics simulation
   - Biomechanical feedback → Cardiac load

### Mental Model

```
┌────────────────────────────────────────────┐
│    "Brain" (Python/FastAPI)                │
│    - Runs simulations                      │
│    - Computes models                       │
│    - Real-time streaming                   │
└───────────────┬────────────────────────────┘
                │
┌────────────────────────────────────────────┐
│    "Nervous System" (Node-RED)             │
│    - Connects everything                   │
│    - Routes events                         │
│    - Automation & alerting                 │
└───────────────┬────────────────────────────┘
                │
┌────────────────────────────────────────────┐
│    "Body" (Node.js Services)               │
│    - Authentication organs                 │
│    - Memory (databases)                    │
│    - External limbs (OpenSim, TAK)         │
└────────────────────────────────────────────┘
```

### Next Steps

1. Review this document and the implementation roadmap
2. Decide which phase to start with (recommend Phase 1: Node-RED basics)
3. Set up development environment
4. Implement first Node-RED flow connecting to existing FastAPI backend
5. Iterate and expand based on specific use case needs

---

**Questions or need clarification? This is a living document - update as the architecture evolves.**
