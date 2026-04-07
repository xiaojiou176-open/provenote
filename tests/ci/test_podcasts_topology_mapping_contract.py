from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_podcasts_topology_mapping_artifacts_exist() -> None:
    assert (REPO_ROOT / "config/upstream/podcasts-topology-mapping.json").exists()
    assert (
        REPO_ROOT / "tooling/scripts/ci/check_podcasts_topology_mapping.py"
    ).exists()


def test_podcasts_topology_mapping_has_required_entries() -> None:
    payload = json.loads(
        (REPO_ROOT / "config/upstream/podcasts-topology-mapping.json").read_text(
            encoding="utf-8"
        )
    )
    mappings = {entry["upstream_path"]: entry for entry in payload["mappings"]}
    assert mappings["api/main.py"]["current_mapping"] == "services/api/main.py"
    assert (
        mappings["commands/podcast_commands.py"]["current_mapping"]
        == "packages/core/application/commands/podcast_commands.py"
    )
    assert (
        mappings["open_notebook/podcasts/models.py"]["current_mapping"]
        == "packages/core/podcasts/models.py"
    )
    assert mappings["api/routers/languages.py"]["status"] == "missing-equivalent"


def test_podcasts_topology_mapping_gate_passes() -> None:
    result = subprocess.run(
        ["python3", "tooling/scripts/ci/check_podcasts_topology_mapping.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout
