import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

import {
  type EpisodeProfileInput,
  podcastsApi,
  type SpeakerProfileInput,
} from "@/lib/api/podcasts";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { useAppMutation } from "@/lib/hooks/use-app-mutation";
import { useTranslation } from "@/lib/hooks/use-translation";
import {
  ACTIVE_EPISODE_STATUSES,
  type EpisodeProfile,
  type EpisodeStatusGroups,
  groupEpisodesByStatus,
  type PodcastEpisode,
  type PodcastGenerationRequest,
  speakerUsageMap,
} from "@/lib/types/podcasts";
import { getApiErrorKey } from "@/lib/utils/error-handler";

interface EpisodeStatusCounts {
  total: number;
  running: number;
  completed: number;
  failed: number;
  pending: number;
}

type PodcastMutationToast = {
  title?: string;
  description?: string;
};

type PodcastMutationToastFactory<TData, TVariables> =
  | PodcastMutationToast
  | ((data: TData, variables: TVariables) => PodcastMutationToast | null | undefined);

interface PodcastMutationOptions<TData, TVariables> {
  mutationFn: (variables: TVariables) => Promise<TData>;
  successToast?: PodcastMutationToastFactory<TData, TVariables>;
  errorTitle: string;
  errorFallback: string;
  invalidateQueryKeys?: ReadonlyArray<readonly unknown[]>;
  refetchQueryKeys?: ReadonlyArray<readonly unknown[]>;
}

function hasActiveEpisodes(episodes: PodcastEpisode[]) {
  return episodes.some((episode) => {
    const status = episode.job_status ?? "unknown";
    return ACTIVE_EPISODE_STATUSES.includes(status);
  });
}

function usePodcastMutation<TData, TVariables = void>({
  mutationFn,
  successToast,
  errorTitle,
  errorFallback,
  invalidateQueryKeys = [],
  refetchQueryKeys = [],
}: PodcastMutationOptions<TData, TVariables>) {
  const queryClient = useQueryClient();

  const runQueryUpdates = () => {
    if (refetchQueryKeys.length > 0) {
      return Promise.all(
        refetchQueryKeys.map((queryKey) => queryClient.refetchQueries({ queryKey })),
      ).then(() => {
        invalidateQueryKeys.forEach((queryKey) => {
          queryClient.invalidateQueries({ queryKey });
        });
      });
    }

    invalidateQueryKeys.forEach((queryKey) => {
      queryClient.invalidateQueries({ queryKey });
    });
    return undefined;
  };

  return useAppMutation({
    mutationFn,
    onSuccess: () => runQueryUpdates(),
    successToast,
    errorToast: (error) => ({
      title: errorTitle,
      description: getApiErrorKey(error, errorFallback),
      variant: "destructive",
    }),
  });
}

export function usePodcastEpisodes(options?: { autoRefresh?: boolean }) {
  const { autoRefresh = true } = options ?? {};

  const query = useQuery({
    queryKey: QUERY_KEYS.podcastEpisodes,
    queryFn: podcastsApi.listEpisodes,
    refetchInterval: (current) => {
      if (!autoRefresh) {
        return false;
      }

      const data = current.state.data as PodcastEpisode[] | undefined;
      if (!data || data.length === 0) {
        return false;
      }

      return hasActiveEpisodes(data) ? 15_000 : false;
    },
  });

  const episodes = useMemo(() => query.data ?? [], [query.data]);

  const statusGroups = useMemo<EpisodeStatusGroups>(
    () => groupEpisodesByStatus(episodes),
    [episodes],
  );

  const statusCounts = useMemo<EpisodeStatusCounts>(
    () => ({
      total: episodes.length,
      running: statusGroups.running.length,
      completed: statusGroups.completed.length,
      failed: statusGroups.failed.length,
      pending: statusGroups.pending.length,
    }),
    [episodes.length, statusGroups],
  );

  const active = useMemo(() => hasActiveEpisodes(episodes), [episodes]);

  return {
    ...query,
    episodes,
    statusGroups,
    statusCounts,
    hasActiveEpisodes: active,
  };
}

export function useRetryPodcastEpisode() {
  const { t } = useTranslation();

  return usePodcastMutation({
    mutationFn: (episodeId: string) => podcastsApi.retryEpisode(episodeId),
    refetchQueryKeys: [QUERY_KEYS.podcastEpisodes],
    successToast: {
      title: t.podcasts.retryStarted,
      description: t.podcasts.retryStartedDesc,
    },
    errorTitle: t.podcasts.failedToRetry,
    errorFallback: t.common.error,
  });
}

export function useDeletePodcastEpisode() {
  const { t } = useTranslation();

  return usePodcastMutation({
    mutationFn: (episodeId: string) => podcastsApi.deleteEpisode(episodeId),
    invalidateQueryKeys: [QUERY_KEYS.podcastEpisodes],
    successToast: {
      title: t.podcasts.episodeDeleted,
      description: t.podcasts.episodeDeletedDesc,
    },
    errorTitle: t.podcasts.failedToDeleteEpisode,
    errorFallback: t.common.error,
  });
}

export function useEpisodeProfiles() {
  const query = useQuery({
    queryKey: QUERY_KEYS.episodeProfiles,
    queryFn: podcastsApi.listEpisodeProfiles,
  });

  return {
    ...query,
    episodeProfiles: query.data ?? [],
  };
}

export function useCreateEpisodeProfile() {
  const { t } = useTranslation();

  return usePodcastMutation({
    mutationFn: (payload: EpisodeProfileInput) => podcastsApi.createEpisodeProfile(payload),
    invalidateQueryKeys: [QUERY_KEYS.episodeProfiles, QUERY_KEYS.podcastEpisodes],
    successToast: {
      title: t.podcasts.profileCreated,
      description: t.podcasts.profileCreatedDesc,
    },
    errorTitle: t.podcasts.failedToCreateProfile,
    errorFallback: t.common.error,
  });
}

export function useUpdateEpisodeProfile() {
  const { t } = useTranslation();

  return usePodcastMutation({
    mutationFn: ({ profileId, payload }: { profileId: string; payload: EpisodeProfileInput }) =>
      podcastsApi.updateEpisodeProfile(profileId, payload),
    invalidateQueryKeys: [QUERY_KEYS.episodeProfiles, QUERY_KEYS.podcastEpisodes],
    successToast: {
      title: t.podcasts.profileUpdated,
      description: t.podcasts.profileUpdatedDesc,
    },
    errorTitle: t.podcasts.failedToUpdateProfile,
    errorFallback: t.common.error,
  });
}

export function useDeleteEpisodeProfile() {
  const { t } = useTranslation();

  return usePodcastMutation({
    mutationFn: (profileId: string) => podcastsApi.deleteEpisodeProfile(profileId),
    invalidateQueryKeys: [QUERY_KEYS.episodeProfiles, QUERY_KEYS.podcastEpisodes],
    successToast: {
      title: t.podcasts.profileDeleted,
      description: t.podcasts.profileDeletedDesc,
    },
    errorTitle: t.podcasts.failedToDeleteProfile,
    errorFallback: t.podcasts.failedToDeleteProfileDesc,
  });
}

export function useDuplicateEpisodeProfile() {
  const { t } = useTranslation();

  return usePodcastMutation({
    mutationFn: (profileId: string) => podcastsApi.duplicateEpisodeProfile(profileId),
    invalidateQueryKeys: [QUERY_KEYS.episodeProfiles, QUERY_KEYS.podcastEpisodes],
    successToast: {
      title: t.podcasts.profileDuplicated,
      description: t.podcasts.profileDuplicatedDesc,
    },
    errorTitle: t.podcasts.failedToDuplicateProfile,
    errorFallback: t.common.error,
  });
}

export function useSpeakerProfiles(episodeProfiles?: EpisodeProfile[]) {
  const query = useQuery({
    queryKey: QUERY_KEYS.speakerProfiles,
    queryFn: podcastsApi.listSpeakerProfiles,
  });

  const speakerProfiles = useMemo(() => query.data ?? [], [query.data]);

  const usage = useMemo(
    () => speakerUsageMap(speakerProfiles, episodeProfiles),
    [speakerProfiles, episodeProfiles],
  );

  return {
    ...query,
    speakerProfiles,
    usage,
  };
}

export function useCreateSpeakerProfile() {
  const { t } = useTranslation();

  return usePodcastMutation({
    mutationFn: (payload: SpeakerProfileInput) => podcastsApi.createSpeakerProfile(payload),
    invalidateQueryKeys: [
      QUERY_KEYS.speakerProfiles,
      QUERY_KEYS.episodeProfiles,
      QUERY_KEYS.podcastEpisodes,
    ],
    successToast: {
      title: t.podcasts.speakerCreated,
      description: t.podcasts.speakerCreatedDesc,
    },
    errorTitle: t.podcasts.failedToCreateSpeaker,
    errorFallback: t.common.error,
  });
}

export function useUpdateSpeakerProfile() {
  const { t } = useTranslation();

  return usePodcastMutation({
    mutationFn: ({ profileId, payload }: { profileId: string; payload: SpeakerProfileInput }) =>
      podcastsApi.updateSpeakerProfile(profileId, payload),
    invalidateQueryKeys: [
      QUERY_KEYS.speakerProfiles,
      QUERY_KEYS.episodeProfiles,
      QUERY_KEYS.podcastEpisodes,
    ],
    successToast: {
      title: t.podcasts.speakerUpdated,
      description: t.podcasts.speakerUpdatedDesc,
    },
    errorTitle: t.podcasts.failedToUpdateSpeaker,
    errorFallback: t.common.error,
  });
}

export function useDeleteSpeakerProfile() {
  const { t } = useTranslation();

  return usePodcastMutation({
    mutationFn: (profileId: string) => podcastsApi.deleteSpeakerProfile(profileId),
    invalidateQueryKeys: [
      QUERY_KEYS.speakerProfiles,
      QUERY_KEYS.episodeProfiles,
      QUERY_KEYS.podcastEpisodes,
    ],
    successToast: {
      title: t.podcasts.speakerDeleted,
      description: t.podcasts.speakerDeletedDesc,
    },
    errorTitle: t.podcasts.failedToDeleteSpeaker,
    errorFallback: t.podcasts.failedToDeleteSpeakerDesc,
  });
}

export function useDuplicateSpeakerProfile() {
  const { t } = useTranslation();

  return usePodcastMutation({
    mutationFn: (profileId: string) => podcastsApi.duplicateSpeakerProfile(profileId),
    invalidateQueryKeys: [QUERY_KEYS.speakerProfiles],
    successToast: {
      title: t.podcasts.speakerDuplicated,
      description: t.podcasts.speakerDuplicatedDesc,
    },
    errorTitle: t.podcasts.failedToDuplicateSpeaker,
    errorFallback: t.common.error,
  });
}

export function useGeneratePodcast() {
  const { t } = useTranslation();

  return usePodcastMutation({
    mutationFn: (payload: PodcastGenerationRequest) => podcastsApi.generatePodcast(payload),
    refetchQueryKeys: [QUERY_KEYS.podcastEpisodes],
    successToast: (response) => ({
      title: t.podcasts.generationStarted,
      description: t.podcasts.generationStartedDesc.replace("{name}", response.episode_name),
    }),
    errorTitle: t.podcasts.failedToStartGeneration,
    errorFallback: t.podcasts.tryAgainMoment,
  });
}
