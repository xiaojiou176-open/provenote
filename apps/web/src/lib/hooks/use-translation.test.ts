import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.unmock("@/lib/hooks/use-translation");

const emitLanguageChangeStartMock = vi.fn();
const emitLanguageChangeEndMock = vi.fn();

vi.mock("react-i18next", () => ({
  useTranslation: vi.fn(),
}));

vi.mock("@/lib/i18n-events", () => ({
  emitLanguageChangeStart: (...args: unknown[]) => emitLanguageChangeStartMock(...args),
  emitLanguageChangeEnd: (...args: unknown[]) => emitLanguageChangeEndMock(...args),
}));

import { useTranslation as useI18nTranslation } from "react-i18next";
import { useTranslation } from "./use-translation";

describe("useTranslation hook", () => {
  const changeLanguageMock = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (
      useI18nTranslation as unknown as { mockReturnValue: (value: unknown) => void }
    ).mockReturnValue({
      t: (key: string, options?: { returnObjects?: boolean }) => {
        if (key.startsWith("deep") && options?.returnObjects) {
          return {};
        }
        if (key === "common") {
          return { appName: "Provenote" };
        }
        if (key === "common.appName") {
          return "Provenote";
        }
        return key;
      },
      i18n: {
        language: "en-US",
        changeLanguage: changeLanguageMock,
      },
    });
  });

  it("returns proxy-backed nested translations and callable access", () => {
    const { result } = renderHook(() => useTranslation());

    expect(result.current.language).toBe("en-US");
    expect(result.current.t.common.appName).toBe("Provenote");
    expect(result.current.t("common.appName")).toBe("Provenote");
    expect(result.current.t.common("appName")).toBe("Provenote");
  });

  it("emits language change lifecycle events when changing language", async () => {
    const { result } = renderHook(() => useTranslation());

    await act(async () => {
      await result.current.setLanguage("zh-CN");
    });

    expect(changeLanguageMock).toHaveBeenCalledWith("zh-CN");
    expect(emitLanguageChangeStartMock).toHaveBeenCalledWith("zh-CN");
    expect(emitLanguageChangeEndMock).toHaveBeenCalledWith("zh-CN");
  });

  it("still emits language change end when changeLanguage rejects", async () => {
    const boom = new Error("cannot switch");
    (
      useI18nTranslation as unknown as { mockReturnValue: (value: unknown) => void }
    ).mockReturnValue({
      t: (key: string) => key,
      i18n: {
        language: "en-US",
        changeLanguage: vi.fn().mockRejectedValue(boom),
      },
    });

    const { result } = renderHook(() => useTranslation());

    await expect(result.current.setLanguage("fr-FR")).rejects.toThrow("cannot switch");
    expect(emitLanguageChangeStartMock).toHaveBeenCalledWith("fr-FR");
    expect(emitLanguageChangeEndMock).toHaveBeenCalledWith("fr-FR");
  });

  it("skips changeLanguage when the requested language is already active", async () => {
    const { result } = renderHook(() => useTranslation());

    await expect(result.current.setLanguage("en-US")).resolves.toBe("en-US");

    expect(changeLanguageMock).not.toHaveBeenCalled();
    expect(emitLanguageChangeStartMock).not.toHaveBeenCalled();
    expect(emitLanguageChangeEndMock).not.toHaveBeenCalled();
  });

  it("returns fallback path strings for missing keys and depth-guard recursion", () => {
    const { result } = renderHook(() => useTranslation());

    expect(result.current.t.missing).toBe("missing");
    expect(result.current.t.deep.one.two.three).toBe("deep.one.two.three");
  });

  it("supports function-call options and nullish fallback values", () => {
    (
      useI18nTranslation as unknown as { mockReturnValue: (value: unknown) => void }
    ).mockReturnValue({
      t: (key: string, options?: { returnObjects?: boolean }) => {
        if (options?.returnObjects && key === "nullish") {
          return null;
        }
        return key;
      },
      i18n: {
        language: "en-US",
        changeLanguage: vi.fn(),
      },
    });

    const { result } = renderHook(() => useTranslation());

    expect(result.current.t({ fallback: "x" })).toBe("");
    expect(result.current.t.nullish).toBe("nullish");
  });

  it("blocks dangerous properties and handles symbol property access", () => {
    const { result } = renderHook(() => useTranslation());

    expect(result.current.t.__proto__).toBeUndefined();
    expect(result.current.t.then).toBeUndefined();
    expect(result.current.t[Symbol.toStringTag]).toBeUndefined();
  });

  it("supports String.prototype methods and primitive translation passthrough", () => {
    (
      useI18nTranslation as unknown as { mockReturnValue: (value: unknown) => void }
    ).mockReturnValue({
      t: (key: string, options?: { returnObjects?: boolean }) => {
        if (options?.returnObjects && (key === "replace" || key === "length")) {
          return {};
        }
        if (key === "") {
          return "root value";
        }
        if (options?.returnObjects && key === "count") {
          return 42;
        }
        return key;
      },
      i18n: {
        language: "en-US",
        changeLanguage: vi.fn(),
      },
    });

    const { result } = renderHook(() => useTranslation());
    const replaceFn = result.current.t.replace as (from: string, to: string) => string;

    expect(replaceFn("root", "leaf")).toBe("leaf value");
    expect(result.current.t.length).toBe(10);
    expect(result.current.t.count).toBe(42);
  });

  it("falls back to proxy when method helper resolves non-string translation", () => {
    (
      useI18nTranslation as unknown as { mockReturnValue: (value: unknown) => void }
    ).mockReturnValue({
      t: (key: string, options?: { returnObjects?: boolean }) => {
        if (options?.returnObjects && key === "replace") {
          return {};
        }
        if (key === "") {
          return { not: "a string" };
        }
        return key;
      },
      i18n: {
        language: "en-US",
        changeLanguage: vi.fn(),
      },
    });

    const { result } = renderHook(() => useTranslation());
    expect(typeof result.current.t.replace).toBe("function");
  });

  it("resets loop counters and breaks runaway property access", () => {
    const nowSpy = vi.spyOn(Date, "now");
    nowSpy.mockReturnValueOnce(0);
    nowSpy.mockReturnValue(1500);

    const loopSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const { result } = renderHook(() => useTranslation());

    void result.current.t.alpha;
    for (let i = 0; i < 1001; i += 1) {
      void result.current.t.looped;
    }

    expect(result.current.t.looped).toBe("looped");
    expect(loopSpy).toHaveBeenCalled();

    loopSpy.mockRestore();
    nowSpy.mockRestore();
  });
});
