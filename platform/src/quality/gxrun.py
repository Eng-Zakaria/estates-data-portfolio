"""P03 GX runner: execute suites on pandas frames, collect counts + samples.

One file-context per run (so ``build_data_docs`` renders every validation).
``result_format`` COMPLETE with ``partial_unexpected_count=100`` satisfies the
"up to 100 sample rows" requirement: offending values come from GX, full sample
rows are selected from the in-memory frame by matching those values.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import great_expectations as gx
import pandas as pd
from great_expectations.core.result_format import ResultFormat

from .gxcompile import expectation_key

SAMPLE_LIMIT = 100


@dataclass
class GxResult:
    check_id: str
    rows_checked: int
    rows_failed: int
    samples: list[dict] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if self.rows_checked <= 0:
            return 1.0
        return max(0.0, 1.0 - self.rows_failed / self.rows_checked)


def _frame_samples(frame: pd.DataFrame, columns: list[str], values: list, limit: int = SAMPLE_LIMIT) -> list[dict]:
    """Select up to ``limit`` full rows whose columns match offending values."""
    if not columns or not values:
        return []
    sub = frame[columns]
    if len(columns) == 1:
        col = columns[0]
        try:
            mask = sub[col].isin(values)
        except TypeError:
            return []
        picked = frame.loc[mask].head(limit)
    else:
        keys = set()
        for v in values:
            keys.add(tuple(v) if isinstance(v, (list, tuple)) else (v,))
        tuples = pd.Series(list(zip(*[sub[c] for c in columns], strict=True)), index=sub.index)
        picked = frame.loc[tuples.isin(keys)].head(limit)
    out: list[dict] = []
    for row in picked.to_dict(orient="records"):
        out.append({k: (None if pd.isna(v) else str(v)) for k, v in row.items()})
    return out


def run_suite(
    context: gx.DataContext,
    batch_definition: object,
    suite: gx.ExpectationSuite,
    frame: pd.DataFrame,
    check_index: dict[tuple, str],
) -> list[GxResult]:
    """Run one suite; map each expectation result back to its check id."""
    vd = gx.ValidationDefinition(data=batch_definition, suite=suite, name=f"vd_{suite.name}")
    context.validation_definitions.add(vd)
    result = vd.run(
        batch_parameters={"dataframe": frame},
        result_format={  # type: ignore[arg-type]
            "result_format": ResultFormat.COMPLETE,
            "partial_unexpected_count": SAMPLE_LIMIT,
        },
    )
    if len(result.results) != len(suite.expectations):
        raise RuntimeError(
            f"suite {suite.name}: {len(result.results)} results for {len(suite.expectations)} expectations"
        )
    out: list[GxResult] = []
    for exp_result, exp_config in zip(result.results, suite.expectations, strict=True):
        key = expectation_key(exp_config.expectation_type, exp_config.kwargs)
        check_id = check_index[key]
        payload = exp_result.result or {}
        checked = int(payload.get("element_count", len(frame)))
        failed = int(payload.get("unexpected_count", 0))
        samples: list[dict] = []
        if failed:
            cols = list(key[1])
            raw_values = payload.get("partial_unexpected_list", []) or []
            if exp_config.expectation_type == "ExpectTableRowCountToBeBetween":
                samples = [{"observed_value": str(payload.get("observed_value"))}]
            else:
                samples = _frame_samples(frame, cols, list(raw_values))
        out.append(GxResult(check_id, checked, failed, samples))
    return out
