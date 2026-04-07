from __future__ import annotations

from pathlib import Path

import pytest

from packages.core.utils.encryption import get_secret_from_env


def test_get_secret_from_env_prefers_file_over_plain_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    secret_path = tmp_path / "secret.txt"
    secret_path.write_text(" file-secret \n", encoding="utf-8")
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD_FILE", str(secret_path))
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", "env-secret")

    assert get_secret_from_env("OPEN_NOTEBOOK_PASSWORD") == "file-secret"


def test_get_secret_from_env_reads_plain_env_when_file_var_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD_FILE", raising=False)
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD", " env-secret ")

    assert get_secret_from_env("OPEN_NOTEBOOK_PASSWORD") == "env-secret"


def test_get_secret_from_env_fails_when_file_path_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    missing_path = tmp_path / "missing-secret.txt"
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD_FILE", str(missing_path))
    monkeypatch.delenv("OPEN_NOTEBOOK_PASSWORD", raising=False)

    with pytest.raises(
        ValueError, match="OPEN_NOTEBOOK_PASSWORD_FILE points to unreadable file"
    ):
        get_secret_from_env("OPEN_NOTEBOOK_PASSWORD")


def test_get_secret_from_env_fails_when_file_content_is_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    empty_secret_path = tmp_path / "empty-secret.txt"
    empty_secret_path.write_text("   \n", encoding="utf-8")
    monkeypatch.setenv("OPEN_NOTEBOOK_PASSWORD_FILE", str(empty_secret_path))

    with pytest.raises(
        ValueError, match="OPEN_NOTEBOOK_PASSWORD_FILE points to empty file"
    ):
        get_secret_from_env("OPEN_NOTEBOOK_PASSWORD")
