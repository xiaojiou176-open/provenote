import { beforeEach, describe, expect, it, vi } from "vitest";

const hoisted = vi.hoisted(() => ({
  apiClientMock: {
    get: vi.fn(),
    put: vi.fn(),
  },
}));

vi.mock("./client", () => ({
  default: hoisted.apiClientMock,
}));

import { settingsApi } from "./settings";

describe("settingsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("gets settings from /settings", async () => {
    hoisted.apiClientMock.get.mockResolvedValue({
      data: {
        default_content_processing_engine_doc: "auto",
        default_content_processing_engine_url: "simple",
      },
    });

    const result = await settingsApi.get();

    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/settings");
    expect(result.default_content_processing_engine_doc).toBe("auto");
    expect(result.default_content_processing_engine_url).toBe("simple");
  });

  it("updates settings through /settings with partial payload", async () => {
    const payload = {
      default_embedding_option: "always",
      auto_delete_files: "no",
    };

    hoisted.apiClientMock.put.mockResolvedValue({ data: payload });

    const result = await settingsApi.update(payload);

    expect(hoisted.apiClientMock.put).toHaveBeenCalledWith("/settings", payload);
    expect(result).toEqual(payload);
  });

  it("propagates update errors", async () => {
    hoisted.apiClientMock.put.mockRejectedValue(new Error("update failed"));

    await expect(settingsApi.update({ auto_delete_files: "yes" })).rejects.toThrow("update failed");
  });
});
