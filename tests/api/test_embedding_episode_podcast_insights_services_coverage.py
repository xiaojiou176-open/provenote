from unittest.mock import MagicMock

import pytest

from services.api.embedding_service import EmbeddingService, embedding_service
from services.api.episode_profiles_service import (
    EpisodeProfilesService,
    episode_profiles_service,
)
from services.api.insights_service import InsightsService, insights_service
from services.api.podcast_api_service import PodcastAPIService, podcast_api_service


def _profile_payload(**overrides):
    payload = {
        "id": "episode_profile:1",
        "name": "Tech Deep Dive",
        "description": "default desc",
        "speaker_config": "speaker_cfg",
        "outline_provider": "google",
        "outline_model": "gemini-3.0-pro",
        "transcript_provider": "google",
        "transcript_model": "gemini-3.0-flash",
        "default_briefing": "briefing",
        "num_segments": 5,
    }
    payload.update(overrides)
    return payload


def _insight_payload(**overrides):
    payload = {
        "id": "source_insight:1",
        "insight_type": "summary",
        "content": "insight content",
        "created": "2026-02-28T00:00:00Z",
        "updated": "2026-02-28T00:00:00Z",
    }
    payload.update(overrides)
    return payload


def _note_payload(**overrides):
    payload = {
        "id": "note:1",
        "title": "Saved insight",
        "content": "note content",
        "note_type": "ai",
        "created": "2026-02-28T00:00:00Z",
        "updated": "2026-02-28T00:00:00Z",
    }
    payload.update(overrides)
    return payload


def test_embedding_service_export_and_embed_content_forwarding(monkeypatch):
    assert isinstance(embedding_service, EmbeddingService)

    expected = {"ok": True, "item_id": "source:1"}
    embed_mock = MagicMock(return_value=expected)
    monkeypatch.setattr(
        "services.api.embedding_service.api_client.embed_content", embed_mock
    )

    service = EmbeddingService()
    result = service.embed_content("source:1", "source")

    assert result == expected
    embed_mock.assert_called_once_with(item_id="source:1", item_type="source")


def test_episode_profiles_service_export_and_get_all_profiles_with_default_description(
    monkeypatch,
):
    assert isinstance(episode_profiles_service, EpisodeProfilesService)

    profile_missing_description = _profile_payload(
        id="episode_profile:2", name="No Desc"
    )
    profile_missing_description.pop("description")
    api_profiles = [
        _profile_payload(description="explicit"),
        profile_missing_description,
    ]
    monkeypatch.setattr(
        "services.api.episode_profiles_service.api_client.get_episode_profiles",
        MagicMock(return_value=api_profiles),
    )

    service = EpisodeProfilesService()
    profiles = service.get_all_episode_profiles()

    assert [p.id for p in profiles] == ["episode_profile:1", "episode_profile:2"]
    assert [p.name for p in profiles] == ["Tech Deep Dive", "No Desc"]
    assert profiles[0].description == "explicit"
    assert profiles[1].description == ""


@pytest.mark.parametrize("api_response", [_profile_payload(), [_profile_payload()]])
def test_episode_profiles_service_get_episode_profile_supports_dict_and_list(
    monkeypatch, api_response
):
    get_mock = MagicMock(return_value=api_response)
    monkeypatch.setattr(
        "services.api.episode_profiles_service.api_client.get_episode_profile", get_mock
    )

    service = EpisodeProfilesService()
    profile = service.get_episode_profile("Tech Deep Dive")

    assert profile.id == "episode_profile:1"
    assert profile.name == "Tech Deep Dive"
    get_mock.assert_called_once_with("Tech Deep Dive")


@pytest.mark.parametrize("api_response", [_profile_payload(), [_profile_payload()]])
def test_episode_profiles_service_create_episode_profile_supports_dict_and_list(
    monkeypatch, api_response
):
    create_mock = MagicMock(return_value=api_response)
    monkeypatch.setattr(
        "services.api.episode_profiles_service.api_client.create_episode_profile",
        create_mock,
    )

    service = EpisodeProfilesService()
    created = service.create_episode_profile(
        name="Tech Deep Dive",
        description="d",
        speaker_config="sp",
        outline_provider="google",
        outline_model="gemini-3.0-pro",
        transcript_provider="google",
        transcript_model="gemini-3.0-flash",
        default_briefing="brief",
        num_segments=6,
    )

    assert created.id == "episode_profile:1"
    assert created.name == "Tech Deep Dive"
    create_mock.assert_called_once_with(
        name="Tech Deep Dive",
        description="d",
        speaker_config="sp",
        outline_provider="google",
        outline_model="gemini-3.0-pro",
        transcript_provider="google",
        transcript_model="gemini-3.0-flash",
        default_briefing="brief",
        num_segments=6,
    )


def test_episode_profiles_service_delete_profile_returns_true(monkeypatch):
    delete_mock = MagicMock(return_value=None)
    monkeypatch.setattr(
        "services.api.episode_profiles_service.api_client.delete_episode_profile",
        delete_mock,
    )

    service = EpisodeProfilesService()
    assert service.delete_episode_profile("episode_profile:1") is True
    delete_mock.assert_called_once_with("episode_profile:1")


def test_insights_service_export_and_get_source_insights(monkeypatch):
    assert isinstance(insights_service, InsightsService)

    payload = [
        _insight_payload(),
        _insight_payload(id="source_insight:2", insight_type="key_point"),
    ]
    monkeypatch.setattr(
        "services.api.insights_service.api_client.get_source_insights",
        MagicMock(return_value=payload),
    )

    service = InsightsService()
    insights = service.get_source_insights("source:1")

    assert [i.id for i in insights] == ["source_insight:1", "source_insight:2"]
    assert [i.insight_type for i in insights] == ["summary", "key_point"]


@pytest.mark.parametrize("api_response", [_insight_payload(), [_insight_payload()]])
def test_insights_service_get_insight_supports_dict_and_list(monkeypatch, api_response):
    get_mock = MagicMock(return_value=api_response)
    monkeypatch.setattr(
        "services.api.insights_service.api_client.get_insight", get_mock
    )

    service = InsightsService()
    insight = service.get_insight("source_insight:1")

    assert insight.id == "source_insight:1"
    assert insight.insight_type == "summary"
    get_mock.assert_called_once_with("source_insight:1")


def test_insights_service_delete_insight_returns_true(monkeypatch):
    delete_mock = MagicMock(return_value=None)
    monkeypatch.setattr(
        "services.api.insights_service.api_client.delete_insight", delete_mock
    )

    service = InsightsService()
    assert service.delete_insight("source_insight:1") is True
    delete_mock.assert_called_once_with("source_insight:1")


@pytest.mark.parametrize("api_response", [_note_payload(), [_note_payload()]])
def test_insights_service_save_insight_as_note_supports_dict_and_list(
    monkeypatch, api_response
):
    save_mock = MagicMock(return_value=api_response)
    monkeypatch.setattr(
        "services.api.insights_service.api_client.save_insight_as_note", save_mock
    )

    service = InsightsService()
    note = service.save_insight_as_note("source_insight:1", notebook_id="notebook:1")

    assert note.id == "note:1"
    assert note.note_type == "ai"
    save_mock.assert_called_once_with("source_insight:1", "notebook:1")


@pytest.mark.parametrize("api_response", [_insight_payload(), [_insight_payload()]])
def test_insights_service_create_source_insight_supports_dict_and_list(
    monkeypatch, api_response
):
    create_mock = MagicMock(return_value=api_response)
    monkeypatch.setattr(
        "services.api.insights_service.api_client.create_source_insight", create_mock
    )

    service = InsightsService()
    insight = service.create_source_insight("source:1", "transformation:1", "model:1")

    assert insight.id == "source_insight:1"
    assert insight.content == "insight content"
    create_mock.assert_called_once_with("source:1", "transformation:1", "model:1")


def test_podcast_api_service_export_and_list_normalization(monkeypatch):
    assert isinstance(podcast_api_service, PodcastAPIService)

    request_mock = MagicMock(side_effect=[[{"id": "episode:1"}], {"id": "episode:2"}])
    monkeypatch.setattr(
        "services.api.podcast_api_service.api_client._make_request", request_mock
    )

    service = PodcastAPIService()
    episodes = service.get_episodes()
    speakers = service.get_speaker_profiles()

    assert episodes == [{"id": "episode:1"}]
    assert speakers == [{"id": "episode:2"}]


def test_podcast_api_service_get_episode_profiles_forwards(monkeypatch):
    payload = [{"id": "episode_profile:1"}]
    get_mock = MagicMock(return_value=payload)
    monkeypatch.setattr(
        "services.api.podcast_api_service.api_client.get_episode_profiles", get_mock
    )

    service = PodcastAPIService()
    assert service.get_episode_profiles() == payload
    get_mock.assert_called_once_with()


@pytest.mark.parametrize(
    ("method_name", "target", "args", "kwargs"),
    [
        (
            "delete_episode",
            "services.api.podcast_api_service.api_client._make_request",
            ("episode:1",),
            {},
        ),
        (
            "create_episode_profile",
            "services.api.podcast_api_service.api_client.create_episode_profile",
            ({"name": "p"},),
            {},
        ),
        (
            "update_episode_profile",
            "services.api.podcast_api_service.api_client.update_episode_profile",
            ("episode_profile:1", {"name": "p"}),
            {},
        ),
        (
            "delete_episode_profile",
            "services.api.podcast_api_service.api_client.delete_episode_profile",
            ("episode_profile:1",),
            {},
        ),
        (
            "duplicate_episode_profile",
            "services.api.podcast_api_service.api_client._make_request",
            ("episode_profile:1",),
            {},
        ),
        (
            "create_speaker_profile",
            "services.api.podcast_api_service.api_client._make_request",
            ({"name": "sp"},),
            {},
        ),
        (
            "update_speaker_profile",
            "services.api.podcast_api_service.api_client._make_request",
            ("speaker_profile:1", {"name": "sp"}),
            {},
        ),
        (
            "delete_speaker_profile",
            "services.api.podcast_api_service.api_client._make_request",
            ("speaker_profile:1",),
            {},
        ),
        (
            "duplicate_speaker_profile",
            "services.api.podcast_api_service.api_client._make_request",
            ("speaker_profile:1",),
            {},
        ),
    ],
)
def test_podcast_api_service_boolean_methods_success_and_failure(
    monkeypatch, method_name, target, args, kwargs
):
    service = PodcastAPIService()

    success_mock = MagicMock(return_value={"ok": True})
    monkeypatch.setattr(target, success_mock)
    assert getattr(service, method_name)(*args, **kwargs) is True

    def _raise(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(target, _raise)
    assert getattr(service, method_name)(*args, **kwargs) is False
