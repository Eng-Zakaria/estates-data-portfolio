# P12 seeded errors — recall evidence (2026-10-06, synthetic workbooks)

Corrupted workbook: `data/cobie/corrupted.xlsx` with `seeded_errors.json` (42 seeded
events). Validator output: `data/cobie/report_corrupted/issues.csv` —
**34 blocking + 20 warning = 54 issues, score 39.0**. One seeded event routinely
produces several issues (e.g. a duplicated key flags every duplicated row; a
blanked `Type.Name` cascades into `Job → Type` FK failures). Recall is therefore
reported per seeded *category*: every category is detected with the correct rule
family (100% category recall).

| Seeded category | Events | Detecting rule id(s) | Issues found | Recall |
|---|---|---|---|---|
| missing_sheet (Zone, Document dropped) | 2 | `sheet_zone_present`, `sheet_document_present` | 2 | 2/2 |
| missing_column (Contact.Phone, Type.ModelNumber) | 2 | `col_contact_phone`, `col_type_model` | 2 | 2/2 |
| column_order (Component Name/TypeName swapped) | 1 | `order_component_cols` | 1 | 1/1 |
| empty_mandatory (Facility.CreatedOn, Space.FloorName x2, Component.TypeName, Floor.Name, Type.Name) | 6 | `mandatory_*` | 7 | 6/6 events |
| duplicate_key (Component.Name, Type.Name, Space.Name) | 3 | `unique_component_name`, `unique_type_name`, `unique_space_name` | 6 | 3/3 |
| broken_fk single-value (Component→Type x2, Component→Space, Space→Floor, Job→Type) | 5 | `fk_component_type`, `fk_component_space`, `fk_space_floor`, `fk_job_type` (+1 cascade: blanked AHUType1 breaks Job-AHU) | 7 | 5/5 |
| broken_fk multi-value (Component.Space `;`, System.ComponentNames `,`) | 2 | `fk_component_space`, `fk_system_component` | 3 | 2/2 |
| broken_fk_createdby (ghost address x2) | 2 | `createdby_in_contact` | 2 | 2/2 |
| bad_format_email | 1 | `format_contact_email` | 1 | 1/1 |
| bad_format_date (Component.InstallationDate x2, Type.CreatedOn) | 3 | `format_component_installdate`, `format_createdon_iso` | 3 | 3/3 |
| numeric_range (GrossArea −5, Height 99, ExpectedLife 999, Warranty −3) | 4 | `range_*` | 4 | 4/4 |
| invalid_category (`???`/`!!!` x3) | 3 | `category_type`, `category_component` | 3 | 3/3 |
| missing_air (Manufacturer x2, ExpectedLife, Warranty x2, Serial, InstallDate) | 7 | `air_*` | 9 (incl. blanked Type.Name cascading to `air_typename_required` x2) | 7/7 |
| duplicate_serial (SN-DUP x3 rows) | 1 | `unique_component_serial` (+air/mandatory knock-ons) | 5 | 1/1 |

Valid workbook: `data/cobie/valid.xlsx` → **score 100.0, 0 blocking, 0 warning**.

Loader evidence:
- `load data/cobie/valid.xlsx --out data/cobie/handover` → `inserted=8 rejected=0`;
  immediate re-run → `unchanged=8 inserted=0` (idempotent via `state.json` row hashes).
- `load data/cobie/corrupted.xlsx --out data/cobie/handover_bad` →
  `inserted=3 rejected=6`, every rejected row carries a reason in `quarantine.csv`
  (unknown TypeName/Space, missing SerialNumber, duplicate serial).
- `--dry-run` prints the same diff and writes nothing.
