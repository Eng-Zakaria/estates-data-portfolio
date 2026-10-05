# Branch protection + repo settings (human checklist, P05)

GitHub → Settings. Agent cannot apply these; the human must.

## Ruleset for `main` (Settings → Rules → Rulesets → New branch ruleset)

- Name: `main-protection`; enforcement: Active; target: `main`.
- ✅ Require a pull request before merging (min 1 approval; dismiss stale
  approvals; require CODEOWNERS review).
- ✅ Require status checks to pass: select `ci (3.11)` and `ci (3.12)`
  (exact names appear after the first `ci.yml` run).
- ✅ Require conversation resolution; block force pushes; block deletions.

## Pages (Settings → Pages)

- Source: GitHub Actions (used by `docs.yml`).

## Secrets

- No secrets required: CI uses only `GITHUB_TOKEN`. Never commit `.env`
  (see `.env.example`); demo passwords are labelled `DEMO ONLY`.

## CODEOWNERS

- Replace `@YOUR-ORG/estates-owners` in `.github/CODEOWNERS` with the real
  team/user, else review requests never fire.
