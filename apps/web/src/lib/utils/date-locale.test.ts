import { bn, enUS, fr, ja, ptBR, ru, zhCN, zhTW } from "date-fns/locale";
import { describe, expect, it } from "vitest";
import { getDateLocale } from "./date-locale";

describe("getDateLocale", () => {
  it("returns the configured locale for supported languages", () => {
    expect(getDateLocale("en-US")).toBe(enUS);
    expect(getDateLocale("zh-CN")).toBe(zhCN);
    expect(getDateLocale("zh-TW")).toBe(zhTW);
    expect(getDateLocale("pt-BR")).toBe(ptBR);
    expect(getDateLocale("ja-JP")).toBe(ja);
    expect(getDateLocale("fr-FR")).toBe(fr);
    expect(getDateLocale("ru-RU")).toBe(ru);
    expect(getDateLocale("bn-IN")).toBe(bn);
  });

  it("falls back to English for unknown languages", () => {
    expect(getDateLocale("bn-BD")).toBe(enUS);
    expect(getDateLocale("unknown")).toBe(enUS);
  });
});
