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

import { sourcesApi } from "./sources";

function formDataToObject(formData: FormData): Record<string, string> {
  return Object.fromEntries(
    Array.from(formData.entries()).map(([key, value]) => {
      if (typeof value === "string") {
        return [key, value];
      }
      return [key, value.name];
    }),
  );
}

describe("sourcesApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lists, gets, updates, deletes and checks status", async () => {
    hoisted.apiClientMock.get
      .mockResolvedValueOnce({ data: [{ id: "src-1" }] })
      .mockResolvedValueOnce({ data: { id: "src-1", title: "one" } })
      .mockResolvedValueOnce({ data: { id: "src-1", status: "processing" } });
    hoisted.apiClientMock.put.mockResolvedValue({ data: { id: "src-1", title: "updated" } });
    hoisted.apiClientMock.delete.mockResolvedValue({ data: undefined });

    const listResult = await sourcesApi.list({ notebook_id: "nb-1", limit: 10, offset: 0 });
    const getResult = await sourcesApi.get("src-1");
    const updateResult = await sourcesApi.update("src-1", { title: "updated" });
    await sourcesApi.delete("src-1");
    const statusResult = await sourcesApi.status("src-1");

    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(1, "/sources", {
      params: { notebook_id: "nb-1", limit: 10, offset: 0 },
    });
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(2, "/sources/src-1");
    expect(hoisted.apiClientMock.put).toHaveBeenCalledWith("/sources/src-1", { title: "updated" });
    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/sources/src-1");
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(3, "/sources/src-1/status");
    expect(listResult).toEqual([{ id: "src-1" }]);
    expect(getResult.id).toBe("src-1");
    expect(updateResult.title).toBe("updated");
    expect(statusResult.status).toBe("processing");
  });

  it("creates source payload with FormData and optional fields", async () => {
    hoisted.apiClientMock.post.mockResolvedValue({ data: { id: "src-2" } });
    const file = new File(["hello"], "demo.txt", { type: "text/plain" });

    await sourcesApi.create({
      type: "upload",
      notebooks: ["nb-1"],
      notebook_id: "nb-1",
      title: "title",
      url: "https://example.com",
      content: "body",
      transformations: ["summary"],
      embed: true,
      delete_source: true,
      async_processing: true,
      file,
    });

    const postArgs = hoisted.apiClientMock.post.mock.calls[0];
    expect(postArgs[0]).toBe("/sources");
    const formData = postArgs[1] as FormData;
    const formObject = formDataToObject(formData);
    expect(formObject).toMatchObject({
      type: "upload",
      notebooks: '["nb-1"]',
      notebook_id: "nb-1",
      title: "title",
      url: "https://example.com",
      content: "body",
      transformations: '["summary"]',
      file: "demo.txt",
      embed: "true",
      delete_source: "true",
      async_processing: "true",
    });
  });

  it("uses default boolean values when creating source", async () => {
    hoisted.apiClientMock.post.mockResolvedValue({ data: { id: "src-3" } });

    await sourcesApi.create({
      type: "text",
      content: "minimal",
    });

    const formData = hoisted.apiClientMock.post.mock.calls[0][1] as FormData;
    const formObject = formDataToObject(formData);
    expect(formObject.embed).toBe("false");
    expect(formObject.delete_source).toBe("false");
    expect(formObject.async_processing).toBe("false");
  });

  it("omits file field when payload file is not a File instance", async () => {
    hoisted.apiClientMock.post.mockResolvedValue({ data: { id: "src-no-file" } });

    await sourcesApi.create({
      type: "upload",
      title: "no-file",
      file: { name: "fake-file" } as unknown as File,
    });

    const formData = hoisted.apiClientMock.post.mock.calls[0][1] as FormData;
    const formObject = formDataToObject(formData);

    expect(formObject.type).toBe("upload");
    expect(formObject.file).toBeUndefined();
    expect(formObject.title).toBe("no-file");
  });

  it("uploads source file and sets multipart header", async () => {
    hoisted.apiClientMock.post.mockResolvedValue({ data: { id: "src-4" } });
    const file = new File(["data"], "upload.pdf", { type: "application/pdf" });

    const result = await sourcesApi.upload(file, "nb-2");

    const args = hoisted.apiClientMock.post.mock.calls[0];
    expect(args[0]).toBe("/sources");
    expect(args[2]).toEqual({
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    const formObject = formDataToObject(args[1] as FormData);
    expect(formObject).toMatchObject({
      file: "upload.pdf",
      notebook_id: "nb-2",
      type: "upload",
      async_processing: "true",
    });
    expect(result.id).toBe("src-4");
  });

  it("retries processing and downloads files", async () => {
    const blob = new Blob(["content"], { type: "text/plain" });
    hoisted.apiClientMock.post.mockResolvedValue({ data: { id: "src-5" } });
    hoisted.apiClientMock.get.mockResolvedValue({ data: blob });

    const retryResult = await sourcesApi.retry("src-5");
    const downloadResult = await sourcesApi.downloadFile("src-5");

    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/sources/src-5/retry");
    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/sources/src-5/download", {
      responseType: "blob",
    });
    expect(retryResult.id).toBe("src-5");
    expect(downloadResult.data).toBe(blob);
  });

  it("loads the processing report and reprocesses a source", async () => {
    hoisted.apiClientMock.get.mockResolvedValue({ data: { source_id: "src-6" } });
    hoisted.apiClientMock.post.mockResolvedValue({ data: { id: "src-6" } });

    const report = await sourcesApi.processingReport("src-6");
    const reprocessed = await sourcesApi.reprocess("src-6");

    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/sources/src-6/processing-report");
    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/sources/src-6/reprocess");
    expect(report).toEqual({ source_id: "src-6" });
    expect(reprocessed).toEqual({ id: "src-6" });
  });
});
