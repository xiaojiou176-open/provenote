import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { auditableApi } from "@/lib/api/auditable";
import { useAuditableRuns } from "@/lib/hooks/use-auditable-runs";
import { AuditableMarkdownPanel } from "./AuditableMarkdownPanel";

const hoisted = vi.hoisted(() => ({
  toastMock: vi.fn(),
  getApiErrorMessageMock: vi.fn(),
}));

vi.mock("@/lib/hooks/use-auditable-runs");
vi.mock("@/lib/api/auditable", () => ({
  auditableApi: {
    downloadMarkdown: vi.fn(),
  },
}));
vi.mock("@/lib/hooks/use-toast", () => ({
  useToast: () => ({ toast: hoisted.toastMock }),
}));
vi.mock("@/lib/utils/error-handler", () => ({
  getApiErrorMessage: hoisted.getApiErrorMessageMock,
}));

function createUseAuditableRunsMock(
  overrides: Partial<ReturnType<typeof useAuditableRuns>> = {},
): ReturnType<typeof useAuditableRuns> {
  return {
    runs: [],
    latestRun: null,
    startRun: {
      mutate: vi.fn(),
      isPending: false,
    },
    repairClaim: {
      mutate: vi.fn(),
      isPending: false,
    },
    repairSection: {
      mutate: vi.fn(),
      isPending: false,
    },
    isLoading: false,
    isFetching: false,
    error: null,
    refetchRuns: vi.fn(),
    ...overrides,
  } as unknown as ReturnType<typeof useAuditableRuns>;
}

describe("AuditableMarkdownPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hoisted.getApiErrorMessageMock.mockReturnValue("resolved-auditable-error");

    Object.defineProperty(window.URL, "createObjectURL", {
      writable: true,
      value: vi.fn(() => "blob:mock-url"),
    });
    Object.defineProperty(window.URL, "revokeObjectURL", {
      writable: true,
      value: vi.fn(),
    });
    HTMLAnchorElement.prototype.click = vi.fn();
  });

  it("renders latest run status and counters", () => {
    const repairClaim = vi.fn();
    const repairSection = vi.fn();
    vi.mocked(useAuditableRuns).mockReturnValue(
      createUseAuditableRunsMock({
        latestRun: {
          id: "run_1",
          source_id: "src_1",
          status: "completed",
          model_id: "gemini-3.1-pro-preview",
          language: "zh-CN",
          near_dedup_threshold: 0.97,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-01T00:01:00Z",
          metrics: {
            coverage_rate: 0.85,
            missing_count: 3,
            duplicate_count: 2,
            uncited_claims_count: 1,
            dedup_group_count: 2,
            unknown_pid_count: 1,
            unclassified_count: 4,
          },
          coverage_json: {},
          dedup_json: {},
          result_markdown: "# report",
          sections: [{ title: "Summary", source_pids: ["P000001"] }],
          claims: [{ text: "Claim A", source_pids: ["P000001"] }],
        },
        repairClaim: {
          mutate: repairClaim,
          isPending: false,
        } as unknown as ReturnType<typeof useAuditableRuns>["repairClaim"],
        repairSection: {
          mutate: repairSection,
          isPending: false,
        } as unknown as ReturnType<typeof useAuditableRuns>["repairSection"],
      }),
    );

    render(<AuditableMarkdownPanel sourceId="src_1" />);

    expect(screen.getByText("Auditable Markdown")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("0.85")).toBeInTheDocument();
    expect(screen.getAllByText("1")).toHaveLength(2);
    expect(screen.getByText("4")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Sections" }));
    fireEvent.click(screen.getByRole("tab", { name: "Claims" }));
    fireEvent.click(screen.getByRole("button", { name: "Repair claim" }));
    expect(repairClaim).toHaveBeenCalledWith({ runId: "run_1", targetIndex: 0 });
    expect(repairSection).not.toHaveBeenCalled();
  });

  it("triggers run when click run button", () => {
    const mutate = vi.fn();
    vi.mocked(useAuditableRuns).mockReturnValue(
      createUseAuditableRunsMock({
        startRun: {
          mutate,
          isPending: false,
        } as unknown as ReturnType<typeof useAuditableRuns>["startRun"],
      }),
    );

    render(<AuditableMarkdownPanel sourceId="src_1" />);

    fireEvent.click(screen.getByTestId("start-auditable-run"));

    expect(mutate).toHaveBeenCalledTimes(1);
    expect(mutate).toHaveBeenCalledWith({});
  });

  it("offers a direct draft-lane CTA when a completed run belongs to exactly one notebook", () => {
    const onUseInDraft = vi.fn();
    vi.mocked(useAuditableRuns).mockReturnValue(
      createUseAuditableRunsMock({
        latestRun: {
          id: "run_cta",
          source_id: "src_1",
          status: "completed",
          model_id: "gemini-3.1-pro-preview",
          language: "zh-CN",
          near_dedup_threshold: 0.97,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-01T00:01:00Z",
          metrics: {
            coverage_rate: 0.9,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            dedup_group_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          coverage_json: {},
          dedup_json: {},
          result_markdown: "# report",
        },
      }),
    );

    render(
      <AuditableMarkdownPanel
        sourceId="src_1"
        linkedNotebookIds={["notebook:1"]}
        onUseInDraft={onUseInDraft}
      />,
    );

    fireEvent.click(screen.getByTestId("use-source-in-draft"));
    expect(onUseInDraft).toHaveBeenCalledWith("notebook:1");
    expect(screen.getByText("Next step: turn this source into a draft")).toBeInTheDocument();
  });

  it("enables markdown download only for completed runs and downloads file", async () => {
    vi.mocked(useAuditableRuns).mockReturnValue(
      createUseAuditableRunsMock({
        latestRun: {
          id: "run_2",
          source_id: "src_1",
          status: "running",
          model_id: "gemini-3.1-pro-preview",
          language: "zh-CN",
          near_dedup_threshold: 0.97,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-01T00:01:00Z",
          metrics: {
            coverage_rate: 1,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            dedup_group_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          coverage_json: {},
          dedup_json: {},
          result_markdown: "# report",
        },
      }),
    );

    const { rerender } = render(<AuditableMarkdownPanel sourceId="src_1" />);

    expect(screen.getByTestId("download-auditable-markdown")).toBeDisabled();

    vi.mocked(useAuditableRuns).mockReturnValue(
      createUseAuditableRunsMock({
        latestRun: {
          id: "run_3",
          source_id: "src_1",
          status: "completed",
          model_id: "gemini-3.1-pro-preview",
          language: "zh-CN",
          near_dedup_threshold: 0.97,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-01T00:01:00Z",
          metrics: {
            coverage_rate: 1,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            dedup_group_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          coverage_json: {},
          dedup_json: {},
          result_markdown: "# report",
        },
      }),
    );

    vi.mocked(auditableApi.downloadMarkdown).mockResolvedValue({
      data: new Blob(["# report"]),
      headers: {
        "content-disposition": 'attachment; filename="auditable-report.md"',
      },
    } as unknown as Awaited<ReturnType<typeof auditableApi.downloadMarkdown>>);

    rerender(<AuditableMarkdownPanel sourceId="src_1" />);

    const downloadButton = screen.getByTestId("download-auditable-markdown");
    expect(downloadButton).toBeEnabled();

    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(auditableApi.downloadMarkdown).toHaveBeenCalledWith("run_3");
    });
  });

  it("handles failed/unknown statuses and surfaces query load errors", () => {
    vi.mocked(useAuditableRuns).mockReturnValue(
      createUseAuditableRunsMock({
        latestRun: {
          id: "run_failed",
          source_id: "src_1",
          status: "failed",
          model_id: "gemini-3.1-pro-preview",
          language: "zh-CN",
          near_dedup_threshold: 0.97,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-01T00:01:00Z",
          metrics: {
            coverage_rate: 0,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            dedup_group_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          coverage_json: {},
          dedup_json: {},
          result_markdown: "",
        },
        error: new Error("load failed"),
      }),
    );

    const { rerender } = render(<AuditableMarkdownPanel sourceId="src_1" />);
    expect(screen.getByText("Run failed")).toBeInTheDocument();
    expect(screen.getByText("Failed to load auditable runs")).toBeInTheDocument();

    vi.mocked(useAuditableRuns).mockReturnValue(
      createUseAuditableRunsMock({
        latestRun: {
          id: "run_unknown",
          source_id: "src_1",
          status: "stale",
          model_id: "gemini-3.1-pro-preview",
          language: "zh-CN",
          near_dedup_threshold: 0.97,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-01T00:01:00Z",
          metrics: {
            coverage_rate: 1,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            dedup_group_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          coverage_json: {},
          dedup_json: {},
          result_markdown: "",
        },
      }),
    );
    rerender(<AuditableMarkdownPanel sourceId="src_1" />);
    expect(screen.getByText("stale")).toBeInTheDocument();
  });

  it("falls back filename when header is missing and handles 404/non-404 download errors", async () => {
    vi.mocked(useAuditableRuns).mockReturnValue(
      createUseAuditableRunsMock({
        latestRun: {
          id: "run_404",
          source_id: "src_1",
          status: "completed",
          model_id: "gemini-3.1-pro-preview",
          language: "zh-CN",
          near_dedup_threshold: 0.97,
          created: "2026-01-01T00:00:00Z",
          updated: "2026-01-01T00:01:00Z",
          metrics: {
            coverage_rate: 1,
            missing_count: 0,
            duplicate_count: 0,
            uncited_claims_count: 0,
            dedup_group_count: 0,
            unknown_pid_count: 0,
            unclassified_count: 0,
          },
          coverage_json: {},
          dedup_json: {},
          result_markdown: "",
        },
      }),
    );

    const originalCreateElement = document.createElement.bind(document);
    const linkMock = originalCreateElement("a");
    const clickSpy = vi.spyOn(linkMock, "click").mockImplementation(() => {});
    const appendSpy = vi.spyOn(document.body, "appendChild");
    const removeSpy = vi.spyOn(document.body, "removeChild");
    vi.spyOn(document, "createElement").mockImplementation(((
      tagName: string,
      options?: ElementCreationOptions,
    ) => {
      if (tagName.toLowerCase() === "a") {
        return linkMock;
      }
      return originalCreateElement(tagName, options);
    }) as typeof document.createElement);

    vi.mocked(auditableApi.downloadMarkdown).mockResolvedValueOnce({
      data: new Blob(["# report"]),
      headers: {
        "content-disposition": "attachment; filename*=UTF-8''report%20%E4%B8%AD%E6%96%87.md",
      },
    } as unknown as Awaited<ReturnType<typeof auditableApi.downloadMarkdown>>);
    vi.mocked(auditableApi.downloadMarkdown).mockResolvedValueOnce({
      data: new Blob(["# report"]),
      headers: {},
    } as unknown as Awaited<ReturnType<typeof auditableApi.downloadMarkdown>>);

    render(<AuditableMarkdownPanel sourceId="src_1" />);
    fireEvent.click(screen.getByTestId("download-auditable-markdown"));

    await waitFor(() => {
      expect(linkMock.download).toBe("report 中文.md");
      expect(clickSpy).toHaveBeenCalledTimes(1);
      expect(hoisted.toastMock).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Success",
          description: "Markdown downloaded.",
        }),
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("download-auditable-markdown")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("download-auditable-markdown"));
    await waitFor(() => {
      expect(linkMock.download).toBe("auditable-run_404.md");
      expect(appendSpy).toHaveBeenCalledWith(linkMock);
      expect(removeSpy).toHaveBeenCalledWith(linkMock);
      expect(clickSpy).toHaveBeenCalledTimes(2);
    });

    vi.mocked(auditableApi.downloadMarkdown).mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 404 },
    });
    fireEvent.click(screen.getByTestId("download-auditable-markdown"));

    await waitFor(() => {
      expect(hoisted.toastMock).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Error",
          description: "Generated markdown is not available yet.",
          variant: "destructive",
        }),
      );
    });

    vi.mocked(auditableApi.downloadMarkdown).mockRejectedValueOnce(new Error("network failed"));
    fireEvent.click(screen.getByTestId("download-auditable-markdown"));

    await waitFor(() => {
      expect(hoisted.toastMock).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Error",
          description: "resolved-auditable-error",
          variant: "destructive",
        }),
      );
    });
  });
});
