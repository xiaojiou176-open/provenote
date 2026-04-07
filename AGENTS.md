# AGENTS.md

> Internal operator guidance for this fork. Not canonical public collaboration policy; use `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `SUPPORT.md` for public-facing authority.

Repository-level operator guide.

## Purpose

- Route contributors and agents to the correct module entrypoint quickly.
- Keep runtime, documentation, and review rules small and stable.
- Preserve a minimal, open-source-friendly repository surface.

## Kept navigation surfaces

- Root: `AGENTS.md`, `CLAUDE.md`
- Main modules: `apps/web`, `services/api`, `packages/core`, `tests`

## Nearest-first rule

Read order is fixed:

1. nearest `CLAUDE.md`
2. nearest `AGENTS.md`
3. root `CLAUDE.md`
4. root `AGENTS.md`
5. a targeted public doc under `docs/`

## Search-before-write

Run these commands before adding rules, docs, or workflow policy:

```bash
rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md docs config contracts tooling services packages apps tests ops evals mutants
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'
```

Record the commands plus at least one evidence token such as `README.md:1` or `services/api/main.py:1`.

## Non-negotiable repo rules

- Do not track `.agents/`, `.agent/`, `.codex/`, `.claude/`, `.runtime-cache/`, log directories, or log files.
- Current tracked exceptions under `.agents/` are intentional historical/operator SSOT and must not be treated as residue:
  - `.agents/Tasks/TASK_BOARD-provenote-full-rollout.md`
  - tracked `.agents/Plans/2026-*.md` closeout and handoff artifacts already in the index
  - do not add new tracked `.agents/` files unless the repository's tracked exception set is explicitly widened
- Keep tracked docs and navigation files English-only.
- Keep the public docs surface minimal.
- Route Python bootstrap commands through `tooling/scripts/runtime/run_uv_managed.sh` or the CI container wrapper.
- When testing Git path visibility for tracked host artifacts, distinguish `tracked in the index` from `ignored by rules`; do not use `git status --untracked-files=all` as a proxy for both.

## Shared Workstation Hygiene

- Treat browser instances, browser profiles, tabs, Docker containers, and cache directories as shared workstation resources, not disposable infinite capacity.
- Treat host-process control as a hard safety boundary:
  - never add `killall`, `pkill`, or pattern-based host cleanup to worker, test, CI, or local-dev paths
  - only stop repo-owned processes through recorded positive PID files under `.runtime-cache/local/pids/`
  - if a port is occupied by an unknown PID, treat it as a blocker instead of killing first and asking questions later
  - desktop or browser cleanup must stay repo-owned and exact-match; broad host cleanup is out of scope
- Start with ownership-first machine awareness:
  - identify which browser/profile/tab/container/cache surface belongs to this repo and this task
  - treat any surface owned by another repo or another active L1 lane as off-limits unless the user explicitly authorizes intervention
- When a task needs Chrome, Chromium, Safari, Playwright, or another browser-backed surface:
  - if more than six browser instances are already active on the workstation, do not open a new one until ownership is checked and a smaller-footprint path is ruled out
  - open the minimum number of windows and tabs required
  - prefer background execution; treat detached browser/runtime launch as review-required and only acceptable inside repo-owned browser roots or directly held child handles
  - avoid stealing the current desktop focus unless foreground control is strictly required for the task
  - close every browser window or tab you created when the task is done
  - do not leave background browser processes running without a current task need
  - when this repo provides a generated browser identity tab, keep it as the human-facing anchor for that lane when practical
  - do not script Chrome private pin-tab, avatar, theme, or Dock customization as part of the normal repo bootstrap; keep those manual if desired
- Never reuse or take over browser instances, tabs, or profiles created by another repo or another L1 lane. Only use browser state you created for the current repo, or state the user explicitly assigned to this repo.
- If ownership is unclear, treat the browser or cache surface as off-limits and record the ambiguity instead of guessing.
- If a task requires a cloned or temporary browser profile, keep it isolated to the current repo/task and remove the temporary clone when finished. Do not accumulate abandoned browser-profile copies under cache roots.
- Login-state checks must stop early:
  - use at most one or two clearly-owned browser/profile attempts for the current repo
  - if those attempts show that human login or owner-owned session state is required, record an external blocker instead of opening more browser instances or profile clones
- Keep Docker/buildx/container state governed:
  - do not leave throwaway containers, builders, or large temporary caches running after the task that created them is finished
  - do not perform broad cleanup that could disrupt another active repo or another L1 lane without explicit user approval
- Host safety is hard policy:
  - do not use `killall`, `pkill -f`, `kill -9`, `xargs kill`, `osascript`, or `System Events` in tracked automation paths
  - do not signal negative/zero PIDs or broad port listeners that are not proven repo-owned
  - local runtime stop/restart flows must target repo-recorded PID files or
    repo-owned command signatures only
- Git / GitHub closeout must be equally disciplined:
  - close or delete only those branches, worktrees, and PR tails whose unique work is already merged into `main` or otherwise proven superseded
  - treat dirty worktrees with unique local changes as live continuation lanes, not automatic cleanup targets
- Current-repo Git / GitHub closeout writes are allowed only inside the user-authorized closeout scope.
- Default to read-only behavior on external accounts and platforms outside that scope. Do not publish releases, edit off-scope repository metadata, submit listings, change domain or DNS state, post externally, mutate settings, or take any other write action against the user's external accounts unless the user explicitly asked for that exact write in the current task.
- Repository-scoped Git and GitHub closeout writes require explicit task authorization and do not extend to release publication, homepage/metadata edits, domain/DNS actions, third-party listing submissions, social posting, or partnership/outreach writes.

## Host Safety Contract

- Worker-safe mode is the default for this repository.
- `pkill -f`, `pkill`, `killall`, `killpg(...)`, pattern-scoped force-kill, negative/zero PID signals, `loginwindow` / Force Quit APIs, and AppleScript or `System Events` app-control are forbidden in first-party automation paths.
- Local service lifecycle must flow through repo-owned pid files under `.runtime-cache/local/pids` and the `tooling/scripts/dev/*_local.sh` entrypoints.
- If a service cannot be mapped to a recorded pid or repo-owned port, fail closed instead of killing by name or pattern.
- Detached browser/runtime launch is review-required only and must stay inside repo-owned browser roots or repo-recorded child handles.

## Core commands

```bash
bash tooling/scripts/runtime/run_uv_managed.sh sync
cd apps/web && npm ci && cd ../..
bash tooling/scripts/ci/check_env_governance.sh
bash tooling/scripts/ci/check_secret_leaks.sh
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py
bash tooling/scripts/ci/pre_commit_lint.sh
bash tooling/scripts/ci/pre_commit_lint.sh --mode runtime
```

## Verification baseline

```bash
make test-backend-cov
cd apps/web && npm test && cd ../..
```
