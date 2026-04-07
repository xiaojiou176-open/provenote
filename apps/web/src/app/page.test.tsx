import { redirect } from "next/navigation";
import { describe, expect, it, vi } from "vitest";
import HomePage from "./page";

vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
}));

describe("HomePage", () => {
  it("redirects root requests to sources", () => {
    HomePage();
    expect(redirect).toHaveBeenCalledWith("/sources");
  });
});
