-- Multi-Heart-Model Database Schema
-- PostgreSQL 16+ compatible
--
-- This schema supports:
-- - HBCM simulation runs and results
-- - User authentication and sessions
-- - Performance metrics and monitoring
-- - Audit logging
-- - Node-RED dashboard persistence

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For GIN indexes

-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'user',  -- 'admin', 'researcher', 'user'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Sessions table for JWT refresh tokens
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_refresh_token ON sessions(refresh_token);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- ============================================================================
-- HBCM SIMULATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS simulations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255),
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'

    -- Configuration
    duration_seconds FLOAT NOT NULL,
    dt FLOAT NOT NULL,
    initial_state JSONB NOT NULL,  -- {v, w, x, y}

    -- Model parameters
    neural_params JSONB,  -- FitzHugh-Nagumo parameters
    cardiac_params JSONB,  -- Van der Pol parameters
    coupling_params JSONB,  -- Coupling parameters

    -- Environmental context (from space integration)
    env_context JSONB,  -- NASA POWER environmental data
    comms_profile JSONB,  -- Starlink communications profile
    scenario_config JSONB,  -- Space scenario configuration

    -- Performance metrics
    wall_clock_time_seconds FLOAT,
    realtime_factor FLOAT,
    total_timesteps INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Results summary
    results_summary JSONB  -- Statistical summary of results
);

CREATE INDEX idx_simulations_user_id ON simulations(user_id);
CREATE INDEX idx_simulations_status ON simulations(status);
CREATE INDEX idx_simulations_created_at ON simulations(created_at DESC);
CREATE INDEX idx_simulations_env_context ON simulations USING GIN (env_context);

-- Simulation results (time series data)
CREATE TABLE IF NOT EXISTS simulation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    simulation_id UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    time_index INTEGER NOT NULL,
    time_value FLOAT NOT NULL,

    -- Neural state
    neural_v FLOAT NOT NULL,
    neural_w FLOAT NOT NULL,

    -- Cardiac state
    cardiac_x FLOAT NOT NULL,
    cardiac_y FLOAT NOT NULL,

    -- Optional derived quantities
    heart_rate FLOAT,
    neural_activity FLOAT,
    coupling_strength FLOAT,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_simulation_results_simulation_id ON simulation_results(simulation_id);
CREATE INDEX idx_simulation_results_time_index ON simulation_results(time_index);
CREATE INDEX idx_simulation_results_composite ON simulation_results(simulation_id, time_index);

-- Partition simulation_results by simulation_id for better performance
-- (For large-scale deployments, consider partitioning by date/simulation_id)

-- ============================================================================
-- MOTORHANDPRO CONTROL SESSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS control_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255),
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active',  -- 'active', 'paused', 'stopped'

    -- Network configuration
    comms_profile JSONB,  -- Starlink profile for network simulation

    -- Performance metrics
    total_cycles INTEGER DEFAULT 0,
    packet_losses INTEGER DEFAULT 0,
    mean_latency_ms FLOAT,
    p99_latency_ms FLOAT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    stopped_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_control_sessions_user_id ON control_sessions(user_id);
CREATE INDEX idx_control_sessions_status ON control_sessions(status);
CREATE INDEX idx_control_sessions_created_at ON control_sessions(created_at DESC);

-- Control loop cycles (telemetry)
CREATE TABLE IF NOT EXISTS control_cycles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES control_sessions(id) ON DELETE CASCADE,
    cycle_index INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Sensor data
    sensor_value FLOAT NOT NULL,
    target_value FLOAT NOT NULL,
    error_value FLOAT NOT NULL,

    -- Control output
    control_signal FLOAT NOT NULL,
    throttle INTEGER NOT NULL,

    -- Performance
    cycle_latency_ms FLOAT NOT NULL,
    network_delay_ms FLOAT NOT NULL,
    packet_lost BOOLEAN NOT NULL DEFAULT FALSE,

    -- Optional HBCM feedback
    cardiac_stress FLOAT
);

CREATE INDEX idx_control_cycles_session_id ON control_cycles(session_id);
CREATE INDEX idx_control_cycles_timestamp ON control_cycles(timestamp DESC);
CREATE INDEX idx_control_cycles_composite ON control_cycles(session_id, cycle_index);

-- ============================================================================
-- PERFORMANCE METRICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,  -- 'counter', 'gauge', 'histogram', 'summary'
    metric_value FLOAT NOT NULL,
    labels JSONB,  -- Key-value pairs for metric labels
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp DESC);
CREATE INDEX idx_performance_metrics_labels ON performance_metrics USING GIN (labels);
CREATE INDEX idx_performance_metrics_composite ON performance_metrics(metric_name, timestamp DESC);

-- ============================================================================
-- AUDIT LOGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL,  -- 'login', 'logout', 'create_simulation', etc.
    resource_type VARCHAR(100),  -- 'simulation', 'user', 'session', etc.
    resource_id UUID,
    details JSONB,  -- Additional context
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- ============================================================================
-- NODE-RED DASHBOARD PERSISTENCE
-- ============================================================================

CREATE TABLE IF NOT EXISTS dashboards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    layout JSONB NOT NULL,  -- Dashboard layout configuration
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dashboards_user_id ON dashboards(user_id);
CREATE INDEX idx_dashboards_is_public ON dashboards(is_public);

-- Widget configurations
CREATE TABLE IF NOT EXISTS widgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    widget_type VARCHAR(100) NOT NULL,  -- 'chart', 'gauge', 'table', etc.
    title VARCHAR(255),
    configuration JSONB NOT NULL,  -- Widget-specific config
    position_x INTEGER NOT NULL,
    position_y INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_widgets_dashboard_id ON widgets(dashboard_id);

-- ============================================================================
-- TRIGGERS & FUNCTIONS
-- ============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dashboards_updated_at BEFORE UPDATE ON dashboards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_widgets_updated_at BEFORE UPDATE ON widgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Active simulations view
CREATE OR REPLACE VIEW active_simulations AS
SELECT
    s.id,
    s.name,
    u.username,
    s.status,
    s.duration_seconds,
    s.created_at,
    s.started_at,
    EXTRACT(EPOCH FROM (NOW() - s.started_at)) AS running_time_seconds
FROM simulations s
LEFT JOIN users u ON s.user_id = u.id
WHERE s.status IN ('pending', 'running')
ORDER BY s.created_at DESC;

-- User activity view
CREATE OR REPLACE VIEW user_activity AS
SELECT
    u.id,
    u.username,
    u.email,
    u.role,
    COUNT(DISTINCT s.id) AS total_simulations,
    COUNT(DISTINCT cs.id) AS total_control_sessions,
    u.last_login_at,
    u.created_at
FROM users u
LEFT JOIN simulations s ON u.id = s.user_id
LEFT JOIN control_sessions cs ON u.id = cs.user_id
GROUP BY u.id, u.username, u.email, u.role, u.last_login_at, u.created_at;

-- Performance summary view
CREATE OR REPLACE VIEW performance_summary AS
SELECT
    metric_name,
    metric_type,
    COUNT(*) AS sample_count,
    AVG(metric_value) AS avg_value,
    MIN(metric_value) AS min_value,
    MAX(metric_value) AS max_value,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY metric_value) AS p50_value,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY metric_value) AS p95_value,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY metric_value) AS p99_value,
    MAX(timestamp) AS last_updated
FROM performance_metrics
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY metric_name, metric_type;

-- ============================================================================
-- SEED DATA (Development Only)
-- ============================================================================

-- Create default admin user (password: 'admin' - CHANGE IN PRODUCTION!)
-- Password hash generated with bcrypt, rounds=12
INSERT INTO users (username, email, password_hash, first_name, last_name, role)
VALUES (
    'admin',
    'admin@multi-heart-model.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ztP6xDGLvW6i',  -- 'admin'
    'System',
    'Administrator',
    'admin'
)
ON CONFLICT (username) DO NOTHING;

-- Create demo researcher user (password: 'researcher' - CHANGE IN PRODUCTION!)
INSERT INTO users (username, email, password_hash, first_name, last_name, role)
VALUES (
    'researcher',
    'researcher@multi-heart-model.local',
    '$2b$12$8P.TkZvFz0JMHxQqKJ4Lxu8qN7mZJ4uV5dE/8zGx3RkV5T8cE5K5y',  -- 'researcher'
    'Demo',
    'Researcher',
    'researcher'
)
ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- MAINTENANCE PROCEDURES
-- ============================================================================

-- Clean old sessions
CREATE OR REPLACE FUNCTION clean_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Archive old simulation results
CREATE OR REPLACE FUNCTION archive_old_simulation_results(days_old INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- In production, this would move data to archive table
    -- For now, just count what would be archived
    SELECT COUNT(*) INTO archived_count
    FROM simulation_results sr
    JOIN simulations s ON sr.simulation_id = s.id
    WHERE s.completed_at < NOW() - (days_old || ' days')::INTERVAL;

    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Vacuum and analyze (run periodically)
CREATE OR REPLACE FUNCTION maintenance_vacuum_analyze()
RETURNS VOID AS $$
BEGIN
    VACUUM ANALYZE users;
    VACUUM ANALYZE simulations;
    VACUUM ANALYZE simulation_results;
    VACUUM ANALYZE control_sessions;
    VACUUM ANALYZE control_cycles;
    VACUUM ANALYZE performance_metrics;
    VACUUM ANALYZE audit_logs;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PERMISSIONS (Application User)
-- ============================================================================

-- Create application user (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'multiheart_app') THEN
        CREATE USER multiheart_app WITH PASSWORD 'change_me_in_production';
    END IF;
END
$$;

-- Grant permissions
GRANT CONNECT ON DATABASE multiheart_prod TO multiheart_app;
GRANT USAGE ON SCHEMA public TO multiheart_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO multiheart_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO multiheart_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO multiheart_app;

-- Grant permissions on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO multiheart_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO multiheart_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO multiheart_app;

-- ============================================================================
-- COMPLETION
-- ============================================================================

-- Analyze all tables for query optimization
ANALYZE;

-- Print summary
DO $$
DECLARE
    table_count INTEGER;
    view_count INTEGER;
    function_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

    SELECT COUNT(*) INTO view_count FROM information_schema.views
    WHERE table_schema = 'public';

    SELECT COUNT(*) INTO function_count FROM information_schema.routines
    WHERE routine_schema = 'public' AND routine_type = 'FUNCTION';

    RAISE NOTICE 'Database initialization complete!';
    RAISE NOTICE 'Tables created: %', table_count;
    RAISE NOTICE 'Views created: %', view_count;
    RAISE NOTICE 'Functions created: %', function_count;
END
$$;
