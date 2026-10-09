# P10 OPEN_QUESTIONS.md

## Gaps from public spec access (human action required)

1. **HESA EMR exact code lists**: The public EMR spec lists return categories but the full coding manual (with exact codes like "1.1.1 Teaching", "1.1.2 Research", etc.) may be behind login. Current mapping uses generic names. **Action**: If official codes needed, obtain HESA login or request from estates office.

2. **TRAC cost driver formulas**: TRAC guidance describes driver logic (space + staff FTE + research income) but exact weighting formulas are in the detailed TRAC model (Excel). Current implementation uses simplified NIA × category weight × dept activity split. **Action**: Obtain TRAC model Excel from finance office for exact formulas.

3. **HESA EMR water/energy sections**: The return requires water consumption (m³) and energy by fuel type. Water not in HH feeds (NA in this mock). **Action**: Verify if water meter data available in real estate; add if so.

4. **Year-on-year comparison**: EMR requires prior year comparison. Synthetic data only has one year. **Action**: When multi-year data available, implement YoY change flags with explanation fields per validation rule V004.

5. **Cost pool definitions**: TRAC defines specific cost pools (rates, utilities, maintenance, cleaning, security, insurance, etc.). Current pools are illustrative. **Action**: Align with finance office's actual chart of accounts.

5. **Building register (UPRN)**: HESA requires UPRN. Synthetic buildings lack UPRN. **Action**: Add UPRN column when real building register available.

## P10-specific follow-ups

- Add multi-year snapshot support for YoY validation (rule V004).
- Expand validation rules to cover all HESA EMR mandatory fields.
- Implement explanation field capture for YoY >15% changes.
- Generate return for multiple years from snapshots.
- Add UPRN lookup and validation.

## Audit trail enhancements

- GPG-sign snapshots for non-repudiation.
- Add CI gate that fails if deterministic re-run check fails.
- Publish run_log + sign_off to a shared audit store.