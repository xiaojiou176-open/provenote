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

import { modelsApi } from "./models";

describe("modelsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("handles base CRUD and defaults endpoints", async () => {
    hoisted.apiClientMock.get
      .mockResolvedValueOnce({ data: [{ id: "m-1" }] })
      .mockResolvedValueOnce({ data: { id: "m-2" } })
      .mockResolvedValueOnce({ data: { default_chat_model: "m-1" } })
      .mockResolvedValueOnce({ data: { google: true } });
    hoisted.apiClientMock.post.mockResolvedValueOnce({ data: { id: "m-3" } });
    hoisted.apiClientMock.put.mockResolvedValueOnce({ data: { default_chat_model: "m-2" } });
    hoisted.apiClientMock.delete.mockResolvedValueOnce({ data: undefined });

    const list = await modelsApi.list();
    const model = await modelsApi.get("m-2");
    const created = await modelsApi.create({
      name: "gemini-pro",
      provider: "google",
      model_type: "language",
      model_name: "gemini-3.1-pro",
      credential_id: "cred-1",
    });
    await modelsApi.delete("m-3");
    const defaults = await modelsApi.getDefaults();
    const updatedDefaults = await modelsApi.updateDefaults({ default_chat_model: "m-2" });
    const providers = await modelsApi.getProviders();

    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(1, "/models");
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(2, "/models/m-2");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(1, "/models", {
      name: "gemini-pro",
      provider: "google",
      model_type: "language",
      model_name: "gemini-3.1-pro",
      credential_id: "cred-1",
    });
    expect(hoisted.apiClientMock.delete).toHaveBeenCalledWith("/models/m-3");
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(3, "/models/defaults");
    expect(hoisted.apiClientMock.put).toHaveBeenCalledWith("/models/defaults", {
      default_chat_model: "m-2",
    });
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(4, "/models/providers");

    expect(list).toEqual([{ id: "m-1" }]);
    expect(model.id).toBe("m-2");
    expect(created.id).toBe("m-3");
    expect(defaults.default_chat_model).toBe("m-1");
    expect(updatedDefaults.default_chat_model).toBe("m-2");
    expect(providers.google).toBe(true);
  });

  it("maps discovery, sync, provider and test endpoints", async () => {
    hoisted.apiClientMock.get
      .mockResolvedValueOnce({ data: [{ model_name: "gemini-3.1-pro" }] })
      .mockResolvedValueOnce({ data: { count: 2 } })
      .mockResolvedValueOnce({ data: [{ id: "m-7" }] });
    hoisted.apiClientMock.post
      .mockResolvedValueOnce({ data: { provider: "google", synced: 2 } })
      .mockResolvedValueOnce({ data: { providers: { google: 2 } } })
      .mockResolvedValueOnce({ data: { assigned: { chat: "m-7" }, missing: [] } })
      .mockResolvedValueOnce({ data: { success: true, message: "ok" } });

    const discovered = await modelsApi.discoverModels("google");
    const providerSync = await modelsApi.syncProvider("google");
    const allSync = await modelsApi.syncAll();
    const providerCount = await modelsApi.getProviderModelCount("google");
    const providerModels = await modelsApi.getByProvider("google");
    const autoAssign = await modelsApi.autoAssign();
    const testResult = await modelsApi.testModel("m-7");

    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(1, "/models/discover/google");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(1, "/models/sync/google");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(2, "/models/sync");
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(2, "/models/count/google");
    expect(hoisted.apiClientMock.get).toHaveBeenNthCalledWith(3, "/models/by-provider/google");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(3, "/models/auto-assign");
    expect(hoisted.apiClientMock.post).toHaveBeenNthCalledWith(4, "/models/m-7/test");

    expect(discovered).toHaveLength(1);
    expect(providerSync.provider).toBe("google");
    expect(allSync.providers.google).toBe(2);
    expect(providerCount.count).toBe(2);
    expect(providerModels).toEqual([{ id: "m-7" }]);
    expect(autoAssign.assigned.chat).toBe("m-7");
    expect(testResult.success).toBe(true);
  });
});
