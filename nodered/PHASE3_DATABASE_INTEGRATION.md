# Node-RED Phase 3: Database Integration

**Status**: Implementation Ready
**Date**: 2025-11-15
**Prerequisites**: Phase 1 (Dashboard) ✅, Phase 2 (Authentication) ✅

---

## Overview

Phase 3 adds PostgreSQL database persistence to Node-RED for production deployments. This enables:

- **Simulation history** - Store and retrieve HBCM simulation runs
- **User management** - User accounts, sessions, roles
- **Performance tracking** - Metrics and audit logs over time
- **Dashboard persistence** - Save custom dashboard configurations
- **Control session logging** - MotorHandPro control loop telemetry

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Node-RED Dashboard                       │
│  ┌─────────────┬─────────────┬────────────┬────────────────┐│
│  │   HBCM UI   │  Control UI │  Metrics   │  User Profile  ││
│  └─────────────┴─────────────┴────────────┴────────────────┘│
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   Node-RED Flows (Phase 3)                   │
│  ┌────────────┬──────────────┬───────────┬─────────────────┐│
│  │Simulation  │   Control    │  Metrics  │  User           ││
│  │Persistence │   Logging    │  Storage  │  Management     ││
│  └────────────┴──────────────┴───────────┴─────────────────┘│
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                PostgreSQL Database (Port 5432)               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Tables:                                               │ │
│  │  - users (authentication, profiles)                    │ │
│  │  - simulations (HBCM runs)                            │ │
│  │  - simulation_results (time series data)              │ │
│  │  - control_sessions (MotorHandPro sessions)           │ │
│  │  - control_cycles (telemetry)                         │ │
│  │  - performance_metrics (monitoring)                   │ │
│  │  - audit_logs (security)                              │ │
│  │  - dashboards (UI persistence)                        │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Installation

### 1. Install Required Node-RED Nodes

```bash
cd /home/user/Multi-Heart-Model/nodered

# Install PostgreSQL node
npm install node-red-contrib-postgres-variable

# Install additional utility nodes
npm install node-red-contrib-moment
npm install node-red-contrib-uuid

# Restart Node-RED
pm2 restart nodered  # Or restart via systemctl/docker
```

### 2. Configure PostgreSQL Connection

In Node-RED:
1. Add a **postgres** node from the palette
2. Configure database connection:
   - **Host**: `postgres` (Docker) or `localhost`
   - **Port**: `5432`
   - **Database**: `multiheart_prod`
   - **User**: `multiheart_app`
   - **Password**: (from `deployment/security/production.env`)
   - **SSL**: `disable` (for dev), `require` (for production)

### 3. Initialize Database Schema

```bash
# Using Docker Compose
docker-compose exec postgres psql -U multiheart -d multiheart_prod -f /docker-entrypoint-initdb.d/init.sql

# Or directly
psql -h localhost -U multiheart -d multiheart_prod -f deployment/init_db.sql
```

---

## Database Schema

### Key Tables

#### `simulations`
Stores HBCM simulation configurations and results.

```sql
CREATE TABLE simulations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255),
    duration_seconds FLOAT,
    dt FLOAT,
    initial_state JSONB,
    neural_params JSONB,
    cardiac_params JSONB,
    coupling_params JSONB,
    env_context JSONB,  -- NASA POWER environmental data
    comms_profile JSONB,  -- Starlink communications profile
    wall_clock_time_seconds FLOAT,
    realtime_factor FLOAT,
    created_at TIMESTAMP,
    status VARCHAR(50)
);
```

#### `simulation_results`
Time series data from simulations.

```sql
CREATE TABLE simulation_results (
    id UUID PRIMARY KEY,
    simulation_id UUID REFERENCES simulations(id),
    time_index INTEGER,
    time_value FLOAT,
    neural_v FLOAT,
    neural_w FLOAT,
    cardiac_x FLOAT,
    cardiac_y FLOAT,
    heart_rate FLOAT,
    created_at TIMESTAMP
);
```

#### `control_sessions`
MotorHandPro control loop sessions.

```sql
CREATE TABLE control_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255),
    comms_profile JSONB,
    total_cycles INTEGER,
    packet_losses INTEGER,
    mean_latency_ms FLOAT,
    p99_latency_ms FLOAT,
    created_at TIMESTAMP,
    status VARCHAR(50)
);
```

#### `control_cycles`
Individual control loop cycles (telemetry).

```sql
CREATE TABLE control_cycles (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES control_sessions(id),
    cycle_index INTEGER,
    sensor_value FLOAT,
    target_value FLOAT,
    error_value FLOAT,
    control_signal FLOAT,
    cycle_latency_ms FLOAT,
    network_delay_ms FLOAT,
    packet_lost BOOLEAN,
    timestamp TIMESTAMP
);
```

#### `performance_metrics`
System performance metrics (Prometheus-compatible).

```sql
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY,
    metric_name VARCHAR(255),
    metric_type VARCHAR(50),
    metric_value FLOAT,
    labels JSONB,
    timestamp TIMESTAMP
);
```

---

## Node-RED Flow Examples

### Flow 1: Save HBCM Simulation

```javascript
// Input: msg.payload = {
//   name: "My Simulation",
//   duration_seconds: 120.0,
//   dt: 0.001,
//   initial_state: {v: 0, w: 0, x: 1, y: 0},
//   neural_params: {a: 0.7, b: 0.8, c: 3.0},
//   cardiac_params: {mu: 1.5, omega: 1.0},
//   coupling_params: {n_to_c_gain: 0.5},
//   env_context: {...},  // From space integration
//   trajectory: [...]  // Simulation results
// }

// Function node: Prepare INSERT statement
const simulation_id = msg.payload.simulation_id || uuidv4();

msg.topic = `
INSERT INTO simulations (
    id, user_id, name, duration_seconds, dt, initial_state,
    neural_params, cardiac_params, coupling_params,
    env_context, created_at, status
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), 'completed'
) RETURNING id
`;

msg.params = [
    simulation_id,
    msg.user_id || null,
    msg.payload.name,
    msg.payload.duration_seconds,
    msg.payload.dt,
    JSON.stringify(msg.payload.initial_state),
    JSON.stringify(msg.payload.neural_params),
    JSON.stringify(msg.payload.cardiac_params),
    JSON.stringify(msg.payload.coupling_params),
    JSON.stringify(msg.payload.env_context)
];

// Store simulation_id for results insertion
flow.set('current_simulation_id', simulation_id);

return msg;

// → [postgres node] → Execute INSERT
// → Next: Insert simulation_results
```

### Flow 2: Query Simulation History

```javascript
// Input: msg.payload = {user_id: "uuid", limit: 10}

// Function node: Prepare SELECT statement
msg.topic = `
SELECT
    id, name, duration_seconds, status,
    created_at, wall_clock_time_seconds, realtime_factor,
    env_context->>'source' as env_source,
    comms_profile->>'source' as comms_source
FROM simulations
WHERE user_id = $1 OR $1 IS NULL
ORDER BY created_at DESC
LIMIT $2
`;

msg.params = [msg.payload.user_id || null, msg.payload.limit || 10];

return msg;

// → [postgres node] → Execute SELECT
// → Output: msg.payload = array of simulations
```

### Flow 3: Real-Time Metrics Storage

```javascript
// Input from monitoring: msg.payload = {
//   metric_name: "hbcm_simulation_latency_ms",
//   metric_value: 125.5,
//   labels: {endpoint: "/api/simulate", status: "success"}
// }

// Function node: Prepare INSERT
msg.topic = `
INSERT INTO performance_metrics (
    id, metric_name, metric_type, metric_value, labels, timestamp
) VALUES (
    uuid_generate_v4(), $1, $2, $3, $4, NOW()
)
`;

msg.params = [
    msg.payload.metric_name,
    msg.payload.metric_type || 'gauge',
    msg.payload.metric_value,
    JSON.stringify(msg.payload.labels || {})
];

return msg;

// → [postgres node] → Execute INSERT (fire-and-forget)
```

### Flow 4: Dashboard Analytics

```javascript
// Query: Get simulation statistics for past 24 hours

msg.topic = `
SELECT
    COUNT(*) as total_simulations,
    AVG(duration_seconds) as avg_duration,
    AVG(realtime_factor) as avg_realtime_factor,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
FROM simulations
WHERE created_at > NOW() - INTERVAL '24 hours'
`;

return msg;

// → [postgres node] → Execute SELECT
// → [gauge nodes] → Display stats on dashboard
```

---

## Integration with Existing Phases

### Phase 1 (Dashboard) Integration

**Before** (Phase 1): Data only in memory, lost on restart
**After** (Phase 3): Data persisted to PostgreSQL

```
[HBCM Simulation] → [Store to DB] → [Dashboard Display]
                      ↓
                  [PostgreSQL]
                      ↓
              [History/Analytics]
```

### Phase 2 (Authentication) Integration

**Before** (Phase 2): JWT tokens only
**After** (Phase 3): User accounts, sessions, audit logs

```
[Login] → [Validate JWT] → [Load User from DB]
            ↓                    ↓
        [Sessions Table]    [Users Table]
```

---

## Performance Considerations

### Batch Inserts for Time Series Data

For high-frequency data (control cycles, simulation results), use batch inserts:

```javascript
// Buffer 100 samples before inserting
let buffer = flow.get('buffer') || [];
buffer.push(msg.payload);

if (buffer.length >= 100) {
    // Build multi-row INSERT
    msg.topic = `
    INSERT INTO control_cycles (
        id, session_id, cycle_index, sensor_value, target_value,
        error_value, control_signal, cycle_latency_ms, timestamp
    ) VALUES `;

    const values = buffer.map((item, idx) =>
        `(uuid_generate_v4(), '${item.session_id}', ${item.cycle_index}, ` +
        `${item.sensor_value}, ${item.target_value}, ${item.error_value}, ` +
        `${item.control_signal}, ${item.cycle_latency_ms}, NOW())`
    ).join(', ');

    msg.topic += values;

    // Clear buffer
    flow.set('buffer', []);

    return msg;
}

return null;  // Don't send yet, still buffering
```

### Indexing Strategy

Ensure proper indexes for common queries:

```sql
-- Simulation queries
CREATE INDEX idx_simulations_user_created ON simulations(user_id, created_at DESC);

-- Control session queries
CREATE INDEX idx_control_cycles_session_time ON control_cycles(session_id, timestamp DESC);

-- Metrics queries
CREATE INDEX idx_performance_metrics_name_time ON performance_metrics(metric_name, timestamp DESC);
```

### Connection Pooling

Configure PostgreSQL connection pool in Node-RED:

- **Max connections**: 10-20 per Node-RED instance
- **Idle timeout**: 30 seconds
- **Connection timeout**: 5 seconds

---

## Security

### Database User Permissions

The `multiheart_app` user has limited permissions:

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES TO multiheart_app;
-- NO DROP, TRUNCATE, or admin permissions
```

### Sensitive Data Encryption

Encrypt sensitive fields before storage:

```javascript
// Example: Encrypt user email
const crypto = require('crypto');
const algorithm = 'aes-256-cbc';
const key = Buffer.from(process.env.ENCRYPTION_KEY, 'hex');
const iv = crypto.randomBytes(16);

const cipher = crypto.createCipheriv(algorithm, key, iv);
let encrypted = cipher.update(email, 'utf8', 'hex');
encrypted += cipher.final('hex');

// Store: iv.toString('hex') + ':' + encrypted
```

### SQL Injection Prevention

Always use parameterized queries:

```javascript
// CORRECT
msg.topic = "SELECT * FROM users WHERE username = $1";
msg.params = [username];

// WRONG - susceptible to SQL injection
msg.topic = `SELECT * FROM users WHERE username = '${username}'`;
```

---

## Monitoring & Maintenance

### Database Health Check

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('multiheart_prod'));

-- Check table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check connection count
SELECT count(*) FROM pg_stat_activity
WHERE datname = 'multiheart_prod';
```

### Cleanup Jobs

Run periodic maintenance:

```sql
-- Clean expired sessions (run daily)
SELECT clean_expired_sessions();

-- Archive old simulation results (run weekly)
SELECT archive_old_simulation_results(90);  -- Archive data older than 90 days

-- Vacuum and analyze (run weekly)
SELECT maintenance_vacuum_analyze();
```

Set up cron job or Node-RED flow:

```javascript
// Run every day at 2 AM
[inject node: cron "0 2 * * *"]
  ↓
[function: msg.topic = "SELECT clean_expired_sessions()"]
  ↓
[postgres node]
  ↓
[debug: log result]
```

---

## Migration Guide

### From Phase 2 to Phase 3

1. **Backup existing data** (if any in memory/files)
2. **Initialize database** (`deployment/init_db.sql`)
3. **Update Node-RED flows** to use postgres nodes
4. **Test authentication** with database-backed sessions
5. **Deploy updated flows**

### Data Migration Script

If migrating from file-based storage:

```javascript
// Read old JSON files
const fs = require('fs');
const oldData = JSON.parse(fs.readFileSync('simulations.json'));

// Insert into database
oldData.simulations.forEach(sim => {
    msg.topic = `INSERT INTO simulations (...) VALUES (...)`;
    msg.params = [...];
    // Send to postgres node
});
```

---

## Testing

### Unit Tests for Database Operations

```javascript
// Test: Insert and retrieve simulation
[inject] → [insert simulation] → [postgres] →
[query simulation] → [postgres] → [assert result] → [pass/fail]
```

### Integration Tests

```bash
# Run full integration test
curl -X POST http://localhost:1880/test-db-integration \
  -H "Content-Type: application/json" \
  -d '{
    "test_type": "full",
    "cleanup": true
  }'
```

### Load Testing

```bash
# Simulate 1000 concurrent simulation saves
ab -n 1000 -c 10 -p simulation.json \
   -T application/json \
   http://localhost:1880/api/save-simulation
```

---

## Troubleshooting

### Connection Issues

```
Error: ECONNREFUSED 127.0.0.1:5432
```

**Solution**: Check PostgreSQL is running and accessible:
```bash
docker-compose ps postgres  # Ensure running
psql -h localhost -U multiheart -d multiheart_prod -c "SELECT 1"
```

### Authentication Failures

```
Error: password authentication failed for user "multiheart_app"
```

**Solution**: Verify credentials in `production.env` match `init_db.sql`

### Slow Queries

```
Query took >1 second to execute
```

**Solution**: Check indexes, analyze query plan:
```sql
EXPLAIN ANALYZE SELECT ...;
```

---

## Next Steps

After Phase 3 completion:

- **Phase 4**: OpenSim Integration (biomechanical coupling)
- **Phase 5**: Space API Integration (NASA POWER, Starlink in dashboard)
- **Phase 6**: Production Deployment (SSL, monitoring, backups)

---

## Summary

Phase 3 adds production-grade data persistence to Node-RED:

✅ **PostgreSQL database** for all application data
✅ **User management** with authentication and sessions
✅ **Simulation history** with full time series storage
✅ **Control session logging** for MotorHandPro telemetry
✅ **Performance metrics** storage for monitoring
✅ **Audit logs** for security and compliance
✅ **Dashboard persistence** for custom UI configurations

This infrastructure supports:
- Multi-user production deployments
- Long-term data analysis and research
- Compliance requirements (HIPAA-ready schema)
- Partnership demonstrations with full traceability

**Phase 3 Status**: ✅ Implementation Complete
**Database Schema**: ✅ Ready (`deployment/init_db.sql`)
**Documentation**: ✅ Complete

**Next**: Deploy and test Phase 3 flows!
