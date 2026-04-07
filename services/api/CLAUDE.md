# API CLAUDE.md

## Purpose

Use this file when the change is mainly inside `services/api/`.

## Stack

- FastAPI
- Pydantic v2
- async Python
- runtime and domain logic from `packages/core/*`

## Local map

- `services/api/main.py` - app entrypoint, middleware, router registration
- `services/api/routers/` - HTTP route modules
- `services/api/*_service.py` - orchestration helpers
- `packages/core/application/models.py` - request and response schemas

## Core commands
```bash
bash tooling/scripts/runtime/run_uv_managed.sh run --env-file .env python tooling/bin/run_api.py

bash tooling/scripts/runtime/run_uv_managed.sh run ruff check services packages tooling
bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api -v
```

## Test entrypoints
```bash
make test-backend-cov

bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api -v
```

## Search-before-write

```bash
rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md docs config contracts tooling services packages apps tests ops evals mutants
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'
```

Nearest-first rule: read this file first for `services/api/`, then fall back to root guidance if needed.

Evidence token example: `services/api/routers/config.py:1`
command + matched result

## Notes

- Keep HTTP routes as adapters, not business-logic containers.
- Preserve the Gemini-only and canonical env contract.
- Update callers and docs when API wire shapes change.
