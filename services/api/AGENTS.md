# API AGENTS.md

## Purpose

- Maintain the FastAPI HTTP layer in `services/api/`.
- Keep route contracts thin and delegate core behavior to `packages/core/`.

## Stack
- Python 3.11+
- FastAPI + Pydantic
- async service calls
- runtime and domain logic from `packages/core/*`

## Local map

- `services/api/main.py` - app entrypoint, middleware, router registration
- `services/api/routers/` - HTTP route modules
- `services/api/*_service.py` - orchestration helpers
- `packages/core/application/models.py` - request and response schemas

## Core commands
```bash
bash tooling/scripts/runtime/run_uv_managed.sh run --env-file .env python tooling/bin/run_api.py
bash tooling/scripts/runtime/run_uv_managed.sh run python -m mypy .
bash tooling/scripts/runtime/run_uv_managed.sh run ruff check .
```

## Test entrypoints
```bash
bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ -v
bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api -v
```

## Search-before-write

```bash
rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md docs config contracts tooling services packages apps tests ops evals mutants
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'
```

Nearest-first rule: read this file first for `services/api/`, then fall back to root guidance if needed.

Evidence token example: `services/api/main.py:1`
command + matched result

## Notes

- Keep routes thin.
- Update API docs and frontend callers when wire contracts change.
- Keep the Gemini-only runtime contract intact.
