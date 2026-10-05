"""P03 GX compiler: check YAML -> ``ExpectationSuite`` per dataset.

``value_set_from: {truth_table, column}`` is resolved by querying the truth
reference so large code lists (500 spaces, 16 meters) never get hand-copied
into YAML. ``threshold`` maps to GX ``mostly``.
"""

from __future__ import annotations

from collections import OrderedDict

import duckdb
import great_expectations as gx

from .spec import CheckSpec

_EXPECTATION_FACTORY = {
    "ExpectColumnValuesToNotBeNull": gx.expectations.ExpectColumnValuesToNotBeNull,
    "ExpectColumnValuesToBeUnique": gx.expectations.ExpectColumnValuesToBeUnique,
    "ExpectCompoundColumnsToBeUnique": gx.expectations.ExpectCompoundColumnsToBeUnique,
    "ExpectColumnValuesToBeInSet": gx.expectations.ExpectColumnValuesToBeInSet,
    "ExpectColumnValuesToBeBetween": gx.expectations.ExpectColumnValuesToBeBetween,
    "ExpectColumnValuesToMatchRegex": gx.expectations.ExpectColumnValuesToMatchRegex,
    "ExpectTableRowCountToBeBetween": gx.expectations.ExpectTableRowCountToBeBetween,
}


def expectation_key(expectation_type: str, kwargs: dict) -> tuple:
    """Identity of an expectation within a suite: (normalised_type, columns)."""
    import re

    # Normalise PascalCase (ExpectFoo) to snake_case (expect_foo)
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", expectation_type).lower()
    col = kwargs.get("column")
    cols = tuple(kwargs.get("column_list", [col] if col else []))
    return (snake, cols)


def build_check_index(specs: list[CheckSpec]) -> dict[str, dict[tuple, str]]:
    """Map (dataset -> expectation key -> check id); collisions are spec errors."""
    index: dict[str, dict[tuple, str]] = {}
    for spec in sorted([s for s in specs if s.engine == "gx"], key=lambda s: (s.dataset, s.id)):
        key = expectation_key(spec.expectation or "", spec.kwargs or {})
        per_ds = index.setdefault(spec.dataset, {})
        if key in per_ds:
            raise ValueError(
                f"checks {per_ds[key]} and {spec.id}: same (expectation, columns) "
                "in one dataset; results would be ambiguous"
            )
        per_ds[key] = spec.id
    return index


def resolve_kwargs(spec: CheckSpec, truth_lookup: dict[str, dict[str, list[str]]] | None = None) -> dict:
    """Resolve ``value_set_from`` against pre-fetched truth code lists."""
    kwargs = dict(spec.kwargs or {})
    source = kwargs.pop("value_set_from", None)
    if source is not None:
        if truth_lookup is None:
            raise ValueError(f"check {spec.id}: value_set_from needs truth_lookup")
        table, column = source["truth_table"], source["column"]
        try:
            values = truth_lookup[table][column]
        except KeyError as exc:
            raise ValueError(f"check {spec.id}: unknown value_set_from {source}") from exc
        kwargs["value_set"] = values
    return kwargs


def fetch_truth_lists(con: duckdb.DuckDBPyConnection, refs: set[tuple[str, str]]) -> dict[str, dict[str, list[str]]]:
    """Fetch distinct code lists for every (truth_table, column) referenced."""
    out: dict[str, dict[str, list[str]]] = {}
    for table, column in sorted(refs):
        rows = con.execute(f"SELECT DISTINCT {column} FROM truth_{table} WHERE {column} IS NOT NULL").fetchall()
        out.setdefault(table, {})[column] = sorted(str(r[0]) for r in rows)
    return out


def compile_suites(
    specs: list[CheckSpec],
    con: duckdb.DuckDBPyConnection,
    suite_prefix: str = "dq",
) -> OrderedDict[str, gx.ExpectationSuite]:
    """Group GX checks by dataset; one suite per dataset (deterministic order)."""
    gx_specs = [s for s in specs if s.engine == "gx"]
    refs = {
        (k["truth_table"], k["column"]) for s in gx_specs if (k := (s.kwargs or {}).get("value_set_from")) is not None
    }
    lookup = fetch_truth_lists(con, refs)
    suites: OrderedDict[str, gx.ExpectationSuite] = OrderedDict()
    for spec in sorted(gx_specs, key=lambda s: (s.dataset, s.id)):
        suite = suites.setdefault(
            f"{suite_prefix}_{spec.dataset}",
            gx.ExpectationSuite(name=f"{suite_prefix}_{spec.dataset}"),
        )
        factory = _EXPECTATION_FACTORY[spec.expectation or ""]
        kwargs = resolve_kwargs(spec, lookup)
        suite.add_expectation(factory(**kwargs, mostly=spec.mostly))
    return suites
