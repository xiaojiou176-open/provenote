import { useQuery, useQueryClient } from "@tanstack/react-query";
import { notesApi } from "@/lib/api/notes";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { useAppMutation } from "@/lib/hooks/use-app-mutation";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { CreateNoteRequest, UpdateNoteRequest } from "@/lib/types/api";
import { getApiErrorKey } from "@/lib/utils/error-handler";

export function useNotes(notebookId?: string) {
  return useQuery({
    queryKey: QUERY_KEYS.notes(notebookId),
    queryFn: () => notesApi.list({ notebook_id: notebookId }),
    enabled: !!notebookId,
  });
}

export function useNote(id?: string, options?: { enabled?: boolean }) {
  const noteId = id ?? "";
  return useQuery({
    queryKey: QUERY_KEYS.note(noteId),
    queryFn: () => notesApi.get(noteId),
    enabled: !!noteId && (options?.enabled ?? true),
  });
}

export function useCreateNote() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: (data: CreateNoteRequest) => notesApi.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.notes(variables.notebook_id),
      });
    },
    successToast: {
      title: t.common.success,
      description: t.notebooks.noteCreatedSuccess,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorKey(error, t.notebooks.failedToCreateNote),
      variant: "destructive",
    }),
  });
}

export function useUpdateNote() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateNoteRequest }) =>
      notesApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notes() });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.note(id) });
    },
    successToast: {
      title: t.common.success,
      description: t.notebooks.noteUpdatedSuccess,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorKey(error, t.notebooks.failedToUpdateNote),
      variant: "destructive",
    }),
  });
}

export function useDeleteNote() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useAppMutation({
    mutationFn: (id: string) => notesApi.delete(id),
    onSuccess: () => {
      // Invalidate all notes queries (with and without notebook IDs)
      queryClient.invalidateQueries({ queryKey: ["notes"] });
    },
    successToast: {
      title: t.common.success,
      description: t.notebooks.noteDeletedSuccess,
    },
    errorToast: (error) => ({
      title: t.common.error,
      description: getApiErrorKey(error, t.notebooks.failedToDeleteNote),
      variant: "destructive",
    }),
  });
}
