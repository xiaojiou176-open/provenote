import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

test("notebook detail: renders notebook context and sends notebook chat", async ({ page }) => {
  test.setTimeout(60_000);
  const notebookId = "nb-detail";
  const sessionId = "session-detail-1";
  let sessionMessages = [
    {
      id: "msg-ai-0",
      type: "ai",
      content: "Previous notebook answer",
      timestamp: "2026-01-01T00:00:00.000Z",
    },
  ];

  await setupMockApi(page, {
    notebooks: [
      {
        id: notebookId,
        name: "Deep Work Notebook",
        description: "Notebook detail coverage target",
        archived: false,
        source_count: 1,
        note_count: 0,
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-02T00:00:00.000Z",
      },
    ],
    sources: [
      {
        id: "source:detail-1",
        title: "Notebook source alpha",
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-02T00:00:00.000Z",
        embedded: true,
        insights_count: 1,
        notebooks: [notebookId],
      },
    ],
  });

  await page.route("**/api/chat/sessions?*", async (route) => {
    const url = new URL(route.request().url());
    const notebookParam = url.searchParams.get("notebook_id");
    if (route.request().method() === "GET" && notebookParam === notebookId) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: sessionId,
            notebook_id: notebookId,
            title: "Notebook detail session",
            model_override: null,
            message_count: sessionMessages.length,
            created: "2026-01-01T00:00:00.000Z",
            updated: "2026-01-02T00:00:00.000Z",
          },
        ]),
      });
      return;
    }
    await route.fallback();
  });

  await page.route("**/api/chat/sessions", async (route) => {
    if (route.request().method() !== "POST") {
      await route.fallback();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: sessionId,
        notebook_id: notebookId,
        title: "Notebook detail session",
        model_override: null,
        message_count: sessionMessages.length,
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-02T00:00:00.000Z",
      }),
    });
  });

  await page.route(`**/api/chat/sessions/${sessionId}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: sessionId,
        notebook_id: notebookId,
        title: "Notebook detail session",
        model_override: null,
        message_count: sessionMessages.length,
        created: "2026-01-01T00:00:00.000Z",
        updated: "2026-01-02T00:00:00.000Z",
        messages: sessionMessages,
      }),
    });
  });

  await page.route("**/api/chat/execute", async (route) => {
    const body = route.request().postDataJSON() as { message?: string; session_id?: string };
    sessionMessages = [
      {
        id: "msg-human-1",
        type: "human",
        content: body.message ?? "",
        timestamp: "2026-01-02T00:00:01.000Z",
      },
      {
        id: "msg-ai-1",
        type: "ai",
        content: "Notebook answer for detail e2e coverage.",
        timestamp: "2026-01-02T00:00:02.000Z",
      },
    ];
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session_id: body.session_id ?? sessionId,
        messages: sessionMessages,
      }),
    });
  });

  await gotoWithReadyCheck(
    page,
    `/notebooks/${notebookId}`,
    async () => {
      await expect(page.getByText("Deep Work Notebook")).toBeVisible({ timeout: 30_000 });
      await expect(
        page.getByRole("heading", { level: 4, name: "Notebook source alpha" }),
      ).toBeVisible({ timeout: 30_000 });
      await expect(page.getByText("Chat with Notebook")).toBeVisible({ timeout: 30_000 });
    },
    { timeout: 30_000, maxAttempts: 5 },
  );

  const chatInput = page.getByRole("textbox", { name: "Ask anything about your sources..." });
  await chatInput.fill("Summarize the notebook context");
  const sendButton = page.getByRole("button", { name: "Ask anything about your sources..." });
  await expect(sendButton).toBeEnabled();
  await sendButton.click();

  await expect(page.getByText("Summarize the notebook context")).toBeVisible();
  await expect(page.getByText("Notebook answer for detail e2e coverage.")).toBeVisible();
});
