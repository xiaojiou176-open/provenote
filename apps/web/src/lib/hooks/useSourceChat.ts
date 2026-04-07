"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { sourceChatApi } from "@/lib/api/source-chat";
import { useTranslation } from "@/lib/hooks/use-translation";
import { appLog } from "@/lib/log";
import type {
  CreateSourceChatSessionRequest,
  SourceChatContextIndicator,
  SourceChatMessage,
  SourceChatSession,
  UpdateSourceChatSessionRequest,
} from "@/lib/types/api";
import { getApiErrorMessage } from "@/lib/utils/error-handler";

export function useSourceChat(sourceId: string) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<SourceChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [contextIndicators, setContextIndicators] = useState<SourceChatContextIndicator | null>(
    null,
  );
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesRef = useRef<SourceChatMessage[]>([]);
  const currentSessionIdRef = useRef<string | null>(null);
  const requestIdRef = useRef(0);

  const setActiveSessionId = useCallback((sessionId: string | null) => {
    currentSessionIdRef.current = sessionId;
    setCurrentSessionId(sessionId);
  }, []);

  const abortInFlightRequest = useCallback(() => {
    requestIdRef.current += 1;
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setIsStreaming(false);
  }, []);

  // Fetch sessions
  const {
    data: sessions = [],
    isLoading: loadingSessions,
    refetch: refetchSessions,
  } = useQuery<SourceChatSession[]>({
    queryKey: QUERY_KEYS.sourceChatSessions(sourceId),
    queryFn: () => sourceChatApi.listSessions(sourceId),
    enabled: !!sourceId,
  });
  const normalizedSessions = Array.isArray(sessions) ? sessions : [];

  // Fetch current session with messages
  const { data: currentSession, refetch: refetchCurrentSession } = useQuery({
    queryKey: currentSessionId
      ? QUERY_KEYS.sourceChatSession(sourceId, currentSessionId)
      : QUERY_KEYS.sourceChatSessions(sourceId),
    queryFn: () => sourceChatApi.getSession(sourceId, currentSessionId!),
    enabled: !!sourceId && !!currentSessionId,
  });

  // Update messages when session changes
  useEffect(() => {
    if (currentSession?.messages) {
      setMessages(currentSession.messages);
    }
  }, [currentSession]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    currentSessionIdRef.current = currentSessionId;
  }, [currentSessionId]);

  // Auto-select most recent session when sessions are loaded
  useEffect(() => {
    if (normalizedSessions.length > 0 && !currentSessionId) {
      // Find most recent session (sessions are sorted by created date desc from API)
      const mostRecentSession = normalizedSessions[0];
      setActiveSessionId(mostRecentSession.id);
    }
  }, [normalizedSessions, currentSessionId, setActiveSessionId]);

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: (data: Omit<CreateSourceChatSessionRequest, "source_id">) =>
      sourceChatApi.createSession(sourceId, data),
    onSuccess: (newSession) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sourceChatSessions(sourceId) });
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
      data: UpdateSourceChatSessionRequest;
    }) => sourceChatApi.updateSession(sourceId, sessionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sourceChatSessions(sourceId) });
      if (currentSessionId) {
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.sourceChatSession(sourceId, currentSessionId),
        });
      }
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
    mutationFn: (sessionId: string) => sourceChatApi.deleteSession(sourceId, sessionId),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sourceChatSessions(sourceId) });
      if (currentSessionId === deletedId) {
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

  // Send message with streaming
  const sendMessage = useCallback(
    async (message: string, modelOverride?: string) => {
      abortInFlightRequest();
      const controller = new AbortController();
      abortControllerRef.current = controller;
      const requestId = requestIdRef.current;
      let sessionId = currentSessionIdRef.current;

      const isRequestActive = (targetSessionId: string) =>
        requestIdRef.current === requestId &&
        !controller.signal.aborted &&
        currentSessionIdRef.current === targetSessionId;

      // Auto-create session if none exists
      if (!sessionId) {
        try {
          const defaultTitle = message.length > 30 ? `${message.substring(0, 30)}...` : message;
          const newSession = await sourceChatApi.createSession(sourceId, { title: defaultTitle });
          if (requestIdRef.current !== requestId || controller.signal.aborted) {
            return;
          }
          sessionId = newSession.id;
          setActiveSessionId(sessionId);
          queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sourceChatSessions(sourceId) });
        } catch (err: unknown) {
          const error = err as { response?: { data?: { detail?: string } }; message?: string };
          appLog.error("source-chat", "Failed to auto-create chat session", error);
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
      const userMessage: SourceChatMessage = {
        id: `temp-${Date.now()}`,
        type: "human",
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setContextIndicators(null);
      setIsStreaming(true);

      try {
        const response = await sourceChatApi.sendMessage(
          sourceId,
          sessionId,
          {
            message,
            model_override: modelOverride,
          },
          { signal: controller.signal },
        );

        if (!response) {
          throw new Error("No response body");
        }

        const reader = response.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let aiMessage: SourceChatMessage | null = null;
        const existingAiCount = messagesRef.current.filter((msg) => msg.type === "ai").length;
        let streamedAiCount = 0;

        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            buffer += decoder.decode();
          } else {
            buffer += decoder.decode(value, { stream: true });
          }

          const normalized = buffer.replace(/\r\n/g, "\n");
          const lines = normalized.split("\n");
          buffer = done ? "" : lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data:")) {
              continue;
            }
            try {
              const raw = line.slice(5).trimStart();
              if (!raw) {
                continue;
              }
              const data = JSON.parse(raw);
              if (!isRequestActive(sessionId)) {
                return;
              }

              if (data.type === "ai_message") {
                streamedAiCount += 1;
                if (streamedAiCount <= existingAiCount) {
                  continue;
                }

                if (!aiMessage) {
                  aiMessage = {
                    id: `ai-${Date.now()}`,
                    type: "ai",
                    content: data.content || "",
                    timestamp: new Date().toISOString(),
                  };
                  setMessages((prev) => [...prev, aiMessage!]);
                } else {
                  aiMessage.content = data.content || aiMessage.content;
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === aiMessage?.id ? { ...msg, content: aiMessage?.content } : msg,
                    ),
                  );
                }
              } else if (data.type === "context_indicators") {
                setContextIndicators(data.data);
              } else if (data.type === "error") {
                throw new Error(data.message || "Stream error");
              } else if (data.type === "complete") {
                setIsStreaming(false);
              }
            } catch (e) {
              if (e instanceof SyntaxError) {
                appLog.error("source-chat", "Failed to parse SSE payload", e);
              } else {
                throw e;
              }
            }
          }

          if (done) {
            break;
          }
        }
      } catch (err: unknown) {
        if ((err as Error).name === "AbortError") {
          return;
        }
        const error = err as { response?: { data?: { detail?: string } }; message?: string };
        appLog.error("source-chat", "Failed to send source chat message", error);
        toast.error(
          getApiErrorMessage(
            error.response?.data?.detail || error.message,
            (key) => t(key),
            "apiErrors.failedToSendMessage",
          ),
        );
        // Remove optimistic messages on error
        if (isRequestActive(sessionId)) {
          setMessages((prev) => prev.filter((msg) => !msg.id.startsWith("temp-")));
        }
      } finally {
        if (requestIdRef.current === requestId) {
          setIsStreaming(false);
        }
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
        if (isRequestActive(sessionId)) {
          // Refetch session to get persisted messages
          refetchCurrentSession();
        }
      }
    },
    [sourceId, abortInFlightRequest, refetchCurrentSession, queryClient, setActiveSessionId, t],
  );

  // Cancel streaming
  const cancelStreaming = useCallback(() => {
    abortInFlightRequest();
  }, [abortInFlightRequest]);

  // Switch session
  const switchSession = useCallback(
    (sessionId: string) => {
      abortInFlightRequest();
      setMessages([]);
      setActiveSessionId(sessionId);
      setContextIndicators(null);
    },
    [abortInFlightRequest, setActiveSessionId],
  );

  // Create session
  const createSession = useCallback(
    (data: Omit<CreateSourceChatSessionRequest, "source_id">) => {
      return createSessionMutation.mutate(data);
    },
    [createSessionMutation],
  );

  // Update session
  const updateSession = useCallback(
    (sessionId: string, data: UpdateSourceChatSessionRequest) => {
      return updateSessionMutation.mutate({ sessionId, data });
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

  useEffect(
    () => () => {
      abortInFlightRequest();
    },
    [abortInFlightRequest],
  );

  return {
    // State
    sessions: normalizedSessions,
    currentSession: normalizedSessions.find((s) => s.id === currentSessionId),
    currentSessionId,
    messages,
    isStreaming,
    contextIndicators,
    loadingSessions,

    // Actions
    createSession,
    updateSession,
    deleteSession,
    switchSession,
    sendMessage,
    cancelStreaming,
    refetchSessions,
  };
}
