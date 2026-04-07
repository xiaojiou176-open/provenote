# Required Checks Snapshot

Snapshot Date: 2026-03-28

This file is a repo snapshot/expectation only. It documents the required-check shape that repo code, workflows, and contract tests expect, but it is not live proof that remote GitHub settings already match.

Specific remote repo slugs are intentionally generalized in this public artifact. Maintainers should re-run the remote/manual review against the current `origin` repository rather than assuming an older slug remains the public-facing truth.

## Truth Boundary For This Snapshot

- `repo-side truth`: workflow names, job ids, same-SHA witness binding, and the expected trusted/public lane split documented in this file
- `remote/manual truth`: whether GitHub branch protection, rulesets, and required checks currently match the expected shape on the live repository

This file may describe repo-side expectations in detail, but it must not be read as remote enforcement proof unless a remote review record is present and current.

## Remote Review Status Contract

Use one of these statuses when refreshing this snapshot:

- `verified`
- `pending-remote-proof`
- `blocked-by-platform`
- `blocked-by-token-scope`
- `re-review-required`

Do not mark required-check enforcement as `verified` unless the review record captures the minimum fields below.

## Minimum Remote Proof Record

Any remote recheck for this snapshot must record at least:

- `review_status`
- `review_surface`
- `reviewer`
- `review_date`
- `scope_reviewed`
- `evidence_pointer`
- `exceptions_or_limits`
- `next_recheck_trigger`

## Maintainer-Only Trusted Lanes

These lanes depend on repo-owned secrets, self-hosted execution, or same-SHA witness binding. They are the trusted maintainer path, not the public contributor path.

| Check or Witness | Source | Why It Is Trusted |
| --- | --- | --- |
| `UIUX Gemini Gate` | `.github/workflows/uiux-gemini-gate.yml` | Manual-only trusted witness lane for secret-backed UIUX evidence; this is a manual-only trusted witness lane and deterministic fallback is degraded and non-authoritative |
| `Performance Benchmarks` | `.github/workflows/test.yml` job `performance-benchmarks` | Manual-only maintainer lane because it depends on host Docker privilege and benchmark infrastructure that are too noisy for the default required push path |
| `Runner Health` | `.github/workflows/runner-health.yml` job `runner-bootstrap` | Operational self-hosted recovery lane; keeps runner repair outside the default required correctness path |
| `Required Green Gate` (job id `required-green-gate`) | `.github/workflows/test.yml` | Aggregates the deterministic repo-owned checks that stay stable on every push; heavier UIUX/perf/E2E evidence remains outside the blocking aggregate |
| Release same-SHA witness | `.github/workflows/build-and-release.yml` job `verify-required-green-gate` | Verifies the trusted `Required Green Gate` check on the release SHA before publishing images |

## Public Contributor Lanes

These lanes are intentionally hosted-safe and do not claim the same authority as the maintainer-only trusted lanes.

| Lane | Source | Boundary |
| --- | --- | --- |
| `external-pr-security-scan` | `.github/workflows/test.yml` | Runs for external pull requests without repo secrets |
| `external-pr-fast-gate` | `.github/workflows/test.yml` | Public contributor fast path; provides hosted-safe signal only |

## Expected Required Checks

The repo expects remote GitHub required checks to include at least the maintainer-trusted aggregate gate:

- `Required Green Gate` (job id `required-green-gate`)

The repo also expects the workflow topology behind that gate to keep these boundaries intact:

- `external-pr-security-scan`
- `external-pr-fast-gate`
- `UIUX Gemini Gate` remains repo-owned evidence, but it is reviewed outside the default required aggregate because it depends on heavier secret-backed execution.
- `Performance Benchmarks` remains maintainer-owned evidence, but it is reviewed outside the default required aggregate because it depends on host Docker privilege and benchmark-only infrastructure.

## Latest Recorded Remote Review Summary

- Review Status: `verified`
- Review Date: 2026-04-06 03:10 PDT
- Reviewer Surface: GitHub CLI authenticated as the active maintainer account for the reviewed `origin` repository
- Latest recorded evidence:
  - the reviewed origin repository remained reachable, public, admin-visible, and defaulted to `main`
  - `gh api repos/xiaojiou176/provenote/branches/main/protection` succeeded and showed `required_status_checks.strict=true` with `contexts=["Required Green Gate"]`
  - the latest observed `workflow_dispatch` run of `Tests` on the current `main` SHA completed with overall run `failure`, but the corresponding `Required Green Gate` job on that same SHA completed `success`
  - the required protected mainline context on the live repository still points at `Required Green Gate`
  - `gh api repos/xiaojiou176/provenote/releases/tags/v1.8.1` currently returns `404 Not Found`, so predecessor-repo release-tag evidence must not be reused as current truth

Interpretation:

- repo existence, default branch, workflow naming, branch-protection wiring, and same-SHA trusted lane behavior remain live and reviewable on the post-cutover repository
- the maintainer-trusted aggregate check is still the required protected mainline gate
- release-tag evidence must be re-established on the new repository rather than inferred from the deleted predecessor repository

## Verification Boundary

- In-repo code can verify workflow names, job bindings, same-SHA release witness logic, and the documented public/trusted lane split.
- In-repo code cannot prove remote GitHub required-check settings by itself.
- Remote enforcement must be verified manually or with external GitHub admin/API access.
- Use `tooling/scripts/ci/check_public_ci_boundary.py` for the repo-owned contract, and treat this snapshot as expectation plus review aid rather than live remote truth.

## Distribution Note

- This snapshot does not prove registry ownership or public package namespace control.
- Review `.github/repo-settings/registry-ownership.snapshot.md` before claiming the current fork controls a public distribution target.

## Claim Discipline

- Repo docs may describe the expected workflow topology and trusted/public CI split.
- Repo docs must not describe branch protection, rulesets, or required-check enforcement as live-verified unless a fresh remote review record says `verified`.
- A red or cancelled trusted lane remains a real remote blocker even when repo-side contract tests pass locally.
- A visible release page or tag must not be described as proof that the latest `release` event workflow is healthy unless that specific wave is freshly verified.
