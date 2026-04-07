import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

test("search ask: asserts intermediate stream semantics and final idle recovery", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await setupMockApi(page, {
    modelDefaults: {
      default_chat_model: "chat-model-1",
      default_embedding_model: "embedding-model-1",
    },
    askEvents: [
      {
        type: "strategy",
        reasoning: "Use search then summarize.",
        searches: [{ term: "topic", instructions: "find relevant context" }],
      },
      { type: "answer", content: "Partial answer chunk" },
      { type: "final_answer", content: "Final answer from stream" },
      { type: "complete" },
    ],
  });

  await gotoWithReadyCheck(page, "/search", async () => {
    await expect(page).toHaveURL(/\/search$/, { timeout: 15_000 });
    await expect(page.getByRole("button", { name: /^Ask$/ })).toBeVisible({ timeout: 30_000 });
  });

  await page.locator("#ask-question").fill("what is new");
  await page.getByRole("button", { name: /^Ask$/ }).click();

  const responseRegion = page.getByRole("region", { name: "Ask Response" });
  await expect(responseRegion).toBeVisible({ timeout: 30_000 });

  await expect(page.getByRole("button", { name: /^Strategy$/ })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: /^Strategy$/ }).click();
  await expect(page.getByText("Use search then summarize.")).toBeVisible({ timeout: 30_000 });

  await expect(page.getByRole("button", { name: /Individual Answers/i })).toBeVisible({
    timeout: 30_000,
  });
  await page.getByRole("button", { name: /Individual Answers/i }).click();
  await expect(page.getByText("Partial answer chunk")).toBeVisible({ timeout: 30_000 });

  await expect(page.getByText("Final answer from stream")).toBeVisible({ timeout: 30_000 });
  await expect(responseRegion).toHaveAttribute("aria-busy", "false");
  await expect(page.getByRole("button", { name: /^Ask$/ })).toBeEnabled();
  await expect(page.getByRole("button", { name: /^Cancel$/ })).toHaveCount(0);
  await expect(page.locator("#ask-question")).toBeEnabled();
});
