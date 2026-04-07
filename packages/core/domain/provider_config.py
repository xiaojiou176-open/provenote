"""Legacy provider_config module tombstone.

The old ProviderConfig / ProviderCredential implementation was removed.
Use ``packages.core.domain.credential.Credential`` instead.
"""

from __future__ import annotations

REMOVED_MESSAGE = (
    "packages.core.domain.provider_config is removed and archived. "
    "Use packages.core.domain.credential.Credential."
)


class ProviderConfigRemovedError(RuntimeError):
    """Raised when legacy ProviderConfig APIs are accessed."""


def __getattr__(name: str):
    if name in {"ProviderConfig", "ProviderCredential"}:
        raise ProviderConfigRemovedError(REMOVED_MESSAGE)
    raise AttributeError(name)


__all__: list[str] = []
