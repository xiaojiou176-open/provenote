from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANUAL_BROWSER_SCRIPT = REPO_ROOT / "apps/web/scripts/run-browser-manual.sh"


def _write_source_profile(home: Path, *, profile_key: str = "Profile 25") -> Path:
    user_data_dir = home / "Library" / "Application Support" / "Google" / "Chrome"
    profile_dir = user_data_dir / profile_key
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "Cookies").write_text("cookie-jar", encoding="utf-8")
    (profile_dir / "Preferences").write_text(
        '{"homepage":"https://example.com"}', encoding="utf-8"
    )
    payload = {
        "profile": {
            "info_cache": {
                profile_key: {
                    "name": "notebooklab",
                    "user_name": "notebooklab@example.test",
                }
            },
            "last_used": profile_key,
            "last_active_profiles": [profile_key],
        }
    }
    (user_data_dir / "Local State").write_text(json.dumps(payload), encoding="utf-8")
    return user_data_dir


def _manual_env(home: Path) -> dict[str, str]:
    return {
        **os.environ,
        "HOME": str(home),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "OPEN_NOTEBOOK_MACHINE_CACHE_ROOT": "",
        "NOTEBOOKLAB_BROWSER_MODE": "",
        "NOTEBOOKLAB_CHROME_USER_DATA_DIR": "",
        "NOTEBOOKLAB_CHROME_PROFILE_NAME": "",
        "NOTEBOOKLAB_CHROME_PROFILE_KEY": "",
        "NOTEBOOKLAB_SOURCE_CHROME_USER_DATA_DIR": "",
        "NOTEBOOKLAB_SOURCE_CHROME_PROFILE_KEY": "",
        "NOTEBOOKLAB_CHROME_CDP_PORT": "",
        "NOTEBOOKLAB_BROWSER_INSTANCE_STATE_FILE": str(
            home / ".runtime-cache" / "browser" / "chrome-instance.json"
        ),
        "NOTEBOOKLAB_MANAGED_PLAYWRIGHT_PROFILE_DIR": "",
    }


def test_manual_browser_script_exists() -> None:
    assert MANUAL_BROWSER_SCRIPT.exists()


def test_manual_browser_script_dry_run_reports_isolated_real_chrome_defaults(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"

    result = subprocess.run(
        [
            "bash",
            str(MANUAL_BROWSER_SCRIPT),
            "--dry-run",
            "--start-url",
            "https://example.com",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=_manual_env(home),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["command"] == "start-or-attach"
    assert payload["browserMode"] == "real_chrome_profile"
    assert payload["profileKey"] == "Profile 1"
    assert payload["userDataDir"].endswith(".cache/notebooklab/browser/chrome-user-data")
    assert payload["cdpPort"] == 9342
    assert payload["cdpUrl"] == "http://127.0.0.1:9342"
    assert payload["targetUrl"] == "https://example.com"
    assert payload["identityPagePath"].endswith(
        ".runtime-cache/browser-identity/index.html"
    )
    assert payload["identityPageUrl"].startswith("file://")
    assert payload["identityLabel"] == "notebooklab"
    assert payload["identityPage"]["repoLabel"] == "notebooklab"
    assert payload["identityPage"]["identityPath"].endswith(
        ".runtime-cache/browser-identity/index.html"
    )
    assert payload["identityPage"]["identityUrl"].startswith("file://")


def test_manual_browser_script_dry_run_reports_managed_playwright_fallback(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"

    result = subprocess.run(
        ["bash", str(MANUAL_BROWSER_SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={
            **_manual_env(home),
            "NOTEBOOKLAB_BROWSER_MODE": "managed_playwright",
        },
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["browserMode"] == "managed_playwright"
    assert payload["channel"] == "chromium"
    assert payload["userDataDir"].endswith(
        ".runtime-cache/browser/manual-playwright-profile"
    )


def test_manual_browser_status_reports_expected_state_file_and_defaults(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"

    result = subprocess.run(
        ["bash", str(MANUAL_BROWSER_SCRIPT), "status"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=_manual_env(home),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["command"] == "status"
    assert payload["stateExists"] is False
    assert payload["expectedUserDataDir"].endswith(
        ".cache/notebooklab/browser/chrome-user-data"
    )
    assert payload["expectedProfileKey"] == "Profile 1"
    assert payload["expectedCdpUrl"] == "http://127.0.0.1:9342"
    assert payload["expectedIdentityPagePath"].endswith(
        ".runtime-cache/browser-identity/index.html"
    )
    assert payload["expectedIdentityPageUrl"].startswith("file://")
    assert payload["expectedIdentityLabel"] == "notebooklab"
    assert payload["statePath"].endswith(".runtime-cache/browser/chrome-instance.json")


def test_manual_browser_script_dry_run_reports_identity_overrides(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"

    result = subprocess.run(
        ["bash", str(MANUAL_BROWSER_SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={
            **_manual_env(home),
            "NOTEBOOKLAB_BROWSER_IDENTITY_LABEL": "notebooklab live",
            "NOTEBOOKLAB_BROWSER_IDENTITY_ACCENT": "#2563eb",
        },
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["identityLabel"] == "notebooklab live"
    assert payload["identityAccent"] == "#2563eb"
    assert payload["identityPagePath"].endswith(
        ".runtime-cache/browser-identity/index.html"
    )
    assert payload["identityPageUrl"].startswith("file://")


def test_manual_browser_migration_dry_run_reports_source_and_target_roots(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    user_data_dir = _write_source_profile(home)

    result = subprocess.run(
        ["bash", str(MANUAL_BROWSER_SCRIPT), "migrate", "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=_manual_env(home),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["command"] == "migrate"
    assert payload["sourceUserDataDir"] == str(user_data_dir)
    assert payload["sourceProfileKey"] == "Profile 25"
    assert payload["targetProfileKey"] == "Profile 1"
    assert payload["targetUserDataDir"].endswith(
        ".cache/notebooklab/browser/chrome-user-data"
    )
    assert payload["removedSingletons"][-1] == "Singleton*"


def test_manual_browser_migration_copies_local_state_and_profile_1_only(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    source_root = _write_source_profile(home)
    (source_root / "SingletonLock").write_text("locked", encoding="utf-8")
    (source_root / "SingletonCookie").write_text("cookie", encoding="utf-8")
    (source_root / "SingletonSocket").write_text("socket", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(MANUAL_BROWSER_SCRIPT), "migrate"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=_manual_env(home),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    target_root = Path(payload["targetUserDataDir"])
    target_profile = target_root / "Profile 1"

    assert sorted(path.name for path in target_root.iterdir()) == [
        "Local State",
        "Profile 1",
    ]
    assert target_profile.is_dir()
    assert (target_profile / "Cookies").exists()
    assert (target_profile / "Preferences").exists()

    rewritten = json.loads((target_root / "Local State").read_text(encoding="utf-8"))
    assert rewritten["profile"]["last_used"] == "Profile 1"
    assert rewritten["profile"]["last_active_profiles"] == ["Profile 1"]
    assert rewritten["profile"]["info_cache"]["Profile 1"]["name"] == "notebooklab"
    assert "Profile 25" not in rewritten["profile"]["info_cache"]

    for singleton_name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        assert (target_root / singleton_name).exists() is False


def test_manual_browser_script_rejects_real_profile_in_ci(tmp_path: Path) -> None:
    home = tmp_path / "home"
    _write_source_profile(home)

    result = subprocess.run(
        ["bash", str(MANUAL_BROWSER_SCRIPT)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={
            **_manual_env(home),
            "CI": "1",
            "NOTEBOOKLAB_BROWSER_MODE": "real_chrome_profile",
        },
    )

    assert result.returncode == 1
    assert "local-only" in result.stderr


def test_manual_browser_script_dry_run_honors_identity_label_and_accent_overrides(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"

    result = subprocess.run(
        ["bash", str(MANUAL_BROWSER_SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={
            **_manual_env(home),
            "NOTEBOOKLAB_BROWSER_IDENTITY_LABEL": "Notebooklab Lane",
            "NOTEBOOKLAB_BROWSER_IDENTITY_ACCENT": "#2563eb",
        },
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["identityPage"]["repoLabel"] == "Notebooklab Lane"
    assert payload["identityPage"]["accent"] == "#2563eb"
