# Standards

Estates data touches several standards. This section explains which, where each one bites, and how far we have honestly got.

The generated [standards register](../generated/standards-register.md) holds the authoritative table, one page per standard, with its official source URL. Read that for detail; this page is the orientation.

## Status vocabulary

| Status | Meaning | Safe to claim? |
|---|---|---|
| `implemented` | a rule, code list or structure from the official source is encoded and covered by tests | yes, within the stated scope and limitations |
| `mock` | a clearly named development placeholder stands in for the real standard | no. Never present mock output as a standard mapping |
| `awareness-only` | referenced for context; nothing from it is stored or applied | only that we know it exists |
| `not-obtained` | we wanted it and could not obtain it, so nothing is encoded | nothing beyond "not obtained" |

## The short list

| Standard | Status | Where it touches the data |
|---|---|---|
| ISO 19650 and the UK National Annex | implemented (structure, naming, statuses) | information container states, identifier conventions, project handover |
| COBie | implemented (structure, keys, required fields) | handover workbooks, the operations handover pack |
| UK BIM Framework (CDE workflow) | implemented (states and statuses) | the checker that validates container states |
| DESNZ/DEFRA GHG conversion factors | implemented (fetched, versioned) | the carbon mart: kWh to kgCO2e |
| GHG Protocol | awareness-only | scope definitions in the carbon methodology |
| Uniclass | mock | the classifier in the BIM analytics project is a placeholder |
| HESA EMR | mock | the institutional return pack is illustrative, not an official mapping |
| SFG20 | not-obtained | nothing encoded |
| TRAC | awareness-only | nothing encoded |

## How to use the register

1. Read the standard's own entry before assuming a field is required.
2. Check the status. If it says `mock` or `not-obtained`, do not build anything that depends on it.
3. Check `limitations`. "Implemented" always comes with a boundary: which parts, verified how, against which version.
4. Record provenance in the repository's `DATA.md` before committing anything derived from a standard.

## Why we do not reproduce standard text

Standards and guidance are published documents with their own terms. This repository encodes structure, code lists and field rules needed to validate data, and it links to the official source so anyone can check. Nothing here should be treated as a copy of a standard.

## Adopting a standard we do not hold

1. Log it as an open question in the repository so the gap is visible.
2. Record the access terms (licence, price, permitted use) in `DATA.md` before use.
3. Obtain it through the institution's subscription, not a colleague's copy.
4. Encode only what is verifiable, with tests, and state the boundary.
5. Update the register status from `not-obtained` to `mock` first, then to `implemented` when the real codes are in place and tested.

That two-step status change is deliberate: it stops a placeholder from quietly looking real.