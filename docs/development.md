# Development

Use this document as the contributor entrypoint for this fork.

If you are a first-time evaluator rather than a contributor, start with [../README.md](../README.md) and [quickstart.md](quickstart.md) instead.

## Bootstrap

```bash
bash tooling/scripts/runtime/run_uv_managed.sh sync
cd apps/web && npm ci && cd ../..
```

## Core commands

```bash
make test-backend-cov
cd apps/web && npm test && cd ../..
bash tooling/scripts/ci/check_env_governance.sh
bash tooling/scripts/ci/check_secret_leaks.sh
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py
bash tooling/scripts/ops/audit_space_surfaces.sh
bash tooling/scripts/runtime/run_uv_managed.sh run notebooklab status --json --require-healthy
bash tooling/scripts/runtime/run_uv_managed.sh run notebooklab research-thread-to-draft research_thread:123 --verify --download-markdown --download-bundle --output-dir ./exports --json
```

## Local manual browser flow

Use the real Chrome `notebooklab` profile only for local manual browser investigation, not for CI or the formal Playwright test runner.

Environment contract:

- `NOTEBOOKLAB_BROWSER_MODE=real_chrome_profile|managed_playwright`
  - default for the manual launcher: `real_chrome_profile`
- `NOTEBOOKLAB_CHROME_USER_DATA_DIR`
  - default: `~/.cache/notebooklab/browser/chrome-user-data`
- `NOTEBOOKLAB_CHROME_PROFILE_NAME`
  - default: `notebooklab`
- `NOTEBOOKLAB_CHROME_PROFILE_KEY`
  - default target profile key after migration: `Profile 1`
- `NOTEBOOKLAB_SOURCE_CHROME_USER_DATA_DIR`
  - default migration source: `~/Library/Application Support/Google/Chrome`
- `NOTEBOOKLAB_SOURCE_CHROME_PROFILE_KEY`
  - optional migration override when you already know the original Chrome profile directory key
- `NOTEBOOKLAB_CHROME_CDP_PORT`
  - default: `9342`
- `NOTEBOOKLAB_BROWSER_URL`
  - optional initial URL for the manual browser launch
- `NOTEBOOKLAB_BROWSER_IDENTITY_LABEL`
  - optional identity-tab label override for the repo-owned browser lane
- `NOTEBOOKLAB_BROWSER_IDENTITY_ACCENT`
  - optional identity-tab accent override with a hex color such as `#2563eb`

Initial one-time migration:

```bash
cd apps/web && npm run browser:manual:migrate-profile && cd ../..
```

The migration command:

- requires Chrome/Chromium to be fully stopped first
- copies only `Local State` and the selected `Profile xxx/`
- rewrites the target root to contain only:
  - `~/.cache/notebooklab/browser/chrome-user-data/Local State`
  - `~/.cache/notebooklab/browser/chrome-user-data/Profile 1/`
- removes `Singleton*` lock artifacts from the new root

Manual launcher status:

```bash
cd apps/web && npm run browser:manual:status && cd ../..
```

Manual launcher:

```bash
cd apps/web && npm run browser:manual && cd ../..
```

Default launcher semantics:

- `browser:manual` is **start-or-attach**
- it prefers a single shared repo Chrome instance
- if the instance is already alive and its CDP endpoint is reachable, the command attaches to it
- if no compatible instance is running, it starts one and records state in `.runtime-cache/browser/chrome-instance.json`
- it writes a repo-owned identity tab to `.runtime-cache/browser-identity/index.html`
- it keeps that identity tab in the canonical target set so the lane stays human-identifiable on both first launch and instance reuse

Identity tab behavior:

- title format: `<repo-label> · <cdp-port> · browser lane`
- fields shown:
  - repo label
  - CDP URL / port
  - repo root
  - browser user-data-dir
  - profile display name
  - profile directory
- default identity label is the repo directory name
- default accent is a stable hash-derived color
- manual one-time polish is allowed:
  - keep the identity tab on the left when possible
  - pin it manually once if you want a tighter visual marker
- intentionally not automated:
  - Chrome pinned-tab state
  - Chrome profile avatar/theme internals
  - Dock name/icon changes

Those browser-private tweaks are left manual on purpose because they are brittle, version-sensitive, and outside the stable repo-owned automation surface.

If you want the isolated fallback instead of the real Chrome profile:

```bash
cd apps/web && NOTEBOOKLAB_BROWSER_MODE=managed_playwright npm run browser:manual && cd ../..
```

Boundary:

- local manual browser flow may use the real Chrome profile for DOM inspection, console review, API investigation, and login-state continuation
- the repo-owned Chrome root is isolated from the default Chrome user-data root, so the manual lane no longer depends on the shared default Chrome single-instance lock
- CI, `test:e2e`, and `UITestRunRequest` remain isolated and continue to use the managed Playwright browser path

## Maintenance runbooks

- [runbooks/space-governance.md](runbooks/space-governance.md) covers the disk-surface classification model, audit commands, cleanup buckets, and recovery commands.
- [runbooks/operator-cli.md](runbooks/operator-cli.md) covers the first-party operator CLI for status checks, notebook outcome inspection, auditable markdown, and research-thread-to-draft handoffs.
- [../examples/hosts/README.md](../examples/hosts/README.md) is the checked-in compatibility-artifact index for direct Claude Code, Codex, Cursor, and OpenCode public-ready starter bundles plus OpenClaw-compatible public-ready bundles; treat those bundles as repo-hosted install packages, not as marketplace, directory, or partnership claims.

## Upstream maintenance

- This fork uses a `selective-port-first` policy for upstream maintenance rather than a default merge/rebase sync.
- The current topology truth lives in `config/upstream/selective-port-ledger.json` under `live_git_truth`.
- Historical topic clusters under `entries[]` are planning context only. They must not be cited as the current origin/upstream topology once `live_git_truth` disagrees with them.
- Refresh `live_git_truth` by manually dispatching `.github/workflows/upstream-drift.yml` before citing current counts, merge-base status, or fork-topology conclusions.
- Treat `tooling/scripts/ci/check_selective_port_ledger.py` as the repo-side proof that the committed `live_git_truth` block still matches the current local `origin/main` and the current upstream `main` sample.
- Treat `observed_at_utc` and `refresh_required_after_utc` as freshness metadata for the block that declares them: once the freshness window expires, that sample becomes historical context only until it is re-sampled.
- As of the current reviewed topology sample, `origin/main` and `upstream/main` do not share a merge-base, so this repository must be treated as a long-lived productized selective-port fork rather than a normal merge/rebase candidate.
- As of the current reviewed topology sample, `origin_only_commits=9` and `upstream_only_commits=654`. These counts are current only through the active `live_git_truth` block and must not be copied into prose after that block goes stale.
- The contributor SOP for selective-port handling lives in this document plus the ledger itself: read `live_git_truth` first, then use historical entries only for batching or portability context.
- Daily worktrees do not need to keep a persistent `upstream` remote. Upstream maintenance scripts resolve the official upstream branch on demand, compare against it, and clean up temporary refs before exit.

### Upstream sync SOP

1. Read `config/upstream/selective-port-ledger.json` and treat `live_git_truth` as the only current topology source.
2. Confirm `observed_at_utc` and `refresh_required_after_utc` before quoting any live count or merge-base conclusion.
3. Run `python3 tooling/scripts/ci/check_selective_port_ledger.py` after refreshing or before citing the sample, so committed `live_git_truth` is verified against the current local `origin` refs and an on-demand upstream sample.
4. If the freshness window has expired or the checker reports a mismatch, refresh the sample through `.github/workflows/upstream-drift.yml` before planning selective port work.
5. Use historical `entries[]` only for selective port batching, portability review, or decision history after the current topology sample has been checked.

## CI closure notes

- The deterministic PR path is anchored by `Required Green Gate` in `.github/workflows/test.yml:592` and `.github/workflows/test.yml:1173`.
- Ordinary pull_request runs now keep `GEMINI_API_KEY` and `OPEN_NOTEBOOK_ENCRYPTION_KEY` sealed. `required-ci-env` records the hosted-safe PR path, and real CI secret enforcement is limited to non-PR trusted runs.
- Hosted-safe external PR lanes can see only the synthetic merge ref in CI. The `OPEN_NOTEBOOK_EXTERNAL_PR_FAST_GATE=1` marker keeps commit-governance range guards lane-aware so Dependabot/external fast gates skip cleanly on empty post-baseline work instead of failing on topology alone.
- The marker is injected only by `.github/workflows/test.yml` on the `external-pr-fast-gate` job, so trusted same-repo PR lanes still keep the normal commit-governance fail-closed behavior.
- Security and dependency governance now includes four dedicated workflows in addition to the existing `test.yml` and CodeQL lanes:
  - `.github/workflows/dependency-review.yml`
  - `.github/workflows/zizmor.yml`
  - `.github/workflows/trivy.yml`
  - `.github/workflows/trufflehog.yml`
- These lanes are intentionally separate from `Required Green Gate`: they provide fresh repo-owned dependency and workflow hardening evidence without silently widening the deterministic required aggregate.
- Frontend dependency maintenance should keep peer-linked packages aligned in the same lane. Current repo examples: `react` and `react-dom` should stay on the same patch line, and `@size-limit/file` should move with `size-limit` instead of leaving a stale peer version behind.
- Hosted-first CI now keeps operational cleanup inside the remaining manual/maintenance lanes instead of a dedicated runner-recovery workflow.
- GitHub Actions dependency maintenance may update pinned workflow actions independently of product code. Current examples include `docker/login-action`, `dorny/paths-filter`, and `anthropics/claude-code-action`; validate these through workflow contract tests and hosted-lane reruns rather than treating them like ordinary app or runtime dependency bumps.
- Sensitive maintainer witness lanes (`Auditable Quality Gate`, `UIUX Gemini Gate`, `Live Integration`, and manual Claude review lanes) must stay behind the protected `owner-approved-sensitive` environment.
- The frontend container bootstrap must validate the shared Playwright cache from the currently installed browser bundle, not from stale revision-specific directory names. See `tooling/scripts/ci/run_in_consistent_container.sh:347`.
- The manual UIUX witness lane remains trusted-path only. It is a maintainer witness flow for UI artifacts, not a storefront image QA replacement. See `.github/workflows/uiux-gemini-gate.yml:30`.

Search-before-write evidence for navigation or gate changes:

```bash
rg -n "<keyword>" AGENTS.md CLAUDE.md README*.md docs config contracts tooling services packages apps tests ops evals mutants
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*.md'
```

## Documentation policy

- Keep tracked docs English-only.
- Keep the public docs surface minimal.
- Keep runtime, cache, agent, and log directories untracked.
- Keep active public-facing assets inside the approved `docs/assets/{hero,demo,proof,architecture,social}` pool only.
- Public-facing assets must pass a high-resolution manual review before they are linked from README or repo-tracked public docs.

## Local runtime boundary

- Ignored local files such as `.env`, `.env.local`, and user-specific runtime overrides remain a local runtime boundary.
- They are not part of the tracked public repository surface, but they still block any claim that a workstation is fully clean unless local proof exists.
- Never copy local secret values or absolute machine paths into repo docs, proof artifacts, or public issue/PR text.
- Active runtime source defaults and active prompt-pack defaults must stay English-only outside explicit locale/test/demo surfaces.

## Local process safety

Local stop and port-release flows are fail-closed on purpose.

- Repo-owned local services must be recorded under `.runtime-cache/local/pids` with command and start-time metadata.
- `tooling/scripts/dev/stop_local.sh` and `tooling/scripts/ci/release_local_ports.sh` only stop recorded repo-owned services.
- If a target port is occupied by an unknown listener, the scripts must report the PID/command and exit non-zero instead of killing that process.
- Broad host-process primitives are forbidden in tracked repo automation paths:
  - `pkill`
  - `killall`
  - `kill -9`
  - `xargs kill`
  - `osascript`
  - `System Events`

## Navigation policy

The only tracked navigation handbooks are:

- root `AGENTS.md` and `CLAUDE.md`
- `apps/web`
- `services/api`
- `packages/core`
- `tests`

## Contribution path

1. Start from an issue or a clearly scoped change.
2. Keep patches narrow.
3. Run targeted verification.
4. Update minimal public docs only when behavior or contributor workflow changes.

See [../CONTRIBUTING.md](../CONTRIBUTING.md) for the review and submission boundary.
