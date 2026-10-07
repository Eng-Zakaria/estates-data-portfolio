#!/usr/bin/env bash
# Pre-commit hook for the P14 convention checker.
#
# Install (from the repository root):
#   pre-commit install --hook-type pre-commit --config projects/p14-iso19650-checker/examples/pre-commit.yaml
#
# Point the hook at your own convention file by editing PROJECT/CONFIG below, or override with
# environment variables:
#   ISO19650_PROJECT=projects/p09-compliance-tracker ISO19650_CONFIG=conventions/uk_national_annex.yml pre-commit run
#
# Only the files being committed are checked (staged + unstaged for tracked paths), so the hook stays fast.
# Exit code 1 blocks the commit, which is the point: the convention is enforced at the moment of creation.

set -euo pipefail

ISO19650_PROJECT="${ISO19650_PROJECT:-projects/p14-iso19650-checker}"
ISO19650_CONFIG="${ISO19650_CONFIG:-projects/p14-iso19650-checker/conventions/uk_national_annex.yml}"
PYTHON="${PYTHON:-python}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
CLI="$REPO_ROOT/$ISO19650_PROJECT/src/cli.py"
CONFIG="$REPO_ROOT/$ISO19650_CONFIG"

if [[ ! -f "$CLI" || ! -f "$CONFIG" ]]; then
  echo "iso19650: pre-commit hook not applicable here (no $CLI or $CONFIG); skipping."
  exit 0
fi

# Build the list of paths to check: staged additions/modifications/renames.
mapfile -t FILES < <(git diff --cached --name-only --diff-filter=ACMR | grep -Ev '^data/' || true)

if [[ ${#FILES[@]} -eq 0 ]]; then
  exit 0
fi

# Check the folders that contain the changed files, so folder-level rules (container state, orphans,
# series numbering) are evaluated too rather than just the individual names.
mapfile -t ROOTS < <(printf '%s\n' "${FILES[@]}" | xargs -n1 dirname | sort -u)

failed=0
for root in "${ROOTS[@]}"; do
  [[ -d "$REPO_ROOT/$root" ]] || continue
  if ! "$PYTHON" "$CLI" check "$REPO_ROOT/$root" --config "$CONFIG" --format text --quiet \
       --out "${TMPDIR:-/tmp}/iso19650-precommit" --fail-on error; then
    failed=1
  fi
done

if [[ $failed -eq 1 ]]; then
  echo ""
  echo "iso19650: convention violations found. See the report above."
  echo "  Inspect the proposed renames: $PYTHON $CLI check <folder> --config $CONFIG --suggest"
  echo "  Apply the safe ones:        $PYTHON $CLI apply  <folder> --config $CONFIG --apply"
  echo "  Undo them:                 $PYTHON $CLI rollback <folder> --log /path/rename_log.csv"
  exit 1
fi

echo "iso19650: naming convention OK (${#ROOTS[@]} folder(s), ${#FILES[@]} file(s) checked)."
