# Integration Tests README

This directory contains backend integration tests that run against the real FastAPI app wiring.

## Scope

- Validate end-to-end request flow across middleware, routing, exception handling, and response contracts.
- Reuse shared fixtures from `tests/conftest.py` (`api_client`, `api_client_no_auth`) to keep auth/bootstrap behavior consistent with the rest of the backend suite.
- Keep mocking minimal and only for hard external boundaries (for example, network-only dependencies) when unavoidable.

## Boundary vs `tests/api`

- `tests/api`: API-layer tests with focused scope (single router/service contract, targeted mocking allowed).
- `tests/integration`: Cross-layer behavior tests that assert app-level behavior after middleware and router composition.

If a test mainly verifies one route function in isolation, put it in `tests/api`.
If a test verifies behavior created by composing multiple app layers, put it in `tests/integration`.
