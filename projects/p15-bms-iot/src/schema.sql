-- P15 TimescaleDB schema: BMS ingestion store
--
-- Applied once by the timescaledb container on first boot
-- (docker-entrypoint-initdb.d/01-schema.sql). Re-applying is safe.
--
-- Design notes:
--  * bms.readings is a hypertable partitioned on ts, compressed by point_id.
--  * Continuous aggregates (15 min / hourly / daily) back the Grafana panels
--    and the nightly Parquet export.
--  * Dead-letter and alerts are plain tables: they are low volume and read
--    whole by the point-health dashboard.

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE SCHEMA IF NOT EXISTS bms;

-- ---------------------------------------------------------------- point registry
CREATE TABLE IF NOT EXISTS bms.points (
    point_id       TEXT PRIMARY KEY,
    building       TEXT NOT NULL,
    system         TEXT NOT NULL,
    equipment      TEXT NOT NULL,
    equipment_kind TEXT NOT NULL,
    point_class    TEXT NOT NULL,
    unit           TEXT NOT NULL,
    source_address TEXT,
    first_seen     TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS points_building_idx ON bms.points (building);
CREATE INDEX IF NOT EXISTS points_system_idx ON bms.points (system);

-- ---------------------------------------------------------------- readings
CREATE TABLE IF NOT EXISTS bms.readings (
    ts      TIMESTAMPTZ      NOT NULL,
    point_id TEXT             NOT NULL,
    value   DOUBLE PRECISION,
    unit    TEXT,
    quality TEXT
);

-- hypertable + columnar compression keyed on point_id (points are queried by id)
SELECT create_hypertable('bms.readings', 'ts', if_not_exists => TRUE, migrate_data => TRUE);
ALTER TABLE bms.readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'point_id',
    timescaledb.compress_orderby   = 'ts DESC'
);
SELECT add_compression_policy('bms.readings', INTERVAL '7 days', if_not_exists => TRUE);
-- 13 months of raw history, then rely on the daily continuous aggregate
SELECT add_retention_policy('bms.readings', INTERVAL '400 days', if_not_exists => TRUE);

-- uniqueness is enforced by the application (idempotent upsert on re-delivery)
CREATE UNIQUE INDEX IF NOT EXISTS readings_ts_point_uidx ON bms.readings (ts DESC, point_id);

-- ---------------------------------------------------------------- dead letter
CREATE TABLE IF NOT EXISTS bms.dead_letter (
    id       BIGSERIAL PRIMARY KEY,
    ts       TIMESTAMPTZ NOT NULL DEFAULT now(),
    topic    TEXT,
    payload  TEXT,
    reason   TEXT NOT NULL,
    point_id TEXT
);
CREATE INDEX IF NOT EXISTS dead_letter_ts_idx ON bms.dead_letter (ts DESC);
CREATE INDEX IF NOT EXISTS dead_letter_reason_idx ON bms.dead_letter (reason);

-- ---------------------------------------------------------------- findings
-- Windows produced by the batch detector in src/health.py. Kept separate from
-- bms.alerts: alerts are what the pipeline raises on its own (staleness), while
-- findings need the batch job and carry the evidence an engineer needs to
-- decide whether to visit the plant.
CREATE TABLE IF NOT EXISTS bms.findings (
    start_ts  TIMESTAMPTZ NOT NULL,
    end_ts    TIMESTAMPTZ NOT NULL,
    rule_id   TEXT        NOT NULL,
    point_id  TEXT,
    samples   INTEGER,
    detail    TEXT
);
CREATE INDEX IF NOT EXISTS findings_start_idx ON bms.findings (start_ts DESC);
CREATE INDEX IF NOT EXISTS findings_rule_idx ON bms.findings (rule_id);
-- one row per detected window, so re-loading the same findings is idempotent
CREATE UNIQUE INDEX IF NOT EXISTS findings_uidx ON bms.findings (start_ts, rule_id, point_id);

-- ---------------------------------------------------------------- alerts
CREATE TABLE IF NOT EXISTS bms.alerts (
    id        BIGSERIAL PRIMARY KEY,
    ts        TIMESTAMPTZ NOT NULL DEFAULT now(),
    point_id  TEXT,
    alert_type TEXT NOT NULL,
    severity  TEXT NOT NULL DEFAULT 'warning',
    detail    TEXT,
    resolved_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS alerts_ts_idx ON bms.alerts (ts DESC);
CREATE UNIQUE INDEX IF NOT EXISTS alerts_open_uidx ON bms.alerts (point_id, alert_type) WHERE resolved_at IS NULL;

-- ---------------------------------------------------------------- aggregates
-- refresh windows are deliberately wider than the source interval so a late
-- message still lands in a bucket that is not yet sealed
CREATE MATERIALIZED VIEW IF NOT EXISTS bms.readings_15min
WITH (timescaledb.continuous) AS
SELECT time_bucket(INTERVAL '15 minutes', ts) AS bucket,
       point_id,
       AVG(value) AS avg_value,
       MIN(value) AS min_value,
       MAX(value) AS max_value,
       COUNT(*)   AS samples,
       COUNT(*) FILTER (WHERE quality = 'good') AS good_samples
FROM bms.readings
GROUP BY bucket, point_id
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS bms.readings_hourly
WITH (timescaledb.continuous) AS
SELECT time_bucket(INTERVAL '1 hour', ts) AS bucket,
       point_id,
       AVG(value) AS avg_value,
       MIN(value) AS min_value,
       MAX(value) AS max_value,
       COUNT(*)   AS samples,
       COUNT(*) FILTER (WHERE quality = 'good') AS good_samples
FROM bms.readings
GROUP BY bucket, point_id
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS bms.readings_daily
WITH (timescaledb.continuous) AS
SELECT time_bucket(INTERVAL '1 day', ts) AS bucket,
       point_id,
       AVG(value) AS avg_value,
       SUM(value) AS sum_value,
       MIN(value) AS min_value,
       MAX(value) AS max_value,
       COUNT(*)   AS samples
FROM bms.readings
GROUP BY bucket, point_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('bms.readings_15min',
    start_offset => INTERVAL '2 days', end_offset => INTERVAL '15 minutes',
    schedule_interval => INTERVAL '5 minutes', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('bms.readings_hourly',
    start_offset => INTERVAL '14 days', end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '30 minutes', if_not_exists => TRUE);
SELECT add_continuous_aggregate_policy('bms.readings_daily',
    start_offset => INTERVAL '400 days', end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '2 hours', if_not_exists => TRUE);

-- ---------------------------------------------------------------- views used by Grafana
-- plant overview: latest value per point
CREATE OR REPLACE VIEW bms.v_latest_value AS
SELECT DISTINCT ON (point_id)
       point_id, ts, value, unit, quality
FROM bms.readings
ORDER BY point_id, ts DESC;

-- point health: staleness + completeness in one query
CREATE OR REPLACE VIEW bms.v_point_health AS
SELECT p.point_id,
       p.building,
       p.system,
       p.equipment,
       p.point_class,
       p.unit,
       COUNT(r.ts)                                                        AS samples_24h,
       MAX(r.ts)                                                         AS last_seen,
       ROUND(100.0 * COUNT(r.ts) / 288.0, 2)                              AS completeness_pct,
       ROUND(100.0 * COUNT(r.ts) FILTER (WHERE r.quality = 'good') / NULLIF(COUNT(r.ts), 0), 2)
                                                                            AS good_pct
FROM bms.points p
LEFT JOIN bms.readings r
       ON r.point_id = p.point_id
      AND r.ts > now() - INTERVAL '24 hours'
GROUP BY p.point_id, p.building, p.system, p.equipment, p.point_class, p.unit;

-- completeness heatmap: building x point_class coverage
CREATE OR REPLACE VIEW bms.v_completeness AS
SELECT p.building,
       p.point_class,
       COUNT(r.ts)                                          AS samples,
       ROUND(100.0 * COUNT(r.ts) / (288.0 * COUNT(DISTINCT p.point_id)), 2) AS completeness_pct
FROM bms.points p
LEFT JOIN bms.readings r
       ON r.point_id = p.point_id
      AND r.ts > now() - INTERVAL '24 hours'
GROUP BY p.building, p.point_class;
