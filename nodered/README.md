# Node-RED Integration for Multi-Heart-Model
## Phase 1: Real-Time HBCM Dashboard

This directory contains Node-RED flows and configuration for real-time monitoring and control of the Heart-Brain Coupling Model (HBCM).

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Dashboard Components](#dashboard-components)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## 🚀 Quick Start

### Prerequisites

- Node.js 16+ and npm 8+
- FastAPI backend running (from `web_control_panel/backend/`)
- HBCM Python environment configured

### One-Line Install

```bash
cd nodered
chmod +x setup.sh
./setup.sh
```

### Manual Install

```bash
# 1. Install Node-RED globally
npm install -g --unsafe-perm node-red

# 2. Install dashboard nodes
cd nodered
npm install

# 3. Start Node-RED
npm start
```

### Access

- **Node-RED Editor**: http://localhost:1880
- **HBCM Dashboard**: http://localhost:1880/ui

---

## ✨ Features

### Real-Time Monitoring

- **Neural Activity Gauge**: Live voltage (v) measurement with color-coded status
- **Cardiac Position Gauge**: Real-time cardiac oscillator position (x)
- **Time-Series Charts**: 30-second rolling history of neural and cardiac dynamics
- **System Metrics**: Comfort index and phase drift monitoring
- **Debug Console**: Raw data inspection for development

### Simulation Control

- **Start/Stop/Pause/Reset**: Full control over HBCM simulation
- **Status Monitoring**: Automatic system status checks every 5 seconds
- **Visual Feedback**: Toast notifications for control commands

### Architecture

- **WebSocket Connection**: Direct connection to FastAPI backend
- **Low Latency**: Real-time data updates (sub-second)
- **Responsive UI**: Mobile-friendly dashboard layout

---

## 📦 Installation

### Step 1: Install Node.js

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**macOS:**
```bash
brew install node
```

**Windows:**
Download from https://nodejs.org/

### Step 2: Run Setup Script

```bash
cd /home/user/Multi-Heart-Model/nodered
./setup.sh
```

The script will:
1. ✓ Check Node.js version (16+)
2. ✓ Install Node-RED globally
3. ✓ Install dashboard and additional nodes
4. ✓ Create configuration files
5. ✓ Verify flows.json exists
6. ✓ Check FastAPI backend connection

### Step 3: Verify Installation

```bash
# Check Node-RED is installed
node-red --version

# Check dashboard node is installed
npm list node-red-dashboard
```

---

## 🎮 Usage

### Starting the System

**1. Start FastAPI Backend**
```bash
cd ../web_control_panel/backend
uvicorn main:app --reload
```

**2. Start Node-RED**
```bash
cd nodered
npm start
# or: node-red --userDir .
```

**3. Access Dashboard**
Open browser to http://localhost:1880/ui

### Using the Dashboard

1. **Monitor Data**: Dashboard automatically connects to WebSocket
2. **Start Simulation**: Click green "Start" button
3. **View Real-Time Data**: Watch gauges and charts update live
4. **Control Simulation**: Use Stop/Pause/Reset as needed

### Importing Flows

If flows don't load automatically:

1. Open http://localhost:1880 (Node-RED editor)
2. Click hamburger menu (☰) → Import
3. Select `flows.json` from this directory
4. Click "Import"
5. Deploy flows (red "Deploy" button)

---

## 📊 Dashboard Components

### Neural Activity Panel

**Gauge (Left):**
- Range: -2 to +2
- Green: Normal (-0.5 to 0.5)
- Yellow: Warning zone
- Red: Alert zone

**Chart (Bottom):**
- 30-second rolling history
- Real-time line plot
- Y-axis: -2 to +2

### Cardiac Activity Panel

**Gauge (Right):**
- Range: -3 to +3
- Donut chart visualization
- Color-coded status

**Chart (Bottom):**
- 30-second rolling history
- Orange line plot
- Y-axis: -3 to +3

### System Metrics

**Comfort Index:**
- Range: 0 to 1
- Red: < 0.3 (Low comfort)
- Yellow: 0.3-0.7 (Medium)
- Green: > 0.7 (High comfort)

**Phase Drift:**
- Range: 0 to 100 ms
- Green: < 30 ms (Good)
- Yellow: 30-60 ms (Acceptable)
- Red: > 60 ms (High drift)

### Control Panel

| Button | Color | Function |
|--------|-------|----------|
| Start  | Green | Begin HBCM simulation |
| Stop   | Red   | Halt simulation |
| Pause  | Yellow | Pause simulation |
| Reset  | Blue  | Reset to initial state |

**Status Display:**
- Updates every 5 seconds
- Shows current simulation state

---

## 🏗️ Architecture

### Data Flow

```
FastAPI Backend (Port 8000)
    ↓ WebSocket
    ws://localhost:8000/ws/nodered-client
    ↓
Node-RED WebSocket In Node
    ↓
Parse HBCM Data Function
    ↓ Extracted metrics
    ├─→ Neural Gauge
    ├─→ Neural Chart
    ├─→ Cardiac Gauge
    ├─→ Cardiac Chart
    ├─→ Comfort Index Gauge
    └─→ Phase Drift Gauge
```

### Control Flow

```
Dashboard Button (Start/Stop/etc)
    ↓ JSON payload
HTTP Request Node
    ↓ POST http://localhost:8000/api/control
FastAPI Backend
    ↓ Response
Toast Notification
```

### File Structure

```
nodered/
├── flows.json           # Node-RED flow definitions
├── package.json         # Node dependencies
├── settings.js          # Node-RED configuration (auto-generated)
├── setup.sh            # Automated setup script
└── README.md           # This file
```

---

## 🔧 Troubleshooting

### Issue: "Cannot connect to WebSocket"

**Symptoms:**
- Dashboard shows "Waiting for data..."
- No gauges updating
- Debug console shows connection errors

**Solutions:**

1. **Check FastAPI is running:**
   ```bash
   curl http://localhost:8000/api/status
   ```
   If this fails, start FastAPI:
   ```bash
   cd ../web_control_panel/backend
   uvicorn main:app --reload
   ```

2. **Verify WebSocket endpoint:**
   - Open browser dev tools (F12)
   - Check for WebSocket connection to `ws://localhost:8000/ws/nodered-client`
   - Look for connection errors

3. **Check Node-RED WebSocket config:**
   - In Node-RED editor, double-click WebSocket In node
   - Verify URL is `ws://localhost:8000/ws/nodered-client`
   - Click "Edit" on websocket config, then "Update" and "Done"

### Issue: "Dashboard not loading"

**Symptoms:**
- http://localhost:1880/ui shows blank page
- 404 error on dashboard

**Solutions:**

1. **Check dashboard node is installed:**
   ```bash
   npm list node-red-dashboard
   ```
   If missing:
   ```bash
   npm install node-red-dashboard
   ```

2. **Restart Node-RED:**
   - Stop Node-RED (Ctrl+C)
   - Start again: `npm start`

3. **Clear browser cache:**
   - Hard reload: Ctrl+Shift+R (or Cmd+Shift+R on Mac)

### Issue: "Control buttons not working"

**Symptoms:**
- Clicking Start/Stop does nothing
- No toast notifications appear

**Solutions:**

1. **Check FastAPI API endpoint:**
   ```bash
   curl -X POST http://localhost:8000/api/control \
     -H "Content-Type: application/json" \
     -d '{"command":"start"}'
   ```

2. **Check Node-RED debug:**
   - Open Node-RED editor (http://localhost:1880)
   - Click debug icon (bug) in right sidebar
   - Click a control button
   - Look for error messages

3. **Verify HTTP request node:**
   - Double-click "POST Control Command" node
   - Verify URL is `http://localhost:8000/api/control`
   - Method should be "POST"

### Issue: "Node-RED won't start"

**Symptoms:**
- `npm start` fails
- Port already in use error

**Solutions:**

1. **Check port 1880 is free:**
   ```bash
   lsof -i :1880
   # Or on Windows: netstat -ano | findstr :1880
   ```
   Kill existing process if found

2. **Try different port:**
   ```bash
   PORT=1881 node-red --userDir .
   ```

3. **Check Node.js version:**
   ```bash
   node -v  # Should be 16.0.0 or higher
   ```

### Issue: "Gauges show wrong values"

**Symptoms:**
- Gauges stuck at min/max
- Values don't match expected range

**Solutions:**

1. **Check data extraction function:**
   - In Node-RED editor, double-click "Parse HBCM Data" function
   - Verify field names match FastAPI data structure:
     - `data.data.neural.v`
     - `data.data.cardiac.x`

2. **Inspect raw WebSocket data:**
   - Look at Debug panel in Node-RED
   - Compare with expected format

---

## 🚀 Next Steps (Phase 2-6)

### Phase 2: Authentication (Week 2)
- Integrate with Node.js gateway
- Add JWT authentication to Node-RED
- User-specific dashboards

### Phase 3: Database Integration (Week 3)
- Store historical data in MongoDB
- InfluxDB time-series logging
- Historical chart views

### Phase 4: OpenSim Integration (Weeks 4-5)
- Trigger OpenSim simulations from dashboard
- Display biomechanical results
- Closed-loop feedback visualization

### Phase 5: Advanced Flows (Week 6)
- MQTT sensor integration
- Scheduled parameter sweeps
- Email/SMS alerting
- TAK integration flows

### Phase 6: Production Deployment (Week 7)
- Docker containerization
- NGINX reverse proxy
- SSL/TLS certificates
- Monitoring and logging

---

## 📖 Additional Resources

### Documentation

- **Main Integration Guide**: `/docs/NODERED_NODEJS_INTEGRATION.md`
- **HBCM Architecture**: `/docs/ARCHITECTURE_OVERVIEW.md`
- **FastAPI Backend**: `/web_control_panel/backend/main.py`

### Node-RED Resources

- **Official Docs**: https://nodered.org/docs/
- **Dashboard Guide**: https://flows.nodered.org/node/node-red-dashboard
- **Cookbook**: https://cookbook.nodered.org/

### Example Flows

The `flows.json` in this directory includes:

1. **WebSocket Connection** - Real-time data ingestion
2. **Data Parser** - Extract HBCM metrics
3. **Gauges** - Neural and cardiac monitoring
4. **Charts** - Time-series visualization
5. **Control Buttons** - Start/Stop/Pause/Reset
6. **Status Monitor** - System health check

---

## 🤝 Contributing

To add new flows or modify existing ones:

1. Make changes in Node-RED editor
2. Export flows: Menu → Export → Current Flow
3. Save to `flows.json`
4. Test thoroughly
5. Document in this README
6. Commit and push

---

## 📝 License

MIT License - see LICENSE file in repository root

---

## 👥 Support

For issues or questions:

- **GitHub Issues**: https://github.com/STLNFTART/Multi-Heart-Model/issues
- **Main Documentation**: `/docs/NODERED_NODEJS_INTEGRATION.md`
- **FastAPI Logs**: Check terminal running FastAPI for backend errors

---

**Phase 1 Implementation Complete** ✅

This setup provides the foundation for real-time HBCM monitoring. Future phases will add authentication, databases, OpenSim integration, and advanced IoT orchestration.

**Last Updated**: 2025-11-15
**Author**: Multi-Heart-Model Team
