import { useQuery, useQueryClient } from "@tanstack/react-query";
import { insightsApi } from "@/lib/api/insights";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { useAppMutation } from "@/lib/hooks/use-app-mutation";
import { useTranslation } from "@/lib/hooks/use-translation";
import { getApiErrorKey } from "@/lib/utils/error-handler";

export function useInsight(id: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["insights", id],
    queryFn: () => insightsApi.get(id),
    enabled: options?.enabled !== false && !!id,
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useSaveInsightAsNote() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: ({ insightId, notebookId }: { insightId: string; notebookId?: string }) =>
      insightsApi.saveAsNote(insightId, { notebook_id: notebookId }),
    onSuccess: (_, variables) => {
      if (variables.notebookId) {
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.notes(variables.notebookId),
        });
      }
    },
    successToast: {
      title: t.common.success,
      description: t.sources.saveInsightAsNoteSuccess,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorKey(error, t.sources.saveInsightAsNoteFailed),
      variant: "destructive",
    }),
  });
}
