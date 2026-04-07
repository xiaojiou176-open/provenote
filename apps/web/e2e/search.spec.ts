import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

const shouldAssertVisualBaseline = process.env.PLAYWRIGHT_DISABLE_VISUAL_BASELINES !== "1";
test.describe.configure({ timeout: 120_000 });

test("search: visual baseline", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });

  await setupMockApi(page, {
    models: [
      {
        id: "mdl-visual-chat",
        name: "gemini-2.5-flash",
        provider: "google",
        type: "language",
        credential: "cred-google",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
      {
        id: "mdl-visual-embed",
        name: "text-embedding-004",
        provider: "google",
        type: "embedding",
        credential: "cred-google",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
    ],
    modelDefaults: {
      default_chat_model: "mdl-visual-chat",
      default_transformation_model: "mdl-visual-chat",
      default_embedding_model: "mdl-visual-embed",
    },
  });

  await gotoWithReadyCheck(page, "/search", async () => {
    await expect(page).toHaveURL(/\/search$/, { timeout: 15_000 });
    await expect(page.locator("#ask-question")).toBeVisible({ timeout: 15_000 });
  });

  if (shouldAssertVisualBaseline) {
    await expect(page).toHaveScreenshot("search-ask-overview.png", {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.03,
      maxDiffPixels: 16000,
    });
  }
});

test("search: ask and search flows", async ({ page }) => {
  await setupMockApi(page, {
    models: [
      {
        id: "mdl-chat-1",
        name: "gemini-2.5-flash",
        provider: "google",
        type: "language",
        credential: "cred-google",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
      {
        id: "mdl-chat-2",
        name: "gemini-2.5-pro",
        provider: "google",
        type: "language",
        credential: "cred-google",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
      {
        id: "mdl-embed-1",
        name: "text-embedding-004",
        provider: "google",
        type: "embedding",
        credential: "cred-google",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
    ],
    modelDefaults: {
      default_chat_model: "mdl-chat-1",
      default_transformation_model: "mdl-chat-1",
      default_embedding_model: "mdl-embed-1",
    },
    searchResponse: {
      results: [
        {
          id: "search-1",
          title: "Result Source",
          parent_id: "source:src-1",
          final_score: 0.93,
          matches: ["Matched sentence"],
          created: "2025-01-01T00:00:00.000Z",
          updated: "2025-01-01T00:00:00.000Z",
        },
      ],
      total_count: 1,
      search_type: "text",
    },
  });

  await gotoWithReadyCheck(page, "/search", async () => {
    await expect(page).toHaveURL(/\/search$/, { timeout: 15_000 });
    await expect(page.locator("#ask-question")).toBeVisible({ timeout: 15_000 });
  });

  const askTabPanel = page.getByRole("tabpanel").filter({ has: page.locator("#ask-question") });
  const askButton = askTabPanel.getByRole("button", { name: "Ask", exact: true });
  await expect(askButton).toBeDisabled();
  await askTabPanel.getByRole("button", { name: /^advanced$/i }).click();
  const advancedDialog = page.getByRole("dialog");
  await expect(advancedDialog.getByText("Advanced Model Selection")).toBeVisible();
  await advancedDialog.getByRole("button", { name: "Save Changes" }).click();
  await expect(page.getByText("Using Custom Models")).toBeVisible();

  const askRequest = page.waitForRequest((request) => {
    return request.method() === "POST" && request.url().includes("/api/search/ask");
  });
  await page.locator("#ask-question").fill("What does the source say?");
  await expect(askButton).toBeEnabled();
  await askButton.click();

  const askPayload = JSON.parse((await askRequest).postData() ?? "{}");
  expect(askPayload).toMatchObject({
    question: "What does the source say?",
  });
  expect(typeof askPayload.strategy_model).toBe("string");
  expect(typeof askPayload.answer_model).toBe("string");
  expect(typeof askPayload.final_answer_model).toBe("string");

  await expect(page.getByText("Final synthesized answer for testing.")).toBeVisible();
  await expect(askButton).toBeEnabled({ timeout: 15_000 });
  await expect(page.getByRole("button", { name: "Save to Notebooks" })).toBeVisible();

  await page.getByRole("tab", { name: /search/i }).click();
  const searchSourcesCheckbox = page.getByRole("checkbox", { name: "Search Sources" });
  const searchNotesCheckbox = page.getByRole("checkbox", { name: "Search Notes" });
  await expect(searchNotesCheckbox).toHaveAttribute("data-state", "checked");
  await searchSourcesCheckbox.click();
  await expect(searchSourcesCheckbox).toHaveAttribute("data-state", "unchecked");

  const searchRequest = page.waitForRequest((request) => {
    return request.method() === "POST" && request.url().includes("/api/search");
  });
  const searchResponse = page.waitForResponse((response) => {
    return response.request().method() === "POST" && response.url().includes("/api/search");
  });
  const searchInput = page.locator("#search-query");
  const searchButton = page.getByRole("button", { name: /^Search/ }).last();
  await expect(searchButton).toBeDisabled();
  await expect(searchInput).toBeEnabled({ timeout: 15_000 });
  await searchInput.fill("vector database");
  await expect(searchButton).toBeEnabled();
  await searchInput.press("Enter");

  const request = await searchRequest;
  await searchResponse;
  expect(JSON.parse(request.postData() ?? "{}")).toMatchObject({
    query: "vector database",
    search_sources: false,
    search_notes: true,
  });
  const resultButton = page.getByRole("button", { name: "Result Source" });
  await expect.poll(async () => resultButton.count(), { timeout: 20_000 }).toBeGreaterThan(0);
  await expect(resultButton).toBeVisible({ timeout: 20_000 });
  await resultButton.click();
  const sourceDetailsDialog = page.getByRole("dialog", { name: "Source Details" });
  await expect(sourceDetailsDialog).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Matched sentence")).toBeVisible({ timeout: 10_000 });
  await expect(searchInput).toHaveValue("vector database");
  await sourceDetailsDialog.getByRole("button", { name: "Close" }).click();
  await expect(page).not.toHaveURL(/[\?&]modal=/, { timeout: 10_000 });
  await expect(sourceDetailsDialog).toBeHidden({ timeout: 10_000 });

  await page.locator("#vector").click();
  await expect(page.locator("#vector")).toHaveAttribute("data-state", "checked");

  const vectorSearchRequest = page.waitForRequest((request) => {
    return request.method() === "POST" && request.url().includes("/api/search");
  });
  await searchInput.fill("semantic recall");
  await searchButton.click();
  const vectorPayload = JSON.parse((await vectorSearchRequest).postData() ?? "{}");
  expect(vectorPayload).toMatchObject({
    query: "semantic recall",
    type: "vector",
    search_sources: false,
    search_notes: true,
  });

  await searchInput.fill("   ");
  await expect(searchButton).toBeDisabled();
});

test("search: ask stream error keeps save action hidden", async ({ page }) => {
  await setupMockApi(page, {
    models: [
      {
        id: "mdl-chat-error",
        name: "gemini-2.5-flash",
        provider: "google",
        type: "language",
        credential: "cred-google",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
      {
        id: "mdl-embed-error",
        name: "text-embedding-004",
        provider: "google",
        type: "embedding",
        credential: "cred-google",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
    ],
    modelDefaults: {
      default_chat_model: "mdl-chat-error",
      default_transformation_model: "mdl-chat-error",
      default_embedding_model: "mdl-embed-error",
    },
    askEvents: [
      {
        type: "strategy",
        reasoning: "Try a direct search first.",
        searches: [{ term: "error path", instructions: "Collect evidence." }],
      },
      { type: "answer", content: "Partial answer before failure." },
      { type: "error", message: "Mock stream failed." },
    ],
  });

  await gotoWithReadyCheck(page, "/search", async () => {
    await expect(page.locator("#ask-question")).toBeVisible({ timeout: 15_000 });
  });
  const askTabPanel = page.getByRole("tabpanel").filter({ has: page.locator("#ask-question") });
  const askButton = askTabPanel.getByRole("button", { name: "Ask", exact: true });
  const askInput = page.locator("#ask-question");

  await askInput.fill("Trigger stream error");
  await askButton.click();

  await expect(askButton).toBeEnabled({ timeout: 15_000 });
  await expect(page.getByRole("button", { name: "Save to Notebooks" })).toHaveCount(0);
  await expect(page.getByText("Final synthesized answer for testing.")).toHaveCount(0);
  await expect(askInput).toHaveValue("Trigger stream error");
});
