FROM node:18-slim

# Install Python for Python bridge
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies
COPY ../../requirements_web_panel.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy Multi-Heart-Model Python code
COPY ../../src /app/src
COPY ../../bci_integration /app/bci_integration
COPY ../../web_control_panel /app/web_control_panel
COPY ../../run_simulation.py /app/

# Copy Node.js application
COPY package*.json ./
RUN npm ci --only=production

COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Run
CMD ["node", "server.js"]
