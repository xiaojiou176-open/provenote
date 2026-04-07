import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

test.describe.configure({ timeout: 120_000 });

test("smoke: notebooks page loads and critical controls are interactive", async ({ page }) => {
  await setupMockApi(page, {
    notebooks: [
      {
        id: "nb-smoke-controls",
        name: "Smoke Controls Notebook",
        description: "Control readiness notebook",
        archived: false,
        source_count: 2,
        note_count: 1,
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
    ],
  });

  await gotoWithReadyCheck(
    page,
    "/notebooks",
    async () => {
      await expect(page.getByRole("heading", { level: 1, name: "Notebooks" })).toBeVisible({
        timeout: 15_000,
      });
      await expect(page.getByTestId("notebooks-refresh")).toBeVisible({ timeout: 15_000 });
      await expect(
        page.locator('[data-slot="card-title"]', { hasText: "Smoke Controls Notebook" }),
      ).toBeVisible({
        timeout: 15_000,
      });
    },
    { maxAttempts: 6 },
  );

  const newNotebookButton = page.getByRole("button", { name: "New Notebook" }).first();
  await expect(newNotebookButton).toBeVisible({ timeout: 15_000 });
  await expect(newNotebookButton).toBeEnabled();

  const refreshButton = page.getByTestId("notebooks-refresh");
  await expect(refreshButton).toBeVisible();
  await expect(refreshButton).toBeEnabled();
  await refreshButton.click();

  const searchInput = page.locator("#notebook-search");
  await expect(searchInput).toBeVisible();
  await expect(searchInput).toBeEditable();
  await searchInput.fill("Smoke Controls");
  await expect(searchInput).toHaveValue("Smoke Controls");
  await expect(
    page.locator('[data-slot="card-title"]', { hasText: "Smoke Controls Notebook" }),
  ).toBeVisible();
});
