#!/bin/bash
#
# Phase 2 Startup Script
# Starts all required services for authenticated Node-RED integration
#
# Services Started:
# 1. MongoDB (Docker)
# 2. InfluxDB (Docker) - optional
# 3. FastAPI Backend (Port 8000)
# 4. Node.js Gateway (Port 3000)
# 5. Node-RED (Port 1880)
#
# Author: Multi-Heart-Model Team
# Date: 2025-11-15
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Phase 2: Starting All Services"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if MongoDB is running
echo -e "${YELLOW}[1/5] Checking MongoDB...${NC}"
if ! docker ps | grep -q mongo; then
    echo "Starting MongoDB container..."
    docker run -d -p 27017:27017 --name hbcm-mongo mongo:latest || {
        echo -e "${YELLOW}MongoDB container may already exist but stopped. Starting...${NC}"
        docker start hbcm-mongo || echo -e "${YELLOW}Could not start MongoDB. Will try to continue...${NC}"
    }
    sleep 2
    echo -e "${GREEN}✓ MongoDB started${NC}"
else
    echo -e "${GREEN}✓ MongoDB already running${NC}"
fi
echo ""

# Check InfluxDB (optional)
echo -e "${YELLOW}[2/5] Checking InfluxDB (optional)...${NC}"
if ! docker ps | grep -q influxdb; then
    echo "InfluxDB not running (this is optional for Phase 2)"
    echo -e "${BLUE}To start InfluxDB: docker run -d -p 8086:8086 --name hbcm-influx influxdb:2.7${NC}"
else
    echo -e "${GREEN}✓ InfluxDB running${NC}"
fi
echo ""

# Start FastAPI Backend
echo -e "${YELLOW}[3/5] Starting FastAPI Backend...${NC}"
cd "$PROJECT_ROOT/web_control_panel/backend"

if pgrep -f "uvicorn main:app" > /dev/null; then
    echo -e "${GREEN}✓ FastAPI already running${NC}"
else
    echo "Starting FastAPI on port 8000..."
    nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &
    FASTAPI_PID=$!
    echo $FASTAPI_PID > /tmp/fastapi.pid
    sleep 3

    if curl -s http://localhost:8000/api/status > /dev/null 2>&1; then
        echo -e "${GREEN}✓ FastAPI started (PID: $FASTAPI_PID)${NC}"
        echo "  Log: /tmp/fastapi.log"
    else
        echo -e "${RED}✗ FastAPI failed to start. Check /tmp/fastapi.log${NC}"
        exit 1
    fi
fi
echo ""

# Start Node.js Gateway
echo -e "${YELLOW}[4/5] Starting Node.js Gateway...${NC}"
cd "$PROJECT_ROOT/nodejs_gateway"

if pgrep -f "node.*server.js" > /dev/null; then
    echo -e "${GREEN}✓ Node.js Gateway already running${NC}"
else
    echo "Starting Node.js Gateway on port 3000..."

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "Installing Node.js dependencies..."
        npm install
    fi

    nohup node server.js > /tmp/nodejs-gateway.log 2>&1 &
    NODEJS_PID=$!
    echo $NODEJS_PID > /tmp/nodejs-gateway.pid
    sleep 3

    if curl -s http://localhost:3000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Node.js Gateway started (PID: $NODEJS_PID)${NC}"
        echo "  Log: /tmp/nodejs-gateway.log"
    else
        echo -e "${RED}✗ Node.js Gateway failed to start. Check /tmp/nodejs-gateway.log${NC}"
        exit 1
    fi
fi
echo ""

# Start Node-RED
echo -e "${YELLOW}[5/5] Starting Node-RED...${NC}"
cd "$SCRIPT_DIR"

if pgrep -f "node-red" > /dev/null; then
    echo -e "${GREEN}✓ Node-RED already running${NC}"
else
    echo "Starting Node-RED on port 1880..."

    # Use Phase 2 flows
    if [ -f "flows_phase2.json" ]; then
        cp flows_phase2.json flows.json
        echo "Using Phase 2 flows (with authentication)"
    fi

    nohup node-red --userDir . > /tmp/nodered.log 2>&1 &
    NODERED_PID=$!
    echo $NODERED_PID > /tmp/nodered.pid
    sleep 5

    if curl -s http://localhost:1880 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Node-RED started (PID: $NODERED_PID)${NC}"
        echo "  Log: /tmp/nodered.log"
    else
        echo -e "${RED}✗ Node-RED failed to start. Check /tmp/nodered.log${NC}"
        exit 1
    fi
fi
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}All Services Started!${NC}"
echo "=========================================="
echo ""
echo "Access Points:"
echo -e "  ${BLUE}FastAPI Backend:${NC}     http://localhost:8000"
echo -e "  ${BLUE}Node.js Gateway:${NC}     http://localhost:3000"
echo -e "  ${BLUE}Node-RED Editor:${NC}     http://localhost:1880"
echo -e "  ${BLUE}HBCM Dashboard:${NC}      http://localhost:1880/ui"
echo ""
echo "Next Steps:"
echo "  1. Create a user account:"
echo "     curl -X POST http://localhost:3000/auth/register \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"email\":\"demo@example.com\",\"password\":\"demo123\",\"name\":\"Demo User\"}'"
echo ""
echo "  2. Access the dashboard: http://localhost:1880/ui"
echo ""
echo "  3. Login with your credentials on the Login tab"
echo ""
echo "  4. Switch to HBCM Monitor tab to view real-time data"
echo ""
echo "Logs:"
echo "  FastAPI:     tail -f /tmp/fastapi.log"
echo "  Node.js:     tail -f /tmp/nodejs-gateway.log"
echo "  Node-RED:    tail -f /tmp/nodered.log"
echo ""
echo "To stop all services: ./stop_phase2.sh"
echo ""
