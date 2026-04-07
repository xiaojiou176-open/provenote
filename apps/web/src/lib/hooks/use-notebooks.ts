import { useQuery, useQueryClient } from "@tanstack/react-query";
import { notebooksApi } from "@/lib/api/notebooks";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { useAppMutation } from "@/lib/hooks/use-app-mutation";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { CreateNotebookRequest, UpdateNotebookRequest } from "@/lib/types/api";
import { getApiErrorKey } from "@/lib/utils/error-handler";

export function useNotebooks(archived?: boolean) {
  return useQuery({
    queryKey: [...QUERY_KEYS.notebooks, { archived }],
    queryFn: () => notebooksApi.list({ archived, order_by: "updated desc" }),
  });
}

export function useNotebook(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.notebook(id),
    queryFn: () => notebooksApi.get(id),
    enabled: !!id,
  });
}

export function useCreateNotebook() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: (data: CreateNotebookRequest) => notebooksApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebooks });
    },
    successToast: {
      title: t.common.success,
      description: t.notebooks.createSuccess,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: t(getApiErrorKey(error, t.common.error)),
      variant: "destructive",
    }),
  });
}

export function useUpdateNotebook() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateNotebookRequest }) =>
      notebooksApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebooks });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebook(id) });
    },
    successToast: {
      title: t.common.success,
      description: t.notebooks.updateSuccess,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: t(getApiErrorKey(error, t.common.error)),
      variant: "destructive",
    }),
  });
}

export function useNotebookDeletePreview(id: string, enabled: boolean = false) {
  return useQuery({
    queryKey: [...QUERY_KEYS.notebook(id), "delete-preview"],
    queryFn: () => notebooksApi.deletePreview(id),
    enabled: !!id && enabled,
  });
}

export function useDeleteNotebook() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: ({
      id,
      deleteExclusiveSources = false,
    }: {
      id: string;
      deleteExclusiveSources?: boolean;
    }) => notebooksApi.delete(id, deleteExclusiveSources),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notebooks });
      // Also invalidate sources since some may have been deleted
      queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
    successToast: {
      title: t.common.success,
      description: t.notebooks.deleteSuccess,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: t(getApiErrorKey(error, t.common.error)),
      variant: "destructive",
    }),
  });
}
