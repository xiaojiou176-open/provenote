"""OpenAPI schema contract tests.

Ensures that the tracked contract and runtime implementation stay aligned.
"""

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from services.api.main import app
from tooling.scripts.api.export_openapi_contract import _normalize

REPO_ROOT = Path(__file__).resolve().parents[3]
TRACKED_OPENAPI_CONTRACT = REPO_ROOT / "contracts" / "api" / "openapi.yaml"

_CANONICAL_SUCCESS_CODES = {"200", "201", "202", "204"}
_ALLOWED_NO_ERROR_RESPONSE_ROUTES = {
    "GET /api/auth/status",
    "GET /api/config",
    "GET /api/models/defaults",
    "GET /api/models/providers",
    "POST /api/models/sync",
    "POST /api/models/auto-assign",
    "GET /api/transformations",
    "GET /api/transformations/default-prompt",
    "GET /api/settings",
    "GET /api/providers/policy",
    "GET /api/providers/policy/bootstrap-diagnostics",
    "GET /api/commands/registry/debug",
    "GET /api/podcasts/episodes",
    "GET /api/episode-profiles",
    "GET /api/speaker-profiles",
    "GET /api/credentials/status",
    "GET /",
    "GET /health",
}
_ALLOWED_NO_REQUEST_BODY_ROUTES = {
    "POST /api/notebooks/{notebook_id}/sources/{source_id}",
    "POST /api/drafts/{draft_id}/verify",
    "POST /api/models/{model_id}/test",
    "POST /api/models/sync/{provider}",
    "POST /api/models/sync",
    "POST /api/models/auto-assign",
    "POST /api/research-threads/{thread_id}/drafts",
    "POST /api/sources/{source_id}/reprocess",
    "POST /api/sources/{source_id}/retry",
    "POST /api/commands/dead-letter/{entry_id}/requeue",
    "POST /api/podcasts/episodes/{episode_id}/retry",
    "POST /api/episode-profiles/{profile_id}/duplicate",
    "POST /api/speaker-profiles/{profile_id}/duplicate",
    "POST /api/credentials/{credential_id}/test",
    "POST /api/credentials/{credential_id}/discover",
}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    """Test client fixture."""
    monkeypatch.setenv("OPEN_NOTEBOOK_SKIP_MIGRATIONS", "true")
    monkeypatch.setenv("OPEN_NOTEBOOK_SKIP_GEMINI_STARTUP_PROBE", "true")
    for env_var in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GROQ_API_KEY",
        "MISTRAL_API_KEY",
        "DEEPSEEK_API_KEY",
        "XAI_API_KEY",
        "OPENROUTER_API_KEY",
        "VOYAGE_API_KEY",
        "ELEVENLABS_API_KEY",
        "OLLAMA_API_BASE",
        "OLLAMA_BASE_URL",
        "VERTEX_PROJECT",
        "VERTEX_LOCATION",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_VERSION",
        "OPENAI_COMPATIBLE_BASE_URL",
        "OPENAI_COMPATIBLE_API_KEY",
        "API_BASE_URL",
    ):
        monkeypatch.delenv(env_var, raising=False)
    with TestClient(app) as client_instance:
        yield client_instance


@pytest.fixture
def openapi_schema(client):
    """Fetch OpenAPI schema."""
    response = client.get("/openapi.json")
    assert response.status_code == 200, "OpenAPI endpoint should be accessible"
    return response.json()


@pytest.fixture
def tracked_openapi_schema():
    """Load tracked OpenAPI contract."""
    assert TRACKED_OPENAPI_CONTRACT.is_file(), (
        f"Tracked OpenAPI contract missing: {TRACKED_OPENAPI_CONTRACT}"
    )
    return yaml.safe_load(TRACKED_OPENAPI_CONTRACT.read_text(encoding="utf-8"))


def test_tracked_openapi_contract_matches_runtime_export(
    openapi_schema, tracked_openapi_schema
):
    """Tracked OpenAPI contract must match the normalized runtime schema export."""
    runtime_schema = _normalize(openapi_schema)
    assert tracked_openapi_schema == runtime_schema


def test_frontend_generated_contract_metadata_exists() -> None:
    generated = REPO_ROOT / "apps/web/src/lib/api/generated/openapi-contract.ts"
    assert generated.exists()
    assert "openApiContractSha256" in generated.read_text(encoding="utf-8")


def test_openapi_schema_structure(openapi_schema):
    """Verify OpenAPI schema has required fields."""
    assert "openapi" in openapi_schema, "OpenAPI version should be present"
    assert "info" in openapi_schema, "API info should be present"
    assert "paths" in openapi_schema, "API paths should be present"
    assert "components" in openapi_schema, "Components should be present"


def test_openapi_info_completeness(openapi_schema):
    """Verify API info is complete."""
    info = openapi_schema.get("info", {})
    assert "title" in info, "API title should be present"
    assert "version" in info, "API version should be present"
    assert "description" in info, "API description should be present"


def test_all_routes_have_summaries(openapi_schema):
    """Ensure all routes have descriptive summaries."""
    paths = openapi_schema.get("paths", {})
    missing_summaries = []

    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                if "summary" not in details and "description" not in details:
                    missing_summaries.append(f"{method.upper()} {path}")

    assert len(missing_summaries) == 0, (
        f"Routes without summary/description: {missing_summaries}"
    )


def test_all_routes_have_response_models(openapi_schema):
    """Ensure all routes define at least one canonical success response schema."""
    paths = openapi_schema.get("paths", {})
    missing_responses = []

    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                responses = details.get("responses", {})
                has_canonical_success = any(
                    str(code) in _CANONICAL_SUCCESS_CODES for code in responses.keys()
                )
                if not has_canonical_success:
                    missing_responses.append(f"{method.upper()} {path}")

    assert len(missing_responses) == 0, (
        f"Routes without canonical success response "
        f"({_CANONICAL_SUCCESS_CODES}): {missing_responses}"
    )


def test_error_responses_defined(openapi_schema):
    """Ensure error response schemas are defined."""
    paths = openapi_schema.get("paths", {})
    routes_without_error_handling = []

    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                responses = details.get("responses", {})
                has_error_response = any(
                    status_code.startswith(("4", "5"))
                    for status_code in responses.keys()
                )
                if not has_error_response:
                    routes_without_error_handling.append(f"{method.upper()} {path}")

    unexpected_routes = sorted(
        set(routes_without_error_handling) - _ALLOWED_NO_ERROR_RESPONSE_ROUTES
    )
    assert not unexpected_routes, (
        f"Routes missing 4xx/5xx responses outside allowlist: {unexpected_routes}"
    )


def test_request_body_schemas_defined(openapi_schema):
    """Ensure POST/PUT/PATCH routes have request body schemas."""
    paths = openapi_schema.get("paths", {})
    missing_request_schemas = []

    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["post", "put", "patch"]:
                if "requestBody" not in details:
                    # Some routes might not need a body (e.g., POST /logout)
                    # This is a soft check
                    missing_request_schemas.append(f"{method.upper()} {path}")

    unexpected_routes = sorted(
        set(missing_request_schemas) - _ALLOWED_NO_REQUEST_BODY_ROUTES
    )
    assert not unexpected_routes, (
        "POST/PUT/PATCH routes missing requestBody outside allowlist: "
        f"{unexpected_routes}"
    )


def test_security_schemes_defined(openapi_schema):
    """Verify security scheme definitions match actual security requirements."""
    valid_scheme_types = {"apiKey", "http", "oauth2", "openIdConnect", "mutualTLS"}
    components = openapi_schema.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    paths = openapi_schema.get("paths", {})

    required_scheme_names = set()

    global_security = openapi_schema.get("security", [])
    if isinstance(global_security, list):
        for security_requirement in global_security:
            if isinstance(security_requirement, dict):
                required_scheme_names.update(security_requirement.keys())

    for path, methods in paths.items():
        for method, details in methods.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            operation_security = details.get("security", None)
            if not isinstance(operation_security, list):
                continue
            for security_requirement in operation_security:
                if isinstance(security_requirement, dict):
                    required_scheme_names.update(security_requirement.keys())

    assert isinstance(security_schemes, dict), "Security schemes should be a dict"

    violations = []
    if required_scheme_names and not security_schemes:
        violations.append(
            "Security requirements are declared but components.securitySchemes is empty"
        )
    missing_scheme_defs = (
        sorted(required_scheme_names - set(security_schemes.keys()))
        if required_scheme_names
        else []
    )
    if missing_scheme_defs:
        violations.append(
            "Security schemes referenced by operations but not defined: "
            f"{missing_scheme_defs}"
        )

    for scheme_name, scheme_details in security_schemes.items():
        assert isinstance(scheme_details, dict), (
            f"Security scheme {scheme_name} should be an object"
        )
        scheme_type = scheme_details.get("type")
        assert scheme_type in valid_scheme_types, (
            f"Security scheme {scheme_name} has invalid type: {scheme_type}"
        )

        if scheme_type == "apiKey":
            if "name" not in scheme_details or "in" not in scheme_details:
                violations.append(
                    f"apiKey security scheme {scheme_name} should define name and in"
                )
        elif scheme_type == "http":
            if "scheme" not in scheme_details:
                violations.append(
                    f"http security scheme {scheme_name} should define scheme"
                )
        elif scheme_type == "oauth2":
            if "flows" not in scheme_details:
                violations.append(
                    f"oauth2 security scheme {scheme_name} should define flows"
                )
        elif scheme_type == "openIdConnect":
            if "openIdConnectUrl" not in scheme_details:
                violations.append(
                    f"openIdConnect scheme {scheme_name} should define openIdConnectUrl"
                )

    assert not violations, violations


def test_schemas_have_descriptions(openapi_schema):
    """Ensure data models have descriptions."""
    components = openapi_schema.get("components", {})
    schemas = components.get("schemas", {})

    schemas_without_descriptions = []
    for schema_name, schema_details in schemas.items():
        if "description" not in schema_details and "title" not in schema_details:
            schemas_without_descriptions.append(schema_name)

    # Verify we have schemas defined
    assert isinstance(schemas, dict), "Schemas should be a dict"
    assert len(schemas) > 0, "API should have at least one schema defined"
    assert not schemas_without_descriptions, (
        f"Schemas missing both description and title: {schemas_without_descriptions}"
    )


def test_no_hardcoded_server_urls(openapi_schema):
    """Ensure no hardcoded server URLs (should be relative)."""
    servers = openapi_schema.get("servers", [])

    hardcoded_urls = []
    for server in servers:
        url = server.get("url", "")
        # Relative URLs or localhost are OK for dev
        # Prod should not have hardcoded IPs
        if url.startswith("http") and "localhost" not in url and "127.0.0.1" not in url:
            hardcoded_urls.append(url)

    assert isinstance(servers, list), "Servers should be a list"
    assert not hardcoded_urls, (
        f"Found hardcoded non-local server URLs: {hardcoded_urls}"
    )


def test_deprecated_endpoints_marked(openapi_schema):
    """Check deprecation metadata is explicit and internally consistent."""
    paths = openapi_schema.get("paths", {})
    deprecated_endpoints = []
    deprecation_hint_endpoints = []

    for path, methods in paths.items():
        for method, details in methods.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            deprecated_flag = details.get("deprecated", False)
            assert isinstance(deprecated_flag, bool), (
                f"deprecated flag must be bool for {method.upper()} {path}"
            )

            summary = str(details.get("summary", "")).lower()
            description = str(details.get("description", "")).lower()
            if (
                "deprecated" in path.lower()
                or "deprecated" in summary
                or "deprecated" in description
            ):
                deprecation_hint_endpoints.append(
                    (method.upper(), path, deprecated_flag)
                )

            if deprecated_flag:
                deprecated_endpoints.append(f"{method.upper()} {path}")

    assert isinstance(paths, dict), "Paths should be a dict"
    assert len(paths) > 0, "API should have at least one path defined"
    hinted_but_not_marked = sorted(
        f"{method} {path}"
        for method, path, deprecated_flag in deprecation_hint_endpoints
        if not deprecated_flag
    )
    assert not hinted_but_not_marked, (
        "Endpoints with deprecation hints must set deprecated=true: "
        f"{hinted_but_not_marked}"
    )

    invalid_deprecated = [
        e
        for e in deprecated_endpoints
        if not e.startswith(("GET ", "POST ", "PUT ", "DELETE ", "PATCH "))
    ]
    assert not invalid_deprecated, (
        "Deprecated endpoint list should contain normalized HTTP method and path: "
        f"{invalid_deprecated}"
    )
