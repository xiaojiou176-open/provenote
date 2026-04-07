"""
Unit tests for the packages.core.domain module.

This test suite focuses on validation logic, business rules, and data structures
that can be tested without database mocking.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

import packages.core.domain.notebook as notebook_domain
from packages.core.ai.models import ModelManager
from packages.core.database.repository import ensure_record_id
from packages.core.domain.base import RecordModel
from packages.core.domain.content_settings import ContentSettings
from packages.core.domain.credential import Credential
from packages.core.domain.notebook import Asset, Note, Notebook, Source
from packages.core.domain.transformation import Transformation
from packages.core.exceptions import InvalidInputError
from packages.core.podcasts.models import EpisodeProfile, SpeakerProfile

# ============================================================================
# TEST SUITE 1: RecordModel Singleton Pattern
# ============================================================================


class TestRecordModelSingleton:
    """Test suite for RecordModel singleton behavior."""

    def test_recordmodel_singleton_behavior(self):
        """Test that same instance is returned for same record_id."""

        class TestRecord(RecordModel):
            record_id = "test:singleton"
            value: int = 0

        # Clear any existing instance
        TestRecord.clear_instance()

        # Create first instance
        instance1 = TestRecord(value=42)
        assert instance1.value == 42

        # Create second instance - should return same object
        instance2 = TestRecord(value=99)
        assert instance1 is instance2
        assert instance2.value == 99  # Value was updated

        # Cleanup
        TestRecord.clear_instance()


# ============================================================================
# TEST SUITE 2: ModelManager Instance Isolation
# ============================================================================


class TestModelManager:
    """Test suite for ModelManager instance behavior."""

    def test_model_manager_instance_isolation(self):
        """Test that each ModelManager instance is independent (not a singleton)."""
        manager1 = ModelManager()
        manager2 = ModelManager()

        # Each instance should be independent (not a singleton)
        assert manager1 is not manager2
        assert id(manager1) != id(manager2)


# ============================================================================
# TEST SUITE 3: Notebook Domain Logic
# ============================================================================


class TestNotebookDomain:
    """Test suite for Notebook validation and business rules."""

    def test_notebook_name_validation(self):
        """Test empty/whitespace names are rejected."""
        # Empty name should raise error
        with pytest.raises(InvalidInputError, match="Notebook name cannot be empty"):
            Notebook(name="", description="Test")

        # Whitespace-only name should raise error
        with pytest.raises(InvalidInputError, match="Notebook name cannot be empty"):
            Notebook(name="   ", description="Test")

        # Valid name should work
        notebook = Notebook(name="Valid Name", description="Test")
        assert notebook.name == "Valid Name"

    def test_notebook_archived_flag(self):
        """Test archived flag defaults to False."""
        notebook = Notebook(name="Test", description="Test")
        assert notebook.archived is False

        notebook_archived = Notebook(name="Test", description="Test", archived=True)
        assert notebook_archived.archived is True

    def test_notebook_description_defaults_to_empty_string(self):
        """Description should default to empty string for schema/domain consistency."""
        notebook = Notebook(name="Test")
        assert notebook.description == ""

    def test_notebook_description_normalizes_none_to_empty_string(self):
        """Explicit None description should be normalized to empty string."""
        notebook = Notebook(name="Test", description=None)  # type: ignore[arg-type]
        assert notebook.description == ""


class TestCredentialDomain:
    """Test suite for credential normalization rules."""

    def test_credential_provider_is_normalized(self):
        credential = Credential(name="Primary", provider="Google-Cloud", modalities=[])
        assert credential.provider == "google_cloud"


# ============================================================================
# TEST SUITE 4: Source Domain
# ============================================================================


class TestSourceDomain:
    """Test suite for Source domain model."""

    def test_source_command_field_parsing(self):
        """Test RecordID parsing for command field."""
        # Test with string command
        source = Source(title="Test", command="command:123")
        assert source.command == ensure_record_id("command:123")

        # Test with None command
        source2 = Source(title="Test", command=None)
        assert source2.command is None

        # Test command is included in save data prep
        source3 = Source(id="source:123", title="Test", command="command:456")
        save_data = source3._prepare_save_data()
        assert "command" in save_data

    @pytest.mark.asyncio
    async def test_source_delete_cleans_up_file(self, monkeypatch, tmp_path: Path):
        """Test that deleting a source removes the associated file."""
        uploads_root = tmp_path / "uploads"
        uploads_root.mkdir(parents=True)
        source_file = uploads_root / "source.txt"
        source_file.write_text("Test content", encoding="utf-8")
        monkeypatch.setattr(notebook_domain, "UPLOADS_FOLDER", str(uploads_root))

        source = Source(
            id="source:test_delete",
            title="Test Source",
            asset=Asset(file_path=str(source_file)),
        )
        assert source_file.exists()

        # Mock the parent delete method to avoid database operations
        with patch.object(
            Source.__bases__[0], "delete", new_callable=AsyncMock
        ) as mock_delete:
            mock_delete.return_value = True

            # Delete the source
            result = await source.delete()

            # Verify parent delete was called
            mock_delete.assert_called_once()
            assert result is True

        # Verify file was deleted
        assert not source_file.exists()

    @pytest.mark.asyncio
    async def test_source_delete_blocks_path_traversal_and_continues_db_delete(
        self, monkeypatch, tmp_path: Path
    ):
        uploads_root = tmp_path / "uploads"
        uploads_root.mkdir(parents=True)
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("outside", encoding="utf-8")
        escaped_path = uploads_root / ".." / "outside.txt"
        monkeypatch.setattr(notebook_domain, "UPLOADS_FOLDER", str(uploads_root))

        source = Source(
            id="source:test_escape",
            title="Test Source",
            asset=Asset(file_path=str(escaped_path)),
        )

        with patch.object(
            Source.__bases__[0], "delete", new_callable=AsyncMock
        ) as mock_delete:
            mock_delete.return_value = True
            with patch.object(notebook_domain.logger, "warning") as mock_warning:
                result = await source.delete()

            assert result is True
            mock_delete.assert_called_once()
            assert outside_file.exists()
            assert mock_warning.call_count >= 1

    @pytest.mark.asyncio
    async def test_source_delete_blocks_symlink_escape_and_continues_db_delete(
        self, monkeypatch, tmp_path: Path
    ):
        uploads_root = tmp_path / "uploads"
        uploads_root.mkdir(parents=True)
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("outside", encoding="utf-8")
        symlink_path = uploads_root / "escape-link.txt"
        symlink_path.symlink_to(outside_file)
        monkeypatch.setattr(notebook_domain, "UPLOADS_FOLDER", str(uploads_root))

        source = Source(
            id="source:test_symlink_escape",
            title="Test Source",
            asset=Asset(file_path=str(symlink_path)),
        )

        with patch.object(
            Source.__bases__[0], "delete", new_callable=AsyncMock
        ) as mock_delete:
            mock_delete.return_value = True
            with patch.object(notebook_domain.logger, "warning") as mock_warning:
                result = await source.delete()

            assert result is True
            mock_delete.assert_called_once()
            assert outside_file.exists()
            assert symlink_path.exists()
            assert mock_warning.call_count >= 1

    @pytest.mark.asyncio
    async def test_source_delete_without_file(self):
        """Test that deleting a source without a file doesn't fail."""
        # Create source without file asset
        source = Source(id="source:test_no_file", title="Test Source", asset=None)

        # Mock the parent delete method
        with patch.object(
            Source.__bases__[0], "delete", new_callable=AsyncMock
        ) as mock_delete:
            mock_delete.return_value = True

            # Delete should complete without error
            result = await source.delete()
            assert result is True
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_source_delete_continues_on_file_error(self):
        """Test that source deletion continues even if file deletion fails."""
        # Create source with non-existent file
        source = Source(
            id="source:test_missing_file",
            title="Test Source",
            asset=Asset(file_path="/nonexistent/path/file.txt"),
        )

        # Mock the parent delete method
        with patch.object(
            Source.__bases__[0], "delete", new_callable=AsyncMock
        ) as mock_delete:
            mock_delete.return_value = True

            # Delete should complete even though file doesn't exist
            result = await source.delete()
            assert result is True
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_vectorize_raises_valueerror_when_no_text(self):
        """Test that vectorize() raises ValueError (not DatabaseOperationError) for empty text."""
        source = Source(id="source:test_empty", title="Test", full_text=None)
        with pytest.raises(ValueError, match="has no text to vectorize"):
            await source.vectorize()

    @pytest.mark.asyncio
    async def test_vectorize_raises_valueerror_when_empty_string(self):
        """Test that vectorize() raises ValueError for empty string."""
        source = Source(id="source:test_empty_str", title="Test", full_text="")
        with pytest.raises(ValueError, match="has no text to vectorize"):
            await source.vectorize()

    @pytest.mark.asyncio
    async def test_vectorize_raises_valueerror_when_whitespace_only(self):
        """Test that vectorize() raises ValueError for whitespace-only text."""
        source = Source(id="source:test_ws", title="Test", full_text="   \n\t  ")
        with pytest.raises(ValueError, match="has no text to vectorize"):
            await source.vectorize()

    @pytest.mark.asyncio
    async def test_vectorize_submits_command_with_valid_text(self):
        """Test that vectorize() submits embed_source command when text is valid."""
        source = Source(id="source:test_valid", title="Test", full_text="Real content")
        with patch(
            "packages.core.application.command_service.CommandService.submit_command_job",
            new_callable=AsyncMock,
        ) as mock_submit:
            mock_submit.return_value = "command:123"
            result = await source.vectorize()
            mock_submit.assert_called_once_with(
                module_name="open_notebook",
                command_name="embed_source",
                command_args={"source_id": "source:test_valid"},
            )
            assert result == "command:123"


# ============================================================================
# TEST SUITE 5: Note Domain
# ============================================================================


class TestNoteDomain:
    """Test suite for Note validation."""

    def test_note_content_validation(self):
        """Test empty content is rejected."""
        # None content is allowed
        note = Note(title="Test", content=None)
        assert note.content is None

        # Non-empty content is valid
        note2 = Note(title="Test", content="Valid content")
        assert note2.content == "Valid content"

        # Empty string should raise error
        with pytest.raises(InvalidInputError, match="Note content cannot be empty"):
            Note(title="Test", content="")

        # Whitespace-only should raise error
        with pytest.raises(InvalidInputError, match="Note content cannot be empty"):
            Note(title="Test", content="   ")

    def test_note_content_for_embedding(self):
        """Test notes can hold content for embedding.

        Note: Embedding is now handled via command submission in Note.save(),
        not via needs_embedding() method. This test verifies basic content handling.
        """
        note = Note(title="Test", content="Test content")
        assert note.content == "Test content"

        # Test with None content - valid, no embedding will be submitted
        note2 = Note(title="Test", content=None)
        assert note2.content is None


# ============================================================================
# TEST SUITE 6: Podcast Domain Validation
# ============================================================================


class TestPodcastDomain:
    """Test suite for Podcast domain validation."""

    def test_speaker_profile_validation(self):
        """Test speaker profile validates count and required fields."""
        # Test invalid - no speakers
        with pytest.raises(ValidationError):
            SpeakerProfile(
                name="Test",
                description="Test speaker profile",
                tts_provider="google",
                tts_model="gemini-2.5-flash-preview-tts",
                speakers=[],
            )

        # Test invalid - too many speakers (> 4)
        with pytest.raises(ValidationError):
            SpeakerProfile(
                name="Test",
                description="Test speaker profile",
                tts_provider="google",
                tts_model="gemini-2.5-flash-preview-tts",
                speakers=[{"name": f"Speaker{i}"} for i in range(5)],
            )

        # Test invalid - missing required fields
        with pytest.raises(ValidationError):
            SpeakerProfile(
                name="Test",
                description="Test speaker profile",
                tts_provider="google",
                tts_model="gemini-2.5-flash-preview-tts",
                speakers=[
                    {"name": "Speaker 1"}
                ],  # Missing voice_id, backstory, personality
            )

        # Test valid - single speaker with all fields
        profile = SpeakerProfile(
            name="Test",
            description="Test speaker profile",
            tts_provider="google",
            tts_model="gemini-2.5-flash-preview-tts",
            speakers=[
                {
                    "name": "Host",
                    "voice_id": "voice123",
                    "backstory": "A friendly host",
                    "personality": "Enthusiastic and welcoming",
                }
            ],
        )
        assert len(profile.speakers) == 1
        assert profile.speakers[0]["name"] == "Host"


# ============================================================================
# TEST SUITE 7: Transformation Domain
# ============================================================================


class TestTransformationDomain:
    """Test suite for Transformation domain model."""

    def test_transformation_creation(self):
        """Test transformation model creation."""
        transform = Transformation(
            name="summarize",
            title="Summarize Content",
            description="Creates a summary",
            prompt="Summarize the following text: {content}",
            apply_default=True,
        )

        assert transform.name == "summarize"
        assert transform.apply_default is True


# ============================================================================
# TEST SUITE 8: Content Settings
# ============================================================================


class TestContentSettings:
    """Test suite for ContentSettings defaults."""

    def test_content_settings_defaults(self):
        """Test ContentSettings has proper defaults."""
        settings = ContentSettings(
            default_content_processing_engine_doc="auto",
            default_content_processing_engine_url="auto",
            default_embedding_option="ask",
            auto_delete_files="yes",
            youtube_preferred_languages=[
                "en",
                "pt",
                "es",
                "de",
                "nl",
                "en-GB",
                "fr",
                "de",
                "hi",
                "ja",
            ],
        )

        assert settings.record_id == "open_notebook:content_settings"
        assert settings.default_content_processing_engine_doc == "auto"
        assert settings.default_embedding_option == "ask"
        assert settings.auto_delete_files == "yes"
        assert settings.youtube_preferred_languages == [
            "en",
            "pt",
            "es",
            "de",
            "nl",
            "en-GB",
            "fr",
            "de",
            "hi",
            "ja",
        ]


# ============================================================================
# TEST SUITE 9: Episode Profile Validation
# ============================================================================


class TestEpisodeProfile:
    """Test suite for EpisodeProfile validation."""

    def test_episode_profile_segment_validation(self):
        """Test segment count validation (3-20)."""
        # Test invalid - too few segments
        with pytest.raises(
            ValidationError, match="Number of segments must be between 3 and 20"
        ):
            EpisodeProfile(
                name="Test",
                description="Test episode profile",
                speaker_config="default",
                outline_provider="google",
                outline_model="gemini-2.5-pro",
                transcript_provider="google",
                transcript_model="gemini-2.5-flash",
                default_briefing="Test briefing",
                num_segments=2,
            )

        # Test invalid - too many segments
        with pytest.raises(
            ValidationError, match="Number of segments must be between 3 and 20"
        ):
            EpisodeProfile(
                name="Test",
                description="Test episode profile",
                speaker_config="default",
                outline_provider="google",
                outline_model="gemini-2.5-pro",
                transcript_provider="google",
                transcript_model="gemini-2.5-flash",
                default_briefing="Test briefing",
                num_segments=21,
            )

        # Test valid segment count
        profile = EpisodeProfile(
            name="Test",
            description="Test episode profile",
            speaker_config="default",
            outline_provider="google",
            outline_model="gemini-2.5-pro",
            transcript_provider="google",
            transcript_model="gemini-2.5-flash",
            default_briefing="Test briefing",
            num_segments=5,
        )
        assert profile.num_segments == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
