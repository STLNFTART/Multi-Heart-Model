/**
 * Multi-Heart-Model Node.js API Server
 *
 * Provides clean REST API for cardiac simulations, designed to integrate with:
 * - Node-RED for workflow orchestration
 * - MCP for LLM tool access
 * - MQTT/WebHooks for event-driven architecture
 * - TAK for tactical data exchange
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const { PythonShell } = require('python-shell');
const mqtt = require('mqtt');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const MQTT_BROKER = process.env.MQTT_BROKER || 'mqtt://localhost:1883';

// =============================================================================
// Middleware
// =============================================================================

app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('combined'));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use('/api/', limiter);

// =============================================================================
// MQTT Client for Event Publishing
// =============================================================================

let mqttClient = null;
if (process.env.ENABLE_MQTT === 'true') {
  mqttClient = mqtt.connect(MQTT_BROKER);

  mqttClient.on('connect', () => {
    console.log('✓ Connected to MQTT broker:', MQTT_BROKER);
  });

  mqttClient.on('error', (err) => {
    console.error('MQTT error:', err);
  });
}

function publishEvent(topic, payload) {
  if (mqttClient && mqttClient.connected) {
    mqttClient.publish(topic, JSON.stringify(payload));
    console.log(`Published to ${topic}:`, payload);
  }
}

// =============================================================================
// Simulation State Management
// =============================================================================

const simulations = new Map(); // Store active simulations

class SimulationJob {
  constructor(config) {
    this.id = uuidv4();
    this.config = config;
    this.status = 'pending';
    this.result = null;
    this.error = null;
    this.startTime = null;
    this.endTime = null;
    this.progress = 0;
  }

  toJSON() {
    return {
      id: this.id,
      status: this.status,
      config: this.config,
      result: this.result,
      error: this.error,
      startTime: this.startTime,
      endTime: this.endTime,
      progress: this.progress,
      duration: this.endTime && this.startTime
        ? this.endTime - this.startTime
        : null
    };
  }
}

// =============================================================================
// Python Bridge Functions
// =============================================================================

async function runHeartSimulation(config) {
  return new Promise((resolve, reject) => {
    const options = {
      mode: 'json',
      pythonPath: process.env.PYTHON_PATH || 'python3',
      pythonOptions: ['-u'],
      scriptPath: '../../', // Adjust based on your structure
      args: [JSON.stringify(config)]
    };

    PythonShell.run('run_simulation.py', options, (err, results) => {
      if (err) {
        reject(err);
      } else {
        resolve(results[0]);
      }
    });
  });
}

async function runOpenSimCoSimulation(config) {
  return new Promise((resolve, reject) => {
    const options = {
      mode: 'json',
      pythonPath: process.env.PYTHON_PATH || 'python3',
      pythonOptions: ['-u'],
      scriptPath: '../../integrations/opensim/',
      args: [JSON.stringify(config)]
    };

    PythonShell.run('run_cosimulation.py', options, (err, results) => {
      if (err) {
        reject(err);
      } else {
        resolve(results[0]);
      }
    });
  });
}

// =============================================================================
// API Routes
// =============================================================================

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    mqtt: mqttClient ? mqttClient.connected : false,
    activeSims: simulations.size
  });
});

// Get API info
app.get('/api', (req, res) => {
  res.json({
    name: 'Multi-Heart-Model API',
    version: '1.0.0',
    description: 'REST API for cardiac simulations with BCI and OpenSim integration',
    endpoints: {
      health: 'GET /health',
      simulations: {
        list: 'GET /api/simulations',
        create: 'POST /api/simulations',
        get: 'GET /api/simulations/:id',
        status: 'GET /api/simulations/:id/status',
        delete: 'DELETE /api/simulations/:id'
      },
      heart: {
        run: 'POST /api/heart/run',
        validate: 'POST /api/heart/validate'
      },
      opensim: {
        cosimulate: 'POST /api/opensim/cosimulate',
        export: 'POST /api/opensim/export'
      },
      bci: {
        stream: 'POST /api/bci/stream',
        process: 'POST /api/bci/process'
      }
    }
  });
});

// List all simulations
app.get('/api/simulations', (req, res) => {
  const sims = Array.from(simulations.values()).map(sim => sim.toJSON());
  res.json({
    count: sims.length,
    simulations: sims
  });
});

// Create new simulation
app.post('/api/simulations', async (req, res) => {
  try {
    const config = req.body;

    // Validate config (simplified - add Joi validation in production)
    if (!config.duration || !config.dt) {
      return res.status(400).json({
        error: 'Missing required parameters: duration, dt'
      });
    }

    const job = new SimulationJob(config);
    simulations.set(job.id, job);

    // Run simulation asynchronously
    job.status = 'running';
    job.startTime = Date.now();

    publishEvent('simulation/started', { id: job.id, config });

    // Run in background
    (async () => {
      try {
        const result = await runHeartSimulation(config);
        job.result = result;
        job.status = 'completed';
        job.endTime = Date.now();
        job.progress = 100;

        publishEvent('simulation/completed', {
          id: job.id,
          duration: job.endTime - job.startTime,
          metrics: extractMetrics(result)
        });

      } catch (error) {
        job.error = error.message;
        job.status = 'failed';
        job.endTime = Date.now();

        publishEvent('simulation/failed', {
          id: job.id,
          error: error.message
        });
      }
    })();

    res.status(202).json({
      message: 'Simulation started',
      id: job.id,
      status: job.status
    });

  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get simulation by ID
app.get('/api/simulations/:id', (req, res) => {
  const sim = simulations.get(req.params.id);

  if (!sim) {
    return res.status(404).json({ error: 'Simulation not found' });
  }

  res.json(sim.toJSON());
});

// Get simulation status
app.get('/api/simulations/:id/status', (req, res) => {
  const sim = simulations.get(req.params.id);

  if (!sim) {
    return res.status(404).json({ error: 'Simulation not found' });
  }

  res.json({
    id: sim.id,
    status: sim.status,
    progress: sim.progress,
    startTime: sim.startTime,
    endTime: sim.endTime
  });
});

// Delete simulation
app.delete('/api/simulations/:id', (req, res) => {
  const deleted = simulations.delete(req.params.id);

  if (!deleted) {
    return res.status(404).json({ error: 'Simulation not found' });
  }

  res.json({ message: 'Simulation deleted' });
});

// Quick heart simulation run (synchronous for Node-RED)
app.post('/api/heart/run', async (req, res) => {
  try {
    const config = {
      duration: req.body.duration || 10.0,
      dt: req.body.dt || 0.001,
      neural_params: req.body.neural_params || {},
      cardiac_params: req.body.cardiac_params || {},
      coupling_params: req.body.coupling_params || {}
    };

    const result = await runHeartSimulation(config);

    const metrics = extractMetrics(result);

    // Publish to MQTT
    publishEvent('heart/simulation/result', {
      timestamp: new Date().toISOString(),
      metrics
    });

    res.json({
      success: true,
      metrics,
      raw_result: result
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Validate heart configuration
app.post('/api/heart/validate', (req, res) => {
  const config = req.body;

  const errors = [];

  // Validation rules
  if (config.duration && (config.duration <= 0 || config.duration > 1000)) {
    errors.push('Duration must be between 0 and 1000 seconds');
  }

  if (config.dt && (config.dt <= 0 || config.dt > 1)) {
    errors.push('Timestep must be between 0 and 1 second');
  }

  if (errors.length > 0) {
    return res.status(400).json({
      valid: false,
      errors
    });
  }

  res.json({ valid: true });
});

// OpenSim co-simulation
app.post('/api/opensim/cosimulate', async (req, res) => {
  try {
    const config = req.body;

    const result = await runOpenSimCoSimulation(config);

    publishEvent('opensim/cosimulation/result', {
      timestamp: new Date().toISOString(),
      metrics: extractMetrics(result)
    });

    res.json({
      success: true,
      result
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// BCI stream endpoint
app.post('/api/bci/stream', (req, res) => {
  // This would integrate with BCI adapters
  const config = req.body;

  // Publish to MQTT for Node-RED to pick up
  publishEvent('bci/stream/start', config);

  res.json({
    message: 'BCI stream initiated',
    stream_id: uuidv4()
  });
});

// =============================================================================
// Helper Functions
// =============================================================================

function extractMetrics(result) {
  if (!result || !result.trajectory) {
    return {};
  }

  // Extract key metrics from simulation result
  const neural_v = result.trajectory.map(t => t.state[0]);
  const cardiac_x = result.trajectory.map(t => t.state[2]);

  return {
    neural: {
      mean: average(neural_v),
      max: Math.max(...neural_v),
      min: Math.min(...neural_v),
      std: standardDeviation(neural_v)
    },
    cardiac: {
      mean: average(cardiac_x),
      max: Math.max(...cardiac_x),
      min: Math.min(...cardiac_x),
      std: standardDeviation(cardiac_x)
    },
    duration: result.duration,
    n_steps: result.trajectory.length
  };
}

function average(arr) {
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function standardDeviation(arr) {
  const avg = average(arr);
  const squareDiffs = arr.map(value => Math.pow(value - avg, 2));
  return Math.sqrt(average(squareDiffs));
}

// =============================================================================
// WebSocket Server for Real-time Updates
// =============================================================================

const wss = new WebSocket.Server({ noServer: true });

wss.on('connection', (ws) => {
  console.log('WebSocket client connected');

  ws.on('message', (message) => {
    console.log('Received:', message);
  });

  ws.on('close', () => {
    console.log('WebSocket client disconnected');
  });
});

// Upgrade HTTP server to handle WebSocket
const server = app.listen(PORT, () => {
  console.log(`✓ Multi-Heart-Model API listening on port ${PORT}`);
  console.log(`✓ Health check: http://localhost:${PORT}/health`);
  console.log(`✓ API docs: http://localhost:${PORT}/api`);
});

server.on('upgrade', (request, socket, head) => {
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit('connection', ws, request);
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    if (mqttClient) {
      mqttClient.end();
    }
  });
});

module.exports = app; // For testing
