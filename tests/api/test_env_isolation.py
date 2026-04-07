import os

from packages.core.settings import LEGACY_PROVIDER_ENV_BLOCKLIST


def test_legacy_provider_env_blocklist_is_cleared_for_tests():
    leaked = [
        env_var for env_var in LEGACY_PROVIDER_ENV_BLOCKLIST if os.getenv(env_var)
    ]
    assert leaked == []
