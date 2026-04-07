import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  apiClientMock: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  getApiUrlMock: vi.fn(),
}));

vi.mock("./client", () => ({
  default: hoisted.apiClientMock,
}));

vi.mock("@/lib/config", () => ({
  getApiUrl: hoisted.getApiUrlMock,
}));

import { podcastsApi, resolvePodcastAssetUrl } from "./podcasts";

describe("podcastsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.getApiUrlMock.mockResolvedValue("http://localhost:8000");
  });

  it("resolves podcast asset URLs for empty, absolute, rooted, and relative paths", async () => {
    const empty = await resolvePodcastAssetUrl(undefined);
    const absolute = await resolvePodcastAssetUrl("https://cdn.example.com/audio.mp3");
    const rooted = await resolvePodcastAssetUrl("/media/podcast.mp3");
    const relative = await resolvePodcastAssetUrl("media/podcast.mp3");

    expect(empty).toBeUndefined();
    expect(absolute).toBe("https://cdn.example.com/audio.mp3");
    expect(rooted).toBe("http://localhost:8000/media/podcast.mp3");
    expect(relative).toBe("http://localhost:8000/media/podcast.mp3");
  });

  it("maps episodes and profile endpoints", async () => {
    hoisted.apiClientMock.get
      .mockResolvedValueOnce({ data: [{ id: "ep-1" }] })
      .mockResolvedValueOnce({ data: [{ id: "profile-1" }] })
      .mockResolvedValueOnce({ data: [{ id: "speaker-1" }] });
    hoisted.apiClientMock.post
      .mockResolvedValueOnce({ data: { job_id: "job-1", message: "retry queued" } })
      .mockResolvedValueOnce({ data: { id: "profile-2" } })
      .mockResolvedValueOnce({ data: { id: "profile-3" } })
      .mockResolvedValueOnce({ data: { id: "speaker-2" } })
      .mockResolvedValueOnce({ data: { id: "speaker-3" } })
      .mockResolvedValueOnce({ data: { job_id: "job-2", status: "queued" } });
    hoisted.apiClientMock.put
      .mockResolvedValueOnce({ data: { id: "profile-1", profile_name: "Updated" } })
      .mockResolvedValueOnce({ data: { id: "speaker-1", profile_name: "Updated speaker" } });
    hoisted.apiClientMock.delete.mockResolvedValue({ data: undefined });

    const episodes = await podcastsApi.listEpisodes();
    await podcastsApi.deleteEpisode("ep-1");
    const retry = await podcastsApi.retryEpisode("ep-1");

    const episodeProfiles = await podcastsApi.listEpisodeProfiles();
    const createdEpisodeProfile = await podcastsApi.createEpisodeProfile({
      profile_name: "Interview",
      speaker_profile_id: "speaker-1",
      briefing_model_provider: "google",
      briefing_model_name: "gemini-3.1-pro",
      script_model_provider: "google",
      script_model_name: "gemini-3.1-pro",
      segments: 5,
      default_briefing: "Focus on practical takeaways",
      description: "Interview format",
    });
    const updatedEpisodeProfile = await podcastsApi.updateEpisodeProfile("profile-1", {
      profile_name: "Updated",
      speaker_profile_id: "speaker-1",
      briefing_model_provider: "google",
      briefing_model_name: "gemini-3.1-pro",
      script_model_provider: "google",
      script_model_name: "gemini-3.1-pro",
      segments: 5,
      default_briefing: "Updated briefing",
      description: "Updated description",
    });
    await podcastsApi.deleteEpisodeProfile("profile-1");
    const duplicatedEpisodeProfile = await podcastsApi.duplicateEpisodeProfile("profile-1");

    const speakerProfiles = await podcastsApi.listSpeakerProfiles();
    const createdSpeakerProfile = await podcastsApi.createSpeakerProfile({
      profile_name: "Host",
      model: "voice-1",
      provider: "openai",
      speakers: [{ voice_id: "alloy", backstory: "Host", personality: "Warm" }],
      description: "Main host voice",
    });
    const updatedSpeakerProfile = await podcastsApi.updateSpeakerProfile("speaker-1", {
      profile_name: "Updated speaker",
      model: "voice-2",
      provider: "openai",
      speakers: [{ voice_id: "verse", backstory: "Guest", personality: "Calm" }],
      description: "Updated voice profile",
    });
    await podcastsApi.deleteSpeakerProfile("speaker-1");
    const duplicatedSpeakerProfile = await podcastsApi.duplicateSpeakerProfile("speaker-1");

    const generation = await podcastsApi.generatePodcast({
      draft_id: "draft-1",
      notebook_id: "nb-1",
      source_ids: ["src-1"],
      note_ids: ["note-1"],
      summary_mode: "summary",
      episode_profile_id: "profile-1",
      episode_name: "Weekly Brief",
      additional_instructions: "Keep it concise",
    });

    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(1, "/podcasts/episodes");
    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/podcasts/episodes/ep-1");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(1, "/podcasts/episodes/ep-1/retry");

    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(2, "/episode-profiles");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(2, "/episode-profiles", {
      profile_name: "Interview",
      speaker_profile_id: "speaker-1",
      briefing_model_provider: "google",
      briefing_model_name: "gemini-3.1-pro",
      script_model_provider: "google",
      script_model_name: "gemini-3.1-pro",
      segments: 5,
      default_briefing: "Focus on practical takeaways",
      description: "Interview format",
    });
    expect(hoisted.apiClientMock.put).toHaveBeenNthCalledWith(
      1,
      "/episode-profiles/profile-1",
      expect.objectContaining({ profile_name: "Updated" }),
    );
    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/episode-profiles/profile-1");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(
      3,
      "/episode-profiles/profile-1/duplicate",
    );

    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(3, "/speaker-profiles");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(4, "/speaker-profiles", {
      profile_name: "Host",
      model: "voice-1",
      provider: "openai",
      speakers: [{ voice_id: "alloy", backstory: "Host", personality: "Warm" }],
      description: "Main host voice",
    });
    expect(hoisted.apiClientMock.put).toHaveBeenNthCalledWith(
      2,
      "/speaker-profiles/speaker-1",
      expect.objectContaining({ profile_name: "Updated speaker" }),
    );
    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/speaker-profiles/speaker-1");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(
      5,
      "/speaker-profiles/speaker-1/duplicate",
    );

    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(6, "/podcasts/generate", {
      draft_id: "draft-1",
      notebook_id: "nb-1",
      source_ids: ["src-1"],
      note_ids: ["note-1"],
      summary_mode: "summary",
      episode_profile_id: "profile-1",
      episode_name: "Weekly Brief",
      additional_instructions: "Keep it concise",
    });

    expect(episodes).toEqual([{ id: "ep-1" }]);
    expect(retry.job_id).toBe("job-1");
    expect(episodeProfiles).toEqual([{ id: "profile-1" }]);
    expect(createdEpisodeProfile.id).toBe("profile-2");
    expect(updatedEpisodeProfile.id).toBe("profile-1");
    expect(duplicatedEpisodeProfile.id).toBe("profile-3");
    expect(speakerProfiles).toEqual([{ id: "speaker-1" }]);
    expect(createdSpeakerProfile.id).toBe("speaker-2");
    expect(updatedSpeakerProfile.id).toBe("speaker-1");
    expect(duplicatedSpeakerProfile.id).toBe("speaker-3");
    expect(generation.job_id).toBe("job-2");
  });
});
