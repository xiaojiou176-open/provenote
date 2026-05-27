# Scripts Documentation

## export_docs.py

Consolidates markdown documentation files for use with ChatGPT or other platforms with file upload limits.

### What It Does

- Scans all subdirectories in the `docs/` folder
- For each subdirectory, combines all `.md` files (excluding `index.md` files)
- Creates one consolidated markdown file per subdirectory
- Saves all exported files to `doc_exports/` in the project root

### Usage

```bash
# Using Makefile (recommended)
make export-docs

# Or run directly with the managed Python entrypoint
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/export_docs.py

# Or run with standard Python
python tooling/scripts/export_docs.py
```

### Output

The script creates `doc_exports/` directory with consolidated files like:

- `getting-started.md` - All getting-started documentation
- `user-guide.md` - All user guide content
- `features.md` - All feature documentation
- `development.md` - All development documentation
- etc.

Each exported file includes:
- A main header with the folder name
- Section headers for each source file
- Source file attribution
- The complete content from each markdown file
- Visual separators between sections

### Example Output Structure

```markdown
# Getting Started

This document consolidates all content from the getting-started documentation folder.

---

## Installation

*Source: installation.md*

[Full content of installation.md]

---

## Quick Start

*Source: quick-start.md*

[Full content of quick-start.md]

---
```

### Notes

- The `doc_exports/` directory is gitignored and safe to regenerate anytime
- Index files (`index.md`) are automatically excluded
- Files are sorted alphabetically for consistent output
- The script handles subdirectories only (ignores files in the root `docs/` folder)

## run_auditable_markdown.py

Compatibility wrapper around the first-party operator CLI auditable lane.

Preferred surface:

```bash
bash tooling/scripts/runtime/run_uv_managed.sh run notebooklab auditable-markdown source:123 \
  --output ./exports/
```

The wrapper still exists so older operator habits and scripts keep working, but the repo-native first-party surface is now `notebooklab`.

### Usage

```bash
# Preferred
bash tooling/scripts/runtime/run_uv_managed.sh run notebooklab auditable-markdown source:123 \
  --output ./exports/

# Backward-compatible wrapper
bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/run_auditable_markdown.py source:123

# With auth + custom output
OPEN_NOTEBOOK_PASSWORD=your_password \
  bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/scripts/run_auditable_markdown.py 123 \
  --api-base http://localhost:5055/api \
  --output ./exports/
```

### Output

Prints:
- `source_id=...`
- `run_id=...`
- `saved_markdown=...`

The markdown filename defaults to `auditable-<run_id>.md`.

See [docs/runbooks/operator-cli.md](../../docs/runbooks/operator-cli.md) for the broader operator CLI surface, including `status`, `inspect`, and `research-thread-to-draft`.

## ci/run_in_consistent_container.sh

Runs repo commands inside the canonical DevContainer-derived CI/local baseline.
Use this for apps/web-related workflow parity and local reproduction.

### Usage

```bash
bash tooling/scripts/ci/run_in_consistent_container.sh -- \
  bash -lc 'cd apps/web && npm run test:coverage'

bash tooling/scripts/ci/run_in_consistent_container.sh -- \
  bash -lc 'cd apps/web && PLAYWRIGHT_PORT=3113 CI=1 npm run test:e2e -- --project=chromium --workers=6 --shard=3/6'
```

## ops/audit_space_surfaces.sh

Read-only disk audit entrypoint for repo-local and repo-related space surfaces.

### Usage

```bash
bash tooling/scripts/ops/audit_space_surfaces.sh
bash tooling/scripts/ops/audit_space_surfaces.sh --format json
bash tooling/scripts/ops/audit_space_surfaces.sh --inventory-class repo_managed_candidate --action-filter safe_clear,cautious_clear
bash tooling/scripts/ops/audit_space_surfaces.sh --cleanup-owner cleanup_runtime_cache.sh --action-filter safe_clear,cautious_clear
```

### What It Does

- reads `config/runtime/space-surfaces.json`
- reports size, existence, ownership confidence, rebuildability confidence, and clearability
- keeps shared layers advisory-only instead of treating them as repo-exclusive cleanup targets
- separates repo cleanup execution inventory from repo-managed candidate inventory

## dev/run_consistent_env_gate.sh

Runs lint/test/live quality gates with a fixed command contract so checks are
executed in a consistent environment (recommended: DevContainer or
`ci/run_in_consistent_container.sh`).

### Usage

```bash
bash tooling/scripts/dev/run_consistent_env_gate.sh lint
bash tooling/scripts/dev/run_consistent_env_gate.sh test
GEMINI_API_KEY=... bash tooling/scripts/dev/run_consistent_env_gate.sh live
GEMINI_API_KEY=... bash tooling/scripts/dev/run_consistent_env_gate.sh all
```
