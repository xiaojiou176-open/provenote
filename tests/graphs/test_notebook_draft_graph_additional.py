from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from packages.core.graphs import notebook_draft


def test_notebook_draft_helpers_cover_prompt_and_json_paths() -> None:
    paragraphs = notebook_draft.build_notebook_source_paragraphs(
        [SimpleNamespace(id="source:1", title=None, full_text="First paragraph")]
    )
    prompt = notebook_draft._build_llm_prompt_text("Notebook Draft", paragraphs)
    assert "Notebook draft title: Notebook Draft" in prompt
    assert "Untitled Source" in prompt
    assert notebook_draft._extract_json_payload('{"ok": true}') == {"ok": True}
    assert notebook_draft._extract_json_payload('prefix {"ok": true}') == {"ok": True}
    assert notebook_draft._extract_json_payload("broken") is None


@pytest.mark.asyncio
async def test_generate_llm_output_and_serialize_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_chain = SimpleNamespace(
        ainvoke=AsyncMock(
            return_value=SimpleNamespace(
                content='{"sections":[{"title":"Summary","bullets":["A"],"source_pids":["S001-P000001"]}],"claims":[{"text":"Claim","source_pids":["S001-P000001"]}],"unclassified_pids":[]}'
            )
        )
    )
    monkeypatch.setattr(
        notebook_draft,
        "provision_langchain_model",
        AsyncMock(return_value=fake_chain),
    )
    output = await notebook_draft._generate_llm_output(
        model_id="model-x",
        title="Notebook Draft",
        source_paragraphs=notebook_draft.build_notebook_source_paragraphs(
            [SimpleNamespace(id="source:1", title="Alpha", full_text="First paragraph")]
        ),
    )
    assert isinstance(output, notebook_draft.AuditableLLMOutput)
    assert output.sections[0].title == "Summary"

    artifact = notebook_draft.build_auditable_artifact_from_paragraphs(
        notebook_draft.build_notebook_source_paragraphs(
            [SimpleNamespace(id="source:1", title="Alpha", full_text="First paragraph")]
        ),
        title="Notebook Draft",
    )
    serialized = notebook_draft._serialize_artifact(artifact)
    assert serialized["result_markdown"].startswith("# Notebook Draft")


@pytest.mark.asyncio
async def test_generate_llm_output_returns_none_on_invalid_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_chain = SimpleNamespace(
        ainvoke=AsyncMock(return_value=SimpleNamespace(content="no json"))
    )
    monkeypatch.setattr(
        notebook_draft,
        "provision_langchain_model",
        AsyncMock(return_value=fake_chain),
    )
    output = await notebook_draft._generate_llm_output(
        model_id="model-x",
        title="Notebook Draft",
        source_paragraphs=notebook_draft.build_notebook_source_paragraphs(
            [SimpleNamespace(id="source:1", title="Alpha", full_text="First paragraph")]
        ),
    )
    assert output is None
