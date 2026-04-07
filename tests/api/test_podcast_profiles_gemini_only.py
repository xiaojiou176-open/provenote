def test_create_episode_profile_rejects_non_google_provider(api_client) -> None:
    payload = {
        "name": "test-profile",
        "description": "test",
        "speaker_config": "tech_experts",
        "outline_provider": "anthropic",
        "outline_model": "claude-3-5-haiku-latest",
        "transcript_provider": "google",
        "transcript_model": "gemini-2.5-flash",
        "default_briefing": "brief",
        "num_segments": 5,
    }

    response = api_client.post("/api/episode-profiles", json=payload)

    assert response.status_code == 400
    assert "outline_provider" in response.json()["detail"]


def test_create_speaker_profile_rejects_non_google_provider(api_client) -> None:
    payload = {
        "name": "test-speaker",
        "description": "test",
        "tts_provider": "azure",
        "tts_model": "azure-neural-tts",
        "speakers": [
            {
                "name": "Host",
                "voice_id": "voice123",
                "backstory": "A friendly host",
                "personality": "clear and concise",
            }
        ],
    }

    response = api_client.post("/api/speaker-profiles", json=payload)

    assert response.status_code == 400
    assert "tts_provider" in response.json()["detail"]
