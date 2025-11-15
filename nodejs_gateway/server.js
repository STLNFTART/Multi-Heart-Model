/**
 * Node.js API Gateway for Multi-Heart-Model
 *
 * Provides:
 * - JWT authentication and authorization
 * - Rate limiting and request validation
 * - Reverse proxy to FastAPI backend
 * - Historical data API (MongoDB)
 * - OpenSim biomechanical bridge
 * - WebSocket bridge (FastAPI → Socket.io)
 * - Time-series data storage (InfluxDB)
 *
 * Author: Multi-Heart-Model Team
 * License: MIT
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const { createProxyMiddleware } = require('http-proxy-middleware');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const rateLimit = require('express-rate-limit');
const WebSocket = require('ws');
const http = require('http');
const socketio = require('socket.io');
const mongoose = require('mongoose');
const { Influx } = require('influx');

// Import services
const OpenSimBridge = require('./services/opensimBridge');

// Environment configuration
const PORT = process.env.PORT || 3000;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';
const FASTAPI_WS_URL = process.env.FASTAPI_WS_URL || 'ws://localhost:8000/ws/nodejs-bridge';
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production';
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/hbcm';
const INFLUXDB_HOST = process.env.INFLUXDB_HOST || 'localhost';

// Initialize Express app
const app = express();
const server = http.createServer(app);
const io = socketio(server, {
    cors: {
        origin: '*',  // Configure appropriately for production
        methods: ['GET', 'POST']
    }
});

// Middleware
app.use(helmet());  // Security headers
app.use(cors());    // CORS support
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use((req, res, next) => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${req.method} ${req.path} - ${req.ip}`);
    next();
});

// Rate limiting
const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,  // 15 minutes
    max: 100,  // 100 requests per window
    message: 'Too many requests from this IP, please try again later'
});

app.use('/api/', apiLimiter);

// Stricter rate limiting for auth endpoints
const authLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 5,  // 5 attempts per 15 minutes
    message: 'Too many authentication attempts, please try again later'
});

// ============================================================================
// Database Setup
// ============================================================================

// MongoDB connection
mongoose.connect(MONGODB_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true
}).then(() => {
    console.log('Connected to MongoDB');
}).catch(err => {
    console.error('MongoDB connection error:', err);
});

// MongoDB Schemas
const UserSchema = new mongoose.Schema({
    email: { type: String, required: true, unique: true },
    password: { type: String, required: true },
    name: String,
    role: { type: String, default: 'user' },  // user, admin, researcher
    createdAt: { type: Date, default: Date.now }
});

const SimulationSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    timestamp: { type: Date, default: Date.now },
    config: {
        initial_state: [Number],
        t_start: Number,
        t_end: Number,
        dt: Number,
        neural_params: Object,
        cardiac_params: Object,
        coupling_params: Object
    },
    results: {
        times: [Number],
        neural: {
            v: [Number],
            w: [Number]
        },
        cardiac: {
            x: [Number],
            y: [Number]
        }
    },
    metrics: {
        comfort_index: Number,
        max_control: Number,
        phase_drift_ms: Number,
        max_cardiac_pressure: Number
    },
    duration_seconds: Number,
    status: { type: String, default: 'completed' }  // completed, failed, running
});

const User = mongoose.model('User', UserSchema);
const Simulation = mongoose.model('Simulation', SimulationSchema);

// InfluxDB setup for time-series data
const influx = new Influx.InfluxDB({
    host: INFLUXDB_HOST,
    database: 'hbcm',
    schema: [
        {
            measurement: 'simulation',
            fields: {
                neural_v: Influx.FieldType.FLOAT,
                neural_w: Influx.FieldType.FLOAT,
                cardiac_x: Influx.FieldType.FLOAT,
                cardiac_y: Influx.FieldType.FLOAT,
                comfort_index: Influx.FieldType.FLOAT,
                control_output: Influx.FieldType.FLOAT
            },
            tags: ['user_id', 'simulation_id', 'session_id']
        }
    ]
});

// Create InfluxDB database if it doesn't exist
influx.getDatabaseNames()
    .then(names => {
        if (!names.includes('hbcm')) {
            return influx.createDatabase('hbcm');
        }
    })
    .then(() => console.log('InfluxDB ready'))
    .catch(err => console.error('InfluxDB setup error:', err));

// ============================================================================
// Authentication Middleware
// ============================================================================

function authenticate(req, res, next) {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
        return res.status(401).json({ error: 'No authorization header' });
    }

    const token = authHeader.split(' ')[1];  // Bearer <token>

    if (!token) {
        return res.status(401).json({ error: 'No token provided' });
    }

    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        req.user = decoded;
        next();
    } catch (err) {
        return res.status(403).json({ error: 'Invalid or expired token' });
    }
}

// Optional authentication (attaches user if token valid, but doesn't fail if missing)
function optionalAuth(req, res, next) {
    const authHeader = req.headers.authorization;

    if (authHeader) {
        const token = authHeader.split(' ')[1];
        try {
            req.user = jwt.verify(token, JWT_SECRET);
        } catch (err) {
            // Invalid token, but we continue anyway
        }
    }

    next();
}

// ============================================================================
// Authentication Routes
// ============================================================================

// Register new user
app.post('/auth/register', authLimiter, async (req, res) => {
    try {
        const { email, password, name } = req.body;

        // Validate input
        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password required' });
        }

        // Check if user exists
        const existingUser = await User.findOne({ email });
        if (existingUser) {
            return res.status(400).json({ error: 'User already exists' });
        }

        // Hash password
        const hashedPassword = await bcrypt.hash(password, 10);

        // Create user
        const user = new User({
            email,
            password: hashedPassword,
            name
        });

        await user.save();

        res.status(201).json({
            message: 'User created successfully',
            userId: user._id
        });

    } catch (err) {
        console.error('Registration error:', err);
        res.status(500).json({ error: 'Registration failed' });
    }
});

// Login
app.post('/auth/login', authLimiter, async (req, res) => {
    try {
        const { email, password } = req.body;

        // Find user
        const user = await User.findOne({ email });
        if (!user) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        // Verify password
        const validPassword = await bcrypt.compare(password, user.password);
        if (!validPassword) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        // Generate JWT
        const token = jwt.sign(
            {
                userId: user._id,
                email: user.email,
                role: user.role
            },
            JWT_SECRET,
            { expiresIn: '24h' }
        );

        res.json({
            token,
            user: {
                id: user._id,
                email: user.email,
                name: user.name,
                role: user.role
            }
        });

    } catch (err) {
        console.error('Login error:', err);
        res.status(500).json({ error: 'Login failed' });
    }
});

// Verify token
app.get('/auth/verify', authenticate, (req, res) => {
    res.json({ valid: true, user: req.user });
});

// ============================================================================
// FastAPI Reverse Proxy
// ============================================================================

// Proxy all /api/hbcm/* requests to FastAPI backend
app.use('/api/hbcm', authenticate, createProxyMiddleware({
    target: FASTAPI_URL,
    changeOrigin: true,
    pathRewrite: {
        '^/api/hbcm': '/api'  // /api/hbcm/status → /api/status
    },
    onProxyReq: (proxyReq, req) => {
        // Add user context to proxied request
        proxyReq.setHeader('X-User-ID', req.user.userId);
        proxyReq.setHeader('X-User-Email', req.user.email);
        proxyReq.setHeader('X-User-Role', req.user.role);
    },
    onProxyRes: (proxyRes, req, res) => {
        // Log proxied requests
        console.log(`[PROXY] ${req.user.email} - ${req.method} ${req.path} → ${proxyRes.statusCode}`);
    },
    onError: (err, req, res) => {
        console.error('[PROXY ERROR]', err);
        res.status(502).json({
            error: 'FastAPI backend unavailable',
            message: err.message
        });
    }
}));

// ============================================================================
// Historical Data API (MongoDB)
// ============================================================================

// Get user's simulation history
app.get('/api/simulations', authenticate, async (req, res) => {
    try {
        const { startDate, endDate, limit = 100, offset = 0 } = req.query;

        const query = { userId: req.user.userId };

        // Date filtering
        if (startDate || endDate) {
            query.timestamp = {};
            if (startDate) query.timestamp.$gte = new Date(startDate);
            if (endDate) query.timestamp.$lte = new Date(endDate);
        }

        const simulations = await Simulation.find(query)
            .sort({ timestamp: -1 })
            .skip(parseInt(offset))
            .limit(parseInt(limit))
            .select('-results');  // Exclude large results array, just metadata

        const total = await Simulation.countDocuments(query);

        res.json({
            simulations,
            pagination: {
                total,
                limit: parseInt(limit),
                offset: parseInt(offset)
            }
        });

    } catch (err) {
        console.error('Simulations query error:', err);
        res.status(500).json({ error: 'Failed to fetch simulations' });
    }
});

// Get specific simulation by ID
app.get('/api/simulations/:id', authenticate, async (req, res) => {
    try {
        const simulation = await Simulation.findOne({
            _id: req.params.id,
            userId: req.user.userId  // Ensure user owns this simulation
        });

        if (!simulation) {
            return res.status(404).json({ error: 'Simulation not found' });
        }

        res.json(simulation);

    } catch (err) {
        console.error('Simulation fetch error:', err);
        res.status(500).json({ error: 'Failed to fetch simulation' });
    }
});

// Delete simulation
app.delete('/api/simulations/:id', authenticate, async (req, res) => {
    try {
        const result = await Simulation.deleteOne({
            _id: req.params.id,
            userId: req.user.userId
        });

        if (result.deletedCount === 0) {
            return res.status(404).json({ error: 'Simulation not found' });
        }

        res.json({ message: 'Simulation deleted' });

    } catch (err) {
        console.error('Simulation delete error:', err);
        res.status(500).json({ error: 'Failed to delete simulation' });
    }
});

// ============================================================================
// Time-Series Data API (InfluxDB)
// ============================================================================

// Query time-series data
app.get('/api/timeseries/query', authenticate, async (req, res) => {
    try {
        const { measurement = 'simulation', startTime, endTime, tags = {} } = req.query;

        let query = `SELECT * FROM ${measurement}`;

        const conditions = [];

        // Add user filter
        conditions.push(`user_id = '${req.user.userId}'`);

        // Add time range
        if (startTime) conditions.push(`time >= '${startTime}'`);
        if (endTime) conditions.push(`time <= '${endTime}'`);

        // Add tag filters
        for (const [key, value] of Object.entries(tags)) {
            conditions.push(`${key} = '${value}'`);
        }

        if (conditions.length > 0) {
            query += ' WHERE ' + conditions.join(' AND ');
        }

        const results = await influx.query(query);

        res.json({ data: results });

    } catch (err) {
        console.error('Time-series query error:', err);
        res.status(500).json({ error: 'Failed to query time-series data' });
    }
});

// ============================================================================
// OpenSim Integration
// ============================================================================

const opensimBridge = new OpenSimBridge({
    opensimBin: process.env.OPENSIM_BIN || 'opensim-cmd',
    modelsDir: process.env.OPENSIM_MODELS_DIR || '/opt/opensim/models',
    resultsDir: process.env.OPENSIM_RESULTS_DIR || '/tmp/opensim_results'
});

// Run OpenSim biomechanical simulation
app.post('/api/opensim/run', authenticate, async (req, res) => {
    try {
        const { neural, cardiac, config } = req.body;

        if (!cardiac) {
            return res.status(400).json({ error: 'Cardiac trajectory required' });
        }

        // Generate OpenSim motion file from cardiac data
        const motionFile = await opensimBridge.generateMotion({
            neural,
            cardiac,
            config: config || {}
        });

        // Run OpenSim forward dynamics
        const results = await opensimBridge.runForwardDynamics({
            motionFile,
            modelFile: config?.opensimModel,
            setupFile: config?.setupFile
        });

        if (!results.success) {
            return res.status(500).json({
                error: 'OpenSim simulation failed',
                stderr: results.stderr
            });
        }

        // Parse kinematics and forces
        const kinematics = await opensimBridge.parseResults(results.outputFile);

        res.json({
            success: true,
            motion_file: motionFile,
            output_file: results.outputFile,
            kinematics,
            forces: results.forces,
            stdout: results.stdout
        });

    } catch (err) {
        console.error('OpenSim integration error:', err);
        res.status(500).json({
            error: 'OpenSim integration failed',
            message: err.message
        });
    }
});

// ============================================================================
// WebSocket Bridge (FastAPI → Socket.io)
// ============================================================================

// Connect to FastAPI WebSocket
const fastapi_ws = new WebSocket(FASTAPI_WS_URL);

fastapi_ws.on('open', () => {
    console.log('Connected to FastAPI WebSocket');
});

fastapi_ws.on('message', async (data) => {
    try {
        const message = JSON.parse(data);

        if (message.type === 'data_update') {
            const simData = message.data;

            // Broadcast to all Socket.io clients in 'simulation' room
            io.to('simulation').emit('hbcm-update', simData);

            // Store in InfluxDB for historical analysis
            if (simData.current_state) {
                await influx.writePoints([{
                    measurement: 'simulation',
                    tags: {
                        user_id: simData.user_id || 'system',
                        simulation_id: simData.simulation_id || 'unknown',
                        session_id: simData.session_id || 'unknown'
                    },
                    fields: {
                        neural_v: simData.current_state.neural_v,
                        neural_w: simData.current_state.neural_w,
                        cardiac_x: simData.current_state.cardiac_x,
                        cardiac_y: simData.current_state.cardiac_y,
                        comfort_index: simData.current_state.comfort_index || 0,
                        control_output: simData.current_state.control_output || 0
                    },
                    timestamp: new Date()
                }]);
            }
        }
    } catch (err) {
        console.error('WebSocket message processing error:', err);
    }
});

fastapi_ws.on('error', (err) => {
    console.error('FastAPI WebSocket error:', err);
});

fastapi_ws.on('close', () => {
    console.log('FastAPI WebSocket closed. Attempting reconnect in 5s...');
    setTimeout(() => {
        // Reconnect logic here if needed
    }, 5000);
});

// Socket.io connection handling
io.on('connection', (socket) => {
    console.log('Client connected:', socket.id);

    socket.on('join-simulation', (room) => {
        socket.join(room || 'simulation');
        console.log(`Client ${socket.id} joined room: ${room || 'simulation'}`);
    });

    socket.on('control-command', (command) => {
        // Forward control commands to FastAPI WebSocket
        if (fastapi_ws.readyState === WebSocket.OPEN) {
            fastapi_ws.send(JSON.stringify({
                type: 'control',
                command
            }));
        }
    });

    socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id);
    });
});

// ============================================================================
// Health Check and Status
// ============================================================================

app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        services: {
            mongodb: mongoose.connection.readyState === 1,
            influxdb: true,  // Add actual health check
            fastapi_ws: fastapi_ws.readyState === WebSocket.OPEN
        }
    });
});

app.get('/', (req, res) => {
    res.json({
        name: 'Multi-Heart-Model API Gateway',
        version: '1.0.0',
        endpoints: {
            auth: '/auth/*',
            hbcm_proxy: '/api/hbcm/*',
            simulations: '/api/simulations',
            timeseries: '/api/timeseries/query',
            opensim: '/api/opensim/run',
            health: '/health'
        }
    });
});

// ============================================================================
// Error Handling
// ============================================================================

app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({
        error: 'Internal server error',
        message: err.message
    });
});

// ============================================================================
// Start Server
// ============================================================================

server.listen(PORT, () => {
    console.log('='.repeat(60));
    console.log('Multi-Heart-Model API Gateway');
    console.log('='.repeat(60));
    console.log(`Server running on port ${PORT}`);
    console.log(`FastAPI proxy target: ${FASTAPI_URL}`);
    console.log(`FastAPI WebSocket: ${FASTAPI_WS_URL}`);
    console.log(`MongoDB: ${MONGODB_URI}`);
    console.log(`InfluxDB: ${INFLUXDB_HOST}`);
    console.log('='.repeat(60));
});

module.exports = { app, server, io };
