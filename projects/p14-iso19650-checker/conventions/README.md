# Conventions

A convention file is the **whole** rulebook. The engine contains no code list, field width or folder
name of its own: change the YAML and the checker's behaviour changes with no code edit
(`tests/test_conventions.py` proves it).

| File | What it is |
|---|---|
| `uk_national_annex.yml` | The information container identification convention published in the CDBB *BIM Toolkit / National Annex Guidance*, with statuses in use from UK BIM Framework *Guidance Part C, Edition 1*. Read 2026-10-06 — see [`../docs/SOURCES.md`](../docs/SOURCES.md) for the quotes behind every value. |
| `estates_cde_variant.yml` | An **organisation-specific** instantiation (underscore separator, fixed-width fields, an extra `asset_class` facet, word-form statuses). Not a standard; it exists to prove the engine is convention-agnostic and to give the sample generator a second shape to work with. |

## Writing your own

```yaml
name: my_convention                 # required
description: ...                    # shown in reports
source:                             # required by AGENTS.md rule 4: provenance for any code list
  name: Estates information standard v2.1
  url: https://intranet.example/estates/is-v2.1
  edition: v2.1
  retrieved: 2026-10-07

separator: "-"                      # single character
case: upper                         # upper | lower | any
id_fields: [project, originator, number]     # facets that make up the container identifier

container_states:                   # folder name -> statuses valid there (globs allowed)
  WIP: ["WIP"]
  Published: ["APPROVED"]

extension_allowlist: [.ifc, .pdf]  # empty = no restriction
illegal_characters: [" ", "_"]      # characters not allowed in a name
path_max_length: 240                # measured relative to the checked folder
max_stem_length: 96

fields:                             # listed in position order; positions must be unique
  - name: project
    position: 0
    length: 6                       # exact ... or min_length / max_length
    charset: "A-Z0-9"               # regex character-class body, ranges allowed
    description: Project code
    source: Information standard v2.1, table 2   # per-field provenance
  - name: number
    position: 1
    min_length: 4
    max_length: 6
    charset: "0-9"
  - name: kind
    position: 2
    allowed_values: ["DR", "RP"]    # closed code list
  - name: status
    position: 3
    pattern: "WIP|APPROVED"         # regex for open-ended code families (A1, A2, ...)

sequence:                           # which field numbers a series of containers
  field: number
  scope: folder                     # folder | global
  warn_on_gap: true

revision:
  field: revision                   # omit the key if the convention has no revision facet
  allow_version_suffix: true        # e.g. P01.01 for work in progress
  warn_on_gap: true

metadata:
  enabled: true                     # false = no optional dependencies needed at all
  compare_ifc_project_name: true    # needs ifcopenshell
  compare_doc_title: true           # needs python-docx / pypdf / openpyxl
  ignore_case: true
  required_title_fields: [originator, number]   # tokens that must appear in the title
```

Then:

```bash
python projects/p14-iso19650-checker/src/cli.py check <folder> --config conventions/my_convention.yml
```

## Validation and gotchas

The file is validated when it is loaded — duplicate field positions, fields out of position order,
`id_fields`/`sequence.field`/`revision.field` naming a field that does not exist, a separator longer than
one character, `length` together with `min_length`/`max_length`, `min_length > max_length` and an unknown
`case` policy all raise a validation error naming the problem.

- **Quote code values that YAML would reinterpret.** `01` and `02` are read as octal integers, so write
  `"01"`, `"02"`. `00`, `ZZ`, `DR` are fine unquoted. This is why `uk_national_annex.yml` quotes its
  level codes.
- **Quote regex patterns** (`pattern: "[PC][0-9]{2}(\\.[0-9]{2})?"`) so YAML does not eat the backslashes.
- **`charset` is a character-class body**, not a pattern: write `A-Z0-9`, and escape nothing else.
- **A convention with no `id_fields`** falls back to every field except `status` and `revision`.
- **Level/type code lists are seeds, not authorities.** The National Annex says its schedules "should be /
  could be expanded with project-specific codes", so extend or replace them before using this against a
  real project.
