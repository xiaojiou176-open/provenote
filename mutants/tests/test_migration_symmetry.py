from pathlib import Path

import pytest

from packages.core.database.async_migrate import AsyncMigration, AsyncMigrationManager

MIGRATIONS_DIR = Path("packages/core/database/migrations")


def _sql_text(filename: str) -> str:
    return (MIGRATIONS_DIR / filename).read_text(encoding="utf-8")


def test_every_non_latest_migration_has_matching_down_script():
    up_versions = {
        int(path.stem)
        for path in MIGRATIONS_DIR.glob("*.surrealql")
        if "_down" not in path.stem
    }
    down_versions = {
        int(path.stem.replace("_down", ""))
        for path in MIGRATIONS_DIR.glob("*_down.surrealql")
    }

    latest_version = max(up_versions)
    expected_down_versions = up_versions - {latest_version}

    assert expected_down_versions == down_versions


def test_migration_10_down_restores_pre_v10_embedding_schema_and_records_cleanup_note():
    down_sql = _sql_text("10_down.surrealql")

    assert (
        "REMOVE INDEX IF EXISTS idx_source_insight_source ON TABLE source_insight;"
        in down_sql
    )
    assert (
        "REMOVE INDEX IF EXISTS idx_source_embedding_source ON TABLE source_embedding;"
        in down_sql
    )
    assert (
        "DEFINE FIELD OVERWRITE embedding ON TABLE source_insight TYPE array<float>;"
        in down_sql
    )
    assert (
        "DEFINE FIELD OVERWRITE embedding ON TABLE note TYPE array<float>;" in down_sql
    )
    assert "UPSERT open_notebook:migration_rollback_v10 CONTENT {" in down_sql
    assert "irreversible_cleanup: true" in down_sql


def test_migration_13_down_matches_pre_v13_nullable_embedding_semantics():
    up_sql = _sql_text("13.surrealql")
    down_sql = _sql_text("13_down.surrealql")

    assert (
        "DEFINE FIELD OVERWRITE embedding ON TABLE source_insight TYPE option<array<float>>;"
        in up_sql
    )
    assert (
        "DEFINE FIELD OVERWRITE embedding ON TABLE note TYPE option<array<float>>;"
        in up_sql
    )
    assert (
        "DEFINE FIELD OVERWRITE embedding ON TABLE source_insight TYPE option<array<float>>;"
        in down_sql
    )
    assert (
        "DEFINE FIELD OVERWRITE embedding ON TABLE note TYPE option<array<float>>;"
        in down_sql
    )
    assert "TYPE array<float>;" not in down_sql


def test_migration_16_down_restores_singleton_state_and_records_rollback_strategy():
    down_sql = _sql_text("16_down.surrealql")

    assert "DELETE open_notebook:provider_policy;" in down_sql
    assert "UPSERT open_notebook:default_prompts CONTENT {" in down_sql
    assert "DELETE transformation:gemini_extract;" in down_sql
    assert "DELETE transformation:gemini_rewrite;" in down_sql
    assert "DELETE transformation:gemini_audit;" in down_sql
    assert "UPSERT open_notebook:migration_rollback_v16 CONTENT {" in down_sql
    assert "irreversible_without_external_backup: true" in down_sql


def test_all_migrations_place_flexible_after_type_keyword():
    offenders = []
    for path in MIGRATIONS_DIR.glob("*.surrealql"):
        sql = path.read_text(encoding="utf-8")
        if "FLEXIBLE TYPE" in sql:
            offenders.append(path.name)
    assert offenders == []


def test_all_migrations_use_fields_not_columns_in_define_index_statements():
    offenders = []
    for path in MIGRATIONS_DIR.glob("*.surrealql"):
        sql = path.read_text(encoding="utf-8")
        if "DEFINE INDEX" in sql and " COLUMNS " in sql:
            offenders.append(path.name)
    assert offenders == []


def test_search_analyzer_clause_precedes_field_list_in_migrations():
    offenders = []
    for path in MIGRATIONS_DIR.glob("*.surrealql"):
        sql = path.read_text(encoding="utf-8")
        if (
            "FIELDS title SEARCH ANALYZER" in sql
            or "FIELDS content SEARCH ANALYZER" in sql
            or "FIELDS full_text SEARCH ANALYZER" in sql
        ):
            offenders.append(path.name)
    assert offenders == []


def test_async_migration_from_file_splits_top_level_statements_safely():
    migration = AsyncMigration.from_file(
        "packages/core/database/migrations/1.surrealql"
    )

    assert len(migration.statements) > 10
    function_statement = next(
        statement
        for statement in migration.statements
        if statement.startswith("DEFINE FUNCTION IF NOT EXISTS fn::text_search")
    )
    assert function_statement.count(";") > 3
    index_statement = next(
        statement
        for statement in migration.statements
        if "idx_source_title" in statement
    )
    assert "idx_source_full_text" not in index_statement


def test_async_migration_manager_registers_migration_18_up_and_down():
    manager = AsyncMigrationManager()
    assert len(manager.up_migrations) >= 18
    assert len(manager.down_migrations) == 17
    assert "idx_model_provider_type_name" in manager.up_migrations[-1].sql
    assert "chat_knowledgeization" in manager.down_migrations[-1].sql


@pytest.mark.asyncio
async def test_run_one_down_raises_clear_error_when_latest_version_has_no_down_migration():
    manager = AsyncMigrationManager()
    manager.runner.down_migrations = []
    from packages.core.database import async_migrate as async_migrate_module

    async def _fake_latest_version() -> int:
        return 1

    async_migrate_module.get_latest_version = _fake_latest_version  # type: ignore[assignment]
    with pytest.raises(
        RuntimeError, match="No rollback migration registered for version 1"
    ):
        await manager.runner.run_one_down()
