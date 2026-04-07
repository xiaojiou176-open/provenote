# Provenote Release-Grade Closed Clean

Last updated: 2026-04-01
Owner: L1 Supreme Release Closer
Status: ACTIVE - only remote witness and owner release actions remain

## Purpose

This is the tracked release-facing handoff for the final promotion stage.

It answers one question only:

> What still remains after everything repo-side, remote-syncable, and release-preparable has been pushed to the current authorization limit, once the remaining work is compressed into remote witness or owner/external actions?

## Final Product Truth

> Provenote is a source-grounded knowledge-work control tower: an auditable research-and-writing runtime with inspectable outputs, reusable outcome objects, first-party MCP access, and a future substrate for agent-assisted workflows.

### Primary objects

- `source`
- `auditable run / auditable markdown`
- `research thread`
- `notebook draft`
- `verified draft snapshot`
- `bundle export`
- `first-party MCP` outcome/control surfaces

### Primary routes

- `Source -> Auditable Run -> Notebook Draft -> Verified Result -> Handoff`
- `Search / Ask -> Research Thread -> Draft`

## Six-Layer Truth

| Layer | Current state |
| --- | --- |
| `repo-side truth` | complete on `main` for the latest known concrete code/test blocker |
| `worktree truth` | clean |
| `committed local truth` | complete |
| `remote/git truth` | partial: `main` carries the latest known fixes, but the final witness verdict is still pending |
| `live/public truth` | complete to the current authorization limit for repo metadata and draft-release preparation |
| `release/distribution truth` | partially complete: draft release prepared, publication and final release witness still pending |

## Current Promotion Truth

- `main` currently points at `14fb2ce` (`docs: refresh no-survivors release handoff`)
- old failed `main` witness: `23852996237`
  - `Runtime Policy Gates`: failed
  - `Frontend Tests`: failed
  - concrete frontend failure: `src/lib/stores/navigation-store.test.ts` stale fallback expectations
- active replacement `main` witness:
  - latest visible public run id: `23857176689`
  - workflow page now exposes commit `14fb2ce` together with the current `main` promotion chain
  - last successful API-backed refresh before rate limiting was for earlier run `23853689691`, where all non-frontend jobs had already completed successfully and only `Frontend Tests` remained in progress
- stale PR lane:
  - PR `#28` is now closed as superseded-by-main
  - `codex/release-grade-frontend-witness` is no longer the authoritative promotion path
- GitHub API rate limiting is now the current live-refresh boundary for further status checks

## Release-Facing Convergence Summary

### Already complete

- repo-side actionable work: `0`
- worktree clean
- local commits completed
- `main` pushed to `origin/main`
- repo description synchronized
- homepage synchronized
- release-ready changelog / version bump synchronized
- draft release `Provenote v1.8.4` created on `main`

### Still not complete

- final `Frontend Tests` verdict on the latest visible `main` witness (`23857176689`)
- publishing the prepared draft release
- satisfying or confirming the same-SHA manual `Build and Release` witness required by the release workflow
- any external domain / naming / trademark / listing work

## Release Draft Truth

| Field | Current value |
| --- | --- |
| Draft release name | `Provenote v1.8.4` |
| Tag | `v1.8.4` |
| State | `Draft` |
| Target | `main` |
| Published | `No` |
| Release URL | `https://github.com/xiaojiou176-open/provenote/releases/tag/untagged-63fefa9980bf6bc708d7` |

Interpretation:

- the release-facing copy is prepared
- the version semantics are prepared
- publication remains intentionally owner-reviewed because the latest release witness has not closed

## Fresh Evidence

- `git status --short --branch`
  - result: `## main...origin/main`
- `git log --oneline --decorate -n 5`
  - result includes:
    - `14fb2ce (HEAD -> main, origin/main) docs: refresh no-survivors release handoff`
    - `b436ace fix(ci): constrain coverage batch worker memory`
    - `d6ae960 docs: track final release handoff artifacts`
    - `f974089 docs: refresh release witness tracker`
- `gh repo view --json description,homepageUrl,defaultBranchRef,url`
  - result:
    - description: `Source-grounded knowledge-work control tower for auditable research, notebook drafts, and MCP-assisted workflows.`
    - homepage: `https://github.com/xiaojiou176-open/provenote/blob/main/docs/index.md`
- `gh release view v1.8.4 --json tagName,name,isDraft,isPrerelease,publishedAt,body,url,targetCommitish`
  - last successful result before API rate limiting:
    - `tagName=v1.8.4`
    - `name=Provenote v1.8.4`
    - `isDraft=true`
    - `targetCommitish=main`
- fresh local verification:
  - `cd apps/web && npm run lint` -> `0`
  - `cd apps/web && npx vitest run src/lib/stores/navigation-store.test.ts --maxWorkers=1` -> `0`
  - `cd apps/web && FRONTEND_COVERAGE_BATCH_MODE=1 ... 'src/lib/stores/navigation-store.test.ts'` -> `0`
  - `cd apps/web && npx vitest run src/components/source/AuditableClaimReviewWorkspace.test.tsx src/lib/locales/index.test.ts src/lib/hooks/use-navigation.test.ts src/lib/hooks/use-research-threads.test.ts --maxWorkers=1` -> `0`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py` -> `0`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_openapi_contract_drift.py` -> `0`

## Remaining Owner Decision Pack

### 1. Resolve active remote CI witness

- What is missing:
  - current remote `Tests` witness is not green yet
- Why repo-side cannot continue:
  - code and docs are already promoted to `main`; release-grade truth now depends on remote workflow completion
- What the owner must do:
  - refresh the latest `main` witness and confirm the final verdict

### 2. Publish the prepared draft release

- What is missing:
  - the draft release is not published yet
- Why repo-side cannot continue:
  - publication is a product/release decision, not a repository implementation gap
- What the owner must do:
  - review and publish `Provenote v1.8.4`

### 3. Same-SHA manual release witness

- What is missing:
  - the published release workflow expects a successful same-SHA manual `Build and Release` run
- Why repo-side cannot continue:
  - this is release-lane execution policy, not a code or docs defect
- What the owner must do:
  - run or verify the manual `Build and Release` workflow on the final chosen `main` SHA before publishing if required

### 4. External brand/distribution actions

- What is missing:
  - domain / redirect
  - trademark / naming clearance
  - official marketplace / directory listing
- Why repo-side cannot continue:
  - these are external resources or external platform actions
- What the owner must do:
  - decide whether to pursue them, then execute outside pure repo-side work

## Final Honest Verdict

- `repo-side complete`: **yes**
- `worktree clean`: **yes**
- `committed local truth`: **yes**
- `remote/git complete`: **not fully**
- `live/public sync complete`: **yes to the current authorization limit**
- `release-grade complete`: **not fully**

The practical truth is:

> Provenote no longer has broad repo-side unfinished work.
> It is now waiting on remote CI witness completion, promotion choice, and then release publication.

## Next Lowest-Friction Restart

1. Read this file
2. Read `.agents/Plans/2026-04-01__provenote-zero-excuse-final-push.md`
3. Read `.agents/Tasks/TASK_BOARD-provenote-full-rollout.md`
4. Check:
   - `git status --short --branch`
   - the latest `main` `Tests` run page (currently `23857176689`)
   - `gh release view v1.8.4 --json tagName,name,isDraft,publishedAt,url,targetCommitish`
5. Then do only one thing:
   - if `main` is green, move to release witness / publish
   - if `main` is red, use the newest failed job log and fix only that concrete blocker
