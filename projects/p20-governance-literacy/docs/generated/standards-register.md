<!-- GENERATED FILE. Do not edit by hand: run `make p20-build` (src/generate.py). CI fails if this page is stale. -->

# Standards register (generated)

What each standard is, where it bites, and how far we have actually got.

10 standards. Status is honest: `implemented` means a rule or code list from the official source is encoded and tested here; `mock` means a development placeholder; `awareness-only` means nothing is stored or applied; `not-obtained` means we wanted it and could not get it.

| Standard | Status | Where it touches the data | Owner | Project | Source |
|---|---|---|---|---|---|
| COBie | implemented | P12 validates COBie workbooks against the standard's sheet and key structure.; P12 produces a handover diff that the operations team reviews.; The AIR (handover guide) names COBie sheets as required deliverables. | estates-bim | P12 | https://www.buildingsmart.org/standards/cobie/ |
| DESNZ/DEFRA GHG conversion factors | implemented | P04 seeds dim_emission_factor from the flat-format workbook, fetched by script.; P08 multiplies kWh by the factor to get kgCO2e. | estates-energy | P04 | https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025 |
| GHG Protocol | awareness-only | P08 methodology defines Scope 1 (gas) and Scope 2 (purchased electricity, location-based).; The carbon mart labels each fuel row with its scope from dim_emission_factor. | estates-energy | P08 | https://ghgprotocol.org/corporate-standard |
| HESA Estates Management Record (EMR) | mock | P10 produces a mock return pack to rehearse the shape of a submission. | estates-finance | P10 | https://www.hesa.ac.uk/data-and-analysis/estates-management-record |
| ISO 19650 (and the UK National Annex) | implemented | P14 checks information container states (WIP, Shared, Published, Archive) and status codes.; P14 checks information naming: field widths, delimiter, level, type, discipline, status, revision.; P12 uses the National Annex's container-to-handover logic to decide what must be delivered. | estates-bim | P14 | https://www.iso.org/standard/68078.html |
| RICS/IPWS/BCS Standard for the specialist in public sector data estates | awareness-only | Informs the role definitions and data literacy training (E7 in the criteria) in this pack. | estates-analytics | P20 | https://www.gov.uk/government/publications/standard-for-the-specialist-in-public-sector-data-estates |
| SFG20 | not-obtained | Would inform plant efficiency benchmarks in P16 anomaly detection.; Not used by any current table or dashboard. | estates-energy | - | https://www.sfg20.org/ |
| TRAC sustainability guidance | awareness-only | Would define the categories in an institutional sustainability return. | estates-energy | - | https://www.ukri.org/what-we-offer/collaborate-internationally/environment-and-sustainability/ |
| UK BIM Framework (CDE workflow) | implemented | P14 encodes container states and status-to-state statements for the checks. | estates-bim | P14 | https://ukbimframework.org/ |
| Uniclass 2015 | mock | P13 maps free-text asset and space descriptions to Uniclass-like codes.; P11 flags IFC elements with no classification.; P12 would use it to validate COBie component classifications. | estates-bim | P13 | https://www.nbs.org.uk/products/uniclass/ |

## COBie

- **Status**: `implemented`
- **What it is**: A standard set of spreadsheets for handing over building information, one table per topic such as components, spaces, systems and operations.
- **Owner**: `estates-bim`
- **Source**: https://www.buildingsmart.org/standards/cobie/
- **Access**: Publicly described structure. No COBie data files committed.
- **Where it touches the data**:
    - P12 validates COBie workbooks against the standard's sheet and key structure.
    - P12 produces a handover diff that the operations team reviews.
    - The AIR (handover guide) names COBie sheets as required deliverables.
- **Limitations**: Implemented for structure, keys and required fields only. Semantic content (for example whether an asset type is sensible) is not machine-checked.
- **Provenance**: `projects/p12-cobie-validator/docs/SOURCES.md`

## DESNZ/DEFRA GHG conversion factors

- **Status**: `implemented`
- **What it is**: The annual UK government workbook of emission factors per unit of fuel and activity.
- **Owner**: `estates-energy`
- **Source**: https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025
- **Access**: Open Government Licence v3.0
- **Where it touches the data**:
    - P04 seeds dim_emission_factor from the flat-format workbook, fetched by script.
    - P08 multiplies kWh by the factor to get kgCO2e.
- **Limitations**: Factors are refetched each year and change, so published carbon numbers are restated when a new vintage lands. The pipeline records the factor year and source URL in every row.

## GHG Protocol

- **Status**: `awareness-only`
- **What it is**: The international standard that classifies emissions into scopes and describes location-based and market-based accounting.
- **Owner**: `estates-energy`
- **Source**: https://ghgprotocol.org/corporate-standard
- **Access**: Publicly available guidance; referenced, not reproduced.
- **Where it touches the data**:
    - P08 methodology defines Scope 1 (gas) and Scope 2 (purchased electricity, location-based).
    - The carbon mart labels each fuel row with its scope from dim_emission_factor.
- **Limitations**: Scope definitions are used; the standard's calculation guidance is not implemented, and no market-based accounting is attempted.

## HESA Estates Management Record (EMR)

- **Status**: `mock`
- **What it is**: The UK sector data return institutions submit about their estate and sustainability.
- **Owner**: `estates-finance`
- **Source**: https://www.hesa.ac.uk/data-and-analysis/estates-management-record
- **Access**: Public guidance and return templates; not fetched in detail.
- **Where it touches the data**:
    - P10 produces a mock return pack to rehearse the shape of a submission.
- **Limitations**: P10 is illustrative. The field mapping in P10 was written from general knowledge of a return pack, not from the official specification, so it must not be presented as an official HESA mapping.

## ISO 19650 (and the UK National Annex)

- **Status**: `implemented`
- **What it is**: International standard for managing information over a built asset's life: information containers, naming and numbering, statuses, and who may authorise what.
- **Owner**: `estates-bim`
- **Source**: https://www.iso.org/standard/68078.html
- **Access**: Summary only. The standard text is not reproduced; the UK National Annex guidance is public (see DATA.md).
- **Where it touches the data**:
    - P14 checks information container states (WIP, Shared, Published, Archive) and status codes.
    - P14 checks information naming: field widths, delimiter, level, type, discipline, status, revision.
    - P12 uses the National Annex's container-to-handover logic to decide what must be delivered.
- **Limitations**: Structure, code lists and revision formats are encoded from the public UK sources recorded in DATA.md. The full ISO text was not obtained, so nothing here claims full conformance; P14 checks the subset that can be verified.
- **Provenance**: `projects/p14-iso19650-checker/docs/SOURCES.md`

## RICS/IPWS/BCS Standard for the specialist in public sector data estates

- **Status**: `awareness-only`
- **What it is**: A UK competency framework for public sector data specialists.
- **Owner**: `estates-analytics`
- **Source**: https://www.gov.uk/government/publications/standard-for-the-specialist-in-public-sector-data-estates
- **Access**: Publicly available standard document.
- **Where it touches the data**:
    - Informs the role definitions and data literacy training (E7 in the criteria) in this pack.
- **Limitations**: Referenced for competency framing only; no assessment evidence is claimed here.

## SFG20

- **Status**: `not-obtained`
- **What it is**: UK benchmarking scheme setting standard energy and carbon values for building services.
- **Owner**: `estates-energy`
- **Source**: https://www.sfg20.org/
- **Access**: Published reports; no values stored here.
- **Where it touches the data**:
    - Would inform plant efficiency benchmarks in P16 anomaly detection.
    - Not used by any current table or dashboard.
- **Limitations**: Nothing from SFG20 is encoded. Any future use needs the source recorded in DATA.md first, with the vintage of each benchmark value.

## TRAC sustainability guidance

- **Status**: `awareness-only`
- **What it is**: UKRI guidance on sustainability reporting for funded research organisations.
- **Owner**: `estates-energy`
- **Source**: https://www.ukri.org/what-we-offer/collaborate-internationally/environment-and-sustainability/
- **Access**: Public guidance; categories not encoded.
- **Where it touches the data**:
    - Would define the categories in an institutional sustainability return.
- **Limitations**: No TRAC categories or thresholds are stored or applied anywhere in this repository.

## UK BIM Framework (CDE workflow)

- **Status**: `implemented`
- **What it is**: UK guidance for the common data environment: container states, statuses and approvals.
- **Owner**: `estates-bim`
- **Source**: https://ukbimframework.org/
- **Access**: Publicly available guidance; structure encoded, text not reproduced.
- **Where it touches the data**:
    - P14 encodes container states and status-to-state statements for the checks.
- **Limitations**: Encoded as state and status rules. The full guidance text is not copied into this repository; see DATA.md for the source and licence position.

## Uniclass 2015

- **Status**: `mock`
- **What it is**: A classification of construction products, spaces and components that lets systems group like with like across projects.
- **Owner**: `estates-bim`
- **Source**: https://www.nbs.org.uk/products/uniclass/
- **Access**: Licensed tables. Not fetched for this repository.
- **Where it touches the data**:
    - P13 maps free-text asset and space descriptions to Uniclass-like codes.
    - P11 flags IFC elements with no classification.
    - P12 would use it to validate COBie component classifications.
- **Limitations**: P13 ships a clearly named development placeholder code list. No code from the official tables is stored, and no output should be presented as a real Uniclass mapping until the licensed tables are obtained.
- **Provenance**: `projects/p13-uniclass-mapper/README.md`

All data in this pack is synthetic. Numbers come from the portfolio's generator, not from any real university, building or estate, and nothing here is a compliance statement.
