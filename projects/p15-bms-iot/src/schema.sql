-- P15 TimescaleDB schema
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE SCHEMA IF NOT EXISTS bms;

CREATE TABLE IF NOT EXISTS bms.points (
    point_id TEXT PRIMARY KEY,
    building TEXT,
    system TEXT,
    equipment TEXT,
    point_class TEXT,
    unit TEXT,
    source_address TEXT
);

CREATE TABLE IF NOT EXISTS bms.readings (
    ts TIMESTAMPTZ NOT NULL,
    point_id TEXT NOT NULL,
    value DOUBLE PRECISION,
    quality TEXT,
    PRIMARY KEY (ts, point_id)
);

SELECT create_hypertable('bms.readings', 'ts', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS bms.dead_letter (
    ts TIMESTAMPTZ DEFAULT now(),
    topic TEXT,
    payload TEXT,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS bms.alerts (
    ts TIMESTAMPTZ DEFAULT now(),
    point_id TEXT,
    alert_type TEXT,
    detail TEXT
);

-- Continuous aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS bms.readings_15min
WITH (timescaledb.continuous) AS
SELECT time_bucket('15 minutes', ts) AS bucket, point_id, AVG(value) AS avg_value, COUNT(*) AS samples
FROM bms.readings
GROUP BY bucket, point_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS bms.readings_hourly
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', ts) AS bucket, point_id, AVG(value) AS avg_value, COUNT(*) AS samples
FROM bms.readings
GROUP BY bucket, point_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS bms.readings_daily
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 day', ts) AS bucket, point_id, AVG(value) AS avg_value, COUNT(*) AS samples
FROM bms.readings
GROUP BY bucket, point_id;

-- Compression and retention
ALTER TABLE bms.readings SET (timescaledb.compress, timescaledb.compress_segmentby = 'point_id');
SELECT add_compression_policy('bms.readings', INTERVAL '7 days');
SELECT add_retention_policy('bms.readings', INTERVAL '90 days');
