# Multi-Heart-Model Node.js API Gateway

Node.js-based API gateway providing authentication, data persistence, and OpenSim integration for the Multi-Heart-Model HBCM simulation platform.

## Features

- **Authentication & Authorization**: JWT-based user authentication
- **Rate Limiting**: Protect endpoints from abuse
- **Reverse Proxy**: Seamless proxy to FastAPI backend
- **Historical Data**: MongoDB storage for simulation results
- **Time-Series Data**: InfluxDB for real-time metrics
- **OpenSim Integration**: Biomechanical simulation bridge
- **WebSocket Bridge**: FastAPI WebSocket → Socket.io for broader client support

## Architecture

```
Client Requests
    ↓
Node.js Gateway (Port 3000)
    ├─ /auth/*            → MongoDB (User management)
    ├─ /api/hbcm/*        → FastAPI Proxy (Port 8000)
    ├─ /api/simulations   → MongoDB (Historical queries)
    ├─ /api/timeseries/*  → InfluxDB (Time-series data)
    └─ /api/opensim/*     → OpenSim CLI Bridge
```

## Prerequisites

- Node.js 16+ and npm 8+
- MongoDB (local or cloud)
- InfluxDB (optional, for time-series data)
- FastAPI backend running (see `web_control_panel/backend/`)
- OpenSim (optional, for biomechanical simulations)

## Installation

### 1. Install Dependencies

```bash
cd nodejs_gateway
npm install
```

### 2. Configure Environment

Create `.env` file:

```env
# Server
PORT=3000

# FastAPI Backend
FASTAPI_URL=http://localhost:8000
FASTAPI_WS_URL=ws://localhost:8000/ws/nodejs-bridge

# Security
JWT_SECRET=your-secret-key-change-in-production

# MongoDB
MONGODB_URI=mongodb://localhost:27017/hbcm

# InfluxDB
INFLUXDB_HOST=localhost

# OpenSim
OPENSIM_BIN=opensim-cmd
OPENSIM_MODELS_DIR=/opt/opensim/models
OPENSIM_RESULTS_DIR=/tmp/opensim_results
```

### 3. Start Services

**MongoDB:**
```bash
docker run -d -p 27017:27017 --name mongo mongo
```

**InfluxDB (optional):**
```bash
docker run -d -p 8086:8086 --name influxdb influxdb:2.7
```

**FastAPI Backend:**
```bash
cd ../web_control_panel/backend
uvicorn main:app --reload
```

**Node.js Gateway:**
```bash
npm start
# or for development with auto-reload:
npm run dev
```

## API Endpoints

### Authentication

**Register:**
```bash
curl -X POST http://localhost:3000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123", "name": "John Doe"}'
```

**Login:**
```bash
curl -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Returns:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "...",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

**Verify Token:**
```bash
curl http://localhost:3000/auth/verify \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### HBCM Simulation (Proxied to FastAPI)

All `/api/hbcm/*` endpoints are proxied to FastAPI with authentication.

**Get Status:**
```bash
curl http://localhost:3000/api/hbcm/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Configure Simulation:**
```bash
curl -X POST http://localhost:3000/api/hbcm/config/simulation \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "initial_state": [0.0, 0.0, 1.0, 0.0],
    "t_start": 0.0,
    "t_end": 10.0,
    "dt": 0.001,
    "neural_params": {"a": 0.7, "b": 0.8, "c": 3.0},
    "cardiac_params": {"mu": 1.5, "omega": 1.0}
  }'
```

**Control Simulation:**
```bash
curl -X POST http://localhost:3000/api/hbcm/control \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "start"}'
```

### Historical Data (MongoDB)

**Get Simulation History:**
```bash
curl http://localhost:3000/api/simulations?limit=10 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Get Specific Simulation:**
```bash
curl http://localhost:3000/api/simulations/SIMULATION_ID \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Delete Simulation:**
```bash
curl -X DELETE http://localhost:3000/api/simulations/SIMULATION_ID \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Time-Series Data (InfluxDB)

**Query Time-Series:**
```bash
curl "http://localhost:3000/api/timeseries/query?startTime=2024-01-01T00:00:00Z&endTime=2024-01-02T00:00:00Z" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### OpenSim Integration

**Run Biomechanical Simulation:**
```bash
curl -X POST http://localhost:3000/api/opensim/run \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cardiac": {
      "x": [1.0, 0.9, ...],
      "y": [0.0, -0.1, ...]
    },
    "config": {
      "dt": 0.001,
      "opensimModel": "gait2392.osim"
    }
  }'

# Returns:
{
  "success": true,
  "motion_file": "/tmp/opensim_results/cardiac_motion_123456.mot",
  "output_file": "/tmp/opensim_results/biomechanics_123456.sto",
  "kinematics": {...},
  "forces": {...}
}
```

## WebSocket (Socket.io)

**Client Connection:**
```javascript
const socket = io('http://localhost:3000');

// Join simulation room
socket.emit('join-simulation', 'simulation');

// Receive real-time updates
socket.on('hbcm-update', (data) => {
  console.log('Neural v:', data.neural.v);
  console.log('Cardiac x:', data.cardiac.x);
});

// Send control commands
socket.emit('control-command', { command: 'start' });
```

## Development

### Running Tests

```bash
npm test
```

### Linting

```bash
npm run lint
```

### Project Structure

```
nodejs_gateway/
├── server.js              # Main Express server
├── package.json           # Dependencies and scripts
├── .env                   # Environment configuration
├── services/
│   └── opensimBridge.js   # OpenSim integration service
├── routes/                # API route handlers (future)
├── middleware/            # Custom middleware (future)
└── models/                # Mongoose models (future)
```

## Docker Deployment

**Build:**
```bash
docker build -t hbcm-gateway .
```

**Run:**
```bash
docker run -d -p 3000:3000 \
  -e MONGODB_URI=mongodb://mongo:27017/hbcm \
  -e FASTAPI_URL=http://fastapi:8000 \
  --name hbcm-gateway \
  hbcm-gateway
```

**Docker Compose:**
See `/docker-compose.yml` in project root for full stack deployment.

## Security Considerations

### Production Checklist

- [ ] Change `JWT_SECRET` to a strong random string
- [ ] Configure CORS to allow only trusted origins
- [ ] Enable HTTPS/TLS with valid certificates
- [ ] Set up rate limiting per user (not just per IP)
- [ ] Implement password strength requirements
- [ ] Add input validation and sanitization
- [ ] Set up logging and monitoring (ELK, Grafana, etc.)
- [ ] Configure MongoDB authentication
- [ ] Use environment variables for all secrets
- [ ] Set up backup and disaster recovery

### Rate Limits

- Auth endpoints: 5 requests / 15 minutes
- API endpoints: 100 requests / 15 minutes

Adjust in `server.js` as needed.

## Troubleshooting

### FastAPI Connection Failed

**Error:** `FastAPI backend unavailable`

**Solutions:**
- Ensure FastAPI is running: `cd ../web_control_panel/backend && uvicorn main:app`
- Check `FASTAPI_URL` in `.env`
- Verify firewall rules allow port 8000

### MongoDB Connection Error

**Error:** `MongoDB connection error`

**Solutions:**
- Start MongoDB: `docker run -d -p 27017:27017 mongo`
- Check `MONGODB_URI` in `.env`
- Verify MongoDB is accessible: `mongosh mongodb://localhost:27017`

### OpenSim Simulation Failed

**Error:** `OpenSim executable not found`

**Solutions:**
- Install OpenSim: https://opensim.stanford.edu/
- Add OpenSim to PATH or set `OPENSIM_BIN` in `.env`
- Verify installation: `opensim-cmd --version`

### WebSocket Not Connecting

**Error:** Socket.io connection fails

**Solutions:**
- Check FastAPI WebSocket is running
- Verify `FASTAPI_WS_URL` in `.env`
- Check firewall allows WebSocket connections
- Ensure CORS is configured correctly

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m "Add amazing feature"`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/STLNFTART/Multi-Heart-Model/issues
- Documentation: See `/docs/NODERED_NODEJS_INTEGRATION.md`

## Related Documentation

- **HBCM Architecture**: `/docs/ARCHITECTURE_OVERVIEW.md`
- **OpenSim Integration**: `/docs/NODERED_NODEJS_INTEGRATION.md`
- **FastAPI Backend**: `/web_control_panel/backend/README.md`
- **Quick Reference**: `/docs/QUICK_REFERENCE.md`
