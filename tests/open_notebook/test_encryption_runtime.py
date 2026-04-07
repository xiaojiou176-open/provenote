from __future__ import annotations

import base64

import pytest
from cryptography.fernet import Fernet, InvalidToken

from packages.core.utils import encryption


class _AlwaysInvalidFernet:
    def decrypt(self, payload: bytes) -> bytes:
        _ = payload
        raise InvalidToken


class _AlwaysFailingFernet:
    def decrypt(self, payload: bytes) -> bytes:
        _ = payload
        raise RuntimeError("boom")


def _reset_cached_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(encryption, "_ENCRYPTION_KEY", None)


def test_get_secret_from_env_file_var_empty_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPEN_NOTEBOOK_SECRET_FILE", "   ")

    with pytest.raises(ValueError, match="OPEN_NOTEBOOK_SECRET_FILE is set but empty"):
        encryption.get_secret_from_env("OPEN_NOTEBOOK_SECRET")


def test_get_secret_from_env_returns_none_for_blank_plain_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPEN_NOTEBOOK_SECRET_FILE", raising=False)
    monkeypatch.setenv("OPEN_NOTEBOOK_SECRET", "   ")

    assert encryption.get_secret_from_env("OPEN_NOTEBOOK_SECRET") is None


def test_get_or_create_encryption_key_raises_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPEN_NOTEBOOK_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("OPEN_NOTEBOOK_ENCRYPTION_KEY_FILE", raising=False)

    with pytest.raises(ValueError, match="OPEN_NOTEBOOK_ENCRYPTION_KEY is not set"):
        encryption._get_or_create_encryption_key()


def test_get_encryption_key_is_lazy_and_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_cached_key(monkeypatch)
    calls = {"count": 0}

    def _fake_create() -> str:
        calls["count"] += 1
        return "first-key"

    monkeypatch.setattr(encryption, "_get_or_create_encryption_key", _fake_create)

    assert encryption._get_encryption_key() == "first-key"
    assert encryption._get_encryption_key() == "first-key"
    assert calls["count"] == 1


def test_ensure_fernet_key_derives_stable_key() -> None:
    derived_a = encryption._ensure_fernet_key("my-secret")
    derived_b = encryption._ensure_fernet_key("my-secret")
    derived_other = encryption._ensure_fernet_key("other-secret")

    assert derived_a == derived_b
    assert derived_a != derived_other
    assert len(base64.urlsafe_b64decode(derived_a.encode())) == 32


def test_encrypt_and_decrypt_value_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_cached_key(monkeypatch)
    monkeypatch.setenv("OPEN_NOTEBOOK_ENCRYPTION_KEY", "unit-test-key")

    token = encryption.encrypt_value("plain-value")
    assert token != "plain-value"
    assert encryption.looks_like_fernet_token(token) is True

    restored = encryption.decrypt_value(token)
    assert restored == "plain-value"


def test_looks_like_fernet_token_rejects_short_or_invalid_strings() -> None:
    assert encryption.looks_like_fernet_token("short-token") is False
    assert encryption.looks_like_fernet_token("not_base64!!!") is False

    too_small = base64.urlsafe_b64encode(b"x" * 72).decode()
    assert encryption.looks_like_fernet_token(too_small) is False

    malformed_cipher_len = base64.urlsafe_b64encode(b"x" * 74).decode()
    assert encryption.looks_like_fernet_token(malformed_cipher_len) is False


def test_decrypt_value_raises_for_wrong_key_with_encrypted_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = Fernet(Fernet.generate_key()).encrypt(b"secret").decode()
    monkeypatch.setattr(encryption, "get_fernet", lambda: _AlwaysInvalidFernet())

    with pytest.raises(ValueError, match="data appears to be encrypted"):
        encryption.decrypt_value(token)


def test_decrypt_value_treats_non_token_as_legacy_plain_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(encryption, "get_fernet", lambda: _AlwaysInvalidFernet())

    assert encryption.decrypt_value("legacy-plain-text") == "legacy-plain-text"


def test_decrypt_value_wraps_unexpected_decrypt_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(encryption, "get_fernet", lambda: _AlwaysFailingFernet())

    with pytest.raises(ValueError, match="Decryption failed: boom"):
        encryption.decrypt_value("anything")
