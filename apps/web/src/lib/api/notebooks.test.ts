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

import { notebooksApi } from "./notebooks";

describe("notebooksApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lists notebooks with query params", async () => {
    hoisted.apiClientMock.get.mockResolvedValue({ data: [{ id: "nb-1" }] });

    const result = await notebooksApi.list({ archived: false, order_by: "updated desc" });

    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/notebooks", {
      params: { archived: false, order_by: "updated desc" },
    });
    expect(result).toEqual([{ id: "nb-1" }]);
  });

  it("gets, creates and updates notebook", async () => {
    hoisted.apiClientMock.get.mockResolvedValueOnce({ data: { id: "nb-2" } });
    hoisted.apiClientMock.post.mockResolvedValueOnce({ data: { id: "nb-3" } });
    hoisted.apiClientMock.put.mockResolvedValueOnce({ data: { id: "nb-3", name: "Updated" } });

    const fetched = await notebooksApi.get("nb-2");
    const created = await notebooksApi.create({ name: "Created" });
    const updated = await notebooksApi.update("nb-3", { name: "Updated" });

    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/notebooks/nb-2");
    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/notebooks", { name: "Created" });
    expect(hoisted.apiClientMock.put).toHaveBeenCalledWith("/notebooks/nb-3", {
      name: "Updated",
    });
    expect(fetched.id).toBe("nb-2");
    expect(created.id).toBe("nb-3");
    expect(updated.name).toBe("Updated");
  });

  it("calls delete preview and delete with expected params", async () => {
    hoisted.apiClientMock.get.mockResolvedValueOnce({ data: { can_delete: true } });
    hoisted.apiClientMock.delete.mockResolvedValueOnce({ data: { deleted: true } });

    const preview = await notebooksApi.deletePreview("nb-4");
    const deleted = await notebooksApi.delete("nb-4", true);

    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/notebooks/nb-4/delete-preview");
    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/notebooks/nb-4", {
      params: { delete_exclusive_sources: true },
    });
    expect(preview).toEqual({ can_delete: true });
    expect(deleted).toEqual({ deleted: true });
  });

  it("adds and removes source from notebook", async () => {
    hoisted.apiClientMock.post.mockResolvedValueOnce({ data: { ok: true } });
    hoisted.apiClientMock.delete.mockResolvedValueOnce({ data: { ok: true } });

    const added = await notebooksApi.addSource("nb-5", "source-1");
    const removed = await notebooksApi.removeSource("nb-5", "source-1");

    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/notebooks/nb-5/sources/source-1");
    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/notebooks/nb-5/sources/source-1");
    expect(added).toEqual({ ok: true });
    expect(removed).toEqual({ ok: true });
  });
});
