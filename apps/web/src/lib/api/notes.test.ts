import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  apiClientMock: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("./client", () => ({
  default: hoisted.apiClientMock,
}));

import { notesApi } from "./notes";

describe("notesApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lists notes with optional notebook filter", async () => {
    hoisted.apiClientMock.get.mockResolvedValue({ data: [{ id: "n-1" }] });

    const result = await notesApi.list({ notebook_id: "nb-1" });

    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/notes", {
      params: { notebook_id: "nb-1" },
    });
    expect(result).toEqual([{ id: "n-1" }]);
  });

  it("gets one note by id", async () => {
    hoisted.apiClientMock.get.mockResolvedValue({ data: { id: "n-2", title: "title" } });

    const result = await notesApi.get("n-2");

    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/notes/n-2");
    expect(result).toEqual({ id: "n-2", title: "title" });
  });

  it("creates and updates notes", async () => {
    hoisted.apiClientMock.post.mockResolvedValueOnce({ data: { id: "n-3", title: "created" } });
    hoisted.apiClientMock.put.mockResolvedValueOnce({ data: { id: "n-3", title: "updated" } });

    const created = await notesApi.create({
      notebook_id: "nb-1",
      title: "created",
      content: "body",
    });
    const updated = await notesApi.update("n-3", {
      title: "updated",
      content: "body 2",
    });

    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/notes", {
      notebook_id: "nb-1",
      title: "created",
      content: "body",
    });
    expect(hoisted.apiClientMock.put).toHaveBeenCalledWith("/notes/n-3", {
      title: "updated",
      content: "body 2",
    });
    expect(created.id).toBe("n-3");
    expect(updated.title).toBe("updated");
  });

  it("deletes note by id", async () => {
    hoisted.apiClientMock.delete.mockResolvedValue({ data: undefined });

    await notesApi.delete("n-4");

    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/notes/n-4");
  });
});
