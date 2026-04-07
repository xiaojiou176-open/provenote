import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { AuditableClaimReviewWorkspace } from "./AuditableClaimReviewWorkspace";

vi.mock("@/components/ui/card", () => ({
  Card: ({ children, ...props }: { children: ReactNode } & Record<string, unknown>) => (
    <div {...props}>{children}</div>
  ),
  CardHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardDescription: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({
    children,
    onClick,
    disabled,
  }: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
  }) => (
    <button type="button" onClick={onClick} disabled={disabled}>
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: { children: ReactNode }) => <span>{children}</span>,
}));

vi.mock("@/components/ui/tabs", async () => {
  const React = await import("react");
  const TabsContext = React.createContext<{
    value: string;
    setValue: (value: string) => void;
  }>({
    value: "claims",
    setValue: () => undefined,
  });

  return {
    Tabs: ({ defaultValue, children }: { defaultValue: string; children: ReactNode }) => {
      const [value, setValue] = React.useState(defaultValue);
      return <TabsContext.Provider value={{ value, setValue }}>{children}</TabsContext.Provider>;
    },
    TabsList: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    TabsTrigger: ({ value, children }: { value: string; children: ReactNode }) => {
      const ctx = React.useContext(TabsContext);
      return (
        <button type="button" onClick={() => ctx.setValue(value)}>
          {children}
        </button>
      );
    },
    TabsContent: ({ value, children }: { value: string; children: ReactNode }) => {
      const ctx = React.useContext(TabsContext);
      return ctx.value === value ? <div>{children}</div> : null;
    },
  };
});

vi.mock("@/lib/hooks/use-translation", () => ({
  useTranslation: () => {
    const t = Object.assign(
      (key: string, values?: { index?: number; count?: number }) => {
        if (key === "sources.auditableClaimReviewClaimLabel") {
          return `Claim ${values?.index ?? ""}`.trim();
        }
        if (key === "sources.auditableClaimReviewSectionFallback") {
          return `Section ${values?.index ?? ""}`.trim();
        }
        if (key === "sources.auditableClaimReviewSectionEvidenceCount") {
          return `${values?.count ?? 0} PID reference(s) support this section.`;
        }
        return key;
      },
      {
        sources: {
          auditableClaimReviewTitle: "Claim review workspace",
          auditableClaimReviewDescription:
            "Review claims and sections with their PID evidence before you repair or promote this source-backed outcome.",
          auditableClaimReviewClaimsTab: "Claims",
          auditableClaimReviewSectionsTab: "Sections",
          auditableClaimReviewEmptyClaims: "No claims to review yet.",
          auditableClaimReviewEmptySections: "No sections to review yet.",
          auditableClaimReviewEvidencePids: "Evidence PIDs",
          auditableClaimReviewNoEvidence: "No PID evidence.",
          auditableClaimReviewLinkedSections: "Linked sections",
          auditableClaimReviewNoLinkedSections: "No section currently cites the same PID set.",
          auditableClaimReviewRepairClaim: "Repair claim",
          auditableClaimReviewRepairSection: "Repair section",
          auditableClaimReviewSectionPids: "Section PIDs",
          auditableClaimReviewSectionNoEvidence:
            "No PID evidence is currently attached to this section.",
        },
      },
    );

    return { t };
  },
}));

describe("AuditableClaimReviewWorkspace", () => {
  it("shows claim evidence, linked sections, and repair actions", () => {
    const onRepairClaim = vi.fn();
    const onRepairSection = vi.fn();

    render(
      <AuditableClaimReviewWorkspace
        claims={[{ text: "Claim A", source_pids: ["P000001"] }]}
        sections={[{ title: "Summary", source_pids: ["P000001", "P000002"] }]}
        onRepairClaim={onRepairClaim}
        onRepairSection={onRepairSection}
      />,
    );

    expect(screen.getByText("Claim review workspace")).toBeInTheDocument();
    expect(screen.getByText("Claim A")).toBeInTheDocument();
    expect(screen.getByText("P000001")).toBeInTheDocument();
    expect(screen.getByText("Summary")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Repair claim" }));
    expect(onRepairClaim).toHaveBeenCalledWith(0);

    fireEvent.click(screen.getByRole("button", { name: "Sections" }));
    fireEvent.click(screen.getByRole("button", { name: "Repair section" }));
    expect(onRepairSection).toHaveBeenCalledWith(0);
  });
});
