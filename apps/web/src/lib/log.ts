import { getFrontendRunContext } from "@/lib/observability/run-context";

type LogLevel = "debug" | "info" | "warn" | "error";

function normalizePayload(payload: unknown): unknown {
  if (payload instanceof Error) {
    return {
      name: payload.name,
      message: payload.message,
      stack: payload.stack,
    };
  }
  return payload;
}

function emit(level: LogLevel, scope: string, message: string, payload?: unknown): void {
  const writer = console[level] ?? console.log;
  const context = getFrontendRunContext();
  const record = {
    timestamp: new Date().toISOString(),
    level,
    event: message,
    component: `apps/web.${scope}`,
    service: "open-notebook-web",
    domain: "frontend",
    run_id: context.run_id,
    request_id: context.request_id,
    trace_id: context.trace_id,
    user_id: context.user_id,
    test_id: context.test_id,
    artifact_group: context.artifact_group,
    command_id: context.command_id,
    job_kind: context.job_kind,
    source_kind: context.source_kind,
    route: context.route,
    browser_session_id: context.browser_session_id,
    workflow_name: context.workflow_name,
    job_name: context.job_name,
    error_class: payload instanceof Error ? payload.name : "-",
    error_stack: payload instanceof Error ? (payload.stack ?? "-") : "-",
    redaction_version: "v1",
  };

  if (payload === undefined) {
    writer(JSON.stringify(record));
    return;
  }

  writer(JSON.stringify({ ...record, payload: normalizePayload(payload) }));
}

export const appLog = {
  debug(scope: string, message: string, payload?: unknown): void {
    emit("debug", scope, message, payload);
  },
  info(scope: string, message: string, payload?: unknown): void {
    emit("info", scope, message, payload);
  },
  warn(scope: string, message: string, payload?: unknown): void {
    emit("warn", scope, message, payload);
  },
  error(scope: string, message: string, payload?: unknown): void {
    emit("error", scope, message, payload);
  },
};
