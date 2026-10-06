"""Sample project folder generator: ~300 files, seeded issues of every category, logged to truth file."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

ISSUE_CATEGORIES = [
    "wrong_field_count",
    "wrong_field_length",
    "invalid_charset",
    "disallowed_extension",
    "status_container_mismatch",
    "duplicate_identifier",
    "lowercase_field",
    "path_too_long",
]


def make_sample(out: Path, n_files: int = 300, seed: int = 42) -> None:
    random.seed(seed)
    truth = {"files": [], "issues": []}

    folders = ["WIP", "Shared", "Published", "Archive"]
    for i in range(n_files):
        folder = random.choice(folders)
        ext = random.choice([".ifc", ".pdf", ".dwg", ".xlsx", ".docx", ".exe"])

        # Decide issue
        issue = random.choice(ISSUE_CATEGORIES) if random.random() < 0.3 else None

        # Map folder to expected status code (matching convention config)
        folder_status = {"WIP": "WIP", "Shared": "S1", "Published": "S4", "Archive": "S7"}
        expected_status = folder_status.get(folder, "S1")
        # Pad 2-char codes to 3 for consistent length check
        if len(expected_status) == 2:
            expected_status = expected_status.ljust(
                3, " "
            ).rstrip()  # "S1" stays "S1", but we'll handle length in config
        # Simpler: just use the codes as-is and set config length to null or use a range

        if issue == "wrong_field_count":
            name = f"PRJ001-ORG001-VO-LL-TY-RO-{i:04d}"
        elif issue == "wrong_field_length":
            # Make revision too long (expected 2, got 7)
            name = f"PRJ001-ORG001-VO-LL-TY-RO-{i:04d}-{expected_status}-TOOLONG"
        elif issue == "invalid_charset":
            name = f"PRJ001-ORG001-VO-LL-TY-RO-{i:04d}-{expected_status}-P1!"
        elif issue == "disallowed_extension":
            ext = ".exe"
            name = f"PRJ001-ORG001-VO-LL-TY-RO-{i:04d}-{expected_status}-P1"
        elif issue == "status_container_mismatch":
            folder = "WIP"
            name = f"PRJ001-ORG001-VO-LL-TY-RO-{i:04d}-S4-P1"
        elif issue == "duplicate_identifier":
            name = f"PRJ001-ORG001-VO-LL-TY-RO-0001-{expected_status}-P1"
        elif issue == "lowercase_field":
            name = f"prj001-org001-vo-ll-ty-ro-{i:04d}-{expected_status.lower()}-p1"
        elif issue == "path_too_long":
            name = f"PRJ001-ORG001-VO-LL-TY-RO-{i:04d}-{expected_status}-P1" + "-" * 50
        else:
            name = f"PRJ001-ORG001-VO-LL-TY-RO-{i:04d}-{expected_status}-P1"

        path = out / folder / f"{name}{ext}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("sample")
        truth["files"].append(str(path))
        if issue:
            truth["issues"].append({"path": str(path), "category": issue})

    out.mkdir(parents=True, exist_ok=True)
    # Write truth file outside the sample folder so the checker doesn't scan it
    truth_path = out.parent / "truth_issues.json"
    truth_path.write_text(json.dumps(truth, indent=2))
    print(f"Generated {n_files} files in {out}, {len(truth['issues'])} seeded issues")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/iso19650/sample"))
    parser.add_argument("--n", type=int, default=300)
    args = parser.parse_args()
    make_sample(args.out, args.n)
