# SOURCES: where the codification in `conventions/uk_national_annex.yml` comes from

Read on **2026-10-06**. Both documents were downloaded and read; the quoted text below is what the
sources actually say, so that a reviewer can check the config against them without re-reading the PDFs.

AGENTS.md rule 4: no code list, length or rule from memory. Every value encoded in
`conventions/uk_national_annex.yml` traces to one of the two sources below.

---

## 1. BIM Toolkit | National Annex Guidance (UK National Annex)

- **Publisher:** Centre for Digital Built Britain (CDBB), University of Cambridge, for the BIM Toolkit
- **URL:** https://www.cdbb.cam.ac.uk/files/national_annex_guidance.pdf
- **Retrieved:** 2026-10-06
- **Licence / use:** public sector guidance, read and encoded as a *demonstration* configuration. No
  text is reproduced wholesale; the quotes below are short extracts used to justify specific values.
- **Used for:** the identifier fields, the delimiter, field character counts, the level/location, type
  and discipline code lists, the status code table and the revision format.

### 1.1 Structure and delimiter

> "The unique identifier for information containers should be defined using the following fields in
> the stated order, with each field separated by a delimiter." — §1.1, Table 1.1
> Fields: **Project, Originator, Volume/system, Level, Type, Discipline, Number**
> "In {country name}, the following delimitation should be used: Hyphen-minus, Unicode reference U+002D"

Encoded as: `separator: "-"`, seven identifier fields in that order. The Annex also states the number
of fields "can be shortened or expanded as required", which is why the checker does **not** treat a
short name as a field-count error when every declared field is still present (only `field_missing`).

### 1.2 Field character counts (Table 1.2 and §1.2.1–1.2.7)

| Field | Annex text | Encoded |
|---|---|---|
| 1 Project | "A unique project reference number/code", §1.2.1: "between two and six characters" | `min_length: 2, max_length: 6` |
| 2 Originator | "Originator code, specific to the information author's organisation", §1.2.2: "recommended that the code for this field be between three and six characters" | `min_length: 2, max_length: 6` (table range; the 3–6 recommendation is noted in the field's `source:` line) |
| 3 Volume/system | §1.2.3: "recommended that the code for this field be two characters"; "xZZ refers to all volumes or systems; xXX refers to no volumes or systems" | `length: 2`, `allowed_values: [ZZ, XX]` as seeded codes |
| 4 Level/location | §1.2.4: "recommended that the code for this field be two characters" | `length: 2` + Table 1.3 codes |
| 5 Type | §1.2.5: "recommended that the code for this field be two characters" | `length: 2` + Table 1.4 codes |
| 6 Role / Discipline | §1.2.6: "recommended that the code for this field be one character in length" | `min_length: 1, max_length: 2` + Table 1.5 codes |
| 7 Number | §1.2.7: "recommended that this field be between four and six integer numeric digits in length" | `min_length: 4, max_length: 6, charset: "0-9"` |

Note on field 6: Table 1.1 names it **Role**, §1.2.6 and Table 1.5 name it **Discipline**. The config
uses the name `role` (as in Table 1.1) and records the discrepancy in the field's `source:` line. The
Symetrius article referenced in the open questions below reports the same "Role → Discipline"
renaming in a later edition of the National Annex.

### 1.3 Code lists

- **Table 1.3, level/location:** `ZZ` "Refers to multiple locations", `XX` "Refers to no applicable
  location", `00` "Level 00 (ground floor/base storey)", `01` "Level 01 (first floor/first storey)",
  `B1` "Basement level", `M1` "Mezzanine level, above 01".
- **Table 1.4, type (28 codes):** AF Animation file of a model, BQ Bill of quantities, CA
  Calculations, CM Combined model, CO Correspondence, CP Cost plan, CR Clash rendition, DB Database,
  DR Drawing rendition, FN File note, HS Health and safety, IE Information exchange file, M2 2D model,
  M3 3D model, MI Minutes/action notes, MR Model rendition, MS Method statement, PP Presentation,
  PR Programme, RD Room data sheet, RI Request for information, RP Report, SA Schedule of
  accommodation, SH Schedule, SN Snagging list, SP Specification, SU Survey, VS Visualisation.
- **Table 1.5, discipline (19 codes):** A Architect, B Building surveyor, C Civil engineer,
  D Drainage/highways engineer, E Electrical engineer, F Facilities manager, G Geographical and land
  surveyor, H Heating and ventilation designer, I Interior designer, K Client (appointing party),
  L Landscape architect, M Mechanical engineer, P Public health engineer, Q Quantity surveyor,
  S Structural engineer, T Town and country planner, W Contractor (lead appointed party or appointed
  party), X Subcontractor, Y Specialist designer, Z General (non-disciplinary).

**Why the level/type code lists are only *seeded* lists.** §1.2.3–1.2.6 each end with "This schedule
should be expanded with project-specific codes" / "This schedule could be expanded with project-specific
codes". A closed code list would therefore produce false positives on any real project that adds a code.
The config lists the published codes, and the README documents that a project should replace or extend
the list. (The discipline list is 19 single characters, so it is enforced as-is.)

### 1.4 Worked example (§1.3, Table 1.6)

> Fields `123456 | ORG | A1 | ZZ | MO | A | 0001`
> "The same example as a single string of characters: `123456-ORG-A1-ZZ-MO-A-0001`"

### 1.5 Status and revision (§2, Table 2.2)

> "It is recommended that status codes have two characters."
> "The status will dictate the revision prefix codes and numbering convention…"
> Table 2.2: S0 work in progress; S1 Suitable for coordination; S2 Suitable for information;
> S3 Suitable for review and comment; S4 Suitable for review and authorisation; S5 Suitable for review
> and acceptable; A1, An, etc. Authorised or accepted (contractual); B1, Bn, etc. Partial sign-off with
> comments; CR As constructed record document (contractual revision).
> "Information container revision codes should be two integers, prefixed with the letter for the
> corresponding revision types, as below: P = Preliminary (non-contractual information containers); and
> C = Contractual information containers. For example, preliminary revisions will follow the format P01,
> P02, and so on, and contractual revisions will follow the format C01, C02…"
> "Information containers considered a work in progress should also have a two-integer suffix to
> identify the version, delimited with a full stop, for example, P01.01."

Encoded as: `status.pattern = "S[0-6]|A[1-9][0-9]*|B[1-9][0-9]*|CR"` and
`revision.pattern = "[PC][0-9]{2}(\\.[0-9]{2})?"`. The status field is **pattern**-checked rather than
list-checked because the A/B series is open-ended ("n" = the project information delivery milestone).

### 1.6 Status is metadata, not identification (§2)

> "Metadata does not form part of the information identification, unless information containers are
> exported from the common data environment (CDE), in which case it could be added to the identification
> as a suffix."

This is why `id_fields` in the config lists only the seven identification fields: the checker treats
status and revision as metadata that accompanies an *exported* container name, and uniqueness is
enforced on id + revision.

---

## 2. UK BIM Framework, Guidance Part C (CDE workflow and technical solutions), Edition 1

- **Publisher:** UK BIM Framework
- **URL:** https://ukbimframework.org/wp-content/uploads/2020/09/Guidance-Part-C_Facilitating-the-common-data-environment-workflow-and-technical-solutions_Edition-1.pdf
  (a copy is also published at the `/2021/02/` path)
- **Edition / date:** Edition 1, September 2020
- **Retrieved:** 2026-10-06
- **Used for:** the CDE container states, the status codes actually in use (including S7 withdrawn and
  S6 added), the status-to-state mapping, and the worked revision/status progression.

### 2.1 Container states

The four ISO 19650-2 clause 5.6/5.7 states — Work in Progress (WIP), Shared, Published, Archive — are
the folder names the checker treats as container states (`container_states` keys in the config). Part C
describes containers moving between them and states:

> "Make it clear where in the CDE workflow the information resides. For example, information containers
> with S1 or S2 metadata are in the Shared state, whereas information containers with A4, A5 or A6
> metadata are in the Published state." — §6.2

### 2.2 Status codes in use (Tables 3 and 4)

S0 · S1 Suitable for coordination · S2 Suitable for information · S3 Suitable for review and comment ·
S4 Suitable for review and authorisation (also "S4 would eliminate the need to use the S6 status in 14";
the S4 status requests acceptance by the appointing party) · S5 · S6 Suitable for PIM authorisation ·
S7 "is no longer used and has been withdrawn" · A1, A2, … ("A1 would represent an authorized and
accepted information container generated in Stage 1") · B1, Bn Partial sign-off (with comments) ·
CR as constructed record document.

This is why the status pattern accepts `S0`–`S6`, the `A`/`B` series and `CR`, and **not** `S7`.

### 2.3 Worked progression (Stage 3 illustration, Figure 9 / Table 4)

| Step | Status | Revision | Source text |
|---|---|---|---|
| Production in WIP | S0 | P01.01, then P02.01, P03.01 | "The drawing is assigned a metadata status S0 and saved to a local CDE solution with a metadata revision P01.01" |
| Issued for comment | S3 | P01 | "The drawing is assigned status S3, suitable for review and comment" |
| Issued for coordination | S1 | P01 | "The model … is assigned an S1 status, suitable for coordination only" |
| For authorisation | S6 | P02 | "assigned an S6 status, suitable for Information model authorization (PIM…)" |
| Requesting acceptance | S4 | P03.01 | "The drawing is re-issued with status S4, noting the drawing meets the stage requirements and the task team requests that it be accepted by the appointing party" |
| Accepted / published | A3 | C01 | "The drawing is then approved and the revision updated to reflect a contractual revision. The drawing is assigned status A3… and published onto the CDE" |

### 2.4 The status-to-state map is an *example instantiation*

Part C gives the states and the statuses, but the guidance is explicit that the mapping belongs in the
project's own information standard:

> "Make it clear how metadata assignments defined in the information standard shall be assigned to the
> information containers." — Part C checklist

The config therefore encodes an example map derived from the table above, and labels it as such in the
YAML comment directly above `container_states`:

```yaml
WIP:       ["S0"]
Shared:    ["S1", "S2", "S3", "S4", "S5", "S6"]
Published: ["A*", "B*"]
Archive:   ["CR"]
```

Globs are supported because the `A`/`B` series is open-ended. A real project would replace this block.

---

## 3. Values that are **not** from the sources (local policy, configurable)

| Config key | Value | Why it is here |
|---|---|---|
| `extension_allowlist` | 13 formats | Not in either source. A local file-type policy; the Annex does not restrict container formats. |
| `illegal_characters` | space, `_`, `!`, `@`, `#`, `%`, `&`, `(`, `)`, `+`, `=` | Not in either source. Windows-portability and shell hygiene. |
| `path_max_length` | 240 | Not in either source. Common Windows path limit. |
| `max_stem_length` | 96 | Not in either source. |
| `case: upper` | upper case | Not in either source; taken from the published examples (`123456-ORG-A1-ZZ-MO-A-0001`). |
| `metadata.required_title_fields` | `[originator, number]` | Not in either source. A project decision about what a document title must agree with. |

## 4. Second shipped convention

`conventions/estates_cde_variant.yml` is **not** an official standard and says so in its header. It is an
organisation-specific instantiation that uses the freedoms the Annex grants ("The number of fields can
be shortened or expanded as required"; schedules "should be/could be expanded with project-specific
codes") to prove the engine takes its behaviour from config.

## 5. Open questions / not verified

- **Later edition of the UK National Annex.** Secondary sources (for example
  https://www.symetri.us/insights/blog/iso-19650-file-naming-update, retrieved 2026-10-06) describe a
  2021 update to the UK National Annex that renames the fields to *Project – Originator – Functional
  Breakdown – Spatial Breakdown – Form – Discipline – Number* and revises the discipline code list to
  describe technical activities rather than job titles. **The 2021 edition itself was not obtained**, so
  it is not encoded here. The configured convention is the edition that was read (§1 above) and its
  header says so. If the 2021 text is obtained, add it as a third shipped convention and re-verify
  Tables 1.3–1.5.
- **Uniclass codes** (referenced in the Annex §2.1.2 as a classification option) are deliberately *not*
  encoded: the Annex does not specify a code list, and inventing one would break rule 4. See P13, which
  handles Uniclass mapping separately and labels its placeholder code list.
- **IFC project-name field** used by the metadata check is the `IfcProject` name in the IFC header; the
  ISO 10303-46 property is not cited here because the checker reads it through IfcOpenShell rather than
  validating against the schema.
