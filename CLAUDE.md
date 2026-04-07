# Root CLAUDE.md

> Internal operator guidance for this fork. Not canonical public collaboration policy; public-facing authority lives in `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `SUPPORT.md`.

Root navigation guide.

## Scope

Use this file to answer three questions quickly:

1. where to read next
2. what must never be tracked
3. which checks are required before claiming a change is safe

## Main module routes

- frontend: `apps/web/CLAUDE.md`
- api: `services/api/CLAUDE.md`
- core runtime: `packages/core/CLAUDE.md`
- tests and verification: `tests/CLAUDE.md`

## Nearest-first rule

Read order is fixed:

1. nearest `CLAUDE.md`
2. nearest `AGENTS.md`
3. root `CLAUDE.md`
4. root `AGENTS.md`
5. a targeted file under `docs/`

## Search-before-write

```bash
rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md docs config contracts tooling services packages apps tests ops evals mutants
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'
```

Keep at least one evidence token in the changed docs, for example `README.md:1`.

## Hard rules

- Keep docs English-only.
- Keep docs minimal.
- Keep runtime, agent, cache, and log directories untracked.
- Prefer repo-local docs and scripts over stale historical notes.

## Core commands

```bash
bash tooling/scripts/runtime/run_uv_managed.sh sync
cd apps/web && npm ci && cd ../..
bash tooling/scripts/ci/check_env_governance.sh
bash tooling/scripts/ci/check_secret_leaks.sh
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py
```
