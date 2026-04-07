.PHONY: run apps/web check ruff database lint api start-all stop-all status clean-cache worker worker-start worker-stop worker-restart quality-fast quality-full quality-live test-gate-fast test-gate-full guard-all ci-local-preflight governance-final
.PHONY: dev-local-up dev-local-down dev-local-health
.PHONY: docker-buildx-prepare docker-buildx-clean docker-buildx-reset docker-runtime-audit cleanup-operator-audit cleanup-operator-apply
.PHONY: cleanup-operator-dry-run cleanup-operator-rebuildable cleanup-operator-aggressive
.PHONY: docker-push docker-push-latest docker-release docker-build-local tag export-docs
.PHONY: test-backend-cov test-apps/web-coverage test-e2e-chromium test-e2e-real-smoke test-mutation-python test-live-llm test-live-external-web post-test-housekeeping test-all

# Get version from pyproject.toml
VERSION := $(shell grep -m1 version pyproject.toml | cut -d'"' -f2)
export UV_PROJECT_ENVIRONMENT ?= .runtime-cache/venv/default
export SETUPTOOLS_EGG_BASE ?= .runtime-cache/build/egg-info
MANAGED_UV := bash tooling/scripts/runtime/run_uv_managed.sh

# Current fork publish defaults:
# - local builds always tag a repo-local image name
# - remote pushes require explicit maintainer-controlled targets
# - Docker Hub publishing remains opt-in via DOCKERHUB_IMAGE_REPOSITORY
LOCAL_DOCKER_IMAGE ?= provenote-local
CI_IMAGE_NAME ?= $(shell sed -n 's/^CI_IMAGE_NAME=//p' config/ci-toolchain.env | head -n1)
GHCR_IMAGE ?=
DOCKERHUB_IMAGE ?= $(DOCKERHUB_IMAGE_REPOSITORY)

# Build platforms
PLATFORMS := linux/amd64,linux/arm64
GUARD_MODE ?= full
BACKEND_COVERAGE_SCOPE ?= phase1
VALID_BACKEND_COVERAGE_SCOPES := phase0 phase1
RUN_PERFORMANCE_BENCHMARKS ?= 0
VALID_RUN_PERFORMANCE_BENCHMARKS := 0 1
PYTHON_CORE_MARK_EXPR := not property and not live
export HYPOTHESIS_STORAGE_DIRECTORY ?= .runtime-cache/test/hypothesis

ifneq ($(filter $(BACKEND_COVERAGE_SCOPE),$(VALID_BACKEND_COVERAGE_SCOPES)),$(BACKEND_COVERAGE_SCOPE))
$(warning Unknown BACKEND_COVERAGE_SCOPE='$(BACKEND_COVERAGE_SCOPE)', fallback to 'phase0')
BACKEND_COVERAGE_SCOPE := phase0
endif

ifneq ($(filter $(RUN_PERFORMANCE_BENCHMARKS),$(VALID_RUN_PERFORMANCE_BENCHMARKS)),$(RUN_PERFORMANCE_BENCHMARKS))
$(warning Unknown RUN_PERFORMANCE_BENCHMARKS='$(RUN_PERFORMANCE_BENCHMARKS)', fallback to '0')
RUN_PERFORMANCE_BENCHMARKS := 0
endif

BACKEND_COV_ARGS_PHASE0 := --cov=services.api.main --cov=packages.core.application.models --cov=services.api.routers.auditable_runs --cov=packages.core.auditable
BACKEND_COV_ARGS_PHASE1 := --cov=services.api --cov=services.worker --cov=packages.core.ai --cov=packages.core.graphs --cov=packages.core.database --cov=packages.core.utils --cov=packages.core.auditable

ifeq ($(BACKEND_COVERAGE_SCOPE),phase1)
BACKEND_COV_ARGS := $(BACKEND_COV_ARGS_PHASE1)
else
BACKEND_COV_ARGS := $(BACKEND_COV_ARGS_PHASE0)
endif

ifeq ($(RUN_PERFORMANCE_BENCHMARKS),1)
BACKEND_PERF_IGNORE_ARGS :=
else
BACKEND_PERF_IGNORE_ARGS := --ignore=tests/performance
endif

database:
	docker compose -p provenote up -d surrealdb

run:
	@echo "⚠️  Warning: Starting apps/web only. For full functionality, use 'make start-all'"
	cd apps/web && npm run dev

apps/web:
	cd apps/web && npm run dev

lint:
	$(MANAGED_UV) run python -m mypy .

ruff:
	ruff check . --fix

test-backend-cov:
	@echo "BACKEND_COVERAGE_SCOPE=$(BACKEND_COVERAGE_SCOPE)"
	@echo "BACKEND_COV_ARGS=$(BACKEND_COV_ARGS)"
	@echo "RUN_PERFORMANCE_BENCHMARKS=$(RUN_PERFORMANCE_BENCHMARKS)"
	@echo "PYTHON_CORE_MARK_EXPR=$(PYTHON_CORE_MARK_EXPR)"
	@echo "BACKEND_PERF_IGNORE_ARGS=$(BACKEND_PERF_IGNORE_ARGS)"
	rm -f .coverage .coverage.*
	rm -f .runtime-cache/test/coverage/backend/coverage.xml
	mkdir -p .runtime-cache/test/coverage/backend
	OPEN_NOTEBOOK_SKIP_MIGRATIONS=true $(MANAGED_UV) run python -m pytest tests/ -v -m "$(PYTHON_CORE_MARK_EXPR)" $(BACKEND_PERF_IGNORE_ARGS) $(BACKEND_COV_ARGS) --cov-branch --cov-fail-under=0 --cov-report=term-missing --cov-report=xml:.runtime-cache/test/coverage/backend/coverage.xml
	$(MANAGED_UV) run python tooling/scripts/ci/check_coverage_thresholds.py --backend-xml .runtime-cache/test/coverage/backend/coverage.xml --backend-scope $(BACKEND_COVERAGE_SCOPE) --skip-apps/web

test-apps/web-coverage:
	rm -f .runtime-cache/test/coverage/apps/web/lcov.info
	cd apps/web && npm run test:coverage

test-e2e-chromium:
	bash tooling/scripts/ci/run_with_retry.sh --label e2e-chromium --max-retries $${E2E_MAX_RETRIES:-2} -- \
	  bash -lc "cd apps/web && npm run test:e2e:install && npm run test:e2e -- --project=chromium --workers=1"

test-e2e-real-smoke:
	bash tooling/scripts/ci/with_heartbeat.sh --label e2e-real-smoke --interval 30 -- \
	  bash tooling/scripts/ci/run_real_backend_smoke.sh

test-mutation-python:
	MUTATION_PROFILE=$${MUTATION_PROFILE:-core} MUTATION_MAX_CHILDREN=$${MUTATION_MAX_CHILDREN:-4} bash tooling/scripts/ci/run_mutation_profile.sh

test-live-llm:
	bash tooling/scripts/ci/with_heartbeat.sh --label live-llm --interval $${LIVE_HEARTBEAT_SECONDS:-15} -- \
	  bash -lc "RUN_LIVE_TESTS=1 bash tooling/scripts/ci/run_with_retry.sh --label live-llm --max-retries $${LIVE_MAX_RETRIES:-2} -- bash tooling/scripts/runtime/run_uv_managed.sh run python -m pytest tests/live/test_google_live_smoke.py -v -m live"

test-live-external-web:
	bash tooling/scripts/ci/with_heartbeat.sh --label live-external-web --interval $${LIVE_HEARTBEAT_SECONDS:-15} -- \
	  bash -lc "cd apps/web && RUN_LIVE_TESTS=1 LIVE_EXTERNAL_WEB_ENABLED=1 LIVE_EXTERNAL_SITE_URL=$${LIVE_EXTERNAL_SITE_URL:-https://example.com/} bash ../tooling/scripts/ci/run_with_retry.sh --label live-external-web --max-retries $${LIVE_MAX_RETRIES:-2} -- npm run test:e2e:external-live -- --project=chromium"

post-test-housekeeping:
	bash tooling/scripts/ci/post_test_housekeeping.sh

test-all: test-backend-cov test-apps/web-coverage test-e2e-chromium post-test-housekeeping

quality-fast:
	bash tooling/scripts/ci/run_unified_test_gate.sh fast

quality-full:
	@if [ "$${OPEN_NOTEBOOK_CI_HOST_BYPASS:-0}" = "1" ]; then \
		set -e; \
		python3 tooling/scripts/ci/check_architecture_guard.py & pid1=$$!; \
		python3 tooling/scripts/ci/check_google_genai_usage.py & pid2=$$!; \
		python3 tooling/scripts/ci/check_first_party_file_length.py & pid3=$$!; \
		status=0; \
		wait $$pid1 || status=1; \
		wait $$pid2 || status=1; \
		wait $$pid3 || status=1; \
		test $$status -eq 0; \
		bash tooling/scripts/ci/run_unified_test_gate.sh full; \
		make test-e2e-real-smoke; \
		GIT_TERMINAL_PROMPT=0 bash tooling/scripts/ci/check_upstream_drift.sh --strict-divergence --no-fetch; \
		bash tooling/scripts/ci/post_test_housekeeping.sh --cleanup-only; \
	else \
		bash tooling/scripts/ci/run_in_consistent_container.sh --profile full -- \
		  bash -lc 'OPEN_NOTEBOOK_CI_IN_CONTAINER=1 python3 tooling/scripts/ci/check_architecture_guard.py & pid1=$$!; OPEN_NOTEBOOK_CI_IN_CONTAINER=1 python3 tooling/scripts/ci/check_google_genai_usage.py & pid2=$$!; OPEN_NOTEBOOK_CI_IN_CONTAINER=1 python3 tooling/scripts/ci/check_first_party_file_length.py & pid3=$$!; status=0; wait $$pid1 || status=1; wait $$pid2 || status=1; wait $$pid3 || status=1; test $$status -eq 0; OPEN_NOTEBOOK_CI_IN_CONTAINER=1 bash tooling/scripts/ci/run_unified_test_gate.sh full; OPEN_NOTEBOOK_CI_IN_CONTAINER=1 make test-e2e-real-smoke; GIT_TERMINAL_PROMPT=0 bash tooling/scripts/ci/check_upstream_drift.sh --strict-divergence --no-fetch; bash tooling/scripts/ci/post_test_housekeeping.sh --cleanup-only'; \
	fi

test-gate-fast:
	bash tooling/scripts/ci/run_unified_test_gate.sh fast

test-gate-full:
	bash tooling/scripts/ci/run_unified_test_gate.sh full

guard-all:
	LONG_TESTS_PARALLEL=$${LONG_TESTS_PARALLEL:-1} HEARTBEAT_INTERVAL_SECONDS=$${HEARTBEAT_INTERVAL_SECONDS:-30} bash tooling/scripts/ci/run_unified_test_gate.sh $(GUARD_MODE)

ci-local-preflight:
	bash tooling/scripts/ci/local_preflight_before_push.sh $${LOCAL_PREFLIGHT_MODE:+--mode $$LOCAL_PREFLIGHT_MODE}

governance-final:
	bash tooling/scripts/ci/post_test_housekeeping.sh --cleanup-only
	python3 tooling/scripts/ci/check_root_cleanliness.py --mode authoritative
	$(MANAGED_UV) run python tooling/scripts/ci/check_entrypoint_contract.py
	$(MANAGED_UV) run python tooling/scripts/ci/check_output_path_policy.py
	$(MANAGED_UV) run python tooling/scripts/ci/check_runtime_surfaces.py
	$(MANAGED_UV) run python tooling/scripts/ci/check_layer_boundaries.py
	$(MANAGED_UV) run python tooling/scripts/ci/check_log_contract.py
	$(MANAGED_UV) run python tooling/scripts/ci/check_log_sink_integrity.py
	$(MANAGED_UV) run python tooling/scripts/ci/check_frontend_logging_contract.py
	$(MANAGED_UV) run python tooling/scripts/ci/check_openapi_contract_drift.py
	$(MANAGED_UV) run python tooling/scripts/ci/check_external_surfaces.py
	$(MANAGED_UV) run python tooling/scripts/ci/check_no_floating_external_inputs.py
	$(MANAGED_UV) run python tooling/scripts/ci/check_docs_render_freshness.py
	bash tooling/scripts/ci/check_cache_wipe_rebuild.sh full
	bash tooling/scripts/ci/run_unified_test_gate.sh full

quality-live:
	@if [ -z "$${GEMINI_API_KEY:-}" ]; then \
		echo "ERROR: Set GEMINI_API_KEY before running quality-live"; \
		exit 1; \
	fi
	$(MANAGED_UV) run python tooling/scripts/ci/check_live_test_static_audit.py
	$(MAKE) test-live-llm
	$(MAKE) test-live-external-web

# === Docker Build Setup ===
docker-buildx-prepare:
	@docker buildx inspect multi-platform-builder >/dev/null 2>&1 || \
		docker buildx create --use --name multi-platform-builder --driver docker-container
	@docker buildx use multi-platform-builder

docker-buildx-clean:
	@echo "🧹 Cleaning up buildx builders..."
	@docker buildx rm multi-platform-builder 2>/dev/null || true
	@docker ps -a | grep buildx_buildkit | awk '{print $$1}' | xargs -r docker rm -f 2>/dev/null || true
	@echo "✅ Buildx cleanup complete!"

docker-buildx-reset: docker-buildx-clean docker-buildx-prepare
	@echo "✅ Buildx reset complete!"

cleanup-operator-audit: cleanup-operator-dry-run

cleanup-operator-apply: cleanup-operator-rebuildable

docker-runtime-audit:
	@echo "🔍 Auditing repo-related Docker runtime surfaces..."
	@docker images --format '{{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}' | grep "^$(CI_IMAGE_NAME):" || true
	@docker buildx ls || true
	@docker system df -v || true

cleanup-operator-dry-run:
	@echo "🧪 Provenote cleanup operator path (dry-run)"
	@echo "1) audit repo-owned runtime surfaces"
	bash tooling/scripts/ops/audit_space_surfaces.sh --cleanup-owner cleanup_runtime_cache.sh --action-filter safe_clear,cautious_clear
	@echo ""
	@echo "2) audit repo-related machine cache candidates"
	bash tooling/scripts/ops/cleanup_machine_cache.sh --mode audit-only
	@echo ""
	@echo "3) preview repo-local runtime cleanup"
	bash tooling/scripts/ops/cleanup_runtime_cache.sh --dry-run
	@echo ""
	@echo "4) preview buildx cleanup candidates (operator action only)"
	@echo "   make docker-buildx-clean"
	@echo "5) inspect Docker/runtime pressure"
	@echo "   make docker-runtime-audit"

cleanup-operator-rebuildable:
	@echo "🧹 Provenote cleanup operator path (rebuildable)"
	@echo "1) remove buildx builder residue"
	$(MAKE) docker-buildx-clean
	@echo "2) clear repo-local runtime rebuildables"
	bash tooling/scripts/ops/cleanup_runtime_cache.sh
	@echo "3) apply repo-related machine-cache cleanup for stale bootstrap snapshots"
	bash tooling/scripts/ops/cleanup_machine_cache.sh --mode apply --include-stale-bootstrap-snapshots

cleanup-operator-aggressive:
	@echo "🧹 Provenote cleanup operator path (aggressive)"
	@echo "1) remove buildx builder residue"
	$(MAKE) docker-buildx-clean
	@echo "2) clear repo-local runtime rebuildables"
	bash tooling/scripts/ops/cleanup_runtime_cache.sh
	@echo "3) apply repo-related machine-cache cleanup with stale bootstrap snapshots and historical candidates"
	bash tooling/scripts/ops/cleanup_machine_cache.sh --mode apply --include-stale-bootstrap-snapshots --include-historical-candidates

# === Docker Build Targets ===

# Build production image for local platform only (no push)
docker-build-local:
	@echo "🔨 Building production image locally ($(shell uname -m))..."
	docker build \
		-t $(LOCAL_DOCKER_IMAGE):$(VERSION) \
		-t $(LOCAL_DOCKER_IMAGE):local \
		.
	@echo "✅ Built $(LOCAL_DOCKER_IMAGE):$(VERSION) and $(LOCAL_DOCKER_IMAGE):local"
	@echo "Run with: docker run -p 5055:5055 -p 3000:3000 $(LOCAL_DOCKER_IMAGE):local"

# Build and push version tags ONLY (no latest) for both regular and single images
docker-push: docker-buildx-prepare
	@if [ -z "$(GHCR_IMAGE)" ] && [ -z "$(DOCKERHUB_IMAGE)" ]; then \
		echo "ERROR: Set GHCR_IMAGE and/or DOCKERHUB_IMAGE (or DOCKERHUB_IMAGE_REPOSITORY) before pushing release images."; \
		exit 1; \
	fi
	@echo "📤 Building and pushing version $(VERSION) to the configured registries..."
	@regular_tags=""; \
	if [ -n "$(GHCR_IMAGE)" ]; then regular_tags="$$regular_tags -t $(GHCR_IMAGE):$(VERSION)"; fi; \
	if [ -n "$(DOCKERHUB_IMAGE)" ]; then regular_tags="$$regular_tags -t $(DOCKERHUB_IMAGE):$(VERSION)"; fi; \
	echo "🔨 Building regular image..."; \
	eval "docker buildx build --pull --platform $(PLATFORMS) --progress=plain $$regular_tags --push ."
	@single_tags=""; \
	if [ -n "$(GHCR_IMAGE)" ]; then single_tags="$$single_tags -t $(GHCR_IMAGE):$(VERSION)-single"; fi; \
	if [ -n "$(DOCKERHUB_IMAGE)" ]; then single_tags="$$single_tags -t $(DOCKERHUB_IMAGE):$(VERSION)-single"; fi; \
	echo "🔨 Building single-container image..."; \
	eval "docker buildx build --pull --platform $(PLATFORMS) --progress=plain -f ops/docker/Dockerfile.single $$single_tags --push ."
	@echo "✅ Pushed version $(VERSION) to the configured registries (latest NOT updated)"
	@if [ -n "$(DOCKERHUB_IMAGE)" ]; then \
		echo "  📦 Docker Hub:"; \
		echo "    - $(DOCKERHUB_IMAGE):$(VERSION)"; \
		echo "    - $(DOCKERHUB_IMAGE):$(VERSION)-single"; \
	fi
	@if [ -n "$(GHCR_IMAGE)" ]; then \
		echo "  📦 GHCR:"; \
		echo "    - $(GHCR_IMAGE):$(VERSION)"; \
		echo "    - $(GHCR_IMAGE):$(VERSION)-single"; \
	fi

# Update v1-latest tags to current version (both regular and single images)
docker-push-latest: docker-buildx-prepare
	@if [ -z "$(GHCR_IMAGE)" ] && [ -z "$(DOCKERHUB_IMAGE)" ]; then \
		echo "ERROR: Set GHCR_IMAGE and/or DOCKERHUB_IMAGE (or DOCKERHUB_IMAGE_REPOSITORY) before promoting latest tags."; \
		exit 1; \
	fi
	@echo "📤 Updating v1-latest tags to version $(VERSION)..."
	@regular_tags=""; \
	if [ -n "$(GHCR_IMAGE)" ]; then regular_tags="$$regular_tags -t $(GHCR_IMAGE):$(VERSION) -t $(GHCR_IMAGE):v1-latest"; fi; \
	if [ -n "$(DOCKERHUB_IMAGE)" ]; then regular_tags="$$regular_tags -t $(DOCKERHUB_IMAGE):$(VERSION) -t $(DOCKERHUB_IMAGE):v1-latest"; fi; \
	echo "🔨 Building regular image with latest tag..."; \
	eval "docker buildx build --pull --platform $(PLATFORMS) --progress=plain $$regular_tags --push ."
	@single_tags=""; \
	if [ -n "$(GHCR_IMAGE)" ]; then single_tags="$$single_tags -t $(GHCR_IMAGE):$(VERSION)-single -t $(GHCR_IMAGE):v1-latest-single"; fi; \
	if [ -n "$(DOCKERHUB_IMAGE)" ]; then single_tags="$$single_tags -t $(DOCKERHUB_IMAGE):$(VERSION)-single -t $(DOCKERHUB_IMAGE):v1-latest-single"; fi; \
	echo "🔨 Building single-container image with latest tag..."; \
	eval "docker buildx build --pull --platform $(PLATFORMS) --progress=plain -f ops/docker/Dockerfile.single $$single_tags --push ."
	@echo "✅ Updated v1-latest to version $(VERSION)"
	@if [ -n "$(DOCKERHUB_IMAGE)" ]; then \
		echo "  📦 Docker Hub:"; \
		echo "    - $(DOCKERHUB_IMAGE):$(VERSION) → v1-latest"; \
		echo "    - $(DOCKERHUB_IMAGE):$(VERSION)-single → v1-latest-single"; \
	fi
	@if [ -n "$(GHCR_IMAGE)" ]; then \
		echo "  📦 GHCR:"; \
		echo "    - $(GHCR_IMAGE):$(VERSION) → v1-latest"; \
		echo "    - $(GHCR_IMAGE):$(VERSION)-single → v1-latest-single"; \
	fi

# Full release: push version AND update latest tags
docker-release: docker-push-latest
	@echo "✅ Full release complete for version $(VERSION)"

tag:
	@version=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	echo "Creating tag v$$version"; \
	git tag "v$$version"; \
	git push origin "v$$version"


dev:
	docker compose -f docker-compose.dev.yml up --build

full:
	docker compose -f docker-compose.full.yml up --build


api:
	$(MANAGED_UV) run --env-file .env python tooling/bin/run_api.py

.PHONY: worker worker-start worker-stop worker-restart

worker: worker-start

worker-start:
	@echo "Starting surreal-commands worker..."
	@bash tooling/scripts/dev/start_worker_local.sh

worker-stop:
	@echo "Stopping surreal-commands worker..."
	@bash tooling/scripts/dev/stop_local.sh worker

worker-restart: worker-stop
	@sleep 2
	@$(MAKE) worker-start

# === Service Management ===
start-all:
	@echo "🚀 Starting Provenote (Database + API + Worker + Frontend)..."
	@bash tooling/scripts/dev/start_surreal_local.sh
	@bash tooling/scripts/dev/start_api_local.sh
	@bash tooling/scripts/dev/start_worker_local.sh
	@bash tooling/scripts/dev/start_frontend_local.sh
	@echo "✅ All services started!"
	@echo "📱 Frontend: http://localhost:3000"
	@echo "🔗 API: http://localhost:5055"
	@echo "📚 API Docs: http://localhost:5055/docs"

stop-all:
	@echo "🛑 Stopping all Provenote services..."
	@bash tooling/scripts/dev/stop_local.sh apps/web worker api surrealdb
	@echo "✅ All services stopped!"

status:
	@echo "📊 Provenote Service Status:"
	@bash tooling/scripts/dev/healthcheck_local.sh

# === Documentation Export ===
export-docs:
	@echo "📚 Exporting documentation..."
	@$(MANAGED_UV) run python tooling/scripts/export_docs.py
	@echo "✅ Documentation export complete!"

# === Cleanup ===
clean-cache:
	@echo "🧹 Cleaning cache directories..."
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".mypy_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".hypothesis" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".benchmarks" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".mutmut-cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -type f -delete 2>/dev/null || true
	@find . -name "*.pyo" -type f -delete 2>/dev/null || true
	@find . -name "*.pyd" -type f -delete 2>/dev/null || true
	@echo "✅ Cache directories cleaned!"

# === Non-Docker Local Runtime ===
dev-local-up:
	@echo "🚀 Starting non-Docker local runtime..."
	@bash tooling/scripts/dev/start_surreal_local.sh
	@bash tooling/scripts/dev/start_api_local.sh
	@bash tooling/scripts/dev/start_worker_local.sh
	@bash tooling/scripts/dev/start_frontend_local.sh
	@bash tooling/scripts/dev/healthcheck_local.sh

dev-local-down:
	@echo "🛑 Stopping non-Docker local runtime..."
	@bash tooling/scripts/dev/stop_local.sh

dev-local-health:
	@bash tooling/scripts/dev/healthcheck_local.sh
