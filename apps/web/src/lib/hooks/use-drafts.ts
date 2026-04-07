import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { draftsApi } from "@/lib/api/drafts";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { useToast } from "@/lib/hooks/use-toast";
import { useTranslation } from "@/lib/hooks/use-translation";
import type {
  CreateDraftRequest,
  DraftResponse,
  DraftStatus,
  RerunDraftRequest,
} from "@/lib/types/api";
import { getApiErrorMessage } from "@/lib/utils/error-handler";

const ACTIVE_DRAFT_STATUSES: ReadonlySet<DraftStatus> = new Set(["queued", "running"]);

function hasActiveStatus(status?: DraftStatus) {
  return status ? ACTIVE_DRAFT_STATUSES.has(status) : false;
}

export function useNotebookDrafts(notebookId: string) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { t } = useTranslation();

  const draftsQuery = useQuery({
    queryKey: QUERY_KEYS.notebookDrafts(notebookId),
    queryFn: () => draftsApi.list(notebookId),
    enabled: !!notebookId,
    staleTime: 0,
    refetchInterval: (query) => {
      const drafts = (query.state.data as DraftResponse[] | undefined) ?? [];
      return drafts.some((draft) => hasActiveStatus(draft.status)) ? 2000 : false;
    },
  });

  const createDraft = useMutation({
    mutationFn: (payload: CreateDraftRequest) => draftsApi.create(notebookId, payload),
    onSuccess: (draft) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebookDrafts(notebookId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.draft(draft.id) });
      toast({
        title: t.common.success,
        description: t.notebooks.draftCreateSuccess,
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

  const rerunDraft = useMutation({
    mutationFn: ({ draftId, payload }: { draftId: string; payload?: RerunDraftRequest }) =>
      draftsApi.rerun(draftId, payload),
    onSuccess: (draft) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebookDrafts(notebookId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.draft(draft.id) });
      toast({
        title: t.common.success,
        description: t.notebooks.draftRerunSuccess,
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

  const verifyDraft = useMutation({
    mutationFn: (draftId: string) => draftsApi.verify(draftId),
    onSuccess: (draft) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebookDrafts(notebookId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.draft(draft.id) });
      toast({
        title: t.common.success,
        description: t.notebooks.draftVerifySuccess,
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

  return {
    drafts: draftsQuery.data ?? [],
    isLoading: draftsQuery.isLoading,
    isFetching: draftsQuery.isFetching,
    error: draftsQuery.error,
    refetch: draftsQuery.refetch,
    createDraft,
    rerunDraft,
    verifyDraft,
  };
}
