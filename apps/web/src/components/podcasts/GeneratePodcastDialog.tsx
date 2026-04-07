"use client";

import { useQueries, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { chatApi } from "@/lib/api/chat";
import { draftsApi } from "@/lib/api/drafts";
import { notesApi } from "@/lib/api/notes";
import { QUERY_KEYS } from "@/lib/api/query-client";
import { sourcesApi } from "@/lib/api/sources";
import { useNotebooks } from "@/lib/hooks/use-notebooks";
import { useEpisodeProfiles, useGeneratePodcast } from "@/lib/hooks/use-podcasts";
import { useToast } from "@/lib/hooks/use-toast";
import { useTranslation } from "@/lib/hooks/use-translation";
import { appLog } from "@/lib/log";
import type {
  BuildContextRequest,
  DraftResponse,
  NoteResponse,
  SourceListResponse,
} from "@/lib/types/api";
import type { PodcastGenerationRequest } from "@/lib/types/podcasts";

import { GeneratePodcastContentSelectionPanel } from "./GeneratePodcastContentSelectionPanel";
import {
  buildContextConfig,
  getSourceDefaultMode,
  hasSelections,
  type NotebookSelection,
  type NotebookSummary,
  type SourceMode,
} from "./generate-podcast-utils";

interface GeneratePodcastDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function GeneratePodcastDialog({ open, onOpenChange }: GeneratePodcastDialogProps) {
  const { t } = useTranslation();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [expandedNotebooks, setExpandedNotebooks] = useState<string[]>([]);
  const [selections, setSelections] = useState<Record<string, NotebookSelection>>({});
  const [episodeProfileId, setEpisodeProfileId] = useState<string>("");
  const [episodeName, setEpisodeName] = useState("");
  const [instructions, setInstructions] = useState("");
  const [selectedDraftId, setSelectedDraftId] = useState<string>("");
  const [isBuildingContext, setIsBuildingContext] = useState(false);
  const [tokenCount, setTokenCount] = useState<number>(0);
  const [charCount, setCharCount] = useState<number>(0);

  const notebooksQuery = useNotebooks();
  const episodeProfilesQuery = useEpisodeProfiles();
  const generatePodcast = useGeneratePodcast();

  const notebooks = useMemo(() => notebooksQuery.data ?? [], [notebooksQuery.data]);
  const episodeProfiles = useMemo(
    () => episodeProfilesQuery.episodeProfiles ?? [],
    [episodeProfilesQuery.episodeProfiles],
  );

  const sourcesQueries = useQueries({
    queries: notebooks.map((notebook) => ({
      queryKey: QUERY_KEYS.sources(notebook.id),
      queryFn: () => sourcesApi.list({ notebook_id: notebook.id }),
      enabled:
        open && (expandedNotebooks.includes(notebook.id) || hasSelections(selections[notebook.id])),
    })),
  });

  const notesQueries = useQueries({
    queries: notebooks.map((notebook) => ({
      queryKey: QUERY_KEYS.notes(notebook.id),
      queryFn: () => notesApi.list({ notebook_id: notebook.id }),
      enabled:
        open && (expandedNotebooks.includes(notebook.id) || hasSelections(selections[notebook.id])),
    })),
  });

  const draftsQueries = useQueries({
    queries: notebooks.map((notebook) => ({
      queryKey: QUERY_KEYS.notebookDrafts(notebook.id),
      queryFn: () => draftsApi.list(notebook.id),
      enabled: open && expandedNotebooks.includes(notebook.id),
    })),
  });

  const sourcesByNotebook = useMemo<Record<string, SourceListResponse[]>>(() => {
    const map: Record<string, SourceListResponse[]> = {};
    notebooks.forEach((notebook, index) => {
      map[notebook.id] = sourcesQueries[index]?.data ?? [];
    });
    return map;
  }, [notebooks, sourcesQueries]);

  const notesByNotebook = useMemo<Record<string, NoteResponse[]>>(() => {
    const map: Record<string, NoteResponse[]> = {};
    notebooks.forEach((notebook, index) => {
      map[notebook.id] = notesQueries[index]?.data ?? [];
    });
    return map;
  }, [notebooks, notesQueries]);

  const draftsByNotebook = useMemo<Record<string, DraftResponse[]>>(() => {
    const map: Record<string, DraftResponse[]> = {};
    notebooks.forEach((notebook, index) => {
      map[notebook.id] = draftsQueries[index]?.data ?? [];
    });
    return map;
  }, [draftsQueries, notebooks]);

  const fetchingNotebookIds = useMemo(() => {
    const ids = new Set<string>();
    notebooks.forEach((notebook, index) => {
      if (sourcesQueries[index]?.isFetching) {
        ids.add(notebook.id);
      }
    });
    return ids;
  }, [notebooks, sourcesQueries]);

  useEffect(() => {
    if (!open) {
      return;
    }

    setSelections((prev) => {
      let changed = false;
      const next = { ...prev };

      notebooks.forEach((notebook, index) => {
        const sources = sourcesQueries[index]?.data;
        const notes = notesQueries[index]?.data;

        if (!sources && !notes) {
          return;
        }

        if (!next[notebook.id]) {
          next[notebook.id] = { sources: {}, notes: {} };
          changed = true;
        }

        if (sources) {
          const currentSources = next[notebook.id].sources;
          sources.forEach((source) => {
            if (!(source.id in currentSources)) {
              currentSources[source.id] = getSourceDefaultMode(source);
              changed = true;
            }
          });
        }

        if (notes) {
          const currentNotes = next[notebook.id].notes;
          notes.forEach((note) => {
            if (!(note.id in currentNotes)) {
              currentNotes[note.id] = "full";
              changed = true;
            }
          });
        }
      });

      return changed ? next : prev;
    });
  }, [open, notebooks, notesQueries, sourcesQueries]);

  const resetState = useCallback(() => {
    setExpandedNotebooks([]);
    setSelections({});
    setEpisodeProfileId("");
    setEpisodeName("");
    setInstructions("");
    setSelectedDraftId("");
    setTokenCount(0);
    setCharCount(0);
  }, []);

  useEffect(() => {
    if (!open) {
      resetState();
    }
  }, [open, resetState]);

  useEffect(() => {
    if (!open) {
      return;
    }

    const updateContextCounts = async () => {
      const hasAnySelections = Object.values(selections).some(
        (selection) =>
          Object.values(selection.sources).some((mode) => mode !== "off") ||
          Object.values(selection.notes).some((mode) => mode !== "off"),
      );

      if (!hasAnySelections) {
        setTokenCount(0);
        setCharCount(0);
        return;
      }

      try {
        let totalTokens = 0;
        let totalChars = 0;

        for (const [notebookId, selection] of Object.entries(selections)) {
          const contextConfig = buildContextConfig(selection);
          if (
            Object.keys(contextConfig.sources).length === 0 &&
            Object.keys(contextConfig.notes).length === 0
          ) {
            continue;
          }

          const response = await chatApi.buildContext({
            notebook_id: notebookId,
            context_config: contextConfig,
          });

          totalTokens += response.token_count;
          totalChars += response.char_count;
        }

        setTokenCount(totalTokens);
        setCharCount(totalChars);
      } catch (error) {
        appLog.error("generate-podcast-dialog", "Failed to update context counts", error);
      }
    };

    void updateContextCounts();
  }, [open, selections]);

  const selectedEpisodeProfile = useMemo(() => {
    if (!episodeProfileId) {
      return undefined;
    }
    return episodeProfiles.find((profile) => profile.id === episodeProfileId);
  }, [episodeProfileId, episodeProfiles]);

  const availableDrafts = useMemo(() => {
    return notebooks.flatMap((notebook) =>
      (draftsByNotebook[notebook.id] ?? []).map((draft) => ({
        ...draft,
        notebookName: notebook.name,
      })),
    );
  }, [draftsByNotebook, notebooks]);

  const selectedNotebookSummaries = useMemo<NotebookSummary[]>(() => {
    return notebooks.map((notebook) => {
      const selection = selections[notebook.id];
      if (!selection) {
        return { notebookId: notebook.id, sources: 0, notes: 0 };
      }
      const sourcesCount = Object.values(selection.sources).filter((mode) => mode !== "off").length;
      const notesCount = Object.values(selection.notes).filter((mode) => mode !== "off").length;
      return { notebookId: notebook.id, sources: sourcesCount, notes: notesCount };
    });
  }, [notebooks, selections]);

  const handleNotebookToggle = useCallback(
    (notebookId: string, checked: boolean | "indeterminate") => {
      const shouldCheck = checked === "indeterminate" ? true : checked;
      const sources = sourcesByNotebook[notebookId] ?? [];
      const notes = notesByNotebook[notebookId] ?? [];

      setSelections((prev) => {
        if (shouldCheck) {
          const nextSources: Record<string, SourceMode> = {};
          sources.forEach((source) => {
            nextSources[source.id] = getSourceDefaultMode(source);
          });
          const nextNotes: Record<string, SourceMode> = {};
          notes.forEach((note) => {
            nextNotes[note.id] = "full";
          });
          return {
            ...prev,
            [notebookId]: {
              sources: nextSources,
              notes: nextNotes,
            },
          };
        }

        const clearedSources: Record<string, SourceMode> = {};
        sources.forEach((source) => {
          clearedSources[source.id] = "off";
        });
        const clearedNotes: Record<string, SourceMode> = {};
        notes.forEach((note) => {
          clearedNotes[note.id] = "off";
        });

        return {
          ...prev,
          [notebookId]: {
            sources: clearedSources,
            notes: clearedNotes,
          },
        };
      });
    },
    [notesByNotebook, sourcesByNotebook],
  );

  const handleSourceModeChange = useCallback(
    (notebookId: string, sourceId: string, mode: SourceMode) => {
      setSelections((prev) => ({
        ...prev,
        [notebookId]: {
          sources: {
            ...(prev[notebookId]?.sources ?? {}),
            [sourceId]: mode,
          },
          notes: prev[notebookId]?.notes ?? {},
        },
      }));
    },
    [],
  );

  const handleNoteToggle = useCallback(
    (notebookId: string, noteId: string, checked: boolean | "indeterminate") => {
      setSelections((prev) => ({
        ...prev,
        [notebookId]: {
          sources: prev[notebookId]?.sources ?? {},
          notes: {
            ...(prev[notebookId]?.notes ?? {}),
            [noteId]: checked ? "full" : "off",
          },
        },
      }));
    },
    [],
  );

  const buildContentFromSelections = useCallback(async () => {
    const parts: string[] = [];
    const tasks: Array<{ notebookId: string; payload: BuildContextRequest }> = [];

    Object.entries(selections).forEach(([notebookId, selection]) => {
      const contextConfig = buildContextConfig(selection);
      if (
        Object.keys(contextConfig.sources).length === 0 &&
        Object.keys(contextConfig.notes).length === 0
      ) {
        return;
      }

      tasks.push({
        notebookId,
        payload: {
          notebook_id: notebookId,
          context_config: contextConfig,
        },
      });
    });

    if (tasks.length === 0) {
      return "";
    }

    for (const task of tasks) {
      try {
        const response = await chatApi.buildContext(task.payload);
        const notebookName =
          notebooks.find((nb) => nb.id === task.notebookId)?.name ?? task.notebookId;
        const contextString = JSON.stringify(response.context, null, 2);
        const snippet = `${t.common.notebookLabel.replace("{name}", notebookName)}\n${contextString}`;
        parts.push(snippet);
      } catch (error) {
        appLog.error("generate-podcast-dialog", "Failed to build context for notebook", {
          notebookId: task.notebookId,
          error,
        });
        throw new Error(t.podcasts.buildContextFailed);
      }
    }

    return parts.join("\n\n");
  }, [notebooks, selections, t]);

  const handleSubmit = useCallback(async () => {
    if (!selectedEpisodeProfile) {
      toast({
        title: t.podcasts.profileRequired,
        description: t.podcasts.profileRequiredDesc,
        variant: "destructive",
      });
      return;
    }

    if (!episodeName.trim()) {
      toast({
        title: t.podcasts.nameRequired,
        description: t.podcasts.nameRequiredDesc,
        variant: "destructive",
      });
      return;
    }

    setIsBuildingContext(true);
    try {
      let content = "";
      if (!selectedDraftId) {
        content = await buildContentFromSelections();
      }
      if (!selectedDraftId && !content.trim()) {
        toast({
          title: t.podcasts.addContext,
          description: t.podcasts.addContextDesc,
          variant: "destructive",
        });
        return;
      }

      const payload: PodcastGenerationRequest = {
        episode_profile: selectedEpisodeProfile.name,
        speaker_profile: selectedEpisodeProfile.speaker_config,
        episode_name: episodeName.trim(),
        draft_id: selectedDraftId || undefined,
        content: selectedDraftId ? undefined : content,
        briefing_suffix: instructions.trim() ? instructions.trim() : undefined,
      };

      await generatePodcast.mutateAsync(payload);

      toast({
        title: t.common.success,
        description: t.podcasts.podcastTaskStarted,
      });

      setTimeout(() => {
        onOpenChange(false);
        resetState();
      }, 500);
    } catch (error) {
      appLog.error("generate-podcast-dialog", "Failed to generate podcast", error);
      toast({
        title: t.podcasts.generationFailed,
        description: error instanceof Error ? error.message : t.common.refreshPage,
        variant: "destructive",
      });
    } finally {
      setIsBuildingContext(false);
    }
  }, [
    buildContentFromSelections,
    episodeName,
    generatePodcast,
    instructions,
    onOpenChange,
    resetState,
    selectedEpisodeProfile,
    toast,
    t,
  ]);

  const isSubmitting = generatePodcast.isPending || isBuildingContext;

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        onOpenChange(value);
        if (!value) {
          resetState();
        }
      }}
    >
      <DialogContent className="w-[80vw] max-w-[1080px] max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>{t.podcasts.generateEpisode}</DialogTitle>
          <DialogDescription>{t.podcasts.generateEpisodeDesc}</DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 md:grid-cols-[2fr_1fr] xl:grid-cols-[3fr_1fr]">
          <GeneratePodcastContentSelectionPanel
            notebooks={notebooks}
            isLoading={notebooksQuery.isLoading}
            selectedNotebookSummaries={selectedNotebookSummaries}
            tokenCount={tokenCount}
            charCount={charCount}
            expandedNotebooks={expandedNotebooks}
            setExpandedNotebooks={setExpandedNotebooks}
            selections={selections}
            sourcesByNotebook={sourcesByNotebook}
            notesByNotebook={notesByNotebook}
            fetchingNotebookIds={fetchingNotebookIds}
            handleNotebookToggle={handleNotebookToggle}
            handleSourceModeChange={handleSourceModeChange}
            handleNoteToggle={handleNoteToggle}
            queryClient={queryClient}
          />

          <div className="space-y-6">
            <div className="space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                {t.podcasts.episodeSettings}
              </h3>
              {episodeProfilesQuery.isLoading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> {t.podcasts.loadingProfiles}
                </div>
              ) : episodeProfiles.length === 0 ? (
                <div className="rounded-lg border border-dashed bg-muted/30 p-4 text-sm text-muted-foreground">
                  {t.podcasts.noProfilesFound}
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="draft_id">Verified draft (optional)</Label>
                    <Select value={selectedDraftId} onValueChange={setSelectedDraftId}>
                      <SelectTrigger id="draft_id">
                        <SelectValue placeholder="Use live notebook context" />
                      </SelectTrigger>
                      <SelectContent className="z-[140]">
                        <SelectItem value="">Use live notebook context</SelectItem>
                        {availableDrafts.map((draft) => (
                          <SelectItem key={draft.id} value={draft.id}>
                            {draft.title} · {draft.notebookName} · v{draft.version}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {selectedDraftId ? (
                      <p className="text-xs text-muted-foreground">
                        Podcast generation will use the selected draft as the canonical input.
                      </p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="episode_profile">{t.podcasts.episodeProfile}</Label>
                    <Select
                      value={episodeProfileId}
                      onValueChange={setEpisodeProfileId}
                      disabled={episodeProfiles.length === 0}
                    >
                      <SelectTrigger id="episode_profile">
                        <SelectValue placeholder={t.podcasts.episodeProfilePlaceholder} />
                      </SelectTrigger>
                      <SelectContent className="z-[140]">
                        {episodeProfiles.map((profile) => (
                          <SelectItem key={profile.id} value={profile.id}>
                            {profile.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {selectedEpisodeProfile && (
                      <p className="text-xs text-muted-foreground">
                        {t.podcasts.usesSpeakerProfile}{" "}
                        <strong>{selectedEpisodeProfile.speaker_config}</strong>
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="episode_name">{t.podcasts.episodeName}</Label>
                    <Input
                      id="episode_name"
                      name="episode_name"
                      value={episodeName}
                      onChange={(event) => setEpisodeName(event.target.value)}
                      placeholder={t.podcasts.episodeNamePlaceholder}
                      autoComplete="off"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="instructions">{t.podcasts.additionalInstructions}</Label>
                    <Textarea
                      id="instructions"
                      name="instructions"
                      placeholder={t.podcasts.instructionsPlaceholder}
                      value={instructions}
                      onChange={(event) => setInstructions(event.target.value)}
                      className="min-h-[100px] text-xs"
                      autoComplete="off"
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="flex flex-col gap-3">
              <Button onClick={handleSubmit} disabled={isSubmitting} className="w-full">
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isSubmitting ? t.podcasts.generating : t.podcasts.generate}
              </Button>
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
                className="w-full"
              >
                {t.common.cancel}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
