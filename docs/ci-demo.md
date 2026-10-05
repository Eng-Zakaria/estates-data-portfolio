# CI demo: a deliberately failing PR → red, then green (P05)

> Human placeholders: branch names, PR numbers and the `docs/img/*.png`
> screenshots below are filled in when the repo is pushed to GitHub. The gate
> logic itself was verified locally on 2026-10-05 (outputs quoted verbatim).

## Failing PR (red)

Branch `demo/dq-gate-red`, PR `#[NN]`: add a temporary fixture
`platform/quality/dq_results.json` containing one `error`-severity failure,
push, watch `ci` turn red at the **DQ gate** step:

```text
DQ GATE FAILED: 1 error-severity checks failing:
  - meters.demo_fail: fail
```

Exit code `1` fails the job; merge is blocked by the required `ci` check
(see `docs/branch-protection.md`). Screenshot placeholder:
`docs/img/ci-red-dq-gate.png` (human adds).

## Fix (green)

Branch `demo/dq-gate-green`: remove the fixture (P03 not built yet, so the
gate skips explicitly), push, `ci` goes green:

```text
SKIP: platform/quality DQ results not present (P03 not built yet).
Fail-on-error gate will enforce once P03 lands.
```

Screenshot placeholder: `docs/img/ci-green.png` (human adds).

## Validation checklist (human, 2 min)

- [ ] PR with bad fixture: `ci` red, failing step = `DQ gate`.
- [ ] PR removing it: `ci` green on both matrix versions (3.11, 3.12).
- [ ] `main` branch protection lists `ci (3.11)` / `ci (3.12)` as required.
- [ ] Badges at the top of `README.md` point at this repo (replace
  `YOUR-ORG/estates-data-portfolio`).
