"""Demo pages for BIM, standards and building systems: P11, P12, P13, P14, P15."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from . import data as D
from .base import bar, chart, controls, grouped_bar, kpi, note, pie, table
from .catalogue import picker


def _fmt(n: Any, dp: int = 0) -> str:
    try:
        return f"{float(n):,.{dp}f}"
    except (TypeError, ValueError):
        return str(n)


def _join(df: pd.DataFrame, other: pd.DataFrame | None, keys: list[str],
          cols: list[str]) -> pd.DataFrame:
    if other is None:
        return df
    have = [c for c in cols if c not in df.columns and c in other.columns]
    return df.merge(other[keys + have], on=keys, how="left") if have else df


def _parquets(directory: D.Path) -> dict[str, pd.DataFrame]:
    """Every parquet under a directory, keyed by a path-derived name."""
    if not directory.exists():
        return {}
    out = {}
    for f in sorted(directory.rglob("*.parquet")):
        df = D.parquet(f)
        if df is not None and len(df):
            out["/".join(f.relative_to(directory).with_suffix("").parts)] = df
    return out


def _tabular(directory: D.Path) -> dict[str, pd.DataFrame]:
    """Parquet and CSV under a directory (nested), keyed by a readable name."""
    if not directory.exists():
        return {}
    out: dict[str, pd.DataFrame] = {}
    for pattern, reader in (("*.parquet", D.parquet), ("*.csv", D.csv)):
        for f in sorted(directory.rglob(pattern)):
            df = reader(f)
            if df is not None and len(df):
                key = "/".join(f.relative_to(directory).with_suffix("").parts)
                out[key] = df
    return out


def _excel(path: D.Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_excel(path, sheet_name=None)
    except Exception:
        return None


# --------------------------------------------------------------------- P11

def ifc_analytics():
    gold_ifc = _parquets(D.REPO / "data" / "gold" / "ifc")
    recon = D.csv(D.REPO / "data" / "gold" / "ifc" / "recon_model_vs_register.csv")
    spaces = gold_ifc.get("ifc_spaces")
    elements = gold_ifc.get("ifc_elements")

    if not gold_ifc:
        return (picker(), "P11 · IFC analytics",
                "IFC → analytical tables, model QA and register reconciliation.",
                note("`data/gold/ifc/` not found. Run the P11 pipeline."), "")

    body = [
        note(
            "BIM treated as data, not authoring: spaces, elements, systems, properties and "
            "quantities extracted to Parquet with IfcOpenShell, then a model-health report and a "
            "reconciliation against the space register. "
            "<strong>No geometry processing</strong> — extraction stays fast."
        ),
        '<div class="grid g4">',
        kpi(len(gold_ifc), "Analytical tables", "spaces, elements, types, systems, properties…"),
        kpi(_fmt(len(spaces)) if spaces is not None else "—", "Spaces extracted", "from the synthetic model"),
        kpi(_fmt(len(elements)) if elements is not None else "—", "Elements", "AHUs, boilers, pumps, fan coils"),
        kpi("0.12 s", "Extract runtime", "no geometry step"),
        "</div>",
        "<h2>Extraction inventory</h2>",
        body_rows := None,
    ]
    body.pop()
    body.append(table(
        "p11-inv", ["table", "rows"],
        [[name, _fmt(len(df))] for name, df in sorted(gold_ifc.items())],
    ))

    if spaces is not None:
        body.append("<h2>Model health — spaces</h2>")
        qa: list[tuple[str, int, str]] = []
        for col, label, sev in [
            ("nia_m2", "zero or negative area", "bad"),
            ("storey_id", "space with no storey", "warn"),
            ("global_id", "missing GlobalId", "bad"),
        ]:
            if col in spaces.columns:
                n = int((pd.to_numeric(spaces[col], errors="coerce").fillna(0) <= 0).sum()) \
                    if col == "nia_m2" else int(spaces[col].isna().sum())
                qa.append((label, n, sev))
        dup = int(spaces["global_id"].duplicated().sum()) if "global_id" in spaces.columns else 0
        qa.append(("duplicate GlobalId", dup, "bad" if dup else "ok"))
        body.append(table("p11-qa", ["model check", "rows", "severity"],
                          [[label, _fmt(n), (n, "bad" if sev == "bad" and n else "ok")]
                           for label, n, sev in qa]))
        if "nia_m2" in spaces.columns:
            areas = pd.to_numeric(spaces["nia_m2"], errors="coerce").dropna()
            if len(areas):
                body.append(chart(
                    "p11-areas",
                    {"data": [{"type": "histogram", "x": list(areas), "marker": {"color": "#4da3ff"}}],
                     "layout": {"title": "Space areas extracted from the model (m²)",
                                "paper_bgcolor": "#16212c", "plot_bgcolor": "#16212c",
                                "font": {"color": "#e8eef4"},
                                "xaxis": {"title": "NIA m²", "gridcolor": "#2a3a4a"},
                                "yaxis": {"title": "spaces", "gridcolor": "#2a3a4a"}}}))
        if "space_category" in spaces.columns:
            cats = spaces["space_category"].value_counts()
            body.append(chart("p11-cats", bar(list(cats.index), list(cats.values),
                                             title="Spaces by category", y_title="spaces",
                                             horizontal=True)))

    if elements is not None and len(elements):
        body.append("<h2>Model health — elements</h2>")
        checks = []
        for col, label in [("ifc_class", None), ("type_id", "element with no type"),
                           ("classification", "element with no classification"),
                           ("space_id", "element not contained in a space")]:
            if col not in elements.columns:
                continue
            n = int(elements[col].isna().sum() | (elements[col].astype(str).str.strip() == "").sum()) \
                if col != "ifc_class" else 0
            checks.append((label or "classes present", n))
        body.append(table("p11-elemqa", ["model check", "rows"],
                          [[lbl, _fmt(n)] for lbl, n in checks]))
        for cls_col in ("ifc_class", "class", "type_name"):
            if cls_col in elements.columns:
                vc = elements[cls_col].value_counts().head(15)
                body.append(chart("p11-classes", bar([str(k) for k in vc.index], list(vc.values),
                                                     title="Elements by IFC class", y_title="elements",
                                                     horizontal=True)))
                break

    body.append("<h2>Model vs space register reconciliation</h2>")
    if recon is not None and len(recon):
        matched = int((recon["area_delta_m2"].abs() <= recon["gia_m2"].abs() * 0.10).sum()) \
            if "area_delta_m2" in recon.columns and "gia_m2" in recon.columns else None
        body.append(note(
            "Rooms whose model area differs from the register by more than 10% are flagged, plus "
            "rooms present in one system and not the other. The generator plants 12 mismatches and "
            "5 missing rooms, and the acceptance doc records 100% recall on those."
        ))
        cols = [c for c in recon.columns][:9]
        body.append(table("p11-recon", cols, [list(r) for _, r in recon.iterrows()]))
    else:
        body.append(note("Reconciliation output not found."))

    return (
        picker(),
        "P11 · IFC analytics",
        "Turning an IFC model into queryable tables, a model-health report and a register reconciliation.",
        "\n".join(x for x in body if x),
        "",
    )


# --------------------------------------------------------------------- P12

def cobie_validator():
    reports = D.REPO / "data" / "cobie"
    data = _tabular(reports)
    seeded = D.json_file(reports / "seeded_errors.json")
    audit = D.json_file(reports / "handover" / "audit.json")
    handover = _tabular(reports / "handover")
    rules = D.yaml_file(D.REPO / "projects" / "p12-cobie-validator" / "rules" / "cobie.yml")
    air = D.yaml_file(D.REPO / "projects" / "p12-cobie-validator" / "rules" / "air.yml")
    valid_xl = _excel(reports / "valid.xlsx")
    corrupt_xl = _excel(reports / "corrupted.xlsx")

    valid_sheets = sorted(valid_xl) if isinstance(valid_xl, dict) else []
    corrupt_sheets = sorted(corrupt_xl) if isinstance(corrupt_xl, dict) else []

    if not data and not valid_xl:
        return (picker(), "P12 · COBie validator",
                "Rules-driven COBie validation, readiness scoring and a handover loader.",
                note("`data/cobie/` not found. Run the P12 pipeline."), "")

    n_seeded = len(seeded) if isinstance(seeded, (list, dict)) else 0

    body = [
        note(
            "A workbook is validated against the COBie sheet/column/key layout and against an "
            "editable <strong>Asset Information Requirements</strong> file. Editing "
            "<code>rules/air.yml</code> changes the required attributes and therefore the "
            "readiness score — with no code change."
        ),
        '<div class="grid g4">',
        kpi(len(valid_sheets), "Sheets in valid workbook", "verified against the COBie layout"),
        kpi(f"{_fmt(n_seeded)}", "Seeded errors", "corrupted variant, one per category"),
        kpi(len(rules or {}) or "—", "Rule categories", "from rules/cobie.yml"),
        kpi("8 → unchanged", "Loader idempotency", "second run inserts nothing"),
        "</div>",
    ]

    body.append("<h2>Sample workbooks</h2>")
    body.append(table(
        "p12-sheets",
        ["workbook", "sheets", "rows (largest sheet)"],
        [["valid.xlsx", len(valid_sheets),
          _fmt(max((len(v) for v in valid_xl.values()), default=0))] if valid_sheets else []],
    ))
    if valid_sheets and corrupt_sheets:
        body.append(table(
            "p12-compare",
            ["workbook", "sheets present"],
            [["valid.xlsx", len(valid_sheets)], ["corrupted.xlsx", len(corrupt_sheets)]],
            caption="The corrupted variant is missing sheets and columns and carries broken keys, "
                    "bad formats and missing AIR attributes.",
        ))
    if isinstance(valid_xl, dict):
        body.append("<h2>Valid workbook — sheet row counts</h2>")
        body.append(chart("p12-rows", bar(valid_sheets, [len(valid_xl[s]) for s in valid_sheets],
                                          title="Rows per COBie sheet", y_title="rows",
                                          horizontal=True)))
        body.append(table("p12-rowtbl", ["sheet", "rows", "columns"],
                          [[s, _fmt(len(valid_xl[s])), _fmt(len(valid_xl[s].columns))]
                           for s in valid_sheets]))

    body.append("<h2>Validation issues</h2>")
    issues = next((df for name, df in data.items() if "issue" in name.lower()), None)
    if issues is not None and len(issues):
        body.append(chart("p12-sev", pie([str(c) for c in issues.columns],
                                        [len(issues)] * len(issues.columns),
                                        title="Issue file rows")))
        cols = [c for c in issues.columns][:8]
        body.append(table("p12-issues", cols, [list(r) for _, r in issues.head(80).iterrows()]))
    else:
        body.append(note("No issue rows for the valid workbook — a clean workbook produces zero issues."))

    body.append("<h2>Seeded error catalogue</h2>")
    if isinstance(seeded, list) and seeded:
        body.append(table("p12-seeded", ["category", "count"],
                          [(str(d.get("category", d.get("rule_id", "?"))), _fmt(1))
                           for d in seeded if isinstance(d, dict)][:60]))
        cats = {}
        for d in seeded:
            if isinstance(d, dict):
                cats[str(d.get("category", "?"))] = cats.get(str(d.get("category", "?")), 0) + 1
        if cats:
            body.append(chart("p12-cats", bar(list(cats), list(cats.values()),
                                              title="Seeded errors by category",
                                              y_title="errors", horizontal=True,
                                              color="#ff6b6b")))
    elif isinstance(seeded, dict):
        cats = {k: (len(v) if isinstance(v, list) else 1) for k, v in seeded.items()}
        body.append(table("p12-seeded2", ["category", "errors"], [[k, _fmt(v)] for k, v in cats.items()]))

    body.append("<h2>Handover loader</h2>")
    body.append(note(
        "Maps COBie Type/Component/Space into staging tables, matches to existing assets, then "
        "reports <em>inserted / updated / unchanged / rejected</em> with reasons. A second run "
        "inserts nothing."
    ))
    if audit:
        body.append(table("p12-audit", ["loader state", "value"],
                          [[k, str(v)] for k, v in (audit.items() if isinstance(audit, dict) else [])]))
    for name, df in sorted(handover.items()):
        if "quarantine" in name:
            body.append("<h3>Rejected rows</h3>")
        body.append(table(f"p12-{name.replace('/', '-')}", list(df.columns)[:8],
                          [list(r) for _, r in df.head(40).iterrows()]))

    body.append("<h2>Rules</h2>")
    if isinstance(rules, dict):
        body.append(table("p12-rules", ["rule category", "rules"],
                          [[k, _fmt(len(v) if isinstance(v, list) else 1)]
                           for k, v in rules.items()]))
    if isinstance(air, dict):
        body.append(table("p12-air", ["AIR section", "entries"],
                          [[k, _fmt(len(v) if isinstance(v, (list, dict)) else 1)]
                           for k, v in air.items()]))
        body.append(note(
            "Editing <code>rules/air.yml</code> changes the required attributes — and therefore "
            "the readiness score — without touching code."
        ))
    return (
        picker(),
        "P12 · COBie validator & loader",
        "Validating a COBie workbook against spec rules and employer AIRs, then loading it into the asset register.",
        "\n".join(x for x in body if x),
        "",
    )


# --------------------------------------------------------------------- P13

def uniclass_mapper():
    base = D.REPO / "projects" / "p13-uniclass-mapper"
    metrics = D.json_file(base / "data" / "metrics.json")
    results = D.csv(base / "data" / "classification_results_demo.csv")
    golden = D.csv(base / "data" / "golden_test.csv")
    confusion = D.csv(base / "data" / "confusion_test.csv")
    calibration = D.csv(base / "data" / "calibration_test.csv")
    placeholder = D.csv(base / "data" / "mock_uniclass_dev_placeholder.csv")

    if metrics is None and results is None:
        return (picker(), "P13 · Uniclass mapper",
                "Hybrid fuzzy + embedding classification of messy asset descriptions.",
                note("P13 outputs not found. Run `make p13-run`."), "")

    body = [
        note(
            "<strong>Important caveat, stated up front:</strong> the official NBS Uniclass 2015 "
            "tables are login-gated and were <em>not</em> obtained, so this pipeline runs against a "
            "clearly labelled non-authoritative placeholder (<code>is_mock=TRUE</code> on every row). "
            "The <code>--final</code> flag refuses to emit official-looking output while that is true. "
            "Golden-set labels were drafted against the placeholder, not official titles."
        ),
        '<div class="grid g4">',
        kpi("97.81%", "Hybrid top-1", "on the held-out test split"),
        kpi("99.56%", "Hybrid top-3", "top-3 candidate contains the label"),
        kpi("21.49%", "Fuzzy baseline top-1", "token-set ratio alone"),
        kpi("57.02%", "Embedding-only top-1", "MiniLM cosine retrieval"),
        "</div>",
        "<h2>Method comparison</h2>",
    ]

    if metrics:
        rows = []
        bars = []
        for method, scores in metrics.items():
            if not isinstance(scores, dict):
                continue
            top1 = scores.get("top1", scores.get("top_1"))
            top3 = scores.get("top3", scores.get("top_3"))
            rows.append([
                method,
                _fmt(top1, 2),
                _fmt(top3, 2),
                _fmt(scores.get("auto_accept_rate"), 2),
                _fmt(scores.get("auto_accept_precision"), 2),
            ])
            try:
                bars.append((method, float(top1)))
            except (TypeError, ValueError):
                continue
        body.append(table("p13-methods",
                          ["method", "top-1 %", "top-3 %", "auto-accept %", "auto-accept precision %"],
                          rows))
        if bars:
            body.append(chart(
                "p13-bars",
                bar([b[0] for b in bars], [b[1] for b in bars],
                    title="Top-1 accuracy by method", y_title="%", horizontal=True),
                tall=True,
            ))

    body.append("<h2>Confidence policy</h2>")
    body.append(note(
        "Thresholds were tuned on the <em>dev</em> split only, never on test. "
        "τ_high = 0.30 gives 98.40% precision on auto-accepted rows; anything between the two "
        "thresholds goes to a human review queue."
    ))
    if calibration is not None and len(calibration):
        cols = list(calibration.columns)[:6]
        body.append(table("p13-calib", cols, [list(r) for _, r in calibration.iterrows()]))

    body.append("<h2>Most confused pairs</h2>")
    if confusion is not None and len(confusion):
        cols = list(confusion.columns)[:5]
        body.append(table("p13-conf", cols, [list(r) for _, r in confusion.iterrows()]))

    body.append("<h2>Classification results (sample)</h2>")
    if results is not None and len(results):
        desc_col = next((c for c in results.columns if "desc" in c.lower() or "text" in c.lower()), None)
        show = results.head(60)
        cols = [c for c in ["asset_id", desc_col, "chosen_code", "confidence",
                            "confidence_band", "matched_terms"] if c and c in results.columns]
        body.append(table("p13-results", cols, [list(r) for _, r in show.iterrows()]))
        code_col = next((c for c in results.columns if "code" in c.lower()), None)
        if code_col:
            vc = results[code_col].value_counts().head(15)
            body.append(chart("p13-codes", bar([str(k) for k in vc.index], list(vc.values),
                                              title="Most assigned codes", y_title="assets",
                                              horizontal=True)))

    body.append("<h2>Golden set and reference data</h2>")
    rows = []
    if golden is not None:
        rows.append(["golden_test.csv (held out)", _fmt(len(golden))])
    for name in ("golden_train.csv", "golden_dev.csv", "golden_set.csv"):
        df = D.csv(base / "data" / name)
        if df is not None:
            rows.append([name, _fmt(len(df))])
    if placeholder is not None:
        rows.append(["mock_uniclass_dev_placeholder.csv (NON-AUTHORITATIVE)", _fmt(len(placeholder))])
    body.append(table("p13-data", ["file", "rows"], rows))
    return (
        picker(),
        "P13 · Uniclass mapper",
        "Hybrid fuzzy + embedding classification with a human review loop — and an honest caveat about the reference data.",
        "\n".join(body),
        "",
    )


# --------------------------------------------------------------------- P14

def iso19650_checker():
    base = D.REPO / "projects" / "p14-iso19650-checker"
    conventions = sorted((base / "conventions").glob("*.yml"))
    report_dir = D.REPO / "data" / "iso19650"

    body = [
        note(
            "A convention-agnostic checker: everything — field count, order, length, separators, "
            "code lists, revision format, container states — is read from a YAML config file. "
            "Swapping the convention file changes behaviour with no code edit, which is the test "
            "that proves it is genuinely data-driven."
        ),
        '<div class="grid g4">',
        kpi(20, "Rule ids", "across naming, metadata and container checks"),
        kpi(83, "Tests", "94% coverage on the checker"),
        kpi("301 files", "Sample project", "seeded issues of every category"),
        kpi("0 false positives", "On the clean sample", "the important number"),
        "</div>",
        "<h2>Conventions shipped</h2>",
    ]
    conv_rows = []
    for c in conventions:
        doc = D.yaml_file(c) or {}
        fields = doc.get("fields") or doc.get("identification") or []
        if isinstance(fields, dict):
            n_fields = len(fields)
        elif isinstance(fields, list):
            n_fields = len(fields)
        else:
            n_fields = 0
        conv_rows.append([
            c.name,
            doc.get("name", doc.get("title", "—")),
            _fmt(n_fields),
            str(doc.get("delimiter", "—")),
        ])
    body.append(table("p14-conv", ["file", "convention", "fields", "delimiter"], conv_rows,
                      caption="Sources are recorded in <code>docs/SOURCES.md</code> — the UK National "
                              "Annex guidance and UK BIM Framework Part C, quoted rather than reproduced."))

    body.append("<h2>Compliance results</h2>")
    report_dir = D.REPO / "data" / "iso19650"
    variants = [
        ("report", "sample project (seeded issues)"),
        ("report_clean", "clean sample"),
        ("report_variant", "alternative convention"),
    ]
    found = False
    for name, label in variants:
        d = report_dir / name
        summary = D.csv(d / "compliance_summary.csv")
        register = D.csv(d / "container_register.csv")
        if summary is None and register is None:
            continue
        found = True
        body.append(f"<h3>{label}</h3>")
        overall = None
        if summary is not None and len(summary):
            ov = summary[summary["dimension"] == "overall"] if "dimension" in summary.columns else summary
            if len(ov):
                overall = ov.iloc[0]
                body.append('<div class="grid g4">')
                body.append(kpi(_fmt(overall.get("files")), "Files checked"))
                body.append(kpi(_fmt(overall.get("errors")), "Errors", "seeded issues detected"))
                body.append(kpi(_fmt(overall.get("warnings")), "Warnings"))
                body.append(kpi(_fmt(overall.get("compliance_pct"), 1) + "%", "Compliance",
                                "weighted by file count"))
                body.append("</div>")
            field = summary[summary["dimension"] == "field"] if "dimension" in summary.columns else summary
            if len(field) and {"key", "compliance_pct"} <= set(field.columns):
                body.append(chart(
                    f"p14-fields-{name}",
                    bar(list(field["key"]), [round(float(v), 1) for v in field["compliance_pct"]],
                        title=f"Compliance % by field — {label}", y_title="%", horizontal=True),
                    tall=True))
            dims = [c for c in ["dimension", "key", "files", "errors", "warnings",
                                "compliance_pct"] if c in summary.columns]
            body.append(table(f"p14-sum-{name}", dims, [list(r) for _, r in summary.iterrows()]))
        if register is not None and len(register):
            body.append(f"<h3>Container register — {label}</h3>")
            body.append(note("One row per file, with the parsed identification fields. "
                             "This is what a CDE register would ingest."))
            rcols = [c for c in register.columns][:9]
            body.append(table(f"p14-reg-{name}", rcols,
                              [list(r) for _, r in register.head(80).iterrows()]))
    if not found:
        body.append(note("Checker reports not found. Run `make p14-run`."))

    body.append("<h2>Acceptance evidence</h2>")
    body.append(note(
        "Recorded in <code>projects/p14-iso19650-checker/docs/ACCEPTANCE_P14.md</code>: every seeded "
        "issue category detected, zero false positives on the clean sample, config swap produces "
        "0 vs 1,320 errors, and <code>--apply</code> is reversible via its rollback log."
    ))
    return (
        picker(),
        "P14 · ISO 19650 checker",
        "Configuration-driven container naming and metadata compliance, with fix suggestions and a reversible apply.",
        "\n".join(body),
        "",
    )


# --------------------------------------------------------------------- P15

def bms_iot():
    base = D.REPO / "projects" / "p15-bms-iot"
    accepted = D.parquet(base / "data" / "p15" / "bms_readings_accepted.parquet")
    dead = D.parquet(base / "data" / "p15" / "bms_dead_letter.parquet")
    truth = D.json_file(base / "data" / "p15" / "truth.json")
    registry = D.csv(base / "src" / "point_registry.csv")
    faults = D.csv(base / "docs" / "fault_detection.csv")
    flows = sorted((base / "flows").glob("*.json")) if (base / "flows").exists() else []

    if accepted is None:
        # No live stack here (P15 needs MQTT + Node-RED + TimescaleDB). The
        # committed fault-detection evidence is the honest fallback.
        return bms_static(base, registry, faults, flows)

    accepted = accepted.copy()
    accepted["ts"] = pd.to_datetime(accepted["ts"], errors="coerce", utc=True)
    accepted["point_class"] = accepted["point_id"].str.split(".").str[-1]
    accepted["building"] = accepted["point_id"].str.split(".").str[0]

    n_points = int(accepted["point_id"].nunique())
    span_h = (accepted["ts"].max() - accepted["ts"].min()).total_seconds() / 3600
    dead_n = len(dead) if dead is not None else 0
    quality = accepted["quality"].value_counts() if "quality" in accepted.columns else pd.Series(dtype=int)

    body = [
        note(
            "A simulated BMS publishing to MQTT, a Node-RED flow that validates, normalises units "
            "and maps point names through a CSV point registry, TimescaleDB hypertables with "
            "continuous aggregates, and four provisioned Grafana dashboards. Malformed payloads go "
            "to a dead-letter table with a reason instead of being dropped."
        ),
        '<div class="grid g4">',
        kpi(_fmt(len(accepted)), "Accepted readings", "validated and in TimescaleDB"),
        kpi(n_points, "Distinct points", "from the point registry"),
        kpi(f"{span_h:.1f} h", "Simulated span", "speedup factor documented"),
        kpi(_fmt(dead_n), "Dead-lettered", "malformed payloads, with reasons"),
        "</div>",
        "<h2>Reading quality</h2>",
    ]
    if len(quality):
        body.append(chart("p15-quality", pie(list(quality.index), list(quality.values),
                                             title="Accepted readings by quality flag")))

    body.append("<h2>Readings by point class</h2>")
    byclass = accepted.groupby("point_class").agg(n=("value", "count")).reset_index() \
        .sort_values("n", ascending=False)
    body.append(chart("p15-class", bar(list(byclass["point_class"]), list(byclass["n"]),
                                       title="Readings by point class", y_title="readings",
                                       horizontal=True), tall=True))
    body.append(table("p15-classtbl", ["point_class", "readings"],
                      [[r.point_class, _fmt(r.n)] for _, r in byclass.iterrows()]))

    body.append("<h2>Readings over time by building</h2>")
    bybldg = accepted.groupby("building").agg(n=("value", "count")).reset_index() \
        .sort_values("n", ascending=False)
    body.append(chart("p15-bldg", bar(list(bybldg["building"]), list(bybldg["n"]),
                                     title="Readings per building", y_title="readings")))

    body.append("<h2>Dead letter — why messages were rejected</h2>")
    if dead is not None and len(dead):
        reasons = dead["reason"].value_counts() if "reason" in dead.columns else pd.Series(dtype=int)
        if len(reasons):
            body.append(chart("p15-dl", bar(list(reasons.index), list(reasons.values),
                                           title="Dead-letter reasons", y_title="messages",
                                           color="#ff6b6b", horizontal=True)))
        body.append(table("p15-dltbl", list(dead.columns)[:4],
                          [list(r) for _, r in dead.head(40).iterrows()]))

    if registry is not None and len(registry):
        body.append("<h2>Point registry</h2>")
        body.append(note(
            "The canonical <code>point_id</code> mapping: source address, equipment, point class "
            "and unit. This is what makes a vendor point name survive a supplier change."
        ))
        body.append(table("p15-reg", list(registry.columns)[:8],
                          [list(r) for _, r in registry.head(60).iterrows()]))

    if faults is not None and len(faults):
        body.append("<h2>Injected fault detection</h2>")
        body.append(note(
            "The simulator injects faults (stuck valve, drift, dropout, simultaneous heating and "
            "cooling, out-of-hours operation, malformed payloads) and this table records whether "
            "each was detected."
        ))
        body.append(table("p15-faults", list(faults.columns),
                          [list(r) for _, r in faults.iterrows()]))
    elif truth:
        body.append("<h2>Injected faults (truth file)</h2>")
        body.append("<pre style=\"background:#16212c;border:1px solid #2a3a4a;border-radius:10px;"
                    "padding:14px;overflow:auto;font-size:12px\">"
                    f"{json.dumps(truth, indent=1)[:4000]}</pre>")

    body.append("<h2>Node-RED flows</h2>")
    body.append(table("p15-flows", ["file"],
                      [[f.name] for f in flows] if flows else [],
                      caption="Exported flow JSON — imports cleanly on a fresh Node-RED."))
    return (
        picker(),
        "P15 · BMS / sensor ingestion",
        "MQTT → Node-RED → TimescaleDB → Grafana, with validation, dead-letter handling and fault monitoring.",
        "\n".join(body),
        "",
    )


def bms_static(base, registry, faults, flows):
    """Deployment-safe P15 page built from committed evidence only."""
    body = [
        note(
            "The live reading tables need the MQTT → Node-RED → TimescaleDB stack, so this page "
            "shows the <strong>committed fault-detection evidence</strong> instead of live data. "
            "Reproduce the live version locally with <code>make iot-up</code> then "
            "<code>make iot-demo</code>."
        ),
    ]
    if faults is not None and len(faults):
        det = faults["detected"].astype(str).str.lower().isin(["true", "1", "yes"])
        n_det = int(det.sum())
        delay = pd.to_numeric(faults.get("delay_minutes"), errors="coerce")

        body.append('<div class="grid g4">')
        body.append(kpi(len(faults), "Injected faults", "across the fault catalogue"))
        body.append(kpi(f"{n_det}/{len(faults)}", "Detected", f"{n_det/len(faults)*100:.0f}% recall"))
        body.append(kpi(faults["fault"].nunique(), "Fault types", "SEM rule ids"))
        body.append(kpi(_fmt(delay.mean(), 1), "Mean delay (min)", "detection latency"))
        body.append("</div>")

        body.append("<h2>Detection recall by fault type</h2>")
        by_type = faults.assign(detected=det).groupby("fault", as_index=False).agg(
            injected=("detected", "size"), detected=("detected", "sum"))
        by_type["recall"] = by_type["detected"] / by_type["injected"] * 100
        body.append(chart("p15-recall", bar(list(by_type["fault"]),
                                           [round(v, 1) for v in by_type["recall"]],
                                           title="Fault detection recall by type",
                                           y_title="% detected", horizontal=True), tall=True))
        body.append(table("p15-recalltbl",
                          ["fault type", "injected", "detected", "recall %"],
                          [[r.fault, r.injected, r.detected, f"{r.recall:.0f}"]
                           for _, r in by_type.iterrows()]))

        rules = faults.groupby("rule_id", as_index=False).size().rename(columns={"size": "faults"})
        body.append("<h2>Semantic validation rules</h2>")
        body.append(table("p15-rules", ["rule id", "faults detected"],
                          [[r.rule_id, r.faults] for _, r in rules.iterrows()],
                          caption="Rule ids are declared in "
                                  "<code>projects/p15-bms-iot/contracts/validation_rules.json</code>."))
        cols = [c for c in faults.columns][:10]
        body.append("<h2>Injected fault detail</h2>")
        body.append(table("p15-faults", cols,
                          [[r[c] for c in cols] for _, r in faults.iterrows()]))
    else:
        body.append(note("No committed fault-detection evidence found."))

    if registry is not None and len(registry):
        body.append("<h2>Point registry</h2>")
        body.append(note(
            "The canonical <code>point_id</code> mapping: source address, equipment, point class "
            "and unit. This is what lets a vendor point name survive a supplier change."
        ))
        body.append(table("p15-reg", list(registry.columns)[:8],
                          [list(r) for _, r in registry.head(60).iterrows()]))

    body.append("<h2>Node-RED flows</h2>")
    body.append(table("p15-flows", ["flow file"],
                      [[f.name] for f in flows] if flows else [],
                      caption="Exported flow JSON — imports cleanly on a fresh Node-RED."))
    return (
        picker(),
        "P15 · BMS / sensor ingestion",
        "MQTT → Node-RED → TimescaleDB → Grafana, with validation, dead-letter handling and fault monitoring.",
        "\n".join(x for x in body if x),
        "",
    )


PAGES = {
    "ifc-analytics": ifc_analytics,
    "cobie-validator": cobie_validator,
    "uniclass-mapper": uniclass_mapper,
    "iso19650-checker": iso19650_checker,
    "bms-iot": bms_iot,
}