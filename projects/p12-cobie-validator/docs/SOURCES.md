# P12 sources — COBie specification (verified 2026-10-06)

> Hard rule: no standard codes, sheet layouts or field rules are invented from memory.
> What is implemented below was read from the public sources; the AIR file is an
> explicitly simulated employer requirement, not a standard.

| Item | Source | Version | Retrieved | Used for |
|---|---|---|---|---|
| COBie overview, purpose and sheet model | https://www.buildingsmart.org/standards/cobie/ | Current (cited 2026-10-06) | 2026-10-06 (direct fetch timed out this session; sheet set cross-checked via NBS + NBIMS sources below) | 19-sheet set implemented in `make_sample_cobie.py` and `rules/cobie.yml` |
| COBie worksheets explained (Contact/Component/Job semantics; Component instance → Type + Space) | https://www.thenbs.com/knowledge/what-is-cobie | Current (retrieved via search 2026-10-06) | 2026-10-06 | Confirms `TypeName`/`Space` FK design ("instance of a type in a space"); column semantics |
| COBie v2.4 table structure (Contact/Facility/Floor/Space/Zone/Type/Component/System/Assembly + process/support tables) | https://nibs.org/nbims/v3/cobie (NBIMS COBie V3 §4, documents v2.4 lineage) | COBie v2.4 lineage | 2026-10-06 | Column order for `Component`, mandatory-field set, FK pairs |
| UK BIM Framework guidance (COBie as the operational handover exchange) | https://ukbimframework.org/ | Current (cited 2026-10-06) | 2026-10-06 | Confirms COBie role for handover; no codes copied |
| ISO 8601 date format | https://www.iso.org/iso-8601-date-and-time-format.html | Current | 2026-10-06 | `format_*` rules require `YYYY-MM-DD` |

Key relationships implemented (all from the v2.4 layout):
Component → Type (`TypeName`), Component → Space (`Space`, multi-value on `,;|`),
Space → Floor (`FloorName`), System → Component (`ComponentNames`, multi-value),
Job → Type (`TypeName`), Zone → Space (`SpaceNames`, multi-value),
`CreatedBy` → Contact (`Email`).

What was NOT taken from a standard (stated honestly):
- `rules/air.yml` is a simulated employer AIR (required manufacturer/model/warranty/
  expected-life/serial/install-date). It is editable YAML, not a statutory list.
- Category validation is a syntactic pattern (`letters/numbers/spaces/hyphens`),
  not Uniclass membership — that check waits for P13 reference data.
- Numeric ranges (floor height 2–30 m, expected life 1–100 y, warranty 0–120 mo,
  area > 0) are plausibility guards, not statutory values.
