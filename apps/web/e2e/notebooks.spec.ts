import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

const shouldAssertVisualBaseline = process.env.PLAYWRIGHT_DISABLE_VISUAL_BASELINES !== "1";

test("notebooks: visual baseline", async ({ page }) => {
  test.setTimeout(60_000);
  await page.setViewportSize({ width: 1440, height: 900 });

  await setupMockApi(page, {
    notebooks: [
      {
        id: "nb-visual",
        name: "Visual Notebook",
        description: "Visual regression baseline notebook",
        archived: false,
        source_count: 3,
        note_count: 2,
        created: "2025-01-10T00:00:00.000Z",
        updated: "2025-01-11T00:00:00.000Z",
      },
    ],
  });

  await gotoWithReadyCheck(page, "/notebooks", async () => {
    await expect(page.getByRole("heading", { level: 1, name: "Notebooks" })).toBeVisible({
      timeout: 30_000,
    });
    await expect(
      page.locator('[data-slot="card-title"]', { hasText: "Visual Notebook" }),
    ).toBeVisible({ timeout: 30_000 });
  });

  if (shouldAssertVisualBaseline) {
    await expect(page).toHaveScreenshot("notebooks-overview.png", {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.03,
      maxDiffPixels: 12000,
    });
  }
});

test("notebooks: create a new notebook", async ({ page }) => {
  test.setTimeout(90_000);

  await setupMockApi(page, {
    notebooks: [
      {
        id: "nb-existing",
        name: "Existing Notebook",
        description: "Existing baseline notebook",
        archived: false,
        source_count: 2,
        note_count: 1,
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-02T00:00:00.000Z",
      },
    ],
  });

  await gotoWithReadyCheck(page, "/notebooks", async () => {
    await expect(page.getByRole("heading", { level: 1, name: "Notebooks" })).toBeVisible({
      timeout: 30_000,
    });
  });
  const newNotebookButton = page.getByRole("button", { name: "New Notebook" }).first();
  await expect(newNotebookButton).toBeVisible({ timeout: 30_000 });
  await newNotebookButton.click();

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible({ timeout: 10_000 });
  const submitButton = dialog.locator('button[type="submit"]');
  await expect(submitButton).toBeDisabled();
  await expect(dialog.locator("#notebook-name")).toHaveValue("");
  await expect(dialog.locator("#notebook-description")).toHaveValue("");
  const createNotebookResponse = page.waitForResponse((response) => {
    return response.request().method() === "POST" && /\/api\/notebooks\/?$/.test(response.url());
  });
  await dialog.locator("#notebook-name").fill("E2E Notebook");
  await expect(submitButton).toBeEnabled();
  await dialog.locator("#notebook-description").fill("Created in playwright e2e.");
  await submitButton.click();
  const response = await createNotebookResponse;
  expect(response.status()).toBe(201);
  expect(JSON.parse(response.request().postData() ?? "{}")).toMatchObject({
    name: "E2E Notebook",
    description: "Created in playwright e2e.",
  });

  await expect(dialog).toHaveCount(0);
  await expect(page.locator('[data-slot="card-title"]', { hasText: "E2E Notebook" })).toBeVisible();
  const searchInput = page.locator("#notebook-search");
  await searchInput.fill("E2E Notebook");
  const notebookTitles = page.locator('[data-slot="card-title"]:visible');
  await expect(notebookTitles.filter({ hasText: "E2E Notebook" })).toHaveCount(1);
  await expect(notebookTitles.filter({ hasText: "Existing Notebook" })).toHaveCount(0);
  await expect(page.getByRole("heading", { level: 1, name: "Notebooks" })).toBeVisible();
});

test("notebooks: refresh button refetches and search input filters cards", async ({ page }) => {
  test.setTimeout(90_000);
  let activeNotebookListRequests = 0;
  page.on("request", (request) => {
    if (
      request.method() === "GET" &&
      request.url().includes("/api/notebooks") &&
      request.url().includes("archived=false")
    ) {
      activeNotebookListRequests += 1;
    }
  });

  await setupMockApi(page, {
    notebooks: [
      {
        id: "nb-alpha",
        name: "Alpha Notebook",
        description: "Alpha baseline notebook",
        archived: false,
        source_count: 1,
        note_count: 1,
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-02T00:00:00.000Z",
      },
      {
        id: "nb-bravo",
        name: "Bravo Notebook",
        description: "Bravo baseline notebook",
        archived: false,
        source_count: 2,
        note_count: 2,
        created: "2025-01-03T00:00:00.000Z",
        updated: "2025-01-04T00:00:00.000Z",
      },
    ],
  });

  await gotoWithReadyCheck(page, "/notebooks", async () => {
    await expect.poll(() => activeNotebookListRequests, { timeout: 30_000 }).toBeGreaterThan(0);
    await expect(page.getByRole("heading", { level: 1, name: "Notebooks" })).toBeVisible({
      timeout: 30_000,
    });
  });

  const refreshButton = page.getByTestId("notebooks-refresh");
  const requestsBeforeRefresh = activeNotebookListRequests;
  await refreshButton.click();
  await expect
    .poll(() => activeNotebookListRequests, { timeout: 15_000 })
    .toBeGreaterThan(requestsBeforeRefresh);
  await expect(page.getByRole("heading", { level: 1, name: "Notebooks" })).toBeVisible();

  const searchInput = page.locator("#notebook-search");
  await expect(searchInput).toBeVisible();
  await expect(searchInput).toBeEditable();
  await searchInput.fill("Alpha");
  await expect(searchInput).toHaveValue("Alpha");
  const notebookTitles = page.locator('[data-slot="card-title"]:visible');
  await expect(notebookTitles.filter({ hasText: "Alpha Notebook" })).toHaveCount(1);
  await expect(notebookTitles.filter({ hasText: "Bravo Notebook" })).toHaveCount(0);
  await searchInput.fill("");
  await expect(searchInput).toHaveValue("");
  await expect(notebookTitles.filter({ hasText: "Alpha Notebook" })).toHaveCount(1);
  await expect(notebookTitles.filter({ hasText: "Bravo Notebook" })).toHaveCount(1);
});

test("notebooks: notebook title button supports keyboard activation", async ({ page }) => {
  test.setTimeout(60_000);
  await setupMockApi(page, {
    notebooks: [
      {
        id: "nb-keyboard",
        name: "Keyboard Notebook",
        description: "Notebook used for keyboard accessibility regression checks",
        archived: false,
        source_count: 1,
        note_count: 1,
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-02T00:00:00.000Z",
      },
    ],
  });

  await gotoWithReadyCheck(page, "/notebooks", async () => {
    await expect(page.getByRole("heading", { level: 1, name: "Notebooks" })).toBeVisible({
      timeout: 30_000,
    });
  });
  const notebookOpenButton = page.getByTestId("notebook-open-nb-keyboard");
  await expect(notebookOpenButton).toBeVisible({ timeout: 30_000 });
  await notebookOpenButton.focus();
  await expect(notebookOpenButton).toBeFocused();
  await Promise.all([
    page.waitForURL(/\/notebooks\/nb-keyboard(?:\/.*)?$/, { timeout: 15_000 }),
    page.keyboard.press("Enter"),
  ]);
  await expect(page).toHaveURL(/\/notebooks\/nb-keyboard(?:\/.*)?$/);
});
