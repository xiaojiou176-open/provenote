from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_19 = REPO_ROOT / "packages/core/database/migrations/19.surrealql"
MIGRATION_20 = REPO_ROOT / "packages/core/database/migrations/20.surrealql"
OUTCOME_MODELS = REPO_ROOT / "packages/core/application/outcome_models.py"


def test_draft_thread_ids_migration_targets_research_threads() -> None:
    migration_text = MIGRATION_19.read_text(encoding="utf-8")

    assert "array<record<research_thread>>" in migration_text
    assert "array<record<chat_session>>" not in migration_text


def test_outcome_models_describe_thread_ids_as_research_threads() -> None:
    models_text = OUTCOME_MODELS.read_text(encoding="utf-8")

    assert (
        'description="Optional research thread IDs reserved for future draft enrichment"'
        in models_text
    )


def test_outcome_spine_migrations_use_surreal_flexible_syntax_order() -> None:
    migration_19_text = MIGRATION_19.read_text(encoding="utf-8")
    migration_20_text = MIGRATION_20.read_text(encoding="utf-8")

    for migration_text in (migration_19_text, migration_20_text):
        assert "TYPE FLEXIBLE " not in migration_text

    assert "TYPE object FLEXIBLE" in migration_19_text
    assert "TYPE array<record<research_thread>> DEFAULT []" in migration_19_text
    assert "TYPE array<record<source>> DEFAULT []" in migration_20_text
