from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


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
    current_mappings = {
        entry["current_mapping"]: entry
        for entry in payload["mappings"]
        if entry["current_mapping"] is not None
    }
    assert "services/api/main.py" in current_mappings
    assert "packages/core/application/commands/podcast_commands.py" in current_mappings
    assert "packages/core/podcasts/models.py" in current_mappings

    missing_equivalents = [
        entry for entry in payload["mappings"] if entry["status"] == "missing-equivalent"
    ]
    assert missing_equivalents, "topology mapping should retain missing-equivalent entries"
    assert any(
        entry["current_mapping"] is None for entry in missing_equivalents
    ), "missing-equivalent entries must leave current_mapping unset"


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
