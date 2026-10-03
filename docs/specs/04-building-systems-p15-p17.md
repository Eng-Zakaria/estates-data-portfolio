# Building systems and sensor projects P15-P17

These cover "integrate data from building systems (BMS, meters, sensors)" and the desirable CAFM/BMS/energy/sensor experience. Everything is simulated or uses open datasets. Say so in every README, and describe how the design would map to real BACnet/Modbus gateways.

Depends on: foundation (meters, sensors, timetable, ground truth). P15 can run independently of the lakehouse; P16 and P17 read from gold or directly from the foundation.

---

## P15: BMS / sensor ingestion (MQTT → Node-RED → TimescaleDB → Grafana)

**Location:** `projects/p15-bms-iot/`
**Criteria:** E2, E4, D2 (Node-RED), D3 (monitoring), D7
**Stack:** Docker Compose with Mosquitto (MQTT), Node-RED, TimescaleDB (PostgreSQL), Grafana; Python simulator (paho-mqtt); optional BACpypes3 BACnet/IP simulated device as a stretch goal.

### Simulator
- ~20 plant items (AHUs, boilers, pumps) and ~50 rooms across 3 buildings.
- Points: supply/return air temperature, damper position, fan speed, heating/cooling valve position, room temperature and setpoint, CO₂, occupancy, electrical sub-meter kWh.
- Topics `campus/<building>/<system>/<point>`; JSON payload `{ts, value, unit, quality}`; intervals 1-15 min; `--speedup` factor (24 h in ≤ 10 min).
- **Fault modes (configurable, logged to a truth file):** stuck valve, sensor drift, comms dropout, simultaneous heating and cooling, out-of-hours operation, malformed payloads.

### Node-RED flows (exported JSON committed to the repo)
Subscribe → validate (schema, plausible range, timestamp sanity) → normalise units → map point names to canonical `point_id` via the point registry (CSV lookup) → batch insert into `bms.readings(ts, point_id, value, quality)` → malformed messages to `bms.dead_letter` → last-seen heartbeat per point → raise an alert row when no data for N minutes.

### Database
- Tables: `bms.points` (point_id, building, system, equipment, point_class, unit, source_address), hypertable `bms.readings`, `bms.dead_letter`, `bms.alerts`.
- Continuous aggregates (15-min, hourly, daily), compression and retention policies.
- Nightly export of aggregates to Parquet for lakehouse ingestion (`bms_trends` source in P01).

### Grafana (dashboards-as-code, provisioned)
Plant overview; point health (staleness, flat-lines, comms quality); active faults; data-completeness heatmap.

### Security and docs
MQTT with a password file (no anonymous), `.env` for credentials, notes on TLS in a real deployment; `docs/architecture.md` (Mermaid), `docs/topic-taxonomy.md`, `docs/point-naming.md`, `docs/mapping-to-real-systems.md` (BACnet objects/COV vs polling, Modbus registers, gateways, network segmentation, read-only integration principle).

### Acceptance
- `make iot-up` then `make iot-demo` produce data in Grafana within 2 minutes.
- 24 simulated hours with ≥ 99.9% ingestion of valid messages; malformed messages found in dead-letter with reasons; every injected fault visible in point health or alerts (fault detection table in README).
- Flow JSON imports cleanly on a fresh Node-RED.
- Tests for the simulator, for the SQL schema (migration applies cleanly), and for the ingestion contract.

**CV bullet:** *Built a simulated BMS ingestion stack (MQTT, Node-RED, TimescaleDB, Grafana) with validation, dead-letter handling, continuous aggregates and fault monitoring; documented how it maps to BACnet/Modbus gateways.*

---

## P16: Energy anomaly and fault detection

**Location:** `projects/p16-energy-anomaly/`
**Criteria:** E3, E5 (feeds dashboards), D7, D8
**Stack:** Python, pandas, scikit-learn, statsmodels or `ruptures` for change points, plotly, Jinja2, optional Streamlit, pytest.

### Data
1. **Building Data Genome Project 2** (open dataset of hourly building energy and weather; verify and record the licence; download by script). Filter to education-type buildings, 20-50 buildings from one or two sites.
2. Campus synthetic half-hourly data with planted anomalies (B007 overnight baseload, B019 summer heating, M-B015-E01 flat-line).

### Pipeline
1. **Cleaning:** gaps, zero runs, flat-lines, unit sanity, outlier winsorising for baseline fitting only.
2. **Baselines:** (a) weekday/hour median profile; (b) regression on outdoor temperature (degree-hours), hour-of-week and holiday flags; (c) gradient boosting; **rolling-origin time-series cross-validation**; report CVRMSE/NMBE-style fit metrics.
3. **Anomaly detectors:** robust residual z-score (MAD); Isolation Forest on engineered features; CUSUM / change-point detection for sustained shifts (baseload creep); rule for out-of-hours consumption above x% of peak.
4. **Fault typology:** high overnight baseload, weekend operation, step change, gradual drift, spike, flat-line/meter fault, missing data.
5. **Savings estimate:** kWh, £ (configurable tariff), kgCO₂e (factor table from P08), annualised, with an uncertainty range and the assumptions stated.
6. **Prioritised action list** with evidence plots per finding.

### Evaluation
- Inject ≥ 200 synthetic anomalies (known type, magnitude, duration) into held-out series; report precision, recall, F1 and detection delay per type and per method.
- For real BDG2 data (no labels): manual review of top-N flags documented with plots; do not claim accuracy.
- Planted campus findings: report whether and when each is detected.

### Outputs
`anomalies.parquet`, `building_scorecard.parquet`, per-building HTML reports, Power BI handoff for an "Energy exceptions" page (feeds P08).

### Acceptance
- `make eval` reproduces all metrics from fixed seeds; numbers in README exactly as measured.
- Planted B007 and B019 findings are in the top 3 of the action list, with savings estimates.
- Tests for each detector on synthetic series with known answers (for example a pure step change at a known timestamp).

---

## P17: Smart Campus air quality and occupancy analytics

**Location:** `projects/p17-air-quality-occupancy/`
**Criteria:** E3, E4, D7
**Stack:** Python, pandas/DuckDB, scikit-learn, plotly, optional Streamlit, pytest.
**Data:** foundation `sensors`, `sensor_readings` (CO₂, temperature, humidity, occupancy count at 15 min for 150 rooms), `timetable_events`, `spaces`.

### Privacy note (include in README)
Aggregate counts only, no personal data, no device identifiers. Add `docs/privacy.md` covering data-minimisation, retention and a pointer that a real deployment would need a DPIA.

### Analyses
1. **Ventilation adequacy:** % of occupied time above configurable CO₂ thresholds (defaults 1,000 and 1,500 ppm; **verify guideline sources and cite them** in `docs/methodology.md`), peak CO₂ per session, CO₂ rise rate per occupant, optional air-change-rate estimate from decay curves after sessions end.
2. **Thermal comfort:** hours outside a configurable band; overheating hours.
3. **Actual vs timetabled occupancy:** no-show rate, over-capacity sessions, chronic over-booking vs under-use. Write results to `fct_space_observed_occupancy` for P06.
4. **Out-of-hours conditioning:** rooms heated or ventilated while empty (setpoint held vs occupancy); rough energy waste estimate linking to P16/P08.
5. **Sensor health:** dropouts, stuck values, drift (for example 1st-percentile CO₂ trending upward during long unoccupied periods).
6. **Room archetypes:** k-means on usage and CO₂ profiles; label clusters in plain English.
7. Optional: next-day building occupancy forecast (gradient boosting) with a naive-baseline comparison.

### Outputs
`room_scorecard.parquet` (ventilation risk, comfort risk, utilisation flags, sensor health), `sensor_health.parquet`, a "Healthy buildings" Power BI page spec, a short methodology note.

### Acceptance
- The planted B005 lecture theatre CO₂ problem is ranked in the top 3 ventilation-risk rooms; SN-0042 drift detected with an estimated start week within ±1 week.
- Occupancy no-show findings for B003 match the foundation's ground truth within a stated tolerance.
- Unit tests with synthetic CO₂ curves (known rise rate, known decay) check the calculations.
