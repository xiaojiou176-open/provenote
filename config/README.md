# Tool Configuration

Lint, security, and formatting configs consolidated here to reduce root clutter.

| File | Used By |
|------|---------|
| `gitleaks.toml` | gitleaks (pre-commit, CI) |
| `secrets.baseline` | detect-secrets (pre-commit) |
| `typos.toml` | typos (pre-commit) |
| `stylelintrc.json` | stylelint (pre-commit) |
| `worktreeinclude` | worktree/local overrides (optional; ex `.worktreeinclude`) |
| `markdownlint-cli2.yaml` | markdownlint-cli2 (pre-commit) |
| `architecture/layer-boundaries.json` | architecture boundary gate (`check_layer_boundaries.py`) |
| `ci/atomic-commit-exceptions.json` | audited migration exceptions for atomic commit guards (`check_atomic_commit_scope*.sh`) |
| `root/top-level-allowlist.json` | root cleanliness gate (`check_root_cleanliness.py`) |
| `runtime/runtime-surfaces.json` | unified runtime/evidence path gate (`check_runtime_surfaces.py`) |
| `runtime/space-surfaces.json` | disk space governance SSOT (`check_space_surfaces.py`, `audit_space_surfaces.sh`) |
| `upstream/external-surfaces.json` | external surfaces gate (`check_external_surfaces.py`) |

All tool configs are consolidated in `config/` to reduce root clutter.

Paths are set in `.pre-commit-config.yaml` and `.github/workflows/test.yml`.
