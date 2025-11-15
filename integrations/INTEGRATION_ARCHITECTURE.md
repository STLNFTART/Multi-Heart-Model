# Multi-Heart-Model Integration Architecture

**Event-Driven, Multi-Protocol System for Real-World Deployment**

## Overview

This architecture extends the Multi-Heart-Model with production-grade integration capabilities:

1. **OpenSim Biomechanical Co-Simulation** - Heart-brain-muscle coupling
2. **Node.js REST API** - Clean, stable service layer
3. **Node-RED Orchestration** - Visual workflow "mission control"
4. **MQTT Event Bus** - Asynchronous, decoupled messaging
5. **TAK Integration** - Tactical Awareness Kit for field deployment
6. **MCP Tools** - LLM-accessible simulation primitives

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                            │
│  Dashboards | TAK Clients | Web UI | MCP-enabled LLMs          │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────────────────┐
│              Orchestration Layer (Node-RED)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Cron    │  │ Webhooks │  │ Decision │  │  Alerts  │       │
│  │  Jobs    │  │  Routes  │  │  Rules   │  │  Engine  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────────────────┐
│                  Event Bus (MQTT)                                │
│  Topics: heart/*, bci/*, opensim/*, tak/*, alerts/*            │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────────────────┐
│               Service Layer (Node.js API)                        │
│  REST Endpoints | WebSocket | State Management | Python Bridge │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────────────────┐
│               Simulation Engines (Python)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │    HBCM     │  │   OpenSim   │  │     BCI     │            │
│  │ Neural-Card │  │ Biomechanics│  │  Adapters   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────────────────┐
│               Hardware / Data Sources                            │
│  Serial Devices | OpenBCI | Sensors | TAK Feeds | Lab Equipment│
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Layer 1: Simulation Engines (Python)

**What it does:**
- Solves ODEs (FitzHugh-Nagumo, Van der Pol)
- Runs OpenSim biomechanical co-simulations
- Processes BCI data streams
- Computes organ-on-chip dynamics

**What it does NOT do:**
- Handle HTTP requests (that's Node.js)
- Manage workflows (that's Node-RED)
- Store long-term data (that's databases)

**Files:**
- `src/coupling/hbcm.py` - Core heart-brain coupling
- `integrations/opensim/opensim_bridge.py` - OpenSim interface
- `bci_integration/` - BCI hardware adapters

---

### Layer 2: Service Layer (Node.js)

**What it does:**
- Exposes clean REST API for simulations
- Manages simulation job queue
- Bridges Python engines to web/MQTT
- Handles authentication and rate limiting
- Maintains WebSocket connections

**What it does NOT do:**
- Physics/math (delegates to Python)
- Complex workflows (delegates to Node-RED)
- Real-time control loops (too slow)

**Key Endpoints:**
- `POST /api/heart/run` - Run cardiac simulation
- `POST /api/opensim/cosimulate` - Heart-muscle co-simulation
- `GET /api/simulations/:id/status` - Check job status
- `POST /api/bci/stream` - Initiate BCI streaming

**Why Node.js?**
- Native async I/O for event-driven architecture
- Excellent MQTT/WebSocket support
- Easy to containerize and scale horizontally
- Wide ecosystem for hardware integration

**Install & Run:**
```bash
cd integrations/nodejs
npm install
npm start

# With environment variables
PORT=3000 ENABLE_MQTT=true npm start

# Docker
npm run docker:build
npm run docker:run
```

---

### Layer 3: Event Bus (MQTT)

**What it does:**
- Decouples components via pub/sub
- Enables asynchronous communication
- Buffers messages for offline clients
- Supports quality-of-service levels

**Topic Structure:**
```
heart/
  ├── simulation/result       # Completed simulation metrics
  ├── simulation/started       # Job initiated
  ├── simulation/failed        # Error notifications
  ├── alerts                   # Threshold violations
  └── sweep/summary            # Batch results

bci/
  ├── sensor/data              # Raw sensor data
  ├── stream/start             # Stream initiated
  └── quality/metrics          # Signal quality

opensim/
  ├── cosimulation/result      # Co-sim completed
  └── muscle/forces            # Real-time forces

tak/
  ├── +/event                  # TAK events (wildcard)
  └── medical/response         # Medical assessment
```

**MQTT Broker Options:**
- **Mosquitto** (lightweight, local)
- **EMQX** (scalable, enterprise)
- **HiveMQ** (cloud-native)

**Setup Mosquitto:**
```bash
# Install
sudo apt install mosquitto mosquitto-clients

# Start
sudo systemctl start mosquitto

# Test
mosquitto_pub -t "test" -m "Hello"
mosquitto_sub -t "test"
```

---

### Layer 4: Orchestration (Node-RED)

**What it does:**
- Visual workflow design
- Event routing and transformation
- Protocol bridging (MQTT ↔ HTTP ↔ Serial ↔ WebSocket)
- Scheduled jobs (cron)
- Decision trees and alerts
- Dashboard creation

**What it does NOT do:**
- Core simulation logic
- Heavy computation
- Millisecond-level timing

**Use Cases:**

#### 1. **TAK Event → Simulation → Response**
```
TAK medical alert
  → Node-RED receives via MQTT
  → Extract heart rate, patient ID
  → POST /api/heart/run
  → Format result as TAK CoT
  → Send to TAK server
```

#### 2. **Scheduled Configuration Sweep**
```
Cron trigger (hourly)
  → Create 5 different configs
  → Loop: POST /api/heart/run for each
  → Join results
  → Aggregate summary
  → Publish to MQTT + dashboard
```

#### 3. **Hardware Bridge**
```
Serial port (OpenBCI)
  → Parse EEG/ECG data
  → Normalize values
  → Store in TimescaleDB
  → Publish to MQTT
  → Trigger simulation if anomaly
```

#### 4. **Alerting Pipeline**
```
Simulation complete (MQTT)
  → Extract metrics
  → Decision node: if cardiac_max > 2.0
    → Send email/Slack/PagerDuty
    → Log to incident DB
    → Trigger secondary validation sim
  → else: just store metrics
```

**Install & Run:**
```bash
# Install globally
npm install -g node-red

# Start
node-red

# Access UI
open http://localhost:1880

# Import flows
# Copy contents of integrations/nodered/flows.json
# In Node-RED UI: Menu → Import → Paste JSON
```

**Flow Examples Included:**
- `flow_main` - Webhook → Sim → Alert/DB
- `flow_cron` - Scheduled 5-config sweep
- `flow_serial_hardware` - Serial device → TimescaleDB
- `flow_tak_integration` - TAK medical event handling

---

### Layer 5: TAK Integration

**What is TAK?**
Team Awareness Kit - situational awareness platform used by:
- Military operations
- Emergency response
- Disaster relief
- Field medicine

**Integration Points:**

**1. TAK as Trigger:**
```javascript
// TAK event structure (CoT - Cursor on Target)
{
  "event": {
    "uid": "medical-001",
    "type": "a-f-G-E-S",  // Medical event
    "detail": {
      "patient_id": "12345",
      "heart_rate": 110,
      "blood_pressure": "140/90"
    }
  }
}

// Node-RED flow:
// 1. Receive TAK event via MQTT or HTTP
// 2. Extract medical parameters
// 3. Configure HBCM simulation
// 4. Run simulation
// 5. Return assessment to TAK
```

**2. TAK as Display:**
```javascript
// Simulation result → TAK CoT
{
  "event": {
    "uid": "sim-result-001",
    "type": "a-f-G-E-S",
    "time": "2025-11-15T10:30:00Z",
    "detail": {
      "simulation_result": {
        "cardiac_max": 2.3,
        "neural_max": 1.5,
        "assessment": "abnormal",
        "recommendation": "Immediate evaluation required"
      }
    }
  }
}
```

**3. Node-RED TAK Flow:**
```
MQTT: tak/+/event
  ↓
Filter: event_type === 'medical'
  ↓
Extract: heart_rate, patient_id
  ↓
POST /api/heart/run
  ↓
Format: Create TAK CoT response
  ↓
POST to TAK server
```

---

### Layer 6: OpenSim Integration

**What is OpenSim?**
Biomechanical simulation software for musculoskeletal modeling.

**Repository:** https://github.com/opensim-org/opensim-core

**Co-Simulation Architecture:**

```python
# Bi-directional coupling:

HBCM Cardiac Output (x, y)
  ↓
Convert to Muscle Activation (0-1 range)
  ↓
Apply to OpenSim Muscles
  ↓
OpenSim Computes Muscle Forces
  ↓
Convert Forces to Cardiac Load
  ↓
Feed back to HBCM (influences heart rate)
  ↓
Loop in lockstep (same dt)
```

**Use Cases:**

**1. Exercise Physiology:**
```python
# Simulate running
# - Cardiac oscillator drives leg muscle activation
# - Muscle forces create metabolic demand
# - Demand increases cardiac frequency
# - Feedback loop models heart rate during exercise
```

**2. Rehabilitation:**
```python
# Post-surgery recovery
# - Limited muscle activation capacity
# - HBCM models cardiac response to reduced load
# - Predict safe exercise intensity
```

**3. Prosthetic Control:**
```python
# BCI → HBCM → OpenSim → Prosthetic
# - Brain signal controls cardiac model
# - Cardiac output drives virtual muscle
# - Muscle activation controls prosthetic limb
```

**Python API Usage:**
```python
from integrations.opensim import OpenSimBridge, HBCMOpenSimCoSimulator
from src.coupling import HeartBrainCouplingModel

# Setup
opensim_bridge = OpenSimBridge(config)
opensim_bridge.load_model("arm26.osim")

# Create co-simulator
cosim = HBCMOpenSimCoSimulator(
    hbcm_model=hbcm,
    opensim_bridge=opensim_bridge,
    coupling_gain=0.1
)

# Run
results = cosim.simulate(
    initial_hbcm_state=(0.0, 0.0, 1.0, 0.0),
    duration=10.0,
    dt=0.001
)

# Export
cosim.export_to_opensim("output/")
```

**Node.js API:**
```bash
curl -X POST http://localhost:3000/api/opensim/cosimulate \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 10.0,
    "opensim_model": "arm26.osim",
    "coupling_gain": 0.1
  }'
```

---

## MCP Integration

**MCP (Model Context Protocol)** allows LLMs to call these tools:

```json
{
  "tools": [
    {
      "name": "run_heart_simulation",
      "description": "Run HBCM cardiac simulation with specified parameters",
      "input_schema": {
        "type": "object",
        "properties": {
          "duration": {"type": "number"},
          "neural_params": {"type": "object"},
          "cardiac_params": {"type": "object"}
        }
      }
    },
    {
      "name": "cosimulate_heart_muscle",
      "description": "Run coupled heart-muscle biomechanical simulation",
      "input_schema": {
        "type": "object",
        "properties": {
          "duration": {"type": "number"},
          "opensim_model": {"type": "string"},
          "coupling_gain": {"type": "number"}
        }
      }
    }
  ]
}
```

**MCP Server Implementation:**
```javascript
// MCP server wraps Node.js API
const mcpServer = createMCPServer({
  tools: {
    run_heart_simulation: async (params) => {
      const response = await axios.post('http://localhost:3000/api/heart/run', params);
      return response.data;
    },
    cosimulate_heart_muscle: async (params) => {
      const response = await axios.post('http://localhost:3000/api/opensim/cosimulate', params);
      return response.data;
    }
  }
});
```

**LLM Interaction:**
```
User: "Run a simulation with high neural coupling and check if it's stable"

LLM: I'll run a simulation with increased neural coupling:
<tool_call>
{
  "tool": "run_heart_simulation",
  "parameters": {
    "duration": 20.0,
    "coupling_params": {
      "neural_to_cardiac_gain": 0.8
    }
  }
}
</tool_call>

Result: {
  "metrics": {
    "cardiac": {"max": 2.1, "std": 0.45},
    "neural": {"max": 1.8, "std": 0.62}
  }
}

LLM: The simulation shows the system is stable. The cardiac oscillation
     max of 2.1 is within normal bounds, and the standard deviation
     of 0.45 indicates consistent periodic behavior.
```

---

## Data Flow Examples

### Example 1: Field Medical Assessment

```
1. Medic wearing BCI headset in field
   └→ OpenBCI streams EEG via serial

2. Node-RED flow: Serial → Parse → Store → MQTT
   └→ Topic: bci/sensor/data

3. Python BCI adapter consumes MQTT
   └→ Processes signal quality
   └→ Publishes: bci/quality/metrics

4. Node-RED decision node
   └→ If quality > 0.7: trigger simulation
   └→ Else: alert "Poor signal quality"

5. POST http://nodejs:3000/api/heart/run
   └→ Node.js calls Python HBCM
   └→ Returns metrics

6. Node-RED formats for TAK
   └→ POST to TAK server
   └→ Commander sees assessment on tablet

7. If cardiac_max > 2.0
   └→ Send alert via MQTT: alerts/medical
   └→ Trigger secondary validation sim
   └→ Log to incident database
```

### Example 2: Hourly Research Sweep

```
1. Node-RED cron trigger (every hour)
   └→ Create array of 5 configurations

2. For each config:
   └→ POST /api/heart/run
   └→ Wait for result

3. Join all 5 results
   └→ Aggregate summary statistics
   └→ Compare configurations

4. Publish to MQTT: heart/sweep/summary
   └→ Research dashboard updates
   └→ Store in PostgreSQL

5. Decision node
   └→ If any config shows drift > 50ms
       └→ Email research team
       └→ Flag for manual review
```

### Example 3: Prosthetic Control Loop

```
1. User thinks "move arm"
   └→ BCI headset captures EEG

2. BCI adapter processes signal
   └→ Publishes: bci/intent/detected

3. Node-RED receives intent
   └→ Configures HBCM with intent signal

4. POST /api/heart/run (very short duration, 100ms)
   └→ HBCM produces cardiac trajectory

5. POST /api/opensim/cosimulate
   └→ Cardiac trajectory drives muscle activation
   └→ OpenSim computes joint torques

6. Node-RED receives torques
   └→ Formats as motor commands
   └→ Sends via serial to prosthetic controller

7. Prosthetic arm moves
   └→ Entire loop: <100ms latency
```

---

## Deployment Scenarios

### Scenario 1: Lab Research Station

```yaml
# docker-compose.yml
version: '3.8'
services:
  mosquitto:
    image: eclipse-mosquitto
    ports: ["1883:1883"]

  nodejs-api:
    build: ./integrations/nodejs
    ports: ["3000:3000"]
    environment:
      ENABLE_MQTT: "true"
      MQTT_BROKER: "mqtt://mosquitto:1883"

  node-red:
    image: nodered/node-red
    ports: ["1880:1880"]
    volumes:
      - ./integrations/nodered:/data

  postgres:
    image: timescale/timescaledb:latest-pg14
    environment:
      POSTGRES_DB: heart_data
```

**Run:**
```bash
docker-compose up -d
open http://localhost:1880  # Node-RED
open http://localhost:3000  # API
```

### Scenario 2: Field Deployment (Offline)

```
Edge Device (Raspberry Pi 4):
  ├── Mosquitto (local broker)
  ├── Node.js API (cached models)
  ├── Node-RED (pre-loaded flows)
  └── SQLite (local storage)

Optional connectivity:
  └── Sync to cloud when available
```

### Scenario 3: Cloud (Scalable)

```
Load Balancer
  ├→ Node.js API (3 replicas)
  ├→ Python Workers (10 replicas)
  └→ Node-RED (read-only, 2 replicas)

MQTT Cluster (EMQX)
  ├→ 3 nodes with persistence

Databases:
  ├→ PostgreSQL (simulation results)
  ├→ TimescaleDB (time-series sensor data)
  └→ Redis (job queue, caching)
```

---

## Security Considerations

### 1. API Authentication
```javascript
// Add JWT to Node.js
const jwt = require('jsonwebtoken');

app.use('/api/', (req, res, next) => {
  const token = req.headers['authorization'];
  if (!token) return res.status(401).json({ error: 'No token' });

  jwt.verify(token, process.env.JWT_SECRET, (err, decoded) => {
    if (err) return res.status(403).json({ error: 'Invalid token' });
    req.user = decoded;
    next();
  });
});
```

### 2. MQTT Authentication
```conf
# mosquitto.conf
allow_anonymous false
password_file /etc/mosquitto/passwd

# Create users
mosquitto_passwd -c /etc/mosquitto/passwd admin
mosquitto_passwd /etc/mosquitto/passwd nodered
```

### 3. Rate Limiting
```javascript
// Already implemented in Node.js server
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100
});
```

### 4. Input Validation
```javascript
const Joi = require('joi');

const simSchema = Joi.object({
  duration: Joi.number().min(0.1).max(1000).required(),
  dt: Joi.number().min(0.0001).max(1).required(),
  neural_params: Joi.object().optional(),
  cardiac_params: Joi.object().optional()
});

app.post('/api/heart/run', (req, res) => {
  const { error } = simSchema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details });
  // ...
});
```

---

## Performance Tuning

### Node.js
```javascript
// Cluster mode for multi-core
const cluster = require('cluster');
const numCPUs = require('os').cpus().length;

if (cluster.isMaster) {
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
} else {
  // Worker processes run the server
  require('./server');
}
```

### Python
```python
# Use multiprocessing for parallel sims
from multiprocessing import Pool

def run_sim(config):
    # ... simulation code
    return result

with Pool(4) as pool:
    results = pool.map(run_sim, configs)
```

### MQTT
```conf
# mosquitto.conf
max_connections 10000
max_queued_messages 10000
message_size_limit 0
```

---

## Monitoring & Observability

### Metrics to Track
```javascript
// Node.js Prometheus metrics
const prometheus = require('prom-client');

const simCounter = new prometheus.Counter({
  name: 'simulations_total',
  help: 'Total simulations run'
});

const simDuration = new prometheus.Histogram({
  name: 'simulation_duration_seconds',
  help: 'Simulation execution time'
});

app.get('/metrics', (req, res) => {
  res.set('Content-Type', prometheus.register.contentType);
  res.end(prometheus.register.metrics());
});
```

### Logging
```javascript
// Structured logging
const winston = require('winston');

const logger = winston.createLogger({
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

logger.info('Simulation started', { id: job.id, duration: config.duration });
```

---

## Troubleshooting

### MQTT Connection Failed
```bash
# Check broker running
sudo systemctl status mosquitto

# Test with clients
mosquitto_pub -t "test" -m "hello"
mosquitto_sub -t "test" -v

# Check firewall
sudo ufw allow 1883/tcp
```

### Node.js Can't Find Python
```bash
# Set Python path
export PYTHON_PATH=/usr/bin/python3

# Or in Node.js
const options = {
  pythonPath: '/usr/bin/python3',
  // ...
};
```

### Node-RED Flow Not Triggering
```
1. Check Node-RED logs: journalctl -u nodered -f
2. Verify MQTT broker connection in Node-RED settings
3. Test MQTT independently: mosquitto_pub -t "test" -m "msg"
4. Check topic subscriptions match exactly
5. Verify QoS settings (use QoS 1 or 2 for reliability)
```

---

## Next Steps

1. **Install Dependencies:**
   ```bash
   # MQTT Broker
   sudo apt install mosquitto

   # Node.js
   cd integrations/nodejs && npm install

   # Node-RED
   npm install -g node-red

   # OpenSim (optional)
   conda install -c opensim-org opensim
   ```

2. **Start Services:**
   ```bash
   # Terminal 1: MQTT
   mosquitto -v

   # Terminal 2: Node.js API
   cd integrations/nodejs && npm start

   # Terminal 3: Node-RED
   node-red
   ```

3. **Import Flows:**
   - Open http://localhost:1880
   - Menu → Import → Clipboard
   - Paste contents of `integrations/nodered/flows.json`

4. **Test Integration:**
   ```bash
   # Trigger webhook
   curl -X POST http://localhost:1880/trigger/simulation \
     -H "Content-Type: application/json" \
     -d '{"duration": 5.0}'

   # Check MQTT
   mosquitto_sub -t "heart/#" -v
   ```

---

## Summary

**Mental Model:**

- **Multi-Heart + OpenSim**: Do the math (Python)
- **Node.js**: Expose clean API, manage state
- **MQTT**: Event bus for decoupling
- **Node-RED**: Visual "mission control" for workflows
- **TAK**: Field deployment and situational awareness
- **MCP**: Let LLMs orchestrate simulations

**Where Each Belongs:**

| Task | Tool |
|------|------|
| Solve ODEs | Python (HBCM) |
| Muscle dynamics | Python (OpenSim) |
| REST API | Node.js |
| WebSocket | Node.js |
| Event routing | MQTT |
| Workflows | Node-RED |
| Cron jobs | Node-RED |
| Protocol bridges | Node-RED |
| Alerts | Node-RED |
| Dashboards | Node-RED |
| LLM tools | MCP (wraps Node.js) |
| Tactical display | TAK |

**Value Proposition:**

This architecture enables:
- **Rapid integration** of new sensors/protocols (Node-RED visual flows)
- **Zero downtime updates** (MQTT buffering, stateless Node.js)
- **Field deployment** (offline-capable edge devices)
- **LLM orchestration** (MCP tool access)
- **Real-time alerting** (event-driven, <1s latency)
- **Multi-domain coupling** (heart + brain + muscle + hardware)

You now have a production-ready, event-driven system ready for research, clinical trials, or field deployment.
