import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
}));

vi.mock("./client", () => ({
  default: {
    get: hoisted.getMock,
    post: hoisted.postMock,
  },
}));

import { auditableApi } from "./auditable";

describe("auditableApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lists runs for a source", async () => {
    hoisted.getMock.mockResolvedValue({
      data: [{ id: "run-1", status: "completed" }],
    });

    const result = await auditableApi.listRuns("source-1");

    expect(hoisted.getMock).toHaveBeenCalledWith("/sources/source-1/auditable-runs");
    expect(result).toEqual([{ id: "run-1", status: "completed" }]);
  });

  it("starts a run with optional payload", async () => {
    hoisted.postMock.mockResolvedValue({
      data: { id: "run-2", status: "queued" },
    });

    const result = await auditableApi.startRun("source-2", {
      language: "en",
      model_id: "model-1",
    });

    expect(hoisted.postMock).toHaveBeenCalledWith("/sources/source-2/auditable-runs", {
      language: "en",
      model_id: "model-1",
    });
    expect(result).toEqual({ id: "run-2", status: "queued" });
  });

  it("defaults startRun payload to an empty object", async () => {
    hoisted.postMock.mockResolvedValue({
      data: { id: "run-3", status: "queued" },
    });

    await auditableApi.startRun("source-3");

    expect(hoisted.postMock).toHaveBeenCalledWith("/sources/source-3/auditable-runs", {});
  });

  it("gets a single run and downloads markdown as blob response", async () => {
    const blobResponse = { data: new Blob(["markdown"]) };
    hoisted.getMock
      .mockResolvedValueOnce({
        data: { id: "run-4", status: "running" },
      })
      .mockResolvedValueOnce(blobResponse);
    hoisted.postMock
      .mockResolvedValueOnce({ data: { id: "repair-claim" } })
      .mockResolvedValueOnce({ data: { id: "repair-section" } });

    const run = await auditableApi.getRun("run-4");
    const repairedClaim = await auditableApi.repairClaim("run-4", { target_index: 0 });
    const repairedSection = await auditableApi.repairSection("run-4", { target_index: 1 });
    const markdown = await auditableApi.downloadMarkdown("run-4");

    expect(hoisted.getMock).toHaveBeenNthCalledWith(1, "/auditable-runs/run-4");
    expect(hoisted.postMock).toHaveBeenNthCalledWith(1, "/auditable-runs/run-4/repair-claim", {
      target_index: 0,
    });
    expect(hoisted.postMock).toHaveBeenNthCalledWith(2, "/auditable-runs/run-4/repair-section", {
      target_index: 1,
    });
    expect(hoisted.getMock).toHaveBeenNthCalledWith(2, "/auditable-runs/run-4/markdown", {
      responseType: "blob",
    });
    expect(run).toEqual({ id: "run-4", status: "running" });
    expect(repairedClaim).toEqual({ id: "repair-claim" });
    expect(repairedSection).toEqual({ id: "repair-section" });
    expect(markdown).toBe(blobResponse);
  });
});
