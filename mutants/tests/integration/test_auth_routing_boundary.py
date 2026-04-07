import pytest


def test_auth_and_routing_boundary_with_real_app_wiring(
    api_client, api_client_no_auth
) -> None:
    auth_status_response = api_client_no_auth.get("/api/auth/status")
    assert auth_status_response.status_code == 200
    auth_status_payload = auth_status_response.json()
    assert auth_status_payload["auth_enabled"] is True
    assert auth_status_payload["message"] == "Authentication is required"

    unauthenticated_response = api_client_no_auth.get("/api/route-that-does-not-exist")
    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json() == {"detail": "Missing authorization header"}
    assert unauthenticated_response.headers["WWW-Authenticate"] == "Bearer"

    authenticated_response = api_client.get("/api/route-that-does-not-exist")
    assert authenticated_response.status_code == 404
    assert authenticated_response.json() == {"detail": "Not Found"}
    assert authenticated_response.headers["X-Request-ID"]
    assert authenticated_response.headers["X-Trace-ID"]


@pytest.mark.parametrize("method_name", ["get", "post"])
def test_unauthenticated_unknown_route_fails_closed_before_router_resolution(
    api_client_no_auth, method_name
) -> None:
    response = getattr(api_client_no_auth, method_name)(
        "/api/route-that-does-not-exist"
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing authorization header"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_invalid_authorization_header_is_rejected_before_not_found(
    api_client_no_auth,
) -> None:
    response = api_client_no_auth.get(
        "/api/route-that-does-not-exist",
        headers={"Authorization": "Basic invalid"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authorization header format"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_options_requests_bypass_auth_and_do_not_return_bearer_challenge(
    api_client_no_auth,
) -> None:
    response = api_client_no_auth.options("/api/route-that-does-not-exist")

    assert response.status_code in {200, 404, 405}
    assert response.status_code != 401
    assert "WWW-Authenticate" not in response.headers
