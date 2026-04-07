# Provenote Final Closed Clean

Last updated: 2026-04-01
Owner: L1 Supreme Closeout Orchestrator
Status: ACTIVE

## Purpose

This is the authoritative handoff artifact after the queue-burst closeout sequence.

It answers one question only:

> What is true now, after the final repo-side fixes, fresh verification, and cleanup evidence, and what still requires operator or external action?

## Repo Positioning

- Vertical: local-first AI research and source-grounded writing
- Primary objects:
  - `auditable runs`
  - `research threads`
  - `notebook drafts`
- Core routes:
  - `Source -> Auditable Markdown -> Draft -> Verify`
  - `Search / Ask -> Research Thread -> Draft`
- Product posture:
  - control tower / operator surface / auditable runtime
  - not a generic AI shell
  - MCP is the integration surface, not the brand center

## Four-Layer Truth Map

| Layer | Current state |
| --- | --- |
| `repo-side truth` | Waves 0-4 repo-side actionable scope exists and is internally aligned |
| `worktree truth` | all repo-side actionable items are implemented locally; frontend i18n regression is fixed; cleanup evidence is refreshed |
| `remote/git truth` | remote still reflects `origin/main`; local dirty state must be promoted via local commit before claiming committed local truth; remote sync still requires explicit push action |
| `live/public truth` | local runtime is healthy; public docs are aligned locally; remote homepage / description / release body are not yet synced to the latest local truth |

## What Changed In This Final Pass

### Repo-side fixes

- repaired the frontend i18n contract for the main journey by:
  - converting interpolated translations in high-value components from `t.section.key({...})` to `t("section.key", {...})`
  - wiring test translation mocks to resolve and interpolate locale strings instead of leaking raw key paths
  - adding the missing locale key `notebooks.draftSelectSource`
- kept the already-landed backend / MCP / contract / shared-client truth intact and revalidated it

### Files directly touched in the final pass

- `apps/web/src/components/notebooks/NotebookDraftPanel.tsx`
- `apps/web/src/components/notebooks/NotebookOutcomeJourneyCard.tsx`
- `apps/web/src/components/notebooks/ResearchThreadsPanel.tsx`
- `apps/web/src/components/source/AuditableMarkdownPanel.tsx`
- `apps/web/src/components/source/SourceOutcomeJourneyCard.tsx`
- `apps/web/src/lib/locales/en-US/sections/core.ts`
- `apps/web/src/test/setup.ts`
- `apps/web/src/components/notebooks/NotebookDraftPanel.test.tsx`
- `apps/web/src/components/notebooks/ResearchThreadsPanel.test.tsx`
- `.agents/Tasks/TASK_BOARD-provenote-full-rollout.md`

## Fresh Evidence

### Backend / MCP / contract

- `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py tests/api/test_draft_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py -q`
  - result: `30 passed`
- `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
  - result: `PASS`
- `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
  - result: `PASS`
- `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/api/generate_frontend_api_contract.py --write`
  - result: `PASS`
- `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_openapi_contract_drift.py`
  - result: `PASS`
- `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
  - result: `PASS`

### Frontend main journey

- `cd apps/web && npm test -- --run 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/components/search/ResearchCapturePanel.test.tsx' 'src/components/source/AuditableMarkdownPanel.test.tsx'`
  - result: `16 passed`
- `cd apps/web && npm test -- --run 'src/components/notebooks/NotebookOutcomeJourneyCard.test.tsx' 'src/components/source/SourceOutcomeJourneyCard.test.tsx' 'src/components/notebooks/ResearchThreadsPanel.test.tsx'`
  - result: `7 passed`
- `cd apps/web && npm test -- --run 'src/app/(dashboard)/search/page.test.tsx' 'src/app/(dashboard)/sources/[id]/page.test.tsx' 'src/app/(dashboard)/notebooks/[id]/page.test.tsx' 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/components/notebooks/NotebookOutcomeJourneyCard.test.tsx' 'src/components/search/ResearchCapturePanel.test.tsx' 'src/components/source/AuditableMarkdownPanel.test.tsx' 'src/components/source/AuditableClaimReviewWorkspace.test.tsx' 'src/components/source/SourceOutcomeJourneyCard.test.tsx'`
  - result: `54 passed`

### Runtime / docs

- local docs link resolution across README + docs index + proof + MCP + project-status + integrations + use-cases
  - result: `PASS`
- `docker compose -f ops/compose/docker-compose.yml ps && curl -fsS --max-time 10 http://localhost:5055/health && curl -I --max-time 10 http://localhost:8502`
  - result:
    - `provenote` and `surrealdb` both `Up`
    - `{"status":"healthy"}`
    - `307 /notebooks`

## Cleanup Evidence

### Before

- `make cleanup-operator-audit`
  - repo internal rebuildables: `309.8 MiB`
  - repo runtime cache root: `309.5 MiB`
  - repo-related machine `uv-cache`: `12.0 KiB`
- `docker system df`
  - images: `16.17GB`
  - build cache: `1.724GB`

### Actions

- `make cleanup-operator-apply`
- `docker builder prune -f`
- manual safe cleanup of remaining repo `__pycache__`

### After

- `docker system df`
  - images: `16.18GB`
  - build cache: `1.724GB`
  - reclaimable build cache: `0B`
- `du -sh .runtime-cache apps/web/.next/cache <repo-machine-cache-root> <repo-machine-cache-root>/python/uv-cache <repo-machine-cache-root>/ci-host/home-cache/provenote/python/uv-cache`
  - `.runtime-cache`: `309M`
  - `apps/web/.next/cache`: `348K`
  - `<repo-machine-cache-root>`: `1.6G`
  - repo-related machine `uv-cache` paths: `0B`
- `find . -type d \\( -name '__pycache__' -o -name '.pytest_cache' \\) -prune`
  - result: none remain

Interpretation:

- runtime cache remained within policy and protected-state boundaries, so it was audited rather than force-cleared
- machine cache and repo pycache residue were safe to clear and were cleared
- Docker build cache had no reclaimable residue left after prune

## Final Matrix Verdict

| Bucket | Final state |
| --- | --- |
| `Implemented in current local truth only` | still the right classification for Waves 0-4 repo-side work |
| `Deferred by design` | unchanged |
| `Rejected / intentionally not pursued` | unchanged |
| `Blocked by genuine external dependency` | unchanged |
| `Not yet implemented but actionable now` | `0 items` |

## Remaining Items Only

### Operator / external blockers

- local commit promotion to reach committed local truth and a clean worktree
- optional push / release / homepage / repo description sync
- domain registration / redirect setup for any future `.ai` surface
- trademark / naming clearance
- official marketplace / directory / vendor listing submission

### Deferred by design

- remote MCP deployment page
- broader marketing-site rewrite
- notebook-wide or hosted multi-user review console beyond current source-level repair
- broader outcome-first MCP expansion beyond current core objects
- hosted/team collaboration/autopilot bets

### Rejected / intentionally not pursued

- official vendor partnership wording
- marketplace or plugin-listing claims without proof
- automatic domain-mirroring rename of repo/package/CLI/MCP names
- SourceHarbor follow-up work inside Provenote closeout

## Next Lowest-Friction Restart

1. Read this file
2. Read `.agents/Plans/2026-04-01__provenote-prompt9-hard-mode-closeout.md`
3. Read `.agents/Tasks/TASK_BOARD-provenote-full-rollout.md`
4. Check:
   - `git status --short --branch`
   - `docker compose -f ops/compose/docker-compose.yml ps`
   - `curl -fsS http://localhost:5055/health`
   - `curl -I http://localhost:8502`
5. Then do only one of:
   - local commit / optional push when explicitly authorized
   - external brand/domain/listing work outside pure repo-side closeout
