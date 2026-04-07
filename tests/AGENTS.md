# tests AGENTS.md

## Purpose

- Maintain the test entrypoints and quality gates for the repository.
- Keep fake-green tests and stale governance assumptions out of the tree.

## Stack
- Pytest + Hypothesis + mutmut
- Vitest + Playwright
- CI shell guards in `tooling/scripts/ci/*`

## Local map

- `tests/api/` - API tests
- `tests/auditable/` - auditable pipeline tests
- `tests/graphs/` - graph workflow tests
- `tests/property/` - property tests
- `tests/live/` - real external integration smoke tests
- `tests/README.md` - canonical test command reference

## Core commands
```bash
make test-backend-cov
OPEN_NOTEBOOK_SKIP_MIGRATIONS=true bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/property/ -v -m property
bash tooling/scripts/ci/check_test_smells.sh
bash tooling/scripts/ci/check_env_governance.sh
```

## Test entrypoints
```bash
make quality-fast
make quality-full
cd apps/web && npm run test:e2e -- --project=chromium && cd ..
```

## Search-before-write

```bash
rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md docs config contracts tooling services packages apps tests ops evals mutants
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'
```

Nearest-first rule: read this file first for `tests/`, then fall back to root guidance if needed.

Evidence token example: `tests/README.md:1`
command + matched result

## Notes

- Add assertions that can actually fail.
- Keep live tests opt-in and clearly marked.
- Update `tests/README.md` when the test command surface changes.
