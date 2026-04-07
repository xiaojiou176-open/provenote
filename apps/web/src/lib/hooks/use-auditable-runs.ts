import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

import { auditableApi } from "@/lib/api/auditable";
import { useToast } from "@/lib/hooks/use-toast";
import { useTranslation } from "@/lib/hooks/use-translation";
import type {
  AuditableRunResponse,
  AuditableRunStatus,
  CreateAuditableRunRequest,
} from "@/lib/types/api";
import { getApiErrorMessage } from "@/lib/utils/error-handler";

const ACTIVE_AUDITABLE_STATUSES: ReadonlySet<AuditableRunStatus> = new Set(["queued", "running"]);

export const AUDITABLE_QUERY_KEYS = {
  runs: (sourceId: string) => ["sources", sourceId, "auditable-runs"] as const,
  run: (sourceId: string, runId: string) => ["sources", sourceId, "auditable-runs", runId] as const,
};

function sortRunsByNewest(runs: AuditableRunResponse[]) {
  return [...runs].sort((left, right) => {
    const leftTs = Date.parse(left.updated || left.created || "");
    const rightTs = Date.parse(right.updated || right.created || "");

    if (Number.isNaN(leftTs) && Number.isNaN(rightTs)) {
      return 0;
    }
    if (Number.isNaN(leftTs)) {
      return 1;
    }
    if (Number.isNaN(rightTs)) {
      return -1;
    }

    return rightTs - leftTs;
  });
}

function hasActiveStatus(status?: AuditableRunStatus) {
  return status ? ACTIVE_AUDITABLE_STATUSES.has(status) : false;
}

export function getLatestAuditableRun(runs: AuditableRunResponse[]): AuditableRunResponse | null {
  const [latestRun] = sortRunsByNewest(runs);
  return latestRun ?? null;
}

export function useStartAuditableRun(sourceId: string) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { t } = useTranslation();

  return useMutation({
    mutationFn: (payload?: CreateAuditableRunRequest) => {
      if (!sourceId) {
        throw new Error("Source id is required to start auditable markdown run");
      }
      return auditableApi.startRun(sourceId, payload ?? {});
    },
    onSuccess: (run) => {
      queryClient.invalidateQueries({
        queryKey: AUDITABLE_QUERY_KEYS.runs(sourceId),
      });
      queryClient.invalidateQueries({
        queryKey: AUDITABLE_QUERY_KEYS.run(sourceId, run.id),
      });
      toast({
        title: t.common.success,
        description: "Auditable markdown run started.",
      });
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: getApiErrorMessage(error, (key) => t(key), t.common.error),
        variant: "destructive",
      });
    },
  });
}

export function useAuditableRuns(sourceId: string) {
  const runsQuery = useQuery({
    queryKey: AUDITABLE_QUERY_KEYS.runs(sourceId),
    queryFn: () => auditableApi.listRuns(sourceId),
    enabled: !!sourceId,
    staleTime: 0,
    refetchInterval: (query) => {
      const runs = query.state.data as AuditableRunResponse[] | undefined;
      const latestRun = runs ? getLatestAuditableRun(runs) : null;
      return hasActiveStatus(latestRun?.status) ? 2000 : false;
    },
  });

  const latestListedRun = useMemo(
    () => getLatestAuditableRun(runsQuery.data ?? []),
    [runsQuery.data],
  );

  const latestRunId = latestListedRun?.id ?? "";

  const latestRunQuery = useQuery({
    queryKey: AUDITABLE_QUERY_KEYS.run(sourceId, latestRunId),
    queryFn: () => auditableApi.getRun(latestRunId),
    enabled: !!sourceId && !!latestRunId,
    staleTime: 0,
    refetchInterval: (query) => {
      const run = query.state.data as AuditableRunResponse | undefined;
      return hasActiveStatus(run?.status) ? 2000 : false;
    },
  });

  const startRun = useStartAuditableRun(sourceId);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { t } = useTranslation();

  const repairClaim = useMutation({
    mutationFn: ({ runId, targetIndex }: { runId: string; targetIndex: number }) =>
      auditableApi.repairClaim(runId, { target_index: targetIndex }),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: AUDITABLE_QUERY_KEYS.runs(sourceId) });
      queryClient.invalidateQueries({
        queryKey: AUDITABLE_QUERY_KEYS.run(sourceId, run.id),
      });
      toast({
        title: t.common.success,
        description: "Claim repaired into a new auditable run.",
      });
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: getApiErrorMessage(error, (key) => t(key), t.common.error),
        variant: "destructive",
      });
    },
  });

  const repairSection = useMutation({
    mutationFn: ({ runId, targetIndex }: { runId: string; targetIndex: number }) =>
      auditableApi.repairSection(runId, { target_index: targetIndex }),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: AUDITABLE_QUERY_KEYS.runs(sourceId) });
      queryClient.invalidateQueries({
        queryKey: AUDITABLE_QUERY_KEYS.run(sourceId, run.id),
      });
      toast({
        title: t.common.success,
        description: "Section repaired into a new auditable run.",
      });
    },
    onError: (error: unknown) => {
      toast({
        title: t.common.error,
        description: getApiErrorMessage(error, (key) => t(key), t.common.error),
        variant: "destructive",
      });
    },
  });

  const runs = runsQuery.data ?? [];
  const latestRun = latestRunQuery.data ?? latestListedRun;

  return {
    runs,
    latestRun,
    startRun,
    repairClaim,
    repairSection,
    isLoading: runsQuery.isLoading || latestRunQuery.isLoading,
    isFetching: runsQuery.isFetching || latestRunQuery.isFetching,
    error: runsQuery.error ?? latestRunQuery.error,
    refetchRuns: runsQuery.refetch,
  };
}
