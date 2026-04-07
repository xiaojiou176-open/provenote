from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_shared_context_types_exist_outside_page_layer() -> None:
    context_types = REPO_ROOT / "apps/web/src/lib/types/context.ts"
    assert context_types.exists()
    text = context_types.read_text(encoding="utf-8")
    assert "export type ContextMode" in text
    assert "export interface ContextSelections" in text


def test_shared_dialogs_are_owned_by_components_or_providers_layer() -> None:
    assert (
        REPO_ROOT / "apps/web/src/components/notebooks/NoteEditorDialog.tsx"
    ).exists()
    assert (
        REPO_ROOT / "apps/web/src/components/providers/CreateDialogsProvider.tsx"
    ).exists()


def test_page_layer_no_longer_owns_shared_context_contracts() -> None:
    notebook_page = (
        REPO_ROOT / "apps/web/src/app/(dashboard)/notebooks/[id]/page.tsx"
    ).read_text(encoding="utf-8")
    assert "export interface ContextSelections" not in notebook_page
