from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_promptfoo_surface_is_declared_deterministic_and_lexical() -> None:
    config_text = (
        REPO_ROOT / "evals" / "promptfoo" / "promptfooconfig.yaml"
    ).read_text(encoding="utf-8")

    assert "deterministic lexical evidence gate" in config_text
    assert "does not call a model" in config_text
    assert "provider" in config_text and "echo" in config_text
    assert "not live model judgment" in config_text


def test_ragas_surface_is_declared_as_threshold_gate_not_live_loop() -> None:
    config_text = (REPO_ROOT / "evals" / "ragas" / "config.yaml").read_text(
        encoding="utf-8"
    )

    assert "deterministic threshold gate" in config_text
    assert "does not run a live Ragas pipeline" in config_text
    assert "minimum honest proof surface" in config_text


def test_quality_docs_and_tests_readme_match_eval_surface_positioning() -> None:
    quality_doc = (REPO_ROOT / "docs" / "quality" / "index.md").read_text(
        encoding="utf-8"
    )
    tests_readme = (REPO_ROOT / "tests" / "README.md").read_text(encoding="utf-8")
    quality_doc_lower = quality_doc.lower()
    tests_readme_lower = tests_readme.lower()

    assert "deterministic lexical evidence gate" in quality_doc_lower
    assert "threshold gate" in quality_doc_lower
    assert "must not claim" in quality_doc_lower
    assert "deterministic lexical evidence gate" in tests_readme_lower
    assert "threshold gate" in tests_readme_lower
    assert "not an end-to-end, live-model quality loop" in tests_readme_lower
