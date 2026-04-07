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

import { transformationsApi } from "./transformations";

describe("transformationsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lists and fetches transformation details", async () => {
    hoisted.apiClientMock.get
      .mockResolvedValueOnce({ data: [{ id: "tr-1" }] })
      .mockResolvedValueOnce({ data: { id: "tr-1", name: "summary" } });

    const list = await transformationsApi.list();
    const detail = await transformationsApi.get("tr-1");

    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(1, "/transformations");
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(2, "/transformations/tr-1");
    expect(list).toEqual([{ id: "tr-1" }]);
    expect(detail).toEqual({ id: "tr-1", name: "summary" });
  });

  it("creates and updates transformation payload", async () => {
    hoisted.apiClientMock.post.mockResolvedValueOnce({ data: { id: "tr-2" } });
    hoisted.apiClientMock.put.mockResolvedValueOnce({ data: { id: "tr-2", name: "updated" } });

    const created = await transformationsApi.create({
      name: "summary",
      title: "Summary",
      description: "desc",
      prompt: "prompt",
      apply_default: true,
    });

    const updated = await transformationsApi.update("tr-2", {
      name: "summary-v2",
      prompt: "new prompt",
    });

    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/transformations", {
      name: "summary",
      title: "Summary",
      description: "desc",
      prompt: "prompt",
      apply_default: true,
    });

    expect(hoisted.apiClientMock.put).toHaveBeenCalledWith("/transformations/tr-2", {
      name: "summary-v2",
      prompt: "new prompt",
    });

    expect(created).toEqual({ id: "tr-2" });
    expect(updated).toEqual({ id: "tr-2", name: "updated" });
  });

  it("delete targets the expected endpoint", async () => {
    hoisted.apiClientMock.delete.mockResolvedValue({ data: undefined });

    await transformationsApi.delete("tr-1");

    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/transformations/tr-1");
  });

  it("execute returns response and propagates backend failures", async () => {
    hoisted.apiClientMock.post.mockResolvedValueOnce({ data: { output: "done" } });

    const result = await transformationsApi.execute({
      transformation_id: "tr-1",
      model_id: "model-1",
      input_text: "hello",
    });

    expect(result).toEqual({ output: "done" });
    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/transformations/execute", {
      transformation_id: "tr-1",
      model_id: "model-1",
      input_text: "hello",
    });

    const error = new Error("Transformation not found");
    hoisted.apiClientMock.post.mockRejectedValueOnce(error);

    await expect(
      transformationsApi.execute({
        transformation_id: "tr-missing",
        model_id: "model-1",
        input_text: "hello",
      }),
    ).rejects.toThrow("Transformation not found");
  });

  it("gets and updates default prompt while surfacing failures", async () => {
    hoisted.apiClientMock.get.mockResolvedValueOnce({
      data: { transformation_instructions: "current" },
    });
    hoisted.apiClientMock.put.mockResolvedValueOnce({
      data: { transformation_instructions: "next" },
    });

    const prompt = await transformationsApi.getDefaultPrompt();
    const updated = await transformationsApi.updateDefaultPrompt({
      transformation_instructions: "next",
    });

    expect(prompt).toEqual({ transformation_instructions: "current" });
    expect(updated).toEqual({ transformation_instructions: "next" });
    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/transformations/default-prompt");
    expect(hoisted.apiClientMock.put).toHaveBeenCalledWith("/transformations/default-prompt", {
      transformation_instructions: "next",
    });

    const getError = new Error("default prompt fetch failed");
    hoisted.apiClientMock.get.mockRejectedValueOnce(getError);
    await expect(transformationsApi.getDefaultPrompt()).rejects.toThrow(
      "default prompt fetch failed",
    );

    const putError = new Error("update rejected");
    hoisted.apiClientMock.put.mockRejectedValueOnce(putError);
    await expect(
      transformationsApi.updateDefaultPrompt({ transformation_instructions: "tighten" }),
    ).rejects.toThrow("update rejected");
  });
});
