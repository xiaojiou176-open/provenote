import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

const shouldAssertVisualBaseline = process.env.PLAYWRIGHT_DISABLE_VISUAL_BASELINES !== "1";
test.describe.configure({ timeout: 120_000 });

test("settings: visual baseline", async ({ page }) => {
  test.setTimeout(60_000);
  await page.setViewportSize({ width: 1440, height: 900 });

  await setupMockApi(page, {
    settings: {
      default_content_processing_engine_doc: "auto",
      default_content_processing_engine_url: "auto",
      default_embedding_option: "ask",
      auto_delete_files: "no",
    },
  });

  await gotoWithReadyCheck(page, "/settings", async () => {
    await expect(page.getByRole("heading", { level: 1, name: "Settings" })).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByRole("button", { name: "Save" }).first()).toBeVisible({
      timeout: 30_000,
    });
  });

  if (shouldAssertVisualBaseline) {
    await expect(page).toHaveScreenshot("settings-overview.png", {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.03,
      maxDiffPixels: 16000,
    });
  }
});

test("settings: refresh and save update preferences", async ({ page }) => {
  test.setTimeout(90_000);
  let settingsGetRequests = 0;
  page.on("request", (request) => {
    if (request.method() === "GET" && request.url().includes("/api/settings")) {
      settingsGetRequests += 1;
    }
  });

  await setupMockApi(page, {
    settings: {
      default_content_processing_engine_doc: "auto",
      default_content_processing_engine_url: "auto",
      default_embedding_option: "ask",
      auto_delete_files: "no",
    },
  });

  await gotoWithReadyCheck(page, "/settings", async () => {
    await expect(page).toHaveURL(/\/settings$/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { level: 1, name: "Settings" })).toBeVisible({
      timeout: 30_000,
    });
  });
  await expect.poll(() => settingsGetRequests).toBeGreaterThan(0);

  const refreshButton = page.getByTestId("settings-refresh");
  const requestsBeforeRefresh = settingsGetRequests;
  await refreshButton.click();
  await expect.poll(() => settingsGetRequests).toBeGreaterThan(requestsBeforeRefresh);

  const saveButton = page.locator("form").getByRole("button", { name: "Save" });
  await expect(saveButton).toBeDisabled();

  await page.getByTestId("settings-doc-engine-trigger").click();
  await page.getByTestId("settings-doc-engine-docling").click();
  await expect(page.getByTestId("settings-doc-engine-trigger")).toContainText(/docling/i);

  await page.getByTestId("settings-embedding-trigger").click();
  await page.getByTestId("settings-embedding-always").click();
  await expect(page.getByTestId("settings-embedding-trigger")).toContainText(/always/i);

  await page.locator("#url_engine").click();
  await page.getByRole("option", { name: /jina/i }).click();
  await expect(page.locator("#url_engine")).toContainText(/jina/i);

  await page.locator("#auto_delete").click();
  await page.getByRole("option", { name: /^yes$/i }).click();
  await expect(page.locator("#auto_delete")).toContainText(/yes/i);

  await expect(saveButton).toBeEnabled();

  const saveResponse = page.waitForResponse((response) => {
    return response.request().method() === "PUT" && response.url().includes("/api/settings");
  });
  await page.getByRole("button", { name: "Save", exact: true }).last().click();

  const response = await saveResponse;
  expect(response.status()).toBe(200);
  expect(JSON.parse(response.request().postData() ?? "{}")).toMatchObject({
    default_content_processing_engine_doc: "docling",
    default_content_processing_engine_url: "jina",
    default_embedding_option: "always",
    auto_delete_files: "yes",
  });

  await expect(
    page.locator("form .ui-success-pop", { hasText: "Saved successfully" }),
  ).toBeVisible();
  await expect(saveButton).toBeDisabled();
});

test("settings: save failure shows error state and keeps submit enabled", async ({ page }) => {
  test.setTimeout(90_000);
  await setupMockApi(page, {
    settings: {
      default_content_processing_engine_doc: "auto",
      default_content_processing_engine_url: "auto",
      default_embedding_option: "ask",
      auto_delete_files: "no",
    },
    settingsUpdateStatus: 500,
  });

  await gotoWithReadyCheck(page, "/settings", async () => {
    await expect(page).toHaveURL(/\/settings$/, { timeout: 15_000 });
  });
  await expect(page.getByRole("heading", { level: 1, name: "Settings" })).toBeVisible({
    timeout: 30_000,
  });

  const saveButton = page.locator("form").getByRole("button", { name: "Save" });
  await expect(saveButton).toBeDisabled();

  await page.getByTestId("settings-doc-engine-trigger").click();
  await page.getByTestId("settings-doc-engine-docling").click();
  await expect(saveButton).toBeEnabled();

  const failedSaveResponse = page.waitForResponse((response) => {
    return response.request().method() === "PUT" && response.url().includes("/api/settings");
  });
  await saveButton.click();
  const response = await failedSaveResponse;

  expect(response.status()).toBe(500);
  expect(JSON.parse(response.request().postData() ?? "{}")).toMatchObject({
    default_content_processing_engine_doc: "docling",
  });

  await expect(page.locator("form .ui-form-error")).toBeVisible({ timeout: 15_000 });
  await expect(saveButton).toBeEnabled();
  await expect(page.locator("form .ui-success-pop")).toHaveCount(0);
});
