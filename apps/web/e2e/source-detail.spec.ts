import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

test("source detail: render auditable panel and create an insight", async ({ page }) => {
  test.setTimeout(120_000);

  await setupMockApi(page, {
    sources: [
      {
        id: "src-detail",
        title: "Detailed Source",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-02T00:00:00.000Z",
        insights_count: 1,
        embedded: true,
        asset: {
          url: "https://example.com/source-detail",
        },
      },
    ],
    sourceDetails: [
      {
        id: "src-detail",
        title: "Detailed Source",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-02T00:00:00.000Z",
        insights_count: 1,
        embedded: true,
        embedded_chunks: 42,
        asset: {
          url: "https://example.com/source-detail",
        },
        full_text: "Detailed source full text for e2e assertions.",
        notebooks: ["nb-detail"],
      },
    ],
    sourceInsights: [
      {
        id: "insight-existing",
        source_id: "src-detail",
        insight_type: "summary",
        content: "Existing insight content for source detail page.",
        created: "2025-01-03T00:00:00.000Z",
        updated: "2025-01-03T00:00:00.000Z",
      },
    ],
    transformations: [
      {
        id: "tr-summary",
        name: "summary",
        title: "Summary Transformation",
        description: "Summarize source content.",
        prompt: "Summarize the source.",
        apply_default: false,
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
    ],
    sourceChatSessions: [],
    auditableRuns: [
      {
        id: "auditable-completed",
        source_id: "src-detail",
        status: "completed",
        model_id: "model-auditable",
        language: "en",
        created: "2025-01-02T00:00:00.000Z",
        updated: "2025-01-03T00:00:00.000Z",
        metrics: {
          coverage_rate: 0.93,
          missing_count: 1,
          duplicate_count: 0,
          uncited_claims_count: 0,
          dedup_group_count: 0,
          unknown_pid_count: 0,
          unclassified_count: 0,
        },
      },
    ],
  });

  await gotoWithReadyCheck(page, "/sources/src-detail", async () => {
    await expect(page.getByText("Auditable Markdown", { exact: true })).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByRole("button", { name: "Download Markdown" })).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByRole("button", { name: "Detailed Source" })).toBeVisible({
      timeout: 30_000,
    });
  });

  const insightsTab = page.getByRole("tab", { name: /Insights/i });
  await insightsTab.click();
  await expect(page.getByText("Generate New Insight")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Existing insight content for source detail page.")).toBeVisible({
    timeout: 10_000,
  });

  const startAuditableRunResponsePromise = page.waitForResponse((response) => {
    return (
      response.request().method() === "POST" &&
      response.url().endsWith("/api/sources/src-detail/auditable-runs")
    );
  });
  await page.getByTestId("start-auditable-run").click();
  const startAuditableRunResponse = await startAuditableRunResponsePromise;
  expect(startAuditableRunResponse.status()).toBe(201);
  await expect(page.getByTestId("start-auditable-run")).toBeVisible({ timeout: 10_000 });

  const createInsightResponsePromise = page.waitForResponse((response) => {
    return (
      response.request().method() === "POST" &&
      response.url().endsWith("/api/sources/src-detail/insights")
    );
  });
  await page.locator("#transformation-select").click();
  await page.getByRole("option", { name: "Summary Transformation" }).click();
  const insightGenerator = page
    .locator('label[for="transformation-select"]')
    .locator("..")
    .locator("..");
  await insightGenerator.getByRole("button", { name: "New" }).click();
  const createInsightResponse = await createInsightResponsePromise;
  expect([200, 201, 202]).toContain(createInsightResponse.status());

  await expect(page.getByText("Mock insight for src-detail")).toBeVisible({ timeout: 15_000 });

  await insightsTab.click();
  await expect(insightsTab).toHaveAttribute("data-state", "active");
  const insightsPanel = page.getByRole("tabpanel").filter({
    has: page.getByText("Generate New Insight"),
  });
  await expect(insightsPanel).toBeVisible();
  const createdInsightCard = insightsPanel
    .locator("div.rounded-lg.border.bg-background.p-4")
    .filter({
      has: page.getByText("Mock insight for src-detail"),
    });
  await createdInsightCard.getByRole("button", { name: "View Insight" }).click();
  const insightDialog = page.getByRole("dialog", { name: "Source Insight" });
  await expect(insightDialog).toBeVisible();
  await expect(insightDialog.getByText("Mock insight for src-detail")).toBeVisible({
    timeout: 15_000,
  });
  await insightDialog.getByRole("button", { name: "Delete" }).click();
  await expect(insightDialog.getByRole("button", { name: "Cancel" })).toBeVisible();
  const deleteInsightResponsePromise = page.waitForResponse((response) => {
    return (
      response.request().method() === "DELETE" && /\/api\/insights\/insight-/.test(response.url())
    );
  });
  await insightDialog.getByRole("button", { name: "Delete", exact: true }).click();
  const deleteInsightResponse = await deleteInsightResponsePromise;
  expect(deleteInsightResponse.status()).toBe(200);
  await expect(insightDialog).toBeHidden();

  await expect(insightsPanel.getByText("Mock insight for src-detail")).toHaveCount(0);
});
