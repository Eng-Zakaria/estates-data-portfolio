"""Main orchestrator for P10 institutional return (run from repo root)."""

from __future__ import annotations

import argparse
import uuid
from datetime import date
from pathlib import Path

from mapping import write_mapping_csv
from return_builder import build_return
from validation import validate_return_data, write_validation_report
from cost_allocation import build_allocation, check_balance, write_allocation_csv
from audit import log_run, sign_off, snapshot_outputs, verify_deterministic


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build P10 institutional return.")
    p.add_argument("--return-date", default=date.today().isoformat(), help="Return date (YYYY-MM-DD)")
    p.add_argument("--out", default="data/p10_output", help="Output directory")
    p.add_argument("--sign-off", action="store_true", help="Record sign-off after build")
    p.add_argument("--reviewer", default="", help="Reviewer name for sign-off")
    p.add_argument("--verify", action="store_true", help="Verify deterministic re-run")
    args = p.parse_args(argv)

    return_date = date.fromisoformat(args.return_date)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = f"p10_{return_date.isoformat()}_{uuid.uuid4().hex[:8]}"
    print(f"Run ID: {run_id}")

    # 1. Write mapping table (for audit)
    write_mapping_csv(out_dir / "category_mapping.csv")
    print("Mapping table written")

    # 2. Build return
    manifest = build_return(return_date, out_dir)
    print(f"Return built: {len(manifest['files'])} files")

    # 3. Cost allocation
    alloc = build_allocation()
    ok, errors = check_balance(alloc)
    if not ok:
        print("Cost allocation balance FAILED:")
        for e in errors:
            print("  ERROR:", e)
        return 1
    write_allocation_csv(alloc, out_dir / f"cost_allocation_{return_date.isoformat()}.csv")
    print("Cost allocation balanced and written")

    # 4. Validation
    passed, violations = validate_return_data(return_date, out_dir)
    if not passed:
        print("VALIDATION FAILED (blocking violations):")
        for v in violations:
            print(f"  {v['rule_id']} ({v['severity']}): {v['message'][:120]}")
        return 1
    else:
        print("Validation passed")

    # 5. Audit trail
    log_entry = log_run(run_id, return_date.isoformat(), str(out_dir))
    print(f"Run logged: {log_entry['run_id']}")

    snap_path = snapshot_outputs(str(out_dir), run_id)
    print(f"Snapshot: {snap_path}")

    if args.sign_off and args.reviewer:
        sign_off(run_id, args.reviewer, "approved", "All checks passed")
        print(f"Signed off by {args.reviewer}")

    if args.verify:
        ok = verify_deterministic(run_id, str(out_dir))
        print(f"Deterministic re-run: {'PASSED' if ok else 'FAILED'}")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())