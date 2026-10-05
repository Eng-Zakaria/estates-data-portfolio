"""P03 recall: planted-defect detection measured against ground_truth.yaml.

Granularity depends on what the defect log identifies (read
``packages/campus_synth/.../defects.py`` and ``exports.py`` — the rules below
are grounded in that code, not guessed):
- exact unique keys (WO/EV/room/IN ids): entry detected iff its key is in
  quarantine (ANY reason — overlap-safe, since the pipeline quarantines a
  multi-hit row once under the earliest rule) or in the mapped silver-leak
  check failures.
- masked keys (``xx``): count rule over silver xx rows + quarantine xx rows
  (wide supplier-B counts divide by 48 — one wide row melts to 48 long rows).
- space nulls: null-reason rows + the blank-row rule (the all-null row never
  reaches raw, so absence from bronze counts as handled, documented).
- space misspelt: keys absent from bronze (per-campus sheet filter drops
  misspelt-building rows before ingest).
- meters (repeated keys): signature rules (reason counts, grain-excess for
  duplicates, gaps-report max, /48 for wide) + Tier-2 bronze cross-match for
  shorts (matches bronze signature rows to quarantine on natural keys).
- sensors (repeated keys): key presence in quarantine + leak volumes.
- aggregates (bms N/A, gaps): artifact rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import duckdb

from .spec import CheckSpec

# (table, defect_type) -> (quarantine view, key column, bronze key column).
KEYED = {
    "space_register": ("quarantine_spaces", "Room", "Room"),
    "cafm_workorders": ("quarantine_work_orders", "WO_Number", "WO_Number"),
    "timetable": ("quarantine_timetable", "event_id", "event_id"),
    "statutory_inspections": ("quarantine_inspections", "inspection_id", "inspection_id"),
}

# (table, defect_type) -> silver leak check whose failed keys count as detected.
LEAK_MAP = {
    ("space_register", "out_of_range"): "spaces_capacity_non_negative",
    ("cafm_workorders", "out_of_range"): "wo_labour_non_negative",
    ("cafm_workorders", "misspelt_category"): "wo_id_pattern",
    ("timetable", "misspelt_category"): "tt_event_id_pattern",
    ("timetable", "future_dates"): "tt_no_future_date",
    ("meter_hh_supplierA", "misspelt_category"): "ma_id_known",
    ("meter_hh_supplierB", "misspelt_category"): "mb_id_known",
    ("meter_hh_supplierB", "future_dates"): "mb_no_future_ts",
    ("sensors", "misspelt_category"): "sensors_id_known",
}

# (table, defect_type) -> quarantine reason prefix for count rules.
REASON_MAP = {
    ("meter_hh_supplierA", "nulls_in_mandatory"): "nulls_in_mandatory",
    ("meter_hh_supplierA", "out_of_range"): "negative_or_spiked_meter",
    ("meter_hh_supplierB", "out_of_range"): "negative_or_spiked_meter",
    ("space_register", "nulls_in_mandatory"): "nulls_in_mandatory",
}


@dataclass
class RecallResult:
    check_id: str
    planted: int
    detected: int
    evidence: str
    samples: list[dict] = field(default_factory=list)

    @property
    def recall(self) -> float:
        return 1.0 if self.planted == 0 else min(1.0, self.detected / self.planted)

    @property
    def rows_failed(self) -> int:
        return max(0, self.planted - self.detected)


def _planted(con: duckdb.DuckDBPyConnection, table: str, dtype: str) -> list[str]:
    rows = con.execute('SELECT row_key FROM defects WHERE "table" = ? AND type = ?', [table, dtype]).fetchall()
    return [str(r[0]) for r in rows]


def _qkeys(con: duckdb.DuckDBPyConnection, qview: str, keycol: str) -> set[str]:
    rows = con.execute(f"SELECT DISTINCT {keycol} FROM {qview} WHERE {keycol} IS NOT NULL").fetchall()
    return {str(r[0]) for r in rows}


def _reason_count(con: duckdb.DuckDBPyConnection, qview: str, prefix: str) -> int:
    return int(con.execute(f"SELECT COUNT(*) FROM {qview} WHERE _reject_reason LIKE '{prefix}%%'").fetchone()[0])


def _like_count(con: duckdb.DuckDBPyConnection, view: str, col: str, pattern: str) -> int:
    return int(con.execute(f"SELECT COUNT(*) FROM {view} WHERE {col} LIKE '{pattern}'").fetchone()[0])


def _bronze_match(
    con: duckdb.DuckDBPyConnection,
    bronze_glob: str,
    signature_sql: str,
    natural_keys: list[str],
    qview: str,
    qkey_map: dict[str, str],
) -> tuple[int, int, str]:
    """Tier-2: match bronze signature rows to quarantine rows on natural keys.

    Returns (bronze_signature_rows, matched_in_quarantine, note). Matches on
    any quarantine reason — this attributes overlap rows to prove containment.
    """
    sig_rows = con.execute(f"SELECT * FROM ({signature_sql})").fetchall()
    cols = [d[0] for d in con.execute(f"SELECT * FROM ({signature_sql}) LIMIT 0").description]
    matched = 0
    reasons: dict[str, int] = {}
    for row in sig_rows:
        rec = dict(zip(cols, row, strict=True))
        conds = []
        for nk in natural_keys:
            qcol = qkey_map.get(nk, nk)
            val = rec[nk]
            conds.append(f"{qcol} IS NULL" if val is None else f"CAST({qcol} AS VARCHAR) = '{val}'")
        hit = con.execute(f"SELECT _reject_reason FROM {qview} WHERE {' AND '.join(conds)} LIMIT 1").fetchall()
        if hit:
            matched += 1
            reasons[str(hit[0][0])] = reasons.get(str(hit[0][0]), 0) + 1
    note = f"bronze signature rows={len(sig_rows)} matched={matched} reasons={reasons}"
    return len(sig_rows), matched, note


def evaluate(
    con: duckdb.DuckDBPyConnection,
    spec: CheckSpec,
    all_specs: dict[str, CheckSpec],
    gx_samples: dict[str, list[dict]],
    lake: str,
) -> RecallResult:
    """Evaluate one recall check; raises on SQL errors (loud, never silent)."""
    assert spec.engine == "recall", spec.id
    table = str(spec.kwargs.get("table"))
    dtype = str(spec.kwargs.get("defect_type"))
    keys = _planted(con, table, dtype)
    planted = len(keys)
    if planted == 0:
        return RecallResult(spec.id, 0, 0, "no planted defects of this type")

    leak_check = LEAK_MAP.get((table, dtype))

    def leak_keys() -> set[str]:
        if leak_check is None:
            return set()
        mapped = all_specs[leak_check]
        key_col = mapped.key_col or (mapped.kwargs or {}).get("column")
        if mapped.engine == "gx":
            rows = gx_samples.get(leak_check, [])
            return {str(r.get(key_col, "")) for r in rows if r.get(key_col) not in (None, "")}
        # sql: re-run the failed query fully (no sample cap) for exact keys
        cols = [d[0] for d in con.execute(f"SELECT * FROM ({mapped.sql_failed}) LIMIT 0").description]
        col = mapped.key_col or cols[0]
        idx = cols.index(col)
        return {str(r[idx]) for r in con.execute(mapped.sql_failed).fetchall() if r[idx] is not None}

    # --- exact unique keys (overlap-safe: any quarantine reason counts) ---
    if (table, dtype) in {
        ("space_register", "duplicate_rows"),
        ("cafm_workorders", "nulls_in_mandatory"),
        ("cafm_workorders", "duplicate_rows"),
        ("cafm_workorders", "future_dates"),
        ("cafm_workorders", "orphan_fk"),
        ("cafm_workorders", "completed_before_raised"),
        ("cafm_workorders", "out_of_range"),
        ("timetable", "nulls_in_mandatory"),
        ("timetable", "duplicate_rows"),
        ("timetable", "out_of_range"),
        ("timetable", "orphan_fk"),
        ("timetable", "future_dates"),
        ("statutory_inspections", "duplicate_rows"),
        ("space_register", "out_of_range"),
    }:
        qview, keycol, _ = KEYED[table]
        qkeys = _qkeys(con, qview, keycol)
        lk = leak_keys()
        exact = [k for k in keys if k != "None" and "xx" not in k]
        detected_keys = [k for k in exact if k in qkeys or k in lk]
        masked = [k for k in keys if "xx" in k]
        samples = [{"row_key": k} for k in keys if k not in detected_keys][:100]
        return RecallResult(
            spec.id,
            planted,
            len(detected_keys),
            f"exact keys: {len(detected_keys)}/{len(exact)} in quarantine-or-leak; "
            f"masked keys in log: {len(masked)} (none expected here)",
            samples,
        )

    # --- masked keys: count rule over xx patterns ---
    if dtype == "misspelt_category":
        divisor = 1
        if table == "meter_hh_supplierB":
            divisor = 48
        if table == "space_register":
            # never exported (per-campus sheet filter); absence from bronze counts
            _, _, bronzecol = KEYED[table]
            sub = "space_register" if table == "space_register" else table
            missing = con.execute(
                f"SELECT COUNT(*) FROM (SELECT DISTINCT row_key FROM defects WHERE table = '{table}' "
                f"AND type = 'misspelt_category') AS d ANTI JOIN "
                f"(SELECT DISTINCT Room FROM read_parquet('{lake}/bronze/{sub}/*/*.parquet')) AS b "
                f"ON d.row_key = b.Room"
            ).fetchone()[0]
            detected = int(missing)
            return RecallResult(spec.id, planted, detected, f"keys absent from bronze: {missing}/{planted}")
        if table == "sensors":
            qn = _like_count(con, "quarantine_sensors", "sensor_id", "%xx%")
            sn = len(leak_keys())
            detected = min(planted, qn + sn)
            return RecallResult(spec.id, planted, detected, f"quarantine xx rows={qn} silver xx ids={sn}")
        # cafm / timetable / meters_a: silver xx rows + quarantine xx rows
        qview, keycol, _ = {
            "cafm_workorders": ("quarantine_work_orders", "WO_Number", ""),
            "timetable": ("quarantine_timetable", "event_id", ""),
            "meter_hh_supplierA": ("quarantine_meters_a", "meter_id", ""),
            "meter_hh_supplierB": ("quarantine_meters_b", "meter_id", ""),
        }[table]
        qn = _like_count(con, qview, keycol, "%xx%")
        sn = len(leak_keys())
        detected = min(planted, (qn + sn) // divisor if divisor > 1 else qn + sn)
        return RecallResult(
            spec.id,
            planted,
            detected,
            f"quarantine xx rows={qn} silver xx keys={sn} divisor={divisor}",
        )

    # --- space nulls: reason count + blank-row rule ---
    if (table, dtype) == ("space_register", "nulls_in_mandatory"):
        n_reason = _reason_count(con, "quarantine_spaces", "nulls_in_mandatory")
        n_blank_logged = sum(1 for k in keys if k == "blank")
        n_blank_absent = con.execute(
            "SELECT COUNT(*) FROM (SELECT 1 WHERE NOT EXISTS "
            f"(SELECT 1 FROM read_parquet('{lake}/bronze/space_register/*/*.parquet') AS b "
            "WHERE b.Room IS NULL AND b.building_name IS NULL)) "
        ).fetchone()[0]
        blank_ok = n_blank_logged if n_blank_absent else 0
        detected = min(planted, n_reason + blank_ok)
        return RecallResult(
            spec.id,
            planted,
            detected,
            f"null-reason rows={n_reason} blank entries={n_blank_logged} blank-absent={bool(n_blank_absent)}",
        )

    # --- meters_a count rules + Tier-2 bronze match ---
    if table == "meter_hh_supplierA" and dtype in ("nulls_in_mandatory", "out_of_range"):
        prefix = REASON_MAP[(table, dtype)]
        n_reason = _reason_count(con, "quarantine_meters_a", prefix)
        if dtype == "nulls_in_mandatory":
            sig = (
                "SELECT meter_id, local_time FROM "
                f"read_parquet('{lake}/bronze/meter_hh_supplierA/*/*.parquet') "
                "WHERE meter_id IS NULL OR local_time IS NULL"
            )
            _, matched, note = _bronze_match(con, "", sig, ["meter_id", "local_time"], "quarantine_meters_a", {})
            detected = min(planted, n_reason + matched)
            return RecallResult(spec.id, planted, detected, f"reason rows={n_reason} tier2: {note}")
        sig = (
            "SELECT meter_id, local_time FROM "
            f"read_parquet('{lake}/bronze/meter_hh_supplierA/*/*.parquet') "
            "WHERE TRY_CAST(kwh AS DOUBLE) < 0"
        )
        _, matched, note = _bronze_match(con, "", sig, ["meter_id", "local_time"], "quarantine_meters_a", {})
        detected = min(planted, matched)
        return RecallResult(spec.id, planted, detected, f"tier2 bronze-match: {note}")

    # --- meters_a duplicates: grain-excess rule ---
    if (table, dtype) == ("meter_hh_supplierA", "duplicate_rows"):
        excess = con.execute(
            "SELECT COALESCE(SUM(cnt - 1), 0) FROM (SELECT COUNT(*) AS cnt FROM silver_meters_a "
            "GROUP BY meter_id, ts_utc HAVING COUNT(*) > 1)"
        ).fetchone()[0]
        n_reason = _reason_count(con, "quarantine_meters_a", "duplicate")
        detected = max(0, planted - int(excess))
        return RecallResult(
            spec.id,
            planted,
            detected,
            f"silver excess copies={excess} quarantine dup rows={n_reason}",
        )

    # --- meters_a gaps: report max rule ---
    if (table, dtype) == ("meter_hh_supplierA", "gaps"):
        top = con.execute(
            "SELECT meter_id, local_date, missing FROM "
            f"read_parquet('{lake}/quarantine/meter_hh_supplierA/report.parquet') "
            "ORDER BY missing DESC LIMIT 5"
        ).fetchall()
        big = con.execute(
            "SELECT COUNT(*) FROM "
            f"read_parquet('{lake}/quarantine/meter_hh_supplierA/report.parquet') "
            "WHERE missing >= 40 AND local_date NOT IN ('2026-03-29', '2026-04-01')"
        ).fetchone()[0]
        detected = 1 if int(big) > 0 else 0
        samples = [{"meter_id": str(r[0]), "local_date": str(r[1]), "missing": str(r[2])} for r in top]
        return RecallResult(spec.id, planted, detected, f"report days missing>=40 (excl DST/spill): {big}", samples)

    # --- meters_b wide rules (/48 structural divisor) ---
    if table == "meter_hh_supplierB" and dtype in (
        "nulls_in_mandatory",
        "duplicate_rows",
        "future_dates",
        "out_of_range",
    ):
        if dtype == "nulls_in_mandatory":
            n = con.execute(
                "SELECT COUNT(*) FROM quarantine_meters_b "
                "WHERE _reject_reason LIKE 'dst%' AND CAST(local_date AS VARCHAR) = 'None'"
            ).fetchone()[0]
            detected = min(planted, int(n) // 48)
            return RecallResult(spec.id, planted, detected, f"null-date rows/48: {n}/48")
        if dtype == "duplicate_rows":
            excess = con.execute(
                "SELECT COALESCE(SUM(cnt - 1), 0) FROM (SELECT COUNT(*) AS cnt FROM silver_meters_b "
                "GROUP BY meter_id, ts_utc HAVING COUNT(*) > 1)"
            ).fetchone()[0]
            detected = max(0, planted - int(excess))
            return RecallResult(spec.id, planted, detected, f"silver excess copies={excess}")
        if dtype == "future_dates":
            n = len(leak_keys())
            detected = min(planted, n // 48)
            return RecallResult(spec.id, planted, detected, f"silver future rows/48: {n}/48")
        n_reason = _reason_count(con, "quarantine_meters_b", "negative_or_spiked_meter")
        detected = min(planted, n_reason)
        return RecallResult(spec.id, planted, detected, f"negative-reason rows={n_reason}")

    # --- sensors: key presence (log keys are repeated sensor ids) ---
    if table == "sensors" and dtype in (
        "nulls_in_mandatory",
        "duplicate_rows",
        "out_of_range",
        "future_dates",
    ):
        qkeys = _qkeys(con, "quarantine_sensors", "sensor_id")
        exact = [k for k in keys if "xx" not in k]
        detected = sum(1 for k in exact if k in qkeys)
        samples = [{"row_key": k} for k in exact if k not in qkeys][:100]
        return RecallResult(
            spec.id, planted, detected, f"sensor ids present in quarantine: {detected}/{len(exact)}", samples
        )

    # --- bms N/A: artifact rule ---
    if (table, dtype) == ("bms_trends", "nulls_in_mandatory"):
        n = con.execute(
            "SELECT COUNT(*) FROM quarantine_bms WHERE _reject_reason LIKE 'nulls_in_mandatory%'"
        ).fetchone()[0]
        detected = 1 if int(n) > 0 else 0
        return RecallResult(spec.id, planted, detected, f"N/A quarantine cells={n}")

    raise ValueError(f"no recall rule for ({table}, {dtype}) — add one, never silently pass")
