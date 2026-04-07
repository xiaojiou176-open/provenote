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

import { credentialsApi } from "./credentials";

describe("credentialsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("maps status/list/get/create/update/test endpoints", async () => {
    hoisted.apiClientMock.get
      .mockResolvedValueOnce({
        data: {
          configured: { google: true },
          source: { google: "database" },
          legacy_env_detected: { google: false },
          encryption_configured: true,
        },
      })
      .mockResolvedValueOnce({ data: [{ id: "cred-1", provider: "google" }] })
      .mockResolvedValueOnce({ data: [{ id: "cred-2", provider: "openai" }] })
      .mockResolvedValueOnce({ data: { id: "cred-1", provider: "google" } });

    hoisted.apiClientMock.post
      .mockResolvedValueOnce({ data: { id: "cred-3", provider: "google" } })
      .mockResolvedValueOnce({ data: { provider: "google", success: true, message: "ok" } });

    hoisted.apiClientMock.put.mockResolvedValueOnce({ data: { id: "cred-1", name: "Updated" } });

    const status = await credentialsApi.getStatus();
    const listWithoutProvider = await credentialsApi.list();
    const listByProvider = await credentialsApi.listByProvider("openai");
    const credential = await credentialsApi.get("cred-1");
    const created = await credentialsApi.create({
      name: "Google prod",
      provider: "google",
      modalities: ["language"],
      api_key: "sk-secret",
    });
    const updated = await credentialsApi.update("cred-1", { name: "Updated" });
    const testResult = await credentialsApi.test("cred-1");

    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(1, "/credentials/status");
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(2, "/credentials", { params: {} });
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(3, "/credentials/by-provider/openai");
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(4, "/credentials/cred-1");

    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(1, "/credentials", {
      name: "Google prod",
      provider: "google",
      modalities: ["language"],
      api_key: "sk-secret",
    });
    expect(hoisted.apiClientMock.put).toHaveBeenCalledWith("/credentials/cred-1", {
      name: "Updated",
    });
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(2, "/credentials/cred-1/test");

    expect(status.encryption_configured).toBe(true);
    expect(listWithoutProvider).toEqual([{ id: "cred-1", provider: "google" }]);
    expect(listByProvider).toEqual([{ id: "cred-2", provider: "openai" }]);
    expect(credential.id).toBe("cred-1");
    expect(created.id).toBe("cred-3");
    expect(updated.name).toBe("Updated");
    expect(testResult.success).toBe(true);
  });

  it("passes delete query params for model deletion and migration", async () => {
    hoisted.apiClientMock.delete.mockResolvedValue({
      data: { message: "ok", deleted_models: 1 },
    });

    const result = await credentialsApi.delete("cred-1", {
      delete_models: true,
      migrate_to: "cred-2",
    });

    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/credentials/cred-1", {
      params: { delete_models: true, migrate_to: "cred-2" },
    });
    expect(result.deleted_models).toBe(1);
  });

  it("uses empty params when deleting without options", async () => {
    hoisted.apiClientMock.delete.mockResolvedValue({
      data: { message: "ok", deleted_models: 0 },
    });

    await credentialsApi.delete("cred-9");

    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/credentials/cred-9", {
      params: {},
    });
  });

  it("propagates discover failures", async () => {
    const error = new Error("provider unavailable");
    hoisted.apiClientMock.post.mockRejectedValue(error);

    await expect(credentialsApi.discover("cred-1")).rejects.toThrow("provider unavailable");
    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/credentials/cred-1/discover");
  });

  it("propagates register model failures with original error message", async () => {
    const error = new Error("register failed");
    hoisted.apiClientMock.post.mockRejectedValue(error);

    await expect(
      credentialsApi.registerModels("cred-1", {
        models: [{ name: "gemini-2.5-pro", provider: "google", model_type: "language" }],
      }),
    ).rejects.toThrow("register failed");

    expect(hoisted.apiClientMock.post).toHaveBeenCalledWith("/credentials/cred-1/register-models", {
      models: [{ name: "gemini-2.5-pro", provider: "google", model_type: "language" }],
    });
  });

  it("sends provider query when listing with filter", async () => {
    hoisted.apiClientMock.get.mockResolvedValue({ data: [] });

    await credentialsApi.list("google");

    expect(hoisted.apiClientMock.get).toHaveBeenCalledWith("/credentials", {
      params: { provider: "google" },
    });
  });
});
