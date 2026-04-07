import { useQueryClient } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { queryClient } from "@/lib/api/query-client";
import { QueryProvider } from "./QueryProvider";

function QueryClientProbe() {
  const client = useQueryClient();
  return <div data-testid="query-client-id">{client === queryClient ? "same" : "different"}</div>;
}

describe("QueryProvider", () => {
  it("provides the shared query client instance to descendants", () => {
    render(
      <QueryProvider>
        <QueryClientProbe />
      </QueryProvider>,
    );

    expect(screen.getByTestId("query-client-id")).toHaveTextContent("same");
  });
});
