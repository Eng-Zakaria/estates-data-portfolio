# Topic taxonomy

## Shape

```
campus/<building>/<system>/<equipment>/<point_class>
```

Example: `campus/B001/ahu/ahu_01/supply_temp`

| segment | values | source |
|---|---|---|
| `campus` | fixed root | reserves the prefix for other estates systems later |
| `<building>` | `B001`, `B003`, `B007` | matches `B\d{3}` in the contract |
| `<system>` | `ahu`, `boiler`, `pump`, `room` | the service the point belongs to |
| `<equipment>` | `ahu_01`, `boiler_02`, `room_17`, `pump_03` | the physical item |
| `<point_class>` | `supply_temp`, `fan_speed`, `co2`, ... | what is measured |

The authoritative pattern lives in
[`contracts/validation_rules.json`](../contracts/validation_rules.json) as
`topic_pattern`. `src/validate.py` compiles it directly; the Node-RED function
node uses the JavaScript equivalent (`(?<name>...)` instead of Python's
`(?P<name>...)`), and a test asserts the two are the same pattern.

## Why the equipment segment is not optional

An earlier version of this taxonomy omitted it:

```
campus/<building>/<system>/<point_class>
```

That looks tidier and is wrong. `campus/B001/ahu/cooling_valve` is the topic for
`ahu_01`'s cooling valve **and** `ahu_02`'s and `ahu_03`'s. Every message on
that topic resolved to the same `point_id`, so 294 registry points collapsed
onto 45 topics: the plant overview showed one valve three times and lost two
thirds of the data without any error. `tests/test_registry.py::test_topics_are_unique_per_point`
now fails if this happens again.

## Point classes and their units

Units are canonical in the registry and enforced by the contract. Aliases
(`degC`, `°C`, `Celsius`, `degF`, `F`) are normalised on the way in; Fahrenheit
temperatures are converted to Celsius, not rejected, because the point stores
Celsius either way and refusing the reading loses data rather than fixing the
controller.

| point_class | unit | plausible range | typical source |
|---|---|---|---|
| `supply_temp` | C | -20 .. 90 | AHU / boiler supply air or water |
| `return_temp` | C | -20 .. 60 | AHU return air |
| `room_temp` | C | 5 .. 45 | room sensor |
| `setpoint` | C | 5 .. 35 | room controller setpoint |
| `damper_pos` | % | 0 .. 100 | AHU damper actuator |
| `fan_speed` | % | 0 .. 100 | fan VFD feedback |
| `heating_valve` | % | 0 .. 100 | heating valve position |
| `cooling_valve` | % | 0 .. 100 | cooling valve position |
| `co2` | ppm | 250 .. 10000 | room CO2 sensor |
| `occupancy` | count | 0 .. 500 | room people counter |
| `sub_meter_kwh` | kWh | 0 .. 1000 | sub-meter |

## Payload

```json
{"ts": "2026-10-08T01:05:00+00:00", "value": 62.0, "unit": "%", "quality": "good"}
```

| field | type | notes |
|---|---|---|
| `ts` | ISO-8601 with offset | the **event** time, not the send time. `Z` accepted, a naive timestamp is read as UTC |
| `value` | number | string values are rejected (`NON_NUMERIC_VALUE`) |
| `unit` | string | alias-tolerant, must resolve to the class unit |
| `quality` | enum | `good`, `suspect`, `bad` |

`quality` travels with the reading on purpose. The pipeline does **not** drop
`suspect` values: an engineer needs to see that a controller is reporting
trouble, and a dashboard that silently omits those points is worse than one
that shows them flagged.

## Rejection reasons

Every one of these is written to `bms.dead_letter.reason`, and each has a test
that reaches it.

| reason | meaning | typical cause |
|---|---|---|
| `TOPIC_PATTERN` | topic does not match the contract | new device wired in with an ad-hoc topic |
| `MALFORMED_JSON` | body is not parseable JSON | serial-to-IP gateway truncating a frame |
| `MISSING_FIELD` | a required field is absent | older firmware publishing a shorter payload |
| `NON_NUMERIC_VALUE` | `value` is not a number | float formatted with a locale decimal comma |
| `QUALITY_INVALID` | `quality` outside the enum | new quality code added by a vendor |
| `UNIT_MISMATCH` | unit does not resolve to the class unit | sensor replaced with a differently-scaled one |
| `OUT_OF_RANGE` | value outside the plausible range for the class | failed sensor, or a genuinely broken reading |
| `TIMESTAMP_FORMAT` | `ts` unparseable | clock unset on the controller |
| `TIMESTAMP_IN_FUTURE` | more than 5 minutes ahead | clock drift, or a replay from a badly-set device |
| `TIMESTAMP_TOO_OLD` | more than 168 hours behind | buffered data flushed after an outage |
| `UNKNOWN_POINT_ID` | topic shape is valid but nothing is registered on it | new plant item not yet added to the registry |

## Subscription patterns

| pattern | used for |
|---|---|
| `campus/#` | the single subscription the demo flow uses: everything, so a new point class is picked up without a flow change |
| `campus/+/ahu/#` | one service across all buildings, e.g. for an AHU-specific dashboard |
| `campus/B001/#` | one building |

A production deployment would also want a dead-letter or quarantine topic
(`campus/dead-letter`) so a failed gateway can hand over buffered readings
without waiting for the broker's retain window; that is not needed here because
the dead letter is a table, not a topic.

## QoS

The demo publishes at QoS 0. Both ends of that choice are deliberate and worth
stating:

* **QoS 0** is enough here because the simulator re-runs from a fixed start
  timestamp, and the `bms.readings` upsert makes a redelivery harmless.
* **QoS 1** would be the floor for a real deployment: at-least-once, so a
  dropped message on a flaky link is recovered, at the cost of duplicates that
  the upsert already tolerates.
* **QoS 2** is not worth it for telemetry. Its exactly-once guarantee needs a
  four-way handshake per message, which on a 294-point 5-minute cadence is
  roughly 1,400 extra round trips a day for no operational benefit.