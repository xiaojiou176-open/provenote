"use client";

import { BookOpen, CheckCircle2, Loader2, Save } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNotebooks } from "@/lib/hooks/use-notebooks";
import {
  useAppendResearchThreadEntry,
  useCreateResearchThread,
} from "@/lib/hooks/use-research-threads";
import { useTranslation } from "@/lib/hooks/use-translation";
import type { SearchResult } from "@/lib/types/search";

const AUTO_SAVE_ENABLED_KEY = "provenote:research-capture:auto-save-enabled";
const AUTO_SAVE_NOTEBOOK_KEY = "provenote:research-capture:notebook-id";
const AUTO_SAVE_CAPTURE_MAP_KEY = "provenote:research-capture:session-map";

interface SessionCaptureEntry {
  threadId: string;
  lastSignature: string;
}

function canUseSessionStorage() {
  return typeof window !== "undefined" && typeof window.sessionStorage !== "undefined";
}

function readCaptureMap(): Record<string, SessionCaptureEntry> {
  if (!canUseSessionStorage()) {
    return {};
  }

  const raw = window.sessionStorage.getItem(AUTO_SAVE_CAPTURE_MAP_KEY);
  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw) as Record<string, SessionCaptureEntry>;
  } catch {
    window.sessionStorage.removeItem(AUTO_SAVE_CAPTURE_MAP_KEY);
    return {};
  }
}

function writeCaptureMap(value: Record<string, SessionCaptureEntry>) {
  if (!canUseSessionStorage()) {
    return;
  }
  window.sessionStorage.setItem(AUTO_SAVE_CAPTURE_MAP_KEY, JSON.stringify(value));
}

interface ResearchCapturePanelProps {
  mode: "ask" | "search";
  query: string;
  answer?: string | null;
  searchResults?: SearchResult[];
  defaultNotebookId?: string;
  sourceIds?: string[];
  noteIds?: string[];
  hasCompletedResult: boolean;
}

function normalizeTitle(
  mode: "ask" | "search",
  query: string,
  getMessage: (key: string, values?: Record<string, unknown>) => string,
) {
  const trimmed = query.trim();
  if (!trimmed) {
    return mode === "ask"
      ? getMessage("searchPage.capturedAskThreadFallback")
      : getMessage("searchPage.capturedSearchThreadFallback");
  }
  const clipped = trimmed.length > 72 ? `${trimmed.slice(0, 69)}...` : trimmed;
  return mode === "ask"
    ? getMessage("searchPage.capturedAskPrefix", { query: clipped })
    : getMessage("searchPage.capturedSearchPrefix", { query: clipped });
}

export function ResearchCapturePanel({
  mode,
  query,
  answer,
  searchResults = [],
  defaultNotebookId = "",
  sourceIds = [],
  noteIds = [],
  hasCompletedResult,
}: ResearchCapturePanelProps) {
  const { t } = useTranslation();
  const { data: notebooks = [], isLoading } = useNotebooks(false);
  const [selectedNotebookId, setSelectedNotebookId] = useState("");
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(false);
  const [lastCaptureMessage, setLastCaptureMessage] = useState<string | null>(null);
  const createResearchThread = useCreateResearchThread();
  const appendResearchThreadEntry = useAppendResearchThreadEntry(selectedNotebookId);
  const pendingSignatureRef = useRef<string>("");

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const storedNotebookId = window.localStorage.getItem(AUTO_SAVE_NOTEBOOK_KEY);
    const storedEnabled = window.localStorage.getItem(AUTO_SAVE_ENABLED_KEY);
    if (storedNotebookId) {
      setSelectedNotebookId(storedNotebookId);
    }
    if (storedEnabled === "1") {
      setAutoSaveEnabled(true);
    }
  }, []);

  useEffect(() => {
    if (!defaultNotebookId) {
      return;
    }
    setSelectedNotebookId(defaultNotebookId);
  }, [defaultNotebookId]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    if (selectedNotebookId) {
      window.localStorage.setItem(AUTO_SAVE_NOTEBOOK_KEY, selectedNotebookId);
    } else {
      window.localStorage.removeItem(AUTO_SAVE_NOTEBOOK_KEY);
    }
    window.localStorage.setItem(AUTO_SAVE_ENABLED_KEY, autoSaveEnabled ? "1" : "0");
  }, [autoSaveEnabled, selectedNotebookId]);

  const notebookOptions = useMemo(
    () => notebooks.filter((notebook) => !notebook.archived),
    [notebooks],
  );

  const captureKey = useMemo(() => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery || !selectedNotebookId) {
      return "";
    }

    return JSON.stringify({
      mode,
      notebookId: selectedNotebookId,
      query: trimmedQuery,
    });
  }, [mode, query, selectedNotebookId]);

  const resultSignature = useMemo(() => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery || !hasCompletedResult || !captureKey) {
      return "";
    }

    if (mode === "ask") {
      return JSON.stringify({
        captureKey,
        answer: answer?.trim() ?? "",
        sourceIds,
        noteIds,
      });
    }

    return JSON.stringify({
      captureKey,
      results: searchResults.map((result) => ({
        id: result.id,
        title: result.title,
        parent_id: result.parent_id,
        final_score: result.final_score,
        matches: result.matches ?? [],
      })),
      sourceIds,
      noteIds,
    });
  }, [answer, captureKey, hasCompletedResult, noteIds, query, searchResults, sourceIds]);

  useEffect(() => {
    if (!autoSaveEnabled || !selectedNotebookId || !captureKey || !resultSignature) {
      return;
    }
    if (pendingSignatureRef.current === resultSignature) {
      return;
    }

    const captureMap = readCaptureMap();
    const existingCapture = captureMap[captureKey];
    if (existingCapture?.lastSignature === resultSignature) {
      return;
    }

    const title = normalizeTitle(mode, query, (key, values) => t(key, values));
    let cancelled = false;
    pendingSignatureRef.current = resultSignature;

    async function persistResult() {
      if (existingCapture?.threadId) {
        await appendResearchThreadEntry.mutateAsync({
          threadId: existingCapture.threadId,
          payload: {
            entry_type: mode === "ask" ? "answer_snapshot" : "search_result",
            title,
            content:
              mode === "ask"
                ? answer?.trim() || query.trim()
                : t.searchPage.capturedSearchUpdate({ query: query.trim() }),
            source_ids: sourceIds,
            note_ids: noteIds,
            metadata:
              mode === "ask"
                ? { question: query.trim() }
                : {
                    query: query.trim(),
                    search_results: searchResults.map((result) => ({ ...result })),
                  },
          },
        });
        writeCaptureMap({
          ...captureMap,
          [captureKey]: {
            threadId: existingCapture.threadId,
            lastSignature: resultSignature,
          },
        });
        if (!cancelled) {
          setLastCaptureMessage(t.searchPage.researchCaptureUpdatedMessage);
        }
        return;
      }

      const created = await createResearchThread.mutateAsync({
        notebookId: selectedNotebookId,
        payload: {
          title,
          seed_kind: mode,
          question: query.trim() || undefined,
          answer: mode === "ask" ? answer?.trim() || undefined : undefined,
          source_ids: sourceIds,
          note_ids: noteIds,
          search_results: mode === "search" ? searchResults.map((result) => ({ ...result })) : [],
        },
      });
      writeCaptureMap({
        ...captureMap,
        [captureKey]: {
          threadId: created.id,
          lastSignature: resultSignature,
        },
      });
      if (!cancelled) {
        setLastCaptureMessage(
          t("searchPage.researchCaptureSavedToMessage", { title: created.title }),
        );
      }
    }

    void persistResult().catch(() => {
      pendingSignatureRef.current = "";
      if (!cancelled) {
        setLastCaptureMessage(t.searchPage.researchCaptureFailedMessage);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [
    answer,
    appendResearchThreadEntry,
    autoSaveEnabled,
    captureKey,
    createResearchThread,
    mode,
    noteIds,
    query,
    resultSignature,
    searchResults,
    selectedNotebookId,
    sourceIds,
  ]);

  const helpText =
    mode === "ask" ? t.searchPage.researchCaptureAskHelp : t.searchPage.researchCaptureSearchHelp;
  const resultTypeLabel =
    mode === "ask"
      ? t.searchPage.researchCaptureAnswerLabel
      : t.searchPage.researchCaptureSearchResultLabel;

  return (
    <div
      className="ui-research-capture rounded-[1.35rem] border border-border/80 bg-card/85 p-5"
      data-testid="research-capture-panel"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="ui-metric-label text-primary">{t.searchPage.researchCaptureTitle}</p>
          <p className="font-serif text-2xl leading-none tracking-[-0.03em] text-foreground">
            {t.searchPage.researchCaptureTitle}
          </p>
          <p className="max-w-2xl text-sm leading-6 text-muted-foreground">{helpText}</p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-border/80 bg-background/80 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          <Save className="h-3.5 w-3.5" />
          {autoSaveEnabled
            ? t.searchPage.researchCaptureAutoSaveOn
            : t.searchPage.researchCaptureAutoSaveOff}
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-[minmax(0,1fr),auto] md:items-end">
        <label className="grid gap-1.5 text-sm">
          <span className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            {t.searchPage.researchCaptureWorkingNotebook}
          </span>
          <select
            className="rounded-2xl border border-border/80 bg-background/90 px-3 py-2.5 text-sm shadow-[0_10px_20px_oklch(18%_0.02_45deg_/4%)]"
            value={selectedNotebookId}
            onChange={(event) => setSelectedNotebookId(event.target.value)}
            disabled={isLoading || notebookOptions.length === 0}
          >
            <option value="">
              {isLoading
                ? t.searchPage.researchCaptureLoadingNotebooks
                : t.searchPage.researchCaptureSelectNotebook}
            </option>
            {notebookOptions.map((notebook) => (
              <option key={notebook.id} value={notebook.id}>
                {notebook.name}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2 rounded-2xl border border-border/80 bg-background/90 px-3 py-2.5 text-sm shadow-[0_10px_20px_oklch(18%_0.02_45deg_/4%)]">
          <input
            type="checkbox"
            checked={autoSaveEnabled}
            onChange={(event) => setAutoSaveEnabled(event.target.checked)}
            disabled={!selectedNotebookId}
          />
          {t.searchPage.researchCaptureAutoSaveCompletedResults}
        </label>
      </div>

      <div className="mt-4 rounded-2xl border border-border/70 bg-muted/20 px-4 py-3 text-xs text-muted-foreground">
        <p>{t("searchPage.researchCaptureAutoSaveHint", { resultType: resultTypeLabel })}</p>
        <p className="mt-2">{t.searchPage.researchCaptureThreadHint}</p>
      </div>

      {createResearchThread.isPending || appendResearchThreadEntry.isPending ? (
        <div className="mt-4 flex items-center gap-2 rounded-2xl border border-border/70 bg-background/70 px-3 py-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          {t.searchPage.researchCaptureSaving}
        </div>
      ) : null}

      {lastCaptureMessage ? (
        <div className="mt-4 flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-2.5 text-sm text-emerald-700">
          <CheckCircle2 className="h-4 w-4" />
          {lastCaptureMessage}
        </div>
      ) : null}

      {!isLoading && notebookOptions.length === 0 ? (
        <div className="mt-4 flex items-center gap-2 rounded-2xl border border-dashed border-border/80 px-3 py-2.5 text-sm text-muted-foreground">
          <BookOpen className="h-4 w-4" />
          {t.searchPage.researchCaptureCreateNotebookHint}
        </div>
      ) : null}
    </div>
  );
}
