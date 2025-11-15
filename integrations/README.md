# Multi-Heart-Model Integrations

**Production-Ready Event-Driven Architecture**

This directory contains enterprise-grade integrations for deploying Multi-Heart-Model in real-world scenarios:

## 📂 Directory Structure

```
integrations/
├── opensim/              # OpenSim biomechanical co-simulation
│   ├── opensim_bridge.py
│   └── run_cosimulation.py
├── nodejs/               # Node.js REST API service
│   ├── server.js
│   ├── package.json
│   └── Dockerfile
├── nodered/              # Node-RED workflow orchestration
│   └── flows.json
├── mosquitto/            # MQTT broker configuration
│   └── config/mosquitto.conf
├── docker-compose.yml    # Full stack deployment
└── INTEGRATION_ARCHITECTURE.md  # Complete architecture guide
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
cd integrations

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f nodejs-api

# Stop all services
docker-compose down
```

**Access:**
- Node.js API: `http://localhost:3000`
- Node-RED: `http://localhost:1880`
- Grafana: `http://localhost:3001` (admin/admin)
- MQTT: `localhost:1883`

### Option 2: Manual Setup

**1. Start MQTT Broker:**
```bash
# Install
sudo apt install mosquitto mosquitto-clients

# Configure
sudo cp mosquitto/config/mosquitto.conf /etc/mosquitto/conf.d/

# Start
sudo systemctl start mosquitto

# Test
mosquitto_pub -t "test" -m "hello"
mosquitto_sub -t "test" -v
```

**2. Start Node.js API:**
```bash
cd nodejs
npm install

# Set environment
export ENABLE_MQTT=true
export MQTT_BROKER="mqtt://localhost:1883"

# Run
npm start

# Or with PM2 for production
npm install -g pm2
pm2 start server.js --name multi-heart-api
```

**3. Start Node-RED:**
```bash
# Install
npm install -g node-red

# Run
node-red

# Access: http://localhost:1880

# Import flows
# 1. Open Node-RED UI
# 2. Menu → Import
# 3. Paste contents of nodered/flows.json
# 4. Deploy
```

## 📖 Component Guides

### OpenSim Integration

**Purpose:** Couple heart-brain dynamics with musculoskeletal biomechanics.

**Requirements:**
```bash
# Install OpenSim Python API
conda install -c opensim-org opensim
```

**Usage:**
```python
from integrations.opensim import OpenSimBridge, HBCMOpenSimCoSimulator

# Create bridge
bridge = OpenSimBridge(config)
bridge.load_model("arm26.osim")

# Run co-simulation
cosim = HBCMOpenSimCoSimulator(hbcm, bridge)
results = cosim.simulate(
    initial_hbcm_state=(0.0, 0.0, 1.0, 0.0),
    duration=10.0,
    dt=0.001
)
```

**API Endpoint:**
```bash
curl -X POST http://localhost:3000/api/opensim/cosimulate \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 10.0,
    "opensim_model": "arm26.osim"
  }'
```

**Features:**
- Cardiac dynamics → Muscle activation mapping
- Muscle forces → Cardiac load feedback
- Synchronized time-stepping
- Export to OpenSim .sto format

---

### Node.js API

**Purpose:** Clean REST interface for simulations with event publishing.

**Key Endpoints:**

```bash
# Health check
curl http://localhost:3000/health

# API documentation
curl http://localhost:3000/api

# Run simulation
curl -X POST http://localhost:3000/api/heart/run \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 5.0,
    "dt": 0.001,
    "cardiac_params": {"omega": 1.2}
  }'

# Create simulation job (async)
curl -X POST http://localhost:3000/api/simulations \
  -H "Content-Type: application/json" \
  -d '{"duration": 60.0, "dt": 0.001}'

# Check status
curl http://localhost:3000/api/simulations/STATUS_ID/status

# List all simulations
curl http://localhost:3000/api/simulations
```

**Environment Variables:**
```bash
PORT=3000                              # API port
ENABLE_MQTT=true                       # Enable MQTT publishing
MQTT_BROKER=mqtt://localhost:1883      # MQTT broker URL
PYTHON_PATH=/usr/bin/python3          # Python executable
NODE_ENV=production                    # Environment mode
```

**MQTT Events Published:**
- `simulation/started` - Job initiated
- `simulation/completed` - Results available
- `simulation/failed` - Error occurred
- `heart/simulation/result` - Quick run metrics

---

### Node-RED Flows

**Purpose:** Visual workflow orchestration, no-code integration.

**Included Flows:**

**1. Main Orchestration (`flow_main`):**
```
Webhook → Extract Config → POST /heart/run → Check Thresholds
  ├→ If cardiac_max > 2.0: Send Alert (MQTT)
  └→ Else: Store in DB
```

**2. Scheduled Sweeps (`flow_cron`):**
```
Hourly Trigger → Create 5 Configs → For Each:
  POST /heart/run → Join Results → Aggregate Summary → Publish
```

**3. Serial Hardware (`flow_serial_hardware`):**
```
Serial Port → Parse Sensor Data → Normalize → Store in TimescaleDB
  └→ Also: Publish to MQTT (bci/sensor/data)
```

**4. TAK Integration (`flow_tak_integration`):**
```
MQTT: tak/+/event → Filter Medical → Create Sim Config →
  POST /heart/run → Format for TAK → Send to TAK Server
```

**Customization:**
1. Open http://localhost:1880
2. Double-click any node to edit
3. Change topics, thresholds, endpoints
4. Deploy changes (top-right button)

---

### MQTT Topics

**Simulation Events:**
- `heart/simulation/result` - Completed simulation metrics
- `heart/simulation/started` - Job initiated
- `heart/simulation/failed` - Error notifications
- `heart/alerts` - Threshold violations
- `heart/sweep/summary` - Batch sweep results

**BCI Events:**
- `bci/sensor/data` - Raw sensor data from hardware
- `bci/stream/start` - Stream initiated
- `bci/quality/metrics` - Signal quality scores

**OpenSim Events:**
- `opensim/cosimulation/result` - Co-simulation completed
- `opensim/muscle/forces` - Real-time muscle force data

**TAK Events:**
- `tak/+/event` - TAK events (wildcard subscription)
- `tak/medical/response` - Medical assessment results

**Subscribe to All:**
```bash
mosquitto_sub -t "#" -v  # All topics
mosquitto_sub -t "heart/#" -v  # Heart-related only
```

---

## 🔧 Configuration

### Mosquitto (MQTT Broker)

Edit `mosquitto/config/mosquitto.conf`:

```conf
# Enable authentication (production)
allow_anonymous false
password_file /mosquitto/config/passwd
acl_file /mosquitto/config/acl

# Create users
mosquitto_passwd -c /mosquitto/config/passwd admin
mosquitto_passwd /mosquitto/config/passwd nodered
mosquitto_passwd /mosquitto/config/passwd nodejs-api
```

### Node.js API

Create `.env` file in `nodejs/`:

```env
PORT=3000
ENABLE_MQTT=true
MQTT_BROKER=mqtt://localhost:1883
PYTHON_PATH=/usr/bin/python3
NODE_ENV=production
JWT_SECRET=your-secret-key-change-this
```

### PostgreSQL / TimescaleDB

Initialize database:

```sql
-- Create hypertable for sensor data
CREATE TABLE sensor_data (
  time TIMESTAMPTZ NOT NULL,
  ecg DOUBLE PRECISION,
  eeg DOUBLE PRECISION,
  source TEXT
);

SELECT create_hypertable('sensor_data', 'time');

-- Create index
CREATE INDEX idx_sensor_time ON sensor_data (time DESC);
```

---

## 📊 Monitoring & Dashboards

### Prometheus Metrics

Node.js exposes Prometheus metrics at `/metrics`:

```bash
curl http://localhost:3000/metrics
```

**Key Metrics:**
- `simulations_total` - Total simulations run
- `simulation_duration_seconds` - Execution time histogram
- `http_requests_total` - API request count
- `nodejs_heap_size_used_bytes` - Memory usage

### Grafana Dashboards

Access Grafana at `http://localhost:3001` (default: admin/admin)

**Pre-configured:**
- Simulation metrics over time
- MQTT message rates
- API request latency
- System resource usage

**Create Custom Dashboard:**
1. Add Data Source → PostgreSQL (host: `postgres:5432`)
2. New Dashboard → Add Panel
3. Query: `SELECT * FROM sensor_data WHERE time > NOW() - INTERVAL '1 hour'`

---

## 🐳 Docker Deployment

### Build Images

```bash
# Build Node.js API
cd nodejs
docker build -t multi-heart-api .

# Or use docker-compose
cd ..
docker-compose build
```

### Production Deployment

```bash
# Set environment variables
export POSTGRES_PASSWORD=your-secure-password
export GRAFANA_PASSWORD=your-admin-password

# Start services
docker-compose up -d

# Scale API replicas
docker-compose up -d --scale nodejs-api=3

# Update single service
docker-compose up -d --no-deps --build nodejs-api

# View logs
docker-compose logs -f nodejs-api

# Execute commands in container
docker-compose exec nodejs-api node --version
docker-compose exec postgres psql -U postgres heart_data
```

### Docker Secrets (Swarm/Kubernetes)

```bash
# Create secrets
echo "my-password" | docker secret create postgres_password -

# Update docker-compose.yml
secrets:
  postgres_password:
    external: true

services:
  postgres:
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
```

---

## 🔐 Security

### Authentication

**Node.js JWT:**
```javascript
// Generate token
curl -X POST http://localhost:3000/api/auth/login \
  -d '{"username": "user", "password": "pass"}'

// Use token
curl -H "Authorization: Bearer <token>" \
  http://localhost:3000/api/simulations
```

### MQTT ACL

Create `mosquitto/config/acl`:

```
# Admin - full access
user admin
topic readwrite #

# Node-RED - read all, write to flows
user nodered
topic read #
topic write nodered/#

# Node.js API - write simulation results
user nodejs-api
topic write heart/#
topic write opensim/#
```

### Rate Limiting

Node.js has built-in rate limiting (100 requests per 15 minutes).

Adjust in `server.js`:

```javascript
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 1000  // Increase for production
});
```

---

## 🧪 Testing

### Unit Tests (Node.js)

```bash
cd nodejs
npm test

# With coverage
npm run test:coverage
```

### Integration Tests

```bash
# Start services
docker-compose up -d

# Run tests
python -m pytest tests/integration/

# Test MQTT flow
python tests/test_mqtt_integration.py

# Test Node-RED flows
npm run test:nodered
```

### Manual Testing

**1. Test API:**
```bash
# Health check
curl http://localhost:3000/health

# Run simulation
curl -X POST http://localhost:3000/api/heart/run \
  -H "Content-Type: application/json" \
  -d '{"duration": 1.0}' | jq .
```

**2. Test MQTT:**
```bash
# Terminal 1: Subscribe
mosquitto_sub -t "heart/#" -v

# Terminal 2: Trigger simulation (should see MQTT message in Terminal 1)
curl -X POST http://localhost:3000/api/heart/run -d '{"duration": 1.0}'
```

**3. Test Node-RED:**
```bash
# Trigger webhook
curl -X POST http://localhost:1880/trigger/simulation \
  -H "Content-Type: application/json" \
  -d '{"duration": 2.0, "source": "test"}'
```

---

## 🔍 Troubleshooting

### Problem: MQTT broker not connecting

**Solution:**
```bash
# Check broker running
sudo systemctl status mosquitto

# Check port open
netstat -tulpn | grep 1883

# Test connection
mosquitto_pub -t "test" -m "hello"
mosquitto_sub -t "test"

# Check firewall
sudo ufw allow 1883/tcp
```

### Problem: Node.js can't find Python

**Solution:**
```bash
# Find Python path
which python3

# Set environment
export PYTHON_PATH=/usr/bin/python3

# Or in .env file
echo "PYTHON_PATH=/usr/bin/python3" >> nodejs/.env
```

### Problem: Docker containers can't communicate

**Solution:**
```bash
# Check network
docker network ls
docker network inspect multi-heart-network

# Restart services
docker-compose down
docker-compose up -d

# Check DNS resolution
docker-compose exec nodejs-api ping mosquitto
```

### Problem: High latency in simulations

**Solution:**
```bash
# Check system resources
docker stats

# Increase container limits
# In docker-compose.yml:
services:
  nodejs-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

# Use faster timestep (but less accurate)
{"duration": 10.0, "dt": 0.01}  # Instead of 0.001
```

---

## 🌐 Use Cases

### 1. Research Lab

- **Setup:** Docker Compose on lab server
- **Workflow:** Node-RED collects BCI data → triggers simulations → stores in TimescaleDB
- **Visualization:** Grafana dashboards for real-time monitoring
- **Alerting:** Email notifications on anomalies

### 2. Field Deployment

- **Setup:** Raspberry Pi with offline capability
- **Workflow:** Serial hardware → Node-RED → local MQTT → SQLite storage
- **Sync:** Periodic upload to cloud when connectivity available
- **TAK Integration:** Send assessments to tactical operations center

### 3. Cloud-Native

- **Setup:** Kubernetes cluster with auto-scaling
- **Workflow:** API Gateway → Load Balancer → Node.js replicas → Python workers
- **Storage:** S3 for results, RDS for metadata
- **Monitoring:** Prometheus + Grafana + PagerDuty

---

## 📚 Additional Resources

- **Architecture Guide:** [INTEGRATION_ARCHITECTURE.md](INTEGRATION_ARCHITECTURE.md)
- **API Documentation:** http://localhost:3000/api (when running)
- **Node-RED Documentation:** https://nodered.org/docs/
- **MQTT Documentation:** https://mosquitto.org/documentation/
- **OpenSim Documentation:** https://opensim.stanford.edu/

---

## 🤝 Contributing

To add new integrations:

1. Create directory: `integrations/your_integration/`
2. Add adapter: Implement standard interface
3. Update API: Add endpoints in `nodejs/server.js`
4. Create flow: Design Node-RED workflow
5. Document: Update this README
6. Test: Add integration tests

---

## 📝 License

MIT License - See LICENSE file for details

---

## ✅ Checklist for Deployment

- [ ] Install and configure MQTT broker
- [ ] Set up environment variables (.env files)
- [ ] Configure authentication (JWT, MQTT passwords)
- [ ] Set up databases (PostgreSQL/TimescaleDB)
- [ ] Import Node-RED flows
- [ ] Test API endpoints
- [ ] Verify MQTT pub/sub
- [ ] Configure monitoring (Prometheus/Grafana)
- [ ] Set up SSL/TLS for production
- [ ] Configure firewall rules
- [ ] Set up backups
- [ ] Document custom workflows
- [ ] Train operators on Node-RED interface

**Status:** All components ready for deployment! 🎉
