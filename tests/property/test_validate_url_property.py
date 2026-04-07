"""Property-based tests for URL validation SSRF guardrails."""

import ipaddress

import pytest
from hypothesis import given
from hypothesis import strategies as st

from services.api.credentials_service import validate_url

pytestmark = pytest.mark.property


def _ipv4_link_local_strings() -> st.SearchStrategy[str]:
    return st.builds(
        lambda x, y: f"169.254.{x}.{y}",
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
    )


def _ipv4_non_link_local_strings() -> st.SearchStrategy[str]:
    return st.builds(
        lambda x, y, z, w: f"{x}.{y}.{z}.{w}",
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
    ).filter(lambda ip: not ipaddress.ip_address(ip).is_link_local)


@given(ip=_ipv4_link_local_strings(), scheme=st.sampled_from(["http", "https"]))
def test_rejects_all_ipv4_link_local_addresses(ip: str, scheme: str) -> None:
    """Any link-local IPv4 literal must be blocked."""
    with pytest.raises(ValueError, match="Link-local addresses"):
        validate_url(f"{scheme}://{ip}", "openai")


@given(ip=_ipv4_non_link_local_strings(), scheme=st.sampled_from(["http", "https"]))
def test_accepts_non_link_local_ipv4_literals(ip: str, scheme: str) -> None:
    """No non-link-local IPv4 literal should be rejected by SSRF guardrails."""
    assert validate_url(f"{scheme}://{ip}", "openai") is None


@given(
    octet3=st.integers(min_value=0, max_value=255),
    octet4=st.integers(min_value=0, max_value=255),
    scheme=st.sampled_from(["http", "https"]),
)
def test_rejects_ipv4_mapped_ipv6_link_local_literals(
    octet3: int, octet4: int, scheme: str
) -> None:
    """IPv4-mapped IPv6 addresses must not bypass link-local rejection."""
    host = f"[::ffff:169.254.{octet3}.{octet4}]"
    with pytest.raises(ValueError, match="Link-local addresses"):
        validate_url(f"{scheme}://{host}", "openai")
