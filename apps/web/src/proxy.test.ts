import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";
import { proxy } from "./proxy";

describe("proxy", () => {
  it("redirects root requests to sources", () => {
    const response = proxy(new NextRequest("http://localhost:3000/"));

    expect(response.headers.get("location")).toBe("http://localhost:3000/sources");
  });

  it("passes through non-root requests", () => {
    const response = proxy(new NextRequest("http://localhost:3000/notebooks"));

    expect(response.headers.get("location")).toBeNull();
  });
});
