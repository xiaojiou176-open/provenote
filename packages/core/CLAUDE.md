# open_notebook CLAUDE.md

## Purpose

Use this file when the change is mainly inside `packages/core/`.

## Stack

- Python + async workflows
- LangGraph / LangChain
- SurrealDB
- Pydantic

## Local map

- `packages/core/ai/` - model provisioning and key handling
- `packages/core/graphs/` - workflow orchestration
- `packages/core/domain/` - entities and query logic
- `packages/core/database/` - persistence and migrations
- `packages/core/auditable/` - auditable rendering and pipeline behavior
- `packages/core/utils/` - shared utilities and error helpers

## Core commands
```bash
make test-backend-cov

OPEN_NOTEBOOK_SKIP_MIGRATIONS=true bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/property/ -v -m property
bash tooling/scripts/runtime/run_uv_managed.sh run mutmut run --max-children=4
bash tooling/scripts/runtime/run_uv_managed.sh run mutmut results
```

## Test entrypoints
```bash
bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/graphs -v
bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/auditable -v
bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/live/test_google_live_smoke.py -v -m live
```

## Search-before-write

```bash
rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md docs config contracts tooling services packages apps tests ops evals mutants
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'
```

Nearest-first rule: read this file first for `packages/core/`, then fall back to root guidance if needed.

Evidence token example: `packages/core/settings.py:1`
command + matched result

## Notes

- Avoid leaking API or UI coupling into core runtime code.
- Keep env handling and provider policy fail-closed.
- Preserve observable, typed error paths when refactoring.
