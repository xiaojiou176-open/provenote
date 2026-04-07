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

import { researchThreadsApi } from "./research-threads";

describe("researchThreadsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lists, creates, gets, appends, and creates drafts from research threads with expected paths", async () => {
    hoisted.apiClientMock.get
      .mockResolvedValueOnce({ data: [{ id: "thread-1" }] })
      .mockResolvedValueOnce({ data: { id: "thread-1" } });
    hoisted.apiClientMock.post
      .mockResolvedValueOnce({ data: { id: "thread-2" } })
      .mockResolvedValueOnce({ data: { id: "thread-1", entry_count: 2 } })
      .mockResolvedValueOnce({ data: { id: "draft-3" } });

    const list = await researchThreadsApi.list("nb-1");
    const created = await researchThreadsApi.create("nb-1", { title: "Thread" } as never);
    const detail = await researchThreadsApi.get("thread-1");
    const appended = await researchThreadsApi.append("thread-1", {
      entry_type: "answer_snapshot",
      content: "saved answer",
    });
    const draft = await researchThreadsApi.createDraft("thread-1");

    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(
      1,
      "/notebooks/nb-1/research-threads",
    );
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(
      1,
      "/notebooks/nb-1/research-threads",
      { title: "Thread" },
    );
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(2, "/research-threads/thread-1");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(
      2,
      "/research-threads/thread-1/entries",
      { entry_type: "answer_snapshot", content: "saved answer" },
    );
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(
      3,
      "/research-threads/thread-1/drafts",
    );
    expect(list).toEqual([{ id: "thread-1" }]);
    expect(created).toEqual({ id: "thread-2" });
    expect(detail).toEqual({ id: "thread-1" });
    expect(appended).toEqual({ id: "thread-1", entry_count: 2 });
    expect(draft).toEqual({ id: "draft-3" });
  });
});
