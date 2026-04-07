import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  sessionStorage.clear();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  delete process.env.GITHUB_WORKFLOW;
  delete process.env.GITHUB_JOB;
  vi.resetModules();
});

describe("frontend run context + logger", () => {
  it("falls back to a deterministic server-side run id when randomUUID is unavailable", async () => {
    vi.stubGlobal("window", undefined);
    vi.stubGlobal("crypto", {} as Crypto);
    vi.spyOn(Date, "now").mockReturnValue(1234567890);

    const { getFrontendRunContext } = await import("./observability/run-context");

    const context = getFrontendRunContext();
    expect(context.run_id).toBe("frontend-fallback-1234567890");
    expect(context.browser_session_id).toBe("frontend-fallback-1234567890");
    expect(context.route).toBe("server-side");
  });

  it("emits structured debug records with the current frontend run context", async () => {
    sessionStorage.clear();
    vi.stubGlobal("crypto", {
      randomUUID: vi.fn(() => "debug-run-id"),
    } as Crypto);
    const debugSpy = vi.spyOn(console, "debug").mockImplementation(() => {});

    const { appLog } = await import("./log");

    appLog.debug("source.content", "debug-event", { sample: true });

    expect(debugSpy).toHaveBeenCalledTimes(1);
    const record = JSON.parse(String(debugSpy.mock.calls[0][0])) as Record<string, unknown>;

    expect(record.component).toBe("apps/web.source.content");
    expect(record.event).toBe("debug-event");
    expect(record.level).toBe("debug");
    expect(record.run_id).toBe("frontend-debug-run-id");
    expect(record.browser_session_id).toBe("frontend-debug-run-id");
    expect(record.route).toBe("/");
    expect(record.payload).toEqual({ sample: true });
  });

  it("includes workflow metadata and serialized errors in error logs", async () => {
    vi.stubGlobal("window", undefined);
    vi.stubGlobal("crypto", {
      randomUUID: vi.fn(() => "error-run-id"),
    } as Crypto);
    process.env.GITHUB_WORKFLOW = "frontend-tests";
    process.env.GITHUB_JOB = "coverage";

    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const { appLog } = await import("./log");
    const error = new Error("boom");

    appLog.error("source.content", "error-event", error);

    expect(errorSpy).toHaveBeenCalledTimes(1);
    const record = JSON.parse(String(errorSpy.mock.calls[0][0])) as Record<string, unknown>;

    expect(record.workflow_name).toBe("frontend-tests");
    expect(record.job_name).toBe("coverage");
    expect(record.error_class).toBe("Error");
    expect(String(record.error_stack)).toContain("boom");
    expect(record.payload).toMatchObject({
      name: "Error",
      message: "boom",
    });
  });
});
