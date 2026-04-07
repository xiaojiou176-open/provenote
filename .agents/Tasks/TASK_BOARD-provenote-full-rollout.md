# Provenote Full Rollout Task Board

Last updated: 2026-04-07 final mainline/tag truth sync after closeout merge
Owner: L1 Orchestrator
Status: ACTIVE

## 2026-04-07 Current Truth Refresh

- current truth layer:
  - `main == origin/main` at the current canonical closeout head
  - current worktree is clean on `main`
  - remote GitHub live truth currently reads:
    - open PRs: `0`
    - Pages: built from `main:/docs`
    - homepage: `https://xiaojiou176-open.github.io/provenote/`
    - description: `Messy long context -> structured insight -> auditable markdown, research threads, and inspectable outcomes.`
    - topics: `ai-notes`, `auditable-markdown`, `citations`, `knowledge-management`, `long-context`, `mcp`, `notebooks`, `research-assistant`, `research-threads`, `research-workbench`, `source-grounded-writing`, `traceable-writing`
    - custom social preview: not currently proven live (`open_graph_image_url = null`)
    - branch protection: `Required Green Gate`, strict, linear history, required signatures enabled
    - code scanning / secret scanning / dependabot alerts: `0 / 0 / 0`
    - secret-scanning higher toggles remain below ceiling:
      - `secret_scanning_non_provider_patterns = disabled`
      - `secret_scanning_validity_checks = disabled`
      - a repo-owned PATCH attempt was accepted without changing live state, so this is currently classified as a GitHub plan/policy boundary rather than a solved repo-side hardening step
    - releases: `Provenote v1.8.5` is published as the current canonical GitHub release object
    - tag truth:
      - `v1.8.4` remains pinned to the old hard-cut baseline commit `3f9328b`
      - `v1.8.5` is the current canonical closeout tag for the merged mainline
- closeout focus for this refresh:
  - this closeout slice is now landed on canonical `main`
  - the former local continuation lane is no longer local-only:
    - CI semantics now align to `pre-commit / pre-push / hosted / nightly / manual`
    - README/docs front door is compressed around `messy long context -> structured insight -> inspectable outcomes`
    - public package/version truth is aligned to `1.8.5`
    - local provenote rollback bundles have been cleared after release/tag truth stabilized on canonical `main`
- fresh verification evidence in this refresh:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_prepush_policy_contract.py tests/ci/test_distribution_readiness_contract.py tests/ci/test_public_artifact_prep_contract.py tests/ci/test_distribution_submission_packs.py tests/ci/test_required_checks_snapshot_contract.py tests/ci/test_public_distribution_surface_contract.py -q`
    - result: `89 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_workflow_policy.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_snapshot_freshness.py`
    - result: `PASS`
  - `make ci-local-preflight`
    - result: `PASS`
    - note: local host execution is now the default path; explicit repo-CI container rehearsal remains opt-in via `OPEN_NOTEBOOK_CI_FORCE_CONTAINER=1`
- blocker classification:
  - repo-owned closeout for this slice is complete on canonical `main`
  - remaining blockers are external-only:
    - GitHub-side advanced secret-scanning toggles that remained disabled after repo-owned PATCH attempt
    - custom social preview upload remains an owner-facing settings action, not a repo-side engineering gap

## 2026-04-05 Public Distribution Ladder + Submission Pack Sync

- current truth layer:
  - `main == origin/main == 7053c7d`
  - this section records the public-distribution closeout lane that promoted host starter bundles from vague local-prep wording to explicit claim-ladder truth and then tightened the registry prep boundary on `main`
  - the goal of this slice is:
    - keep `repo-owned prep`, `public-ready package available`, `publicly discoverable listing live`, and `official marketplace listing live` separated
    - finish every repo-side packaging/doc/proof task before leaving only external listing or publish buttons
- synced distribution package:
  - new shared claim-ladder and surface matrix now live in:
    - `docs/distribution.md`
    - `README.md`
    - `docs/project-status.md`
    - `docs/faq.md`
    - `docs/index.md`
    - `docs/mcp.md`
    - `docs/proof.md`
  - Claude Code and Codex starter bundles are now explicitly classified as:
    - `public-ready package available`
  - OpenClaw now has:
    - public-ready bundle-family wording in `examples/hosts/openclaw/README.md`
    - a repo-owned submission pack in `examples/hosts/openclaw/CLAWHUB_SUBMISSION.md`
    - a canonical ClawHub publish root in `examples/hosts/openclaw/clawhub/provenote-mcp-outcome-workflows/SKILL.md`
  - repo-owned directory/registry submission materials now exist for the non-live official surfaces:
    - `examples/hosts/claude-code/DIRECTORY_SUBMISSION.md`
    - `examples/hosts/codex/PLUGIN_DIRECTORY_SUBMISSION.md`
    - `examples/public-distribution/mcp-registry/README.md`
    - `examples/public-distribution/mcp-registry/server.json`
  - host example bundle readmes and contract surfaces were tightened together:
    - `examples/hosts/README.md`
    - `examples/hosts/claude-code/provenote-outcome-bundle/README.md`
    - `examples/hosts/codex/provenote-outcome-bundle/README.md`
    - `examples/hosts/cursor/provenote-outcome-bundle/README.md`
    - `examples/hosts/opencode/provenote-outcome-bundle/README.md`
    - `examples/hosts/openclaw/provenote-claude-bundle/README.md`
    - `examples/hosts/openclaw/provenote-cursor-bundle/README.md`
    - `examples/hosts/openclaw/provenote-codex-bundle/README.md`
- fresh verification evidence:
  - `.venv/bin/python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `.venv/bin/python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
  - `.venv/bin/pytest tests/ci/test_public_distribution_surface_contract.py -q`
    - result: `1 passed`
  - `.venv/bin/pytest tests/ci/test_distribution_readiness_contract.py tests/ci/test_distribution_submission_packs.py tests/ci/test_host_examples_contract.py tests/ci/test_host_surface_contract.py tests/test_mcp_server.py tests/test_operator_cli.py -q`
    - result: `56 passed`
  - `.venv/bin/ruff check services/api services/worker packages/core tooling/scripts`
    - result: `All checks passed!`
  - `.venv/bin/provenote status --json`
    - result:
      - entrypoints present: `provenote`, `provenote-mcp`
      - local API health: `connection refused` because the local stack was not running during this check
  - `.venv/bin/python tooling/scripts/ci/check_public_distribution_surface.py`
    - result: `PASS`
- blocker classification:
  - no evidence-backed repo-side blocker remains in the docs/bundle/submission-pack/contract lane
  - landed commit chain for this slice:
    - `78a5934 docs(distribution): add public-ready host packages and submission packs`
    - `4772dbf docs(distribution): tighten registry prep boundary`
    - `1acd043 docs(distribution): add submission packs and starter package proofs`
    - `5cec0af test(distribution): align registry readiness proof`
    - `7635d53 chore(agents): sync public distribution landing truth`
    - `1197cd0 test(distribution): mirror root registry metadata`
    - `7053c7d docs(distribution): sync task board and registry pack`
    - `1197cd0 test(distribution): mirror root registry metadata`
    - `7053c7d docs(distribution): sync task board and registry pack`
  - official listing publication is still external-only:
    - Anthropic directory submission if Anthropic exposes that path to the owner
    - any future official OpenAI Codex listing path once OpenAI exposes it
    - authenticated OpenClaw / ClawHub submission under the chosen owner account
    - authenticated MCP Registry publish flow plus a supported public artifact path
  - previously broader claims remain intentionally unclaimed:
    - official partnership / endorsement
    - live marketplace or directory status
    - public skills catalog
    - release publication / homepage / domain / trademark actions

## 2026-04-05 Docker + Host Starter Bundle + Registry Truth Sync

- current truth layer:
  - this section records the current closeout sync package that follows the landed `54708e1 -> 35eb72b -> 96cee6d -> 731f7fd -> 3bb564b -> 31d9556 -> f6606f4` spine
  - purpose:
    - keep public front-door wording, host starter artifacts, Docker build truth, and ledger surfaces aligned
- synced closeout package:
  - tracked host starter artifacts now form a clearer repo-owned install path:
    - `examples/hosts/README.md`
    - `examples/hosts/claude-code/provenote-outcome-bundle/README.md`
    - `examples/hosts/codex/provenote-outcome-bundle/README.md`
    - `examples/hosts/cursor/provenote-outcome-bundle/README.md`
    - `examples/hosts/opencode/provenote-outcome-bundle/README.md`
    - `examples/hosts/openclaw/README.md`
    - `examples/hosts/openclaw/provenote-claude-bundle/README.md`
    - `examples/hosts/openclaw/provenote-cursor-bundle/README.md`
    - `examples/hosts/openclaw/provenote-codex-bundle/README.md`
  - MCP and host compatibility wording stays in the repo-owned proof/prep lane instead of drifting into plugin, marketplace, or partnership claims:
    - `docs/mcp.md`
    - `docs/integrations/claude-code.md`
    - `docs/integrations/codex.md`
    - `docs/integrations/cursor.md`
    - `docs/integrations/openclaw.md`
    - `docs/integrations/opencode.md`
    - `README.md`
  - Docker runtime truth is now aligned with the app-local build output contract:
    - `ops/docker/Dockerfile`
    - `ops/docker/Dockerfile.single`
    - runtime stages copy:
      - `apps/web/.runtime-cache/build/next/standalone`
      - `apps/web/.runtime-cache/build/next/static`
  - registry-auth and release-proof guardrails are now explicit instead of implied:
    - `.github/workflows/build-dev.yml`
    - `.github/workflows/build-and-release.yml`
    - `tests/ci/test_build_dev_registry_auth_contract.py`
    - `tests/ci/test_build_registry_linkage_contract.py`
    - `tests/ci/test_registry_push_auth_contract.py`
    - `tests/ci/test_release_proof_contract.py`
  - authoritative public/project memory is being brought up to the same truth layer:
    - `CHANGELOG.md`
    - this task board
- fresh verification evidence:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_docker_frontend_build_contract.py tests/ci/test_frontend_size_limit_contract.py -q`
    - result: `2 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_build_dev_registry_auth_contract.py tests/ci/test_registry_push_auth_contract.py tests/ci/test_build_registry_linkage_contract.py tests/ci/test_release_proof_contract.py tests/ci/test_host_examples_contract.py tests/test_mcp_server.py -q`
    - result: passed
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_host_surface_contract.py tests/ci/test_host_examples_contract.py tests/test_mcp_server.py tests/test_operator_cli.py -q`
    - result: `40 passed`
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_workflow_policy.py`
    - result: `PASS`
  - `docker build -f ops/docker/Dockerfile --platform linux/amd64 --target runtime -t provenote-build-regular-test .`
    - result: succeeded with the app-local frontend artifact copy path
- blocker classification:
  - no code-level repo-side blocker is reproduced in the Docker, host-bundle, MCP, CLI, or docs drift surfaces covered above
  - latest remote required-check witness still needs one final fresh read after the closeout sync lands
  - external-only remainder remains unchanged:
    - release publish / keep-draft decision
    - homepage destination choice
    - domain / redirect
    - trademark / naming clearance
    - directory / marketplace submission
    - partnership / endorsement approval

## 2026-04-05 Root First Door + Host-Process Safety Landing

- current truth layer:
  - this section now records **merged/main truth**
  - current aligned landed head is:
    - `main == origin/main`
- landed continuation package:
  - app root first-door contract now aligns with the repo-documented product center:
    - `/` redirects to `/sources`
    - this keeps first entry on the `collect` side before notebook/process surfaces
  - local runtime start scripts now preserve fail-closed unsafe-record handling:
    - `tooling/scripts/dev/start_api_local.sh`
    - `tooling/scripts/dev/start_frontend_local.sh`
    - `tooling/scripts/dev/start_surreal_local.sh`
    - `tooling/scripts/dev/start_worker_local.sh`
    - unsafe pid-record state remains a hard stop instead of being swallowed by shell `if` status semantics
  - host-process safety is now explicitly guarded as repo-owned runtime truth:
    - new CI/runtime guard:
      - `tooling/scripts/ci/check_host_process_safety.py`
    - new contract coverage:
      - `tests/ci/test_host_process_safety_contract.py`
      - `tests/resource_management/test_local_runtime_start_scripts.py`
    - runtime/workflow wiring updated in:
      - `.github/workflows/test.yml`
      - `tooling/scripts/ci/pre_commit_lint.sh`
      - `tests/ci/test_runtime_governance_contracts.py`
      - `docs/development.md`
  - detached repo-owned Chrome launch now requires an explicit operator override:
    - `apps/web/scripts/real-chrome-profile.mjs`
    - override env:
      - `PROVENOTE_ALLOW_DETACHED_CHROME_LAUNCH=1`
  - tracked OpenClaw example-bundle skills now keep the repo-owned proof/prep boundary explicit and tested:
    - `examples/hosts/openclaw/provenote-claude-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md`
    - `examples/hosts/openclaw/provenote-cursor-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md`
    - `examples/hosts/openclaw/provenote-codex-bundle/skills/provenote-mcp-outcome-workflows/SKILL.md`
    - `tests/test_mcp_server.py`
    - `tests/ci/test_host_examples_contract.py`
  - public repo memory now records the landed continuation in:
    - `CHANGELOG.md`
- fresh verification evidence:
  - `npm --prefix apps/web test -- src/app/page.test.tsx`
    - result: `1 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/resource_management/test_local_runtime_start_scripts.py tests/resource_management/test_resource_cleanup.py tests/api/test_app_lifecycle.py tests/api/test_ui_tests_router.py tests/test_operator_cli.py tests/test_mcp_server.py -q`
    - result: `62 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_host_process_safety_contract.py tests/ci/test_runtime_governance_contracts.py -q`
    - result: `30 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_host_process_safety.py`
    - result: `PASS`
  - `npm --prefix apps/web test -- scripts/real-chrome-profile.test.ts`
    - result: `17 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_browser_manual_contract.py -q`
    - result: `9 passed`
  - `cd apps/web && npm test`
    - result: `161 files passed, 896 tests passed`
  - `make test-backend-cov`
    - result:
      - `1627 passed`
      - `coverage thresholds satisfied`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
- blocker classification:
  - no evidence-backed repo-side blocker remains inside this landed continuation package
  - external-only remainder from the landed closeout slices remains unchanged:
    - release publish / keep-draft decision
    - homepage destination choice
    - domain / redirect
    - trademark / naming clearance
    - directory / marketplace submission
    - partnership / endorsement approval

## 2026-04-05 Apps/Web Build-Path Contract Convergence

- current main truth:
  - `main == origin/main`
  - this slice converges the frontend build path contract onto project-local tool-constrained build roots
  - scope:
    - `apps/web/.runtime-cache/build/next`
    - `apps/web/.runtime-cache/build/next-playwright`
    - `apps/web/.runtime-cache/build/next-playwright-manual`
- landed contract package in this slice:
  - default `apps/web` Next build no longer points outside the project root
  - `start-server.js`, `playwright.config.ts`, `playwright.config.test.ts`, `tsconfig.json`, and `vitest.config.mts` now align with the same project-local build-root family
  - runtime/cache governance now explicitly allowlists those tool-constrained app-local build roots
  - `space-surfaces` and cleanup truth now track the Next cache at:
    - `apps/web/.runtime-cache/build/next/cache`
- fresh verification evidence:
  - `npm --prefix apps/web run build`
    - result: `PASS`
  - `npm --prefix apps/web test -- playwright.config.test.ts`
    - result: `3 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_output_path_policy.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_space_surfaces.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_space_surfaces_contract.py -q`
    - result: `11 passed`
- blocker classification:
  - the previous Next 16 / Turbopack `distDirRoot` failure is cleared
  - no new repo-side blocker remains for this build-path convergence slice

## 2026-04-05 Isolated Chrome Root + CDP 9342 Landing

- current main truth:
  - `main == origin/main`
  - landed runtime/browser implementation chain for this slice now includes:
    - `ebea448 feat(runtime): isolate repo chrome root and move CDP to 9342`
    - `ec91e32 fix(web): support CDP json/new tab attach on Chrome 146`
    - `5e70a45 fix(web): open attached target tabs via Playwright CDP`
    - `window identity layer landed in the canonical browser lane`
  - later ledger-only commits in this slice may continue normalizing wording without changing the landed runtime/browser contract
  - worktree state:
    - clean after final readback
  - open PR set:
    - `[]`
  - local branches:
    - only `main`
  - worktrees:
    - single visible worktree on `main`
  - release:
    - `v1.8.4` remains draft / unpublished
  - homepage:
    - still points to the GitHub docs index blob URL
- landed browser/runtime package in this slice:
  - repo-local real Chrome manual flow defaults to the isolated root:
    - `~/.cache/provenote/browser/chrome-user-data`
    - `Profile 1`
  - source migration contract is explicit:
    - source root defaults to `~/Library/Application Support/Google/Chrome`
    - source profile resolution still maps `provenote -> Profile 25`
    - migration rewrites the isolated target root to `Local State + Profile 1` only
  - manual browser lifecycle now locks to:
    - `start-or-attach`
    - single repo-owned Chrome instance
    - fixed CDP port `9342`
    - `.runtime-cache/browser/chrome-instance.json`
  - browser window identity layer now lands on the canonical lane:
    - generated identity page path: `.runtime-cache/browser-identity/index.html`
    - title shape: `<repo-label> · <cdp-port> · browser lane`
    - env overrides: `PROVENOTE_BROWSER_IDENTITY_LABEL` / `PROVENOTE_BROWSER_IDENTITY_ACCENT`
    - identity target is included on first launch and re-ensured on instance reuse
  - attach-time target opening now uses Playwright CDP page navigation:
    - avoids Chrome 146 `/json/new` blank-page drift when the repo-owned instance already exists
  - browser root remains repo-exclusive but outside auto-clean:
    - `machine-browser-chrome-user-data`
    - `default_action = do_not_clear`
    - excluded from TTL / root-cap / historical migration wipe
  - workstation browser threshold rule is now:
    - allow up to `6` active browser instances before blocking new repo-owned launches
- fresh verification evidence:
  - `cd apps/web && npm test -- scripts/shared/browser-instance-identity.test.ts scripts/real-chrome-profile.test.ts`
    - result: `17 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_browser_manual_contract.py -q`
    - result: `9 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_browser_manual_contract.py tests/ci/test_space_surfaces_contract.py tests/ci/test_machine_cache_cleanup_contract.py tests/ci/test_consistent_container_contract.py -q`
    - result: `45 passed`
  - `npm --prefix apps/web run lint`
    - result: `PASS`
  - `npm --prefix apps/web run browser:manual -- --dry-run`
    - result:
      - `identityPagePath` points to `.runtime-cache/browser-identity/index.html`
      - `identityLabel = provenote`
  - `npm --prefix apps/web run browser:manual:status`
    - result:
      - `expectedIdentityPagePath` points to `.runtime-cache/browser-identity/index.html`
      - CDP target list includes the generated `file://.../browser-identity/index.html` tab
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_space_surfaces.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_output_path_policy.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
  - `git diff --check`
    - result: clean
  - `npm --prefix apps/web run browser:manual:status`
    - result:
      - `attachable = true`
      - `expectedCdpUrl = http://127.0.0.1:9342`
      - `profileKey = Profile 1`
  - machine-local validation boundary:
    - one workstation-local migration and site/login witness run was completed during this landing
    - those results are intentionally not tracked here as repo-wide main truth
    - the exact target URL and account-level witness are intentionally excluded from this ledger
    - authoritative repo truth for this slice is limited to script/config/contract landing plus the attachable isolated Chrome instance contract
- final blocker classification after `ebea448`:
  - no new repo-side implementation wave remains for the isolated browser-root request
  - no new repo-side blocker remains
  - remaining work is external-only:
    - publish or keep-draft `v1.8.4`
    - homepage destination choice
    - domain / redirect
    - trademark / naming clearance
    - directory / marketplace submission
    - partnership / endorsement approval

## 2026-04-04 Governance Closeout After `993ce3a`

- current main truth:
  - `main == origin/main == 993ce3a`
  - governance unification commit:
    - `993ce3a chore(runtime): unify cache and browser governance`
  - worktree state:
    - clean
  - open PR set:
    - `[]`
  - release:
    - `v1.8.4` remains draft / unpublished
  - homepage:
    - still points to the GitHub docs index blob URL
- landed governance package in this slice:
  - repo-owned runtime/build/test outputs continue converging on `.runtime-cache`
  - repo-specific external caches stay under `~/.cache/provenote`
  - `machine_cache_policy.clearable_root_cap_bytes = 6442450944`
  - `historical-provenote-cache-candidates` remain migration-only and are entrypoint-cleaned by default
  - shared layers now explicitly include `~/.cache/uv` and remain advisory-only
  - local manual browser flow now supports the real Chrome `provenote` profile without polluting CI or the formal UI test API contract
  - `.serena/` is ignored as local MCP cache and excluded from governance
- fresh readback evidence:
  - `git status --short --branch`
    - result: `## main...origin/main`
  - `git log --oneline --decorate -n 1`
    - result: `993ce3a (HEAD -> main, origin/main) chore(runtime): unify cache and browser governance`
  - `git ls-remote origin refs/heads/main`
    - result: `993ce3ac0dc2f702318353e5ccdaa3af4cf0a11e refs/heads/main`
  - `gh pr list --state open --json number,title,headRefName,baseRefName,isDraft,url`
    - result: `[]`
  - `gh release view v1.8.4 --json name,tagName,isDraft,isPrerelease,url,targetCommitish`
    - result:
      - `isDraft = true`
      - `tagName = v1.8.4`
      - `targetCommitish = main`
  - `gh repo view --json nameWithOwner,homepageUrl,defaultBranchRef,description`
    - result:
      - `nameWithOwner = xiaojiou176-open/provenote`
      - `defaultBranchRef.name = main`
      - `homepageUrl = https://github.com/xiaojiou176-open/provenote/blob/main/docs/index.md`
- final blocker classification after `993ce3a`:
  - no new repo-side implementation wave remains for the approved governance plan
  - no new repo-side blocker remains
  - remaining work is external-only:
    - publish or keep-draft `v1.8.4`
    - homepage destination choice
    - domain / redirect
    - trademark / naming clearance
    - directory / marketplace submission
    - partnership / endorsement approval

## 2026-04-04 Final Live-Main Truth Sync After #60

- current main truth:
  - `main == origin/main == 9bdb39e`
  - merged/main closeout chain now includes:
    - `#56` safe maintenance replacement plus truth sync
    - `#57` frontend coverage recovery
    - `#58` first attempt to downgrade broken cache export
    - `#59` final image-workflow hardening
    - `#60` final blocker truth sync
  - open PR set:
    - `[]`
  - release `v1.8.4` remains draft / unpublished
  - homepage still points to the GitHub docs index blob URL
  - local Git residue:
    - no stash
    - no extra local branches
    - no extra worktrees
  - remote tracking residue:
    - only `origin/main` remains after `git fetch --prune origin`
- fresh readback evidence:
  - `git status --short --branch`
    - result: `## main...origin/main`
  - `git worktree list --porcelain`
    - result: single visible worktree on `main`
  - `git branch -vv`
    - result: only `main`
  - `git ls-remote origin refs/heads/main`
    - result: `9bdb39e60e1ef3534b1077120b672e827dd61e21 refs/heads/main`
  - `gh pr list --state open --json number,title,headRefName,baseRefName,isDraft,url`
    - result: `[]`
  - `gh repo view --json nameWithOwner,homepageUrl,defaultBranchRef,description`
    - result:
      - `nameWithOwner = xiaojiou176-open/provenote`
      - `defaultBranchRef.name = main`
      - `homepageUrl = https://github.com/xiaojiou176-open/provenote/blob/main/docs/index.md`
  - `gh release view v1.8.4 --json name,tagName,isDraft,isPrerelease,url,targetCommitish`
    - result:
      - `isDraft = true`
      - `tagName = v1.8.4`
      - `targetCommitish = main`
  - `gh run list --commit 9bdb39e60e1ef3534b1077120b672e827dd61e21 --limit 20 --json databaseId,name,displayTitle,status,conclusion,headSha,event,createdAt,url`
    - result: `[]`
- landed repo-side recoveries in this final closeout slice:
  - host artifact Git contract is repaired
  - `apps/web` dependency family is aligned:
    - `vitest 4.1.2`
    - `@vitest/ui 4.1.2`
    - `@vitest/coverage-istanbul 4.1.2`
    - `@vitest/coverage-v8 4.1.2`
    - `@tailwindcss/postcss 4.2.2`
    - `lucide-react 1.7.0`
  - frontend line coverage is restored above gate:
    - `95.02%`
  - `#39` and `#44` are superseded and closed
  - `#46` is deferred and closed as a Vite 8 toolchain migration lane
- final blocker classification:
  - product-spine repo-side work is complete
  - Git / PR / stash / worktree residue is complete
  - current remaining blocker is now external/platform, not repo-code:
    - `#60` itself is a task-board truth-sync commit and does not add a new workflow witness
    - latest relevant workflow evidence still comes from `Development Build` run `23987814523` on workflow-bearing head `763e5ab`
    - `build-regular` and `build-single` both still fail only at GHCR push time after image build/export succeeds
    - latest failed-log witness shows GHCR responds `403 Forbidden` on blob HEAD while pushing:
      - `ghcr.io/xiaojiou176-open/provenote:v1-dev`
      - `ghcr.io/xiaojiou176-open/provenote:v1-dev-single`
  - owner/external remainder remains:
    - publish or keep-draft `v1.8.4`
    - homepage destination choice
    - domain / redirect
    - trademark / naming clearance
    - directory / marketplace submission
    - partnership / endorsement approval

## 2026-04-04 Historical Local Continuation Slice Before PR #50

- current truth layer:
  - `main == origin/main == b3098b7`
  - at this time the worktree carried validated local truth beyond the landed closeout chain below
  - at this time the slice was **current local truth only**; it was not yet merged/main truth, release truth, or public-distribution truth
  - live GitHub drift changed since the earlier zero-open-PR snapshot:
    - open PRs are no longer `[]`
    - current open PR set is a Dependabot maintenance lane (`#37` through `#49` in the latest fetch)
    - classify these as maintenance drift, not as reopened Prompt 14 / N6 / N7 product blockers
- current local continuation package:
  - host/operator proof surfaces strengthened:
    - tracked host example family under `examples/hosts/`
    - host contract tests under `tests/ci/test_host_examples_contract.py` and `tests/ci/test_host_surface_contract.py`
    - operator CLI health gate carry-forward in `packages/core/operator/cli.py` and `tests/test_operator_cli.py`
    - Cursor host bundle now explicitly unignores `.cursor/commands/provenote-mcp-outcome-workflows.md` so the checked-in host example is visible to `git status` / `git add`, not silently dropped by the root `.gitignore` `.cursor/` rule
  - runtime probe stabilization carry-forward:
    - `packages/core/ai/connection_tester.py` now keeps the startup probe on the stable fast-path default (`gemini-2.5-flash`) instead of the stale `gemini-3.1-pro` default
    - `packages/core/ai/google_genai_adapter.py` now normalizes SDK-thrown model-404 errors into the existing `API key valid (test model not available)` semantic result instead of letting startup crash before fallback can run
    - paired regression coverage lives in `tests/api/test_gemini_startup_probe.py` and `tests/test_google_genai_adapter.py`
  - web metadata / front-door carry-forward:
    - `apps/web/src/app/layout.tsx`
    - `apps/web/src/app/robots.ts`
    - `apps/web/src/app/manifest.ts`
    - paired tests for layout / robots / manifest
  - journey continuity carry-forward:
    - search page keeps `ResearchCapturePanel` as a secondary continuity surface instead of the first-screen primary task
    - notebook draft lane now targets the real recommended / bridge cards instead of stale hidden thread-card anchors
    - source multi-notebook outcome CTA stays draft-first (`choose notebook for the draft`) instead of degrading to generic notebook management language
- fresh evidence for this current-local slice:
  - `git diff --check`
    - result: clean
  - `npm --prefix apps/web run lint`
    - result: `PASS`
  - `npm --prefix apps/web test -- src/app/layout.test.tsx src/app/page.test.tsx src/app/robots.test.ts src/app/manifest.test.ts src/app/(dashboard)/search/page.test.tsx src/components/notebooks/NotebookDraftPanel.test.tsx src/components/notebooks/ResearchThreadsPanel.test.tsx src/components/source/SourceInsightDialog.test.tsx src/components/source/SourceInsightsTab.test.tsx src/components/source/SourceOutcomeJourneyCard.test.tsx`
    - result: `77 passed`
  - `npm --prefix apps/web test -- src/app/layout.test.tsx src/app/page.test.tsx src/app/manifest.test.ts src/app/robots.test.ts src/app/(dashboard)/search/page.test.tsx src/components/notebooks/NotebookDraftPanel.test.tsx src/components/notebooks/ResearchThreadsPanel.test.tsx src/components/source/SourceInsightDialog.test.tsx src/components/source/SourceInsightsTab.test.tsx src/components/source/SourceOutcomeJourneyCard.test.tsx src/components/search/ResearchCapturePanel.test.tsx`
    - result: `80 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run pytest tests/test_operator_cli.py tests/test_mcp_server.py tests/ci/test_host_examples_contract.py tests/ci/test_host_surface_contract.py -q`
    - result: `29 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api/test_gemini_startup_probe.py tests/test_google_genai_adapter.py -q`
    - result: `24 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_host_examples_contract.py tests/ci/test_host_surface_contract.py -q`
    - result: `12 passed`
  - repo-owned live runtime proof:
    - `docker run -d --name provenote-surreal-e2e -p 38080:8000 surrealdb/surrealdb:v2.3.10 start --log warn --user root --pass root memory`
      - result: local Surreal witness container available on `127.0.0.1:38080`
    - `env GEMINI_MODEL=gemini-2.5-flash API_PORT=35055 API_HOST=127.0.0.1 bash tooling/scripts/runtime/run_uv_managed.sh run --env-file .env python tooling/bin/run_api.py`
      - result: foreground API witness run becomes healthy against the current continuation package
    - `curl -fsS http://127.0.0.1:35055/health`
      - result: `{\"status\":\"healthy\"}`
    - `bash tooling/scripts/runtime/run_uv_managed.sh run provenote --api-base http://127.0.0.1:35055 status --json --require-healthy`
      - result: `healthy=true`
- blocker classification for this continuation slice:
  - no fresh evidence-backed repo-side blocker remains inside the current local truth package above
  - previously active repo-side blockers now reduced to fixed or downgraded states:
    - Gemini startup probe crash is resolved inside the current local truth package
    - Cursor host bundle git-visibility residual is resolved inside the current local truth package
    - `start_api_local.sh` was not used as the authoritative final witness because it hard-sources local `.env` before launching; the repo-owned healthy proof above uses direct `run_uv_managed.sh --env-file .env` plus explicit runtime overrides so local workstation drift does not masquerade as repo code failure
  - remaining non-local blockers stay outside repo-side execution:
    - publish or keep-draft decision for `v1.8.4`
    - homepage destination choice
    - domain / redirect execution
    - trademark / naming clearance
    - directory or marketplace submission
    - partnership or endorsement approval

## 2026-04-04 Final Push Closure + Resource Hygiene + Browser Discipline Landing

- current truth layer:
  - `main == origin/main`
  - current aligned head before this task-board-only sync: `1402f1f`
  - this turn treated Prompt 14 landing as already complete and only finished the remaining closure surfaces
  - later task-board-only sync commits should preserve this aligned-main truth instead of rewriting the product conclusion
  - the later `AGENTS.md` browser-discipline hardening is workstation-governance follow-through, not a reopened repo-side product backlog
- landed closeout chain after Prompt 14:
  - `c82935c docs(agents): add workstation hygiene guardrails`
  - `fc74a73 docs(agents): tighten closeout write boundaries`
  - `4ef9784 chore(agents): sync final push live truth ledger`
  - `a5e1bc0 refactor(mcp): extract validation helpers`
  - `e952452 chore(runtime): tighten resource hygiene governance (#34)`
  - `000d710 chore(agents): sync final push closure ledger`
  - `1a22be0 chore(agents): sync final push closure ledger`
  - `1402f1f docs(agents): add browser discipline stop rules`
- current repo-side closeout interpretation:
  - no still-actionable Prompt 14 / N6 / N7 repo-side blocker remains
  - Git / GitHub closeout tails are reduced to zero open PRs and zero remaining `codex/*` remote branches
  - browser / Docker hygiene is ownership-first:
    - no current-task-owned browser/profile residue required cleanup
    - other-repo browser resources remain off-limits
    - current repo Docker containers were started for final runtime smoke, verified, and then removed, so no current-task-owned Docker residue remains
- external-only remainder after final push:
  - publish or keep-draft decision for `v1.8.4`
  - homepage destination choice
  - domain / redirect execution
  - trademark / naming clearance
  - directory or marketplace submission
  - partnership or endorsement approval

## 2026-04-03 Prompt 14 Landed Truth + External Execution

- current truth layer:
  - `main == origin/main`
  - Prompt 13 repo-side package is no longer local-only or merge-ready-only; it is landed truth on the main branch
  - landed commit chain:
    - `080f27e docs: land ecosystem truth and external boundary`
    - `6266874 docs: refresh landing copy and changelog`
    - `5749403 docs: record prompt14 landed truth`
    - `d3cd4aa chore: restore auditable wrapper formatting`
    - `85c754b chore(agents): sync prompt14 PR-ready ledger`
    - `bd17665 chore(agents): record prompt14 landed truth`
    - `f5aa90b chore(agents): sync prompt14 landed head`
    - `9ff73b1 chore(agents): stabilize prompt14 landed ledger wording`
    - `8fcb4ec chore(agents): sync prompt14 live truth ledger`
  - latest aligned head at Prompt 14 closeout time: `8fcb4ec`
  - this section is the 2026-04-03 landing slice; the 2026-04-04 sections above carry forward later aligned-main heads and closeout-only follow-through
  - any later task-board-only sync commit should preserve this aligned-main truth instead of rewriting the product conclusion
- landed repo-side package:
  - `README.md`
  - `CHANGELOG.md`
  - `docs/brand-domain.md`
  - `docs/faq.md`
  - `docs/index.md`
  - `docs/mcp.md`
  - `docs/project-status.md`
  - `docs/proof.md`
  - `packages/core/application/outcome_client_mixin.py`
  - `packages/core/mcp/server.py`
  - `tooling/scripts/ci/pre_commit_lint.sh`
  - this task board
- Prompt 14 cleanup decisions:
  - removed `docs/ecosystem-boundary.md`
    - redundant standalone public page; boundary guidance now lives inside existing authoritative docs
  - reverted `docs/quickstart.md` carry-forward addition
    - Prompt 13 itself had already classified quickstart as coherent and out of scope
  - restored `tooling/scripts/run_auditable_markdown.py`
    - accidental blank-line-only deletion should not remain as landed truth
- fresh landed-closeout evidence at the 2026-04-03 slice:
  - `git status --short --branch`
    - result: `## main...origin/main`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_operator_cli.py tests/test_mcp_server.py -q`
    - result: `17 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run provenote status --json`
    - result:
      - local API health: `healthy`
      - entrypoints: `provenote`, `provenote-mcp`
      - inspect surfaces: `notebook`, `draft`, `research_thread`, `auditable_run`
      - operator workflows: `research-thread-to-draft`, `auditable-markdown`
  - `bash tooling/scripts/ci/pre_commit_lint.sh --mode runtime`
    - result: `PASS`
- remote truth at the 2026-04-03 landing slice:
  - `git ls-remote origin refs/heads/main`
    - result: `8fcb4ece630d333b0257f01f6ac68f9a3b28673c`
  - `gh repo view`:
    - repo: `xiaojiou176-open/provenote`
    - default branch: `main`
    - homepage: GitHub docs index
  - `gh release view v1.8.4`:
    - release exists as draft
    - unpublished
    - target: `main`
  - `gh pr list`:
    - open PRs: `[]`
- external-only remainder after landing:
  - publish or keep-draft decision for `v1.8.4`
  - homepage destination choice
  - domain / redirect execution
  - trademark / naming clearance
  - directory or marketplace submission
  - partnership or endorsement approval

## 2026-04-03 Prompt 13 Final-Phase Merge: N6 + N7 + External Window (historical local-ready snapshot)

- prompt focus:
  - `N6 ecosystem truth wave`
  - `N7 growth system wave`
  - `External Window exact unblock pack`
- concurrency preflight:
  - `git status --short --branch`
    - result: `## main...origin/main`
  - `git worktree list --porcelain`
    - result: single visible worktree on `main`
  - `git branch -vv`
    - result: `* main 4795a51 [origin/main] test(operator): align status surface assertion`
  - `git diff --check`
    - result: clean before this prompt's edits
- scope decision:
  - do **not** reopen `N1` through `N5`
  - do **not** revive the old release-grade `Prompt 13 Zero-Excuse Final Push` section below as current truth
  - do **not** pull Switchyard back into the active wave
  - current naming for this final-phase pass is:

  | Current working label | Meaning in this prompt | Notes |
  | --- | --- | --- |
  | `N6` | ecosystem truth wave | OpenClaw, plugin / marketplace, public skills, host / CLI / MCP boundary |
  | `N7` | growth system wave | README / index / proof / status / FAQ / quick-result routing coherence |
  | `External Window` | release / listing / domain / trademark / partnership prep | exact unblock pack only; owner/external actions stay external |
- current truth snapshot:
  - `N1` long-context front door remains landed on `main`
  - `N2` structured insight continuity remains landed on `main`
  - `N3` truthful host compatibility remains landed on `main`
  - `N4` Prompt 10 + Prompt 11 truth-promotion / first-entry continuity remains landed on `main`
  - `N5` first-party operator CLI remains landed on `main`
  - this prompt is therefore a truth-and-growth closeout pass, not a feature-core reopen
- N6 ecosystem truth package prepared in current local truth:
  - public docs now explicitly separate:
    - host compatibility pages via MCP
    - first-party `provenote` CLI
    - absent public skills surface
    - OpenClaw local example bundles plus a public non-claim
    - plugin / marketplace / listing as non-claims or external-only
  - touched tracked docs:
    - `README.md`
    - `docs/project-status.md`
    - `docs/proof.md`
    - `docs/faq.md`
    - `docs/mcp.md`
- N7 growth system package prepared in current local truth:
  - docs routing now makes the front door clearer for:
    - messy long context users
    - proof-first evaluators
    - coding-agent / MCP users
    - operator / CLI users
  - touched tracked docs:
    - `README.md`
    - `docs/index.md`
    - `docs/project-status.md`
    - `docs/proof.md`
    - `docs/faq.md`
- External Window prep prepared in current local truth:
  - authoritative workspace-local package:
    - `.agents/Plans/2026-04-03__provenote-prompt13-n6-n7-external-window-closeout.md`
  - purpose:
    - exact owner / external action matrix
    - ready copy and safe wording
    - explicit separation between repo-ready and owner-button work
    - current remote snapshot and owner playbook
    - post-action verification checklist
- fresh evidence:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_operator_cli.py tests/test_mcp_server.py -q`
    - result: `17 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run provenote status --json`
    - result:
      - local API health: `healthy`
      - entrypoints: `provenote`, `provenote-mcp`
      - inspect surfaces: `notebook`, `draft`, `research_thread`, `auditable_run`
      - operator workflows: `research-thread-to-draft`, `auditable-markdown`
  - isolated runtime/type gate follow-up:
    - isolated-cache `pre_commit_lint.sh --mode runtime`: `PASS`
    - isolated managed-cache `sync --frozen --extra dev`: `PASS`
    - isolated runtime `ruff`: `PASS`
    - isolated runtime `mypy`: `PASS`
    - isolated runtime governance gates: `PASS`
    - repo-side type gaps fixed in:
      - `packages/core/application/outcome_client_mixin.py`
      - `packages/core/mcp/server.py`
      - `tooling/scripts/ci/pre_commit_lint.sh`
- reviewer truth:
  - no independent reviewer token was available in this turn
  - blocker-only self-review found:
    - no scope drift into Switchyard, hosted/team/autopilot, or fake marketplace/plugin claims
    - no host guide promoted into product-center wording
    - no evidence that public docs now overclaim OpenClaw or public skills support
- final interpretation:
  - repo-side N6 work is complete in the current local truth package for the current truthful public surface
  - repo-side N7 work is complete in the current local truth package as a minimal system, not a new pile of pages
  - once this package is committed, pushed, and remote-confirmed, remaining work should reduce to exact owner / external actions recorded in the Prompt 13 closeout artifact
  - the older release-grade `Prompt 13 Zero-Excuse Final Push` section below is historical under a different scope and must not override this stronger-vision closeout

## 2026-04-03 Prompt 12 Closeout + N5 Operator Surface

- prompt focus:
  - `N1/N2, N3, N4 closeout ledger sync`
  - `N5 first-party operator / CLI / skills-ready surface`
- concurrency preflight:
  - `git status --short --branch`
    - result: `## main...origin/main`
  - `git worktree list --porcelain`
    - result: single visible worktree on `main`
  - `git branch -vv`
    - result: `* main 81faedb [origin/main] feat(web): clarify long-context first-entry ladder`
  - `git diff --check`
    - result: clean
- wave mapping table:

  | Old artifact naming | Current repo truth | This-round working naming | Notes |
  | --- | --- | --- | --- |
  | `N1` | long-context front door is already landed on `main` | `N1` | unchanged |
  | `N2` | structured insight -> outcome continuity is already landed on `main` | `N2` | unchanged |
  | `N3` | safe host expansion, especially OpenCode via MCP, is already landed on `main` | `N3` | unchanged |
  | `N4` | Prompt 10 + Prompt 11 closeout is already landed on `main` through `720711d` and `81faedb` | `N4` | this round only needs closeout sync, not a reopen |
  | `N4` (older master-plan label) | historical label for `CLI / skills / operator surface` | `N5` | remapped this round so Prompt 10/11 closeout and operator completion do not collide |
  | `N5` (older master-plan label) | external distribution, listing, domain, trademark, partnership decisions | `Deferred endgame` | remains outside this repo-side completion wave |
- merged closeout ledger:

  | Wave | Task complete | Merged/main truth | Public truth | Release/distribution truth |
  | --- | --- | --- | --- | --- |
  | `N1` | yes | yes | yes | no |
  | `N2` | yes | yes | yes | no |
  | `N3` | yes | yes | yes | no |
  | `N4` | yes | yes, through `720711d` and `81faedb` | yes | no |
  | `N5` | yes | carried by this prompt's tracked diff | carried by this prompt's tracked docs and runbook | no |
- N1 / N2 / N3 / N4 current interpretation:
  - `N1` is long-context first-entry truth on `main`, not an open front-door backlog
  - `N2` is structured insight continuity on `main`, not a direct `insight -> draft` reopen
  - `N3` is host-compatibility truth on `main`, not plugin/marketplace/public-distribution truth
  - `N4` is Prompt 10 + Prompt 11 already landed, so this round only closes stale artifact wording and continuity ledger drift
- N5 surface decision:
  - build one narrow first-party operator CLI instead of renaming `provenote-mcp`
  - strongest honest path:
    - `inspect current outcome object state`
    - `source -> auditable markdown`
    - `research_thread -> draft -> verify/download`
  - first-party command name:
    - `provenote`
  - why this is the right shape:
    - it operates on real outcome objects
    - it exposes one inspect lane and one non-toy action lane
    - it stays inside the current product center instead of becoming a plugin/store fantasy
- endgame deferred ledger:

  | Item | Classification | Notes |
  | --- | --- | --- |
  | OpenClaw | deferred by design | no repo-backed host proof in this wave |
  | plugin / marketplace | deferred by design | not a repo-backed claim surface today |
  | SEO / landing / promo / video / external heat | implemented but not this wave's focus | public docs exist, but external growth work remains separate |
  | release / listing / domain / trademark / partnership | blocked by genuine external dependency | owner/external decision layer only |

## 2026-04-04 Prompt 10 + Prompt 11 Merged Strike

- prompt focus:
  - `Prompt 10 truth-promotion / authoritative sync`
  - `Prompt 11 long-context first-entry unification`
- concurrency preflight:
  - `git status --short --branch`
    - result: `## main...origin/main`
  - `git worktree list --porcelain`
    - result: single visible worktree on `main`
  - `git branch -vv`
    - result: `* main 81faedb [origin/main] feat(web): clarify long-context first-entry ladder`
  - `git diff --check`
    - result: clean
- merged truth-promotion ledger:
  - `Prompt 7`
    - `task complete`: yes
    - `implemented in current local truth`: yes
    - `merged/main truth`: yes
    - `public truth`: yes, through docs already on `main`
    - `release/distribution truth`: no
  - `Prompt 8`
    - `task complete`: yes
    - `implemented in current local truth`: yes
    - `merged/main truth`: yes, now retained on `81faedb`
    - `public truth`: yes, for the tracked docs now on `main`
    - `release/distribution truth`: no
  - `Prompt 9`
    - `task complete`: yes
    - `implemented in current local truth`: yes
    - `merged/main truth`: yes, now retained on `81faedb`
    - `public truth`: yes, for the tracked docs now on `main`
    - `release/distribution truth`: no
- authoritative-artifact correction:
  - the Prompt 8 and Prompt 9 sections below remain valuable as historical same-turn records
  - they are **not** the current truth layer for merge status anymore
  - read any `current local truth only` wording in those historical sections as pre-promotion history, not current repo truth
  - merged strike authoritative handoff:
    - `.agents/Plans/2026-04-04__provenote-prompt10-11-merged-truth-promotion-and-long-context-first-entry.md`
    - this handoff file lives under ignored `.agents/` operator space and is a workspace-local package, not merged/main or public truth by itself
- N4 long-context first-entry decision:
  - no new backend contract is needed for this wave
  - the sharpest remaining repo-side gap is first-entry clarity and continuity:
    - `long messy context`
    - `-> structured insight`
    - `-> note / research thread / draft-adjacent notebook lane`
  - OpenCode remains a host surface, not the product center
- what landed in Prompt 11 merged/main truth:
  - public docs now point more directly to:
    - `messy long context`
    - `-> Chat Knowledgeization`
    - `-> note / seeded Ask lane / notebook research thread`
    - `-> draft-adjacent notebook work`
  - `LongContextTransformationStarter.tsx` now surfaces the first-entry route inside the starter card
  - `SourceInsightsTab.tsx` now exposes note / research / research-thread continuation directly from the insight list
  - `SourceInsightDialog.tsx` now surfaces the same next-lane guidance and puts `Save as note` ahead of broader research actions
  - touched `en-US` / `zh-CN` locale copy now carries the same continuity ladder
- fresh evidence:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py -q`
    - result: `12 passed`
  - `cd apps/web && npm test -- --run 'src/app/(dashboard)/transformations/components/LongContextTransformationStarter.test.tsx' 'src/app/(dashboard)/transformations/page.test.tsx' 'src/components/source/SourceInsightsTab.test.tsx' 'src/components/source/SourceInsightDialog.test.tsx' 'src/components/source/SourceDetailContent.test.tsx'`
    - result: `5 files passed, 45 tests passed`
- blocker-only reviewer verdict:
  - no independent reviewer token captured in this turn
  - blocker-only self-review found no evidence-backed blocker or scope drift
- authoritative artifact update:
  - `.agents/Plans/2026-04-04__provenote-prompt10-11-merged-truth-promotion-and-long-context-first-entry.md`
- next worker should start here:
  - treat Prompt 7, Prompt 8, and Prompt 9 as **merged/main truth**
  - treat public docs in `main` as public truth surfaces
  - do **not** inflate that into release/distribution truth
  - treat the Prompt 11 first-entry slice as **merged/main truth** on `81faedb`
  - continue from N4 first-entry and continuity strengthening, not host expansion

## 2026-04-04 Stronger-Vision Prompt 9

> Historical note:
> This section records the Prompt 9 same-turn state before later truth promotion.
> Current repo truth is now `HEAD == origin/main == 81faedb`, which retains Prompt 9 as merged/main truth.

- prompt focus:
  - `Prompt 8 inherited local truth audit + N3 OpenCode proof-hardening`
- concurrency preflight:
  - `git status --short --branch`
    - result: `## main...origin/main`
  - `git worktree list --porcelain`
    - result: single visible worktree on `main`
  - `git branch -vv`
    - result: `* main 206c316 [origin/main] Merge pull request #29 from xiaojiou176-open/codex/prompt6-n2-continuity-closeout`
  - `git diff --check`
    - result: clean
- inherited Prompt 8 local truth ledger:
  - current local truth still lives in:
    - `docs/integrations/opencode.md`
    - `docs/mcp.md`
    - `docs/proof.md`
    - `docs/project-status.md`
    - `docs/index.md`
    - `docs/faq.md`
    - `README.md`
    - `.agents/Tasks/TASK_BOARD-provenote-full-rollout.md`
  - Prompt 8 artifact self-description matches the actual doc surface at a high level:
    - OpenCode is still framed as `compatibility through MCP`
    - Prompt 7 remains treated as `merged/main truth`
    - Prompt 8 was `implemented in current local truth only` at the original Prompt 9 turn
  - no evidence-backed mixed-layer blocker was found, but the docs surface still needed a stronger self-verify loop so it did not read like a standalone integration page floating without proof
- OpenCode claim boundary recheck:
  - safe now:
    - `Provenote works with OpenCode via MCP`
    - OpenCode docs expose an `mcp` config section
    - OpenCode docs describe adding local and remote MCP servers
    - Provenote ships `provenote-mcp` and concrete `draft.*` / `research_thread.*` / `auditable_run.*` tool families
  - still not claimed:
    - official partnership
    - bundled OpenCode integration
    - plugin or marketplace listing
    - generic `works with every MCP host`
- what landed in Prompt 9 current local truth:
  - `docs/integrations/opencode.md` now includes a repo-backed proof loop:
    - check `provenote-mcp`
    - inspect outcome-tool families
    - start local runtime
    - connect OpenCode
    - verify a narrow list/read action before write actions
  - `docs/proof.md` now includes a proof-map row and a short compatibility-proof section for the OpenCode self-verify loop
  - `docs/mcp.md` and `docs/project-status.md` now point to the narrower setup-and-verify path so the OpenCode page reads as a proof surface, not a marketing island
  - `docs/index.md` and `docs/faq.md` remain inherited Prompt 8 routing surfaces; Prompt 9 did not reopen them
  - new authoritative artifact:
    - `.agents/Plans/2026-04-04__provenote-prompt9-n3-proof-hardening.md`
  - `README.md` was intentionally left untouched in this Prompt 9 slice
- fresh evidence:
  - repo/code anchors:
    - `pyproject.toml`
      - result: `provenote-mcp = "packages.core.mcp.server:main"`
    - `packages/core/mcp/server.py`
      - result: outcome-first tool groups `draft.*`, `research_thread.*`, `auditable_run.*` are present
    - `packages/core/mcp/schemas.py`
      - result: typed request schemas back those outcome groups
    - `tests/test_mcp_server.py`
      - result: MCP contract coverage exists for tool registration and stdio entrypoint truth
    - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py -q`
      - result: `12 passed`
  - official OpenCode docs rechecked in this turn:
    - `https://opencode.ai/docs/config/`
      - result: public config page with `opencode.json` and `mcp` config coverage
    - `https://opencode.ai/docs/mcp-servers/`
      - result: public MCP servers page describing local and remote MCP tools
    - `https://opencode.ai/brand`
      - result: public brand page exists for descriptive name usage
  - docs verification:
    - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
      - result: `PASS`
    - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
      - result: `PASS`
  - blocker-only reviewer over the Prompt 9 docs/artifact diff
    - result: unavailable in this session; blocker-only self-review found no evidence-backed blocker or scope drift
- scope discipline:
  - did **not** reopen N2 implementation
  - did **not** expand to OpenClaw / plugin / marketplace / CLI / skills
  - did **not** turn OpenCode into the product center
  - at the time of Prompt 9, it did **not** yet promote current local truth into merged/main truth
- next worker should start here:
  - treat Prompt 9 as a truthful hardening slice on top of Prompt 8, not a new host-expansion wave
  - keep the strongest current interpretation:
    - Prompt 7 = merged/main truth
    - Prompt 8 + Prompt 9 were current local truth only **at that time**
    - current repo truth now retains Prompt 8 + Prompt 9 as merged/main truth on `81faedb`
  - if Prompt 10 opens, prefer another narrow proof/inspection hardening slice over host portfolio expansion

## 2026-04-03 Stronger-Vision Prompt 8

> Historical note:
> This section records the Prompt 8 same-turn state before Prompt 9 and the later merge promotion now retained on `81faedb`.
> Current repo truth now treats Prompt 8 as merged/main truth.

- prompt focus:
  - `Prompt 7 truth promotion + N3 truthful OpenCode compatibility first cut`
- concurrency preflight:
  - `git status --short --branch`
    - result: `## main...origin/main`
  - `git worktree list --porcelain`
    - result: single visible worktree on `main`
  - `git branch -vv`
    - result: `* main 206c316 [origin/main] Merge pull request #29 from xiaojiou176-open/codex/prompt6-n2-continuity-closeout`
- starting repo truth:
  - PR #29 is already merged, so Prompt 7 is no longer branch-local truth
  - current `main` and `origin/main` are aligned at `206c316`
  - there is no visible second local L1 write lane in this repo snapshot
- Prompt 7 truth promotion ledger:
  - the Prompt 7 N2 convergence slice is now **merged/main truth**
  - N2 is now **closed at merged/main truth** for repo-side actionable scope
  - the Prompt 7 reviewer timeout remains a historical process fact, not a new repo-side blocker
  - public/release truth stays separate from merged/main truth
- what landed in Prompt 8 current local truth:
  - added `docs/integrations/opencode.md` as a repo-backed OpenCode compatibility-through-MCP page
  - wired OpenCode into `docs/mcp.md`, `docs/index.md`, `docs/faq.md`, and `docs/project-status.md`
  - applied a minimal front-door consistency sync in `README.md` and `docs/proof.md` so the new host surface is not hidden behind stale three-host wording
  - kept the wording at `compatibility through MCP`, not partnership/plugin/marketplace language
- OpenCode claim boundary:
  - safe now:
    - `Provenote works with OpenCode via MCP`
    - `OpenCode can register local and remote MCP servers`
    - `Provenote ships a first-party stdio MCP entrypoint`
  - not claimed:
    - official partnership
    - bundled OpenCode integration
    - marketplace/plugin-store listing
    - generic `works with every MCP host`
- fresh evidence:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
  - blocker-only reviewer over the Prompt 8 docs/artifact diff
    - result: `APPROVE`
  - official OpenCode docs checked during this turn:
    - `https://opencode.ai/docs/config/`
      - result: documents the `mcp` config section
    - `https://opencode.ai/docs/mcp-servers/`
      - result: documents adding local and remote MCP tools
    - `https://opencode.ai/brand`
      - result: public brand page exists for descriptive name usage
- next worker should start here:
  - treat Prompt 7 as historical landed truth, not an active N2 implementation backlog
  - historical at-turn note:
    - the new OpenCode docs surface started as **current local truth only**
  - current repo truth:
    - the Prompt 8 compatibility slice is now merged/main truth on `81faedb`
  - keep follow-up work on truth discipline and long-context product-center strengthening, not plugin/marketplace/OpenClaw expansion

## 2026-04-03 Stronger-Vision Prompt 7

- prompt focus:
  - `truthful insight -> draft-adjacent bridge + N2 final convergence`
- chosen continuity slice:
  - `save insight to research thread -> notebook draft lane handoff`
- why this slice beat the alternatives:
  - Prompt 6 already made `research_thread -> first draft` legible inside the notebook lane, but users arriving from a freshly structured insight still had no explicit "this is your next draft seed" bridge
  - the strongest remaining N2 gap was therefore not a new capability or backend contract; it was continuity, discoverability, and truthful handoff between the saved insight-origin thread and the notebook draft lane
  - this slice keeps the product boundary honest by routing source-side continuity into the notebook lane instead of inventing a fake direct `insight -> draft` shortcut or turning `SourceInsightDialog` into a draft launcher
- what landed:
  - saving an inspected insight into a notebook research thread now routes to `/notebooks/[id]?draftSeedThread=<thread>#research-threads-panel` instead of dropping the user onto a generic thread list with no explicit next step
  - notebook pages now carry that `draftSeedThread` state into `NotebookOutcomeJourneyCard` and `ResearchThreadsPanel`, and mobile notebook pages auto-switch to the `drafts` tab so the handoff is visible immediately
  - `NotebookDraftPanel` now mirrors the same continuity story by surfacing either the strongest recommended draft seed or the exact insight-origin seed that just arrived with the page
  - `NotebookOutcomeJourneyCard` now tells the user that the just-saved insight is already sitting at the draft doorway and previews that exact saved thread as the next draft-adjacent seed
  - `ResearchThreadsPanel` now shows a dedicated bridge callout plus a `Draft seed` marker on the matching thread card, while still preserving the separate truthful "recommended first" banner when another thread is stronger overall
  - touched notebook/source continuity copy for this bridge is now keyed in both `en-US` and `zh-CN` instead of relying on scattered literals
  - frontend tests now explicitly cover the new bridge, the mobile auto-open behavior, and the updated source-detail routing
- continuity matrix delta:
  - `insight -> note`: unchanged baseline
  - `insight -> research_thread`: unchanged truthful path, but its success landing is now much clearer because the newly created thread is carried forward as a visible draft seed
  - `insight -> draft-adjacent`: **materially closed in current local truth**, because the user can now save an insight-origin thread and land directly inside the notebook draft lane with that exact seed called out
  - `research_thread -> draft`: unchanged truthful creation path, but now more explicit when the thread came from a freshly saved insight
  - broader first-entry i18n: still intentionally scoped, but the touched notebook / research-thread / draft-adjacent continuity ring is now systematic enough to stop treating this lane as open
- fresh evidence:
  - `cd apps/web && npm test -- --run 'src/components/notebooks/NotebookOutcomeJourneyCard.test.tsx' 'src/components/notebooks/ResearchThreadsPanel.test.tsx' 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/app/(dashboard)/notebooks/[id]/page.test.tsx' 'src/components/source/SourceDetailContent.test.tsx' 'src/components/source/SourceInsightDialog.test.tsx' 'src/app/(dashboard)/search/page.test.tsx' 'src/components/search/ResearchCapturePanel.test.tsx' 'src/components/search/SaveToResearchThreadDialog.test.tsx'`
    - result: `9 files passed, 100 tests passed`
  - blocker-only reviewer dispatch
    - result: `timeout / no independent verdict captured in this turn`
- next worker should start here:
  - treat Prompt 7 as the N2 convergence attempt that closed the remaining repo-side continuity gap and was later promoted to merged/main truth by Prompt 8
  - do **not** reopen direct `insight -> draft` fantasy work unless a truly new contract is intentionally authorized
  - if you need one more closeout step, keep it on truthful N3 compatibility or proof-hardening rather than reopening N2 implementation

## 2026-04-02 Stronger-Vision Relaunch

- superseding plan for active product work:
  - `.agents/Plans/2026-04-02__provenote-vision-gap-master-plan.md`
- why this new lane exists:
  - Prompt 8 / Prompt 9 / Closed Clean / Version-Grade remain valid for the old closeout scope
  - they are **not** sufficient as the new stronger-vision SSOT because today's floor is `long messy context -> structured knowledge objects`, not only `repo-side closeout = 0 actionable`
- strongest new interpretation:
  - do **not** reopen retired blocker families like `thread_ids`, first-run, or SourceHarbor noise
  - do reopen the product ledger where the stronger vision reveals hidden-but-real capability and missing entry surfaces
- first slice now landed in current local truth:
  - long-context public front door
  - long-context transformation starter in app
  - long-context recommendation inside source ingest
- Prompt 2 continuity slice now landed in current local truth:
  - `source_insight -> notebook note` handoff in source detail
  - `save as note` CTA inside the insight dialog itself
  - note-first continuity that opens the saved note instead of leaving the structured result buried in source insights
- strongest remaining Wave N2 gaps after Prompt 7:
  - no direct `insight -> draft` automation exists, but that is now an intentional boundary rather than an active N2 blocker
  - broader first-entry i18n cleanup still exists outside the touched notebook / research-thread / draft-adjacent ring, but it is no longer the sharpest still-actionable N2 gap
  - Wave N3 truthful compatibility is still intentionally deferred until N2 closeout evidence and branch-truth accounting are treated as sufficient
- next restart rule:
  - read the new master plan first
  - then treat this task board as historical continuity + retired-blocker memory, not the sole active backlog
  - start from Wave N2 follow-up, not another Prompt 1 rediscovery pass

## 2026-04-02 Stronger-Vision Prompt 6

- prompt focus:
  - `recommended thread continuity + bounded Prompt 4 hardening`
- chosen continuity slice:
  - `research_thread -> first draft` now keeps the same recommendation story inside the thread lane itself instead of stopping at the outcome card
- why this slice beat the alternatives:
  - Prompt 5 already put a "go to the thread lane first" sign on the wall, but the panel still behaved more like a passive archive shelf than a guided next-step corridor
  - this slice strengthens N2 without pretending direct `insight -> draft` exists and without reopening Prompt 4 contract archaeology
  - the smallest honest hardening move was to require `insight_id` whenever `seed_kind="insight"` instead of leaving provenance enforcement as convention-only
- what landed:
  - `NotebookOutcomeJourneyCard` now chooses its preview thread through an explicit "richest saved context" helper instead of assuming the first returned thread is the best next draft seed
  - `ResearchThreadsPanel` now carries the recommendation story forward with a recommended-thread banner, a repeated recommended marker on the matching card, and reason copy that explains why that thread is a stronger draft seed
  - the thread list is now ordered by transparent saved-context signals (`entry_count`, attached sources/notes, then recency) instead of passive server order
  - touched `en-US` / `zh-CN` copy now explains "recommended first" as a truthful guide rail rather than an automatic decision
  - Prompt 4 residual hardening now rejects `seed_kind="insight"` requests that omit `insight_id` at both API request-model and MCP schema validation layers
  - backend + MCP tests now explicitly cover the new provenance guard
- continuity matrix delta:
  - `insight -> note`: unchanged baseline
  - `insight -> research_thread`: unchanged product path, but tighter provenance guard on the `insight` contract
  - `research_thread -> draft`: **more legible and more continuous in current local truth**, because the same recommended thread now persists from outcome card into the thread panel
  - broader first-entry i18n: improved for notebook outcome + research-thread continuity surfaces, but still not globally closed
- fresh evidence:
  - `cd apps/web && npm test -- --run 'src/components/notebooks/NotebookOutcomeJourneyCard.test.tsx' 'src/components/notebooks/ResearchThreadsPanel.test.tsx' 'src/app/(dashboard)/notebooks/[id]/page.test.tsx'`
    - result: `3 files passed, 22 tests passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py tests/test_mcp_server.py -q`
    - result: `19 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/api/export_openapi_contract.py --write`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/api/generate_frontend_api_contract.py --write`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_openapi_contract_drift.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
    - result: `PASS`
- next worker should start here:
  - keep N2 scope honest: the next bigger move is still a truthful `insight -> draft-adjacent` bridge, not a fake direct draft launcher
  - treat notebook/research-thread continuity i18n as materially tighter but still not full-repo complete
  - keep N3 OpenCode compatibility work deferred until the remaining N2 continuity gap is either closed or deliberately frozen

## 2026-04-02 Stronger-Vision Prompt 5

- prompt focus:
  - `thread -> draft-adjacent bridge inside notebook outcome lane`
- chosen continuity slice:
  - `research_thread -> first draft` guidance and handoff cleanup inside notebook pages
- why this slice beat the alternatives:
  - Prompt 4 already fixed the contract truth for `insight -> research_thread`, so the next strongest friction was inside the notebook lane itself
  - the user explicitly asked not to turn `SourceInsightDialog` into a draft entrypoint, which keeps this slice centered on notebook outcome IA
  - broader first-entry i18n cleanup is still valuable, but the most truthful next move was to make the existing thread lane feel like the natural way into a first draft
- what landed:
  - `NotebookOutcomeJourneyCard` now detects the state `threads exist but no draft yet` and sends the user to `ResearchThreadsPanel` instead of a generic empty draft lane
  - that same outcome card now previews the strongest current thread inline so the next step feels like choosing a draft seed, not clicking a generic button
  - `ResearchThreadsPanel` now explains itself as the clean handoff point into the next notebook draft revision
  - creating a draft from a research thread now auto-scrolls the user back to the notebook draft lane so the result is easier to continue immediately
  - mobile notebook pages now switch to the `drafts` tab before trying to open the draft lane or research-thread lane from the outcome card
  - touched notebook outcome lane copy gained broader `zh-CN` coverage instead of relying on scattered `en-US` fallback for the whole lane
- continuity matrix delta:
  - `insight -> note`: unchanged baseline
  - `insight -> research_thread`: unchanged from Prompt 4 baseline
  - `research_thread -> draft`: **more discoverable and more natural in current local truth**
  - broader first-entry i18n: improved for the notebook outcome lane, but still not treated as globally closed
- fresh evidence:
  - `cd apps/web && npm test -- --run 'src/components/notebooks/NotebookOutcomeJourneyCard.test.tsx' 'src/components/notebooks/ResearchThreadsPanel.test.tsx' 'src/app/(dashboard)/notebooks/[id]/page.test.tsx'`
    - result: `3 files passed, 20 tests passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
- next worker should start here:
  - keep N2 scope on a truthful `insight -> draft-adjacent` bridge if more continuity still feels weak
  - treat notebook outcome lane i18n as improved but not globally finished
  - keep N3 OpenCode compatibility work deferred until N2 is harder, not merely more polished

## 2026-04-02 Stronger-Vision Prompt 4

- prompt focus:
  - `make source_insight -> research_thread truthful at the contract layer`
- chosen continuity slice:
  - `insight-aware research_thread seed semantics`
- why this slice beat the alternatives:
  - Prompt 3 already made the research lane reachable, but it still created the thread as a generic `ask` seed
  - direct `insight -> draft` is still a larger product move and is not the smallest truthful continuity fix
  - broader first-entry i18n cleanup remains worthwhile, but it is polish work rather than the sharpest N2 blocker
- what landed:
  - research-thread create contracts now accept `seed_kind: "insight"`
  - source insight capture now sends `insight_id` and `insight_type` when creating a notebook research thread
  - research-thread creation stores insight provenance inside the first entry metadata instead of pretending the seed came from a generic ask flow
  - MCP/client helper surfaces now accept the same optional insight provenance fields without leaking empty values into non-insight calls
  - notebook research-thread summaries now render seed kinds more readably by replacing `_` with spaces
- continuity matrix delta:
  - `insight -> note`: unchanged baseline
  - `insight -> research_thread`: **contract-level gap materially closed in current local truth**
  - `insight -> draft`: still open
  - touched continuity i18n: unchanged from Prompt 3; still better than pre-Prompt-3 but broader first-entry cleanup remains open
- fresh evidence:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py tests/test_mcp_server.py -q`
    - result: `17 passed`
  - `cd apps/web && npm test -- --run 'src/components/source/SourceDetailContent.test.tsx' 'src/components/notebooks/ResearchThreadsPanel.test.tsx'`
    - result: `2 files passed, 23 tests passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/api/export_openapi_contract.py --write`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/api/generate_frontend_api_contract.py --write`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_openapi_contract_drift.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
    - result: `PASS`
- next worker should start here:
  - treat `insight-aware research_thread` contract as landed current local truth
  - decide whether the next N2 slice is a truthful `insight -> draft-adjacent` bridge or a broader first-entry i18n cleanup
  - do **not** reopen the old question of whether Prompt 3 only shipped a generic ask-thread hack; Prompt 4 already settled that contract gap

## 2026-04-02 Stronger-Vision Prompt 3

- prompt focus:
  - `structured insight -> reusable research object`
- chosen continuity slice:
  - `source_insight -> seeded research lane + direct notebook research-thread capture`
- why this slice beat the alternatives:
  - Prompt 2 already made `insight -> note` real, so the next strongest missing step was entering the active research lane
  - direct `insight -> draft` still runs into the current source-first draft contract and is not the smallest truthful slice
  - the chosen path reuses the existing Search / Ask -> ResearchCapture -> Save-to-thread flow and the existing thread-create contract instead of inventing a fake new backend object
- what landed:
  - source insight detail now exposes a `Research this insight` CTA
  - that CTA opens the existing Search / Ask page with an editable seeded query, `autostart=0`, and carries linked source/notebook context when available
  - Search / Ask now honors seeded prefill without silently auto-running the query
  - the seeded lane now pre-arms the working notebook in research capture and the manual save dialog when notebook context is already known
  - source insight detail now also exposes a direct `Save to research thread` capture that reuses the existing notebook research-thread create flow
  - Search-page `Save to research thread` buttons now use i18n instead of hard-coded English
  - touched `zh-CN` research capture / save-thread copy is filled in so the seeded continuity lane is not English-only
- continuity matrix delta:
  - `insight -> note`: still real and unchanged
  - `insight -> research_thread`: **substantially closed in current local truth** via both seeded research entry and direct notebook thread capture
  - `insight -> draft`: still open
  - touched continuity i18n: materially tighter on `en-US` + `zh-CN`
- fresh evidence:
  - `cd apps/web && npm test -- --run 'src/components/source/SourceInsightDialog.test.tsx' 'src/components/source/SourceDetailContent.test.tsx' 'src/app/(dashboard)/search/page.test.tsx' 'src/components/search/ResearchCapturePanel.test.tsx'`
    - result: `4 files passed, 61 tests passed`
  - `cd apps/web && npx vitest run 'src/components/search/SaveToResearchThreadDialog.test.tsx' -t 'preselects seeded notebook ids when provided'`
    - result: `1 passed, 3 skipped`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
- next worker should start here:
  - keep Wave N2 scope tight
  - decide whether the next slice is `first-class insight seed_kind / contract cleanup`, `insight -> draft-adjacent bridge`, or a broader first-entry i18n cleanup

## 2026-04-02 Stronger-Vision Prompt 2

- prompt focus:
  - `long-context structured result -> reusable knowledge object`
- chosen continuity slice:
  - `source_insight -> notebook note`
- why this slice beat the alternatives:
  - Prompt 1 already solved the strongest entry/discoverability gap
  - the next strongest missing step was the bridge from structured insight into a durable notebook object
  - this path reused an already-real backend route instead of inventing a fake direct draft shortcut
- what landed:
  - source insights list now exposes `save as note`
  - source insight dialog now exposes the same CTA
  - the save action currently routes through the linked notebook path when the source is already associated to a notebook
  - the long-context use-case page now describes the note-first continuity truth
- continuity matrix delta:
  - `insight -> note`: **partial gap closed in current local truth**
  - `insight -> research_thread`: still open
  - `insight -> draft`: still open
  - `insight -> searchability`: materially stronger because notebook notes already participate in notebook/search/chat context
- fresh evidence:
  - `cd apps/web && npm test -- --run 'src/lib/api/insights.test.ts' 'src/lib/hooks/use-insights.test.ts' 'src/components/source/SourceInsightsTab.test.tsx' 'src/components/source/SourceInsightDialog.test.tsx' 'src/components/source/SourceDetailContent.test.tsx'`
    - result: `41 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
    - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
    - result: `PASS`
- next worker should start here:
  - keep Wave N2 scope tight
  - choose between `insight -> research_thread seed`, `insight -> draft-adjacent bridge`, or a broader but still surgical i18n cleanup of touched continuity surfaces

## Prompt 13 Zero-Excuse Final Push

- active promotion branch: no longer authoritative; PR `#28` is closed
- latest tracked closeout update promoted to `main`: `14fb2ce docs: refresh no-survivors release handoff`
- current `main` head: `14fb2ce`
- current main witness run visible on the public workflow page: `23857176689`
- current remote/public state:
  - repo description already synced
  - homepage already synced
  - draft release `v1.8.4` already prepared
- current interpretation:
  - broad repo-side engineering residuals are now compressed to remote witness and promotion actions
  - do not reopen product/API/i18n archaeology unless a fresh remote failure proves a new repo-side blocker

## 2026-04-01 Zero-Excuse Final Push Update

- Current operator branch: `codex/release-grade-frontend-witness`
- Current branch head: `0d7b7e1 docs: refresh release witness tracker`
- Current main head: `14fb2ce docs: refresh no-survivors release handoff`
- Latest branch-only tracked deltas versus `main`:
  - no remaining repo-side code blockers are known to require branch promotion
- Latest concrete repo-side blocker that was fixed:
  - `apps/web/src/lib/stores/navigation-store.test.ts` stale fallback expectations no longer match the store/hook contract
  - fixed on `main`, then followed by `b436ace` to absorb the last known batch-worker memory guard from the stale promotion branch, and then `14fb2ce` to align the tracked no-survivors handoff on `main`
- Latest known remote witness state before GitHub API rate limiting:
  - old `main` failure witness: `23852996237`
    - `Runtime Policy Gates`: failed
    - `Frontend Tests`: failed
  - fresh visible `main` witness: `23857176689`
    - visible on the public workflow page for the current `main` promotion chain
  - PR `#28` has been closed as superseded-by-main
- Practical interpretation:
  - repo-side actionable engineering work is now effectively `0`
  - remaining work is promotion-layer only:
    - wait for fresh `Frontend Tests` verdict
    - confirm/run manual `Build and Release`
    - publish draft release `v1.8.4`

## Prompt 11/12 Release Witness Addendum

- `main` currently points at `371ab74` (`fix(ci): harden frontend coverage and i18n gates`)
- active `Tests` workflow on `main`: `23852996237`
- active PR branch for the last frontend release-witness residual: `codex/release-grade-frontend-witness`
- PR: `#28` `[codex] stabilize frontend release witness coverage`
- PR head SHA: `80f79e4`
- latest checked PR `Tests` workflows:
  - `23853212396` `pending`
  - `23853102553` `queued`

Current interpretation:

- broad product / docs / API / MCP / i18n convergence is already landed
- the only active engineering residual family is release-witness CI stabilization
- do not reopen product-scope archaeology unless a fresh CI failure proves a new repo-side blocker

## Prompt 2 Status

- Prompt: `Prompt 2 / 5 — P0 stability and key contract repair`
- Outcome:
  - `Wave 0` is now **substantially completed in current local truth**
  - `Wave 1` is now **partially completed in current local truth**
  - `Wave 2+` remain intentionally untouched in this prompt

### Prompt 2 Fresh Evidence

- `docker compose -f ops/compose/docker-compose.yml up -d --build`
  - result: build succeeded, `provenote-provenote-1` and `provenote-surrealdb-1` both reached `Up`
- `docker compose -f ops/compose/docker-compose.yml ps`
  - result: both services up with `5055` and `8502` published
- `docker logs --tail 120 provenote-provenote-1`
  - result: supervisor reports `api`, `worker`, `surrealdb`, and `web` all entered `RUNNING`
- `curl -fsS http://localhost:5055/health`
  - result: `{"status":"healthy"}`
- `curl -I --max-time 10 http://localhost:8502`
  - result: `HTTP/1.1 307 Temporary Redirect` with `location: /notebooks`
- `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api/test_draft_service.py tests/api/test_research_thread_service.py tests/api/contract/test_outcome_spine_contract.py tests/ci/test_supervisor_log_path_contract.py -q`
  - result: `16 passed`
- `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_source_processing_report.py -q`
  - result: `6 passed`
- `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api/test_gemini_startup_probe.py tests/api/test_credentials_governance.py -q`
  - result: `21 passed`
- `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_model_strategy.py tests/api/test_gemini_startup_probe.py tests/api/test_credentials_governance.py tests/test_migration_symmetry.py tests/api/test_auth_fail_closed.py tests/api/test_auth_additional_coverage.py tests/integration/test_auth_routing_boundary.py tests/api/test_draft_service.py tests/api/test_research_thread_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_source_processing_report.py tests/api/contract/test_outcome_spine_contract.py tests/ci/test_supervisor_log_path_contract.py -q`
  - result: `74 passed`
- direct runtime API smoke with default payloads:
  - `POST /api/notebooks` -> `200`
  - `POST /api/sources/json` -> `200`
  - `POST /api/sources/{source_id}/auditable-runs` -> `200` with `model_id=gemini-2.5-flash`
  - `POST /api/notebooks/{notebook_id}/drafts` -> `500` with `Selected draft sources do not contain any non-empty paragraph`

### Prompt 2 Decisions

- Canonical `thread_ids` semantic is now **`research_thread`**, not `chat_session`.
- The documented Docker fast path now defends itself against stale local `.env` overrides for:
  - API/browser URL wiring
  - CORS allowlist
  - Gemini startup model
- Auth contract now matches the repo's public/runtime story:
  - when `OPEN_NOTEBOOK_PASSWORD` is unset, API runs in open mode instead of claiming auth is disabled while rejecting protected writes
- The old archive root cause `Invalid name: 'apps/web'` is now treated as **archive truth only**.
  - It was real in older runtime evidence.
  - It is no longer the active current-local blocker after the local supervisor fixes.
- The new residual runtime gap is **not** startup anymore.
  - Startup and auditable first result now work.
  - Remaining raw API gap is notebook draft creation immediately after source creation, which currently returns `Selected draft sources do not contain any non-empty paragraph`.
  - Treat that as the first Wave 2 runtime/product-journey handoff item unless it reproduces as a broader persisted-data blocker.

### Wave Status After Prompt 2

| Wave | Status | Notes |
| --- | --- | --- |
| Wave 0 — Truth + Unblockers | done in current local truth | first-run default compose path now reaches healthy API and reachable UI; auth/runtime contract aligns with public story; `thread_ids` local contract aligned; still awaiting reviewer/commit promotion to main truth |
| Wave 1 — Stability + Contract Hardening | partial | core schema/service/tests are aligned locally for `thread_ids`; broader reviewer signoff and commit/promotion still pending |
| Wave 2 — Core Product Journey | done in current local truth | source/notebook/search now expose a connected outcome path, unified journey/status cards, research capture entry, and draft compare/verify cues; live API smoke now completes `source -> auditable -> draft -> verify` without the old draft 500 |
| Wave 3 — Outcome Tooling + MCP | partial in current local truth | outcome-first MCP first cut now exists for draft / research_thread / auditable_run; draft export bundle route + UI are landed locally and live-smoked; source-level claim review workspace is landed locally; batch ingestion MVP was re-verified through existing UI lane tests; remaining Wave 3 work is broader outcome coverage, not first-cut availability |
| Wave 4 — Growth / SEO / Branding / Distribution | pending | intentionally not started in this prompt |

## Prompt 4 Status

- Prompt: `Prompt 4 / 5 — Outcome Tooling / MCP / deeper productization`
- Outcome:
  - `Wave 3` is now **partial but real in current local truth**
  - `Wave 4` remains intentionally untouched in this prompt

### Prompt 4 Fresh Evidence

- outcome-first MCP suite:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py -q`
  - result: `10 passed`
- export / review backend suite:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api/test_draft_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py -q`
  - result: `19 passed`
- claim review / outcome draft frontend suite:
  - `cd apps/web && npm test -- --run 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/components/source/AuditableMarkdownPanel.test.tsx' 'src/components/source/AuditableClaimReviewWorkspace.test.tsx'`
  - result: `15 passed`
- batch ingestion MVP re-verification:
  - `cd apps/web && npm test -- --run 'src/components/sources/AddSourceDialog.test.tsx' 'src/components/sources/steps/SourceTypeStep.test.tsx'`
  - result: `17 passed`
- Wave 3 bundled targeted suite:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py tests/api/test_draft_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py -q`
  - result: `29 passed`
  - `cd apps/web && npm test -- --run 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/components/source/AuditableMarkdownPanel.test.tsx' 'src/components/source/AuditableClaimReviewWorkspace.test.tsx' 'src/components/sources/AddSourceDialog.test.tsx' 'src/components/sources/steps/SourceTypeStep.test.tsx'`
  - result: `32 passed`
- contract drift:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_openapi_contract_drift.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
  - result: `PASS`
- fresh runtime rebuild:
  - `docker compose -f ops/compose/docker-compose.yml up -d --build`
  - result: rebuilt successfully after reboot; `/api/drafts/{draft_id}/bundle` is now present in live OpenAPI
  - `curl -fsS http://localhost:5055/openapi.json | ...`
  - result: `/api/drafts/{draft_id}/bundle` present in runtime schema
  - `curl -fsS http://localhost:5055/health`
  - result: `{"status":"healthy"}`
  - `curl -I --max-time 10 http://localhost:8502`
  - result: `HTTP/1.1 307 Temporary Redirect` to `/notebooks`
- direct export bundle smoke:
  - created fresh notebook -> source -> draft -> bundle
  - result: zip contains `draft.md`, `metadata.json`, `metrics.json`, `pid_summary.json`, `source_manifest.json`, `claims.json`, `sections.json`, `coverage.json`, `dedup.json`, `README.txt`
  - verified-bundle smoke additionally produced `verified_snapshot.json`

### Prompt 4 Decisions

- Outcome-first MCP first cut is:
  - `draft.list`
  - `draft.create`
  - `draft.verify`
  - `draft.download`
  - `research_thread.list`
  - `research_thread.create`
  - `research_thread.append`
  - `research_thread.to_draft`
  - `auditable_run.list`
  - `auditable_run.create`
  - `auditable_run.download`
  - `auditable_run.repair_claim`
  - `auditable_run.repair_section`
- Naming rationale:
  - use dot-separated noun-first names to match existing MCP surface
  - prefer direct outcome verbs over another generic `*.mutate` wrapper for first-cut outcome objects
  - keep control-plane tools (`settings.mutate`, `ui_test.control`, `computer_use.control`) intact instead of mixing them into outcome groups
- Export bundle canonical shape:
  - `zip` is the first cut
  - main artifact: `draft.md`
  - support artifacts: `metadata.json`, `metrics.json`, `pid_summary.json`, `source_manifest.json`, `claims.json`, `sections.json`, `coverage.json`, `dedup.json`, `README.txt`
  - `verified_snapshot.json` is included when the draft has been verified
- Claim review workspace boundary:
  - first cut is source-level and auditable-run-centered
  - optimize for readable claim/section/PID review plus repair actions
  - do not expand into a full notebook-wide review console in this prompt
- Batch ingestion MVP boundary:
  - reuse the existing notebook-scoped `AddSourceDialog` batch lane
  - support multi-URL and multi-file input with shared notebook/processing settings
  - do not create a second async/status system for batch in this prompt

### Prompt 5 Handoff

- Start from **Wave 4 — Growth / SEO / branding / final audit**, not from another Wave 3 rediscovery pass.
- Reuse current Wave 3 evidence:
  - `tests/test_mcp_server.py` green for the outcome-first MCP first cut
  - export bundle route + direct zip smoke already proven
  - claim review workspace tests already green
  - batch ingestion MVP tests already green
  - openapi/frontend contract drift checks already green
- Remaining non-blocker follow-ups after Prompt 4:
  - broader outcome MCP coverage such as podcast/export surfaces if still desired
  - richer notebook-level review workspace beyond source-level claim review
  - growth/distribution work only after one quick Wave 3 smoke re-check

## Prompt 3 Status

- Prompt: `Prompt 3 / 5 — core product journey`
- Outcome:
  - `Wave 2` is now **done in current local truth**
  - `Wave 3+` remain intentionally untouched in this prompt

### Prompt 3 Fresh Evidence

- frontend targeted journey suite:
  - `cd apps/web && npm test -- 'src/app/(dashboard)/search/page.test.tsx' 'src/app/(dashboard)/sources/[id]/page.test.tsx' 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/components/search/ResearchCapturePanel.test.tsx' 'src/components/notebooks/NotebookOutcomeJourneyCard.test.tsx' 'src/components/source/SourceOutcomeJourneyCard.test.tsx'`
  - result: `6 passed`, `40 passed`
  - `cd apps/web && npm test -- 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/app/(dashboard)/search/page.test.tsx' 'src/components/search/ResearchCapturePanel.test.tsx'`
  - result: `3 passed`, `33 passed`
- backend targeted spine suite:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api/test_draft_service.py tests/test_migration_symmetry.py -q`
  - result: `17 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api/test_draft_service.py -q`
  - result: `8 passed`
- runtime health:
  - `docker compose -f ops/compose/docker-compose.yml up -d --build`
  - result: frontend production build passed and `provenote-provenote-1` was recreated successfully
  - `docker compose -f ops/compose/docker-compose.yml logs --tail 160 provenote`
  - result: `api`, `worker`, `surrealdb`, and `web` all entered `RUNNING`
  - `curl -fsS http://localhost:5055/health`
  - result: `{"status":"healthy"}`
  - `curl -I --max-time 10 http://localhost:8502`
  - result: `HTTP/1.1 307 Temporary Redirect` with `location: /notebooks`
  - `docker compose -f ops/compose/docker-compose.yml ps`
  - result: `provenote` and `surrealdb` both `Up`
  - `curl -fsS 'http://localhost:5055/api/notebooks/notebook:cb4poyxgw34mdokvh81i/drafts' | grep -o '"created":"[^"]*"\\|"updated":"[^"]*"'`
  - result:
    - `"created":"2026-03-31 17:42:22.704390+00:00"`
    - `"updated":"2026-03-31 17:42:22.704395+00:00"`
- browser snapshots after the fresh rebuild:
  - `/search` visibly renders `Research capture`, a working-notebook combobox, and the explicit auto-save toggle
  - `/notebooks/{notebook_id}` renders `Outcome path`, `Jump to draft lane`, the draft lane, and `Research Threads`
  - after clicking `Create Draft`, the same notebook page advances to `Draft complete`, `Verify active`, and shows the `Why verify?` callout without hitting the old React boundary

### Prompt 3 Decisions

- Shortest product journey stays **`Source -> Auditable Markdown -> Draft -> Verify`**.
- Search and ask now capture into research threads through an explicit working-notebook control instead of hidden background saves.
- Auto-save remains opt-in and result-triggered:
  - it only runs when the user arms a notebook target
  - it only runs after a completed ask/search result exists
  - it is guarded against duplicate thread spam by the capture component state map and targeted tests
  - same notebook + same query now reuses the same session-scoped research thread and appends updates instead of spraying sibling threads
- Unified status is intentionally human-facing:
  - source page summarizes processing + auditable + draft + verify
  - notebook page summarizes sources ready + draft + verify + research threads
  - raw command/process internals stay in detail panels instead of being forced into the main journey card
- Compare / verify now has explicit product meaning in the draft lane:
  - compare summary shows deltas versus the previous draft
  - verify explains that it freezes markdown + metrics into a stable snapshot
- Prompt 3 also fixed a live journey blocker discovered during browser smoke:
  - fresh draft creation previously surfaced `created: "None"` / `updated: "None"` through the API and crashed the notebook page with `RangeError: Invalid time value`
  - current local truth now adds draft timestamp schema coverage, migration-manager registration, draft response normalization, and a notebook timestamp fallback so the journey can continue even if older bad records exist

### Prompt 4 Handoff

- Start from **Wave 3 — Outcome Tooling + MCP**, not from another Wave 2 rediscovery pass.
- Reuse current evidence instead of re-running the same Wave 2 reconnaissance:
  - frontend journey/status/capture/compare tests are already green
  - backend `research_thread -> draft -> verify` tests are already green
  - fresh rebuild + browser snapshots already prove the Prompt 3 source/search/notebook journey surfaces are rendering
- Next prompt should focus on:
  - outcome tooling surfaces such as export bundle / review workspace
  - outcome-first MCP promotion for `draft`, `research_thread`, and `auditable_run`
  - one quick live runtime smoke for `source -> auditable -> draft -> verify` should still run at the very start, but the old notebook timestamp crash is no longer an open blocker
  - only then return to growth / SEO / landing / integrations

## Mission

Land every enhancement discussed in thread `019d4359-899f-7572-82a6-c35ef6880bba` until each item is in exactly one state:

- landed with fresh evidence
- intentionally deferred with explicit scope/risk reasoning
- blocked by a real external dependency

## Truth Layers

- `archive truth`: what the March 31 archive said or proposed
- `current main truth`: what committed repo state shows today
- `current local truth`: what current worktree shows today, including uncommitted local-only fixes
- `external blocker`: machine/runtime state outside repo logic

## Fresh Live Truth Snapshot

- `git status --short --branch` currently shows `main...origin/main` with a dirty worktree.
- `git log --oneline --decorate -n 20` shows `3dc34db [codex] land notebook outcome spine (#25)` and `4005375 chore(ops): add cleanup operator path (#26)`, so notebook outcome spine is already on `main`.
- Source-level auditable runs, notebook drafts, research threads, source QA/reprocess, and draft-to-podcast bridge all exist in current code/docs/contracts.
- `thread_ids` drift was real: OpenAPI + outcome models + `research_thread_service` treated `thread_ids` as research-thread IDs, while migration `19.surrealql` still typed them as `record<chat_session>`.
- This turn fixed the `thread_ids` drift in repo code/tests:
  - `packages/core/database/migrations/19.surrealql`
  - `services/api/draft_service.py`
  - `tests/api/test_draft_service.py`
  - `tests/api/contract/test_outcome_spine_contract.py`
- Current local worktree contains uncommitted first-run hardening that is not yet committed main truth:
  - `ops/compose/docker-compose.yml` adds `name: provenote` and container-stable API URL envs
  - `ops/supervisor/supervisord.conf` and `ops/supervisor/supervisord.single.conf` rename `[program:apps/web]` to `[program:web]`
  - `.dockerignore` now exists locally and excludes runtime/cache/node_modules surfaces
  - `tests/ci/test_supervisor_log_path_contract.py` and `tooling/scripts/ci/check_supervisor_log_path.py` add guards for safe supervisor program names and compose fast-path contract
- Prompt 2 also confirmed a deeper first-run blocker and fixed it:
  - `ops/compose/docker-compose.yml` now pins `GEMINI_MODEL=gemini-2.5-flash` for the documented Docker fast path
  - `packages/core/database/migrations/19.surrealql` and `20.surrealql` no longer use invalid `TYPE FLEXIBLE ...` ordering
  - `README.md` and `docs/quickstart.md` now describe the fast path as injecting a known-good Gemini model
- Additional first-run fixes landed this turn:
  - `ops/compose/docker-compose.yml` no longer exposes host `8000:8000` on the default fast path
  - `ops/supervisor/supervisord.single.conf` now imports `services.worker` instead of missing `commands`
- Those first-run changes now have fresh targeted evidence:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_supervisor_log_path_contract.py tests/api/test_draft_service.py tests/api/test_research_thread_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/contract/test_outcome_spine_contract.py -q`
  - Result: `20 passed`
- Fresh runtime proof now shows the documented quick result path is restored on the current local worktree:
  - `docker compose -f ops/compose/docker-compose.yml up -d --build` succeeds
  - `docker compose -f ops/compose/docker-compose.yml ps` shows both `provenote` and `surrealdb` up
  - `docker logs provenote-provenote-1` shows supervisor keeping `surrealdb`, `api`, `worker`, and `web` running
  - `curl http://localhost:5055/health` returns `{\"status\":\"healthy\"}`
  - `curl -I http://localhost:8502` returns `307 Temporary Redirect` to `/notebooks`

## Enhancement Inventory

| Item | Category | Archive truth | Current status | Recommended wave |
| --- | --- | --- | --- | --- |
| Single-container first-run | Stability | P0 blocker; archive said supervisor `apps/web` name broke single-container start | `current local truth`: documented compose fast path is now healthy with clean `ps`, `health`, and UI redirect evidence; still uncommitted main truth | Wave 0 done locally |
| Docker fast-path predictability | Stability | Fast path should open `:8502` and `:5055/health` reliably | Compose naming, API URL env pinning, known-good Gemini model pinning, `.dockerignore`, and migration syntax fixes now make the local fast path reproducible | Wave 0 done locally |
| `draft.thread_ids` contract alignment | Contract | Archive marked as medium-risk drift | Landed this turn with schema/service/tests and contract evidence | Wave 0 done locally |
| Outcome spine canonical path | Product spine | `Source -> Auditable -> Draft -> Verify -> Podcast`; `Search/Ask -> Research Thread -> Draft` | Largely landed on main, but guided UX between steps is still fragmented | Wave 2 |
| Research thread auto-save | Product UX | Desired enhancement | Current local truth now has one explicit research-capture panel on Ask/Search with notebook opt-in, completed-result-only auto-save, and session-level dedupe/append semantics | Wave 2 landed locally |
| Draft compare / review workspace | Product UX | Desired enhancement | Current local truth now has compare summary, verify freeze callout, and verified snapshot cue inside the draft lane; full review workspace/export bundle still deferred | Wave 2 partial / Wave 3 for full workspace |
| Export bundle | Outcome tooling | Desired enhancement | Markdown download exists for auditable runs and drafts; no bundled multi-artifact export | Wave 3 |
| Claim review workspace | Outcome tooling | Desired enhancement | Source-level claim/section repair exists; notebook-level review bundle does not | Wave 3 |
| Batch ingestion | Product capability | Mentioned in archive backlog | Already exists for source import UI; auditable batch API also exists | No new wave unless gaps appear |
| Outcome-first MCP | MCP / agent | Archive said current MCP is too control-plane | Confirmed: current MCP exposes notebook/source/note/search/chat/model/settings/ui_test/computer_use, but not `draft.*`, `research_thread.*`, `auditable_run.*` outcome tools | Wave 3 |
| `computer_use` / `ui_test` maturity | Control plane | Archive treated them as side surfaces, not main product | Confirmed: real API + MCP + tests exist; still auxiliary control plane | Wave 3 |
| Claude Code / Codex / Cursor integration pages | Growth / SEO | Archive recommended as P0 growth lever | Not implemented in current repo docs/pages | Wave 4 |
| Landing / SEO pages for auditable AI notes / research thread / verified draft | Growth / SEO | Archive recommended as core traffic capture | Not implemented in current repo docs/pages | Wave 4 |
| Branding / domain strategy | Growth / brand | Archive said keep `Provenote`, treat `.ai` as landing domain, not immediate rebrand | No repo implementation yet; domain availability still [to be confirmed] | Wave 4 |
| Docs / verification closeout | Docs / trust | Archive demanded proof-aligned docs and fresh evidence | Public docs already improved on main; next work is integration/growth docs plus first-run runtime proof refresh | Wave 4 |

## Completed Or Sufficiently Landed Already

Do not re-scout these unless new conflicting evidence appears:

- source import and source detail surface
- source-level auditable markdown runs with metrics + markdown download + claim/section repair
- notebook-level drafts CRUD + rerun + verify + markdown download
- research thread CRUD + thread-to-draft bridge
- source processing report + reprocess routes
- draft-to-podcast bridge using `draft_id`
- current public README / proof / quickstart / FAQ front door
- current MCP existence, tool count, and control-plane shape
- source batch ingestion UI and auditable batch API

## Wave Plan

### Wave 0 — Truth + Unblockers

Why now:
- This wave removes blockers that distort every later judgment.
- No later UX or growth work should ship on top of a drifting contract or an unverified first-run story.

Expected files/modules:
- `packages/core/database/migrations/19.surrealql`
- `services/api/draft_service.py`
- `tests/api/test_draft_service.py`
- `tests/api/contract/test_outcome_spine_contract.py`
- existing local-only startup files if/when they are adopted:
  - `ops/compose/docker-compose.yml`
  - `ops/supervisor/supervisord.conf`
  - `ops/supervisor/supervisord.single.conf`
  - `.dockerignore`
  - `tests/ci/test_supervisor_log_path_contract.py`
  - `tooling/scripts/ci/check_supervisor_log_path.py`

Required tests:
- `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/api/test_draft_service.py tests/api/test_research_thread_service.py tests/api/contract/test_outcome_spine_contract.py -q`
- `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/ci/test_supervisor_log_path_contract.py tests/api/test_research_thread_service.py -q`
- repeatable runtime proof commands:
  - `docker compose -f ops/compose/docker-compose.yml up -d --build`
  - `docker compose -f ops/compose/docker-compose.yml ps`
  - `docker logs --tail 200 provenote-provenote-1`
  - `docker logs --tail 120 provenote-surrealdb-1`
  - `docker inspect -f '{{.State.Status}} {{.State.Restarting}} {{.RestartCount}}' provenote-provenote-1`
  - `curl -fsS http://localhost:5055/health`
  - `curl -I http://localhost:8502`

Blockers:
- `surrealdb` container exits/restarts in the default compose path
- API startup probe fails against `models/gemini-3.1-pro`

Can parallelize with:
- Wave 4 research/doc writing
- Wave 3 MCP design scoping

Done when:
- `thread_ids` contract is aligned across schema/service/tests
- first-run local-only patch is either committed/adopted, or rejected with fresh runtime evidence
- default compose path reaches healthy `:5055/health` and reachable `:8502`

### Wave 1 — Stability + Contract Hardening

Why now:
- After truth is fixed, lock safety rails before bigger UX/growth work.

Expected files/modules:
- `contracts/api/openapi.yaml`
- generated frontend contract surfaces
- `tests/api/contract/*`
- `tests/ci/*` outcome-spine and runtime guards
- any first-run files promoted from current local truth

Required tests:
- API contract drift checks
- targeted router/service tests for drafts, research threads, auditable runs, podcasts
- runtime/supervisor/compose contract tests

Blockers:
- none besides unresolved Wave 0 first-run proof

Can parallelize with:
- Wave 2 UX scoping

Done when:
- no contract ambiguity remains between schema, services, generated types, and tests

### Wave 2 — Core Product Journey

Why now:
- Main capabilities exist, but user flow still feels like separate rooms instead of one guided corridor.

Expected files/modules:
- `apps/web/src/app/(dashboard)/sources/[id]/page.tsx`
- `apps/web/src/app/(dashboard)/notebooks/[id]/page.tsx`
- `apps/web/src/app/(dashboard)/search/page.tsx`
- `apps/web/src/components/notebooks/NotebookDraftPanel.tsx`
- `apps/web/src/components/notebooks/ResearchThreadsPanel.tsx`
- `apps/web/src/components/source/AuditableMarkdownPanel.tsx`
- supporting hooks/API clients

Required tests:
- relevant Vitest component/hook coverage
- action-matrix or targeted E2E smoke for source -> auditable -> draft -> verify

Blockers:
- none, once Wave 0/1 are settled

Can parallelize with:
- early Wave 4 content planning

Done when:
- the shortest product story is one connected path, not a set of isolated panels
- manual save-only rough edges are either resolved or explicitly deferred

### Wave 3 — Outcome Tooling + MCP

Why now:
- Once the main journey works for humans, expose the same outcome spine cleanly to agents and power users.

Expected files/modules:
- `packages/core/mcp/server.py`
- MCP schemas/tests
- draft/research-thread/auditable outcome services or adapters
- notebook/source review/export UI surfaces if needed

Required tests:
- `tests/test_mcp_server.py`
- new outcome-first MCP contract tests
- targeted router/service tests for export/review features

Blockers:
- avoid creating a second truth system beside REST/services

Can parallelize with:
- Wave 4 content pages after exact tool names are frozen

Done when:
- MCP exposes first-class outcome tools, not only control-plane utilities
- draft/research-thread/auditable outcome objects have agent-friendly entrypoints

### Wave 4 — Growth / SEO / Branding / Distribution

Why now:
- Growth pages should describe real, verified product surfaces, not wishful roadmap copy.

Expected files/modules:
- `README.md`
- `docs/proof.md`
- `docs/faq.md`
- `docs/quickstart.md`
- new landing/integration docs or page surfaces as needed
- possibly repo metadata / topics / descriptions if in scope

Required tests:
- docs/link integrity checks
- navigation docs pair checks
- proof-page references stay evidence-backed

Blockers:
- do not publish pages for flows not yet verified
- domain availability remains external and [to be confirmed]

Can parallelize with:
- none that depend on unverified product claims

Done when:
- integration pages for Claude Code / Codex / Cursor exist or are intentionally deferred
- landing/SEO structure matches proven product outcomes
- branding recommendations are translated into concrete repo/docs surfaces

## Owner Model

- `l2-explorer`
  - archive diff refresh only if new code lands
  - MCP surface inventory refresh after Wave 3
- `l2-debugger`
  - first-run/runtime verification and root-cause isolation for default-compose failures
- `l2-implementer`
  - Wave 2 and Wave 3 scoped code changes
- `l2-reviewer`
  - blocker-only review before any “wave done” claim
- `l2-librarian`
  - official-source SEO / integration / branding refresh for Wave 4
- `l2-designer`
  - only when a new landing or integration page actually enters implementation

## Acceptance Checklist

- [x] Archive was fully read before planning
- [x] Live repo truth was separated from archive truth
- [x] `thread_ids` contract drift was confirmed with file-level evidence
- [x] Prompt 2 restored a verifiable local Docker fast path on the current worktree
- [x] Prompt 2 aligned `thread_ids` across migration/service/tests with fresh targeted evidence

## Prompt 2 Status

### Done

- first-run / single-container startup blocker:
  - safe supervisor program names
  - single-container worker import path fixed
  - known-good fast-path Gemini model pinned
  - migration 19/20 SurrealQL syntax corrected for clean-DB startup
  - local `docker compose -f ops/compose/docker-compose.yml up -d --build` + `ps` + `/health` + `:8502` witness passed
- `draft.thread_ids` canonical meaning:
  - canonical semantic is `research_thread`
  - schema, service normalization, and targeted tests are aligned locally
- minimal acceptance guards:
  - startup/supervisor/compose contract guard strengthened
  - `research_thread -> draft` and outcome-spine contract tests strengthened
  - `draft -> verify` remains covered by existing targeted tests

### Partial

- none within Prompt 2 local scope

### Blocked

- committed main truth still lags behind current local truth because this turn does not commit
- full blocker-only reviewer verdict was requested but not received in time

## Prompt 3 Status

Prompt 3 moved Wave 2 from plan-only into current local truth:

- [x] `Search / Ask` now has one clear `ResearchCapturePanel` surface instead of a second hand-written auto-save card
- [x] Research capture stays explicit opt-in, notebook-scoped, completed-result-only, and session-deduped
- [x] `Source -> Auditable -> Draft -> Verify` is now visible on source and notebook pages through outcome-path cards and next-step CTAs
- [x] `NotebookDraftPanel` now surfaces compare summary, verify freeze callout, and verified snapshot cue in the draft lane
- [x] Targeted frontend verification passed:
  - `npm test -- --run src/app/(dashboard)/search/page.test.tsx src/components/search/ResearchCapturePanel.test.tsx src/components/notebooks/NotebookDraftPanel.test.tsx src/lib/hooks/use-research-threads.test.ts src/app/(dashboard)/sources/[id]/page.test.tsx`
  - result: `41 passed`
- [x] Live browser snapshots confirmed the new outcome-path copy/state surfaces on:
  - `/sources/{id}` for source outcome guidance
  - `/notebooks/{id}` for notebook outcome guidance + draft lane + research-thread lane
- [ ] One full live browser/runtime pass for `source -> auditable -> draft -> verify` is still missing from this turn
- [ ] Wave 3 outcome tooling / MCP work has not started
- [ ] Wave 4 growth / integration / landing work remains intentionally untouched

## Unresolved Risks

- Current dirty worktree already contains local-only first-run edits; do not accidentally overwrite or double-claim them.
- First-run runtime truth is no longer blocked by daemon availability, but it is still incomplete because deeper SurrealDB/API blockers remain.
- Outcome-first MCP work can easily drift into a parallel contract if it bypasses service/API truth.
- Growth copy can overclaim if written before Wave 0/2 runtime proof is refreshed.

## External Blockers

- domain availability / trademark clearance for any `.ai` or rebrand decision remains external

## Prompt 4 Status

- Prompt: `Prompt 4 / 5 — outcome tooling / MCP / deeper productization`
- Outcome:
  - `Wave 3` is now **partial in current local truth**
  - `Wave 4` remains intentionally untouched in this prompt

### Prompt 4 Fresh Evidence

- outcome-first MCP + draft bundle backend suite:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py tests/api/test_draft_service.py tests/api/test_drafts_router.py tests/api/test_auditable_runs_router.py -q`
  - result: `31 passed`
- frontend outcome/export/review suite:
  - `cd apps/web && npm test -- --run 'src/lib/api/drafts.test.ts' 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/components/source/AuditableClaimReviewWorkspace.test.tsx' 'src/components/source/AuditableMarkdownPanel.test.tsx'`
  - result: `16 passed`
- batch ingestion MVP re-verification:
  - `cd apps/web && npm test -- --run 'src/components/sources/steps/SourceTypeStep.test.tsx'`
  - result: `5 passed`
  - `cd apps/web && npm test -- --run 'src/components/sources/AddSourceDialog.test.tsx' -t 'handles batch submit with partial failures and warns user|handles upload batch full failures and shows batch failed summary'`
  - result: `2 passed`
- contract drift:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_openapi_contract_drift.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/api/generate_frontend_api_contract.py --write`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
  - result: `PASS`
- live API smoke on the current local API:
  - `POST /api/sources/{source_id}/auditable-runs` -> `200`, `status=completed`
  - `POST /api/notebooks/{notebook_id}/drafts` -> `200`, `status=completed`, `version=1`
  - `POST /api/drafts/{draft_id}/verify` -> `200`, `status=verified`, `verified_brief_snapshot=true`
- external runtime blocker:
  - `docker compose -f ops/compose/docker-compose.yml up -d --build`
  - result: failed after local code landed because Docker Desktop could not resolve `registry-1.docker.io` while fetching base image metadata
  - interpretation: external network/build blocker, not a repo-side contract failure

### Prompt 4 Decisions

- Outcome-first MCP first cut is now centered on outcome objects:
  - `draft.list`
  - `draft.create`
  - `draft.verify`
  - `draft.download`
  - `research_thread.list`
  - `research_thread.create`
  - `research_thread.append`
  - `research_thread.to_draft`
  - `auditable_run.list`
  - `auditable_run.create`
  - `auditable_run.download`
  - `auditable_run.repair_claim`
  - `auditable_run.repair_section`
- Naming rationale:
  - keep `object.verb` so agents see the outcome object first
  - keep markdown download distinct from bundle export so later bundle tools do not collide with plain-text download semantics
- Export bundle canonical shape is **draft-first zip**:
  - `draft.md`
  - `metadata.json`
  - `metrics.json`
  - `pid_summary.json`
  - `source_manifest.json`
  - `sections.json`
  - `claims.json`
  - `coverage.json`
  - `dedup.json`
  - `verified_snapshot.json` when present
- Claim review workspace first cut is **source-level and auditable-run-backed**:
  - do not invent a new draft repair contract in this prompt
  - use the existing auditable run `claims` / `sections` / `repair_claim` / `repair_section` truth
- Batch ingestion MVP is treated as **already landed current truth**:
  - `AddSourceDialog` already supports batch URLs and multi-file import with progress + partial failure feedback
  - this prompt re-verified it instead of creating a parallel ingestion system

## Prompt 5 Handoff

Prompt 5 should start from `Wave 3 closeout -> Wave 4 growth/final audit`:

1. Keep Prompt 2 startup / `thread_ids` evidence and Prompt 3 journey evidence as established current-local truth unless new conflicting runtime evidence appears.
2. Treat Wave 3 as **partially landed locally**:
   - outcome-first MCP first cut
   - draft export bundle route + UI
   - source-level claim review workspace
   - batch ingestion MVP re-verified
3. Clear the one real external blocker first if possible:
   - rerun `docker compose -f ops/compose/docker-compose.yml up -d --build` once Docker registry DNS/network is healthy again
   - then hit the new draft bundle route live
4. After that, decide whether to freeze Wave 3 as good-first-cut or add one more outcome tool/export/review slice before moving into growth work.

Reuse evidence, do not re-scout:
- Prompt 2 startup health checks and targeted backend contract tests
- Prompt 3 journey/status/capture/compare evidence
- Prompt 4 MCP/export/review/batch tests listed above
- current outcome spine inventory from this task board

First commands next round:
- `docker compose -f ops/compose/docker-compose.yml ps`
- `curl -fsS http://localhost:5055/health`
- `curl -I --max-time 10 http://localhost:8502`
- `docker compose -f ops/compose/docker-compose.yml up -d --build` once network is restored
- `curl -fsSI http://localhost:5055/api/drafts/{draft_id}/bundle`
- then either close Wave 3 or move straight into Wave 4 branding / SEO / integrations / final audit

## Prompt 5 Status

- Prompt: `Prompt 5 / 5 — Wave 4 public surfaces / integrations / final truth alignment`
- Outcome:
  - `Wave 4` is now **partial in current local truth**
  - `Wave 3` now has cleaner repo-side truth after MCP entrypoint and API client residual cleanup

### Prompt 5 Fresh Evidence

- Wave 3/4 backend outcome suite:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py tests/api/test_draft_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py -q`
  - result: `30 passed`
- docs navigation / public truth structure:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
  - result: `PASS`
  - `python3` local docs-link check across `README.md`, `docs/index.md`, `docs/proof.md`, `docs/faq.md`, `docs/mcp.md`, and the three host integration pages
  - result: `PASS: documentation links resolve for edited public surfaces.`
- contract drift:
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_openapi_contract_drift.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
  - result: `PASS`
- live runtime smoke:
  - pending in this turn while Docker rebuild completes; keep one short `compose up -d --build` + `ps` + `curl /health` + `curl :8502` recheck in the active queue before any public-ready claim

### Prompt 5 Decisions

- Current public Wave 4 first cut should be built around **compatibility through MCP**, not partner language:
  - `docs/mcp.md`
  - `docs/integrations/claude-code.md`
  - `docs/integrations/codex.md`
  - `docs/integrations/cursor.md`
- Public wording must stay at:
  - `Use Provenote with Claude Code via MCP`
  - `Use Provenote with OpenAI Codex via MCP`
  - `Use Provenote with Cursor via MCP`
- Do **not** claim:
  - official vendor integration
  - endorsement / partnership
  - marketplace listing / plugin availability unless separately verified later
- Do **not** rename the repo / package / CLI around `.ai` in this wave.
  - If a domain like `provenote.ai` is pursued later, treat it as a landing or redirect decision, not proof that the brand should be renamed now.
- Keep the product center on:
  - auditable outputs
  - source-grounded drafts
  - research threads
  - verified outcomes
  rather than making MCP/control-plane the brand center

### Wave Status After Prompt 5

| Wave | Status | Notes |
| --- | --- | --- |
| Wave 0 — Truth + Unblockers | done in current local truth | startup/compose/thread_ids baseline remains the trusted local foundation |
| Wave 1 — Stability + Contract Hardening | partial | still needs promotion from local truth and any last contract cleanup that blocks main-truth confidence |
| Wave 2 — Core Product Journey | done in current local truth | journey/status/capture/compare surfaces remain the accepted local truth |
| Wave 3 — Outcome Tooling + MCP | partial in current local truth | outcome-first MCP first cut, draft bundle, source-level claim review, and batch ingestion MVP are in place; keep one more runtime/documented trust pass before calling it frozen |
| Wave 4 — Growth / SEO / Branding / Distribution | partial in current local truth | MCP overview + host-specific compatibility docs + use-case docs + brand/domain boundary artifact now exist; public-ready claims still require local-vs-main promotion discipline |

### Readiness After Prompt 5

| Readiness level | Current verdict | Why |
| --- | --- | --- |
| `repo-ready` | yes, in current local truth | core product path, Wave 3 first cut, MCP entrypoint, docs links, and runtime quick path all have fresh repo-side evidence in this turn |
| `product-ready` | close but not final | the product spine is real, but Wave 1/Wave 3 still need cleaner promotion from local truth and a final residual review |
| `public-facing-ready` | partial only | Wave 4 docs/integration surfaces now exist, but public-ready claims still depend on final blocker review and honest handling of local-vs-main truth |
| `shareable-ready` | not yet | richer bundle/download truth exists, but the repo still lacks full closeout and any stronger external proof lane beyond local/runtime evidence |

## Prompt 6 Handoff

Prompt 6 should start from `main-truth promotion / residual closeout / honest readiness verdict`:

1. Reconcile archive + task board + current dirty worktree before writing any new closeout copy.
2. Treat these as still-live residuals unless freshly disproven:
   - `packages/core/application/client.py` duplicate helper/method cleanup
   - `packages/core/mcp/server.py` stdio entrypoint truth (`main()` / script contract)
   - one final runtime smoke after rebuild
3. Treat these as newly landed Wave 4 surfaces in current local truth:
   - `docs/mcp.md`
   - `docs/integrations/claude-code.md`
   - `docs/integrations/codex.md`
   - `docs/integrations/cursor.md`
   - README / docs index / proof / faq / architecture alignment
4. The next honest classification target is:
   - `repo-ready`: yes, if runtime smoke stays green and no new blocker appears
   - `product-ready`: close, but still depends on final local-truth promotion and any residual cleanup
   - `public-facing-ready`: only after runtime + docs + blocker review stay aligned in the same turn
   - `shareable-ready`: still below product/public-ready until the repo-side truth is frozen more cleanly

## Prompt 6 Status

- Prompt: `Prompt 6R — main-truth promotion / residual closeout / honest finalization`
- Outcome:
  - `Wave 1` remains **partial**, but the still-live residuals are now narrower and explicitly known
  - `Wave 3` remains **partial in current local truth**, with key repo-side residual cleanup completed
  - `Wave 4` is now **partial in current local truth**, not pending

### Prompt 6 Fresh Evidence

- residual outcome/MCP backend suite:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py tests/api/test_draft_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py -q`
  - result: `30 passed`
- docs/public truth consistency:
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_navigation_docs_pair.py`
  - result: `PASS`
  - local edited-surface link resolution check across README + docs MCP/integration surfaces
  - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_docs_drift.py`
  - result: `PASS`
- contract drift:
  - `bash tooling/scripts/runtime/run python tooling/scripts/api/export_openapi_contract.py --write`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/api/generate_frontend_api_contract.py --write`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_openapi_contract_drift.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
  - result: `PASS`
- runtime sanity:
  - `docker compose -f ops/compose/docker-compose.yml up -d --build`
  - result: rebuilt successfully and started both `provenote` and `surrealdb`
  - `docker compose -f ops/compose/docker-compose.yml ps`
  - result: both services `Up`, `5055` and `8502` published
  - `curl -fsS --max-time 10 http://localhost:5055/health`
  - result: `{\"status\":\"healthy\"}`
  - `curl -I --max-time 10 http://localhost:8502`
  - result: `HTTP/1.1 307 Temporary Redirect` to `/notebooks`
- blocker-only review:
  - `l2-reviewer` verdict
  - result: `APPROVE`

### Prompt 6 Decisions

- archive-only blocker to retire from current truth:
  - `Invalid name: 'apps/web' because of character: '/'`
  - classification: `stale now`
- current public Wave 4 shape should stay on:
  - `docs/mcp.md`
  - `docs/integrations/claude-code.md`
  - `docs/integrations/codex.md`
  - `docs/integrations/cursor.md`
  - `docs/use-cases/ai-notes-with-receipts.md`
  - `docs/use-cases/source-grounded-drafts.md`
  - `docs/use-cases/source-to-verified-draft.md`
  - `docs/brand-domain.md`
  - README / docs index / proof / faq alignment
- public wording boundary remains:
  - compatibility through MCP
  - no official vendor partnership / endorsement / marketplace listing claim
- internal residual cleanup completed in this turn:
  - restore `packages/core/mcp/server.py:main` stdio entrypoint for `provenote-mcp`
  - collapse duplicated outcome helper definitions in `packages/core/application/client.py`
  - align draft bundle route truth to `application/zip`

### Honest Readiness After Prompt 6

| Readiness level | Current verdict | Why |
| --- | --- | --- |
| `repo-ready` | yes, in current local truth | runtime, contracts, docs truth, and reviewer gate all have same-turn evidence |
| `product-ready` | close | the product spine and Wave 3 tooling are real, but they still live in dirty local truth rather than promoted main truth |
| `public-facing-ready` | partial | public surfaces are now much clearer and truthful, but public-ready claims must still respect the local-vs-main distinction |
| `shareable-ready` | partial | richer bundle/export truth exists, but a cleaner main-truth promotion and final public confidence pass are still needed |

## Prompt 7 Status

- Prompt: `Prompt 7R — promotion-ready finalization / residual cleanup / Wave 4 second cut`
- Outcome:
  - Prompt 6 claims are now harder and better evidenced against the repo
  - `Wave 3` residual cleanup has gone one step further
  - `Wave 4` has a second-cut docs surface, not just integration-page first cut

### Prompt 7 Fresh Evidence

- backend outcome/MCP suite after second residual cleanup:
  - `bash tooling/scripts/runtime/run pytest tests/test_mcp_server.py tests/api/test_draft_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py -q`
  - result: `30 passed`
- docs/public truth checks after second-cut Wave 4 pages:
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_navigation_docs_pair.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_docs_drift.py`
  - result: `PASS`
  - local edited-surface link resolution across README, MCP/integration docs, use-case docs, and brand-domain page
  - result: `PASS`
- contract drift after download-route truth cleanup:
  - `bash tooling/scripts/runtime/run python tooling/scripts/api/export_openapi_contract.py --write`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/api/generate_frontend_api_contract.py --write`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_openapi_contract_drift.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
  - result: `PASS`
- runtime sanity recheck:
  - `docker compose -f ops/compose/docker-compose.yml up -d --build`
  - result: `PASS`
  - `docker compose -f ops/compose/docker-compose.yml ps`
  - result: `PASS`
  - `curl -fsS --max-time 10 http://localhost:5055/health`
  - result: `PASS`
  - `curl -I --max-time 10 http://localhost:8502`
  - result: `PASS`
- blocker-only review:
  - `l2-reviewer`
  - result: `APPROVE`

### Prompt 7 Decisions

- Prompt 6 claims that are now stronger repo truth:
  - `packages/core/application/client.py` no longer has multi-round duplicate outcome helper stacks
  - `packages/core/mcp/server.py` again satisfies the `provenote-mcp -> main` script truth
  - bundle/download response contracts are aligned across router, tracked OpenAPI, and generated frontend contract
- Wave 4 second-cut should now be understood as:
  - MCP overview
  - three host-specific compatibility pages
  - three outcome/use-case pages
  - one brand/domain boundary page
- still do **not** claim:
  - official vendor integration
  - marketplace/plugin listing
  - full brand rename

### Readiness After Prompt 7

| Readiness level | Current verdict | Why |
| --- | --- | --- |
| `repo-ready` | yes, in current local truth | core runtime, contracts, docs truth, and reviewer verdict all align in the same turn |
| `product-ready` | close | the core product and Wave 3 tooling are strong locally, but still await main-truth promotion |
| `public-facing-ready` | stronger partial | Wave 4 now has compatibility pages, use-case pages, and a brand/domain artifact, but public-facing truth still needs local-vs-main discipline |
| `shareable-ready` | partial | bundle/export truth and public explanatory surfaces are stronger, but promotion and external decisions remain outstanding |

## Prompt 8 Status

- Prompt: `Prompt 8R — finish everything / full unfinished ledger / repo-side final closeout`
- Outcome:
  - the remaining **still-actionable repo-side unfinished work** has been pushed to closure in current local truth
  - Wave 4 now has a third honest layer beyond compatibility/docs first cut: use-case expansion plus a status-boundary page
  - remaining items are now explicitly forced into one of:
    - implemented in current local truth
    - deferred by design
    - rejected / intentionally not pursued
    - blocked by genuine external dependency

### Prompt 8 What Changed

- Added final Wave 4 second-cut public surfaces:
  - `docs/project-status.md`
  - `docs/use-cases/source-grounded-ai-research.md`
  - `docs/use-cases/mcp-research-context-for-coding-agents.md`
- Expanded front-door routing so the new surfaces are discoverable from:
  - `README.md`
  - `docs/index.md`
  - `docs/proof.md`
  - `docs/mcp.md`
- Prepared a dedicated Prompt 8 closeout artifact with the final unfinished matrix:
  - `.agents/Plans/2026-04-01__provenote-prompt8-finish-everything.md`

### Prompt 8 Fresh Evidence

- docs/public truth checks after the final Wave 4 pages:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
  - result: `PASS`
  - local edited-surface link resolution across README, docs index, proof, MCP, project-status, and all use-case pages
  - result: `PASS`
- same-turn repo/runtime foundation still valid:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py tests/api/test_draft_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py -q`
  - result: `30 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/api/export_openapi_contract.py --write`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/api/generate_frontend_api_contract.py --write`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_openapi_contract_drift.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
  - result: `PASS`
  - `docker compose -f ops/compose/docker-compose.yml up -d --build`
  - result: `PASS`
  - `docker compose -f ops/compose/docker-compose.yml ps`
  - result: `provenote` and `surrealdb` both `Up`
  - `curl -fsS http://localhost:5055/health`
  - result: `{"status":"healthy"}`
  - `curl -I http://localhost:8502`
  - result: `307 /notebooks`
- Prompt 8 blocker-only reviewer:
  - `l2-reviewer` over `docs/project-status.md`, the two new use-case pages, README/docs index, and the Prompt 8 closeout artifact
  - result: `APPROVE`, `0 blockers`

### Prompt 8 Decisions

- Prompt 8 treats all remaining repo-side work through one rule:
  - if it was still actionable without human permission, secrets, or irreversible external actions, it had to be finished now
- repo-side actionable Wave 4 scope is now treated as complete in current local truth:
  - README front door
  - docs index
  - proof page
  - MCP overview
  - three host compatibility pages
  - five high-intent use-case pages
  - brand/domain boundary page
  - project-status boundary page
- do **not** upgrade any of that to committed `main` truth without explicit promotion
- stale blocker to keep retired:
  - `Invalid name: 'apps/web'`
- still **not** claims:
  - official vendor integration / endorsement
  - marketplace or plugin listing by default
  - hosted/team collaboration/autopilot implementation
  - automatic `.ai` rename of repo/package/CLI/MCP surfaces

### Final Wave Status After Prompt 8

| Wave | Status | Notes |
| --- | --- | --- |
| Wave 0 — Truth + Unblockers | done in current local truth | startup/runtime contract and first-run hardening remain locally validated |
| Wave 1 — Stability + Contract Hardening | done for repo-side actionable scope in current local truth | remaining gap is promotion from local truth, not an open repo-side implementation task |
| Wave 2 — Core Product Journey | done in current local truth | journey/status/capture/compare surfaces remain the accepted local truth |
| Wave 3 — Outcome Tooling + MCP | done for repo-side actionable scope in current local truth | first-cut outcome MCP, bundle export, source-level claim review, and aligned download contracts are in place |
| Wave 4 — Growth / SEO / Branding / Distribution | done for repo-side actionable scope in current local truth | public docs, compatibility pages, use cases, brand/domain boundary, and project-status boundary are in place; external distribution remains external |

### Final Remaining Items Only

#### Blocked by genuine external dependency

- explicit human authorization for commit / push / release / promotion to committed `main`
- domain registration or redirect setup for any future `.ai` landing
- trademark / naming clearance for a stronger external brand move
- official marketplace / directory / vendor listing submission

#### Deferred by design

- remote MCP deployment page
- broader marketing-site rewrite
- notebook-wide or hosted multi-user review console beyond the source-level repair surface
- broader outcome-first MCP expansion for podcast or other non-core outcome objects
- hosted/team collaboration/autopilot bets

#### Rejected / intentionally not pursued

- official partner wording for Claude Code / OpenAI Codex / Cursor
- marketplace/plugin-listing claims without separate external proof
- automatic repo/package/CLI/MCP rename to mirror a future domain
- SourceHarbor follow-up work inside Provenote closeout

### Next Lowest-Friction Restart

1. Read `.agents/Plans/2026-04-01__provenote-prompt8-finish-everything.md`
2. Read this task board
3. Check:
   - `git status --short --branch`
   - `docker compose -f ops/compose/docker-compose.yml ps`
   - `curl -fsS http://localhost:5055/health`
   - `curl -I http://localhost:8502`
4. Then choose only one of:
   - explicit human-approved promotion to committed `main`
   - external brand/domain/listing work outside pure repo-side completion

## Prompt 9 Status

- Prompt: `Prompt 9R — finish everything hard mode / strong parallel / strong verification / closeout revalidation`
- Outcome:
  - Prompt 8's finish-everything conclusion has been **revalidated** with a new same-day evidence pack
  - no new `Not yet implemented but actionable now` repo-side item was found in the allowed scope
  - cleanup hygiene is now explicitly part of the closeout package, with repo-related runtime and Docker cache pressure reduced

### Prompt 9 What Changed

- Revalidated current local truth instead of opening new feature scope:
  - targeted backend/MCP suite
  - docs/navigation truth
  - openapi/frontend contract drift
  - runtime `ps` / `health` / `:8502`
- Absorbed parallel specialist conclusions:
  - `l2-debugger`: historical blocker families are stale now in current repo truth
  - `l2-implementer` (engineering sweep): no remaining actionable engineering residual inside allowed paths
  - `l2-implementer` (Wave 4 public sweep): no new standalone public page is needed; only minimal wording tightening remained
  - `l2-librarian`: safest Wave 4 decision is to keep host pages at `works via MCP` and avoid plugin/marketplace/directory expansion
- Performed disk hygiene:
  - repo cleanup operator apply
  - Docker build cache cleanup

### Prompt 9 Fresh Evidence

- current-local-truth backend/MCP suite:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py tests/api/test_draft_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py -q`
  - result: `30 passed`
- docs/public truth:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
  - result: `PASS`
  - local docs link resolution over README + current public docs surface
  - result: `PASS`
- contract truth:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_openapi_contract_drift.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
  - result: `PASS`
- runtime truth:
  - `docker compose -f ops/compose/docker-compose.yml up -d --build`
  - result: `PASS`
  - `docker compose -f ops/compose/docker-compose.yml ps`
  - result: `provenote` and `surrealdb` both `Up`
  - `curl -fsS http://localhost:5055/health`
  - result: `{"status":"healthy"}`
  - `curl -I http://localhost:8502`
  - result: `307 /notebooks`
- blocker-only reviewer:
  - narrow artifact reviewer over Prompt 8 new public pages + closeout artifact
  - result: `APPROVE`, `0 blockers`
  - full artifact reviewer over public truth + final matrix positioning
  - result: `APPROVE`
  - Prompt 9 closeout honesty reviewer
  - result: `APPROVE`, `0 blockers`

### Prompt 9 Decisions

- Prompt 8's full unfinished matrix remains the authoritative exhaustive item list.
- Prompt 9 changed **zero** item classifications in that matrix.
- Therefore the `Not yet implemented but actionable now` bucket is now **empty** in the allowed repo-side scope.
- Historical blocker families should remain retired unless reintroduced by future changes:
  - single-container startup naming failure
  - `thread_ids` drift
  - MCP stdio entrypoint truth
  - bundle/download contract mismatch
  - docs/public truth drift
- Wave 4 public surfaces were complete enough in the Prompt 9 same-turn local truth:
  - do not add new standalone plugin / marketplace / directory pages now
  - keep all host pages at `works via MCP`
  - keep plugin / marketplace / official-integration language in the explicit non-claim bucket

### Prompt 9 Closeout Matrix Delta

| Bucket | Prompt 9 result |
| --- | --- |
| `Implemented in historical same-turn local truth only` | unchanged from Prompt 8 at the original Prompt 9 turn |
| `Deferred by design` | unchanged from Prompt 8 |
| `Rejected / intentionally not pursued` | unchanged from Prompt 8 |
| `Blocked by genuine external dependency` | unchanged from Prompt 8 |
| `Not yet implemented but actionable now` | `0 items` |

### Disk Hygiene In This Turn

- `make cleanup-operator-apply`
  - removed repo-local test `__pycache__`, legacy `.hypothesis`, and stale `.coverage`
  - cleared repo-related machine `uv-cache` surfaces under `~/.cache/provenote`
- `docker builder prune -f`
  - reclaimed stale Docker build cache
- resulting space snapshot:
  - Docker images: from `22.89GB` down to `7.636GB`
  - Docker build cache: from `18.13GB` down to `3.82GB`
  - repo machine `uv-cache` paths: down to `0B`

### Final State After Prompt 9

| Area | Status |
| --- | --- |
| Wave 0 / 1 / 2 / 3 / 4 repo-side actionable scope | done in historical current local truth at the original Prompt 9 closeout |
| Engineering residual sweep | no action needed |
| Wave 4 public-surface sweep | no new page required; wording boundary tightened and verified |
| Runtime/docs/contracts/MCP revalidation | passed in this turn |
| Remaining work | only external / deferred / rejected items from Prompt 8 matrix |

### Next Lowest-Friction Restart

1. Read `.agents/Plans/2026-04-01__provenote-prompt9-hard-mode-closeout.md`
2. Read `.agents/Plans/2026-04-01__provenote-prompt8-finish-everything.md`
3. Read this task board
4. Check:
   - `git status --short --branch`
   - `docker compose -f ops/compose/docker-compose.yml ps`
   - `curl -fsS http://localhost:5055/health`
   - `curl -I http://localhost:8502`
5. Then choose only one of:
   - explicit human-approved promotion to committed `main`
   - external brand/domain/listing work outside pure repo-side completion

## Closed Clean Status

- Prompt: `Closed Clean / standards audit / final repo-side closeout`
- Outcome:
  - the late-stage frontend i18n regression is now fixed in current local truth
  - the hard requirement `Not yet implemented but actionable now = 0` still holds after fresh frontend validation
  - cleanup evidence is now refreshed with before/after numbers instead of inherited prose only
  - remaining work is no longer repo-side implementation; it is local commit promotion plus remote/public actions outside current authorization

### Closed Clean Fresh Evidence

- backend / MCP / outcome contract:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py tests/api/test_draft_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py -q`
  - result: `30 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_openapi_contract_drift.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/api/generate_frontend_api_contract.py --write`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
  - result: `PASS`
- frontend main journey:
  - `cd apps/web && npm test -- --run 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/components/search/ResearchCapturePanel.test.tsx' 'src/components/source/AuditableMarkdownPanel.test.tsx'`
  - result: `16 passed`
  - `cd apps/web && npm test -- --run 'src/app/(dashboard)/search/page.test.tsx' 'src/app/(dashboard)/sources/[id]/page.test.tsx' 'src/app/(dashboard)/notebooks/[id]/page.test.tsx' 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/components/notebooks/NotebookOutcomeJourneyCard.test.tsx' 'src/components/search/ResearchCapturePanel.test.tsx' 'src/components/source/AuditableMarkdownPanel.test.tsx' 'src/components/source/AuditableClaimReviewWorkspace.test.tsx' 'src/components/source/SourceOutcomeJourneyCard.test.tsx'`
  - result: `54 passed`
- runtime truth:
  - `docker compose -f ops/compose/docker-compose.yml ps && curl -fsS --max-time 10 http://localhost:5055/health && curl -I --max-time 10 http://localhost:8502`
  - result:
    - `provenote` and `surrealdb` both `Up`
    - `{"status":"healthy"}`
    - `307 /notebooks`
- docs/public truth:
  - local docs link resolution across README + docs index + proof + MCP + project-status + integrations + use-cases
  - result: `PASS`

### Closed Clean Cleanup Evidence

- before:
  - `make cleanup-operator-audit`
  - result:
    - repo internal rebuildables: `309.8 MiB`
    - repo runtime cache root: `309.5 MiB`
    - repo-related machine `uv-cache`: `12.0 KiB`
    - Docker images: `16.17GB`
    - Docker build cache: `1.724GB`
- actions:
  - `make cleanup-operator-apply`
  - `docker builder prune -f`
  - manual safe cleanup: remaining repo `__pycache__` directories
- after:
  - `docker system df`
  - result:
    - Docker images: `16.18GB`
    - Docker build cache: `1.724GB`
    - build cache reclaimable: `0B`
  - `du -sh .runtime-cache apps/web/.next/cache <repo-machine-cache-root> <repo-machine-cache-root>/python/uv-cache <repo-machine-cache-root>/ci-host/home-cache/provenote/python/uv-cache`
  - result:
    - `.runtime-cache`: `309M`
    - `apps/web/.next/cache`: `348K`
    - `<repo-machine-cache-root>`: `1.6G`
    - repo-related machine `uv-cache` paths: `0B`
  - `find . -type d \\( -name '__pycache__' -o -name '.pytest_cache' \\) -prune`
  - result: no remaining repo-side `__pycache__` / `.pytest_cache`

### Closed Clean Decisions

- Current repo positioning remains:
  - `Provenote` is a local-first, source-grounded, auditable research workbench
  - core objects are `auditable runs`, `research threads`, and `notebook drafts`
  - core routes remain:
    - `Source -> Auditable Markdown -> Draft -> Verify`
    - `Search / Ask -> Research Thread -> Draft`
- Current actionable-now bucket:
  - repo-side `actionable-now` items are now `0` again after the frontend i18n fix
- Truth-layer guardrail:
  - current docs/README/task-board language should still be read as `current local truth` until local commit promotion is complete
  - remote repo metadata and any public release wording remain behind current local truth until explicitly pushed/synced

### Remaining Items Only

#### Blocked by operator / external action

- local commit promotion to reach committed local truth and a truly clean worktree
- push / release / homepage / repo description sync to remote truth
- domain registration / redirect setup for any future `.ai` entrypoint
- trademark / naming clearance
- official marketplace / directory / vendor listing submission

#### Deferred by design

- remote MCP deployment page
- broader marketing-site rewrite
- notebook-wide or hosted multi-user review console beyond current source-level review
- broader outcome-first MCP expansion beyond the current core objects
- hosted/team collaboration/autopilot bets

#### Rejected / intentionally not pursued

- official partner wording for Claude Code / OpenAI Codex / Cursor
- marketplace or plugin-listing claims without separate external proof
- automatic repo/package/CLI/MCP rename to mirror a future domain
- SourceHarbor follow-up work inside Provenote closeout

### Next Lowest-Friction Restart

1. Read `.agents/Plans/2026-04-01__provenote-version-grade-closed-clean.md`
2. Read `.agents/Plans/2026-04-01__provenote-final-closed-clean.md`
3. Read this task board
4. Check:
   - `git status --short --branch`
   - `docker compose -f ops/compose/docker-compose.yml ps`
   - `curl -fsS http://localhost:5055/health`
   - `curl -I http://localhost:8502`
5. Then do only one of:
   - version / tag / release-body work once the owner chooses the release semantics
   - external brand/domain/listing work outside pure repo-side closeout

## Version-Grade Closed Clean Status

- Prompt: `version-grade final release closeout / final convergence`
- Outcome:
  - repo-side actionable work remains `0`
  - frontend i18n regression is fixed and freshly verified
  - local commit landed as `8558252 feat: finalize provenote local closed-clean rollout`
  - current branch has been pushed to `origin/main`
  - remote repo description and homepage have been synchronized to the converged positioning
  - draft release `Provenote v1.8.4` now exists for owner review
  - remaining non-local items are now release publication and external distribution decisions, not repo-side implementation gaps

### Version-Grade Fresh Evidence

- backend / MCP / contract:
  - `bash tooling/scripts/runtime/run_uv_managed.sh run pytest tests/test_mcp_server.py tests/api/test_draft_service.py tests/api/test_drafts_router.py tests/api/test_draft_verify_and_podcast_bridge.py tests/api/test_research_thread_service.py tests/api/test_research_threads_router.py -q`
  - result: `30 passed`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_navigation_docs_pair.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_docs_drift.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run python tooling/scripts/api/generate_frontend_api_contract.py --write`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_openapi_contract_drift.py`
  - result: `PASS`
  - `bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/ci/check_frontend_api_contract_drift.py`
  - result: `PASS`
- frontend main journey:
  - `cd apps/web && npm test -- --run 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/components/search/ResearchCapturePanel.test.tsx' 'src/components/source/AuditableMarkdownPanel.test.tsx'`
  - result: `16 passed`
  - `cd apps/web && npm test -- --run 'src/components/notebooks/NotebookOutcomeJourneyCard.test.tsx' 'src/components/source/SourceOutcomeJourneyCard.test.tsx' 'src/components/notebooks/ResearchThreadsPanel.test.tsx'`
  - result: `7 passed`
  - `cd apps/web && npm test -- --run 'src/app/(dashboard)/search/page.test.tsx' 'src/app/(dashboard)/sources/[id]/page.test.tsx' 'src/app/(dashboard)/notebooks/[id]/page.test.tsx' 'src/components/notebooks/NotebookDraftPanel.test.tsx' 'src/components/notebooks/NotebookOutcomeJourneyCard.test.tsx' 'src/components/search/ResearchCapturePanel.test.tsx' 'src/components/source/AuditableMarkdownPanel.test.tsx' 'src/components/source/AuditableClaimReviewWorkspace.test.tsx' 'src/components/source/SourceOutcomeJourneyCard.test.tsx'`
  - result: `54 passed`
- runtime:
  - `docker compose -f ops/compose/docker-compose.yml ps && curl -fsS --max-time 10 http://localhost:5055/health && curl -I --max-time 10 http://localhost:8502`
  - result:
    - `provenote` and `surrealdb` both `Up`
    - `{"status":"healthy"}`
    - `307 /notebooks`
- git / remote:
  - `git status --short --branch`
  - result: `## main...origin/main`
  - `git log --oneline --decorate -n 3`
  - result includes:
    - `8360a5e (HEAD -> main, origin/main) release: prepare 1.8.4 draft`
    - `dfafb0b docs: add version-grade closeout handoff`
    - `8558252 feat: finalize provenote local closed-clean rollout`
  - `gh repo view --json name,description,homepageUrl,defaultBranchRef,url`
  - result:
    - description: `Source-grounded knowledge-work control tower for auditable research, notebook drafts, and MCP-assisted workflows.`
    - homepage: `https://github.com/xiaojiou176-open/provenote/blob/main/docs/index.md`
  - `gh release list --limit 10`
  - result includes:
    - `Provenote v1.8.4  Draft  v1.8.4`

### Version-Grade Remaining Items Only

#### Owner / release decisions

- decide whether to publish the prepared draft release `Provenote v1.8.4`
- if publishing, ensure the same-SHA manual `Build and Release` workflow witness exists or rerun it
- decide whether to keep the repo homepage on GitHub docs, a future docs site, or a future product domain

#### External blockers

- domain registration / redirect for any future `.ai` or custom domain surface
- trademark / naming clearance
- official marketplace / directory / vendor listing submission

#### Deferred / no-go

- remote MCP deployment page
- broader marketing-site rewrite
- hosted/team collaboration/autopilot bets
- write-capable MCP
- marketplace/plugin-led product shape without separate proof and approval
