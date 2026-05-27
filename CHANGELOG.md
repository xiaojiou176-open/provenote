# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.8.5] - 2026-04-07

### Changed
- Compressed the public front door again so the first screen keeps the product center on `messy long context -> structured insight -> inspectable outcomes`, while leaving MCP, starter bundles, distribution, and promotion surfaces in the second ring.
- Clarified the docs/front-door routing so `README -> quickstart -> proof` is the shortest honest evaluation order, and promotion/status pages stop competing with the first product read.
- Split CI governance more cleanly into `pre-commit / pre-push / hosted / nightly / manual`, moved lingering weekly maintenance language to nightly, and made the default local pre-push rehearsal path fast by default while keeping `full` as the stricter opt-in path.
- Refreshed the active task-board and required-check snapshots with 2026-04-07 live truth so older same-day release/homepage claims no longer masquerade as current state.
- Raised the managed Python security floor by pinning `pillow>=12.1.1,<13` through `tool.uv.override-dependencies`, narrowed uv lock resolution to the current Linux/macOS support surface, and refreshed both `uv.lock` files so the in-repo dependency graph no longer requires the vulnerable `pillow < 12.1.1` line for active supported environments.
- Added repo-owned security/governance workflows for GitHub Dependency Review, Trivy, TruffleHog, and a scoped Zizmor lane, while refreshing the pinned GitHub Actions dependency SHAs for checkout, setup-node, setup-python, github-script, artifact transfer, Docker Buildx/build-push, and the Claude Code action.
- Hardened the composite Python bootstrap action against template-injection by parsing `sync-args` through a shell-safe argv bridge instead of interpolating raw workflow input directly into the `run_uv_managed.sh` command line.
- Converted the stale public-distribution task-board snapshot into an explicitly non-authoritative historical artifact by recording the 2026-04-06 closeout addendum: `main/origin/main = 9d2a4a6`, `open PRs = 20`, `draft releases = []`, `open_graph_image_url = null`, `open code/secret scanning alerts = 0`, and the two active `pillow` Dependabot alerts targeted in this wave.
- Added an explicit Dependabot ignore ledger for the currently unlandable `apps/web` and `evals/promptfoo` update wave so unsupported or unverified package bumps stop reopening as if they were silently accepted.
- Aligned the app root first door with the documented source-first product path by redirecting `/` to `/sources` instead of the notebook lane, so first-run entry now matches the repo's long-context collection story.
- Hardened local runtime host-process safety with fail-closed PID-record handling in the `start_*_local.sh` entrypoints, a new host-process safety CI/runtime gate, and contract coverage that forbids broad kill/desktop-automation primitives in tracked repo automation.
- Required an explicit `NOTEBOOKLAB_ALLOW_DETACHED_CHROME_LAUNCH=1` operator override before detached repo-owned Chrome launches can start from the real-profile helper, keeping manual browser control inside an ownership-first boundary.
- Tightened the tracked OpenClaw example-bundle skills so they preserve the same read-first validation loop and non-public-boundary wording as the repo-local `notebooklab-mcp-outcome-workflows` skill, instead of drifting into over-broad compatibility claims.
- Removed the broken `cache-to: type=gha` export path from both `Development Build` and `Build and Release`; those workflows still read from shared GHA cache scopes, but no longer let optional cache export turn a successfully built GHCR image into a red build.
- Aligned the frontend test toolchain after the `@vitest/ui` bump by moving `vitest`, `@vitest/coverage-istanbul`, and `@vitest/coverage-v8` onto the same `4.1.2` family so fresh installs stop failing peer resolution.
- Refreshed the frontend dependency surface with `@tailwindcss/postcss 4.2.2` and `lucide-react 1.7.0`, while replacing the removed YouTube icon export in `SourceContentTab` with a stable play glyph so the existing content flow keeps rendering.
- Fixed the Cursor-style host bundle contract test so it now checks the bundle command file as a tracked, non-ignored Git path instead of relying on `git status --untracked-files=all` for a clean tracked file.
- Refreshed the closeout truth artifacts so the active plan/task-board layer no longer claims older same-day SHA snapshots or a zero-open-PR state that no longer matches live GitHub truth.
- Clarified the ecosystem truth boundary across the public docs surface so host guides, the first-party CLI, public-skills non-claims, OpenClaw defer status, plugin/marketplace non-claims, and owner-only external actions stay in separate buckets.
- Tightened front-door audience routing across the README, proof page, and quickstart so messy-context, research, coding-agent, operator, and readiness readers can reach the right proof path without mistaking host pages for the product center.
- Refreshed the public status and brand/domain boundary pages with the current external-window framing: repo metadata can be ready before release publication, domain moves, trademark decisions, listings, or partnership actions happen.
- Hardened the outcome client typing surface and the MCP `research_thread.create` typed envelope so runtime type gates pass without changing the current outcome-lane behavior.
- Fixed the runtime lint gate so template-only directories no longer get misclassified as Python source roots during `pre_commit_lint.sh --mode runtime`.
- Added a strict-health option to `notebooklab status --json` so operator and agent workflows can fail fast when the local `/health` probe is down instead of only printing a degraded payload.
- Brought the Claude Code, Codex, and Cursor integration pages up to the same repo-backed proof-loop standard as the OpenCode page, so host compatibility can be verified from repo-owned entrypoints and tests instead of resting on thin setup copy alone.
- Aligned both Docker runtime build paths with the app-local frontend artifact contract, so `ops/docker/Dockerfile` and `ops/docker/Dockerfile.single` now copy `.runtime-cache/build/next/standalone` and `.runtime-cache/build/next/static` instead of stale `.next` assumptions.
- Added tracked Claude Code, Codex, Cursor, and OpenCode starter bundles under `examples/hosts/`, added a dedicated OpenClaw local proof/prep page, and tightened the OpenClaw-compatible bundle family so local install artifacts, skills, and MCP config stay repo-owned without drifting into plugin-store or marketplace claims.
- Hardened registry-auth and release-proof truth around the host bundle and image lanes: release proof now checks explicit GHCR auth linkage, and `Development Build` degrades honestly when GHCR push access is unavailable instead of turning a successful build into a misleading red publish failure.
- Surfaced the tracked host starter bundles from the public front door so developers can reach repo-owned copy/install artifacts directly from the README instead of discovering them only through deeper docs.
- Fixed the Gemini startup probe so SDK-thrown model-404 errors now normalize into the existing fallback semantics instead of crashing startup before the stable fast-path probe can continue.
- Added a host-example landing guard for the Cursor bundle so `.cursor/commands/notebooklab-mcp-outcome-workflows.md` stays visible to Git and contract tests instead of being silently swallowed by the root `.gitignore` `.cursor/` rule.

## [1.8.4] - 2026-04-01

### Changed
- Finalized the local-to-remote closeout wave: the queue-burst rollout now converges as a source-grounded knowledge-work control tower with synchronized README, docs index, project-status, proof, and compatibility surfaces.
- Promoted the previously local-only closeout truth to committed and pushed `main`, including the authoritative version-grade handoff package and refreshed task board / closeout artifacts.
- Completed the high-value journey i18n convergence pass: interpolated notebook/source/research journey strings now flow through the shared locale contract, test translation mocks resolve placeholders correctly, and the main journey frontend suites are green again.
- Kept API, MCP, generated client, and builder-facing wording aligned under the same product truth: first-party MCP remains the integration surface, not the brand center, and current public wording stays compatibility-first without official-partnership overclaim.
- Refreshed cleanup evidence with a new audit/apply/recheck pass, including repo-local runtime/cache hygiene, machine-cache cleanup, and final `__pycache__` removal while preserving protected local state.

## [1.8.3] - 2026-03-28

### Changed
- The release workflow now refuses to publish a release event from an out-of-date tag SHA and only uploads release-proof artifacts when the corresponding image build actually succeeds, reducing noisy false downstream failures in `Build and Release`.
- Release publication semantics are now split cleanly: the real image publication path stays on `workflow_dispatch` from the trusted `main` head, while the `release` event only verifies that a same-SHA successful manual build already exists before allowing the public release page wave to pass.
- Current fork drift governance now uses a refreshed `live_git_truth` sample with direct repo-side validation, and no-merge-base topology is now treated as a first-class selective-port reality instead of an ordinary merge/rebase drift story.
- Public-facing repository wording now describes the current path as a repo-documented local proof loop rather than a one-minute hosted trial, and release visibility is explicitly separated from release health in repo-tracked public surface snapshots.
- Active runtime source and prompt defaults now keep English-only canonical behavior, with a dedicated runtime English boundary gate and contract test wired into the deterministic CI path.
- The tracked public asset pool is now explicitly guarded in CI, and the broken quick-result storyboard GIF has been removed from the repository asset surface.

## [1.8.2] - 2026-03-28

### Changed
- This release tag captured the first governance closeout wave but did not become the final clean public release proof because its release-event build was published before the new same-SHA timing model had been fully exercised.

## [1.8.1] - 2026-03-25

### Changed
- Public-facing repository narrative was rewritten around a product-first Notebooklab identity: the README now leads with result path, proof map, why-star framing, and layered docs entrypoints instead of opening with governance-heavy boundary language.
- Public docs were reorganized for first-time visitors: `docs/index.md` now routes by user goal, and new `docs/quickstart.md`, `docs/proof.md`, and `docs/faq.md` provide evaluation, onboarding, and public-proof entry surfaces.
- Public visual assets were added for GitHub-native growth and sharing, including a hero visual, proof-stack visual, architecture visual, and a social preview image under `docs/assets/`.
- GitHub growth surfaces were tightened around Notebooklab's current public identity, including repository description/topics/discussions strategy, release-note category configuration, and discussion-first support routing in the issue chooser.
- Auto-assign model policy now tolerates provider naming aliases (for example `gemini-3-flash-preview` vs `gemini-3.0-flash`) in `services/services/api/routers/models.py`, and related API regression tests were aligned with current fail-closed idempotency and source-processing error semantics to keep local preflight deterministic.
- UIUX gate hardening for shared self-hosted runners: Playwright browser install now retries with backoff in `.github/workflows/uiux-gemini-gate.yml` to tolerate transient apt lock contention (`/var/lib/apt/lists/lock`) under concurrent CI load.
- UIUX visual baseline stability calibration: increased `maxDiffPixels` for Chromium snapshots in `search/settings/sources` E2E visual-baseline tests while keeping `maxDiffPixelRatio=0.03`, reducing cross-runner rendering false negatives without relaxing ratio-based strictness.
- Playwright CI artifact policy tightened for self-hosted disk stability: screenshot capture is now `only-on-failure` (instead of `on`) while keeping trace/video retry evidence, reducing ENOSPC risk without weakening failure diagnostics.
- Backend coverage merge reliability: normalized cross-runner coverage path handling via `tool.coverage.run.relative_files` + `tool.coverage.paths` and made test/merge steps explicitly use `pyproject.toml` coverage config, fixing `No source for code` failures in `Tests` workflow coverage aggregation.
- Mutation profile config cleanup: removed three intermediate `mutants/tests/test_mutation_survivor_killers.py` injections from `pyproject.toml`; runtime survivor-killer selection now stays script-driven via `tests/test_mutation_survivor_killers_runtime.py`.
- Mutation profile execution now uses repo-relative survivor-killer test selection (`mutants/tests/test_mutation_survivor_killers.py`) instead of runtime-generated absolute temp paths, fixing mutmut collect failures on workspaces whose absolute path includes `[]`.
- Frontend UI accessibility hardening: clickable notebook/source cards are now keyboard-activatable (Enter/Space) with explicit interactive semantics, source card status/progress colors now follow theme tokens, and Playwright a11y gate now scans `/notebooks`, `/sources`, `/settings` in both light and dark themes.
- CI queue-pressure optimization: `Pre-commit` now runs on `push` only for `main` (while still running on `pull_request`), `Claude Code` interaction workflow runs on `ubuntu-latest`, heavy execution lanes are pinned to `e2-core`, and build workflows (`Development Build`, `Build and Release`) enforce workflow-level concurrency to prevent redundant queued runs.
- Additional queue hardening: maintenance/control workflows (`JSCPD Duplication Check`, `Pre-commit Outdated Check`, `Upstream Drift Check`, `Claude Code Review`, `UIUX Auto Remediation`) are now hosted-only with explicit workflow-level concurrency to preserve `e2-core` slots for heavy trusted lanes.
- Build acceleration hardening: `Development Build` and `Build and Release` switched Docker Buildx cache from local filesystem cache to shared `type=gha` scopes, improving cache reuse across self-hosted runners while preserving existing release/quality gates.
- Billing-fallback routing: when GitHub-hosted jobs are unavailable due billing limits, PR gate workflows (`Pre-commit`, `JSCPD Duplication Check`, `Upstream Drift Check`, `Claude Code Review`, `Auditable Quality Gate`, and `Tests`) now execute on `self-hosted,e2-core` to prevent immediate startup failures.
- CI reliability hardening on self-hosted: `Pre-commit` now auto-cleans corrupted cache and retries once, heavy change-detection workflows explicitly grant `pull-requests: read` for `dorny/paths-filter`, and `Claude Code Review` is gated by `vars.CLAUDE_CODE_REVIEW_ENABLED` to avoid failing when the review token is not configured.
- Drift governance scope update: `Upstream Drift Check` is now manual-only (`workflow_dispatch`) so selective-port review stays available without turning every `main` merge into a predictable red maintenance lane.
- Release-proof GHCR auth fix: `tooling/scripts/ci/export_oci_evidence.py` now uses workflow-provided GHCR credentials when available, so same-SHA witness export no longer depends on anonymous GHCR pulls when the repository-scoped package remains private.
- Development Build shared-runner hardening: privileged disk cleanup now degrades to best-effort when passwordless `sudo` is unavailable, and build jobs use isolated Docker config state so macOS keychain prompts do not break Buildx bootstrap before dev image publication even starts.
- Single-container release fix: `ops/docker/Dockerfile.single` now uses a Docker-compatible frontend stage name (`apps-web-builder`), unblocking the single-image build path used by both `Development Build` and `Build and Release`.
- UIUX gate stability hardening: accessibility E2E now tolerates long-running route hydration in CI (`domcontentloaded` + bounded `networkidle` wait), and visual thresholds were calibrated for self-hosted Chromium variance without relaxing ratio guardrails.
- Self-hosted resilience hardening: `UIUX Gemini Gate` now performs bounded runner disk hygiene before E2E (`_diag`/`_temp` retention cleanup + stale report cleanup) and prints disk telemetry to prevent "No space left on device" runner crashes.
- Automatic hosted fallback switch: hosted maintenance workflows (`Pre-commit Outdated Check`, `UIUX Auto Remediation`, `Claude Code`) now support `HOSTED_FALLBACK_TO_E2_CORE`; a new self-hosted workflow (`Hosted Runner Fallback Autoswitch`) detects hosted quota/billing pickup failures, enables fallback, and reruns failed jobs on `e2-core`.
- Spot burst control for heavy lanes: heavy CI jobs now support `CI_HEAVY_USE_SPOT`; enabling it routes mutation/E2E/live-integration heavy tasks to `self-hosted,e2-core,spot`, keeping default behavior stable while unlocking burst capacity when spot runners are available.
- Funnel routing hardening: lightweight CI control lanes now default to `ubuntu-latest` with variable-driven autoswitch fallback (`HOSTED_FALLBACK_TO_E2_CORE`) while heavy lanes remain self-hosted-only (`e2-core`/`spot`) for deterministic throughput.
- Fallback lane isolation hardening: hosted-fallback jobs now target `self-hosted,e2-core-dedicated` (core-only) instead of broad `e2-core`, preventing lightweight fallback traffic from stealing `spot` burst slots reserved for heavy CI lanes.
- Strict key/env fail-fast gate: added `tooling/tooling/scripts/ci/check_required_ci_env.sh` and wired it into critical workflows (`Pre-commit`, `JSCPD`, `Tests`, `Auditable Quality Gate`, `UIUX Gemini Gate`) so missing/placeholder `GEMINI_API_KEY` or `OPEN_NOTEBOOK_ENCRYPTION_KEY` fails CI immediately with no bypass path.
- Local resource policy update: pre-push hook set is slimmed to fast governance checks; heavy static/runtime audits are CI-enforced to keep developer machines responsive without relaxing merge gates.
- Pre-commit load rebalancing: expensive governance scans (`test-smells`, `python test-smells`, live static audit, env/secret governance, navigation docs pair, Gemini UIUX semantic audit, workflow-policy contract tests) were moved from `pre-commit` to `pre-push`, keeping commit-time feedback fast while preserving strict push/CI enforcement.
- Workflow policy hardening (`tooling/tooling/scripts/ci/check_workflow_policy.py`): now additionally enforces strict env gate wiring (`check_required_ci_env.sh` + both required secrets) and codified runner routing contracts for hosted fallback lanes vs heavy self-hosted/spot lanes.
- Live workflow secret parity: `live-integration.yml` now uses the same strict required-secret validator (`check_required_ci_env.sh`) as other critical workflows instead of a simple non-empty key check.
- Heavy runner routing parity: `Tests` backend shards/frontend coverage and `Auditable Quality Gate` eval/property jobs now support `CI_HEAVY_USE_SPOT` (`self-hosted,e2-core,spot`) with stable fallback to `self-hosted,e2-core`.
- Heavy lane routing consistency: `test.yml` `property-tests` now also supports `CI_HEAVY_USE_SPOT`, and workflow policy contracts were updated accordingly to keep heavy lanes uniformly spot-capable.
- Local hook cost trimming: `gemini-uiux-audit-pre-commit` is moved to `manual` stage (optional local execution), while strict UIUX quality gate remains mandatory in CI workflow.

## [1.7.4] - 2026-02-18

### Fixed
- Embedding large documents (3MB+) fails with 413 Payload Too Large (#594)
- `generate_embeddings()` now batches texts in groups of 50 with per-batch retry, preventing provider payload limits from being exceeded
- 413 errors now classified with user-friendly message in error classifier
- Misleading "Created 0 embedded chunks" log in `process_source_command` — embedding is fire-and-forget, so the count was always 0; now logs "embedding submitted" instead

## [1.7.3] - 2026-02-17

### Added
- Retry button for failed podcast episodes in the UI (#211, #218)
- Error details displayed on failed podcast episodes (#185, #355)
- `POST /podcasts/episodes/{id}/retry` API endpoint for re-submitting failed episodes
- `error_message` field in podcast episode API responses

### Fixed
- Podcast generation failures now correctly marked as "failed" instead of "completed" (#300, #335)
- Disabled automatic retries for podcast generation to prevent duplicate episode records (#302)

### Dependencies
- Bump podcast-creator to >= 0.11.2
- Bump esperanto to >= 2.19.4

## [1.7.2] - 2026-02-16

### Added
- Error classification utility that maps LLM provider errors to user-friendly messages (#506)
- Global exception handlers in FastAPI for all custom exception types with proper HTTP status codes
- `getApiErrorMessage()` frontend helper that falls back to backend messages when no i18n mapping exists

### Fixed
- LLM errors (invalid API key, wrong model, rate limits) now show descriptive messages instead of "An unexpected error occurred" (#590)
- SSE streaming error events in source chat and ask hooks were swallowed by inner JSON parse catch blocks
- Transformation execution errors were caught and re-wrapped as generic 500s instead of using proper status codes
- Fail fast when source content extraction returns empty instead of retrying (#589)
- Chat input and message overflow with long unbroken strings (#588)
- Word-wrap overflow in source cards, note editor, inline edit, note titles, and dialog content (#588)
- Translation proxy shadowing `name` keys (#588)
- OpenAI-compatible provider name handling via Esperanto update (#583)

### Changed
- `ValueError` replaced with `ConfigurationError` in model provisioning for proper error classification
- `ConfigurationError` added to command retry `stop_on` lists to avoid retrying permanent config failures

### Dependencies
- Bump esperanto to 2.19.3 (#583)
- Bump podcast-creator to 0.9.1

## [1.7.1] - 2026-02-14

### Added
- French (fr-FR) language support (#581)
- CI test workflow and improved i18n validation (#580)
- Expose embed `command_id` in note API responses (#545)

### Fixed
- ElevenLabs TTS credential passthrough via Esperanto update (#578)
- Handle empty/whitespace source content without retry loop (#576)
- Increase transformation `max_tokens` and update Esperanto dep (#568)
- Turn the embedding field into optional (#557)

### Docs
- Fix docker container names in local setup guides (#577)

### Dependencies
- Bump langchain-core from 1.2.7 to 1.2.11 (#564)
- Bump cryptography from 46.0.3 to 46.0.5 (#563)

## [1.7.0] - 2026-02-10

### Added
- **Credential-Based Provider Management** (#477)
  - New Settings → API Keys page for managing AI provider credentials via the UI
  - Support for 14 providers: OpenAI, Anthropic, Google, Groq, Mistral, DeepSeek, xAI, OpenRouter, Voyage AI, ElevenLabs, Ollama, Azure OpenAI, OpenAI-Compatible, and Vertex AI
  - Secure storage of API keys in SurrealDB with field-level encryption (Fernet AES-128-CBC + HMAC-SHA256)
  - One-click connection testing, model discovery, and model registration per credential
  - Migration tool to import existing environment variable keys into the credential system
  - Azure OpenAI support with service-specific endpoints (LLM, Embedding, STT, TTS)
  - OpenAI-Compatible support with per-service URL configurations
  - Vertex AI support with project, location, and credentials path
  - Environment variable API keys deprecated in favor of Settings UI

- **Security Enhancements**
  - Docker secrets support via `_FILE` suffix pattern (e.g., `OPEN_NOTEBOOK_PASSWORD_FILE`)
  - Default encryption key derived from "0p3n-N0t3b0ok" for easy setup (change in production!)
  - Default password "open-notebook-change-me" for out-of-box experience (change in production!)
  - URL validation for SSRF protection - blocks private IPs and localhost (except for Ollama which runs locally)
  - Security warnings logged when using default credentials

- HTML clipboard detection for text sources (#426)
  - When pasting content, automatically detects HTML format (e.g., from Word, web pages)
  - Shows info message when HTML is detected, informing user it will be converted to Markdown
  - Preserves formatting that would be lost with plain text paste
  - Bump content-core to 0.11.0 for HTML to Markdown conversion support

- **Improved Getting Started Experience**
  - Simplified docker-compose.yml in repository root (single official file)
  - Added examples/ folder with ready-made configurations:
    - `docker-compose-ollama.yml` - Local AI with Ollama
    - `docker-compose-speaches.yml` - Local TTS/STT with Speaches
    - `docker-compose-full-local.yml` - 100% local setup (Ollama + Speaches)
  - Inline quick start in README (no need to navigate to docs)
  - Cross-references between docker-compose examples and documentation
  - .env.example template with all configuration options

### Fixed
- Azure form race condition: all configuration now saved in single atomic request
- Migration API "error error" display: added proper MigrationResult model with message field
- Connection tester for Ollama providers: improved error handling and URL validation
- SqliteSaver async compatibility issues in chat system (#509, #525, #538)
- Re-embedding failures with empty content (#513, #515)
- Deletion cascade for notes and sources (#77)
- YouTube content availability issues (#494)
- Large document embedding errors (#489)

### Security
- API keys are encrypted at rest using Fernet symmetric encryption
- Keys are never returned to the frontend, only configuration status
- SSRF protection prevents internal network access via URL validation

### Docs
- Complete documentation update for credential-based system across 25 files
- All quick-start, installation, and configuration guides now use Settings UI workflow
- Environment variable API key instructions moved to deprecated/legacy sections
- Fixed broken links in installation docs
- Added comprehensive examples/ folder with documented docker-compose configurations
- Updated local-tts.md and local-stt.md with links to ready-made examples

### Internationalization
- Added Russian (ru-RU) language support (#524)
- Added Italian (it-IT) language support (#508)

## [1.6.2] - 2026-01-24

### Fixed
- Connection error with llama.cpp and OpenAI-compatible providers (#465)
  - Bump Esperanto to 2.17.2 which fixes LangChain connection errors caused by garbage collection

## [1.6.1] - 2026-01-22

### Fixed
- "Failed to send message" error with unhelpful logs when chat model is not configured (#358)
  - Added detailed error logging with model selection context and full traceback
  - Improved error messages to guide users to Settings → Models
  - Added warnings when default models are not configured

### Docs
- Ollama troubleshooting: Added "Model Name Configuration" section emphasizing exact model names from `ollama list`
- Added troubleshooting entry for "Failed to send message" error with step-by-step solutions
- Updated AI Chat Issues documentation with model configuration guidance


## [1.6.0] - 2026-01-21

### Added
- Content-type aware text chunking with automatic HTML, Markdown, and plain text detection (#350, #142)
- Unified embedding generation with mean pooling for large content that exceeds model context limits
- Dedicated embedding commands: `embed_note`, `embed_insight`, `embed_source`
- New utility modules: `chunking.py` and `embedding.py` in `packages/core/utils/`
- Japanese (ja-JP) language support (#450)

### Changed
- Embedding is now fire-and-forget: domain models submit embedding commands asynchronously after save
- `rebuild_embeddings_command` now delegates to individual embed_* commands instead of inline processing
- Chunk size reduced to 1500 characters for better compatibility with Ollama embedding models
- Bump Esperanto to 2.16 for increased Ollama context window support

### Removed
- Legacy embedding commands: `embed_single_item_command`, `embed_chunk_command`, `vectorize_source_command`
- `needs_embedding()` and `get_embedding_content()` methods from domain models
- `split_text()` function from text_utils (replaced by `chunk_text()` in chunking module)

### Fixed
- Embedding failures when content exceeds model context limits (#350, #142)
- Empty note titles when saving from chat (clean thinking tags from prompt graph output)
- Orphaned embedding/insight records when deleting sources (cascade delete)
- Search results crash with null parent_id (defensive frontend check)
- Database migration 10 cleans up existing orphaned records

## [1.5.2] - 2026-01-15

### Performance
- Improved source listing speed by 20-30x (#436, closes #351)
  - Added database indexes on `source` field for `source_insight` and `source_embedding` tables
  - Use SurrealDB `FETCH` clause for command status instead of N async calls

## [1.5.1] - 2026-01-15

### Fixed
- Podcast dialog infinite loop error caused by excessive translation Proxy accesses in loops
- Podcast dialog UI freezing when typing episode name or additional instructions
- Removed incorrect translation keys for user-defined episode profiles (user content should not be translated)

## [1.5.0] - 2026-01-15

### Added
- Internationalization (i18n) support with Chinese (Simplified and Traditional) translations (#371, closes #344, #349, #360)
- Frontend test infrastructure with Vitest (#371)
- Language toggle component for switching UI language (#371)
- Date localization using date-fns locales (#371)
- Error message translation system (#371)

### Fixed
- Accessibility improvements: added missing `id`, `name`, and `autoComplete` attributes to form inputs (#371)
- Added `DialogDescription` to dialogs for Radix UI accessibility compliance (#371)
- Fixed "Collapsible is changing from uncontrolled to controlled" warning in SettingsForm (#371)
- Fixed lint command for Next.js 16 compatibility (`eslint` instead of `next lint`)

### Changed
- Dockerfile optimizations: better layer caching, `--no-install-recommends` for smaller images (#371)
- Dockerfile.single refactored into 3 separate build stages for better caching (#371)

## [1.4.0] - 2026-01-14

### Added
- CTA button to empty state notebook list for better onboarding (#408)
- Offline deployment support for Docker containers (#414)

### Fixed
- Large file uploads (>10MB) by upgrading to Next.js 16 (#423)
- Orphaned uploaded files when sources are removed (#421)
- Broken documentation links to ai-providers.md (#419)
- ZIP support indication removed from UI (#418)
- Duplicate Claude Code workflow runs on PRs (#417)
- Claude Code review workflow now runs on PRs from forks (#416)

### Changed
- Upgraded Next.js from 15.4.10 to 16.1.1 (#423)
- Upgraded React from 19.1.0 to 19.2.3 (#423)
- Renamed `middleware.ts` to `proxy.ts` for Next.js 16 compatibility (#423)

### Dependencies
- next: 15.4.10 → 16.1.1
- react: 19.1.0 → 19.2.3
- react-dom: 19.1.0 → 19.2.3

## [1.2.4] - 2025-12-14

### Added
- Infinite scroll for notebook sources - no more 50 source limit (#325)
- Markdown table rendering in chat responses, search results, and insights (#325)

### Fixed
- Timeout errors with Ollama and local LLMs - increased to 10 minutes (#325)
- "Unable to Connect to API Server" on Docker startup - frontend now waits for API health check (#325, #315)
- SSL issues with langchain (#274)
- Query key consistency for source mutations to properly refresh infinite scroll (#325)
- Docker compose start-all flow (#323)

### Changed
- Timeout configuration now uses granular httpx.Timeout (short connect, long read) (#325)

### Dependencies
- Updated next.js to 15.4.10
- Updated httpx to >=0.27.0 for SSL fix
