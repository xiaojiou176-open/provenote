import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getApiUrl, getConfig, resetConfig } from "./config";

describe("Config Priority", () => {
  const originalEnv = process.env;
  const originalFetch = global.fetch;
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.resetModules();
    resetConfig();
    process.env = { ...originalEnv };
    process.env.NODE_ENV = "test";
    fetchMock.mockReset();
    global.fetch = fetchMock;
    vi.spyOn(console, "info").mockImplementation(() => undefined);
  });

  afterEach(() => {
    process.env = originalEnv;
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("should prioritize runtime config over everything else", async () => {
    // Setup: Env var set, Runtime config returns explicit value
    process.env.NEXT_PUBLIC_API_URL = "http://env-url.com";

    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apiUrl: "http://runtime-url.com" }),
    } as Response);

    // Mock the second fetch call (api/config check)
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "1.0.0" }),
    } as Response);

    const url = await getApiUrl();
    expect(url).toBe("http://runtime-url.com");
  });

  it("should fall back to env var if runtime config returns empty/null", async () => {
    // Setup: Env var set, Runtime config returns empty string (simulating not set)
    process.env.NEXT_PUBLIC_API_URL = "http://env-url.com";

    // First fetch: /config returns empty apiUrl
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apiUrl: "" }),
    } as Response);

    // Second fetch: api/config check using env url
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "1.0.0" }),
    } as Response);

    const url = await getApiUrl();
    expect(url).toBe("http://env-url.com");
  });

  it("should fall back to env var if runtime config returns empty object", async () => {
    // Setup: Env var set, Runtime config returns empty object
    process.env.NEXT_PUBLIC_API_URL = "http://env-url.com";

    // First fetch: /config returns {}
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}), // Missing apiUrl
    } as Response);

    // Second fetch: api/config check using env url
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "1.0.0" }),
    } as Response);

    const url = await getApiUrl();
    expect(url).toBe("http://env-url.com");
  });

  it("should use default (relative path) if both runtime and env are missing", async () => {
    // Setup: Env var NOT set, Runtime config returns empty
    delete process.env.NEXT_PUBLIC_API_URL;

    // First fetch: /config returns empty
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apiUrl: "" }),
    } as Response);

    // Second fetch: api/config check using default relative path
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "1.0.0" }),
    } as Response);

    const url = await getApiUrl();
    expect(url).toBe("");
  });

  it("should reuse in-flight config request for concurrent getApiUrl calls", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apiUrl: "http://runtime-url.com" }),
    } as Response);
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "1.0.0" }),
    } as Response);

    const [urlA, urlB] = await Promise.all([getApiUrl(), getApiUrl()]);

    expect(urlA).toBe("http://runtime-url.com");
    expect(urlB).toBe("http://runtime-url.com");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("should reuse cached config in subsequent getApiUrl calls", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apiUrl: "http://runtime-url.com" }),
    } as Response);
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "1.0.0" }),
    } as Response);

    const first = await getApiUrl();
    const second = await getApiUrl();

    expect(first).toBe("http://runtime-url.com");
    expect(second).toBe("http://runtime-url.com");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("should reuse in-flight config request for concurrent getConfig calls", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apiUrl: "http://runtime-url.com" }),
    } as Response);
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "1.0.0" }),
    } as Response);

    const [configA, configB] = await Promise.all([getConfig(), getConfig()]);

    expect(configA).toEqual(configB);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("should return cached config on subsequent getConfig calls", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apiUrl: "http://runtime-url.com" }),
    } as Response);
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "1.2.3", hasUpdate: true, latestVersion: "1.3.0" }),
    } as Response);

    const first = await getConfig();
    const second = await getConfig();

    expect(first).toEqual(second);
    expect(first.apiUrl).toBe("http://runtime-url.com");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("should safely handle malformed runtime config payload", async () => {
    process.env.NEXT_PUBLIC_API_URL = "http://env-url.com";

    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => null,
    } as Response);
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "1.0.0" }),
    } as Response);

    expect(await getApiUrl()).toBe("http://env-url.com");
  });

  it("should return runtime endpoint status log path in development when /config is non-ok", async () => {
    process.env.NODE_ENV = "development";
    process.env.NEXT_PUBLIC_API_URL = "http://env-url.com";

    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 418,
    } as Response);
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "1.0.0" }),
    } as Response);

    await expect(getApiUrl()).resolves.toBe("http://env-url.com");
    expect(console.info).toHaveBeenCalled();
  });

  it("should log runtime value path in development when /config returns success", async () => {
    process.env.NODE_ENV = "development";

    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apiUrl: "http://runtime-url.com" }),
    } as Response);
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "1.0.0" }),
    } as Response);

    await expect(getApiUrl()).resolves.toBe("http://runtime-url.com");
    expect(console.info).toHaveBeenCalled();
  });

  it("should throw when backend config endpoint returns non-ok status", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apiUrl: "" }),
    } as Response);
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 503,
    } as Response);

    await expect(getApiUrl()).rejects.toThrow("API config endpoint returned status 503");
  });

  it("should throw when runtime config fetch fails and backend config fetch fails", async () => {
    process.env.NODE_ENV = "development";
    process.env.NEXT_PUBLIC_API_URL = "http://env-url.com";

    fetchMock.mockRejectedValueOnce(new Error("runtime endpoint down"));
    fetchMock.mockRejectedValueOnce(new Error("backend down"));

    await expect(getApiUrl()).rejects.toThrow("backend down");
    expect(console.info).toHaveBeenCalled();
  });

  it("should clear failed in-flight request and allow recovery on retry", async () => {
    process.env.NEXT_PUBLIC_API_URL = "http://env-url.com";

    fetchMock.mockRejectedValueOnce(new Error("runtime endpoint down"));
    fetchMock.mockRejectedValueOnce(new Error("backend down"));
    await expect(getApiUrl()).rejects.toThrow("backend down");

    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apiUrl: "" }),
    } as Response);
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ version: "2.0.0", hasUpdate: false }),
    } as Response);

    await expect(getApiUrl()).resolves.toBe("http://env-url.com");
  });
});
