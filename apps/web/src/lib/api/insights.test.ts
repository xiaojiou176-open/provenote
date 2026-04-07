import { beforeEach, describe, expect, it, vi } from "vitest";
import { appLog } from "@/lib/log";

const hoisted = vi.hoisted(() => ({
  apiClientMock: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("./client", () => ({
  default: hoisted.apiClientMock,
}));

vi.mock("@/lib/log", () => ({
  appLog: {
    error: vi.fn(),
    warn: vi.fn(),
  },
}));

import { insightsApi } from "./insights";

describe("insightsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("maps insight CRUD and command status endpoints", async () => {
    hoisted.apiClientMock.get
      .mockResolvedValueOnce({ data: [{ id: "ins-1" }] })
      .mockResolvedValueOnce({ data: { id: "ins-1", content: "summary" } })
      .mockResolvedValueOnce({ data: { job_id: "cmd-1", status: "running" } });
    hoisted.apiClientMock.post.mockResolvedValueOnce({
      data: {
        status: "pending",
        source_id: "src-1",
        transformation_id: "tr-1",
        message: "queued",
      },
    });
    hoisted.apiClientMock.post.mockResolvedValueOnce({
      data: {
        id: "note-1",
        title: "Summary from source Example",
        content: "summary",
        note_type: "ai",
      },
    });
    hoisted.apiClientMock.delete.mockResolvedValueOnce({ data: undefined });

    const list = await insightsApi.listForSource("src-1");
    const detail = await insightsApi.get("ins-1");
    const created = await insightsApi.create("src-1", { transformation_id: "tr-1" });
    const note = await insightsApi.saveAsNote("ins-1", { notebook_id: "notebook:1" });
    await insightsApi.delete("ins-1");
    const status = await insightsApi.getCommandStatus("cmd-1");

    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(1, "/sources/src-1/insights");
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(2, "/insights/ins-1");
    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/sources/src-1/insights", {
      transformation_id: "tr-1",
    });
    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/insights/ins-1/save-as-note", {
      notebook_id: "notebook:1",
    });
    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/insights/ins-1");
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(3, "/commands/jobs/cmd-1");

    expect(list).toEqual([{ id: "ins-1" }]);
    expect(detail.id).toBe("ins-1");
    expect(created.status).toBe("pending");
    expect(note.id).toBe("note-1");
    expect(status.status).toBe("running");
  });

  it("waitForCommand returns true when command reaches completed", async () => {
    const commandSpy = vi
      .spyOn(insightsApi, "getCommandStatus")
      .mockResolvedValueOnce({ job_id: "cmd-2", status: "running" })
      .mockResolvedValueOnce({ job_id: "cmd-2", status: "completed" });

    const result = await insightsApi.waitForCommand("cmd-2", {
      maxAttempts: 3,
      intervalMs: 0,
    });

    expect(result).toBe(true);
    expect(commandSpy).toHaveBeenCalledTimes(2);
  });

  it("waitForCommand returns false for failed status and timeout retries", async () => {
    const failSpy = vi.spyOn(insightsApi, "getCommandStatus").mockResolvedValueOnce({
      job_id: "cmd-3",
      status: "failed",
      error_message: "backend failed",
    });

    const failed = await insightsApi.waitForCommand("cmd-3", { maxAttempts: 3, intervalMs: 0 });

    failSpy.mockReset();
    failSpy.mockRejectedValue(new Error("temporary"));
    const timeout = await insightsApi.waitForCommand("cmd-4", { maxAttempts: 2, intervalMs: 0 });

    expect(failed).toBe(false);
    expect(timeout).toBe(false);
    expect(appLog.error).toHaveBeenCalledWith(
      "insights-api",
      "Command failed while polling insight generation",
      {
        commandId: "cmd-3",
        status: "failed",
        errorMessage: "backend failed",
      },
    );
    expect(appLog.error).toHaveBeenCalledWith("insights-api", "Error checking command status", {
      commandId: "cmd-4",
      error: expect.any(Error),
    });
    expect(appLog.warn).toHaveBeenCalledWith("insights-api", "Command polling timed out", {
      commandId: "cmd-4",
      maxAttempts: 2,
    });
  });
});
