"use client";

import {
  AlertCircle,
  ChevronDown,
  MessageCircleQuestion,
  Save,
  Search,
  Settings,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import { type CSSProperties, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { AppShell } from "@/components/layout/AppShell";
import { AdvancedModelsDialog } from "@/components/search/AdvancedModelsDialog";
import { ResearchCapturePanel } from "@/components/search/ResearchCapturePanel";
import { SaveToResearchThreadDialog } from "@/components/search/SaveToResearchThreadDialog";
import { StreamingResponse } from "@/components/search/StreamingResponse";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useAsk } from "@/lib/hooks/use-ask";
import { useModalManager } from "@/lib/hooks/use-modal-manager";
import { useModelDefaults, useModels } from "@/lib/hooks/use-models";
import { useSearch } from "@/lib/hooks/use-search";
import { useTranslation } from "@/lib/hooks/use-translation";
import { appLog } from "@/lib/log";
import { parseSourceReferences } from "@/lib/utils/source-references";

export default function SearchPage() {
  const { t } = useTranslation();
  // URL params
  const searchParams = useSearchParams();
  const urlQuery = searchParams?.get("q") || "";
  const rawMode = searchParams?.get("mode");
  const urlMode = rawMode === "search" ? "search" : "ask";
  const shouldAutoTrigger = searchParams?.get("autostart") !== "0";
  const seededSourceId = searchParams?.get("source") || "";
  const seededNotebookId = searchParams?.get("notebook") || "";

  // Tab state (controlled)
  const [activeTab, setActiveTab] = useState<"ask" | "search">(
    urlMode === "search" ? "search" : "ask",
  );

  // Search state
  const [searchQuery, setSearchQuery] = useState(urlMode === "search" ? urlQuery : "");
  const [searchType, setSearchType] = useState<"text" | "vector">("text");
  const [searchSources, setSearchSources] = useState(true);
  const [searchNotes, setSearchNotes] = useState(true);

  // Ask state
  const [askQuestion, setAskQuestion] = useState(urlMode === "ask" ? urlQuery : "");

  // Advanced models dialog
  const [showAdvancedModels, setShowAdvancedModels] = useState(false);
  const [customModels, setCustomModels] = useState<{
    strategy: string;
    answer: string;
    finalAnswer: string;
  } | null>(null);

  // Save to notebooks dialog
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveDialogMode, setSaveDialogMode] = useState<"ask" | "search">("ask");

  // Hooks
  const searchMutation = useSearch();
  const ask = useAsk();
  const { data: modelDefaults, isLoading: modelsLoading } = useModelDefaults();
  const { data: availableModels } = useModels();
  const { openModal } = useModalManager();

  const modelNameById = useMemo(() => {
    if (!availableModels) {
      return new Map<string, string>();
    }
    return new Map(availableModels.map((model) => [model.id, model.name]));
  }, [availableModels]);

  const resolveModelName = (id?: string | null) => {
    if (!id) {
      return t.searchPage.notSet;
    }
    return modelNameById.get(id) ?? id;
  };

  const hasEmbeddingModel = !!modelDefaults?.default_embedding_model;

  // Track if we've already auto-triggered from URL params
  const hasAutoTriggeredRef = useRef(false);
  const hasInitializedUrlSyncRef = useRef(false);
  const lastUrlParamsRef = useRef({ q: urlQuery, mode: urlMode });
  const isSearchComposingRef = useRef(false);

  const handleSearch = useCallback(() => {
    if (!searchQuery.trim()) {
      return;
    }

    searchMutation.mutate({
      query: searchQuery,
      type: searchType,
      limit: 100,
      search_sources: searchSources,
      search_notes: searchNotes,
      minimum_score: 0.2,
    });
  }, [searchQuery, searchType, searchSources, searchNotes, searchMutation]);

  const handleSearchInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") {
      return;
    }
    if (e.nativeEvent.isComposing || isSearchComposingRef.current) {
      return;
    }
    e.preventDefault();
    handleSearch();
  };

  const handleAsk = useCallback(() => {
    if (!askQuestion.trim() || !modelDefaults?.default_chat_model) {
      return;
    }

    const models = customModels || {
      strategy: modelDefaults.default_chat_model,
      answer: modelDefaults.default_chat_model,
      finalAnswer: modelDefaults.default_chat_model,
    };

    ask.sendAsk(askQuestion, models);
  }, [askQuestion, modelDefaults, customModels, ask]);

  // Auto-trigger search/ask when arriving with URL params
  useEffect(() => {
    // Skip if already triggered or no query
    if (hasAutoTriggeredRef.current || !urlQuery || !shouldAutoTrigger) {
      return;
    }

    // Wait for models to load before triggering ask
    if (urlMode === "ask" && modelsLoading) {
      return;
    }

    if (urlMode === "search") {
      handleSearch();
      hasAutoTriggeredRef.current = true;
    } else if (urlMode === "ask" && modelDefaults?.default_chat_model) {
      handleAsk();
      hasAutoTriggeredRef.current = true;
    }
  }, [urlQuery, urlMode, shouldAutoTrigger, modelsLoading, modelDefaults, handleSearch, handleAsk]);

  // Handle URL param changes while on page (e.g., from command palette again)
  useEffect(() => {
    if (!hasInitializedUrlSyncRef.current) {
      hasInitializedUrlSyncRef.current = true;
      return;
    }

    const currentQ = searchParams?.get("q") || "";
    const rawCurrentMode = searchParams?.get("mode");
    const currentMode = rawCurrentMode === "search" ? "search" : "ask";

    // Check if URL params have changed
    if (currentQ !== lastUrlParamsRef.current.q || currentMode !== lastUrlParamsRef.current.mode) {
      lastUrlParamsRef.current = { q: currentQ, mode: currentMode };

      if (currentQ) {
        // Update state based on mode
        if (currentMode === "search") {
          setSearchQuery(currentQ);
          setActiveTab("search");
          // Reset trigger flag so we auto-trigger with new params
          hasAutoTriggeredRef.current = false;
        } else {
          setAskQuestion(currentQ);
          setActiveTab("ask");
          hasAutoTriggeredRef.current = false;
        }
      }
    }
  }, [searchParams]);

  const searchResultsCountLabel = (count: number) =>
    t.searchPage.resultsFound.replace("{count}", count.toString());

  const askReferenceSummary = useMemo(() => {
    const references = parseSourceReferences(ask.finalAnswer ?? "");
    return {
      sourceIds: [
        ...new Set(
          [
            ...references.filter((ref) => ref.type === "source").map((ref) => `source:${ref.id}`),
            ...(seededSourceId ? [seededSourceId] : []),
          ].filter(Boolean),
        ),
      ],
      noteIds: [
        ...new Set(references.filter((ref) => ref.type === "note").map((ref) => `note:${ref.id}`)),
      ],
    };
  }, [ask.finalAnswer, seededSourceId]);

  const searchReferenceSummary = useMemo(() => {
    const results = searchMutation.data?.results ?? [];
    const sourceIds = [
      ...new Set(
        results
          .map((result) => result.parent_id)
          .filter((parentId): parentId is string => Boolean(parentId?.startsWith("source:"))),
      ),
    ];
    const noteIds = [
      ...new Set(
        results
          .map((result) => result.parent_id)
          .filter((parentId): parentId is string => Boolean(parentId?.startsWith("note:"))),
      ),
    ];
    return { sourceIds, noteIds };
  }, [searchMutation.data?.results]);

  const askHasCompletedResult = !ask.isStreaming && Boolean(ask.finalAnswer?.trim());
  const searchHasCompletedResult =
    !searchMutation.isPending && (searchMutation.data?.results.length ?? 0) > 0;
  const showResearchCapture =
    activeTab === "ask"
      ? askHasCompletedResult || Boolean(seededNotebookId)
      : searchHasCompletedResult;

  return (
    <AppShell>
      <div className="ui-page-shell space-y-6 p-4 md:p-6">
        <section className="ui-section-enter" style={{ "--enter-index": 0 } as CSSProperties}>
          <div className="ui-workbench-hero rounded-[1.5rem] p-6 md:p-8">
            <div className="ui-workbench-grid xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)] xl:items-start">
              <div className="space-y-4">
                <span className="ui-workbench-kicker">{t.searchPage.chooseAMode}</span>
                <div className="space-y-3">
                  <h1 className="ui-page-title">{t.searchPage.askAndSearch}</h1>
                  <p className="ui-page-lede">{t.searchPage.askYourKbDesc}</p>
                </div>
              </div>

              <div className="ui-metric-grid">
                <div className="ui-metric-card">
                  <p className="ui-metric-label">{t.searchPage.askBeta}</p>
                  <p className="mt-3 text-base font-semibold">{t.searchPage.askYourKb}</p>
                  <p className="ui-metric-detail">{t.searchPage.askYourKbDesc}</p>
                </div>
                <div className="ui-metric-card">
                  <p className="ui-metric-label">{t.searchPage.search}</p>
                  <p className="mt-3 text-base font-semibold">{t.searchPage.searchType}</p>
                  <p className="ui-metric-detail">{t.searchPage.searchDesc}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <Tabs
          value={activeTab}
          onValueChange={(v) => setActiveTab(v as "ask" | "search")}
          className="ui-section-enter w-full space-y-6"
        >
          <div className="ui-toolbar-surface space-y-3 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {t.searchPage.chooseAMode}
            </p>
            <TabsList aria-label={t.common.accessibility.searchKB} className="w-full max-w-xl">
              <TabsTrigger value="ask">
                <MessageCircleQuestion className="h-4 w-4" />
                {t.searchPage.askBeta}
              </TabsTrigger>
              <TabsTrigger value="search">
                <Search className="h-4 w-4" />
                {t.searchPage.search}
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="ask" className="mt-6">
            <Card className="ui-elevated-panel shadow-none">
              <CardHeader>
                <CardTitle className="font-serif text-[1.6rem] leading-none tracking-[-0.03em]">
                  {t.searchPage.askYourKb}
                </CardTitle>
                <p className="text-sm text-muted-foreground">{t.searchPage.askYourKbDesc}</p>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Question Input */}
                <div className="space-y-2">
                  <Label htmlFor="ask-question">{t.searchPage.question}</Label>
                  <Textarea
                    id="ask-question"
                    name="ask-question"
                    placeholder={t.searchPage.enterQuestionPlaceholder}
                    value={askQuestion}
                    onChange={(e) => setAskQuestion(e.target.value)}
                    onKeyDown={(e) => {
                      // Submit on Cmd/Ctrl+Enter
                      if (
                        (e.metaKey || e.ctrlKey) &&
                        e.key === "Enter" &&
                        !ask.isStreaming &&
                        askQuestion.trim()
                      ) {
                        e.preventDefault();
                        handleAsk();
                      }
                    }}
                    disabled={ask.isStreaming}
                    rows={3}
                    aria-label={t.common.accessibility.enterQuestion}
                  />
                  <p className="text-xs text-muted-foreground">{t.searchPage.pressToSubmit}</p>
                </div>

                {/* Models Display */}
                {!hasEmbeddingModel ? (
                  <div className="ui-status-note-info flex items-center gap-2 rounded-md border p-3 text-sm">
                    <AlertCircle className="h-4 w-4" />
                    <span className="ui-status-note-info-text">
                      {t.searchPage.noEmbeddingModel}
                    </span>
                  </div>
                ) : (
                  <>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-xs text-muted-foreground">
                          {customModels
                            ? t.searchPage.usingCustomModels
                            : t.searchPage.usingDefaultModels}
                        </Label>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setShowAdvancedModels(true)}
                          disabled={ask.isStreaming}
                          className="ui-icon-button h-auto rounded-xl px-2 py-1"
                        >
                          <Settings className="h-3 w-3 mr-1" />
                          {t.searchPage.advanced}
                        </Button>
                      </div>
                      <div className="flex gap-2 text-xs flex-wrap">
                        <Badge variant="secondary">
                          {t.searchPage.strategy}:{" "}
                          {resolveModelName(
                            customModels?.strategy || modelDefaults?.default_chat_model,
                          )}
                        </Badge>
                        <Badge variant="secondary">
                          {t.searchPage.answer}:{" "}
                          {resolveModelName(
                            customModels?.answer || modelDefaults?.default_chat_model,
                          )}
                        </Badge>
                        <Badge variant="secondary">
                          {t.searchPage.final}:{" "}
                          {resolveModelName(
                            customModels?.finalAnswer || modelDefaults?.default_chat_model,
                          )}
                        </Badge>
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-2">
                      <Button
                        onClick={handleAsk}
                        disabled={ask.isStreaming || !askQuestion.trim()}
                        className="ui-primary-cta w-full"
                      >
                        {ask.isStreaming ? (
                          <>
                            <LoadingSpinner size="sm" className="mr-2" />
                            {t.searchPage.processing}
                          </>
                        ) : (
                          t.searchPage.ask
                        )}
                      </Button>

                      {ask.isStreaming && (
                        <Button
                          variant="outline"
                          onClick={ask.cancel}
                          className="w-full rounded-2xl sm:w-auto"
                        >
                          {t.common.cancel}
                        </Button>
                      )}

                      {ask.finalAnswer && (
                        <Button
                          variant="outline"
                          onClick={() => {
                            setSaveDialogMode("ask");
                            setShowSaveDialog(true);
                          }}
                          className="w-full rounded-2xl"
                        >
                          <Save className="h-4 w-4 mr-2" />
                          {t.searchPage.saveToResearchThreadTitle}
                        </Button>
                      )}
                    </div>
                  </>
                )}

                {/* Streaming Response */}
                <StreamingResponse
                  isStreaming={ask.isStreaming}
                  strategy={ask.strategy}
                  answers={ask.answers}
                  finalAnswer={ask.finalAnswer}
                />

                {/* Advanced Models Dialog */}
                <AdvancedModelsDialog
                  open={showAdvancedModels}
                  onOpenChange={setShowAdvancedModels}
                  defaultModels={{
                    strategy: customModels?.strategy || modelDefaults?.default_chat_model || "",
                    answer: customModels?.answer || modelDefaults?.default_chat_model || "",
                    finalAnswer:
                      customModels?.finalAnswer || modelDefaults?.default_chat_model || "",
                  }}
                  onSave={setCustomModels}
                />

                {/* Save to Research Thread Dialog */}
                {saveDialogMode === "ask" && ask.finalAnswer && (
                  <SaveToResearchThreadDialog
                    open={showSaveDialog}
                    onOpenChange={setShowSaveDialog}
                    mode={saveDialogMode}
                    defaultTitle={askQuestion || t.searchPage.capturedAskThreadFallback}
                    defaultNotebookIds={seededNotebookId ? [seededNotebookId] : []}
                    question={askQuestion}
                    answer={ask.finalAnswer}
                    sourceIds={askReferenceSummary.sourceIds}
                    noteIds={askReferenceSummary.noteIds}
                  />
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="search" className="mt-6">
            <Card className="ui-elevated-panel shadow-none">
              <CardHeader>
                <CardTitle className="font-serif text-[1.6rem] leading-none tracking-[-0.03em]">
                  {t.searchPage.search}
                </CardTitle>
                <p className="text-sm text-muted-foreground">{t.searchPage.searchDesc}</p>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Search Input */}
                <div className="space-y-2">
                  <Label htmlFor="search-query" className="sr-only">
                    {t.searchPage.search}
                  </Label>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <Input
                      id="search-query"
                      name="search-query"
                      placeholder={t.searchPage.enterSearchPlaceholder}
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={handleSearchInputKeyDown}
                      onCompositionStart={() => {
                        isSearchComposingRef.current = true;
                      }}
                      onCompositionEnd={() => {
                        isSearchComposingRef.current = false;
                      }}
                      disabled={searchMutation.isPending}
                      className="flex-1 rounded-2xl border-border/80 bg-card/90"
                      aria-label={t.common.accessibility.enterSearch}
                      autoComplete="off"
                    />
                    <Button
                      onClick={handleSearch}
                      disabled={searchMutation.isPending || !searchQuery.trim()}
                      aria-busy={searchMutation.isPending}
                      aria-label={t.common.accessibility.searchKBBtn}
                      className="ui-primary-cta w-full sm:w-auto"
                    >
                      {searchMutation.isPending ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <Search className="h-4 w-4 mr-2" />
                      )}
                      {t.searchPage.search}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">{t.searchPage.pressToSearch}</p>
                </div>

                {/* Search Options */}
                <div className="space-y-4">
                  {/* Search Type */}
                  <div className="space-y-2" role="group" aria-labelledby="search-type-label">
                    <span id="search-type-label" className="text-sm font-medium leading-none">
                      {t.searchPage.searchType}
                    </span>
                    {!hasEmbeddingModel && (
                      <div className="flex items-center gap-2 text-sm text-amber-900 dark:text-amber-300">
                        <AlertCircle className="h-4 w-4" />
                        <span>{t.searchPage.vectorSearchWarning}</span>
                      </div>
                    )}
                    <RadioGroup
                      name="search-type"
                      value={searchType}
                      onValueChange={(value: "text" | "vector") => setSearchType(value)}
                      disabled={modelsLoading || searchMutation.isPending}
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="text" id="text" />
                        <Label htmlFor="text" className="font-normal cursor-pointer">
                          {t.searchPage.textSearch}
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem
                          value="vector"
                          id="vector"
                          disabled={!hasEmbeddingModel || searchMutation.isPending}
                        />
                        <Label
                          htmlFor="vector"
                          className={`font-normal ${!hasEmbeddingModel ? "text-muted-foreground cursor-not-allowed" : "cursor-pointer"}`}
                        >
                          {t.searchPage.vectorSearch}
                        </Label>
                      </div>
                    </RadioGroup>
                  </div>

                  {/* Search Locations */}
                  <div className="space-y-2" role="group" aria-labelledby="search-in-label">
                    <span id="search-in-label" className="text-sm font-medium leading-none">
                      {t.searchPage.searchIn}
                    </span>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="sources"
                          name="sources"
                          checked={searchSources}
                          onCheckedChange={(checked) => setSearchSources(checked as boolean)}
                          disabled={searchMutation.isPending}
                        />
                        <Label htmlFor="sources" className="font-normal cursor-pointer">
                          {t.searchPage.searchSources}
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="notes"
                          name="notes"
                          checked={searchNotes}
                          onCheckedChange={(checked) => setSearchNotes(checked as boolean)}
                          disabled={searchMutation.isPending}
                        />
                        <Label htmlFor="notes" className="font-normal cursor-pointer">
                          {t.searchPage.searchNotes}
                        </Label>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Search Results */}
                {searchMutation.data && (
                  <div className="mt-6 space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-medium">
                        {searchResultsCountLabel(searchMutation.data.total_count)}
                      </h3>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">
                          {searchMutation.data.search_type === "text"
                            ? t.searchPage.textSearch
                            : t.searchPage.vectorSearch}
                        </Badge>
                        <Button
                          variant="outline"
                          size="sm"
                          className="rounded-2xl"
                          onClick={() => {
                            setSaveDialogMode("search");
                            setShowSaveDialog(true);
                          }}
                        >
                          <Save className="mr-2 h-4 w-4" />
                          {t.searchPage.saveToResearchThreadTitle}
                        </Button>
                      </div>
                    </div>

                    {searchMutation.data.results.length === 0 ? (
                      <Card className="ui-elevated-panel shadow-none">
                        <CardContent className="pt-6 text-center text-muted-foreground">
                          {t.searchPage.noResultsFor.replace("{query}", searchQuery)}
                        </CardContent>
                      </Card>
                    ) : (
                      <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-2">
                        {searchMutation.data.results.map((result, index) => {
                          // Parse type from parent_id (format: "source:id" or "note:id" or "source_insight:id")
                          // Handle null parent_id gracefully (orphaned records)
                          if (!result.parent_id) {
                            appLog.warn("search-page", "Search result returned null parent_id", {
                              result,
                            });
                            return null;
                          }
                          const [type, id] = result.parent_id.split(":");
                          const modalType =
                            type === "source_insight"
                              ? "insight"
                              : (type as "source" | "note" | "insight");

                          return (
                            <Card key={index} className="ui-card-surface">
                              <CardContent className="pt-4">
                                <div className="flex items-start justify-between gap-4">
                                  <div className="flex-1">
                                    <button
                                      onClick={() => openModal(modalType, id)}
                                      className="ui-inline-action text-primary hover:underline font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 rounded-sm"
                                    >
                                      {result.title}
                                    </button>
                                    {result.final_score > 0 ? (
                                      <Badge variant="secondary" className="ml-2">
                                        {result.final_score.toFixed(2)}
                                      </Badge>
                                    ) : null}
                                  </div>
                                </div>

                                {result.matches && result.matches.length > 0 && (
                                  <Collapsible className="mt-3">
                                    <div className="rounded-md border border-border/60 bg-muted/30 px-3 py-2 text-sm text-foreground">
                                      {result.matches[0]}
                                    </div>
                                    <CollapsibleTrigger className="ui-inline-action group flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
                                      <ChevronDown className="h-4 w-4 transition-transform duration-200 group-data-[state=open]:rotate-180" />
                                      {t.searchPage.matches.replace(
                                        "{count}",
                                        result.matches.length.toString(),
                                      )}
                                    </CollapsibleTrigger>
                                    <CollapsibleContent className="mt-2 space-y-1">
                                      {result.matches.map((match, i) => (
                                        <div
                                          key={i}
                                          className="text-sm pl-6 py-1 border-l-2 border-muted"
                                        >
                                          {match}
                                        </div>
                                      ))}
                                    </CollapsibleContent>
                                  </Collapsible>
                                )}
                              </CardContent>
                            </Card>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          {showResearchCapture ? (
            <div className="ui-elevated-panel rounded-[1.4rem] border-dashed bg-muted/10 p-1 shadow-none">
              <ResearchCapturePanel
                mode={activeTab}
                query={activeTab === "ask" ? askQuestion : searchQuery}
                answer={activeTab === "ask" ? ask.finalAnswer : null}
                searchResults={activeTab === "search" ? (searchMutation.data?.results ?? []) : []}
                defaultNotebookId={activeTab === "ask" ? seededNotebookId : ""}
                sourceIds={
                  activeTab === "ask"
                    ? askReferenceSummary.sourceIds
                    : searchReferenceSummary.sourceIds
                }
                noteIds={
                  activeTab === "ask" ? askReferenceSummary.noteIds : searchReferenceSummary.noteIds
                }
                hasCompletedResult={
                  activeTab === "ask" ? askHasCompletedResult : searchHasCompletedResult
                }
              />
            </div>
          ) : null}
        </Tabs>
        {saveDialogMode === "search" && searchMutation.data ? (
          <SaveToResearchThreadDialog
            open={showSaveDialog}
            onOpenChange={setShowSaveDialog}
            mode="search"
            defaultTitle={searchQuery || t.searchPage.capturedSearchThreadFallback}
            question={searchQuery}
            searchResults={searchMutation.data.results}
            sourceIds={searchReferenceSummary.sourceIds}
            noteIds={searchReferenceSummary.noteIds}
          />
        ) : null}
      </div>
    </AppShell>
  );
}
