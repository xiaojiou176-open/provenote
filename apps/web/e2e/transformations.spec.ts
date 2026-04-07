import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

test("transformations: opens playground and executes a transformation", async ({ page }) => {
  test.setTimeout(60_000);
  await setupMockApi(page, {
    transformations: [
      {
        id: "tr-summary",
        name: "summary_table",
        title: "Summary Table",
        description: "Create a concise table summary",
        prompt: "Summarize the input as a markdown table.",
        apply_default: true,
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-02T00:00:00.000Z",
      },
    ],
    models: [
      {
        id: "mdl-transform",
        name: "gemini-2.5-flash",
        provider: "google",
        type: "language",
        credential: "cred-google",
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-01T00:00:00.000Z",
      },
    ],
  });

  await gotoWithReadyCheck(page, "/transformations", async () => {
    await expect(page.getByRole("heading", { level: 1, name: "Transformations" })).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByText("summary_table")).toBeVisible({ timeout: 30_000 });
  });

  await page.getByRole("button", { name: "Playground" }).first().click();
  await expect(page.getByText("Input Text")).toBeVisible({ timeout: 30_000 });

  await page.locator("#transformation").click();
  await page.getByRole("option", { name: /summary_table/i }).click();
  await page.getByLabel("Model").click();
  await page.getByRole("option", { name: /gemini-2.5-flash/i }).click();
  await page.locator("textarea[name='input']").fill("Transform this content into bullet points.");

  const executeRequest = page.waitForRequest((request) => {
    return request.method() === "POST" && request.url().includes("/api/transformations/execute");
  });

  await page.getByRole("button", { name: "Run Transformation" }).click();

  const request = await executeRequest;
  expect(request.postDataJSON()).toMatchObject({
    transformation_id: "tr-summary",
    model_id: "mdl-transform",
    input_text: "Transform this content into bullet points.",
  });

  await expect(page.getByText(/Mock output \(summary_table\):/)).toBeVisible({ timeout: 30_000 });
});
