import type { ResearchThreadResponse } from "@/lib/types/api";

const SEED_KIND_PRIORITY: Record<ResearchThreadResponse["seed_kind"], number> = {
  insight: 3,
  ask: 2,
  notebook_chat: 1,
  search: 0,
};

function getUpdatedTime(thread: ResearchThreadResponse) {
  const timestamp = Date.parse(thread.updated);
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

export function compareResearchThreadsForDraftSeed(
  left: ResearchThreadResponse,
  right: ResearchThreadResponse,
) {
  if (left.entry_count !== right.entry_count) {
    return right.entry_count - left.entry_count;
  }

  if (left.source_ids.length !== right.source_ids.length) {
    return right.source_ids.length - left.source_ids.length;
  }

  if (left.note_ids.length !== right.note_ids.length) {
    return right.note_ids.length - left.note_ids.length;
  }

  if (left.seed_kind !== right.seed_kind) {
    return SEED_KIND_PRIORITY[right.seed_kind] - SEED_KIND_PRIORITY[left.seed_kind];
  }

  return getUpdatedTime(right) - getUpdatedTime(left);
}

export function getRecommendedResearchThread(threads: ResearchThreadResponse[]) {
  if (threads.length === 0) {
    return null;
  }

  return [...threads].sort(compareResearchThreadsForDraftSeed)[0] ?? null;
}
