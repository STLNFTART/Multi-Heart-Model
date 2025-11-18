# Multi-Heart-Model: 5-Minute Quick Start Guide

**Get the Multi-Heart-Model system running in 5 minutes with Docker Compose.**

<img src="docs/architecture_diagram.svg" alt="Architecture" width="800"/>

---

## Prerequisites

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Git**
- **8GB RAM** minimum (16GB recommended)
- **5GB free disk space**

### Quick Install (if needed)

```bash
# Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Docker Compose (already included in modern Docker)
docker compose version
```

---

## 5-Minute Setup

### Step 1: Clone Repository (30 seconds)

```bash
git clone https://github.com/STLNFTART/Multi-Heart-Model.git
cd Multi-Heart-Model
```

### Step 2: Start Services (2 minutes)

```bash
# Start all services
docker compose up -d

# Watch startup logs
docker compose logs -f
```

**Services Starting:**
- ✅ Redis (caching layer)
- ✅ FastAPI Backend (Python API)
- ✅ Node-RED Dashboard (visual interface)

### Step 3: Verify Services (30 seconds)

```bash
# Check all services are healthy
docker compose ps

# Expected output:
# NAME                     STATUS
# multiheart-redis-dev     Up (healthy)
# multiheart-api-dev       Up (healthy)
# multiheart-nodered-dev   Up
```

### Step 4: Access Dashboards (30 seconds)

Open in your browser:

1. **Node-RED Dashboard**: http://localhost:1880
   - Visual workflow editor
   - Real-time HBCM monitoring
   - Drag-and-drop interface

2. **API Documentation**: http://localhost:8000/docs
   - Interactive API explorer
   - Try endpoints live
   - Full OpenAPI spec

3. **API Health Check**: http://localhost:8000/health
   - System status
   - Service connectivity

### Step 5: Run First Simulation (1 minute)

```bash
# Option 1: Python simulation
python examples/microprocessor_motorhand_demo.py

# Option 2: Space integration demo
python examples/space_integration_demo.py

# Option 3: API test
curl http://localhost:8000/api/simulate -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 10.0,
    "dt": 0.001,
    "neural_params": {"a": 0.7, "b": 0.8},
    "cardiac_params": {"mu": 1.5, "omega": 1.0}
  }'
```

---

## What You Just Deployed

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
├────────────┬────────────────────────────────────┬───────────────┤
│  Node-RED  │      FastAPI Docs                  │  Web Control  │
│   :1880    │       :8000/docs                   │    Panel      │
└────────────┴────────────────────────────────────┴───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (:8000)                    │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │     HBCM     │  MotorHand   │    OpenSim   │    Space     │ │
│  │  Simulation  │   Control    │  Integration │     API      │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Core Models (Python)                        │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   Cardiac    │    Neural    │   Coupling   │  Primal      │ │
│  │  Van der Pol │  FitzHugh-   │     HBCM     │   Logic      │ │
│  │              │   Nagumo     │              │  Processor   │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer (Redis :6379)                     │
│  - Caching  - Rate Limiting  - Pub/Sub  - Session Storage      │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Port | Status Endpoint |
|-----------|---------|------|-----------------|
| **FastAPI Backend** | Python API, simulations | 8000 | http://localhost:8000/health |
| **Node-RED** | Visual dashboard, workflows | 1880 | http://localhost:1880 |
| **Redis** | Caching, rate limiting | 6379 | `redis-cli ping` |

---

## Next Steps

### 1. Explore the API

```bash
# Health check
curl http://localhost:8000/health

# Get space environment context
curl -X POST http://localhost:8000/api/space/env-context \
  -H "Content-Type: application/json" \
  -d '{"latitude": 38.63, "longitude": -90.20}'

# Get communications profile
curl -X POST http://localhost:8000/api/space/comms-profile \
  -H "Content-Type: application/json" \
  -d '{"severity": 0.3}'

# Run HBCM simulation
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 10.0,
    "dt": 0.001
  }'
```

### 2. Explore Node-RED

1. Go to http://localhost:1880
2. Click hamburger menu (top-right) → **Import** → **Examples**
3. Import "HBCM Real-Time Dashboard"
4. Click **Deploy**
5. Open dashboard at http://localhost:1880/ui

### 3. Run Performance Benchmarks

```bash
# HBCM performance benchmarks
python -m benchmarks.hbcm_benchmark

# Control loop latency benchmarks
python -m benchmarks.control_loop_benchmark

# Run all benchmarks with HTML report
python -m benchmarks.run_all --save-report benchmarks.html
```

### 4. View Architecture Documentation

```bash
# Quick reference
cat docs/QUICK_REFERENCE.md

# Full architecture
cat docs/ARCHITECTURE_OVERVIEW.md

# Space API integration
cat docs/SPACE_INTEGRATION.md
```

---

## Production Deployment

For production deployment with security, monitoring, and high availability:

```bash
# Generate TLS certificates
cd deployment/security
./generate_certificates.sh

# Configure environment
cp deployment/security/production.env.example deployment/security/production.env
# Edit production.env with your values

# Create MQTT passwords
mosquitto_passwd -c deployment/security/mosquitto_passwd admin
mosquitto_passwd deployment/security/mosquitto_passwd hbcm_service
# ... (add other users)

# Start production stack
docker compose -f deployment/docker-compose.production.yml up -d
```

**Production stack includes:**
- ✅ TLS/SSL encryption (MQTT, HTTPS)
- ✅ Client certificate authentication
- ✅ Rate limiting & DDoS protection
- ✅ PostgreSQL database
- ✅ NGINX reverse proxy
- ✅ Prometheus monitoring
- ✅ Grafana visualization
- ✅ Automated backups
- ✅ Health checks & auto-restart

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker daemon
sudo systemctl status docker

# View detailed logs
docker compose logs api
docker compose logs redis
docker compose logs nodered

# Restart services
docker compose restart
```

### Port Conflicts

```bash
# Check if ports are in use
sudo lsof -i :8000  # API
sudo lsof -i :1880  # Node-RED
sudo lsof -i :6379  # Redis

# Change ports in docker-compose.yml if needed
```

### API Not Responding

```bash
# Check API health
curl http://localhost:8000/health

# View API logs
docker compose logs -f api

# Restart API
docker compose restart api
```

### Out of Memory

```bash
# Check container memory usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → Increase to 8GB+

# Or add limits to docker-compose.yml
```

### Redis Connection Error

```bash
# Test Redis connectivity
docker compose exec api sh -c "redis-cli -h redis ping"

# Restart Redis
docker compose restart redis
```

---

## System Requirements

### Minimum (Development)
- **CPU**: 2 cores
- **RAM**: 8GB
- **Disk**: 5GB free space
- **OS**: Linux, macOS, Windows with WSL2

### Recommended (Development)
- **CPU**: 4+ cores
- **RAM**: 16GB
- **Disk**: 10GB free space (SSD)
- **OS**: Ubuntu 22.04 LTS

### Production
- **CPU**: 8+ cores
- **RAM**: 32GB
- **Disk**: 100GB SSD
- **Network**: 1Gbps+
- **OS**: Ubuntu 22.04 LTS or RHEL 8+

---

## Performance Targets

Based on benchmark results:

| Metric | Target | Typical |
|--------|--------|---------|
| **HBCM Step Latency** | <1ms | 0.05-0.15ms |
| **Control Loop Latency** | <100ms | 0.5-2ms |
| **API Response Time** | <50ms | 10-30ms |
| **Throughput** | >1000 Hz | 10,000+ Hz |
| **Real-Time Factor** | >1.0x | 100-1000x |

See `benchmarks/` for detailed performance validation.

---

## Use Cases

### 1. Prosthetic Control
- Real-time control loop (<100ms latency)
- MotorHandPro integration
- Primal Logic Processor
- Hardware control via QUANT

### 2. Physiological Modeling
- Heart-brain coupling simulation
- Delay-differential equations
- Multi-organ systems
- Drug toxicity screening

### 3. Space Weather Integration
- NASA POWER environmental data
- Starlink network modeling
- Scenario generation
- Stress testing

### 4. Biomechanical Coupling
- OpenSim integration
- Motion capture data
- Force feedback
- Rehabilitation systems

### 5. Tactical Awareness (TAK)
- Soldier health monitoring
- Real-time vitals
- Alert distribution
- Mission planning

---

## Getting Help

### Documentation
- **Architecture**: `docs/ARCHITECTURE_OVERVIEW.md`
- **Quick Reference**: `docs/QUICK_REFERENCE.md`
- **Space Integration**: `docs/SPACE_INTEGRATION.md`
- **API Guide**: http://localhost:8000/docs

### Support
- **Issues**: https://github.com/STLNFTART/Multi-Heart-Model/issues
- **Discussions**: https://github.com/STLNFTART/Multi-Heart-Model/discussions

### Community
- Examples: `examples/`
- Tests: `tests/`
- Benchmarks: `benchmarks/`

---

## What's Next?

### Immediate (Day 1)
1. ✅ Run all example scripts
2. ✅ Explore API endpoints
3. ✅ Run performance benchmarks
4. ✅ Review architecture docs

### Short Term (Week 1)
1. Integrate with your hardware
2. Customize simulation parameters
3. Add custom visualizations in Node-RED
4. Deploy to staging environment

### Medium Term (Month 1)
1. Production deployment with TLS
2. Custom model development
3. Integration with external systems
4. Performance optimization

### Partnership Applications
- **Tesla/X**: Neuralink integration, Optimus robot health monitoring
- **Medical**: Wearable monitors, surgical robots, rehabilitation systems
- **Defense**: Soldier monitoring, exoskeleton control, medic overlays
- **Research**: Multi-organ modeling, drug screening, systems biology

---

## License

MIT License - See `LICENSE` file

---

## Citation

If you use Multi-Heart-Model in your research, please cite:

```bibtex
@software{multiheart2025,
  title={Multi-Heart-Model: Production-Ready Heart-Brain Coupling System},
  author={Multi-Heart-Model Team},
  year={2025},
  url={https://github.com/STLNFTART/Multi-Heart-Model}
}
```

---

**System Status**: ✅ Production Ready

**Last Updated**: 2025-11-15

**Version**: 1.0.0
