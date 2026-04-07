import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("runtime config route", () => {
  let infoSpy: ReturnType<typeof vi.spyOn>;
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.resetModules();
    infoSpy = vi.spyOn(console, "info").mockImplementation(() => undefined);
    errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    infoSpy.mockRestore();
    errorSpy.mockRestore();
    delete process.env.API_URL;
    delete process.env.NEXT_PUBLIC_API_URL;
    delete process.env.INTERNAL_API_PORT;
  });

  it("prefers explicit API_URL env configuration", async () => {
    process.env.API_URL = "https://services.api.example.com";
    const { GET } = await import("./route");

    const response = await GET({
      headers: new Headers(),
      nextUrl: new URL("http://localhost/config"),
    } as never);

    await expect(response.json()).resolves.toEqual({
      apiUrl: "https://services.api.example.com",
    });
  });

  it("derives API url from forwarded headers when env is absent", async () => {
    process.env.INTERNAL_API_PORT = "7777";
    const { GET } = await import("./route");

    const response = await GET({
      headers: new Headers([
        ["x-forwarded-proto", "https"],
        ["host", "app.example.com:3000"],
      ]),
      nextUrl: new URL("http://localhost/config"),
    } as never);

    await expect(response.json()).resolves.toEqual({
      apiUrl: "https://app.example.com:7777",
    });
    expect(infoSpy).toHaveBeenCalled();
  });

  it("falls back to localhost when host header is unavailable", async () => {
    const { GET } = await import("./route");

    const response = await GET({
      headers: new Headers(),
      nextUrl: new URL("http://localhost/config"),
    } as never);

    await expect(response.json()).resolves.toEqual({
      apiUrl: "http://localhost:5055",
    });
    expect(infoSpy).toHaveBeenCalled();
  });

  it("falls back to localhost and logs when header inspection throws", async () => {
    const { GET } = await import("./route");

    const response = await GET({
      headers: {
        get: () => {
          throw new Error("header boom");
        },
      },
      nextUrl: new URL("http://localhost/config"),
    } as never);

    await expect(response.json()).resolves.toEqual({
      apiUrl: "http://localhost:5055",
    });
    expect(errorSpy).toHaveBeenCalled();
    expect(infoSpy).toHaveBeenCalled();
  });
});
