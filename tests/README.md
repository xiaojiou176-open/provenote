# Tests README

Canonical test entry for this repository. Run commands from repo root unless noted.

## Remote standard

- `origin` = current write target
- `upstream` = official repo (`https://github.com/lfnovo/open-notebook.git`, sync source) resolved on demand by upstream governance scripts; a persistent local `upstream` remote is optional, not required

```bash
git remote -v
```

## Test layout

Backend (`pytest`):

- `tests/test_*.py` - backend domain/service/router tests
- `tests/api/*.py` - API-layer focused tests
- `tests/integration/*.py` - app-wired integration tests (middleware + router + error contract)
- `tests/auditable/*.py` - auditable pipeline tests
- `tests/conftest.py` - shared pytest bootstrap and env loading policy

Frontend unit/component (`vitest`):

- `apps/web/src/**/*.test.ts`
- `apps/web/src/**/*.test.tsx`

Frontend E2E (`playwright`):

- `apps/web/e2e/*.spec.ts`

## Environment rules

- `tests/conftest.py` ensures `OPEN_NOTEBOOK_PASSWORD` is non-empty for test runs.
- Shared fixture `api_client` injects an `Authorization` header derived from `OPEN_NOTEBOOK_PASSWORD` by default.
- For local unauthenticated assertions, use `api_client_no_auth` fixture.
- Test env loading prefers `.env.test` if present.
- Root `.env` is not loaded by default.

## Core commands

Backend:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ -v
```

Backend (CI-equivalent without live integration tests):

```bash
make test-backend-cov
```

Backend property-based tests (Hypothesis):

```bash
OPEN_NOTEBOOK_SKIP_MIGRATIONS=true bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/property/ -v -m property
```

Backend live Gemini smoke (real API key required):

```bash
RUN_LIVE_TESTS=1 GEMINI_API_KEY=your_key bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/live/test_google_live_smoke.py -v -m live
# Optional model override:
# LIVE_GEMINI_SMOKE_MODEL=gemini-3-flash-preview
# Optional heartbeat interval in seconds (min 5):
# LIVE_HEARTBEAT_SECONDS=15
```

Live key contract for the Gemini smoke test:
- single runtime key variable: `GEMINI_API_KEY`
- no loading from `.env`
- no loading from shell profiles (`~/.zshrc`/`~/.zprofile`)
- when `RUN_LIVE_TESTS=1`, missing/placeholder key is treated as failure (not skip)
- live metadata markers are mandatory in live test files:
  - `live-cleanup: read-only-no-op` for read-only tests
  - `live-cleanup: required` for write/mutating tests (must include teardown)
  - `live-idempotency: ...` to document retry safety/idempotency strategy

Backend mutation tests (critical-module scope):

```bash
bash tooling/scripts/runtime/run_uv_managed.sh run mutmut run --max-children=4
bash tooling/scripts/runtime/run_uv_managed.sh run mutmut results
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_mutation_guard.py --stats-path mutants/mutmut-cicd-stats.json
```

Latest local audit snapshot (2026-03-01): `killed=421`, `survived=60`, `total=481`,
`score=87.53%`, `no_tests=0`, `skipped=0`, `suspicious=0`, `timeout=0`.
Mutation guard now supports anti-regression checks against a baseline stats file:
- `--baseline-stats <path>` enables baseline comparison.
- `--max-survived-regression` defaults to `0` (no survived increase allowed).
- `--max-score-regression` defaults to `0` (no score drop allowed).
- `--report-json <path>` exports an auditable JSON report (current thresholds, baseline delta, module/function survivor hotspots).

Frontend unit/component:

```bash
cd apps/web
npm test
```

Frontend E2E (Chromium):

```bash
cd apps/web
npm run test:e2e:install
npm run test:e2e -- --project=chromium
```

Frontend E2E real-backend smoke:

```bash
docker run -d --name surreal-e2e -p 38080:8000 surrealdb/surrealdb:v2.3.10 start --log warn --user root --pass root memory
cd apps/web
OPEN_NOTEBOOK_SKIP_MIGRATIONS=false SURREAL_EXTERNAL_URL=ws://127.0.0.1:38080/rpc SURREAL_USER=root SURREAL_PASSWORD=root SURREAL_NAMESPACE=open_notebook SURREAL_DATABASE=open_notebook npm run test:e2e:real-smoke -- --workers=1
cd ..
docker rm -f surreal-e2e
```

Frontend E2E external website live smoke:

```bash
cd apps/web
RUN_LIVE_TESTS=1 LIVE_EXTERNAL_WEB_ENABLED=1 LIVE_EXTERNAL_SITE_URL=https://example.com/ npm run test:e2e:external-live -- --project=chromium
# Optional heartbeat interval in seconds (min 5):
# LIVE_HEARTBEAT_SECONDS=15
```

Live cleanup/idempotency policy:
- current external live smoke is read-only and declares `live-cleanup: read-only-no-op`.
- any future mutating live case must switch to `live-cleanup: required`, add explicit teardown, and keep `live-idempotency: ...` metadata.

## Core gates

```bash
# provider-credential governance
bash tooling/scripts/ci/check_env_governance.sh

# test-smell governance (.only/.skip/fake assertions)
bash tooling/scripts/ci/check_test_smells.sh

# static live-policy audit (no live execution)
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_live_test_static_audit.py

# backend lint hard gate
bash tooling/scripts/runtime/run_uv_managed.sh run ruff check .
bash tooling/scripts/runtime/run_uv_managed.sh run python -m mypy .

# staged-commit lint/type gate (staged files only)
bash tooling/scripts/ci/pre_commit_lint.sh

# runtime critical lint/type gate (pre-push/unified gate scope)
bash tooling/scripts/ci/pre_commit_lint.sh --mode runtime

# property-based gate (Hypothesis)
# CI: runs in dedicated `property-tests` job (.github/workflows/test.yml)
OPEN_NOTEBOOK_SKIP_MIGRATIONS=true bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/property/ -v -m property

# backend coverage hard gate (global line >=95, branch coverage enabled)
make test-backend-cov
# default aligns with unified gate core stage:
# - marker scope: not property and not live
# - performance benchmarks excluded unless explicitly enabled
# opt in performance benchmarks only when you intentionally want benchmark preflight in this gate:
# RUN_PERFORMANCE_BENCHMARKS=1 make test-backend-cov
# if benchmarks are enabled on a host without required infra, explicit skip policy is required:
# PERF_BENCHMARK_ALLOW_ENV_SKIP=1 RUN_PERFORMANCE_BENCHMARKS=1 make test-backend-cov

# backend mutation gate (critical-module scope: packages/core/utils/chunking.py + packages/core/utils/text_utils.py with tests/test_chunking.py + tests/test_text_utils_mutation.py)
bash tooling/scripts/runtime/run_uv_managed.sh run mutmut run --max-children=4
bash tooling/scripts/runtime/run_uv_managed.sh run mutmut results
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_mutation_guard.py --stats-path mutants/mutmut-cicd-stats.json

# apps/web unit/component tests
cd apps/web && npm test && cd ..

# apps/web lint hard gate
cd apps/web && npm run lint && cd ..

# GitHub Actions workflow policy + syntax gate
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_workflow_policy.py
bash tooling/scripts/runtime/run_uv_managed.sh run pre-commit run actionlint --all-files

# GitHub dependency review gate (PR workflow)
# repo workflow: .github/workflows/dependency-review.yml

# GitHub Actions security lint gate for the currently governed workflow subset
# repo workflow: .github/workflows/zizmor.yml
uv tool run --from zizmor==1.23.1 zizmor \
  .github/actions/setup-uv-python/action.yml \
  .github/workflows/dependency-review.yml \
  .github/workflows/trivy.yml \
  .github/workflows/trufflehog.yml \
  .github/workflows/zizmor.yml

# Trivy filesystem/dependency scan
mkdir -p .runtime-cache/local/bin
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/v0.69.3/contrib/install.sh \
  | sh -s -- -b .runtime-cache/local/bin v0.69.3
./.runtime-cache/local/bin/trivy fs --exit-code 1 --severity HIGH,CRITICAL --scanners vuln,secret,misconfig .

# TruffleHog git-history scan
mkdir -p .runtime-cache/local/bin
curl -sfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/v3.94.2/scripts/install.sh \
  | sh -s -- -b .runtime-cache/local/bin
./.runtime-cache/local/bin/trufflehog git file://. --results=verified,unknown --fail --no-update

# apps/web e2e tests
cd apps/web && npm run test:e2e:install && npm run test:e2e -- --project=chromium && cd ..

# apps/web Playwright action-matrix contract
cd apps/web && npm run test:e2e:action-matrix:check && cd ..
# strict runtime-evidence contract for real-backend actions (role/runtime layers)
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_action_matrix.py --runtime-evidence .runtime-cache/runs/current/evidence/apps-web/action-runtime-evidence.json --require-runtime-evidence

# apps/web real-backend e2e smoke (auto-bootstraps pinned machine-cache surreal first; Docker remains the manual fallback)
docker run -d --name surreal-e2e -p 38080:8000 surrealdb/surrealdb:v2.3.10 start --log warn --user root --pass root memory
cd apps/web && OPEN_NOTEBOOK_SKIP_MIGRATIONS=false SURREAL_EXTERNAL_URL=ws://127.0.0.1:38080/rpc SURREAL_USER=root SURREAL_PASSWORD=root SURREAL_NAMESPACE=open_notebook SURREAL_DATABASE=open_notebook npm run test:e2e:real-smoke -- --workers=1 && cd ..
docker rm -f surreal-e2e

# live external website e2e smoke
cd apps/web && RUN_LIVE_TESTS=1 LIVE_EXTERNAL_WEB_ENABLED=1 LIVE_EXTERNAL_SITE_URL=https://example.com/ npm run test:e2e:external-live -- --project=chromium && cd ..

# apps/web coverage gate (blocking policy: global line >=95 via threshold reconciler)
cd apps/web && npm run test:coverage && cd ..

# UIUX Gemini blocking gate (trusted manifest/evaluator binding)
python3 tooling/scripts/ci/run_uiux_gemini_gate.py \
  --manifest .runtime-cache/runs/current/evidence/uiux-gemini/manifest.json \
  --evaluator .runtime-cache/runs/current/evidence/uiux-gemini/evaluator.json \
  --playwright-report-dir .runtime-cache/test/playwright/report \
  --playwright-results-dir .runtime-cache/test/playwright/results \
  --expected-git-sha "${GITHUB_SHA}" \
  --expected-run-id "${GITHUB_RUN_ID}"

# navigation handbook pair coverage
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py

# one-command repo gates
make quality-fast
make quality-full
RUN_LIVE_TESTS=1 make quality-live
# guard-all defaults to LONG_TESTS_PARALLEL=1 (override with LONG_TESTS_PARALLEL=0 when needed)
make guard-all
# local preflight defaults to fast mode; opt into full only when you explicitly
# want the stricter local push rehearsal
make ci-local-preflight
LOCAL_PREFLIGHT_MODE=full make ci-local-preflight
make governance-final

# unified gate tuning knobs
# LONG_TESTS_PARALLEL=1 (default): property+mutation long tests run in parallel
# LONG_TESTS_PARALLEL=0: run long tests sequentially (lower host pressure)
# HEARTBEAT_INTERVAL_SECONDS=30 (default): heartbeat interval for long tests
# E2E_MAX_RETRIES=2 (default): retries for e2e-chromium in unified gate
# retry policy source of truth: tooling/scripts/ci/run_with_retry.sh enforces max retries <= 2
# example:
# LONG_TESTS_PARALLEL=0 HEARTBEAT_INTERVAL_SECONDS=20 bash tooling/scripts/ci/run_unified_test_gate.sh full
# LONG_TESTS_PARALLEL=1 HEARTBEAT_INTERVAL_SECONDS=15 E2E_MAX_RETRIES=2 bash tooling/scripts/ci/run_unified_test_gate.sh full

# live test helpers
make test-live-llm
make test-live-external-web

# install local git hooks (enforce test-smell guard on pre-commit + pre-push)
bash tooling/scripts/runtime/run_uv_managed.sh run pre-commit install --install-hooks
bash tooling/scripts/runtime/run_uv_managed.sh run pre-commit run --all-files
```

## Failure attribution and triage

When using `bash tooling/scripts/ci/run_unified_test_gate.sh full`, logs expose three observability layers:

- Stage progress:
  - `STAGE_PROGRESS: 1/4 (25%)`
  - `STAGE_PROGRESS: 3/4 (75%)`
- Long-task heartbeat:
  - `[heartbeat][<label>] tick=<n> elapsed=<sec>s next_tick_in=<sec>s`
- Retry classification (`tooling/scripts/ci/run_with_retry.sh`):
  - max retries policy: `--max-retries <= 2` (applies to E2E and live retry wrappers)
  - `classification=logic_or_test_regression` -> default `retryable=0` (fix logic/test first)
  - `classification=network_or_environment detail=network_or_external_dependency` -> usually transient/retryable
  - `classification=network_or_environment detail=environment_or_runtime_setup` -> check setup/config/dependencies
- managed dependency bootstrap extraction faults such as `Failed to extract archive` / `No such file or directory (os error 2)` are treated as `environment_or_runtime_setup`, so CI can retry a transient cache-unpack failure instead of hard-failing on the first attempt.
  - `evidence=...` shows first matched signature for quick root-cause confirmation

### Lint/Type Scope Policy

- `pre-commit` uses staged scope (`tooling/scripts/ci/pre_commit_lint.sh`): only staged Python/apps/web files are checked.
- `pre-push` and unified gate use runtime scope (`--mode runtime`): `services/api/`, `packages/core/`, `tooling/scripts/ci/`, and `apps/web/`.
- `pre-push` runs `tooling/scripts/ci/check_commit_authorship_range.sh` to keep new human-visible commit authorship on the configured maintainer identity while still allowing Dependabot as the only bot exception.
- `pre-push` runs `tooling/scripts/ci/check_sensitive_surface_guard.py` to block tracked real local paths, personal identity literals, `.env` files, runtime cache residue, and log artifacts from entering public history.
- `pre-push` runs `tooling/scripts/ci/check_github_security_alerts.py` to fail closed when the live repository still has open GitHub code-scanning or secret-scanning alerts.
- in CI `pull_request` runs, the authorship-range guard now skips cleanly when the runner can only see the synthetic merge ref and no enforceable post-baseline commits are visible; this keeps Dependabot/external fast-gate lanes from failing on repo topology alone.
- `pre-push` runs `tooling/scripts/ci/check_live_test_static_audit.py` (static policy check only, does not execute live tests).
- `pre-push` runs `tooling/scripts/ci/check_navigation_docs_pair.py` to enforce `AGENTS.md + CLAUDE.md` pair coverage in root and governed modules.
- `pre-push` also runs `tooling/scripts/ci/check_workflow_policy.py` and CI contract tests (`tests/ci/test_required_gate_contract.py`, `tests/ci/test_prepush_policy_contract.py`, `tests/ci/test_artifact_evidence_contract.py`, `tests/ci/test_sensitive_surface_guard.py`) to block workflow-gate regressions before push.
- pull_request runs keep repo secrets sealed by default: `.github/workflows/test.yml` records a hosted-safe PR path, while real `check_required_ci_env.sh` enforcement is reserved for non-PR trusted runs.
- `mypy` intentionally excludes `tests/**` and `mutants/**` in the staged gate to avoid non-runtime debt blocking commits.
- Replacement gates for `tests/**` and `mutants/**`: `bash tooling/scripts/ci/check_test_smells.sh`, backend `pytest` gates, property tests, and mutation tests (`mutmut`).
- `jscpd` and `pre-commit outdated` are no longer local pre-push hooks; they were moved to CI/maintenance workflows.

### CI Workflow Structure (Speed-Up Baseline)

- `Tests` workflow uses backend shard lanes: `backend-shard-a` (`tests/api` + `tests/auditable`) and `backend-shard-b` (remaining backend tests), then `backend-coverage-merge` runs `coverage combine` and exports `.runtime-cache/test/coverage/backend/coverage.xml` for threshold checks.
- `post-test-housekeeping` now depends on `property-tests` in addition to other quality jobs.
- `property-tests` remains `changes`-conditioned through the standalone `changes` job (`dorny/paths-filter@v3`); the heavier mutation, performance, and Playwright lanes are manual-only (`workflow_dispatch`) advisory checks.
- `mutation-python` still runs with stricter budgets (`MUTATION_MIN_SCORE=86`, `MUTATION_MAX_NO_TESTS=0`, `MUTATION_MAX_SURVIVED=70`, and zero-regression baseline checks for score and survived mutants), but it no longer blocks the default push path.
- Nightly mutation workflow defaults to `MUTATION_PROFILE=extended` to continuously pressure-check a broader scope than PR `core` runs.
- Chromium E2E still runs as a 6-way `e2e shard` matrix (`1/6` ... `6/6`), and `e2e-real-backend` remains a separate conservative single-worker path, but both now run only on manual dispatch so heavy live lanes do not bootstrap on every push.
- `required-green-gate` is intentionally narrowed to deterministic repo-owned lanes; heavy E2E, UIUX Gemini, mutation, and performance jobs remain advisory/manual lanes and must not silently drift into the blocking aggregate.
- sensitive maintainer witness lanes (`Auditable Quality Gate`, `UIUX Gemini Gate`, `Live Integration`, and manual Claude review lanes) stay behind the protected `owner-approved-sensitive` environment.
- Local Playwright commands use a repo-specific machine cache resolved through `tooling/scripts/runtime/cache_env.sh`; shared system caches such as `~/Library/Caches/ms-playwright` remain advisory-only disk surfaces rather than repo-managed cleanup targets.
- Slow Next.js routes in Playwright specs should prefer `apps/web/e2e/navigation.ts` `gotoWithReadyCheck(...)` plus explicit readiness assertions over raw `page.goto(...)`, so workflow startup jitter is absorbed without introducing sleeps or fake-green waits.
- `pre-commit` workflow (`.github/workflows/pre-commit.yml`) uses `concurrency` with `cancel-in-progress: true` to avoid redundant runs on the same ref.
- `pre-commit` workflow keeps `PRE_COMMIT_HOME` on `lookup-only: true`, uses `timeout-minutes: 30`, and wraps `pre-commit run --all-files` in `tooling/scripts/ci/with_heartbeat.sh` so shared runners avoid slow cache untars while still exposing progress during cold bootstrap.
- Critical workflows no longer allow `paths-ignore`; docs-only changes still execute strict governance checks.
- `test-smells` now blocks Playwright hard waits (`page.waitForTimeout(...)`) by default; temporary allowlist entries must include expiry metadata.
- `jscpd` is enforced in `.github/workflows/jscpd-duplication.yml`; `pre-commit outdated` is enforced in `.github/workflows/pre-commit-outdated-check.yml` with nightly `schedule` + manual trigger.
- `Auditable Quality Gate` workflow (`.github/workflows/auditable-quality-gate.yml`) is now manual-only advisory after dedupe, retaining just `promptfoo-eval` and `ragas-eval` (plus workflow-level `concurrency` + `cancel-in-progress: true`).
- Unified gate Stage 1 keeps `test-smells-guard` and runtime lint serial, then runs two parallel guard batches (`observability+env`, `secret-leaks+navigation`) before docs/upstream parallel checks.

### CI Five-Layer Contract

- `pre-commit`: staged-scope lint and atomic hygiene only; keep it seconds-scale.
- `pre-push`: fast local rehearsal plus contract guards; the default wrapper path is now the `repo-fast` container profile instead of the heaviest bootstrap.
- `hosted`: deterministic push/pull_request lanes that keep required checks and security scanning on GitHub.
- `nightly`: scheduled maintenance and deeper repo-owned pressure checks such as mutation and pre-commit outdated review.
- `manual`: live/provider/browser/desktop/heavier witness lanes that should never silently drift into the default blocking path.

### Eval Proof Surface (Current Honest Scope)

- `promptfoo-eval` is a **deterministic lexical evidence gate**, not a live model judge.
  - It uses the `echo` provider in `evals/promptfoo/promptfooconfig.yaml` to replay prepared `result_json` fixtures.
  - The value comes from stable evidence assertions such as uncited-claim, coverage, duplicate-count, and missing-count checks.
- `ragas-eval` is a **threshold gate** over supplied metrics, not a self-running Ragas pipeline.
  - `evals/ragas/run_ragas_eval.py` only compares configured thresholds with either inline metrics or a provided `results_file`.
  - Inline metrics exist so local and CI behavior stays deterministic by default; they should not be presented as proof of live semantic evaluation.
- The honest repo-level claim today is: **deterministic proof gate + threshold gate + lexical evidence gate**.
- The honest repo-level non-claim today is: **not an end-to-end, live-model quality loop**.

### Navigation Handbook Pair Gate Fix

- Failure `root missing` means repository root must contain both `AGENTS.md` and `CLAUDE.md`.
- Failure `<module> missing` means that module must contain both files; adding only one file still fails.
- For intentional temporary exclusions, set `NAV_DOCS_IGNORE_MODULES=module_a,module_b` in pre-commit/pre-push context and document why.

## 5) Drift Checks Explained

- `check_env_contract_drift.py`
- `check_docs_render_freshness.py`
  - Verifies env keys in `packages/core/settings.py` and docs env table are aligned.
  - Fails on missing keys in either direction.
- `check_upstream_drift.sh`
  - Compares `origin/<branch>` and `upstream/<branch>`.
  - Default fail condition: origin behind upstream.
  - Strict mode also fails on divergence.
  - Requires `origin` and an upstream URL. When no persistent `upstream` remote exists locally, the script fetches the upstream branch into a temporary ref and cleans it up before exit.
- `npm run test:coverage` (from `apps/web/`)
  - Runs apps/web unit/component tests with coverage and enforces thresholds from `apps/web/vitest.config.mts`.
  - CI blocking policy is reconciled by `tooling/scripts/ci/check_coverage_thresholds.py` with global line coverage >=95 and key-module line/branch >=95.
- Backend coverage hard gate uses `--cov-branch` plus `tooling/scripts/ci/check_coverage_thresholds.py` as the canonical threshold reconciler.
- Frontend action-matrix contract (`tooling/scripts/ci/check_frontend_action_matrix.py`)
  - Enforces selector count contract from `meta.expected_counts` (`total/data-testid/id/role`).
  - Enforces runtime evidence contract for `real-backend` actions when `--require-runtime-evidence` is provided.
  - Runtime evidence file is produced by real-smoke flow via `PLAYWRIGHT_ACTION_EVIDENCE_FILE` (default path: `.runtime-cache/runs/current/evidence/apps-web/action-runtime-evidence.json`).
- UIUX Gemini gate (`tooling/scripts/ci/run_uiux_gemini_gate.py`)
  - Blocking mode requires trusted schema fields: `strategy=gemini`, empty/null `fallback_reason`, and run-binding hashes/metadata.
  - `deterministic_fallback` is non-blocking only and requires explicit opt-in (`--allow-deterministic-fallback`), which required workflows must not enable.
- `make test-backend-cov` matches unified gate core defaults: `-m "not property and not live"` and `--ignore=tests/performance` (set `RUN_PERFORMANCE_BENCHMARKS=1` to include benchmarks intentionally).
- `tooling/scripts/ci/post_test_housekeeping.sh`
  - Runs runtime cleanup, docs drift check, and upstream drift check in one command.
  - Upstream drift is advisory by default; pass `--strict-upstream-check` (or set `HOUSEKEEPING_STRICT_UPSTREAM_CHECK=true`) only when you intentionally want housekeeping to fail on drift.
  - `--dry-run-cleanup` prints a repo cleanup execution inventory before invoking the cleanup script.
  - Executed locally on demand and automatically in CI post-test job.
