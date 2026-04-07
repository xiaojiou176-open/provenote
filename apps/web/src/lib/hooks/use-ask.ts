"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { searchApi } from "@/lib/api/search";
import { useTranslation } from "@/lib/hooks/use-translation";
import { appLog } from "@/lib/log";
import type { AskStreamEvent } from "@/lib/types/search";
import { getApiErrorMessage } from "@/lib/utils/error-handler";

interface AskModels {
  strategy: string;
  answer: string;
  finalAnswer: string;
}

interface StrategyData {
  reasoning: string;
  searches: Array<{ term: string; instructions: string }>;
}

interface AskState {
  isStreaming: boolean;
  strategy: StrategyData | null;
  answers: string[];
  finalAnswer: string | null;
  error: string | null;
}

export function useAsk() {
  const { t } = useTranslation();
  const abortControllerRef = useRef<AbortController | null>(null);
  const activeRequestIdRef = useRef(0);
  const [state, setState] = useState<AskState>({
    isStreaming: false,
    strategy: null,
    answers: [],
    finalAnswer: null,
    error: null,
  });

  const parseSseBuffer = useCallback(
    (
      rawBuffer: string,
      emit: (data: AskStreamEvent) => void,
      flushLastLine: boolean = false,
    ): string => {
      const normalized = rawBuffer.replace(/\r\n/g, "\n");
      const lines = normalized.split("\n");
      const remainder = flushLastLine ? "" : lines.pop() || "";
      let eventDataLines: string[] = [];

      const processEvent = () => {
        if (eventDataLines.length === 0) {
          return;
        }
        const payload = eventDataLines.join("\n").trim();
        eventDataLines = [];
        if (!payload) {
          return;
        }
        try {
          emit(JSON.parse(payload) as AskStreamEvent);
        } catch (e) {
          if (e instanceof SyntaxError) {
            appLog.error("use-ask", "Failed to parse SSE payload", { error: e, payload });
            return;
          }
          throw e;
        }
      };

      for (const line of lines) {
        if (line.length === 0) {
          processEvent();
          continue;
        }

        if (line.startsWith("data:")) {
          eventDataLines.push(line.slice(5).trimStart());
        }
      }

      if (flushLastLine) {
        processEvent();
      }

      return remainder;
    },
    [],
  );

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  const sendAsk = useCallback(
    async (question: string, models: AskModels) => {
      // Validate inputs
      if (!question.trim()) {
        toast.error(t("apiErrors.pleaseEnterQuestion"));
        return;
      }

      if (!models.strategy || !models.answer || !models.finalAnswer) {
        toast.error(t("apiErrors.pleaseConfigureModels"));
        return;
      }

      // Cancel previous stream before starting a new request
      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;
      const requestId = activeRequestIdRef.current + 1;
      activeRequestIdRef.current = requestId;

      // Reset state
      setState({
        isStreaming: true,
        strategy: null,
        answers: [],
        finalAnswer: null,
        error: null,
      });

      try {
        const response = await searchApi.askKnowledgeBase(
          {
            question,
            strategy_model: models.strategy,
            answer_model: models.answer,
            final_answer_model: models.finalAnswer,
          },
          { signal: controller.signal },
        );

        if (!response) {
          throw new Error("No response body received from server");
        }

        const reader = response.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          if (activeRequestIdRef.current !== requestId) {
            await reader.cancel();
            return;
          }

          const { done, value } = await reader.read();

          if (done) {
            buffer += decoder.decode();
            buffer = parseSseBuffer(
              buffer,
              (data) => {
                if (activeRequestIdRef.current !== requestId) {
                  return;
                }

                if (data.type === "strategy") {
                  setState((prev) => ({
                    ...prev,
                    strategy: {
                      reasoning: data.reasoning || "",
                      searches: data.searches || [],
                    },
                  }));
                  return;
                }

                if (data.type === "answer") {
                  const content = data.content || "";
                  if (!content) {
                    return;
                  }
                  setState((prev) => {
                    const lastAnswer = prev.answers[prev.answers.length - 1];
                    if (lastAnswer === content) {
                      return prev;
                    }
                    return {
                      ...prev,
                      answers: [...prev.answers, content],
                    };
                  });
                  return;
                }

                if (data.type === "final_answer") {
                  setState((prev) => ({
                    ...prev,
                    finalAnswer: data.content || "",
                    isStreaming: false,
                  }));
                  return;
                }

                if (data.type === "complete") {
                  setState((prev) => ({
                    ...prev,
                    isStreaming: false,
                  }));
                  return;
                }

                if (data.type === "error") {
                  throw new Error(data.message || "Stream error occurred");
                }
              },
              true,
            );
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          buffer = parseSseBuffer(buffer, (data) => {
            if (activeRequestIdRef.current !== requestId) {
              return;
            }

            if (data.type === "strategy") {
              setState((prev) => ({
                ...prev,
                strategy: {
                  reasoning: data.reasoning || "",
                  searches: data.searches || [],
                },
              }));
              return;
            }

            if (data.type === "answer") {
              const content = data.content || "";
              if (!content) {
                return;
              }
              setState((prev) => {
                const lastAnswer = prev.answers[prev.answers.length - 1];
                if (lastAnswer === content) {
                  return prev;
                }
                return {
                  ...prev,
                  answers: [...prev.answers, content],
                };
              });
              return;
            }

            if (data.type === "final_answer") {
              setState((prev) => ({
                ...prev,
                finalAnswer: data.content || "",
                isStreaming: false,
              }));
              return;
            }

            if (data.type === "complete") {
              setState((prev) => ({
                ...prev,
                isStreaming: false,
              }));
              return;
            }

            if (data.type === "error") {
              throw new Error(data.message || "Stream error occurred");
            }
          });
        }

        // Ensure streaming is stopped
        if (activeRequestIdRef.current === requestId) {
          setState((prev) => ({ ...prev, isStreaming: false }));
        }
      } catch (error) {
        if ((error as Error).name === "AbortError") {
          if (activeRequestIdRef.current === requestId) {
            setState((prev) => ({ ...prev, isStreaming: false }));
          }
          return;
        }

        const err = error as { message?: string };
        const errorMessage = err.message || "An unexpected error occurred";
        appLog.error("use-ask", "Knowledge-base ask request failed", error);

        if (activeRequestIdRef.current === requestId) {
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            error: errorMessage,
          }));
        }

        toast.error(t("apiErrors.askFailed"), {
          description: getApiErrorMessage(errorMessage, (key) => t(key)),
        });
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    },
    [t, parseSseBuffer],
  );

  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setState({
      isStreaming: false,
      strategy: null,
      answers: [],
      finalAnswer: null,
      error: null,
    });
  }, []);

  useEffect(
    () => () => {
      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
    },
    [],
  );

  return {
    ...state,
    sendAsk,
    cancel,
    reset,
  };
}
