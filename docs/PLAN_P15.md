# PLAN: P15 BMS/sensor ingestion (MQTT → Node-RED → TimescaleDB → Grafana)

## Goal
Simulated BMS ingestion stack: MQTT broker, Node-RED flows, TimescaleDB, Grafana dashboards. 24 simulated hours with fault modes, dead-letter queue, continuous aggregates, and fault monitoring. Document mapping to real BACnet/Modbus gateways.

## Tasks
1. Scaffold `projects/p15-bms-iot/`: `src/`, `tests/`, `docs/`, `flows/` (Node-RED JSON), `docker-compose.yml`, `Makefile`.
2. Docker Compose: Mosquitto (MQTT), Node-RED, TimescaleDB (PostgreSQL), Grafana. `.env.example` for credentials.
3. Python simulator (`src/simulator.py`): ~20 plant items, ~50 rooms, 3 buildings. Points: supply/return temp, damper, fan speed, valve, room temp/setpoint, CO2, occupancy, sub-meter kWh. Topics `campus/<building>/<system>/<point>`. JSON `{ts, value, unit, quality}`. 1-15 min intervals. `--speedup` flag. Fault modes logged to truth file.
4. Node-RED flows (`flows/*.json`): subscribe → validate (schema, range, timestamp) → normalise units → map point names to canonical `point_id` via CSV registry → batch insert `bms.readings` → malformed to `bms.dead_letter` → heartbeat last-seen → alert when no data N min.
5. Database (`src/schema.sql`): `bms.points`, hypertable `bms.readings`, `bms.dead_letter`, `bms.alerts`. Continuous aggregates 15-min/hourly/daily. Compression + retention policies. Nightly export to Parquet.
6. Grafana dashboards-as-code (`grafana/provisioning/`): plant overview, point health, active faults, data-completeness heatmap.
7. Docs: `docs/architecture.md` (Mermaid), `docs/topic-taxonomy.md`, `docs/point-naming.md`, `docs/mapping-to-real-systems.md`.
8. Tests: simulator publishes valid JSON; schema migration applies cleanly; ingestion contract (valid messages accepted, malformed rejected to dead-letter).
9. Acceptance: `make iot-up` + `make iot-demo` produce data in Grafana within 2 min; 24h with ≥99.9% ingestion; malformed in dead-letter; every fault visible in point health or alerts.

## Risks
- Docker Compose networking on Windows; verify Mosquitto/Node-RED/TimescaleDB/Grafana health.
- TimescaleDB hypertable creation requires extension; verify migration applies cleanly.
- Node-RED flow JSON import on fresh instance; verify by exporting from a running instance.
- Simulator speedup: 24h in ≤10 min means ~144x; verify MQTT broker handles it.

## Open questions
- Exact BACnet/Modbus mapping details to document in `mapping-to-real-systems.md` (read-only integration principle, network segmentation).
