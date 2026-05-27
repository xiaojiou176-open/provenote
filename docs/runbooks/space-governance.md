# Space Governance Runbook

Use this runbook when you need to understand or reclaim Notebooklab-related disk usage without guessing.

## Classification Model

Space governance uses five retention classes only:

- `ephemeral`: cheap transient noise that is safe to clear
- `rebuildable`: rebuildable output that still has a developer-time cost
- `evidence`: current proof or diagnostics that should not be auto-cleared
- `protected`: backup, state, or mixed surfaces that require manual review
- `shared_layer`: machine-wide surfaces that may be related to Notebooklab but are not repo-exclusive

Clear actions are intentionally separate from rebuildability:

- `safe_clear`
- `cautious_clear`
- `verify_before_clear`
- `do_not_clear`

## Audit Commands

Human-readable audit:

```bash
bash tooling/scripts/ops/audit_space_surfaces.sh
```

JSON output for automation:

```bash
bash tooling/scripts/ops/audit_space_surfaces.sh --format json
```

Machine-cache audit lane:

```bash
bash tooling/scripts/ops/cleanup_machine_cache.sh --mode audit-only
```

Housekeeping inventory for repo-managed cleanup candidates:

```bash
bash tooling/scripts/ops/audit_space_surfaces.sh \
  --inventory-class repo_managed_candidate \
  --action-filter safe_clear,cautious_clear
```

If you specifically need the repo-internal execution view that matches `cleanup_runtime_cache.sh`, use:

```bash
bash tooling/scripts/ops/audit_space_surfaces.sh \
  --cleanup-owner cleanup_runtime_cache.sh \
  --action-filter safe_clear,cautious_clear
```

Explicit operator path that chains repo-local runtime cleanup, repo-related machine cache review, and Docker/buildx review:

```bash
make cleanup-operator-audit
make cleanup-operator-apply
```

Detailed machine-cache dry run, including stale bootstrap snapshots:

```bash
bash tooling/scripts/ops/cleanup_machine_cache.sh \
  --mode dry-run \
  --include-stale-bootstrap-snapshots
```

Schema and contract validation:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_space_surfaces.py
```

## Operator Path

Use one explicit operator path instead of remembering separate buildx and
repo-local cleanup commands by hand.

```bash
make cleanup-operator-dry-run
make cleanup-operator-rebuildable
make cleanup-operator-aggressive
```

What each lane means:

- `cleanup-operator-dry-run`
  - audits repo-owned runtime surfaces
  - audits repo-related machine caches
  - previews repo-local cleanup
  - tells the operator when `docker-buildx-clean` is the next manual step
- `cleanup-operator-rebuildable`
  - runs `docker-buildx-clean`
  - runs `cleanup_runtime_cache.sh`
  - applies repo-related machine-cache cleanup for stale bootstrap snapshots and legacy `~/.cache/notebooklab-*` roots
- `cleanup-operator-aggressive`
  - still keeps repo-external machine caches in a repo-related operator lane
  - applies stale bootstrap snapshot cleanup and historical machine-cache
    candidates once their age gates pass

## Cleanup Buckets

### Bucket 1: Safe Clear

These are small repo-local transient caches such as:

- `.hypothesis`
- `.runtime-cache/test/pytest_cache`
- `tests/**/__pycache__`
- `mutants/**/__pycache__`

### Bucket 2: Cautious Clear

These are repo-exclusive and rebuildable, but clearing them slows the next run.
Some are repo-internal execution targets, while repo-external entries are candidate inventory only:

- `apps/web/node_modules`
- `apps/web/.runtime-cache/build/next/cache`
- `.runtime-cache/local/ruff-cache`
- `.runtime-cache/local/mypy-cache`
- `.runtime-cache/ci-host/home-cache/notebooklab/python/uv-cache`
- `.runtime-cache/ci-host/home-cache/pre-commit`
- `.runtime-cache/ci-host/home-cache/go-build`
- `.runtime-cache/ci-host/tmp`
- `${HOME}/.cache/notebooklab/playwright/ms-playwright`
- `${HOME}/.cache/notebooklab/python/uv-cache`
- `${HOME}/.cache/notebooklab/ci-host/npm-cache`

Important boundary:

- `apps/web/node_modules` is a repo-local dependency root.
- `.runtime-cache/ci-host/...` paths are repo-local runtime/bootstrap residue owned by this checkout.
- `${HOME}/.cache/notebooklab/...` paths are limited to repo-specific machine download caches.
- They may both be Notebooklab-related, but they are **not** the same cleanup lane and must not be collapsed into one bucket by operator docs or scripts.

Boundary note:

- `apps/web/node_modules` is a repo-local rebuildable dependency root.
- It is **not** a machine-wide cache and must not be re-labeled as shared-layer
  cleanup just because reinstalling it requires network/package resolution.
- Clearing it is allowed only through the repo-managed runtime cleanup path, and
  operators must expect to rerun `cd apps/web && npm ci` afterwards.

### Bucket 3: Verify Before Clear

These keep current proof, backup, state, or tracked worktree context:

- `.runtime-cache/runs/current`
- `.runtime-cache/closure-backups`
- `.runtime-cache/state/local/data`
- `.runtime-cache/venv/default`
- `.runtime-cache/ci-host/bootstrap/apps-web-node-modules`
- `.runtime-cache/ci-host/home-cache/notebooklab/python/uv-project-environment`
- `.runtime-cache/test/coverage/apps/web`
- `.runtime-cache/test/coverage/apps/web-direct`
- `.runtime-cache/test/coverage-batches/apps-web`
- `.runtime-cache/manual-front-a`
- `.runtime-cache/manual-front-b`
- `.runtime-cache/history-rebuild`
- `.runtime-cache/runs/final-release-proof-*`
- `.git/cursor`
- `mutants`
- `${HOME}/.cache/notebooklab/open-source-audit`
- `${HOME}/.cache/notebooklab-*` historical candidates

### Bucket 4: Do Not Clear In Repo Automation

These are not repo-managed cleanup targets:

- `.git`
- `.git/objects`
- `${HOME}/.cache/uv`
- `~/.cache/uv`
- `${HOME}/.npm`
- `${HOME}/Library/Caches/ms-playwright`
- `${HOME}/Library/Containers/com.docker.docker`
- `${HOME}/.docker`
- `${HOME}/.cache/notebooklab/browser/chrome-user-data`

## Recovery Commands

Frontend dependencies:

```bash
cd apps/web && npm ci && cd ../..
```

Managed Python environment and uv cache:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh sync --frozen --extra dev
```

Repo-specific Playwright browsers:

```bash
cd apps/web && npm run test:e2e:install && cd ../..
```

Consistent-container caches:

```bash
bash tooling/scripts/ci/run_in_consistent_container.sh --profile python -- \
  bash -lc 'bash tooling/scripts/runtime/run_uv_managed.sh sync --frozen --extra dev'
```

Repo-local managed Python environment:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh sync --frozen --extra dev
```

## Single-Container Log Truth

The canonical single-container supervisor log roots are:

- `/app/.runtime-cache/runs/current/logs/single-container/`
- `.runtime-cache/runs/current/logs/single-container/`

Current truth boundary:

- `/tmp/*.log` is not a source of truth
- single-container runtime logs must resolve under the canonical runtime-cache path above

## Why Shared Layers Are Not Auto-Cleared

Shared layers are like a building-wide storage room: Notebooklab may use them, but other projects can be using the same storage at the same time.

That is why these paths stay advisory-only in repo automation:

- `${HOME}/.npm`
- `${HOME}/Library/Caches/ms-playwright`
- `${HOME}/Library/Containers/com.docker.docker`
- `${HOME}/.docker`

They can still appear in audits, but repo-owned cleanup scripts must not treat them as Notebooklab-exclusive reclaim targets.

The isolated Chrome user-data root is different:

- `${HOME}/.cache/notebooklab/browser/chrome-user-data`

It is repo-exclusive, but it is a **permanent browser state surface**, not a clearable download cache. Repo automation must treat it as protected browser state and keep it out of TTL/cap trimming.

## Docker Runtime Operator Path

Notebooklab now keeps Docker/buildx cleanup explicit instead of leaving it as tribal knowledge.

- `make docker-runtime-audit`
  - shows repo-related local `open-notebook-ci:*` images, buildx builders, and `docker system df -v` output
- `make docker-buildx-clean`
  - clears buildx builders and BuildKit helper containers
- `make cleanup-operator-audit`
  - audits repo-local cleanup targets, repo-related machine caches, and Docker surfaces in one sequence
- `make cleanup-operator-apply`
  - applies repo-local runtime cleanup, repo-related machine-cache cleanup, and buildx cleanup in that order

This split matters:

- local `open-notebook-ci:*` and buildx residue belong to the Docker operator view
- `apps/web/node_modules` belongs to the repo-local rebuildable dependency view
- `.runtime-cache/venv/default` and `.runtime-cache/ci-host/...` belong to the repo-local runtime/bootstrap view
- `~/.cache/notebooklab/...` belongs to the repo-related machine-cache view only when the surface is a download cache

## Inventory Versus Execution

Two inventory views intentionally coexist:

- `--inventory-class repo_managed_candidate --action-filter ...`
  - repo-managed candidate inventory
  - the default operator-facing summary because it includes repo-local rebuildables and repo-owned machine caches in one honest view
- `--cleanup-owner cleanup_runtime_cache.sh --action-filter ...`
  - repo cleanup execution inventory
  - only the repo-internal surfaces handled by `cleanup_runtime_cache.sh`
  - excludes repo-owned machine caches on purpose, so it should not be mistaken for the full repo-related disk picture

Docker attribution uses three states:

- `unresolved`
- `reachable_but_unattributed`
- `resolved`

Until a dedicated per-repo Docker attribution lane exists, Docker Desktop should stay in the first two states only.

## Machine Cache Namespace

The canonical repo-specific machine cache root is:

- `${HOME}/.cache/notebooklab`

Important subtrees inside that namespace:

- `${HOME}/.cache/notebooklab/python/uv-cache`
- `${HOME}/.cache/notebooklab/playwright/ms-playwright`
- `${HOME}/.cache/notebooklab/ci-host/npm-cache`

Treat this namespace like a repo-owned download shed: it is still Notebooklab-related space even though it lives outside the checkout, but it should only contain reusable download caches.

## Historical Candidates Versus Strict Confirmed Usage

The audit intentionally separates four ideas:

- strict confirmed repo-internal space
- strict confirmed repo-external space
- shared advisory-only layers
- historical candidates

This is why the distinct summary can show historical candidates separately from strict confirmed totals. It prevents parent/child double counting and keeps unresolved named candidates from being silently mixed into the confirmed repo footprint.

`~/.cache/notebooklab-*` entries are migration-only historical candidates. The canonical machine cache root is `~/.cache/notebooklab`, and entrypoint-triggered machine-cache cleanup now removes stray legacy roots instead of preserving them indefinitely.

## Bootstrap Snapshot Governance

`.runtime-cache/ci-host/bootstrap/apps-web-node-modules` stores lock-hash keyed frontend dependency snapshots for the consistent-container bootstrap flow.

Those snapshots must be classified before cleanup:

- `active-bootstrap-cache`: matches the current frontend lock hash and must be preserved
- `stale-bootstrap-candidate`: does not match the current lock hash; report first, then only clear when age/generation thresholds and lock-safety checks pass

The repo-local cleanup lane must never wipe the bootstrap root wholesale. It may only consider stale snapshots individually, while preserving the active hash and any locked snapshot directories.
