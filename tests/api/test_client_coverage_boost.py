from types import SimpleNamespace

import httpx
import pytest

import packages.core.application.client as client_module


def _settings(timeout: object, password: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        internal_api_url="http://services.api.example",
        api_client_timeout=timeout,
        open_notebook_password=password,
    )


def test_sanitize_url_redacts_sensitive_query_values() -> None:
    redacted = client_module._sanitize_url(
        "https://example.test/path?token=abc123&normal=ok&api_key=xyz"
    )

    assert "token=%2A%2A%2A" in redacted
    assert "api_key=%2A%2A%2A" in redacted
    assert "normal=ok" in redacted


def test_sanitize_url_without_query_returns_original() -> None:
    url = "https://example.test/path"
    assert client_module._sanitize_url(url) == url


@pytest.mark.parametrize(
    ("raw_timeout", "expected_timeout"),
    [("15", 30.0), ("4500", 3600.0), ("300", 300.0)],
)
def test_api_client_timeout_clamps_to_valid_range(
    monkeypatch: pytest.MonkeyPatch, raw_timeout: str, expected_timeout: float
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings(raw_timeout))

    c = client_module.APIClient()

    assert c.timeout == expected_timeout


def test_api_client_timeout_invalid_value_uses_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        client_module, "get_settings", lambda: _settings("not-a-number")
    )

    c = client_module.APIClient()

    assert c.timeout == 300.0


def test_api_client_adds_authorization_header_when_password_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        client_module, "get_settings", lambda: _settings("300", password="pw-secret")
    )

    c = client_module.APIClient()

    assert c.headers["Authorization"] == "Bearer pw-secret"


def test_make_request_merges_headers_and_returns_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        client_module, "get_settings", lambda: _settings("300", password="pw-secret")
    )
    c = client_module.APIClient(base_url="https://host.test")

    captured: dict[str, object] = {}

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"ok": "yes"}

    class _FakeClient:
        def __init__(self, timeout: float):
            self.timeout = timeout

        def __enter__(self) -> "_FakeClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def request(self, method: str, url: str, **kwargs):
            captured["method"] = method
            captured["url"] = url
            captured["kwargs"] = kwargs
            return _Response()

    monkeypatch.setattr(client_module.httpx, "Client", _FakeClient)

    result = c._make_request(
        "GET", "/x", headers={"X-Req": "1"}, params={"q": "k"}, timeout=12.0
    )

    assert result == {"ok": "yes"}
    assert captured["method"] == "GET"
    assert captured["url"] == "https://host.test/x"
    headers = captured["kwargs"]["headers"]
    assert headers["X-Req"] == "1"
    assert headers["Authorization"] == "Bearer pw-secret"


def test_make_binary_request_returns_filename_and_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient(base_url="https://host.test")

    class _Response:
        headers = {"Content-Disposition": 'attachment; filename="bundle.zip"'}
        content = b"zip-bytes"

        def raise_for_status(self) -> None:
            return None

    class _FakeClient:
        def __init__(self, timeout: float):
            self.timeout = timeout

        def __enter__(self) -> "_FakeClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def request(self, method: str, url: str, **kwargs):
            return _Response()

    monkeypatch.setattr(client_module.httpx, "Client", _FakeClient)

    filename, payload = c._make_binary_request("GET", "/bundle")

    assert filename == "bundle.zip"
    assert payload == b"zip-bytes"


def test_make_request_wraps_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient(base_url="https://host.test")

    class _FakeClient:
        def __init__(self, timeout: float):
            self.timeout = timeout

        def __enter__(self) -> "_FakeClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def request(self, method: str, url: str, **kwargs):
            raise httpx.RequestError("network down")

    monkeypatch.setattr(client_module.httpx, "Client", _FakeClient)

    with pytest.raises(ConnectionError) as exc_info:
        c._make_request("GET", "/x?token=abc")

    msg = str(exc_info.value)
    assert "Failed to connect to API: GET https://host.test/x?token=%2A%2A%2A" in msg
    assert "RequestError" in msg


def test_make_request_wraps_http_status_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient(base_url="https://host.test")

    req = httpx.Request("GET", "https://host.test/x")
    resp = httpx.Response(503, request=req)
    status_err = httpx.HTTPStatusError("boom", request=req, response=resp)

    class _FakeClient:
        def __init__(self, timeout: float):
            self.timeout = timeout

        def __enter__(self) -> "_FakeClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def request(self, method: str, url: str, **kwargs):
            raise status_err

    monkeypatch.setattr(client_module.httpx, "Client", _FakeClient)

    with pytest.raises(RuntimeError) as exc_info:
        c._make_request("GET", "/x")

    assert str(exc_info.value) == "API request failed: 503 - Service Unavailable"


def test_make_request_reraises_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient(base_url="https://host.test")

    class _FakeClient:
        def __init__(self, timeout: float):
            self.timeout = timeout

        def __enter__(self) -> "_FakeClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def request(self, method: str, url: str, **kwargs):
            raise ValueError("unexpected")

    monkeypatch.setattr(client_module.httpx, "Client", _FakeClient)

    with pytest.raises(ValueError, match="unexpected"):
        c._make_request("GET", "/x")


def test_create_source_requires_notebook_identifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient()

    with pytest.raises(
        ValueError, match="Either notebook_id or notebooks must be provided"
    ):
        c.create_source(source_type="text", content="hello")


def test_get_notebooks_wraps_single_dict_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient()
    monkeypatch.setattr(c, "_make_request", lambda *args, **kwargs: {"id": "nb:1"})

    result = c.get_notebooks(archived=True)

    assert result == [{"id": "nb:1"}]


def test_get_notebook_context_returns_empty_dict_when_backend_returns_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient()
    monkeypatch.setattr(c, "_make_request", lambda *args, **kwargs: [{"id": "x"}])

    result = c.get_notebook_context("notebook:1")

    assert result == {}


def test_rebuild_embeddings_timeout_uses_double_when_needed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient()
    capture: dict[str, object] = {}

    def _fake_request(method: str, endpoint: str, **kwargs):
        capture["method"] = method
        capture["endpoint"] = endpoint
        capture["timeout"] = kwargs["timeout"]
        return {"ok": True}

    monkeypatch.setattr(c, "_make_request", _fake_request)

    c.rebuild_embeddings(mode="all")

    assert capture["method"] == "POST"
    assert capture["endpoint"] == "/api/embeddings/rebuild"
    assert capture["timeout"] == 600.0


def test_api_client_wrapper_methods_forward_correct_endpoints_and_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient()
    calls: list[tuple[str, str, dict[str, object]]] = []

    def _fake_request(method: str, endpoint: str, **kwargs):
        calls.append((method, endpoint, kwargs))
        if endpoint in {
            "/api/notebooks",
            "/api/models",
            "/api/transformations",
            "/api/notes",
            "/api/sources",
            "/api/episode-profiles",
        }:
            return {"id": "wrapped"}
        return {"ok": True}

    monkeypatch.setattr(c, "_make_request", _fake_request)

    c.create_notebook("n", "d")
    c.get_notebook("nb:1")
    c.update_notebook("nb:1", name="u")
    c.delete_notebook("nb:1")
    c.search("q")
    c.ask_simple("q", "s", "a", "f")
    c.get_models(model_type="embedding")
    c.create_model("m", "google", "language")
    c.delete_model("model:1")
    c.get_default_models()
    c.update_default_models(strategy_model="model:1")
    c.get_provider_policy()
    c.update_provider_policy(provider_chain=["google"])
    c.get_provider_bootstrap_diagnostics()
    c.get_transformations()
    c.create_transformation("t", "T", "D", "P")
    c.get_transformation("tr:1")
    c.update_transformation("tr:1", title="new")
    c.delete_transformation("tr:1")
    c.execute_transformation("tr:1", "in", "model:1")
    c.get_notes(notebook_id="nb:1")
    c.create_note("body", title="title", note_type="human", notebook_id="nb:1")
    c.get_note("note:1")
    c.update_note("note:1", content="x")
    c.delete_note("note:1")
    c.embed_content("source:1", "source", async_processing=True)
    c.get_rebuild_status("command:1")
    c.get_settings()
    c.update_settings(theme="dark")
    c.get_sources(notebook_id="nb:1")
    c.get_source("source:1")
    c.get_source_status("source:1")
    c.update_source("source:1", title="new")
    c.delete_source("source:1")
    c.get_source_insights("source:1")
    c.get_insight("insight:1")
    c.delete_insight("insight:1")
    c.save_insight_as_note("insight:1", notebook_id="nb:1")
    c.create_source_insight("source:1", "transformation:1", model_id="model:1")
    c.get_episode_profiles()
    c.get_episode_profile("daily")
    c.create_episode_profile(name="daily")
    c.update_episode_profile("profile:1", description="d")
    c.delete_episode_profile("profile:1")

    def _find(method: str, endpoint: str) -> dict[str, object]:
        for m, e, kwargs in calls:
            if m == method and e == endpoint:
                return kwargs
        raise AssertionError(f"Missing call {method} {endpoint}")

    assert _find("POST", "/api/search")["json"]["query"] == "q"
    assert _find("POST", "/api/search/ask/simple")["timeout"] == c.timeout
    assert _find("POST", "/api/transformations/execute")["timeout"] == c.timeout
    assert _find("POST", "/api/embed")["timeout"] == c.timeout
    assert _find("GET", "/api/models")["params"] == {"type": "embedding"}


def test_create_source_payload_prefers_notebooks_and_includes_optional_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient()
    capture: dict[str, object] = {}

    def _fake_request(method: str, endpoint: str, **kwargs):
        capture["method"] = method
        capture["endpoint"] = endpoint
        capture["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(c, "_make_request", _fake_request)

    c.create_source(
        notebook_id="nb:legacy",
        notebooks=["nb:1", "nb:2"],
        source_type="web",
        url="https://example.test",
        file_path="/tmp/a.txt",
        content="body",
        title="Title",
        transformations=["tr:1"],
        embed=True,
        delete_source=True,
        async_processing=True,
    )

    payload = capture["kwargs"]["json"]
    assert payload["notebooks"] == ["nb:1", "nb:2"]
    assert "notebook_id" not in payload
    assert payload["url"] == "https://example.test"
    assert payload["file_path"] == "/tmp/a.txt"
    assert payload["content"] == "body"
    assert payload["title"] == "Title"
    assert payload["transformations"] == ["tr:1"]


def test_create_source_uses_notebook_id_when_notebooks_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient()
    capture: dict[str, object] = {}

    def _fake_request(method: str, endpoint: str, **kwargs):
        capture["payload"] = kwargs["json"]
        return {"ok": True}

    monkeypatch.setattr(c, "_make_request", _fake_request)

    c.create_source(notebook_id="nb:1", source_type="text", content="x")

    assert capture["payload"]["notebook_id"] == "nb:1"


def test_outcome_api_client_methods_cover_bundle_thread_and_auditable_endpoints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "get_settings", lambda: _settings("300"))
    c = client_module.APIClient()
    request_calls: list[tuple[str, str, dict[str, object]]] = []
    text_calls: list[tuple[str, str, dict[str, object]]] = []
    binary_calls: list[tuple[str, str, dict[str, object]]] = []

    def _fake_request(method: str, endpoint: str, **kwargs):
        request_calls.append((method, endpoint, kwargs))
        return {"ok": True}

    def _fake_text_request(method: str, endpoint: str, **kwargs):
        text_calls.append((method, endpoint, kwargs))
        return "# outcome"

    def _fake_binary_request(method: str, endpoint: str, **kwargs):
        binary_calls.append((method, endpoint, kwargs))
        return ("draft-bundle.zip", b"zip-bytes")

    monkeypatch.setattr(c, "_make_request", _fake_request)
    monkeypatch.setattr(c, "_make_text_request", _fake_text_request)
    monkeypatch.setattr(c, "_make_binary_request", _fake_binary_request)

    c.get_drafts("notebook:1")
    c.create_draft(
        "notebook:1",
        ["source:1"],
        note_ids=["note:1"],
        thread_ids=["research_thread:1"],
        title="Draft",
        model_id="model:1",
        language="en-US",
        near_dedup_threshold=0.91,
    )
    c.verify_draft("draft:1")
    c.get_draft_markdown("draft:1")
    c.get_draft_bundle("draft:1")
    c.get_research_threads("notebook:1")
    c.create_research_thread(
        "notebook:1",
        "Thread",
        "search",
        source_ids=["source:1"],
        note_ids=["note:1"],
        question="What changed?",
        answer="Answer",
        search_results=[{"title": "hit"}],
    )
    c.append_research_thread(
        "research_thread:1",
        "answer_snapshot",
        "Saved answer",
        title="Update",
        source_ids=["source:2"],
        note_ids=["note:2"],
        metadata={"kind": "follow-up"},
    )
    c.create_draft_from_thread("research_thread:1")
    c.get_auditable_runs("source:1")
    c.create_auditable_run(
        "source:1",
        model_id="model:2",
        language="en-US",
        near_dedup_threshold=0.92,
    )
    c.get_auditable_run_markdown("auditable_run:1")
    c.repair_auditable_claim("auditable_run:1", 3, model_id="model:3")
    c.repair_auditable_section("auditable_run:1", 4)

    assert request_calls == [
        ("GET", "/api/notebooks/notebook:1/drafts", {}),
        (
            "POST",
            "/api/notebooks/notebook:1/drafts",
            {
                "json": {
                    "source_ids": ["source:1"],
                    "note_ids": ["note:1"],
                    "thread_ids": ["research_thread:1"],
                    "title": "Draft",
                    "model_id": "model:1",
                    "language": "en-US",
                    "near_dedup_threshold": 0.91,
                }
            },
        ),
        ("POST", "/api/drafts/draft:1/verify", {}),
        ("GET", "/api/notebooks/notebook:1/research-threads", {}),
        (
            "POST",
            "/api/notebooks/notebook:1/research-threads",
            {
                "json": {
                    "title": "Thread",
                    "seed_kind": "search",
                    "source_ids": ["source:1"],
                    "note_ids": ["note:1"],
                    "search_results": [{"title": "hit"}],
                    "question": "What changed?",
                    "answer": "Answer",
                }
            },
        ),
        (
            "POST",
            "/api/research-threads/research_thread:1/entries",
            {
                "json": {
                    "entry_type": "answer_snapshot",
                    "content": "Saved answer",
                    "source_ids": ["source:2"],
                    "note_ids": ["note:2"],
                    "metadata": {"kind": "follow-up"},
                    "title": "Update",
                }
            },
        ),
        ("POST", "/api/research-threads/research_thread:1/drafts", {}),
        ("GET", "/api/sources/source:1/auditable-runs", {}),
        (
            "POST",
            "/api/sources/source:1/auditable-runs",
            {
                "json": {
                    "model_id": "model:2",
                    "language": "en-US",
                    "near_dedup_threshold": 0.92,
                }
            },
        ),
        (
            "POST",
            "/api/auditable-runs/auditable_run:1/repair-claim",
            {"json": {"target_index": 3, "model_id": "model:3"}},
        ),
        (
            "POST",
            "/api/auditable-runs/auditable_run:1/repair-section",
            {"json": {"target_index": 4}},
        ),
    ]
    assert text_calls == [
        ("GET", "/api/drafts/draft:1/markdown", {}),
        ("GET", "/api/auditable-runs/auditable_run:1/markdown", {}),
    ]
    assert binary_calls == [("GET", "/api/drafts/draft:1/bundle", {})]
