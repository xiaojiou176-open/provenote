function newId(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return `fallback-${Date.now()}`;
}

const processRunId = `frontend-${newId()}`;

function browserSessionId(): string {
  if (typeof window === "undefined") {
    return processRunId;
  }
  const storageKey = "provenote-frontend-run-id";
  const existing = window.sessionStorage.getItem(storageKey);
  if (existing) {
    return existing;
  }
  window.sessionStorage.setItem(storageKey, processRunId);
  return processRunId;
}

export interface FrontendRunContext {
  run_id: string;
  request_id: string;
  trace_id: string;
  user_id: string;
  test_id: string;
  artifact_group: string;
  command_id: string;
  job_kind: string;
  source_kind: "frontend";
  route: string;
  browser_session_id: string;
  workflow_name: string;
  job_name: string;
}

export function getFrontendRunContext(): FrontendRunContext {
  const route = typeof window !== "undefined" ? window.location.pathname : "server-side";
  return {
    run_id: browserSessionId(),
    request_id: "-",
    trace_id: "-",
    user_id: "-",
    test_id: "-",
    artifact_group: "-",
    command_id: "-",
    job_kind: "-",
    source_kind: "frontend",
    route,
    browser_session_id: browserSessionId(),
    workflow_name: typeof process !== "undefined" ? (process.env.GITHUB_WORKFLOW ?? "-") : "-",
    job_name: typeof process !== "undefined" ? (process.env.GITHUB_JOB ?? "-") : "-",
  };
}
