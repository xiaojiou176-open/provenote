from types import SimpleNamespace

import pytest

from packages.core.graphs import notebook_draft


def test_build_notebook_source_paragraphs_scopes_pids_and_sources() -> None:
    paragraphs = notebook_draft.build_notebook_source_paragraphs(
        [
            SimpleNamespace(id="source:1", title="Alpha", full_text="First\n\nSecond"),
            SimpleNamespace(id="source:2", title="Bravo", full_text="Third"),
        ]
    )

    assert [paragraph.pid for paragraph in paragraphs] == [
        "S001-P000001",
        "S001-P000002",
        "S002-P000001",
    ]
    assert paragraphs[0].source_id == "source:1"
    assert paragraphs[2].source_title == "Bravo"


@pytest.mark.asyncio
async def test_run_notebook_draft_builds_artifact_without_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_generate_llm_output(**_kwargs):
        return None

    monkeypatch.setattr(
        notebook_draft, "_generate_llm_output", _fake_generate_llm_output
    )

    result = await notebook_draft.run_notebook_draft(
        {
            "title": "Notebook Draft",
            "sources": [
                SimpleNamespace(
                    id="source:1", title="Alpha", full_text="First\n\nSecond"
                )
            ],
            "model": "model-draft",
            "language": "en-US",
            "near_dedup_threshold": 0.97,
            "output": {},
        }
    )

    assert result["output"]["result_markdown"].startswith("# Notebook Draft")
    assert result["output"]["source_paragraphs"][0]["source_id"] == "source:1"
    assert result["output"]["metrics"]["coverage_rate"] == 1.0
