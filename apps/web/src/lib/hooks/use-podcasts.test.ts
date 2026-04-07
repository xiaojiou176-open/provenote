import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QUERY_KEYS } from "@/lib/api/query-client";

const hoisted = vi.hoisted(() => ({
  useAppMutationMock: vi.fn(),
  useQueryMock: vi.fn(),
  useQueryClientMock: vi.fn(),
  getApiErrorKeyMock: vi.fn(),
  queryClient: {
    invalidateQueries: vi.fn(),
    refetchQueries: vi.fn(),
  },
  t: {
    common: {
      error: "COMMON_ERROR",
    },
    podcasts: {
      retryStarted: "Retry started",
      retryStartedDesc: "Retry started desc",
      failedToRetry: "Failed to retry",
      episodeDeleted: "Episode deleted",
      episodeDeletedDesc: "Episode deleted desc",
      failedToDeleteEpisode: "Failed to delete episode",
      failedToDeleteProfile: "Failed to delete profile",
      failedToDeleteProfileDesc: "Delete profile fallback",
      speakerDuplicated: "Speaker duplicated",
      speakerDuplicatedDesc: "Speaker duplicated desc",
      failedToDuplicateSpeaker: "Failed to duplicate speaker",
      generationStarted: "Generation started",
      generationStartedDesc: "Generation started for {name}",
      failedToStartGeneration: "Failed to start generation",
      tryAgainMoment: "Try again in a moment",
    },
  },
}));

vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: hoisted.useQueryMock,
    useQueryClient: hoisted.useQueryClientMock,
  };
});

vi.mock("@/lib/hooks/use-app-mutation", () => ({
  useAppMutation: hoisted.useAppMutationMock,
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({ t: hoisted.t }),
}));

vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorKey: hoisted.getApiErrorKeyMock,
}));

vi.mock("@/lib/api/podcasts", () => ({
  podcastsApi: {
    createEpisodeProfile: vi.fn(),
    createSpeakerProfile: vi.fn(),
    updateEpisodeProfile: vi.fn(),
    retryEpisode: vi.fn(),
    deleteEpisode: vi.fn(),
    deleteEpisodeProfile: vi.fn(),
    duplicateSpeakerProfile: vi.fn(),
    duplicateEpisodeProfile: vi.fn(),
    generatePodcast: vi.fn(),
    listEpisodeProfiles: vi.fn(),
    listSpeakerProfiles: vi.fn(),
    updateSpeakerProfile: vi.fn(),
    deleteSpeakerProfile: vi.fn(),
  },
}));

import {
  useCreateEpisodeProfile,
  useCreateSpeakerProfile,
  useDeleteEpisodeProfile,
  useDeletePodcastEpisode,
  useDeleteSpeakerProfile,
  useDuplicateEpisodeProfile,
  useDuplicateSpeakerProfile,
  useEpisodeProfiles,
  useGeneratePodcast,
  usePodcastEpisodes,
  useRetryPodcastEpisode,
  useSpeakerProfiles,
  useUpdateEpisodeProfile,
  useUpdateSpeakerProfile,
} from "./use-podcasts";

type MutationOptions = {
  onSuccess?: (data: unknown, variables: unknown, context: unknown) => unknown;
  errorToast?: (
    error: unknown,
    variables: unknown,
  ) => {
    title?: string;
    description?: string;
    variant?: "default" | "destructive";
  };
  successToast?:
    | {
        title?: string;
        description?: string;
      }
    | ((
        data: unknown,
        variables: unknown,
      ) => {
        title?: string;
        description?: string;
      });
};

const getMutationOptions = (): MutationOptions =>
  hoisted.useAppMutationMock.mock.calls.at(-1)?.[0] as MutationOptions;

describe("usePodcasts mutation abstraction", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.useQueryMock.mockImplementation((options: unknown) => options);
    hoisted.queryClient.refetchQueries.mockResolvedValue(undefined);
    hoisted.useQueryClientMock.mockReturnValue(hoisted.queryClient);
    hoisted.useAppMutationMock.mockImplementation((options: unknown) => options);
    hoisted.getApiErrorKeyMock.mockReturnValue("RESOLVED_ERROR");
  });

  it("keeps retry behavior on refetch flow", async () => {
    const { podcastsApi } = await import("@/lib/api/podcasts");
    renderHook(() => useRetryPodcastEpisode());
    const options = getMutationOptions();

    await options.mutationFn?.("episode-1");
    expect(podcastsApi.retryEpisode).toHaveBeenCalledWith("episode-1");
    await options.onSuccess?.(undefined, "episode-1", undefined);

    expect(hoisted.queryClient.refetchQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.podcastEpisodes,
    });
    expect(hoisted.queryClient.invalidateQueries).not.toHaveBeenCalled();
  });

  it("keeps delete episode profile invalidations and fallback error copy", () => {
    renderHook(() => useDeleteEpisodeProfile());
    const options = getMutationOptions();

    options.onSuccess?.(undefined, "profile-1", undefined);

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(1, {
      queryKey: QUERY_KEYS.episodeProfiles,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(2, {
      queryKey: QUERY_KEYS.podcastEpisodes,
    });

    const errorToast = options.errorToast?.(new Error("boom"), "profile-1");
    expect(hoisted.getApiErrorKeyMock).toHaveBeenCalledWith(
      expect.any(Error),
      hoisted.t.podcasts.failedToDeleteProfileDesc,
    );
    expect(errorToast).toEqual({
      title: hoisted.t.podcasts.failedToDeleteProfile,
      description: "RESOLVED_ERROR",
      variant: "destructive",
    });
  });

  it("keeps duplicate episode profile invalidation and default fallback", () => {
    renderHook(() => useDuplicateEpisodeProfile());
    const options = getMutationOptions();

    options.onSuccess?.(undefined, "profile-1", undefined);

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(1, {
      queryKey: QUERY_KEYS.episodeProfiles,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenNthCalledWith(2, {
      queryKey: QUERY_KEYS.podcastEpisodes,
    });

    const errorToast = options.errorToast?.(new Error("boom"), "profile-1");
    expect(errorToast).toEqual({
      title: hoisted.t.podcasts.failedToDuplicateProfile,
      description: "RESOLVED_ERROR",
      variant: "destructive",
    });
  });

  it("keeps delete episode invalidation and default error fallback", async () => {
    const { podcastsApi } = await import("@/lib/api/podcasts");
    renderHook(() => useDeletePodcastEpisode());
    const options = getMutationOptions();

    await options.mutationFn?.("episode-1");
    expect(podcastsApi.deleteEpisode).toHaveBeenCalledWith("episode-1");
    options.onSuccess?.(undefined, "episode-1", undefined);

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.podcastEpisodes,
    });

    const errorToast = options.errorToast?.(new Error("boom"), "episode-1");
    expect(hoisted.getApiErrorKeyMock).toHaveBeenCalledWith(
      expect.any(Error),
      hoisted.t.common.error,
    );
    expect(errorToast).toEqual({
      title: hoisted.t.podcasts.failedToDeleteEpisode,
      description: "RESOLVED_ERROR",
      variant: "destructive",
    });
  });

  it("keeps episode profile query defaults plus create/update success flows", async () => {
    const { podcastsApi } = await import("@/lib/api/podcasts");

    hoisted.useQueryMock.mockReturnValueOnce({
      data: undefined,
      isLoading: false,
      isError: false,
    });

    const { result } = renderHook(() => useEpisodeProfiles());
    expect(result.current.episodeProfiles).toEqual([]);
    expect(hoisted.useQueryMock).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: QUERY_KEYS.episodeProfiles,
      }),
    );

    renderHook(() => useCreateEpisodeProfile());
    let options = getMutationOptions();
    await options.mutationFn?.({ name: "Interview" });
    expect(podcastsApi.createEpisodeProfile).toHaveBeenCalledWith({ name: "Interview" });
    expect(options.successToast).toEqual({
      title: hoisted.t.podcasts.profileCreated,
      description: hoisted.t.podcasts.profileCreatedDesc,
    });

    options.onSuccess?.(undefined, { name: "Interview" }, undefined);
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.episodeProfiles,
    });
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.podcastEpisodes,
    });

    renderHook(() => useUpdateEpisodeProfile());
    options = getMutationOptions();
    await options.mutationFn?.({
      profileId: "epf-1",
      payload: { name: "Interview 2" },
    });
    expect(podcastsApi.updateEpisodeProfile).toHaveBeenCalledWith("epf-1", {
      name: "Interview 2",
    });
    expect(options.successToast).toEqual({
      title: hoisted.t.podcasts.profileUpdated,
      description: hoisted.t.podcasts.profileUpdatedDesc,
    });

    renderHook(() => useDeleteEpisodeProfile());
    options = getMutationOptions();
    await options.mutationFn?.("epf-1");
    expect(podcastsApi.deleteEpisodeProfile).toHaveBeenCalledWith("epf-1");
  });

  it("keeps duplicate speaker profile scoped invalidation", () => {
    renderHook(() => useDuplicateSpeakerProfile());
    const options = getMutationOptions();

    options.onSuccess?.(undefined, "speaker-1", undefined);

    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledTimes(1);
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.speakerProfiles,
    });
  });

  it("keeps speaker create/update/delete invalidations and speaker usage map", () => {
    hoisted.useQueryMock.mockReturnValueOnce({
      data: [
        { id: "sp-1", name: "Host Pack", speakers: [] },
        { id: "sp-2", name: "Guest Pack", speakers: [] },
      ],
      isLoading: false,
      isError: false,
    });

    const { result } = renderHook(() =>
      useSpeakerProfiles([
        {
          id: "ep-1",
          name: "Interview",
          description: "",
          speaker_config: "Host Pack",
          outline_provider: "google",
          outline_model: "gemini-3.1-pro",
          transcript_provider: "google",
          transcript_model: "gemini-3.1-pro",
          default_briefing: "",
          num_segments: 3,
        },
      ]),
    );

    expect(result.current.usage).toEqual({
      "Guest Pack": 0,
      "Host Pack": 1,
    });

    renderHook(() => useCreateSpeakerProfile());
    let options = getMutationOptions();
    options.onSuccess?.(undefined, { name: "Host Pack" }, undefined);
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.speakerProfiles,
    });

    renderHook(() => useUpdateSpeakerProfile());
    options = getMutationOptions();
    options.onSuccess?.(
      undefined,
      { profileId: "sp-1", payload: { name: "Host Pack" } },
      undefined,
    );
    expect(hoisted.queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.episodeProfiles,
    });

    renderHook(() => useDeleteSpeakerProfile());
    options = getMutationOptions();
    const errorToast = options.errorToast?.(new Error("boom"), "sp-1");
    expect(errorToast).toEqual({
      title: hoisted.t.podcasts.failedToDeleteSpeaker,
      description: "RESOLVED_ERROR",
      variant: "destructive",
    });
  });

  it("exposes speaker/profile mutationFns that call the podcasts api", async () => {
    const { podcastsApi } = await import("@/lib/api/podcasts");

    renderHook(() => useCreateSpeakerProfile());
    let options = getMutationOptions();
    await options.mutationFn?.({ name: "Host Pack" });
    expect(podcastsApi.createSpeakerProfile).toHaveBeenCalledWith({ name: "Host Pack" });

    renderHook(() => useUpdateSpeakerProfile());
    options = getMutationOptions();
    await options.mutationFn?.({ profileId: "sp-1", payload: { name: "Updated Host" } });
    expect(podcastsApi.updateSpeakerProfile).toHaveBeenCalledWith("sp-1", {
      name: "Updated Host",
    });

    renderHook(() => useDeleteSpeakerProfile());
    options = getMutationOptions();
    await options.mutationFn?.("sp-1");
    expect(podcastsApi.deleteSpeakerProfile).toHaveBeenCalledWith("sp-1");

    renderHook(() => useDuplicateEpisodeProfile());
    options = getMutationOptions();
    await options.mutationFn?.("epf-1");
    expect(podcastsApi.duplicateEpisodeProfile).toHaveBeenCalledWith("epf-1");

    renderHook(() => useDuplicateSpeakerProfile());
    options = getMutationOptions();
    await options.mutationFn?.("sp-1");
    expect(podcastsApi.duplicateSpeakerProfile).toHaveBeenCalledWith("sp-1");

    renderHook(() => useGeneratePodcast());
    options = getMutationOptions();
    await options.mutationFn?.({ episode_name: "Daily Brief" });
    expect(podcastsApi.generatePodcast).toHaveBeenCalledWith({ episode_name: "Daily Brief" });
  });

  it("keeps generation toast interpolation and refetch behavior", async () => {
    renderHook(() => useGeneratePodcast());
    const options = getMutationOptions();

    await options.onSuccess?.(undefined, { topic: "x" }, undefined);

    const successToast = options.successToast as (
      data: { episode_name: string },
      variables: unknown,
    ) => { title?: string; description?: string };

    expect(successToast({ episode_name: "Daily Brief" }, {})).toEqual({
      title: hoisted.t.podcasts.generationStarted,
      description: "Generation started for Daily Brief",
    });
    expect(hoisted.queryClient.refetchQueries).toHaveBeenCalledWith({
      queryKey: QUERY_KEYS.podcastEpisodes,
    });
  });

  it("keeps generation error fallback copy", () => {
    renderHook(() => useGeneratePodcast());
    const options = getMutationOptions();

    const errorToast = options.errorToast?.(new Error("boom"), { topic: "x" });
    expect(hoisted.getApiErrorKeyMock).toHaveBeenCalledWith(
      expect.any(Error),
      hoisted.t.podcasts.tryAgainMoment,
    );
    expect(errorToast).toEqual({
      title: hoisted.t.podcasts.failedToStartGeneration,
      description: "RESOLVED_ERROR",
      variant: "destructive",
    });
  });

  it("keeps podcast episodes grouping and active auto-refresh interval", () => {
    const runningEpisode = {
      id: "ep-running",
      name: "Running",
      episode_profile: {
        id: "p1",
        name: "P1",
        speaker_config: "Host",
        description: "",
        outline_provider: "google",
        outline_model: "m1",
        transcript_provider: "google",
        transcript_model: "m2",
        default_briefing: "",
        num_segments: 2,
      },
      speaker_profile: {
        id: "s1",
        name: "S1",
        description: "",
        tts_provider: "openai",
        tts_model: "tts",
        speakers: [],
      },
      briefing: "",
      job_status: "running",
    };
    const completedEpisode = {
      id: "ep-done",
      name: "Done",
      episode_profile: {
        id: "p2",
        name: "P2",
        speaker_config: "Guest",
        description: "",
        outline_provider: "google",
        outline_model: "m1",
        transcript_provider: "google",
        transcript_model: "m2",
        default_briefing: "",
        num_segments: 2,
      },
      speaker_profile: {
        id: "s2",
        name: "S2",
        description: "",
        tts_provider: "openai",
        tts_model: "tts",
        speakers: [],
      },
      briefing: "",
      job_status: "completed",
    };

    hoisted.useQueryMock.mockReturnValueOnce({
      data: [runningEpisode, completedEpisode],
      isLoading: false,
      isError: false,
    });

    const { result } = renderHook(() => usePodcastEpisodes());
    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      refetchInterval: (input: { state: { data?: unknown } }) => number | false;
    };

    expect(result.current.statusCounts).toEqual({
      total: 2,
      running: 1,
      completed: 1,
      failed: 0,
      pending: 0,
    });
    expect(result.current.hasActiveEpisodes).toBe(true);
    expect(queryOptions.refetchInterval({ state: { data: [runningEpisode] } })).toBe(15000);
  });

  it("keeps auto-refresh disabled when option is false", () => {
    hoisted.useQueryMock.mockReturnValueOnce({
      data: [],
      isLoading: false,
      isError: false,
    });

    renderHook(() => usePodcastEpisodes({ autoRefresh: false }));
    const queryOptions = hoisted.useQueryMock.mock.calls[0][0] as {
      refetchInterval: (input: { state: { data?: unknown } }) => number | false;
    };

    expect(queryOptions.refetchInterval({ state: { data: [{ job_status: "running" }] } })).toBe(
      false,
    );
  });
});
