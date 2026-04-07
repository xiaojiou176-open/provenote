import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { StreamingResponse } from "./StreamingResponse";

const hoisted = vi.hoisted(() => ({
  openModalMock: vi.fn(),
  toastErrorMock: vi.fn(),
}));

vi.mock("@/lib/hooks/use-modal-manager", () => ({
  useModalManager: () => ({
    openModal: hoisted.openModalMock,
  }),
}));

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => ({
    t: {
      common: {
        accessibility: {
          askResponse: "Ask Response",
        },
        strategy: "Strategy",
        reasoning: "Reasoning",
        searchTerms: "Search terms",
        individualAnswers: "{count} answers",
        finalAnswer: "Final answer",
        itemNotFound: "Missing {type}",
      },
      searchPage: {
        processingQuestion: "Processing question",
      },
    },
  }),
}));

vi.mock("sonner", () => ({
  toast: {
    error: hoisted.toastErrorMock,
  },
}));

vi.mock("@/components/common/LoadingSpinner", () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">loading</div>,
}));

vi.mock("@/components/ui/card", () => ({
  Card: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  CardContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/collapsible", async () => {
  const React = await import("react");
  const Context = React.createContext<{
    open: boolean;
    onOpenChange?: (next: boolean) => void;
  }>({ open: false });

  return {
    Collapsible: ({
      children,
      open,
      onOpenChange,
    }: {
      children: ReactNode;
      open: boolean;
      onOpenChange?: (next: boolean) => void;
    }) => <Context.Provider value={{ open, onOpenChange }}>{children}</Context.Provider>,
    CollapsibleTrigger: ({ children }: { children: ReactNode }) => {
      const ctx = React.useContext(Context);
      return (
        <button onClick={() => ctx.onOpenChange?.(!ctx.open)} type="button">
          {children}
        </button>
      );
    },
    CollapsibleContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  };
});

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: { children: ReactNode }) => <span>{children}</span>,
}));

vi.mock("@/lib/utils/source-references", () => ({
  convertReferencesToMarkdownLinks: (content: string) => content,
  createReferenceLinkComponent:
    (onReferenceClick: (type: string, id: string) => void) =>
    ({ href, children }: { href?: string; children?: ReactNode }) => (
      <button
        onClick={() => {
          const [, type = "source", id = "1"] =
            (href ?? "#ref-source-1").match(/^#ref-([^-]+)-(.+)$/) || [];
          onReferenceClick(type, id);
        }}
        type="button"
      >
        {children}
      </button>
    ),
}));

vi.mock("react-markdown", () => ({
  default: ({
    children,
    components,
  }: {
    children: string;
    components: Record<string, (props: { children?: ReactNode; href?: string }) => ReactNode>;
  }) => {
    const Anchor = components.a;
    const Table = components.table;
    const Thead = components.thead;
    const Tbody = components.tbody;
    const Tr = components.tr;
    const Th = components.th;
    const Td = components.td;
    return (
      <div>
        <p>{children}</p>
        <Anchor href="#ref-source-source-1">Open source</Anchor>
        <Anchor href="#ref-source_insight-insight-2">Open insight</Anchor>
        <Table>
          <Thead>
            <Tr>
              <Th>Head</Th>
            </Tr>
          </Thead>
          <Tbody>
            <Tr>
              <Td>Cell</Td>
            </Tr>
          </Tbody>
        </Table>
      </div>
    );
  },
}));

describe("StreamingResponse", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns nothing when there is no streaming content", () => {
    const { container } = render(
      <StreamingResponse answers={[]} finalAnswer={null} isStreaming={false} strategy={null} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("renders strategy, individual answers, final answer, and opens referenced modal", () => {
    const { container } = render(
      <StreamingResponse
        isStreaming
        strategy={{
          reasoning: "Think first",
          searches: [{ term: "alpha", instructions: "find alpha" }],
        }}
        answers={["Answer one"]}
        finalAnswer={"Final answer body"}
      />,
    );

    expect(screen.getByRole("region", { name: "Ask Response" })).toHaveAttribute(
      "aria-busy",
      "true",
    );
    expect(screen.getByText("Think first")).toBeInTheDocument();
    expect(screen.getByText("alpha")).toBeInTheDocument();
    expect(screen.getByText("Answer one")).toBeInTheDocument();
    expect(screen.getByText("Final answer body")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open source" }));
    expect(hoisted.openModalMock).toHaveBeenCalledWith("source", "source-1");

    fireEvent.click(screen.getByRole("button", { name: "Open insight" }));
    expect(hoisted.openModalMock).toHaveBeenCalledWith("insight", "insight-2");
    expect(screen.getByText("Head")).toBeInTheDocument();
    expect(screen.getByText("Cell")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Strategy/i }));
    fireEvent.click(screen.getByRole("button", { name: /1 answers/i }));
    expect(container.querySelectorAll(".rotate-180").length).toBeGreaterThan(0);
  });

  it("shows streaming indicator when waiting for final answer", () => {
    render(<StreamingResponse answers={[]} finalAnswer={null} isStreaming strategy={null} />);

    expect(screen.getByRole("region", { name: "Ask Response" })).toHaveAttribute(
      "aria-busy",
      "true",
    );
    expect(screen.getByText("Processing question")).toBeInTheDocument();
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("shows fallback toast when reference modal fails to open", () => {
    hoisted.openModalMock.mockImplementation(() => {
      throw new Error("modal failed");
    });

    render(
      <StreamingResponse
        answers={[]}
        finalAnswer={"Final with reference"}
        isStreaming={false}
        strategy={null}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open insight" }));
    expect(hoisted.toastErrorMock).toHaveBeenCalledWith("Missing insight");
  });

  it("shows source fallback toast for non-insight reference failures", () => {
    hoisted.openModalMock.mockImplementation(() => {
      throw new Error("modal failed");
    });

    render(
      <StreamingResponse
        answers={[]}
        finalAnswer={"Final with source reference"}
        isStreaming={false}
        strategy={null}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open source" }));
    expect(hoisted.toastErrorMock).toHaveBeenCalledWith("Missing source");
  });
});
