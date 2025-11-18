#!/bin/bash
#
# Phase 2 Stop Script
# Cleanly stops all services started by start_phase2.sh
#
# Author: Multi-Heart-Model Team
# Date: 2025-11-15
#

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "Phase 2: Stopping All Services"
echo "=========================================="
echo ""

# Stop Node-RED
echo -e "${YELLOW}Stopping Node-RED...${NC}"
if [ -f /tmp/nodered.pid ]; then
    PID=$(cat /tmp/nodered.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo -e "${GREEN}✓ Node-RED stopped (PID: $PID)${NC}"
        rm /tmp/nodered.pid
    else
        echo -e "${YELLOW}Node-RED not running${NC}"
        rm /tmp/nodered.pid
    fi
else
    pkill -f "node-red" && echo -e "${GREEN}✓ Node-RED stopped${NC}" || echo -e "${YELLOW}Node-RED not running${NC}"
fi

# Stop Node.js Gateway
echo -e "${YELLOW}Stopping Node.js Gateway...${NC}"
if [ -f /tmp/nodejs-gateway.pid ]; then
    PID=$(cat /tmp/nodejs-gateway.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo -e "${GREEN}✓ Node.js Gateway stopped (PID: $PID)${NC}"
        rm /tmp/nodejs-gateway.pid
    else
        echo -e "${YELLOW}Node.js Gateway not running${NC}"
        rm /tmp/nodejs-gateway.pid
    fi
else
    pkill -f "node.*server.js" && echo -e "${GREEN}✓ Node.js Gateway stopped${NC}" || echo -e "${YELLOW}Node.js Gateway not running${NC}"
fi

# Stop FastAPI
echo -e "${YELLOW}Stopping FastAPI Backend...${NC}"
if [ -f /tmp/fastapi.pid ]; then
    PID=$(cat /tmp/fastapi.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo -e "${GREEN}✓ FastAPI stopped (PID: $PID)${NC}"
        rm /tmp/fastapi.pid
    else
        echo -e "${YELLOW}FastAPI not running${NC}"
        rm /tmp/fastapi.pid
    fi
else
    pkill -f "uvicorn main:app" && echo -e "${GREEN}✓ FastAPI stopped${NC}" || echo -e "${YELLOW}FastAPI not running${NC}"
fi

# Optional: Stop Docker containers
echo ""
echo -e "${YELLOW}Docker containers (MongoDB, InfluxDB) are still running.${NC}"
echo "To stop them:"
echo "  docker stop hbcm-mongo"
echo "  docker stop hbcm-influx"
echo ""
echo "To remove them:"
echo "  docker rm hbcm-mongo"
echo "  docker rm hbcm-influx"
echo ""

echo "=========================================="
echo -e "${GREEN}All Services Stopped!${NC}"
echo "=========================================="
echo ""
