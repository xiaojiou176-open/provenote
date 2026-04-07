import { describe, expect, it } from "vitest";
import robots from "./robots";

describe("robots metadata route", () => {
  it("allows indexing without inventing a canonical sitemap URL", () => {
    expect(robots()).toEqual({
      rules: {
        userAgent: "*",
        allow: "/",
      },
    });
  });
});
