# open_notebook AGENTS.md

## Purpose

- Maintain the core runtime, graph workflows, data access, and shared utilities.
- Provide stable behavior for the API and worker layers.

## Stack
- Python 3.11+
- LangGraph / LangChain
- async SurrealDB access
- Pydantic and internal domain models

## Local map

- `packages/core/ai/` - model provisioning and key handling
- `packages/core/graphs/` - chat, source, ask, and transformation workflows
- `packages/core/domain/` - entities and query logic
- `packages/core/database/` - database access and migrations
- `packages/core/utils/` - shared utilities and error helpers

## Core commands
```bash
bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/graphs tests/test_domain.py -v
make test-backend-cov
```

## Test entrypoints
```bash
bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/graphs -v
bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/property -v -m property
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

- Keep the Gemini-only runtime contract intact.
- Treat graph, settings, and schema changes as cross-surface changes.
- Preserve observable error handling when refactoring core flows.
