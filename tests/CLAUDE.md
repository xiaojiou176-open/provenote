# tests CLAUDE.md

## Purpose

Use this file when the change is mainly inside `tests/` or quality-gate behavior.

## Stack

- Backend: Pytest / Hypothesis / mutmut
- Frontend: Vitest / Playwright
- Governance: `tooling/scripts/ci/check_*.sh`

## Local map

- `tests/conftest.py` - fixture and env baseline
- `tests/api/`, `tests/auditable/`, `tests/graphs/` - backend tests
- `tests/property/` - property tests
- `tests/live/` - external smoke tests
- `tests/README.md` - command reference

## Core commands
```bash
make test-backend-cov
OPEN_NOTEBOOK_SKIP_MIGRATIONS=true bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/property/ -v -m property
bash tooling/scripts/runtime/run_uv_managed.sh run mutmut run --max-children=4 && bash tooling/scripts/runtime/run_uv_managed.sh run mutmut results
```

## Test entrypoints
```bash
# frontend
cd apps/web && npm test && npm run test:coverage && cd ..

# e2e
cd apps/web && npm run test:e2e:install && npm run test:e2e -- --project=chromium && cd ..
```

## Search-before-write

```bash
rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md docs config contracts tooling services packages apps tests ops evals mutants
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'
```

Nearest-first rule: read this file first for `tests/`, then fall back to root guidance if needed.

Evidence token example: `tests/api/test_health.py:1`
command + matched result

## Notes

- Prefer assertions that fail for real regressions.
- Keep live tests explicitly opt-in.
- Update `tests/README.md` when the test command surface changes.
