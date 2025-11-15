#!/bin/bash
#
# Node-RED Setup Script for Multi-Heart-Model
# Phase 1: Basic Installation and Configuration
#
# Author: Multi-Heart-Model Team
# Date: 2025-11-15
#

set -e  # Exit on error

echo "=========================================="
echo "Node-RED Setup for Multi-Heart-Model"
echo "Phase 1: Basic Installation"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Node.js version
echo -e "${YELLOW}[1/6] Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js 16+ from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo -e "${RED}Error: Node.js version must be 16 or higher${NC}"
    echo "Current version: $(node -v)"
    exit 1
fi

echo -e "${GREEN}✓ Node.js $(node -v) detected${NC}"
echo ""

# Check if Node-RED is already installed
echo -e "${YELLOW}[2/6] Checking Node-RED installation...${NC}"
if command -v node-red &> /dev/null; then
    echo -e "${GREEN}✓ Node-RED is already installed: $(node-red --version)${NC}"
else
    echo "Installing Node-RED globally..."
    npm install -g --unsafe-perm node-red
    echo -e "${GREEN}✓ Node-RED installed successfully${NC}"
fi
echo ""

# Install Node-RED dashboard and additional nodes
echo -e "${YELLOW}[3/6] Installing Node-RED dashboard and nodes...${NC}"
cd "$(dirname "$0")"

# Install local dependencies
echo "Installing dashboard nodes..."
npm install

echo -e "${GREEN}✓ Dashboard nodes installed${NC}"
echo ""

# Create settings.js if it doesn't exist
echo -e "${YELLOW}[4/6] Creating Node-RED configuration...${NC}"
if [ ! -f "settings.js" ]; then
    echo "Generating settings.js..."
    cat > settings.js << 'EOF'
module.exports = {
    uiPort: process.env.PORT || 1880,
    mqttReconnectTime: 15000,
    serialReconnectTime: 15000,
    debugMaxLength: 1000,

    functionGlobalContext: {
        // Enable access to environment variables
    },

    // Uncomment to enable authentication
    // adminAuth: {
    //     type: "credentials",
    //     users: [{
    //         username: "admin",
    //         password: "$2a$08$zZWtXTja0fB1pzD4sHCMyOCMYz2Z6dNbM6tl8sJogENOMcxWV9DN.",
    //         permissions: "*"
    //     }]
    // },

    httpNodeRoot: '/api',
    httpAdminRoot: '/admin',
    httpStatic: '/home/pi/static',

    ui: { path: "ui" },

    logging: {
        console: {
            level: "info",
            metrics: false,
            audit: false
        }
    },

    editorTheme: {
        projects: {
            enabled: false
        },
        page: {
            title: "HBCM Node-RED"
        },
        header: {
            title: "Multi-Heart-Model Control"
        }
    }
}
EOF
    echo -e "${GREEN}✓ settings.js created${NC}"
else
    echo -e "${GREEN}✓ settings.js already exists${NC}"
fi
echo ""

# Verify flows.json exists
echo -e "${YELLOW}[5/6] Verifying flows configuration...${NC}"
if [ -f "flows.json" ]; then
    echo -e "${GREEN}✓ flows.json found ($(wc -l < flows.json) lines)${NC}"
else
    echo -e "${RED}Warning: flows.json not found${NC}"
    echo "The example flows file is missing. You'll need to import flows manually."
fi
echo ""

# Check if FastAPI is running
echo -e "${YELLOW}[6/6] Checking FastAPI backend...${NC}"
if curl -s http://localhost:8000/api/status > /dev/null 2>&1; then
    echo -e "${GREEN}✓ FastAPI backend is running on port 8000${NC}"
else
    echo -e "${YELLOW}⚠ FastAPI backend not detected on port 8000${NC}"
    echo "  Make sure to start the FastAPI backend before using Node-RED:"
    echo "  cd web_control_panel/backend && uvicorn main:app --reload"
fi
echo ""

# Setup complete
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start FastAPI backend (if not running):"
echo "   cd ../web_control_panel/backend"
echo "   uvicorn main:app --reload"
echo ""
echo "2. Start Node-RED:"
echo "   cd nodered"
echo "   npm start"
echo "   (or: node-red --userDir .)"
echo ""
echo "3. Access the dashboards:"
echo "   - Node-RED Editor: http://localhost:1880"
echo "   - HBCM Dashboard:  http://localhost:1880/ui"
echo ""
echo "4. In the FastAPI backend, start a simulation to see live data"
echo ""
echo "For troubleshooting, see README.md in this directory"
echo ""
