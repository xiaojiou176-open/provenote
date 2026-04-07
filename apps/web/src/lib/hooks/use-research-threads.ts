import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { researchThreadsApi } from "@/lib/api/research-threads";
import { useToast } from "@/lib/hooks/use-toast";
import { useTranslation } from "@/lib/hooks/use-translation";
import type {
  AppendResearchThreadEntryRequest,
  CreateResearchThreadRequest,
} from "@/lib/types/api";
import { getApiErrorMessage } from "@/lib/utils/error-handler";

export function useNotebookResearchThreads(notebookId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.notebookResearchThreads(notebookId),
    queryFn: () => researchThreadsApi.list(notebookId),
    enabled: !!notebookId,
  });
}

export function useCreateResearchThread() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { t } = useTranslation();

  return useMutation({
    mutationFn: ({
      notebookId,
      payload,
    }: {
      notebookId: string;
      payload: CreateResearchThreadRequest;
    }) => researchThreadsApi.create(notebookId, payload),
    onSuccess: (thread) => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.notebookResearchThreads(thread.notebook_id),
      });
      toast({
        title: t.common.success,
        description: t.notebooks.researchThreadSaved,
      });
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: getApiErrorMessage(error, (key) => t(key), t.common.error),
        variant: "destructive",
      });
    },
  });
}

export function useCreateDraftFromResearchThread(notebookId: string) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { t } = useTranslation();

  return useMutation({
    mutationFn: (threadId: string) => researchThreadsApi.createDraft(threadId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebookDrafts(notebookId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebookResearchThreads(notebookId) });
      toast({
        title: t.common.success,
        description: t.notebooks.researchThreadDraftCreated,
      });
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: getApiErrorMessage(error, (key) => t(key), t.common.error),
        variant: "destructive",
      });
    },
  });
}

export function useAppendResearchThreadEntry(notebookId: string) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { t } = useTranslation();

  return useMutation({
    mutationFn: ({
      threadId,
      payload,
    }: {
      threadId: string;
      payload: AppendResearchThreadEntryRequest;
    }) => researchThreadsApi.append(threadId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebookResearchThreads(notebookId) });
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: getApiErrorMessage(error, (key) => t(key), t.common.error),
        variant: "destructive",
      });
    },
  });
}
