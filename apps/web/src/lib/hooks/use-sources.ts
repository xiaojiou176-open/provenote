import { useInfiniteQuery, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { sourcesApi } from "@/lib/api/sources";
import { useAppMutation } from "@/lib/hooks/use-app-mutation";
import { useTranslation } from "@/lib/hooks/use-translation";
import type {
  CreateSourceRequest,
  SourceListResponse,
  SourceResponse,
  SourceStatusResponse,
  UpdateSourceRequest,
} from "@/lib/types/api";
import { getApiErrorMessage } from "@/lib/utils/error-handler";

const NOTEBOOK_SOURCES_PAGE_SIZE = 30;

function invalidateSourceCaches(
  queryClient: ReturnType<typeof useQueryClient>,
  notebookId?: string,
) {
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sources(), refetchType: "active" });
  if (notebookId) {
    queryClient.invalidateQueries({
      queryKey: QUERY_KEYS.sources(notebookId),
      refetchType: "active",
    });
    queryClient.invalidateQueries({
      queryKey: QUERY_KEYS.sourcesInfinite(notebookId),
      refetchType: "active",
    });
  }
}

export function useSources(notebookId?: string) {
  return useQuery({
    queryKey: QUERY_KEYS.sources(notebookId),
    queryFn: () => sourcesApi.list({ notebook_id: notebookId }),
    enabled: !!notebookId,
    staleTime: 5 * 1000, // 5 seconds - more responsive for real-time source updates
    refetchOnWindowFocus: true, // Refetch when user comes back to the tab
  });
}

/**
 * Hook for fetching notebook sources with infinite scroll pagination.
 * Returns flattened sources array and pagination controls.
 */
export function useNotebookSources(notebookId: string) {
  const queryClient = useQueryClient();

  const query = useInfiniteQuery({
    queryKey: QUERY_KEYS.sourcesInfinite(notebookId),
    queryFn: async ({ pageParam = 0 }) => {
      const data = await sourcesApi.list({
        notebook_id: notebookId,
        limit: NOTEBOOK_SOURCES_PAGE_SIZE,
        offset: pageParam,
        sort_by: "updated",
        sort_order: "desc",
      });
      return {
        sources: data,
        nextOffset:
          data.length === NOTEBOOK_SOURCES_PAGE_SIZE ? pageParam + data.length : undefined,
      };
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextOffset,
    enabled: !!notebookId,
    staleTime: 5 * 1000,
    refetchOnWindowFocus: true,
  });

  // Flatten all pages into a single array (memoized to prevent infinite re-renders)
  const sources: SourceListResponse[] = useMemo(
    () => query.data?.pages.flatMap((page) => page.sources) ?? [],
    [query.data?.pages],
  );

  // Refetch function that resets to first page
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sourcesInfinite(notebookId) });
  }, [queryClient, notebookId]);

  return {
    sources,
    isLoading: query.isLoading,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: query.hasNextPage,
    fetchNextPage: query.fetchNextPage,
    refetch,
    error: query.error,
  };
}

export function useSource(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.source(id),
    queryFn: () => sourcesApi.get(id),
    enabled: !!id,
    staleTime: 30 * 1000, // 30 seconds - shorter stale time for more responsive updates
    refetchOnWindowFocus: true, // Refetch when user comes back to the tab
  });
}

export function useCreateSource() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: (data: CreateSourceRequest) => sourcesApi.create(data),
    onSuccess: (_result: SourceResponse, variables) => {
      const notebookId = variables.notebook_id ?? variables.notebooks?.[0];
      invalidateSourceCaches(queryClient, notebookId);
    },
    successToast: (_, variables) => {
      if (variables.async_processing) {
        return {
          title: t.sources.sourceQueued,
          description: t.sources.sourceQueuedDesc,
        };
      }
      return {
        title: t.common.success,
        description: t.sources.sourceAddedSuccess,
      };
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorMessage(error, (key) => t(key), t.sources.failedToAddSource),
      variant: "destructive",
    }),
  });
}

export function useUpdateSource() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSourceRequest }) =>
      sourcesApi.update(id, data),
    onSuccess: (_, { id }) => {
      invalidateSourceCaches(queryClient);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.source(id) });
    },
    successToast: {
      title: t.common.success,
      description: t.sources.sourceUpdatedSuccess,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorMessage(error, (key) => t(key), t.sources.failedToUpdateSource),
      variant: "destructive",
    }),
  });
}

export function useDeleteSource() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: (id: string) => sourcesApi.delete(id),
    onSuccess: (_, id) => {
      invalidateSourceCaches(queryClient);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.source(id) });
    },
    successToast: {
      title: t.common.success,
      description: t.sources.sourceDeletedSuccess,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorMessage(error, (key) => t(key), t.sources.failedToDeleteSource),
      variant: "destructive",
    }),
  });
}

export function useFileUpload() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: ({ file, notebookId }: { file: File; notebookId: string }) =>
      sourcesApi.upload(file, notebookId),
    onSuccess: (_, variables) => {
      invalidateSourceCaches(queryClient, variables.notebookId);
    },
    successToast: {
      title: t.common.success,
      description: t.sources.fileUploadedSuccess,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorMessage(error, (key) => t(key), t.sources.failedToUploadFile),
      variant: "destructive",
    }),
  });
}

export function useSourceStatus(sourceId: string, enabled = true) {
  return useQuery({
    queryKey: ["sources", sourceId, "status"],
    queryFn: () => sourcesApi.status(sourceId),
    enabled: !!sourceId && enabled,
    refetchInterval: (query) => {
      // Auto-refresh every 2 seconds if processing
      // The query.state.data contains the SourceStatusResponse
      const data = query.state.data as SourceStatusResponse | undefined;
      if (data?.status === "running" || data?.status === "queued" || data?.status === "new") {
        return 2000;
      }
      // No auto-refresh if completed, failed, or unknown
      return false;
    },
    staleTime: 0, // Always consider status data stale for real-time updates
    retry: (failureCount, error) => {
      // Don't retry on 404 (source not found)
      const axiosError = error as { response?: { status?: number } };
      if (axiosError?.response?.status === 404) {
        return false;
      }
      return failureCount < 3;
    },
  });
}

export function useRetrySource() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: (sourceId: string) => sourcesApi.retry(sourceId),
    onSuccess: (_result, sourceId) => {
      // Invalidate status query to refetch latest status
      queryClient.invalidateQueries({
        queryKey: ["sources", sourceId, "status"],
      });
      invalidateSourceCaches(queryClient);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.source(sourceId) });
    },
    successToast: {
      title: t.sources.sourceRequeued,
      description: t.sources.sourceRequeuedDesc,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorMessage(error, (key) => t(key), t.sources.failedToRetry),
      variant: "destructive",
    }),
  });
}

export function useSourceProcessingReport(sourceId: string, enabled = true) {
  return useQuery({
    queryKey: ["sources", sourceId, "processing-report"],
    queryFn: () => sourcesApi.processingReport(sourceId),
    enabled: !!sourceId && enabled,
    staleTime: 0,
  });
}

export function useReprocessSource() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: (sourceId: string) => sourcesApi.reprocess(sourceId),
    onSuccess: (_result, sourceId) => {
      queryClient.invalidateQueries({
        queryKey: ["sources", sourceId, "status"],
      });
      queryClient.invalidateQueries({
        queryKey: ["sources", sourceId, "processing-report"],
      });
      invalidateSourceCaches(queryClient);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.source(sourceId) });
    },
    successToast: {
      title: t.sources.sourceRequeued,
      description: t.sources.sourceRequeuedDesc,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorMessage(error, (key) => t(key), t.sources.failedToRetry),
      variant: "destructive",
    }),
  });
}

export function useAddSourcesToNotebook() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: async ({ notebookId, sourceIds }: { notebookId: string; sourceIds: string[] }) => {
      const { notebooksApi } = await import("@/lib/api/notebooks");

      // Use Promise.allSettled to handle partial failures gracefully
      const results = await Promise.allSettled(
        sourceIds.map((sourceId) => notebooksApi.addSource(notebookId, sourceId)),
      );

      // Count successes and failures
      const successes = results.filter((r) => r.status === "fulfilled").length;
      const failures = results.filter((r) => r.status === "rejected").length;

      return { successes, failures, total: sourceIds.length };
    },
    onSuccess: (_result, { notebookId }) => {
      invalidateSourceCaches(queryClient, notebookId);
    },
    successToast: (result) => {
      // Show appropriate toast based on results
      if (result.failures === 0) {
        return {
          title: t.common.success,
          description: t.sources.sourcesAddedToNotebook.replace(
            "{count}",
            result.successes.toString(),
          ),
        };
      }
      if (result.successes === 0) {
        return {
          title: t.common.error,
          description: t.sources.failedToAddSourcesToNotebook,
          variant: "destructive",
        };
      }
      return {
        title: t.common.success,
        description: t.sources.partialAddSuccess
          .replace("{success}", result.successes.toString())
          .replace("{failed}", result.failures.toString()),
        variant: "default",
      };
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorMessage(
        error,
        (key) => t(key),
        t.sources.failedToAddSourcesToNotebook,
      ),
      variant: "destructive",
    }),
  });
}

export function useRemoveSourceFromNotebook() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: async ({ notebookId, sourceId }: { notebookId: string; sourceId: string }) => {
      // This will call the API we created
      const { notebooksApi } = await import("@/lib/api/notebooks");
      return notebooksApi.removeSource(notebookId, sourceId);
    },
    onSuccess: (_, { notebookId, sourceId }) => {
      invalidateSourceCaches(queryClient, notebookId);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.source(sourceId) });
    },
    successToast: {
      title: t.common.success,
      description: t.sources.sourceRemovedFromNotebook,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorMessage(
        error,
        (key) => t(key),
        t.sources.failedToRemoveSourceFromNotebook,
      ),
      variant: "destructive",
    }),
  });
}
