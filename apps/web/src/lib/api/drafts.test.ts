import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  apiClientMock: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock("./client", () => ({
  default: hoisted.apiClientMock,
}));

import { draftsApi } from "./drafts";

describe("draftsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lists, creates, gets, reruns, verifies, and downloads draft artifacts with expected paths", async () => {
    hoisted.apiClientMock.get
      .mockResolvedValueOnce({ data: [{ id: "draft-1" }] })
      .mockResolvedValueOnce({ data: { id: "draft-1" } })
      .mockResolvedValueOnce({ data: new Blob(["# draft"]) })
      .mockResolvedValueOnce({ data: new Blob(["zip"]) });
    hoisted.apiClientMock.post
      .mockResolvedValueOnce({ data: { id: "draft-2" } })
      .mockResolvedValueOnce({ data: { id: "draft-3" } })
      .mockResolvedValueOnce({ data: { id: "draft-4" } });

    const list = await draftsApi.list("nb-1");
    const created = await draftsApi.create("nb-1", { source_ids: ["source:1"] });
    const detail = await draftsApi.get("draft-1");
    const rerun = await draftsApi.rerun("draft-1", { language: "en-US" });
    const verified = await draftsApi.verify("draft-1");
    await draftsApi.downloadMarkdown("draft-1");
    await draftsApi.downloadBundle("draft-1");

    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(1, "/notebooks/nb-1/drafts");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(1, "/notebooks/nb-1/drafts", {
      source_ids: ["source:1"],
    });
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(2, "/drafts/draft-1");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(2, "/drafts/draft-1/rerun", {
      language: "en-US",
    });
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(3, "/drafts/draft-1/verify");
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(3, "/drafts/draft-1/markdown", {
      responseType: "blob",
    });
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(4, "/drafts/draft-1/bundle", {
      responseType: "blob",
    });
    expect(list).toEqual([{ id: "draft-1" }]);
    expect(created).toEqual({ id: "draft-2" });
    expect(detail).toEqual({ id: "draft-1" });
    expect(rerun).toEqual({ id: "draft-3" });
    expect(verified).toEqual({ id: "draft-4" });
  });
});
