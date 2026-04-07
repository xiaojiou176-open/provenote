"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { chatApi } from "@/lib/api/chat";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { useTranslation } from "@/lib/hooks/use-translation";
import { appLog } from "@/lib/log";
import type {
  CreateNotebookChatSessionRequest,
  NotebookChatMessage,
  NoteResponse,
  SourceListResponse,
  UpdateNotebookChatSessionRequest,
} from "@/lib/types/api";
import type { ContextSelections } from "@/lib/types/context";
import { getApiErrorMessage } from "@/lib/utils/error-handler";

interface UseNotebookChatParams {
  notebookId: string;
  sources: SourceListResponse[];
  notes: NoteResponse[];
  contextSelections: ContextSelections;
}

function createAbortError() {
  return new DOMException("Request was aborted", "AbortError");
}

async function withAbortSignal<T>(promise: Promise<T>, signal: AbortSignal): Promise<T> {
  if (signal.aborted) {
    throw createAbortError();
  }

  return new Promise<T>((resolve, reject) => {
    const onAbort = () => reject(createAbortError());

    signal.addEventListener("abort", onAbort, { once: true });
    promise.then(
      (value) => {
        signal.removeEventListener("abort", onAbort);
        resolve(value);
      },
      (error) => {
        signal.removeEventListener("abort", onAbort);
        reject(error);
      },
    );
  });
}

export function useNotebookChat({
  notebookId,
  sources,
  notes,
  contextSelections,
}: UseNotebookChatParams) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<NotebookChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [tokenCount, setTokenCount] = useState<number>(0);
  const [charCount, setCharCount] = useState<number>(0);
  // Pending model override for when user changes model before a session exists
  const [pendingModelOverride, setPendingModelOverride] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const currentSessionIdRef = useRef<string | null>(null);
  const requestIdRef = useRef(0);
  const contextCountRequestIdRef = useRef(0);

  const setActiveSessionId = useCallback((sessionId: string | null) => {
    currentSessionIdRef.current = sessionId;
    setCurrentSessionId(sessionId);
  }, []);

  const abortInFlightRequest = useCallback(() => {
    requestIdRef.current += 1;
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setIsSending(false);
  }, []);

  // Fetch sessions for this notebook
  const {
    data: sessions = [],
    isLoading: loadingSessions,
    refetch: refetchSessions,
  } = useQuery({
    queryKey: QUERY_KEYS.notebookChatSessions(notebookId),
    queryFn: () => chatApi.listSessions(notebookId),
    enabled: !!notebookId,
  });

  // Fetch current session with messages
  const { data: currentSession, refetch: refetchCurrentSession } = useQuery({
    queryKey: QUERY_KEYS.notebookChatSession(currentSessionId!),
    queryFn: () => chatApi.getSession(currentSessionId!),
    enabled: !!notebookId && !!currentSessionId,
  });

  // Update messages when current session changes
  useEffect(() => {
    if (currentSession?.messages) {
      setMessages(currentSession.messages);
    }
  }, [currentSession]);

  useEffect(() => {
    currentSessionIdRef.current = currentSessionId;
  }, [currentSessionId]);

  // Auto-select most recent session when sessions are loaded
  useEffect(() => {
    if (sessions.length > 0 && !currentSessionId) {
      // Sessions are sorted by created date desc from API
      const mostRecentSession = sessions[0];
      setActiveSessionId(mostRecentSession.id);
    }
  }, [sessions, currentSessionId, setActiveSessionId]);

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: (data: CreateNotebookChatSessionRequest) => chatApi.createSession(data),
    onSuccess: (newSession) => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.notebookChatSessions(notebookId),
      });
      setActiveSessionId(newSession.id);
      toast.success(t.chat.sessionCreated);
    },
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      toast.error(
        getApiErrorMessage(
          error.response?.data?.detail || error.message,
          (key) => t(key),
          "apiErrors.failedToCreateSession",
        ),
      );
    },
  });

  // Update session mutation
  const updateSessionMutation = useMutation({
    mutationFn: ({
      sessionId,
      data,
    }: {
      sessionId: string;
      data: UpdateNotebookChatSessionRequest;
    }) => chatApi.updateSession(sessionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.notebookChatSessions(notebookId),
      });
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.notebookChatSession(currentSessionId!),
      });
      toast.success(t.chat.sessionUpdated);
    },
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      toast.error(
        getApiErrorMessage(
          error.response?.data?.detail || error.message,
          (key) => t(key),
          "apiErrors.failedToUpdateSession",
        ),
      );
    },
  });

  // Delete session mutation
  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: string) => chatApi.deleteSession(sessionId),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.notebookChatSessions(notebookId),
      });
      if (currentSessionIdRef.current === deletedId) {
        setActiveSessionId(null);
        setMessages([]);
      }
      toast.success(t.chat.sessionDeleted);
    },
    onError: (err: unknown) => {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      toast.error(
        getApiErrorMessage(
          error.response?.data?.detail || error.message,
          (key) => t(key),
          "apiErrors.failedToDeleteSession",
        ),
      );
    },
  });

  // Build context from sources and notes based on user selections
  const buildContext = useCallback(async () => {
    // Build context_config mapping IDs to selection modes
    const context_config: { sources: Record<string, string>; notes: Record<string, string> } = {
      sources: {},
      notes: {},
    };

    // Map source selections
    sources.forEach((source) => {
      const mode = contextSelections.sources[source.id];
      if (mode === "insights") {
        context_config.sources[source.id] = "insights";
      } else if (mode === "full") {
        context_config.sources[source.id] = "full content";
      } else {
        context_config.sources[source.id] = "not in";
      }
    });

    // Map note selections
    notes.forEach((note) => {
      const mode = contextSelections.notes[note.id];
      if (mode === "full") {
        context_config.notes[note.id] = "full content";
      } else {
        context_config.notes[note.id] = "not in";
      }
    });

    // Call API to build context with actual content
    const response = await chatApi.buildContext({
      notebook_id: notebookId,
      context_config,
    });

    return response;
  }, [notebookId, sources, notes, contextSelections]);

  // Send message (synchronous, no streaming)
  const sendMessage = useCallback(
    async (message: string, modelOverride?: string) => {
      abortInFlightRequest();
      const controller = new AbortController();
      abortControllerRef.current = controller;
      const requestId = requestIdRef.current;
      let sessionId = currentSessionIdRef.current;
      const optimisticMessageId = `temp-${Date.now()}`;

      const isRequestActive = (targetSessionId: string) =>
        requestIdRef.current === requestId &&
        !controller.signal.aborted &&
        currentSessionIdRef.current === targetSessionId;

      // Auto-create session if none exists
      if (!sessionId) {
        try {
          const defaultTitle = message.length > 30 ? `${message.substring(0, 30)}...` : message;
          const newSession = await withAbortSignal(
            chatApi.createSession({
              notebook_id: notebookId,
              title: defaultTitle,
              // Include pending model override when creating session
              model_override: pendingModelOverride ?? undefined,
            }),
            controller.signal,
          );
          if (requestIdRef.current !== requestId || controller.signal.aborted) {
            return;
          }
          sessionId = newSession.id;
          setActiveSessionId(sessionId);
          // Clear pending model override now that it's applied to the session
          setPendingModelOverride(null);
          queryClient.invalidateQueries({
            queryKey: QUERY_KEYS.notebookChatSessions(notebookId),
          });
        } catch (err: unknown) {
          const error = err as { response?: { data?: { detail?: string } }; message?: string };
          toast.error(
            getApiErrorMessage(
              error.response?.data?.detail || error.message,
              (key) => t(key),
              "apiErrors.failedToCreateSession",
            ),
          );
          return;
        }
      }
      if (!isRequestActive(sessionId)) {
        return;
      }

      // Add user message optimistically
      const userMessage: NotebookChatMessage = {
        id: optimisticMessageId,
        type: "human",
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsSending(true);

      try {
        // Build context and send message
        const contextResponse = await withAbortSignal(buildContext(), controller.signal);
        if (!isRequestActive(sessionId)) {
          return;
        }
        setTokenCount(contextResponse.token_count);
        setCharCount(contextResponse.char_count);
        const response = await withAbortSignal(
          chatApi.sendMessage({
            session_id: sessionId,
            message,
            context: contextResponse.context,
            model_override: modelOverride ?? currentSession?.model_override ?? undefined,
          }),
          controller.signal,
        );
        if (!isRequestActive(sessionId)) {
          return;
        }

        // Update messages with API response
        setMessages(response.messages);

        // Refetch current session to get updated data
        await withAbortSignal(refetchCurrentSession(), controller.signal);
      } catch (err: unknown) {
        if ((err as Error).name === "AbortError") {
          if (currentSessionIdRef.current === sessionId) {
            setMessages((prev) => prev.filter((msg) => msg.id !== optimisticMessageId));
          }
          return;
        }
        const error = err as { response?: { data?: { detail?: string } }; message?: string };
        appLog.error("notebook-chat", "Failed to send notebook chat message", error);
        toast.error(
          getApiErrorMessage(
            error.response?.data?.detail || error.message,
            (key) => t(key),
            "apiErrors.failedToSendMessage",
          ),
        );
        // Remove optimistic message on error
        setMessages((prev) => prev.filter((msg) => msg.id !== optimisticMessageId));
      } finally {
        if (requestIdRef.current === requestId) {
          setIsSending(false);
        }
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    },
    [
      notebookId,
      currentSession,
      pendingModelOverride,
      abortInFlightRequest,
      buildContext,
      refetchCurrentSession,
      queryClient,
      setActiveSessionId,
      t,
    ],
  );

  // Switch session
  const switchSession = useCallback(
    (sessionId: string) => {
      abortInFlightRequest();
      setMessages([]);
      setActiveSessionId(sessionId);
    },
    [abortInFlightRequest, setActiveSessionId],
  );

  // Create session
  const createSession = useCallback(
    (title?: string) => {
      return createSessionMutation.mutate({
        notebook_id: notebookId,
        title,
      });
    },
    [createSessionMutation, notebookId],
  );

  // Update session
  const updateSession = useCallback(
    (sessionId: string, data: UpdateNotebookChatSessionRequest) => {
      return updateSessionMutation.mutate({
        sessionId,
        data,
      });
    },
    [updateSessionMutation],
  );

  // Delete session
  const deleteSession = useCallback(
    (sessionId: string) => {
      return deleteSessionMutation.mutate(sessionId);
    },
    [deleteSessionMutation],
  );

  // Set model override - handles both existing sessions and pending state
  const setModelOverride = useCallback(
    (model: string | null) => {
      if (currentSessionId) {
        // Session exists - update it directly
        updateSessionMutation.mutate({
          sessionId: currentSessionId,
          data: { model_override: model },
        });
      } else {
        // No session yet - store as pending
        setPendingModelOverride(model);
      }
    },
    [currentSessionId, updateSessionMutation],
  );

  // Update token/char counts when context selections change
  useEffect(() => {
    if (!notebookId) {
      setTokenCount(0);
      setCharCount(0);
      return;
    }

    const requestId = contextCountRequestIdRef.current + 1;
    contextCountRequestIdRef.current = requestId;
    const controller = new AbortController();
    let disposed = false;

    const updateContextCounts = async () => {
      try {
        const contextResponse = await withAbortSignal(buildContext(), controller.signal);
        if (disposed || contextCountRequestIdRef.current !== requestId) {
          return;
        }
        setTokenCount(contextResponse.token_count);
        setCharCount(contextResponse.char_count);
      } catch (error) {
        if ((error as Error).name === "AbortError") {
          return;
        }
        if (disposed || contextCountRequestIdRef.current !== requestId) {
          return;
        }
        appLog.error("notebook-chat", "Failed to update context counts", error);
      }
    };
    void updateContextCounts();

    return () => {
      disposed = true;
      controller.abort();
    };
  }, [buildContext, notebookId]);

  useEffect(
    () => () => {
      abortInFlightRequest();
    },
    [abortInFlightRequest],
  );

  return {
    // State
    sessions,
    currentSession: currentSession || sessions.find((s) => s.id === currentSessionId),
    currentSessionId,
    messages,
    isSending,
    loadingSessions,
    tokenCount,
    charCount,
    pendingModelOverride,

    // Actions
    createSession,
    updateSession,
    deleteSession,
    switchSession,
    sendMessage,
    setModelOverride,
    refetchSessions,
  };
}
