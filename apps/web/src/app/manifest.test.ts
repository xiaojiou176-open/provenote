import { describe, expect, it } from "vitest";
import manifest from "./manifest";

describe("web manifest", () => {
  it("describes the long-context-first workbench surface", () => {
    const value = manifest();

    expect(value.name).toBe("Provenote");
    expect(value.short_name).toBe("Provenote");
    expect(value.description).toContain("messy long context");
    expect(value.start_url).toBe("/");
    expect(value.icons?.[0]?.src).toBe("/favicon.ico");
  });
});
