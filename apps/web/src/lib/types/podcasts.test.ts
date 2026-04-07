import { describe, expect, it } from "vitest";
import {
  type EpisodeProfile,
  FAILED_EPISODE_STATUSES,
  groupEpisodesByStatus,
  type PodcastEpisode,
  type SpeakerProfile,
  speakerUsageMap,
} from "./podcasts";

function makeEpisode(status: PodcastEpisode["job_status"]): PodcastEpisode {
  return {
    id: String(status ?? "none"),
    name: `episode-${status ?? "none"}`,
    episode_profile: {
      id: "ep",
      name: "episode profile",
      description: "",
      speaker_config: "team-a",
      outline_provider: "provider",
      outline_model: "model",
      transcript_provider: "provider",
      transcript_model: "model",
      default_briefing: "",
      num_segments: 1,
    },
    speaker_profile: {
      id: "sp",
      name: "speaker profile",
      description: "",
      tts_provider: "provider",
      tts_model: "model",
      speakers: [],
    },
    briefing: "",
    job_status: status,
  };
}

describe("podcasts types helpers", () => {
  it("should expose failed statuses used by grouping logic", () => {
    expect(FAILED_EPISODE_STATUSES).toEqual(["failed", "error"]);
  });

  it("should group episodes into running/completed/failed/pending buckets", () => {
    const episodes: PodcastEpisode[] = [
      makeEpisode("running"),
      makeEpisode("processing"),
      makeEpisode("completed"),
      makeEpisode("failed"),
      makeEpisode("error"),
      makeEpisode("pending"),
      makeEpisode("submitted"),
      makeEpisode("unknown"),
      makeEpisode(null),
    ];

    const grouped = groupEpisodesByStatus(episodes);

    expect(grouped.running).toHaveLength(2);
    expect(grouped.completed).toHaveLength(1);
    expect(grouped.failed).toHaveLength(2);
    expect(grouped.pending).toHaveLength(4);
  });

  it("should return empty usage map when profiles are missing", () => {
    expect(speakerUsageMap(undefined, undefined)).toEqual({});
    expect(speakerUsageMap([], undefined)).toEqual({});
    expect(speakerUsageMap(undefined, [])).toEqual({});
  });

  it("should count usage per speaker profile name", () => {
    const speakers: SpeakerProfile[] = [
      {
        id: "s1",
        name: "team-a",
        description: "",
        tts_provider: "provider",
        tts_model: "model",
        speakers: [],
      },
      {
        id: "s2",
        name: "team-b",
        description: "",
        tts_provider: "provider",
        tts_model: "model",
        speakers: [],
      },
    ];
    const episodes: EpisodeProfile[] = [
      {
        id: "e1",
        name: "episode 1",
        description: "",
        speaker_config: "team-a",
        outline_provider: "provider",
        outline_model: "model",
        transcript_provider: "provider",
        transcript_model: "model",
        default_briefing: "",
        num_segments: 1,
      },
      {
        id: "e2",
        name: "episode 2",
        description: "",
        speaker_config: "team-a",
        outline_provider: "provider",
        outline_model: "model",
        transcript_provider: "provider",
        transcript_model: "model",
        default_briefing: "",
        num_segments: 1,
      },
      {
        id: "e3",
        name: "episode 3",
        description: "",
        speaker_config: "team-c",
        outline_provider: "provider",
        outline_model: "model",
        transcript_provider: "provider",
        transcript_model: "model",
        default_briefing: "",
        num_segments: 1,
      },
    ];

    expect(speakerUsageMap(speakers, episodes)).toEqual({
      "team-a": 2,
      "team-b": 0,
    });
  });
});
