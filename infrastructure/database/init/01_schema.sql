-- Multi-Heart-Model Production Database Schema
-- PostgreSQL 15+

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE;

-- Users and Authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- API Keys for external integrations
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    scopes TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used TIMESTAMP WITH TIME ZONE
);

-- Simulations
CREATE TABLE IF NOT EXISTS simulations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    simulation_type VARCHAR(50) NOT NULL, -- 'hbcm', 'organ_chip', 'bci_integration'
    status VARCHAR(50) DEFAULT 'created', -- 'created', 'running', 'completed', 'failed'
    configuration JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds NUMERIC,
    error_message TEXT
);

CREATE INDEX idx_simulations_user_id ON simulations(user_id);
CREATE INDEX idx_simulations_status ON simulations(status);
CREATE INDEX idx_simulations_type ON simulations(simulation_type);

-- Simulation Results (TimescaleDB hypertable)
CREATE TABLE IF NOT EXISTS simulation_data (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    simulation_id UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    timestep BIGINT NOT NULL,
    neural_v DOUBLE PRECISION,
    neural_w DOUBLE PRECISION,
    cardiac_x DOUBLE PRECISION,
    cardiac_y DOUBLE PRECISION,
    bci_signal DOUBLE PRECISION,
    control_signal DOUBLE PRECISION,
    metadata JSONB,
    PRIMARY KEY (simulation_id, time)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('simulation_data', 'time', if_not_exists => TRUE);

-- BCI Sessions
CREATE TABLE IF NOT EXISTS bci_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    simulation_id UUID REFERENCES simulations(id) ON DELETE SET NULL,
    adapter_type VARCHAR(50) NOT NULL, -- 'openbci', 'lsl', 'synthetic'
    configuration JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'initialized',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    stopped_at TIMESTAMP WITH TIME ZONE,
    total_samples BIGINT,
    error_message TEXT
);

-- BCI Data (TimescaleDB hypertable)
CREATE TABLE IF NOT EXISTS bci_data (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    session_id UUID NOT NULL REFERENCES bci_sessions(id) ON DELETE CASCADE,
    channel_name VARCHAR(50) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    sample_number BIGINT,
    metadata JSONB,
    PRIMARY KEY (session_id, time, channel_name)
);

SELECT create_hypertable('bci_data', 'time', if_not_exists => TRUE);

-- Performance Metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    simulation_id UUID REFERENCES simulations(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL, -- 'latency', 'throughput', 'lipschitz_constant'
    metric_value DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_performance_metrics_simulation ON performance_metrics(simulation_id);
CREATE INDEX idx_performance_metrics_type ON performance_metrics(metric_type);

-- Validation Results
CREATE TABLE IF NOT EXISTS validation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_name VARCHAR(255) NOT NULL,
    test_type VARCHAR(100) NOT NULL, -- 'spacex', 'tesla', 'px4', 'carla', 'starlink'
    status VARCHAR(50) NOT NULL, -- 'passed', 'failed', 'warning'
    score DOUBLE PRECISION,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_validation_results_type ON validation_results(test_type);
CREATE INDEX idx_validation_results_status ON validation_results(status);

-- External Integration Logs
CREATE TABLE IF NOT EXISTS integration_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_type VARCHAR(100) NOT NULL, -- 'opensim', 'starlink', 'nasa_power', 'tesla'
    operation VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    request_data JSONB,
    response_data JSONB,
    error_message TEXT,
    latency_ms NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_integration_logs_type ON integration_logs(integration_type);
CREATE INDEX idx_integration_logs_created ON integration_logs(created_at);

-- System Events (Audit Log)
CREATE TABLE IF NOT EXISTS system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    event_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_system_events_type ON system_events(event_type);
CREATE INDEX idx_system_events_user ON system_events(user_id);
CREATE INDEX idx_system_events_created ON system_events(created_at);

-- MQTT Messages Archive
CREATE TABLE IF NOT EXISTS mqtt_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic VARCHAR(500) NOT NULL,
    payload JSONB,
    qos INTEGER,
    retain BOOLEAN,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mqtt_messages_topic ON mqtt_messages(topic);
CREATE INDEX idx_mqtt_messages_timestamp ON mqtt_messages(timestamp);

-- Device Registry (for QUANT hardware, etc.)
CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_type VARCHAR(100) NOT NULL, -- 'quant_motor', 'opensim_node', 'bci_adapter'
    device_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    configuration JSONB,
    status VARCHAR(50) DEFAULT 'offline',
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_devices_type ON devices(device_type);
CREATE INDEX idx_devices_status ON devices(status);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Materialized Views for Analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS simulation_statistics AS
SELECT
    simulation_type,
    status,
    COUNT(*) as total_simulations,
    AVG(duration_seconds) as avg_duration,
    MIN(duration_seconds) as min_duration,
    MAX(duration_seconds) as max_duration
FROM simulations
GROUP BY simulation_type, status;

CREATE UNIQUE INDEX idx_simulation_stats ON simulation_statistics(simulation_type, status);

-- Performance Metrics Summary
CREATE MATERIALIZED VIEW IF NOT EXISTS performance_summary AS
SELECT
    simulation_id,
    AVG(CASE WHEN metric_type = 'latency' THEN metric_value END) as avg_latency_ms,
    MAX(CASE WHEN metric_type = 'latency' THEN metric_value END) as max_latency_ms,
    AVG(CASE WHEN metric_type = 'throughput' THEN metric_value END) as avg_throughput,
    MAX(CASE WHEN metric_type = 'lipschitz_constant' THEN metric_value END) as max_lipschitz
FROM performance_metrics
GROUP BY simulation_id;

CREATE UNIQUE INDEX idx_performance_summary_sim ON performance_summary(simulation_id);

-- Create default admin user (password: admin123 - CHANGE IN PRODUCTION!)
-- Password hash for 'admin123' using bcrypt
INSERT INTO users (username, email, password_hash, full_name, role)
VALUES (
    'admin',
    'admin@multi-heart-model.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU0kEHe4CjVW',
    'System Administrator',
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mhm_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mhm_user;

-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts and authentication';
COMMENT ON TABLE simulations IS 'Heart-brain coupling and organ chip simulations';
COMMENT ON TABLE simulation_data IS 'TimescaleDB hypertable for high-frequency simulation data';
COMMENT ON TABLE bci_sessions IS 'BCI data acquisition sessions';
COMMENT ON TABLE bci_data IS 'TimescaleDB hypertable for BCI channel data';
COMMENT ON TABLE performance_metrics IS 'System performance metrics (<100ms latency tracking)';
COMMENT ON TABLE validation_results IS 'SpaceX/Tesla/PX4/CARLA validation test results';
COMMENT ON TABLE integration_logs IS 'External integration activity logs';
COMMENT ON TABLE devices IS 'Hardware device registry (QUANT, OpenSim, etc.)';
