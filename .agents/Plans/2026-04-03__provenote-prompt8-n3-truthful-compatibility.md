# Provenote Prompt 8 N3 Truthful Compatibility First Cut

Last updated: 2026-04-03
Owner: L1 Delivery Orchestrator
Status: CLOSED

> Promotion note:
> This artifact preserves the Prompt 8 same-turn scope and evidence.
> Current repo truth is now `HEAD == origin/main == 81faedb`, so Prompt 8 is no longer `current local truth only`.
> It is **merged/main truth**. Public docs in `main` now reflect that merged truth, but release/distribution truth still remains separate.

## This Turn's Goal And Scope Decision

This turn does two things in order:

1. promote Prompt 7 from stale local-only artifact wording into merged/main truth
2. open a truthful N3 compatibility surface through a repo-backed OpenCode page

This is not a reopening of N2 implementation work.

## Concurrency Preflight

- `git status --short --branch`
  - result: `## main...origin/main`
- `git worktree list --porcelain`
  - result: one visible worktree on `main`
- `git branch -vv`
  - result: `* main 206c316 [origin/main] Merge pull request #29 from xiaojiou176-open/codex/prompt6-n2-continuity-closeout`
- `git log --oneline --decorate -n 12`
  - result: `206c316` is the merge commit that carries the Prompt 1-7 branch into `main`

Interpretation:

- no visible second local L1 write lane
- Prompt 7 is no longer branch-local truth
- current write scope is a single-L1 continuation on top of clean `main`

## Requirements Decomposition

- Surface Request:
  - promote Prompt 7 / N2 into authoritative merged/main truth
  - add a repo-backed OpenCode compatibility-through-MCP page
  - wire that page into the existing docs surface without inflating the public claim
- Underlying Goal:
  - keep Provenote centered on long messy context -> structured knowledge objects -> reusable outcomes
  - make the next N3 move honest, inspectable, and narrow
- Success Criteria:
  - Prompt 7 is explicitly recorded as merged/main truth
  - N2 is explicitly closed at merged/main truth for repo-side actionable scope
  - `docs/integrations/opencode.md` exists with a clear non-claim boundary
  - `docs/mcp.md`, `docs/index.md`, `docs/faq.md`, and `docs/project-status.md` are minimally wired
  - docs checks pass with fresh evidence
- Explicit Non-Goals:
  - no direct `insight -> draft`
  - no OpenClaw surface
  - no official-partnership, plugin, marketplace, or listing claim
  - no broad README/front-door rewrite in this turn
- Ambiguities:
  - whether OpenCode official materials support `works via MCP` directly, or only a weaker host-target phrasing
  - whether `README.md` needed only a minimal consistency sync or was safer left untouched
- Key Assumptions:
  - PR #29 already carried Prompt 1-7 into `main`
  - OpenCode official docs are sufficient to support a narrow `via MCP` compatibility claim
  - if README/proof are touched at all, the change should stay limited to consistency sync rather than a broader front-door rewrite
- AI Execution Risk:
  - medium
  - the main risk is overclaim drift, not implementation complexity

## Prompt 7 Truth Promotion Ledger

| Layer | Prompt 7 status now | Notes |
| --- | --- | --- |
| `task complete` | yes | Prompt 7 finished its intended N2 convergence slice |
| `implemented in current local truth` | yes | true in the original Prompt 7 turn and remains true |
| `merged / main truth` | yes | PR #29 landed and `main` is aligned to `origin/main` at `206c316` |
| `public truth` | yes, through current main docs | Prompt 8's touched public docs now live on `main`, while release/distribution truth still stays separate |
| `external-only aspiration` | still separate | plugin/marketplace/listing/official-partnership claims remain outside repo-side done scope |

Additional notes:

- reviewer timeout from the original Prompt 7 turn is preserved as historical process truth
- reviewer timeout is **not** treated as a repo-side N2 blocker now that Prompt 7 is already merged
- direct `insight -> draft` remains intentionally unclaimed

## OpenCode Claim Boundary Matrix

| Bucket | Allowed now | Why |
| --- | --- | --- |
| Safe claim | `Provenote works with OpenCode via MCP` | OpenCode official docs expose MCP server configuration and Provenote ships a first-party MCP entrypoint |
| Safe supporting detail | OpenCode can register local and remote MCP servers; Provenote provides `provenote-mcp` over stdio | backed by official OpenCode docs plus repo code/docs |
| Non-claim bucket | official partnership, bundled OpenCode integration, marketplace listing, plugin-store presence | no repo proof and no official joint announcement |
| Deferred / proof gap | `works with every MCP host`, OpenClaw support, hosted/team/autopilot expansion | evidence is either host-unspecific or entirely absent |

## What Actually Landed In This Turn

- added `docs/integrations/opencode.md`
- updated `docs/mcp.md` to include the new host guide
- updated `docs/index.md` to route OpenCode from the docs entrypoint
- updated `docs/faq.md` to include OpenCode in the compatibility list
- updated `docs/project-status.md` to record the new repo-backed compatibility surface and remove stale candidate-branch wording
- updated `README.md` and `docs/proof.md` with the smallest consistency sync needed so the new OpenCode surface is not hidden behind stale host lists
- updated authoritative planning artifacts so Prompt 7 is no longer treated as local-only truth

## Fresh Evidence

- repo truth:
  - `git status --short --branch`
    - result: `## main...origin/main`
  - `git worktree list --porcelain`
    - result: one visible worktree on `main`
  - `git branch -vv`
    - result: `* main 206c316 [origin/main] Merge pull request #29 from xiaojiou176-open/codex/prompt6-n2-continuity-closeout`
- official OpenCode docs checked in this turn:
  - `https://opencode.ai/docs/config/`
    - result: documents the `mcp` config section
  - `https://opencode.ai/docs/mcp-servers/`
    - result: documents adding local and remote MCP tools
  - `https://opencode.ai/brand`
    - result: public brand page exists for descriptive product naming
- docs verification:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`

## Reviewer Verdict

- blocker-only reviewer:
  - `APPROVE`
- evidence-backed blocker status:
  - no blocker found in the current docs/artifact diff
- non-blocking residual risk:
  - release/distribution truth remains separate from merged/main/public-doc truth

## Authoritative Artifact Update

- updated:
  - `.agents/Tasks/TASK_BOARD-provenote-full-rollout.md`
  - `.agents/Plans/2026-04-02__provenote-vision-gap-master-plan.md`
  - `.agents/Plans/2026-04-03__provenote-prompt7-n2-final-convergence.md`
- added:
  - `.agents/Plans/2026-04-03__provenote-prompt8-n3-truthful-compatibility.md`

## Current N2 / N3 Layering

- `N2`
  - closed at merged/main truth for repo-side actionable continuity scope
  - not reopened in this turn
- `N3`
  - now opened through a narrow truthful compatibility slice
  - the Prompt 8 OpenCode page, docs wiring, and minimal front-door consistency sync are now **implemented at merged/main truth**
- `public truth`
  - compatibility wording now lives in tracked docs on `main`
  - broader release/distribution/public-promotion claims remain out of scope

## The Most Natural Next Cut For Prompt 9

If Prompt 9 opens, the most natural next cut is:

- a narrow proof-hardening or next-host compatibility slice that preserves the same truthful boundary

Most likely options:

1. strengthen the OpenCode proof surface with a tiny repo-owned setup/proof note if needed
2. open the next host-specific compatibility page only if the same official-doc standard is met
3. harden MCP/public-proof cross-linking without touching plugin/marketplace/OpenClaw scope

## Whether A Real External Blocker Exists

- **No**

Current remaining limits are not owner-first blockers:

- docs and artifact work can continue repo-side
- reviewer timeout, if it happens again, is not an owner blocker
- plugin/listing/partnership claims remain deferred by boundary, not blocked by missing owner action

## Prompt 9 Inheritance Note

Prompt 9 re-audited this artifact against the live inherited diff and kept the main interpretation intact:

- Prompt 7 remains `merged/main truth`
- this Prompt 8 compatibility slice is now `merged/main truth`
- no evidence-backed claim-boundary blocker was found
- the strongest follow-up was not another host expansion page, but a narrower proof-hardening loop that makes the OpenCode surface easier to self-verify

Prompt 9 therefore treated this artifact as a valid inheritance source, not as stale self-reporting that needed replacement.

Prompt 10 + Prompt 11 later promoted this artifact's own truth-layer wording so the current interpretation is now explicit:

- Prompt 7 = merged/main truth
- Prompt 8 = merged/main truth
- public docs in `main` = public truth surface
- release/distribution truth = still separate and unclaimed
