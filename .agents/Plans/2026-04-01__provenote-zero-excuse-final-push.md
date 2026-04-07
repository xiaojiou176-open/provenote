# Provenote Zero-Excuse Final Push

Last updated: 2026-04-01
Owner: L1 Zero-Excuse Final Push Commander
Status: ACTIVE - only remote witness and owner/external actions remain

## Final Product Truth

> Provenote is a source-grounded knowledge-work control tower: an auditable research-and-writing runtime with inspectable outputs, reusable outcome objects, first-party MCP access, and a future substrate for agent-assisted workflows.

## Primary Objects

- `source`
- `auditable run / auditable markdown`
- `research thread`
- `notebook draft`
- `verified draft snapshot`
- `bundle export`
- `first-party MCP` outcome/control surfaces

## Primary Routes

- `Source -> Auditable Run -> Notebook Draft -> Verified Result -> Handoff`
- `Search / Ask -> Research Thread -> Draft`

## Six-Layer Snapshot

| Layer | Current state |
| --- | --- |
| `repo-side truth` | complete on `main` for the last known concrete code/test blocker |
| `worktree truth` | clean |
| `committed local truth` | complete |
| `remote/git truth` | partial: `main` carries the latest known fixes, but final witness verdict still pending |
| `live/public truth` | repo description, homepage, and draft release already synced to the current authorization limit |
| `release/distribution truth` | not complete: final witness and owner publish decision still pending |

## Latest Known Promotion Facts

- `main` currently points at `14fb2ce` (`docs: refresh no-survivors release handoff`)
- previous failed `main` witness `23852996237` proved two real blockers:
  - `Runtime Policy Gates`
  - `Frontend Tests`
- the known concrete frontend failure in that old run was:
  - `src/lib/stores/navigation-store.test.ts`
- the active replacement `main` witness is the latest visible `Tests` workflow run:
  - `23857176689`
  - public workflow page now exposes commit `14fb2ce` together with the current `main` promotion chain
  - the last successful API-backed refresh before rate limiting was for earlier run `23853689691`, where all non-frontend jobs were green and only `Frontend Tests` still running
- PR `#28` is now closed and no longer the authoritative promotion path
- GitHub API rate limiting became the current live-refresh boundary after the latest polling attempts

## What Is Finished

- product positioning, public wording, and English-first docs convergence
- repo description and homepage sync
- draft release `v1.8.4` preparation
- latest concrete repo-side CI blocker repair on `main`
- clean worktree / committed local truth

## What Is Still Not Finished

- final `Frontend Tests` verdict on the latest visible `main` witness (`23857176689`)
- manual `Build and Release` witness if still required by policy
- owner publish of draft release `v1.8.4`

## Minimal Owner / External Pack

1. Refresh the latest `main` `Tests` run (`23857176689`) after GitHub API rate limit clears.
   - Success condition: final verdict is visible.
2. Run or confirm same-SHA `Build and Release`.
   - Success condition: release witness is green on the final chosen `main` SHA.
3. Review and publish draft release `v1.8.4`.
   - Success condition: release is public and aligned with the final witnessed `main` SHA.
4. Decide whether to pursue Pages / domain / listing work.
   - Success condition: the external-distribution path is explicitly accepted, deferred, or rejected.

## Restart Protocol

If another operator must continue, do not restart repo archaeology.

Start from:

1. `git status --short --branch`
2. refresh the latest `main` `Tests` run (currently `23857176689`)
3. `gh release view v1.8.4 --json tagName,name,isDraft,publishedAt,url,targetCommitish`

Then do only one thing:

- if `main` is green, move to release witness / publish
- if `main` is red, use the newest failed job log and fix only that concrete blocker
