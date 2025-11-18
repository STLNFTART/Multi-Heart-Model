#!/usr/bin/env node
/**
 * Multi-Heart-Model Production API Server
 * Node.js/Express backend with PostgreSQL, Redis, MQTT integration
 */

require('dotenv').config();
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const { Pool } = require('pg');
const redis = require('redis');
const mqtt = require('mqtt');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');
const promClient = require('prom-client');

// Configuration
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'jwt_super_secret_key';

// Initialize Express
const app = express();

// Prometheus metrics
const register = new promClient.Registry();
promClient.collectDefaultMetrics({ register });

const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_ms',
  help: 'Duration of HTTP requests in ms',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register]
});

const mqttMessageCounter = new promClient.Counter({
  name: 'mqtt_messages_total',
  help: 'Total MQTT messages processed',
  labelNames: ['topic'],
  registers: [register]
});

const simulationCounter = new promClient.Counter({
  name: 'simulations_total',
  help: 'Total simulations created',
  labelNames: ['type', 'status'],
  registers: [register]
});

// PostgreSQL connection pool
const pgPool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

pgPool.on('error', (err) => {
  console.error('Unexpected PostgreSQL error:', err);
});

// Redis client
const redisClient = redis.createClient({
  url: process.env.REDIS_URL,
  socket: {
    reconnectStrategy: (retries) => Math.min(retries * 50, 500)
  }
});

redisClient.on('error', (err) => console.error('Redis error:', err));
redisClient.on('connect', () => console.log('Redis connected'));

// MQTT client
const mqttClient = mqtt.connect(process.env.MQTT_URL || 'mqtt://mqtt:1883', {
  clientId: `api_server_${uuidv4()}`,
  clean: true,
  reconnectPeriod: 1000,
});

mqttClient.on('connect', () => {
  console.log('MQTT connected');
  mqttClient.subscribe(['simulation/#', 'bci/#', 'device/#', 'control/#']);
});

mqttClient.on('message', async (topic, message) => {
  try {
    const payload = JSON.parse(message.toString());
    mqttMessageCounter.inc({ topic });

    // Store in database based on topic
    if (topic.startsWith('simulation/')) {
      await handleSimulationMessage(topic, payload);
    } else if (topic.startsWith('bci/')) {
      await handleBCIMessage(topic, payload);
    } else if (topic.startsWith('device/')) {
      await handleDeviceMessage(topic, payload);
    }

    // Cache in Redis
    await redisClient.setEx(`mqtt:${topic}:latest`, 3600, JSON.stringify(payload));
  } catch (error) {
    console.error('Error processing MQTT message:', error);
  }
});

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use('/api/', limiter);

// Request timing middleware
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    httpRequestDuration.observe(
      { method: req.method, route: req.route?.path || req.path, status_code: res.statusCode },
      duration
    );
  });
  next();
});

// Authentication middleware
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid or expired token' });
    }
    req.user = user;
    next();
  });
};

// Helper functions
async function handleSimulationMessage(topic, payload) {
  const parts = topic.split('/');
  if (parts.length >= 3 && parts[2] === 'data') {
    const simulationId = parts[1];

    // Insert simulation data
    await pgPool.query(
      `INSERT INTO simulation_data (time, simulation_id, timestep, neural_v, neural_w, cardiac_x, cardiac_y, metadata)
       VALUES (NOW(), $1, $2, $3, $4, $5, $6, $7)`,
      [simulationId, payload.timestep, payload.neural?.v, payload.neural?.w,
       payload.cardiac?.x, payload.cardiac?.y, JSON.stringify(payload.metadata || {})]
    );
  }
}

async function handleBCIMessage(topic, payload) {
  const parts = topic.split('/');
  if (parts.length >= 3 && parts[2] === 'data') {
    const sessionId = parts[1];

    // Insert BCI data for each channel
    if (payload.channels && payload.data) {
      for (let i = 0; i < payload.channels.length; i++) {
        await pgPool.query(
          `INSERT INTO bci_data (time, session_id, channel_name, value, sample_number, metadata)
           VALUES (NOW(), $1, $2, $3, $4, $5)`,
          [sessionId, payload.channels[i], payload.data[i], payload.sample_number,
           JSON.stringify(payload.metadata || {})]
        );
      }
    }
  }
}

async function handleDeviceMessage(topic, payload) {
  const parts = topic.split('/');
  if (parts.length >= 2) {
    const deviceId = parts[1];

    // Update device last seen
    await pgPool.query(
      `UPDATE devices SET last_seen = NOW(), status = $1, metadata = $2 WHERE device_id = $3`,
      [payload.status || 'online', JSON.stringify(payload.metadata || {}), deviceId]
    );
  }
}

// Routes

// Health check
app.get('/health', async (req, res) => {
  try {
    await pgPool.query('SELECT 1');
    const redisOk = redisClient.isOpen;
    const mqttOk = mqttClient.connected;

    res.json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      services: {
        database: 'healthy',
        redis: redisOk ? 'healthy' : 'degraded',
        mqtt: mqttOk ? 'healthy' : 'degraded'
      }
    });
  } catch (error) {
    res.status(503).json({
      status: 'error',
      error: error.message
    });
  }
});

// Metrics endpoint for Prometheus
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// Authentication routes
app.post('/api/auth/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    const result = await pgPool.query(
      'SELECT * FROM users WHERE username = $1 AND is_active = true',
      [username]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const user = result.rows[0];
    const validPassword = await bcrypt.compare(password, user.password_hash);

    if (!validPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Update last login
    await pgPool.query(
      'UPDATE users SET last_login = NOW() WHERE id = $1',
      [user.id]
    );

    // Generate JWT
    const token = jwt.sign(
      { userId: user.id, username: user.username, role: user.role },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    res.json({
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        full_name: user.full_name,
        role: user.role
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Login failed' });
  }
});

app.post('/api/auth/register', async (req, res) => {
  try {
    const { username, email, password, full_name } = req.body;

    // Hash password
    const password_hash = await bcrypt.hash(password, 12);

    const result = await pgPool.query(
      `INSERT INTO users (username, email, password_hash, full_name, role)
       VALUES ($1, $2, $3, $4, 'user') RETURNING id, username, email, full_name, role`,
      [username, email, password_hash, full_name]
    );

    const user = result.rows[0];

    // Generate JWT
    const token = jwt.sign(
      { userId: user.id, username: user.username, role: user.role },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    res.status(201).json({
      token,
      user
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(400).json({ error: 'Registration failed' });
  }
});

// Simulation routes
app.get('/api/simulations', authenticateToken, async (req, res) => {
  try {
    const { type, status, limit = 50, offset = 0 } = req.query;

    let query = 'SELECT * FROM simulations WHERE user_id = $1';
    const params = [req.user.userId];

    if (type) {
      params.push(type);
      query += ` AND simulation_type = $${params.length}`;
    }

    if (status) {
      params.push(status);
      query += ` AND status = $${params.length}`;
    }

    params.push(limit, offset);
    query += ` ORDER BY created_at DESC LIMIT $${params.length - 1} OFFSET $${params.length}`;

    const result = await pgPool.query(query, params);

    res.json({
      simulations: result.rows,
      total: result.rowCount
    });
  } catch (error) {
    console.error('Error fetching simulations:', error);
    res.status(500).json({ error: 'Failed to fetch simulations' });
  }
});

app.post('/api/simulations', authenticateToken, async (req, res) => {
  try {
    const { name, description, simulation_type, configuration } = req.body;

    const result = await pgPool.query(
      `INSERT INTO simulations (user_id, name, description, simulation_type, configuration, status)
       VALUES ($1, $2, $3, $4, $5, 'created') RETURNING *`,
      [req.user.userId, name, description, simulation_type, JSON.stringify(configuration)]
    );

    simulationCounter.inc({ type: simulation_type, status: 'created' });

    res.status(201).json(result.rows[0]);
  } catch (error) {
    console.error('Error creating simulation:', error);
    res.status(500).json({ error: 'Failed to create simulation' });
  }
});

app.get('/api/simulations/:id', authenticateToken, async (req, res) => {
  try {
    const result = await pgPool.query(
      'SELECT * FROM simulations WHERE id = $1 AND user_id = $2',
      [req.params.id, req.user.userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Simulation not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching simulation:', error);
    res.status(500).json({ error: 'Failed to fetch simulation' });
  }
});

app.get('/api/simulations/:id/data', authenticateToken, async (req, res) => {
  try {
    const { limit = 1000, offset = 0 } = req.query;

    const result = await pgPool.query(
      `SELECT time, timestep, neural_v, neural_w, cardiac_x, cardiac_y, bci_signal, control_signal
       FROM simulation_data WHERE simulation_id = $1
       ORDER BY time DESC LIMIT $2 OFFSET $3`,
      [req.params.id, limit, offset]
    );

    res.json({
      data: result.rows,
      count: result.rowCount
    });
  } catch (error) {
    console.error('Error fetching simulation data:', error);
    res.status(500).json({ error: 'Failed to fetch simulation data' });
  }
});

// Performance metrics routes
app.get('/api/metrics/performance', authenticateToken, async (req, res) => {
  try {
    const { simulation_id, metric_type } = req.query;

    let query = 'SELECT * FROM performance_metrics WHERE 1=1';
    const params = [];

    if (simulation_id) {
      params.push(simulation_id);
      query += ` AND simulation_id = $${params.length}`;
    }

    if (metric_type) {
      params.push(metric_type);
      query += ` AND metric_type = $${params.length}`;
    }

    query += ' ORDER BY timestamp DESC LIMIT 1000';

    const result = await pgPool.query(query, params);

    // Calculate statistics
    const latencyMetrics = result.rows.filter(m => m.metric_type === 'latency');
    const avgLatency = latencyMetrics.length > 0
      ? latencyMetrics.reduce((sum, m) => sum + parseFloat(m.metric_value), 0) / latencyMetrics.length
      : 0;
    const maxLatency = latencyMetrics.length > 0
      ? Math.max(...latencyMetrics.map(m => parseFloat(m.metric_value)))
      : 0;

    res.json({
      metrics: result.rows,
      summary: {
        avg_latency_ms: avgLatency,
        max_latency_ms: maxLatency,
        under_100ms: latencyMetrics.filter(m => parseFloat(m.metric_value) < 100).length,
        total_samples: latencyMetrics.length
      }
    });
  } catch (error) {
    console.error('Error fetching performance metrics:', error);
    res.status(500).json({ error: 'Failed to fetch performance metrics' });
  }
});

// Validation results routes
app.get('/api/validation/results', authenticateToken, async (req, res) => {
  try {
    const { test_type } = req.query;

    let query = 'SELECT * FROM validation_results';
    const params = [];

    if (test_type) {
      params.push(test_type);
      query += ` WHERE test_type = $${params.length}`;
    }

    query += ' ORDER BY created_at DESC LIMIT 100';

    const result = await pgPool.query(query, params);

    res.json({
      results: result.rows,
      summary: {
        total: result.rows.length,
        passed: result.rows.filter(r => r.status === 'passed').length,
        failed: result.rows.filter(r => r.status === 'failed').length,
        warnings: result.rows.filter(r => r.status === 'warning').length
      }
    });
  } catch (error) {
    console.error('Error fetching validation results:', error);
    res.status(500).json({ error: 'Failed to fetch validation results' });
  }
});

// Device management routes
app.get('/api/devices', authenticateToken, async (req, res) => {
  try {
    const result = await pgPool.query(
      'SELECT * FROM devices ORDER BY last_seen DESC'
    );

    res.json({
      devices: result.rows,
      summary: {
        total: result.rows.length,
        online: result.rows.filter(d => d.status === 'online').length,
        offline: result.rows.filter(d => d.status === 'offline').length
      }
    });
  } catch (error) {
    console.error('Error fetching devices:', error);
    res.status(500).json({ error: 'Failed to fetch devices' });
  }
});

// MQTT control endpoint
app.post('/api/mqtt/publish', authenticateToken, async (req, res) => {
  try {
    const { topic, message, qos = 0, retain = false } = req.body;

    mqttClient.publish(topic, JSON.stringify(message), { qos, retain }, (error) => {
      if (error) {
        return res.status(500).json({ error: 'Failed to publish message' });
      }
      res.json({ success: true, topic, timestamp: new Date().toISOString() });
    });
  } catch (error) {
    console.error('Error publishing MQTT message:', error);
    res.status(500).json({ error: 'Failed to publish message' });
  }
});

// Error handling
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Startup
async function start() {
  try {
    await redisClient.connect();
    console.log('Redis connected successfully');

    const server = app.listen(PORT, () => {
      console.log(`\n${'='.repeat(60)}`);
      console.log('Multi-Heart-Model Production API Server');
      console.log(`${'='.repeat(60)}`);
      console.log(`Server running on port ${PORT}`);
      console.log(`Health check: http://localhost:${PORT}/health`);
      console.log(`Metrics: http://localhost:${PORT}/metrics`);
      console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
      console.log(`${'='.repeat(60)}\n`);
    });

    // Graceful shutdown
    process.on('SIGTERM', async () => {
      console.log('SIGTERM received, shutting down gracefully...');
      server.close(async () => {
        await pgPool.end();
        await redisClient.quit();
        mqttClient.end();
        process.exit(0);
      });
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

start();
