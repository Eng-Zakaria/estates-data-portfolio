# Mapping to real building systems

Everything in this project is simulated. This note is the honest description of
what would have to change to point the same pipeline at a real campus, and what
the design already gets right or deliberately leaves out.

> **Read this before quoting anything from the dashboards.** Every value in
> this project comes from `src/simulator.py`. No real building, controller,
> meter or sensor is involved, and no number here describes the performance of
> any real plant.

## What replaces what

| this project | a real deployment | effort |
|---|---|---|
| `src/simulator.py` (paho-mqtt publisher) | a BACnet/IP gateway or Modbus poller per controller | the largest piece of work |
| `campus/<building>/<system>/<equipment>/<point_class>` | gateway-published topic; the segment names are still yours to choose | mapping work, not redesign |
| `contracts/validation_rules.json` | ranges taken from the site's own controller configuration | needs the site data |
| `src/point_registry.csv` `source_address` | the site's BACnet object list / Modbus register map | needs the site data |
| TimescaleDB `bms.readings` | unchanged | none |
| Grafana dashboards | unchanged | none |
| `src/health.py` rules | unchanged, retune the thresholds | threshold work |

## BACnet: COV subscriptions versus polling

The simulator publishes every point on a fixed cadence, which corresponds to
neither of the two real BACnet strategies cleanly.

**Polling** reads a block of `present-value` properties on an interval. For a
294-point site at a 5-minute cadence that is roughly one `ReadPropertyMultiple`
request per controller per cycle. The cost is predictable and the traffic is
low, which is why many sites use it. The cost is that a controller that is
slowly failing still answers, just with old values, and polling cannot tell the
difference between "unchanged" and "stale". That distinction is exactly what
`STALENESS` needs, so a polling gateway has to timestamp on *read* and let the
downstream staleness rule do the work.

**COV (Change of Value)** subscriptions have the controller push a
`notify`/`COVNotification` when a property changes. That is the closest match
to what the simulator does, and it is much cheaper on the wire for points that
sit still. It has two sharp edges a real integration must handle:

* **The deadband problem.** A property with no intrinsic deadband can generate
  a notification per LSB, which on a noisy sensor is a flood. The gateway must
  apply a deadband per point class, and that deadband is a real engineering
  choice: too small and the broker drowns, too large and a slow drift is
  invisible. It belongs in the point registry, per point class, not in code.
* **Subscription lifetime.** COV subscriptions are not durable. They need
  re-establishing after a controller or network restart, and a gateway that
  reconnects silently has created exactly the stale point the dashboard is
  meant to show. The `bms.alerts` staleness check is what catches this, so a
  real deployment should treat a rising staleness alert count as a gateway
  health signal, not only a plant one.

A third option, **BACnet/SC** (secure connect), exists and is worth naming: it
adds authentication and encryption over TCP, which a campus network will
usually require. It changes the transport, not the object model, so none of the
rest of this document changes.

## Modbus

Modbus has no discovery, no units, no timestamps and no change notification.
Every one of those gaps lands on the integration layer:

| gap | consequence for this pipeline |
|---|---|
| no timestamps | the gateway stamps on read. A slow poll over many registers makes the timestamp a range, not a point |
| no units | `unit` must come from the site configuration. The contract's per-class units are a *check* on that configuration, not a substitute for it |
| no quality flag | `quality` is the gateway's own verdict (comms OK, response sane). There is nothing in Modbus to tell it |
| register addressing | 16-bit registers, no float type. A 32-bit float occupies two registers, and byte order (word swap) differs between vendors |
| device limits | one outstanding request per TCP connection is the safe assumption for many devices |

The word-swap problem is the classic source of silently wrong engineering data:
a flow reading 1,234.5 kWh as 12,345 or as 0.005 gets no error from Modbus at
all. A real gateway must be tested against a known register value at
commissioning, and that test belongs in a documented commissioning record rather
than in the ingest pipeline.

## The read-only integration principle

**The integration is read-only. It never writes to a controller.**

A BMS controls heating, cooling and ventilation in buildings people are sitting
in. A bug in an analytics pipeline that can also command plant is a safety
problem, not a data quality problem. Concretely:

* No write, no override, no command in any code path here.
* Database credentials for the analytics side are read-only against the
  historical store. Nothing in this project can reach a controller because
  nothing in this project speaks BACnet or Modbus at all.
* Alerts route to a person or a ticketing system, not back to a controller. An
  operator acts; the pipeline observes.

If a project ever needs to write to plant, that is a different project with a
different risk assessment, and it belongs on the controls engineer's desk, not
in a data pipeline.

## Network segmentation

A defensible layout, roughly inside out:

```
[ office network | student network ]
              |
        (no route)
              |
  +-----------v-----------+
  |  OT / BMS VLAN        |   controllers, gateways
  |  - no direct Internet |
  |  - gateway is the only
  |    host that talks to
  |    both segments      |
  +-----------+-----------+
              |
  +-----------v-----------+
  |  DMZ / integration    |   MQTT broker, ingest, TimescaleDB
  |  - broker is the only
  |    service open to    |
  |    the OT VLAN        |
  |  - everything else is |
  |    outbound-only      |
  +-----------------------+
```

Points in that layout:

* The **gateway sits on both sides**. It polls controllers on the OT VLAN and
  publishes to the broker in the DMZ. That is the whole trust boundary: one
  process that is allowed to speak both protocols, and nothing else.
* **The broker does not expose 1883 to the office or student networks.** An
  open MQTT port on a building network is a well-known way to inject readings
  into a monitoring system. The demo binds it to `127.0.0.1` on the host and
  gives Node-RED a separate listener on the compose network (see
  [`mosquitto.conf`](../mosquitto.conf) and `scripts/patch_broker.py`).
* **Nothing in the DMZ initiates a connection to a controller.** Traffic to the
  OT VLAN is the gateway's, and it is polled or subscribed, never inbound from
  the analytics side.
* **MQTT over TLS**, with per-device credentials, not the shared password this
  demo uses. The demo's password file exists to show the mechanism works and to
  keep anonymous access off; it is labelled `DEMO ONLY` in `.env.example` and it
  is not a model for production.

## Security in this demo, and its limits

| control | here | a real deployment |
|---|---|---|
| no anonymous MQTT | password file required, `allow_anonymous false` | per-device credentials, rotated |
| credentials in `.env` | yes, `DEMO ONLY` values | a secret store (Vault, cloud secret manager) |
| passwords in the repo | none: the flow JSON holds no credential, and a test asserts it | same |
| TLS | not enabled | required on any network the broker is not alone on |
| Node-RED editor auth | password via env | SSO, and the editor read-only in production |
| database access | compose network only, host-published on 5433 for the demo | no host port publication; network policy instead |

The demo's ports are published to the host so a laptop can reach Grafana and
psql. A real deployment would publish neither: an operator connects through a
VPN or an SSH tunnel.

## Things this design deliberately does not do

* **No control.** Covered above; it is the most important line in the document.
* **No identity or access modelling.** Access control for the dashboards, per
  building or per role, is not attempted. Grafana's folder permissions would be
  the starting point.
* **No long-term raw retention beyond the aggregate.** 400 days of raw readings
  with 7-day compression is a starting point for sizing, not a retention policy
  agreed with anyone. A real policy is a conversation with the estates data
  protection contact, and it interacts with building occupancy data.
* **No personal data.** Point data is plant and room telemetry with no
  individual attached. Occupancy is a count per room per 5 minutes, which is
  aggregate by construction. A real estate with per-person tracking would change
  that, and P17's `docs/privacy.md` is the place that discussion belongs.
* **No BACnet/IP device simulation.** The spec listed a BACpypes3 simulated
  device as a stretch goal; it was not done. The topic abstraction is the part
  that matters for the data contract, and the simulator already exercises that
  contract end to end.