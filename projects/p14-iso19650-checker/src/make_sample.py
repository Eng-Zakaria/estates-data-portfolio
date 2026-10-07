"""Sample information container project generator.

Generates a synthetic CDE-shaped folder tree (WIP / Shared / Published / Archive) that is compliant
with a shipped convention, then injects one file per seeded issue category. Everything is seeded, so
two runs with the same seed produce byte-identical trees and the same truth file.

    python make_sample.py --out data/iso19650/sample --n 300 --seed 42
    python make_sample.py --out data/iso19650/clean --clean     # zero issues, for false-positive tests

The truth file records, per file, the rule ids the seed *plants* (not the full expected issue list, so
tests are not circular: collateral findings from the same malformed name are allowed). Series gaps and
orphans are recorded separately because those findings are reported against a series or a register.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path

import yaml

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DEFAULT_CONVENTION = SRC.parent / "conventions" / "uk_national_annex.yml"

ORIGINATORS = ["ESTM", "ENGG", "ARCV", "FMVS", "QSUR", "STRUCT"]
# Padded to the convention's widths at build time; the source pools are ordinary org/discipline codes.
DOC_EXTS = [".txt", ".docx"]
PLACEHOLDER_EXTS = [".ifc", ".pdf", ".xlsx", ".dwg", ".rvt"]
ALL_EXTS = DOC_EXTS + PLACEHOLDER_EXTS


@dataclass
class Truth:
    files: list[dict[str, object]] = dataclass_field(default_factory=list)
    series_gaps: list[dict[str, object]] = dataclass_field(default_factory=list)
    orphans: list[str] = dataclass_field(default_factory=list)

    def record(self, path: Path, root: Path, seeded: list[str], note: str = "") -> None:
        self.files.append(
            {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "seeded_rule_ids": seeded,
                "note": note,
            }
        )

    def gap(self, rule_id: str, series: str, missing: list[str]) -> None:
        self.series_gaps.append({"rule_id": rule_id, "series": series, "missing": missing})


class ValuePool:
    """Legal values for each field, derived from the convention so both conventions work."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.sep = config.get("separator", "-")
        self.fields = {f["name"]: f for f in config["fields"]}
        self.order = [f["name"] for f in config["fields"]]
        self.states = list(config.get("container_states", {}))

    def spec(self, name: str) -> dict | None:
        return self.fields.get(name)

    def concrete_status(self, state: str) -> str:
        values = self.config["container_states"].get(state, ["S0"])
        for value in values:
            if "*" not in value:
                return value
        return values[0].replace("*", "1")

    def revision_for(self, state: str) -> str | None:
        spec = self.spec("revision")
        if spec is None:
            return None
        if not spec.get("required", True):
            return None
        import re

        pattern = spec.get("pattern")
        candidates = {
            "WIP": ["P01.01", "P02.01", "P01"],
            "Shared": ["P01", "P02", "P03"],
            "Published": ["C01", "C02"],
            "Archive": ["C01"],
        }.get(state, ["P01", "C01"])
        if pattern:
            compiled = re.compile(f"^(?:{pattern})$")
            for candidate in candidates:
                if compiled.match(candidate):
                    return candidate
            return None
        return candidates[0]

    def from_codes(self, name: str, fallback: str) -> str | None:
        spec = self.spec(name)
        if spec is None:
            return None
        values = spec.get("allowed_values")
        if not values:
            return None
        return next((v for v in values if "*" not in v), fallback)

    def width(self, name: str, fallback: int = 2) -> int:
        """Natural (shortest legal) width of a field: its fixed length, else min_length."""
        spec = self.spec(name) or {}
        if spec.get("length"):
            return int(spec["length"])
        return int(spec.get("min_length", fallback))

    def pad(self, value: str, name: str) -> str:
        """Fit a published code into the field; codes are used as published, never padded."""
        width = self.width(name)
        return value[:width] if len(value) > width else value


def _write_content(path: Path, ext: str, title: str) -> None:
    """Write a synthetic container. Real formats are written when the optional dependency exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if ext == ".txt":
        path.write_text(f"{title}\n\nSynthetic placeholder for portfolio demonstration.\n", encoding="utf-8")
        return
    if ext == ".docx":
        try:
            import docx  # noqa: PLC0415 - optional dependency
        except ImportError:
            path.write_text("synthetic placeholder (python-docx not installed)\n", encoding="utf-8")
            return
        document = docx.Document()
        document.core_properties.title = title
        document.add_paragraph(title)
        document.save(str(path))
        return
    path.write_text("synthetic placeholder container\n", encoding="utf-8")


def _title_for(values: dict[str, str], pool: ValuePool) -> str:
    """A document title that agrees with the file name (used by compliant files)."""
    bits = [
        values.get("type", "DOC"),
        values.get("number", ""),
        values.get("originator", ""),
        values.get("level_location", ""),
    ]
    return " ".join(b for b in bits if b) + " synthetic container"


class SampleProject:
    def __init__(self, out: Path, config: dict, seed: int = 42) -> None:
        self.out = out
        self.config = config
        self.pool = ValuePool(config)
        self.rng = random.Random(seed)
        self.truth = Truth()
        self.counters: dict[tuple[str, ...], int] = defaultdict(int)
        self.series_folders: dict[tuple[str, ...], str] = {}
        # Extensions come from the convention's allowlist so a "clean" sample is genuinely compliant;
        # formats we can actually write (txt/docx) are preferred because they feed the metadata check.
        allowed = [e.lower() for e in config.get("extension_allowlist", [])]
        readable = [e for e in allowed if e in DOC_EXTS]
        self.ext_pool = readable or [e for e in allowed if e in PLACEHOLDER_EXTS] or list(ALL_EXTS)
        # The number identifies a container together with the convention's id fields, so the series
        # keys must use the same facets the checker uses, or two series would share a number.
        id_fields = set(config.get("id_fields") or [f["name"] for f in config["fields"]])
        self.series_names = [n for n in self.pool.order if n not in {"number", "revision", "status"} and n in id_fields]

    # -- naming -----------------------------------------------------------------------
    def _compliant_values(self, state: str) -> dict[str, str]:
        pool = self.pool
        values: dict[str, str] = {}
        for name in pool.order:
            if name == "status":
                values[name] = pool.concrete_status(state)
            elif name == "revision":
                revision = pool.revision_for(state)
                if revision is not None:
                    values[name] = revision
            elif name == "number":
                values[name] = ""  # assigned by the series counter
            else:
                code = pool.from_codes(name, "")
                if code:
                    values[name] = pool.pad(code, name)
                    continue
                values[name] = self._invent(name)
        if pool.spec("project"):
            values["project"] = self._fit_project(self.rng.choice(["PRJ01", "PRJ02", "PRJ03"]))
        if pool.spec("originator"):
            spec = pool.spec("originator") or {}
            max_len = int(spec.get("length") or spec.get("max_length") or 6)
            values["originator"] = self.rng.choice([o[:max_len] for o in ORIGINATORS])
        if pool.spec("asset_class"):
            values["asset_class"] = self.rng.choice(["PR1", "PR2", "EN1"])
        return values

    def _invent(self, name: str) -> str:
        """Deterministic filler for a field with no published code list."""
        pool = self.pool
        width = pool.width(name)
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if name != "number" else "0123456789"
        return "".join(self.rng.choice(alphabet) for _ in range(width))

    def _stem(self, values: dict[str, str]) -> str:
        return self.pool.sep.join(values[name] for name in self.pool.order if values.get(name))

    def _next_number(self, values: dict[str, str], state: str, folder: str) -> str:
        """Next sequential number for a series.

        The counter is per (state, folder, series) so that each folder holds a contiguous series:
        numbers scattered across sibling folders would look like gaps to the checker, and they are not.
        """
        key = (
            state,
            folder,
            *(values.get(n, "") for n in self.series_names),
        )
        self.counters[key] += 1
        value = self.counters[key]
        width = self.pool.width("number", fallback=4)
        return str(value).zfill(width)

    def _series_key(self, values: dict[str, str], drop: str) -> str:
        """Stem with one field removed - mirrors the checker's series keys (number / revision series)."""
        index = self.pool.order.index(drop)
        parts = [v for i, v in enumerate(values.values()) if i != index and v]
        return self.pool.sep.join(parts)

    def _series_tuple(self, values: dict[str, str], state: str) -> tuple[str, ...]:
        return (state, *(values.get(n, "") for n in self.series_names))

    def _folder_for(self, values: dict[str, str], state: str) -> str:
        """One folder per series, so a series' numbers stay together and gap checks stay meaningful."""
        key = self._series_tuple(values, state)
        if key not in self.series_folders:
            self.series_folders[key] = self.rng.choice(["", "PackageA", "PackageB", f"Zone{self.rng.randint(1, 3)}"])
        return self.series_folders[key]

    # -- writing ---------------------------------------------------------------------
    def _emit(
        self,
        state: str,
        subfolder: str,
        values: dict[str, str],
        seeded: list[str],
        note: str = "",
        ext: str | None = None,
        title: str | None = None,
        numbered: bool = True,
    ) -> Path:
        if numbered and "number" in values:
            values["number"] = self._next_number(values, state, subfolder)
        if "revision" in self.pool.fields and values.get("revision") is None:
            values.pop("revision", None)
        ext = ext or self.rng.choice(self.ext_pool)
        stem = self._stem(values)
        path = self.out / state / subfolder / f"{stem}{ext}"
        suffix = 2
        while path.exists():
            path = path.with_name(f"{stem}-{suffix}{ext}")
            suffix += 1
        _write_content(path, ext, title if title is not None else _title_for(values, self.pool))
        self.truth.record(path, self.out, seeded, note)
        return path

    # -- compliant population ---------------------------------------------------------
    def populate(self, count: int) -> None:
        states = self.pool.states or ["WIP"]
        for _ in range(count):
            state = self.rng.choice(states)
            values = self._compliant_values(state)
            sub = self._folder_for(values, state)
            self._emit(state, sub, values, [], "compliant")

    # -- seeded violations -----------------------------------------------------------
    def seed_all(self) -> None:
        state = (self.pool.states or ["WIP"])[0]
        seeds = [
            self._seed_field_count,
            self._seed_field_missing,
            self._seed_field_length_short,
            self._seed_field_length_long,
            self._seed_charset,
            self._seed_allowed_value,
            self._seed_status_pattern,
            self._seed_revision_format,
            self._seed_lowercase,
            self._seed_illegal_character,
            self._seed_separator_misuse,
            self._seed_empty_field,
            self._seed_disallowed_extension,
            self._seed_status_container_mismatch,
            self._seed_metadata_mismatch,
        ]
        for seed in seeds:
            seed(state)

    def _values(self, state: str, project: str | None = None) -> dict[str, str]:
        """Values for a seeded file. Each seed gets its own project code so a seeded container can never
        collide with the compliant population (a collision would look like a duplicate identifier)."""
        values = self._compliant_values(state)
        if project and "project" in values:
            values["project"] = project
        return values

    def _seed_project(self, index: int) -> str:
        return self._fit_project(f"SD{index:02d}")

    def _fit_project(self, code: str) -> str:
        """Fit a project code to whatever width the convention demands."""
        if "project" not in self.pool.fields:
            return code
        spec = self.pool.spec("project") or {}
        low = self.pool.width("project", fallback=len(code))
        high = int(spec.get("max_length") or spec.get("length") or len(code))
        if len(code) < low:
            return code.ljust(low, "0")
        return code[:high]

    def _field_index(self, name: str) -> int:
        return self.pool.order.index(name)

    def _replace(self, values: dict[str, str], name: str, new_value: str) -> None:
        values[name] = new_value

    def _seed_field_count(self, state: str) -> None:
        """One field too many: the Annex allows fields to be dropped, not silently merged."""
        values = self._values(state, self._seed_project(1))
        values["number"] = self._next_number(values, state, "Seeds")
        stem = f"{self._stem(values)}{self.pool.sep}EXTRA"
        ext = self.rng.choice(self.ext_pool)
        path = self.out / state / "Seeds" / f"{stem}{ext}"
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_content(path, ext, _title_for(values, self.pool))
        self.truth.record(path, self.out, ["field_count"], "extra field appended")

    def _seed_field_missing(self, state: str) -> None:
        values = self._values(state, self._seed_project(2))
        order = [n for n in self.pool.order if n in values]
        if len(order) < 4:
            return
        dropped = order[-2]
        del values[dropped]
        self._emit(state, "Seeds", values, ["field_missing"], f"{dropped} omitted")

    def _seed_field_length_short(self, state: str) -> None:
        values = self._values(state, self._seed_project(3))
        if "project" in values:
            self._replace(values, "project", "P")
            self._emit(state, "Seeds", values, ["field_length"], "project code too short")

    def _seed_field_length_long(self, state: str) -> None:
        values = self._values(state, self._seed_project(4))
        if "originator" in values:
            self._replace(values, "originator", "ORIGINATOR-ONE")
            self._emit(state, "Seeds", values, ["field_length"], "originator code too long")

    def _seed_charset(self, state: str) -> None:
        values = self._values(state, self._seed_project(5))
        if "role" not in values:
            return
        self._replace(values, "role", "9")
        self._emit(state, "Seeds", values, ["field_charset"], "digit in an A-Z field")

    def _seed_allowed_value(self, state: str) -> None:
        values = self._values(state, self._seed_project(6))
        if "level_location" not in values:
            return
        self._replace(values, "level_location", "99")
        self._emit(state, "Seeds", values, ["field_allowed_values"], "level code outside the published list")

    def _seed_status_pattern(self, state: str) -> None:
        values = self._values(state, self._seed_project(7))
        if "status" not in values:
            return
        self._replace(values, "status", "S9")
        self._emit(state, "Seeds", values, ["field_pattern"], "status code outside S0-S6/A/B/CR pattern")

    def _seed_revision_format(self, state: str) -> None:
        values = self._values(state, self._seed_project(8))
        if "revision" not in values:
            return
        self._replace(values, "revision", "X1")
        self._emit(state, "Seeds", values, ["field_pattern", "revision_format"], "revision without P/C prefix")

    def _seed_lowercase(self, state: str) -> None:
        values = self._values(state, self._seed_project(9))
        values = {k: (v.casefold() if v.isalpha() else v) for k, v in values.items()}
        self._emit(state, "Seeds", values, ["field_case"], "lower-case fields (fixable by rename)")

    def _seed_illegal_character(self, state: str) -> None:
        values = self._values(state, self._seed_project(10))
        if "originator" not in values:
            return
        self._replace(values, "originator", "ES@M")
        self._emit(state, "Seeds", values, ["illegal_character"], "@ is illegal in a file name")

    def _seed_separator_misuse(self, state: str) -> None:
        values = self._values(state, self._seed_project(11))
        values["number"] = self._next_number(values, state, "Seeds")
        stem = self._stem(values).replace(self.pool.sep, "_")
        ext = self.rng.choice(self.ext_pool)
        path = self.out / state / "Seeds" / f"{stem}{ext}"
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_content(path, ext, _title_for(values, self.pool))
        self.truth.record(path, self.out, ["separator_misuse"], "underscore used instead of the convention separator")

    def _seed_empty_field(self, state: str) -> None:
        values = self._values(state, self._seed_project(12))
        values["number"] = self._next_number(values, state, "Seeds")
        stem = self._stem(values)
        order = [n for n in self.pool.order if n in values]
        index = self._field_index(order[1])
        parts = stem.split(self.pool.sep)
        parts.insert(index, "")
        stem = self.pool.sep.join(parts)
        ext = self.rng.choice(self.ext_pool)
        path = self.out / state / "Seeds" / f"{stem}{ext}"
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_content(path, ext, _title_for(values, self.pool))
        self.truth.record(path, self.out, ["empty_field"], "empty field between separators")

    def _seed_disallowed_extension(self, state: str) -> None:
        values = self._values(state, self._seed_project(13))
        self._emit(state, "Seeds", values, ["disallowed_extension"], ".exe is not in the allowlist", ext=".exe")

    def _seed_status_container_mismatch(self, state: str) -> None:
        """A container whose status belongs to a later state sits in an earlier one."""
        states = self.pool.states
        values = self._values(state, self._seed_project(14))
        if "status" not in values or len(states) < 2:
            return
        later = states[-1]
        mismatched = self.pool.concrete_status(later)
        self._replace(values, "status", mismatched)
        self._emit(state, "Seeds", values, ["status_container_mismatch"], f"{mismatched} inside the {state} state")

    def _seed_metadata_mismatch(self, state: str) -> None:
        values = self._values(state, self._seed_project(15))
        self._emit(
            state,
            "Seeds",
            values,
            ["metadata_mismatch"],
            "document title does not mention the originator or number in the file name",
            ext=".txt",
            title="Site walkaround notes",
        )

    def _seed_long_names(self) -> None:
        """path_length + stem_length warnings: a deeply nested folder with a padded name."""
        state = (self.pool.states or ["WIP"])[0]
        folder = "VeryLongFolderNameForTestingPathLengthWarnings" * 3
        values = self._values(state, self._seed_project(90))
        values["number"] = self._next_number(values, state, folder)
        deep = self.out / state / "Archive" / folder
        stem = self._stem(values)
        path = deep / f"{stem}{'-PADDING' * 12}.txt"
        _write_content(path, ".txt", _title_for(values, self.pool))
        self.truth.record(path, self.out, ["path_length", "stem_length"], "path and stem over the configured limits")

    def _seed_duplicates(self) -> None:
        """Two containers sharing an id and revision: the second one found is flagged.

        The folders are named so the walk sees the original first (AOriginal before ZCopy) and reports
        the copy - which is the file the truth file plants the duplicate on.
        """
        state = (self.pool.states or ["WIP"])[0]
        values = self._values(state, self._seed_project(91))
        first = self._emit(state, "Seeds/AOriginal", values, [], "original container")
        duplicate = self.out / state / "Seeds" / "ZCopy" / first.name
        duplicate.parent.mkdir(parents=True, exist_ok=True)
        duplicate.write_bytes(first.read_bytes())
        self.truth.record(duplicate, self.out, ["duplicate_identifier"], "second container with the same id+revision")

    def _seed_series_gaps(self) -> None:
        """Number and revision gaps are series-level findings, recorded in the truth file.

        Each gap series gets its own project code so it cannot collide with the compliant population.
        """
        state = (self.pool.states or ["WIP"])[0]
        width = self.pool.width("number", fallback=4)

        # --- number gap: 0001, 0002, 0004 -> 0003 missing
        values = self._values(state)
        if "project" in values:
            values["project"] = "GAP01"
        numbers = [1, 2, 4]
        for number in numbers:
            container = dict(values)
            container["number"] = str(number).zfill(width)
            path = self.out / state / "Seeds" / f"{self._stem(container)}.txt"
            _write_content(path, ".txt", _title_for(container, self.pool))
            self.truth.record(path, self.out, [], "compliant member of a number series with a gap")
        missing = [str(n).zfill(width) for n in range(1, 5) if n not in numbers]
        self.truth.gap(
            "number_gap", self._series_key({**values, "number": str(numbers[0]).zfill(width)}, "number"), missing
        )

        # --- revision gap: same id, P01 and P03 -> P02 missing
        if "revision" not in self.pool.fields or not self.pool.spec("revision"):
            return
        rev_values = self._values(state)
        if "project" in rev_values:
            rev_values["project"] = "REV01"
        rev_values["number"] = str(1).zfill(width)
        for revision in ("P01", "P03"):
            container = dict(rev_values)
            container["revision"] = revision
            path = self.out / state / "Seeds" / f"{self._stem(container)}.txt"
            _write_content(path, ".txt", _title_for(container, self.pool))
            self.truth.record(path, self.out, [], "compliant member of a revision series with a gap")
        self.truth.gap("revision_gap", self._series_key(rev_values, "revision"), ["02"])

    def _seed_orphan(self) -> Path:
        """A file that exists on disk but is absent from the container register."""
        state = (self.pool.states or ["WIP"])[0]
        values = self._values(state, self._seed_project(92))
        path = self._emit(
            state, "Seeds", values, ["orphan_file"], "created without being added to the container register"
        )
        self.truth.orphans.append(str(path.relative_to(self.out)).replace("\\", "/"))
        return path

    def seed_violations(self) -> None:
        self.seed_all()
        self._seed_long_names()
        self._seed_series_gaps()
        self._seed_duplicates()
        self._seed_orphan()

    # -- register --------------------------------------------------------------------
    def write_register(self, register_path: Path, skip: list[str]) -> None:
        """Container register for every generated file except the seeded orphans."""
        import hashlib

        rows = []
        for path in sorted(self.out.rglob("*")):
            if not path.is_file():
                continue
            rel = str(path.relative_to(self.out)).replace("\\", "/")
            if rel in skip:
                continue
            parts = path.stem.split(self.pool.sep)
            row = {"path": rel, "container_id": self.pool.sep.join(parts[:7]), "sha256": ""}
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            row["sha256"] = digest
            rows.append(row)
        register_path.parent.mkdir(parents=True, exist_ok=True)
        with open(register_path, "w", encoding="utf-8", newline="") as handle:
            handle.write("path,container_id,sha256\n")
            for row in rows:
                handle.write(f"{row['path']},{row['container_id']},{row['sha256']}\n")


def make_sample(
    out: Path,
    n_files: int = 300,
    seed: int = 42,
    clean: bool = False,
    config_path: Path = DEFAULT_CONVENTION,
) -> dict:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    project = SampleProject(out, config, seed=seed)
    out.mkdir(parents=True, exist_ok=True)

    reserved = 15 + 1 + 4 + 2 + 1  # seeds + long names + series members + duplicate + orphan
    clean_count = max(n_files - reserved, 1) if not clean else n_files
    project.populate(clean_count)
    if not clean:
        project.seed_violations()

    total = len(project.truth.files)
    # Artefacts are named after the sample so generating several samples side by side cannot clobber
    # each other's truth file or register.
    truth_path = out.parent / f"{out.name}_truth.json"
    register_path = out.parent / f"{out.name}_register.csv"
    project.write_register(register_path, project.truth.orphans)

    payload = {
        "convention": config["name"],
        "config": str(config_path),
        "seed": seed,
        "root": str(out),
        "clean": clean,
        "register": str(register_path),
        "counts": {
            "total": total,
            "compliant": sum(1 for f in project.truth.files if not f["seeded_rule_ids"]),
            "seeded": sum(1 for f in project.truth.files if f["seeded_rule_ids"]),
            "orphans": len(project.truth.orphans),
            "series_gaps": len(project.truth.series_gaps),
        },
        **project.truth.__dict__,
    }
    truth_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"Generated {total} files in {out} (seed {seed}): "
        f"{payload['counts']['seeded']} seeded issue files, {payload['counts']['orphans']} orphan(s). "
        f"Truth file: {truth_path}"
    )
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("data/iso19650/sample"))
    parser.add_argument("--n", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clean", action="store_true", help="generate only compliant containers")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONVENTION)
    args = parser.parse_args()
    make_sample(args.out, args.n, args.seed, args.clean, args.config)
