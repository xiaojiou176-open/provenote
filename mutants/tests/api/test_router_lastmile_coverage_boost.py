from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from packages.core.application.models import (
    DefaultPromptUpdate,
    TransformationCreate,
    TransformationExecuteRequest,
    TransformationUpdate,
)
from packages.core.exceptions import InvalidInputError, OpenNotebookError
from services.api.routers import config as config_router
from services.api.routers import episode_profiles as episode_router
from services.api.routers import speaker_profiles as speaker_router
from services.api.routers import transformations as transformations_router


@pytest.mark.asyncio
async def test_episode_router_create_update_and_duplicate_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeEpisodeProfile:
        created_rows: list["FakeEpisodeProfile"] = []

        def __init__(self, **kwargs):
            self.id = kwargs.get("id", "episode:new")
            self.name = kwargs["name"]
            self.description = kwargs["description"]
            self.speaker_config = kwargs["speaker_config"]
            self.outline_provider = kwargs["outline_provider"]
            self.outline_model = kwargs["outline_model"]
            self.transcript_provider = kwargs["transcript_provider"]
            self.transcript_model = kwargs["transcript_model"]
            self.default_briefing = kwargs["default_briefing"]
            self.num_segments = kwargs["num_segments"]

        async def save(self) -> None:
            self.__class__.created_rows.append(self)

        async def delete(self) -> None:
            return None

        @classmethod
        async def get(cls, profile_id: str):
            if profile_id == "episode:1":
                instance = cls(
                    id=profile_id,
                    name="old",
                    description="old",
                    speaker_config="speaker:1",
                    outline_provider="google",
                    outline_model="m1",
                    transcript_provider="google",
                    transcript_model="m2",
                    default_briefing="b",
                    num_segments=5,
                )
                return instance
            if profile_id == "episode:dup":
                return SimpleNamespace(
                    id="episode:dup",
                    name="Original",
                    description="desc",
                    speaker_config="speaker:cfg",
                    outline_provider="google",
                    outline_model="model-x",
                    transcript_provider="google",
                    transcript_model="model-y",
                    default_briefing="brief",
                    num_segments=7,
                )
            return None

    monkeypatch.setattr(episode_router, "EpisodeProfile", FakeEpisodeProfile)

    created = await episode_router.create_episode_profile(
        episode_router.EpisodeProfileCreate(
            name="n1",
            description="d1",
            speaker_config="speaker:1",
            outline_provider=" Google ",
            outline_model="gemini-a",
            transcript_provider="GOOGLE",
            transcript_model="gemini-b",
            default_briefing="brief",
            num_segments=3,
        )
    )
    assert created.outline_provider == "google"
    assert created.transcript_provider == "google"

    updated = await episode_router.update_episode_profile(
        "episode:1",
        episode_router.EpisodeProfileCreate(
            name="n2",
            description="d2",
            speaker_config="speaker:2",
            outline_provider="google",
            outline_model="gemini-c",
            transcript_provider="google",
            transcript_model="gemini-d",
            default_briefing="brief2",
            num_segments=4,
        ),
    )
    assert updated.name == "n2"
    assert updated.num_segments == 4

    duplicated = await episode_router.duplicate_episode_profile("episode:dup")
    assert duplicated.name == "Original - Copy"

    with pytest.raises(HTTPException) as missing_update:
        await episode_router.update_episode_profile(
            "episode:404",
            episode_router.EpisodeProfileCreate(
                name="x",
                description="x",
                speaker_config="x",
                outline_provider="google",
                outline_model="x",
                transcript_provider="google",
                transcript_model="x",
                default_briefing="x",
                num_segments=1,
            ),
        )
    assert missing_update.value.status_code == 404

    with pytest.raises(HTTPException) as bad_provider:
        await episode_router.create_episode_profile(
            episode_router.EpisodeProfileCreate(
                name="x",
                description="x",
                speaker_config="x",
                outline_provider="openai",
                outline_model="x",
                transcript_provider="google",
                transcript_model="x",
                default_briefing="x",
                num_segments=1,
            )
        )
    assert bad_provider.value.status_code == 400


@pytest.mark.asyncio
async def test_episode_router_list_get_delete_and_duplicate_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(
        id="episode:1",
        name="P1",
        description=None,
        speaker_config="sp",
        outline_provider="google",
        outline_model="m1",
        transcript_provider="google",
        transcript_model="m2",
        default_briefing="brief",
        num_segments=6,
        delete=AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        episode_router.EpisodeProfile, "get_all", AsyncMock(return_value=[profile])
    )
    listed = await episode_router.list_episode_profiles()
    assert len(listed) == 1
    assert listed[0].description == ""

    monkeypatch.setattr(
        episode_router.EpisodeProfile, "get_by_name", AsyncMock(return_value=profile)
    )
    got = await episode_router.get_episode_profile("P1")
    assert got.name == "P1"

    monkeypatch.setattr(
        episode_router.EpisodeProfile, "get_by_name", AsyncMock(return_value=None)
    )
    with pytest.raises(HTTPException) as missing_get:
        await episode_router.get_episode_profile("missing")
    assert missing_get.value.status_code == 404

    monkeypatch.setattr(
        episode_router.EpisodeProfile, "get", AsyncMock(return_value=profile)
    )
    deleted = await episode_router.delete_episode_profile("episode:1")
    assert deleted["message"] == "Episode profile deleted successfully"

    monkeypatch.setattr(
        episode_router.EpisodeProfile,
        "get_all",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    with pytest.raises(HTTPException) as list_err:
        await episode_router.list_episode_profiles()
    assert list_err.value.status_code == 500

    monkeypatch.setattr(
        episode_router.EpisodeProfile,
        "get",
        AsyncMock(side_effect=RuntimeError("read failed")),
    )
    with pytest.raises(HTTPException) as dup_err:
        await episode_router.duplicate_episode_profile("episode:x")
    assert dup_err.value.status_code == 500


@pytest.mark.asyncio
async def test_speaker_router_create_update_duplicate_and_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSpeakerProfile:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", "speaker:new")
            self.name = kwargs["name"]
            self.description = kwargs["description"]
            self.tts_provider = kwargs["tts_provider"]
            self.tts_model = kwargs["tts_model"]
            self.speakers = kwargs["speakers"]

        async def save(self) -> None:
            return None

        async def delete(self) -> None:
            return None

        @classmethod
        async def get(cls, profile_id: str):
            if profile_id == "speaker:1":
                instance = cls(
                    id=profile_id,
                    name="old",
                    description="desc",
                    tts_provider="google",
                    tts_model="m0",
                    speakers=[{"name": "A"}],
                )
                return instance
            if profile_id == "speaker:dup":
                return SimpleNamespace(
                    id="speaker:dup",
                    name="HostGroup",
                    description="desc",
                    tts_provider="google",
                    tts_model="voice",
                    speakers=[{"name": "Host"}],
                )
            return None

    monkeypatch.setattr(speaker_router, "SpeakerProfile", FakeSpeakerProfile)

    payload = speaker_router.SpeakerProfileCreate(
        name="sp",
        description="desc",
        tts_provider=" GOOGLE ",
        tts_model="tts-1",
        speakers=[{"name": "Host"}],
    )
    created = await speaker_router.create_speaker_profile(payload)
    assert created.tts_provider == "google"

    updated = await speaker_router.update_speaker_profile(
        "speaker:1",
        speaker_router.SpeakerProfileCreate(
            name="sp2",
            description="desc2",
            tts_provider="google",
            tts_model="tts-2",
            speakers=[{"name": "Host2"}],
        ),
    )
    assert updated.name == "sp2"

    duplicated = await speaker_router.duplicate_speaker_profile("speaker:dup")
    assert duplicated.name == "HostGroup - Copy"

    with pytest.raises(HTTPException) as bad_provider:
        await speaker_router.create_speaker_profile(
            speaker_router.SpeakerProfileCreate(
                name="bad",
                description="bad",
                tts_provider="azure",
                tts_model="tts",
                speakers=[{"name": "X"}],
            )
        )
    assert bad_provider.value.status_code == 400

    monkeypatch.setattr(
        speaker_router,
        "SpeakerProfile",
        SimpleNamespace(get=AsyncMock(side_effect=RuntimeError("boom"))),
    )
    with pytest.raises(HTTPException) as delete_err:
        await speaker_router.delete_speaker_profile("speaker:1")
    assert delete_err.value.status_code == 500


@pytest.mark.asyncio
async def test_speaker_router_list_get_and_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(
        id="speaker:1",
        name="Team",
        description=None,
        tts_provider="google",
        tts_model="tts",
        speakers=[{"name": "A"}],
    )

    monkeypatch.setattr(
        speaker_router.SpeakerProfile, "get_all", AsyncMock(return_value=[profile])
    )
    listed = await speaker_router.list_speaker_profiles()
    assert listed[0].description == ""

    monkeypatch.setattr(
        speaker_router.SpeakerProfile, "get_by_name", AsyncMock(return_value=profile)
    )
    got = await speaker_router.get_speaker_profile("Team")
    assert got.name == "Team"

    monkeypatch.setattr(
        speaker_router.SpeakerProfile, "get_by_name", AsyncMock(return_value=None)
    )
    with pytest.raises(HTTPException) as missing:
        await speaker_router.get_speaker_profile("missing")
    assert missing.value.status_code == 404

    monkeypatch.setattr(
        speaker_router.SpeakerProfile,
        "get_all",
        AsyncMock(side_effect=RuntimeError("db fail")),
    )
    with pytest.raises(HTTPException) as list_err:
        await speaker_router.list_speaker_profiles()
    assert list_err.value.status_code == 500


@pytest.mark.asyncio
async def test_transformations_router_success_and_common_error_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = SimpleNamespace(
        id="tr:1",
        name="n",
        title="t",
        description="d",
        prompt="p",
        apply_default=False,
        created="2026-01-01",
        updated="2026-01-02",
    )
    monkeypatch.setattr(
        transformations_router.Transformation,
        "get_all",
        AsyncMock(return_value=[row]),
    )
    listed = await transformations_router.get_transformations()
    assert listed[0].id == "tr:1"

    class FakeTransformation:
        def __init__(self, **kwargs):
            self.id = "tr:new"
            self.name = kwargs["name"]
            self.title = kwargs["title"]
            self.description = kwargs["description"]
            self.prompt = kwargs["prompt"]
            self.apply_default = kwargs["apply_default"]
            self.created = "2026-01-01"
            self.updated = "2026-01-01"

        async def save(self) -> None:
            return None

        async def delete(self) -> None:
            return None

        @classmethod
        async def get(cls, transformation_id: str):
            if transformation_id == "tr:1":
                inst = cls(
                    name="n1",
                    title="t1",
                    description="d1",
                    prompt="p1",
                    apply_default=True,
                )
                inst.id = "tr:1"
                inst.created = "2026-01-01"
                inst.updated = "2026-01-02"
                return inst
            return None

    monkeypatch.setattr(transformations_router, "Transformation", FakeTransformation)

    created = await transformations_router.create_transformation(
        TransformationCreate(
            name="normalize",
            title="Normalize",
            description="desc",
            prompt="do it",
            apply_default=True,
        )
    )
    assert created.id == "tr:new"

    updated = await transformations_router.update_transformation(
        "tr:1",
        TransformationUpdate(name="new-name"),
    )
    assert updated.name == "new-name"

    deleted = await transformations_router.delete_transformation("tr:1")
    assert deleted["message"] == "Transformation deleted successfully"

    with pytest.raises(HTTPException) as not_found:
        await transformations_router.get_transformation("tr:404")
    assert not_found.value.status_code == 404

    monkeypatch.setattr(
        transformations_router,
        "Transformation",
        SimpleNamespace(
            get_all=AsyncMock(side_effect=RuntimeError("db down")),
            get=AsyncMock(side_effect=RuntimeError("db down")),
        ),
    )
    with pytest.raises(HTTPException) as list_err:
        await transformations_router.get_transformations()
    assert list_err.value.status_code == 500
    with pytest.raises(HTTPException) as get_err:
        await transformations_router.get_transformation("tr:1")
    assert get_err.value.status_code == 500


@pytest.mark.asyncio
async def test_transformations_execute_and_default_prompt_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transformation = SimpleNamespace(id="tr:1")
    model = SimpleNamespace(id="model:1")

    monkeypatch.setattr(
        transformations_router.Transformation,
        "get",
        AsyncMock(return_value=transformation),
    )
    monkeypatch.setattr(
        transformations_router.Model, "get", AsyncMock(return_value=model)
    )
    monkeypatch.setattr(
        transformations_router.transformation_graph,
        "ainvoke",
        AsyncMock(return_value={"output": "ok"}),
    )

    executed = await transformations_router.execute_transformation(
        TransformationExecuteRequest(
            transformation_id="tr:1",
            input_text="hello",
            model_id="model:1",
        )
    )
    assert executed.output == "ok"

    monkeypatch.setattr(
        transformations_router.transformation_graph,
        "ainvoke",
        AsyncMock(side_effect=OpenNotebookError("graph failure")),
    )
    with pytest.raises(OpenNotebookError):
        await transformations_router.execute_transformation(
            TransformationExecuteRequest(
                transformation_id="tr:1",
                input_text="hello",
                model_id="model:1",
            )
        )

    class InvalidCreateTransformation:
        def __init__(self, **_kwargs):
            raise InvalidInputError("bad")

    monkeypatch.setattr(
        transformations_router, "Transformation", InvalidCreateTransformation
    )
    with pytest.raises(HTTPException) as create_invalid:
        await transformations_router.create_transformation(
            TransformationCreate(
                name="x",
                title="x",
                description="x",
                prompt="x",
                apply_default=False,
            )
        )
    assert create_invalid.value.status_code == 400

    default_prompts = SimpleNamespace(
        transformation_instructions="initial",
        update=AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        transformations_router.DefaultPrompts,
        "get_instance",
        AsyncMock(return_value=default_prompts),
    )
    got_default = await transformations_router.get_default_prompt()
    assert got_default.transformation_instructions == "initial"

    updated_default = await transformations_router.update_default_prompt(
        DefaultPromptUpdate(transformation_instructions="updated")
    )
    assert updated_default.transformation_instructions == "updated"


@pytest.mark.asyncio
async def test_transformations_update_invalid_input_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = SimpleNamespace(
        id="tr:1",
        name="n",
        title="t",
        description="d",
        prompt="p",
        apply_default=False,
        created="2026-01-01",
        updated="2026-01-02",
        save=AsyncMock(side_effect=InvalidInputError("invalid save")),
    )
    monkeypatch.setattr(
        transformations_router.Transformation, "get", AsyncMock(return_value=target)
    )

    with pytest.raises(HTTPException) as exc:
        await transformations_router.update_transformation(
            "tr:1", TransformationUpdate(prompt="new")
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "invalid save"


@pytest.mark.asyncio
async def test_transformations_additional_error_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        transformations_router.Transformation,
        "get",
        AsyncMock(return_value=None),
    )
    with pytest.raises(HTTPException) as missing_tr:
        await transformations_router.execute_transformation(
            TransformationExecuteRequest(
                transformation_id="tr:missing",
                input_text="hello",
                model_id="model:1",
            )
        )
    assert missing_tr.value.status_code == 404

    monkeypatch.setattr(
        transformations_router.Transformation,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="tr:1")),
    )
    monkeypatch.setattr(
        transformations_router.Model, "get", AsyncMock(return_value=None)
    )
    with pytest.raises(HTTPException) as missing_model:
        await transformations_router.execute_transformation(
            TransformationExecuteRequest(
                transformation_id="tr:1",
                input_text="hello",
                model_id="model:missing",
            )
        )
    assert missing_model.value.status_code == 404

    monkeypatch.setattr(
        transformations_router.Model,
        "get",
        AsyncMock(return_value=SimpleNamespace(id="model:1")),
    )
    monkeypatch.setattr(
        transformations_router.transformation_graph,
        "ainvoke",
        AsyncMock(side_effect=RuntimeError("invoke failed")),
    )
    with pytest.raises(HTTPException) as invoke_err:
        await transformations_router.execute_transformation(
            TransformationExecuteRequest(
                transformation_id="tr:1",
                input_text="hello",
                model_id="model:1",
            )
        )
    assert invoke_err.value.status_code == 500

    monkeypatch.setattr(
        transformations_router.DefaultPrompts,
        "get_instance",
        AsyncMock(side_effect=RuntimeError("prompt store unavailable")),
    )
    with pytest.raises(HTTPException) as default_get_err:
        await transformations_router.get_default_prompt()
    assert default_get_err.value.status_code == 500

    with pytest.raises(HTTPException) as default_update_err:
        await transformations_router.update_default_prompt(
            DefaultPromptUpdate(transformation_instructions="new")
        )
    assert default_update_err.value.status_code == 500


@pytest.mark.asyncio
async def test_transformations_router_lastmile_missing_update_delete_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = SimpleNamespace(
        id="tr:2",
        name="n",
        title="t",
        description="d",
        prompt="p",
        apply_default=False,
        created="2026-01-01",
        updated="2026-01-02",
        save=AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        transformations_router.Transformation, "get", AsyncMock(return_value=row)
    )
    got = await transformations_router.get_transformation("tr:2")
    assert got.id == "tr:2"

    updated = await transformations_router.update_transformation(
        "tr:2",
        TransformationUpdate(
            title="new-title",
            description="new-desc",
            apply_default=True,
        ),
    )
    assert updated.title == "new-title"
    assert updated.description == "new-desc"
    assert updated.apply_default is True

    monkeypatch.setattr(
        transformations_router.Transformation, "get", AsyncMock(return_value=None)
    )
    with pytest.raises(HTTPException) as missing_update:
        await transformations_router.update_transformation(
            "tr:404", TransformationUpdate(title="x")
        )
    assert missing_update.value.status_code == 404

    broken = SimpleNamespace(
        id="tr:3",
        name="n",
        title="t",
        description="d",
        prompt="p",
        apply_default=False,
        created="2026-01-01",
        updated="2026-01-02",
        save=AsyncMock(side_effect=RuntimeError("save failed")),
    )
    monkeypatch.setattr(
        transformations_router.Transformation, "get", AsyncMock(return_value=broken)
    )
    with pytest.raises(HTTPException) as update_500:
        await transformations_router.update_transformation(
            "tr:3", TransformationUpdate(prompt="changed")
        )
    assert update_500.value.status_code == 500

    class FailingCreateTransformation:
        def __init__(self, **kwargs):
            self.id = "tr:new"
            self.name = kwargs["name"]
            self.title = kwargs["title"]
            self.description = kwargs["description"]
            self.prompt = kwargs["prompt"]
            self.apply_default = kwargs["apply_default"]
            self.created = "2026-01-01"
            self.updated = "2026-01-01"

        async def save(self) -> None:
            raise RuntimeError("create failed")

    monkeypatch.setattr(
        transformations_router, "Transformation", FailingCreateTransformation
    )
    with pytest.raises(HTTPException) as create_500:
        await transformations_router.create_transformation(
            TransformationCreate(
                name="n",
                title="t",
                description="d",
                prompt="p",
                apply_default=False,
            )
        )
    assert create_500.value.status_code == 500

    delete_target = SimpleNamespace(
        delete=AsyncMock(side_effect=RuntimeError("delete failed"))
    )
    monkeypatch.setattr(
        transformations_router,
        "Transformation",
        SimpleNamespace(get=AsyncMock(return_value=delete_target)),
    )
    with pytest.raises(HTTPException) as delete_500:
        await transformations_router.delete_transformation("tr:2")
    assert delete_500.value.status_code == 500


@pytest.mark.asyncio
async def test_config_router_cache_and_health_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _return_latest_version(*_args, **_kwargs):
        return "2.0.0"

    async def _raise_network_error(*_args, **_kwargs):
        raise RuntimeError("network error")

    async def _repo_query_online(*_args, **_kwargs):
        return [{"ok": 1}]

    async def _repo_query_offline(*_args, **_kwargs):
        return []

    async def _raise_wait_timeout(*_args, **_kwargs):
        raise asyncio.TimeoutError()

    async def _raise_wait_runtime_error(*_args, **_kwargs):
        raise RuntimeError("db error")

    config_router._version_cache.update(
        {
            "latest_version": "9.9.9",
            "has_update": True,
            "timestamp": 10_000.0,
            "check_failed": False,
        }
    )
    monkeypatch.setattr(config_router.time, "time", lambda: 10_010.0)
    latest, has_update = await config_router.get_latest_version_cached("1.0.0")
    assert latest == "9.9.9"
    assert has_update is True

    monkeypatch.setattr(config_router, "VERSION_CHECK_REPO_URL", None)
    config_router._version_cache.update(
        {
            "latest_version": None,
            "has_update": False,
            "timestamp": 0,
            "check_failed": False,
        }
    )
    monkeypatch.setattr(config_router.time, "time", lambda: 15_000.0)
    latest_disabled, has_update_disabled = await config_router.get_latest_version_cached(
        "1.0.0"
    )
    assert latest_disabled is None
    assert has_update_disabled is False
    assert config_router._version_cache["check_failed"] is False

    monkeypatch.setattr(
        config_router,
        "VERSION_CHECK_REPO_URL",
        "https://github.com/example/notebooklab-release-channel",
    )
    config_router._version_cache.update(
        {
            "latest_version": None,
            "has_update": False,
            "timestamp": 0,
            "check_failed": False,
        }
    )
    monkeypatch.setattr(
        config_router,
        "get_version_from_github_async",
        _return_latest_version,
    )
    monkeypatch.setattr(config_router, "compare_versions", lambda current, latest: -1)
    monkeypatch.setattr(config_router.time, "time", lambda: 20_000.0)
    latest2, has_update2 = await config_router.get_latest_version_cached("1.0.0")
    assert latest2 == "2.0.0"
    assert has_update2 is True

    monkeypatch.setattr(
        config_router,
        "get_version_from_github_async",
        _raise_network_error,
    )
    config_router._version_cache["timestamp"] = 1.0
    monkeypatch.setattr(
        config_router.time, "time", lambda: 1.0 + config_router.VERSION_CACHE_TTL + 1.0
    )
    latest3, has_update3 = await config_router.get_latest_version_cached("1.0.0")
    assert latest3 is None
    assert has_update3 is False
    assert config_router._version_cache["check_failed"] is True

    monkeypatch.setattr(config_router, "repo_query", _repo_query_online)
    assert await config_router.check_database_health() == {"status": "online"}

    monkeypatch.setattr(config_router, "repo_query", _repo_query_offline)
    assert (await config_router.check_database_health())["status"] == "offline"

    # Avoid creating an un-awaited coroutine when wait_for is force-failing below.
    monkeypatch.setattr(config_router, "repo_query", lambda *_args, **_kwargs: [])

    monkeypatch.setattr(
        config_router.asyncio,
        "wait_for",
        _raise_wait_timeout,
    )
    timeout_health = await config_router.check_database_health()
    assert timeout_health["error"] == "health_check_timeout"

    monkeypatch.setattr(
        config_router.asyncio,
        "wait_for",
        _raise_wait_runtime_error,
    )
    error_health = await config_router.check_database_health()
    assert error_health["status"] == "offline"
    assert error_health["error"] == "health_check_failed"


@pytest.mark.asyncio
async def test_speaker_router_not_found_and_create_error_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _missing_speaker_profile(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        speaker_router.SpeakerProfile,
        "get",
        _missing_speaker_profile,
    )
    request = speaker_router.SpeakerProfileCreate(
        name="n",
        description="d",
        tts_provider="google",
        tts_model="m",
        speakers=[{"name": "a"}],
    )

    with pytest.raises(HTTPException) as update_missing:
        await speaker_router.update_speaker_profile("speaker:404", request)
    assert update_missing.value.status_code == 404

    with pytest.raises(HTTPException) as delete_missing:
        await speaker_router.delete_speaker_profile("speaker:404")
    assert delete_missing.value.status_code == 404

    with pytest.raises(HTTPException) as duplicate_missing:
        await speaker_router.duplicate_speaker_profile("speaker:404")
    assert duplicate_missing.value.status_code == 404

    class FailingSpeakerProfile:
        def __init__(self, **_kwargs):
            raise RuntimeError("insert failed")

    monkeypatch.setattr(speaker_router, "SpeakerProfile", FailingSpeakerProfile)
    with pytest.raises(HTTPException) as create_err:
        await speaker_router.create_speaker_profile(request)
    assert create_err.value.status_code == 500


@pytest.mark.asyncio
async def test_config_router_get_version_fallback_and_happy_get_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_bad_toml(_file):
        raise RuntimeError("bad toml")

    monkeypatch.setattr(config_router.tomllib, "load", _raise_bad_toml)
    assert config_router.get_version() == "unknown"

    monkeypatch.setattr(config_router, "get_version", lambda: "1.2.3")

    async def _latest_ok(_current: str):
        return ("1.2.4", True)

    async def _health_ok():
        return {"status": "online"}

    monkeypatch.setattr(config_router, "get_latest_version_cached", _latest_ok)
    monkeypatch.setattr(config_router, "check_database_health", _health_ok)
    payload = await config_router.get_config(request=SimpleNamespace())
    assert payload == {
        "version": "1.2.3",
        "latestVersion": "1.2.4",
        "hasUpdate": True,
        "dbStatus": "online",
    }


@pytest.mark.asyncio
async def test_config_router_get_config_never_breaks_on_update_check_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config_router, "get_version", lambda: "1.2.3")

    async def _raise_latest(_current: str):
        raise RuntimeError("version checker crashed")

    async def _health_offline():
        return {"status": "offline", "error": "db unreachable"}

    monkeypatch.setattr(config_router, "get_latest_version_cached", _raise_latest)
    monkeypatch.setattr(config_router, "check_database_health", _health_offline)

    payload = await config_router.get_config(request=SimpleNamespace())
    assert payload == {
        "version": "1.2.3",
        "latestVersion": None,
        "hasUpdate": False,
        "dbStatus": "offline",
    }
