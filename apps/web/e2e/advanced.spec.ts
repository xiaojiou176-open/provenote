import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

const shouldAssertVisualBaseline = process.env.PLAYWRIGHT_DISABLE_VISUAL_BASELINES !== "1";

test("advanced: rebuild controls validate payload and accordion details", async ({ page }) => {
  test.setTimeout(60_000);
  await setupMockApi(page, {
    rebuildStatus: {
      status: "completed",
      progress: {
        total_items: 8,
        processed_items: 8,
        failed_items: 0,
        percentage: 100,
      },
      stats: {
        sources_processed: 4,
        notes_processed: 3,
        insights_processed: 1,
        failed_items: 0,
        processing_time: 1.2,
      },
    },
  });

  await gotoWithReadyCheck(page, "/advanced", async () => {
    await expect(page).toHaveURL(/\/advanced$/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { level: 1, name: "AdvancedTools" })).toBeVisible({
      timeout: 30_000,
    });
  });

  await page.getByRole("button", { name: "When should I rebuild embeddings?" }).click();
  await expect(page.getByText(/switching models/i)).toBeVisible();

  const includeSources = page.getByRole("checkbox", { name: "Sources" });
  const includeNotes = page.getByRole("checkbox", { name: "Notes" });
  const includeInsights = page.getByRole("checkbox", { name: "Insights" });
  const startRebuild = page.getByRole("button", { name: /start rebuild/i });

  await includeSources.click();
  await includeNotes.click();
  await includeInsights.click();
  await expect(startRebuild).toBeDisabled();

  await includeSources.click();
  await expect(startRebuild).toBeEnabled();

  if (shouldAssertVisualBaseline) {
    await expect(page).toHaveScreenshot("advanced-rebuild-audit.png", {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.03,
      maxDiffPixels: 26000,
    });
  }

  const rebuildResponse = page.waitForResponse((response) => {
    return (
      response.request().method() === "POST" && response.url().includes("/api/embeddings/rebuild")
    );
  });
  await startRebuild.click();

  const response = await rebuildResponse;
  expect(response.status()).toBe(200);
  expect(JSON.parse(response.request().postData() ?? "{}")).toMatchObject({
    mode: "existing",
    include_sources: true,
    include_notes: false,
    include_insights: false,
  });
});
