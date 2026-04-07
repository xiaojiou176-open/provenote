import { describe, expect, it } from "vitest";

import { formatApiError, getApiErrorKey, getApiErrorMessage } from "./error-handler";

const t = (key: string) => `translated:${key}`;

describe("error-handler utilities", () => {
  it("formats known error shapes and string input", () => {
    expect(formatApiError("plain message")).toBe("plain message");
    expect(formatApiError({ response: { data: { detail: "Notebook not found" } } })).toBe(
      "Notebook not found",
    );
    expect(formatApiError({ detail: "Missing authorization" })).toBe("Missing authorization");
    expect(formatApiError({ message: "Network fail" })).toBe("Network fail");
    expect(formatApiError({})).toBe("An unexpected error occurred");
  });

  it("maps exact and prefix backend errors to i18n keys", () => {
    expect(getApiErrorKey("Notebook not found")).toBe("apiErrors.notebookNotFound");
    expect(getApiErrorKey("Strategy model gemini-1.5-pro is unavailable")).toBe(
      "apiErrors.strategyModelNotFound",
    );
    expect(getApiErrorKey("Unknown backend issue")).toBe("apiErrors.genericError");
    expect(getApiErrorKey("", "apiErrors.customFallback")).toBe("apiErrors.customFallback");
  });

  it("returns translated message for mapped keys and raw backend text for unknown", () => {
    expect(getApiErrorMessage("Source not found", t)).toBe("translated:apiErrors.sourceNotFound");
    expect(getApiErrorMessage("Final answer model is missing", t)).toBe(
      "translated:apiErrors.finalAnswerModelNotFound",
    );
    expect(getApiErrorMessage("Human-readable backend message", t)).toBe(
      "Human-readable backend message",
    );
  });

  it("uses fallback translation when message is empty", () => {
    expect(getApiErrorMessage("", t, "apiErrors.fileUploadFailed")).toBe(
      "translated:apiErrors.fileUploadFailed",
    );
    expect(getApiErrorMessage("", t)).toBe("translated:apiErrors.genericError");
  });
});
