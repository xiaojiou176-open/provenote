import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

const shouldAssertVisualBaseline = process.env.PLAYWRIGHT_DISABLE_VISUAL_BASELINES !== "1";

test("sources: visual baseline", async ({ page }) => {
  test.setTimeout(60_000);
  await page.setViewportSize({ width: 1440, height: 900 });

  await setupMockApi(page, {
    sources: [
      {
        id: "src-visual",
        title: "Visual Source",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-02T00:00:00.000Z",
        insights_count: 2,
        embedded: true,
      },
    ],
  });

  await gotoWithReadyCheck(page, "/sources", async () => {
    await expect(page).toHaveURL(/\/sources$/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { level: 1, name: "Sources" })).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByText("Visual Source")).toBeVisible({ timeout: 30_000 });
  });

  if (shouldAssertVisualBaseline) {
    await expect(page).toHaveScreenshot("sources-table-overview.png", {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.03,
      maxDiffPixels: 17000,
    });
  }
});

test("sources: toggle sort and delete a source", async ({ page }) => {
  test.setTimeout(90_000);
  const listRequestUrls: string[] = [];
  const deleteRequestUrls: string[] = [];
  page.on("request", (request) => {
    if (request.method() === "GET" && request.url().includes("/api/sources")) {
      listRequestUrls.push(request.url());
    }
    if (request.method() === "DELETE" && /\/api\/sources\/[^/]+$/.test(request.url())) {
      deleteRequestUrls.push(request.url());
    }
  });

  await setupMockApi(page, {
    sources: [
      {
        id: "src-alpha",
        title: "Alpha Source",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-03T00:00:00.000Z",
        insights_count: 1,
        embedded: true,
      },
      {
        id: "src-bravo",
        title: "Bravo Source",
        created: "2025-01-03T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
        insights_count: 0,
        embedded: false,
      },
      {
        id: "src-charlie",
        title: "Charlie Source",
        created: "2025-01-02T00:00:00.000Z",
        updated: "2025-01-02T00:00:00.000Z",
        insights_count: 3,
        embedded: true,
      },
    ],
  });

  await gotoWithReadyCheck(page, "/sources", async () => {
    await expect(page).toHaveURL(/\/sources$/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { level: 1, name: "Sources" })).toBeVisible({
      timeout: 30_000,
    });
  });

  const rows = page.locator("tbody tr");
  await expect(rows).toHaveCount(3, { timeout: 15_000 });
  await expect(rows.first()).toContainText("Alpha Source", { timeout: 15_000 });
  await expect.poll(() => listRequestUrls.length, { timeout: 15_000 }).toBeGreaterThan(0);
  expect(listRequestUrls[0]).toContain("sort_by=updated");
  expect(listRequestUrls[0]).toContain("sort_order=desc");

  const createdHeader = page.getByRole("columnheader", { name: /created/i });
  const createdSortButton = page.getByRole("button", { name: /created/i });
  await expect(createdHeader).toHaveAttribute("aria-sort", "none");
  const firstRowBeforeToggle = (await rows.first().textContent()) ?? "";

  const firstSortRequest = page.waitForRequest((request) => {
    return (
      request.method() === "GET" &&
      request.url().includes("/api/sources") &&
      request.url().includes("sort_by=created")
    );
  });
  await createdSortButton.click();
  expect((await firstSortRequest).url()).toContain("sort_order=desc");
  const firstSortDirection = await createdHeader.getAttribute("aria-sort");
  expect(["ascending", "descending"]).toContain(firstSortDirection);
  const firstRowAfterFirstToggle = (await rows.first().textContent()) ?? "";
  expect(firstRowAfterFirstToggle).not.toEqual(firstRowBeforeToggle);

  const secondSortRequest = page.waitForRequest((request) => {
    return (
      request.method() === "GET" &&
      request.url().includes("/api/sources") &&
      request.url().includes("sort_by=created") &&
      request.url().includes("sort_order=asc")
    );
  });
  await createdSortButton.click();
  expect((await secondSortRequest).url()).toContain("sort_order=asc");
  const secondSortDirection = await createdHeader.getAttribute("aria-sort");
  expect(["ascending", "descending"]).toContain(secondSortDirection);
  expect(secondSortDirection).not.toBe(firstSortDirection);
  const firstRowAfterSecondToggle = (await rows.first().textContent()) ?? "";
  expect(firstRowAfterSecondToggle).toEqual(firstRowBeforeToggle);

  const bravoRow = page.getByTestId("source-row-src-bravo");
  await expect(bravoRow).toBeVisible();
  await bravoRow.getByTestId("source-delete").click();

  const dialog = page.getByRole("alertdialog");
  await expect(dialog).toContainText("Bravo Source");
  await dialog.getByRole("button", { name: "Cancel" }).click();
  await expect(dialog).toHaveCount(0);
  await expect(rows.filter({ hasText: "Bravo Source" })).toHaveCount(1);
  expect(deleteRequestUrls).toHaveLength(0);

  await bravoRow.getByTestId("source-delete").click();
  const confirmDialog = page.getByRole("alertdialog");
  await expect(confirmDialog).toContainText("Bravo Source");
  const deleteResponse = page.waitForResponse((response) => {
    return (
      response.request().method() === "DELETE" && response.url().includes("/api/sources/src-bravo")
    );
  });
  await confirmDialog.getByRole("button", { name: "Delete" }).click();
  const response = await deleteResponse;
  expect(response.status()).toBe(200);
  expect(deleteRequestUrls).toHaveLength(1);
  expect(deleteRequestUrls[0]).toContain("/api/sources/src-bravo");

  await expect(rows.filter({ hasText: "Bravo Source" })).toHaveCount(0);
  await expect(rows).toHaveCount(2);
});
