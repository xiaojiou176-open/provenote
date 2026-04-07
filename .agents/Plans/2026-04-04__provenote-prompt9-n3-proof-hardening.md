# Provenote Prompt 9 N3 Truthful Compatibility Proof-Hardening

Last updated: 2026-04-04
Owner: L1 Delivery Orchestrator
Status: CLOSED

> Promotion note:
> This artifact preserves the Prompt 9 same-turn scope and evidence.
> Current repo truth is now `HEAD == origin/main == 81faedb`, so Prompt 9 is also **merged/main truth**.
> The docs it hardened are now on `main`, which makes them public truth surfaces. That still does **not** upgrade them to release/distribution truth.

## This Turn's Goal And Scope Decision

This turn does two things in order:

1. audit Prompt 8 inherited local truth and keep its truth layers honest
2. harden the OpenCode compatibility slice into a more repo-owned proof loop

This is not a reopening of N2 implementation work.

## Concurrency Preflight

- `git status --short --branch`
  - result: `## main...origin/main`
- `git worktree list --porcelain`
  - result: one visible worktree on `main`
- `git branch -vv`
  - result: `* main 206c316 [origin/main] Merge pull request #29 from xiaojiou176-open/codex/prompt6-n2-continuity-closeout`
- `git diff --stat`
  - result: inherited Prompt 8 docs/task-board delta plus this Prompt 9 proof-hardening follow-up
- `git diff --check`
  - result: clean

Interpretation:

- no visible second local L1 write lane
- Prompt 7 remains merged/main truth
- at the time of Prompt 9, Prompt 8 remained inherited current local truth only until a later merge promoted it

## Inherited Prompt 8 Historical Local Truth Ledger

| File / surface | Status before Prompt 9 | Truth layer | Notes |
| --- | --- | --- | --- |
| `docs/integrations/opencode.md` | present | historical same-turn local truth | the core OpenCode compatibility page already existed |
| `docs/mcp.md` | updated | historical same-turn local truth | OpenCode already routed from the host guide list |
| `docs/index.md` | updated | historical same-turn local truth | OpenCode already linked from the docs entrypoint |
| `docs/faq.md` | updated | historical same-turn local truth | OpenCode already included in compatibility wording |
| `docs/project-status.md` | updated | historical same-turn local truth | OpenCode already named as a repo-backed compatibility surface |
| `docs/proof.md` | updated | historical same-turn local truth | host-specific integration pages already folded into MCP proof wording |
| `README.md` | minimal sync | historical same-turn local truth | OpenCode only appeared as a host-list consistency sync |
| `.agents/Tasks/TASK_BOARD-provenote-full-rollout.md` | updated | artifact self-description | Prompt 8 and Prompt 9 are both recorded here |
| `.agents/Plans/2026-04-03__provenote-prompt8-n3-truthful-compatibility.md` | updated | artifact self-description | Prompt 8 described the first-cut scope and evidence |

## Requirements Decomposition

- Surface Request:
  - verify the inherited Prompt 8 OpenCode/docs/task-board package
  - correct any truth-layer drift
  - land one narrow proof-hardening slice
  - sync authoritative artifacts for the next worker
- Underlying Goal:
  - keep Prompt 8 from staying as "good-looking local copy only"
  - make the OpenCode surface more inspectable and less marketing-shaped
- Success Criteria:
  - no evidence-backed local/main/public truth mixing remains in the touched copy
  - Prompt 9 adds a repo-owned proof loop or stronger evidence cross-link
  - task board and this artifact explain the new N3 state honestly
- Explicit Non-Goals:
  - no N2 reopening
  - no next-host expansion program
  - no plugin / marketplace / partnership / bundled-host claims
  - no broad front-door rewrite
- Ambiguities:
  - whether Prompt 9 should also open a next-host decision note
  - default decision: no; keep this turn on OpenCode proof-hardening only
- Key Assumptions:
  - `Provenote works with OpenCode via MCP` remains supportable through repo truth plus OpenCode official docs
  - the sharpest remaining gap is proof-loop clarity, not another new host page
- AI Execution Risk:
  - medium
  - the main risk is turning proof-hardening into host expansion or marketing polish

## Prompt 8 Truth Audit

### What held up

- Prompt 8's current-local package is real, not artifact fiction:
  - the task board, Prompt 8 artifact, and current diff all point to the same touched surfaces
  - the wording remains inside `compatibility through MCP`
- Prompt 7 is still correctly separated from Prompt 8:
  - Prompt 7 is merged/main truth
  - Prompt 8 was same-turn current local truth in the original Prompt 9 turn, and is now merged/main truth in current repo truth
- OpenCode did not take over the product center:
  - README, proof, status, and MCP pages still keep the long-context / outcome path as the main product spine

### Risks found

- The biggest residual risk was not overclaim language, but proof-loop weakness:
  - the inherited OpenCode guide was already accurate, but it still benefited from a tighter repo-owned verification loop
- Artifact self-description was stronger than the guide's self-verifiability:
  - Prompt 8 claimed a truthful first cut
  - the repo surfaces supported that claim
  - Prompt 9 narrows the gap by anchoring the OpenCode guide to `tests/test_mcp_server.py`

### Evidence-backed blocker status

- no blocker found
- no scope drift found
- residual risk before Prompt 9:
  - proof-hardening gap
  - not a truth-break, but still worth tightening before later handoff or promotion

## OpenCode Claim Boundary Recheck

| Bucket | Verdict | Why |
| --- | --- | --- |
| `Provenote works with OpenCode via MCP` | safe now | OpenCode official docs expose MCP configuration and MCP server registration, while Provenote ships `provenote-mcp` in-repo |
| OpenCode can register local and remote MCP servers | safe now | supported by OpenCode official MCP docs |
| Provenote ships a first-party stdio MCP entrypoint | safe now | supported by `pyproject.toml` and `packages/core/mcp/server.py` |
| official partnership / project affiliation | not claimed | no joint announcement or repo proof |
| bundled integration / plugin-store / marketplace listing | not claimed | no repo proof and no official OpenCode listing proof |
| generic `works with every MCP host` | still too strong | current proof remains host-specific and compatibility-scoped |

## What Actually Landed In This Turn

- hardened `docs/integrations/opencode.md` with a tighter repo-owned verification loop
- hardened `docs/mcp.md` so the global MCP page points to the same repo-owned host-proof loop
- hardened `docs/proof.md` so the OpenCode compatibility row now points to repo-owned MCP code and schema anchors in addition to the host guide
- added this Prompt 9 artifact so the next worker can resume without re-auditing Prompt 8 from scratch

## Fresh Evidence

- repo truth:
  - `git status --short --branch`
    - result: Prompt 8 inherited docs/task-board package remains live in the current worktree on top of `main...origin/main`
  - `git worktree list --porcelain`
    - result: one visible worktree on `main`
  - `git branch -vv`
    - result: `* main 206c316 [origin/main] Merge pull request #29 from xiaojiou176-open/codex/prompt6-n2-continuity-closeout`
  - `git diff --stat`
    - result: inherited Prompt 8 docs/task-board surface plus Prompt 9 proof-hardening edits are present in current local truth
  - `git diff --check`
    - result: `PASS`
- repo-backed MCP anchors rechecked:
  - `rg -n "provenote-mcp|@mcp.tool\\(name=\\\"draft\\.|@mcp.tool\\(name=\\\"research_thread\\.|@mcp.tool\\(name=\\\"auditable_run\\.|class Draft|class ResearchThread|class Auditable" pyproject.toml packages/core/mcp/server.py packages/core/mcp/schemas.py tests/test_mcp_server.py`
    - result: `provenote-mcp` entrypoint plus outcome-first MCP tool and schema anchors were all found in tracked repo files
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py -q`
    - result: `12 passed`
- OpenCode official sources rechecked:
  - `curl -L --max-time 20 -s https://opencode.ai/docs/config/ | rg -n "mcp|plugin|opencode.json"`
    - result: config docs expose `opencode.json`, `mcp`, and separate `plugin` references
  - `curl -L --max-time 20 -s https://opencode.ai/docs/mcp-servers/ | rg -n "local|remote|MCP|server"`
    - result: official MCP-server docs describe local and remote MCP server modes
  - `curl -L --max-time 20 -s https://opencode.ai/brand | rg -n "OpenCode|brand|logo|name"`
    - result: official brand page exists for descriptive naming and brand assets only
- docs verification:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`

## Reviewer Verdict

- independent blocker-only reviewer:
  - unavailable in this session because no working `spawn_agent` path was exposed
- honest interpretation:
  - no fake `APPROVE` token is claimed here
  - blocker-only self-review found no evidence-backed blocker or scope drift in the touched Prompt 9 slice
  - residual risk after this turn remains truth-layer promotion, not repo-side implementation breakage

## Authoritative Artifact Update

- updated:
  - `.agents/Tasks/TASK_BOARD-provenote-full-rollout.md`
- added:
  - `.agents/Plans/2026-04-04__provenote-prompt9-n3-proof-hardening.md`

## Current N3 State

- `task complete`
  - yes, for this Prompt 9 proof-hardening slice
- `implemented in current local truth`
  - yes
- `merged / main truth`
  - yes, now retained on `81faedb`
- `public truth`
  - yes, through tracked docs now on `main`
- `external-only aspiration`
  - still separate:
    - plugin / marketplace / bundled-host / partnership claims
    - next-host expansion beyond this narrow OpenCode hardening slice

## The Most Natural Next Cut For Prompt 10

If Prompt 10 opens, the most natural next cut is:

1. a narrow truth-promotion / handoff-readiness pass if this local package is meant to be promoted later
2. otherwise, one equally narrow host-proof decision note only if official-doc support is as strong as the OpenCode bar

Do not reopen:

- N2 continuity work
- OpenClaw expansion
- plugin / marketplace / listing language

## Whether A Real External Blocker Exists

- **No**

There is no owner-first blocker for repo-side continuation right now.

What still remains outside pure repo-side completion is unchanged:

- explicit commit / push / merge / release authorization
- domain / trademark / listing / partnership decisions

Prompt 10 + Prompt 11 later promoted the stale truth-layer wording here so the current interpretation is explicit:

- Prompt 7 = merged/main truth
- Prompt 8 = merged/main truth
- Prompt 9 = merged/main truth
- public docs in `main` = public truth surface
- release/distribution truth = still separate and unclaimed
