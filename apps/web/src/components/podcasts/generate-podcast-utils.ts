import type { SourceListResponse } from "@/lib/types/api";

export type SourceMode = "off" | "insights" | "full";

export interface NotebookSelection {
  sources: Record<string, SourceMode>;
  notes: Record<string, SourceMode>;
}

export interface NotebookSummary {
  notebookId: string;
  sources: number;
  notes: number;
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

export function hasSelections(selection?: NotebookSelection): boolean {
  if (!selection) {
    return false;
  }
  return (
    Object.values(selection.sources).some((mode) => mode !== "off") ||
    Object.values(selection.notes).some((mode) => mode !== "off")
  );
}

export function getSourceDefaultMode(source: SourceListResponse): SourceMode {
  return source.insights_count && source.insights_count > 0 ? "insights" : "full";
}

export function buildContextConfig(selection: NotebookSelection): {
  sources: Record<string, string>;
  notes: Record<string, string>;
} {
  const sources = Object.entries(selection.sources)
    .filter(([, mode]) => mode !== "off")
    .reduce<Record<string, string>>((acc, [sourceId, mode]) => {
      const normalizedId = sourceId.replace(/^source:/, "");
      acc[normalizedId] = mode === "insights" ? "insights" : "full content";
      return acc;
    }, {});

  const notes = Object.entries(selection.notes)
    .filter(([, mode]) => mode !== "off")
    .reduce<Record<string, string>>((acc, [noteId]) => {
      const normalizedId = noteId.replace(/^note:/, "");
      acc[normalizedId] = "full content";
      return acc;
    }, {});

  return { sources, notes };
}
