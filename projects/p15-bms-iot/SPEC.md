# P15 - BMS / sensor ingestion (MQTT -> Node-RED -> TimescaleDB -> Grafana)

**Location:** `projects/p15-bms-iot/`
**Criteria:** E2, E4, D2 (Node-RED), D3 (monitoring), D7
**Stack:** Docker Compose with Mosquitto (MQTT), Node-RED, TimescaleDB (PostgreSQL), Grafana; Python simulator (paho-mqtt); optional BACpypes3 BACnet/IP simulated device as a stretch goal.

## Simulator

- ~20 plant items (AHUs, boilers, pumps) and ~50 rooms across 3 buildings.
- Points: supply/return air temperature, damper position, fan speed, heating/cooling valve position, room temperature and setpoint, CO2, occupancy, electrical sub-meter kWh.
- Topics `campus/<building>/<system>/<point>`; JSON payload `{ts, value, unit, quality}`; intervals 1-15 min; `--speedup` factor (24 h in <= 10 min).
- **Fault modes (configurable, logged to a truth file):** stuck valve, sensor drift, comms dropout, simultaneous heating and cooling, out-of-hours operation, malformed payloads.

## Node-RED flows (exported JSON committed to the repo)

Subscribe -> validate (schema, plausible range, timestamp sanity) -> normalise units -> map point names to canonical `point_id` via the point registry (CSV lookup) -> batch insert into `bms.readings(ts, point_id, value, quality)` -> malformed messages to `bms.dead_letter` -> last-seen heartbeat per point -> raise an alert row when no data for N minutes.

## Database

- Tables: `bms.points` (point_id, building, system, equipment, point_class, unit, source_address), hypertable `bms.readings`, `bms.dead_letter`, `bms.alerts`.
- Continuous aggregates (15-min, hourly, daily), compression and retention policies.
- Nightly export of aggregates to Parquet for lakehouse ingestion (`bms_trends` source in P01).

## Grafana (dashboards-as-code, provisioned)

Plant overview; point health (staleness, flat-lines, comms quality); active faults; data-completeness heatmap.

## Security and docs

MQTT with a password file (no anonymous), `.env` for credentials, notes on TLS in a real deployment; `docs/architecture.md` (Mermaid), `docs/topic-taxonomy.md`, `docs/point-naming.md`, `docs/mapping-to-real-systems.md` (BACnet objects/COV vs polling, Modbus registers, gateways, network segmentation, read-only integration principle).

## Acceptance

- `make iot-up` then `make iot-demo` produce data in Grafana within 2 minutes.
- 24 simulated hours with >= 99.9% ingestion of valid messages; malformed messages found in dead-letter with reasons; every injected fault visible in point health or alerts (fault detection table in README).
- Flow JSON imports cleanly on a fresh Node-RED.
- Tests for the simulator, for the SQL schema (migration applies cleanly), and for the ingestion contract.

**CV bullet:** *Built a simulated BMS ingestion stack (MQTT, Node-RED, TimescaleDB, Grafana) with validation, dead-letter handling, continuous aggregates and fault monitoring; documented how it maps to BACnet/Modbus gateways.*

---

## Deviations from the spec

Recorded honestly rather than silently absorbed.

| spec says | this project does | why |
|---|---|---|
| topics `campus/<building>/<system>/<point>` | `campus/<building>/<system>/<equipment>/<point_class>` | the spec's shape is not unique per point: `campus/B001/ahu/cooling_valve` is the topic for three different AHUs, so 294 points collapse onto 45 topics and most of the data is lost without an error. The equipment segment is not optional. `tests/test_registry.py::test_topics_are_unique_per_point` prevents a regression |
| ~20 plant items, ~50 rooms, 3 buildings | 24 plant items, 51 rooms, 294 points | "about 20"; the third AHU per building exists so the two valve fault rules have disjoint equipment and cannot credit each other's detections |
| nightly export of aggregates **to Parquet** for P01 | `bms_trends_YYYYMMDD.csv`, wide, matching `platform/contracts/bms_trends.yml` | P01 already validates that CSV contract. Writing Parquet would mean changing P01; the spec's intent (hand the lakehouse a nightly file) is met by matching the existing contract. See `docs/architecture.md` and `src/export_bms_trends.py` |
| fault modes include malformed payloads | malformed payloads are injected by the simulator, not listed as a fault class | they are not plant faults; they exercise the dead-letter path. Counted separately in the truth file (`messages_malformed`) so ingestion loss is never conflated with fault detection |
| `docs/security.md` | `docs/mapping-to-real-systems.md`, section "Security in this demo, and its limits" | one document rather than two, so the security claims sit next to the BACnet/Modbus and segmentation discussion they depend on |
| BACpypes3 simulated BACnet/IP device (stretch goal) | not built | the topic abstraction and the ingestion contract are what the data pipeline depends on; a BACnet device would exercise the publisher, not the pipeline. Recorded as not done rather than claimed |
| `make iot-demo` produces data in Grafana within 2 minutes | the target is met for the offline path; the live stack needs Docker Desktop, which was not available in the environment this was built in | see `docs/ACCEPTANCE_P15.md` for exactly what was verified and what was not |