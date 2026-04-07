import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

const shouldAssertVisualBaseline = process.env.PLAYWRIGHT_DISABLE_VISUAL_BASELINES !== "1";

test("settings api keys: visual baseline", async ({ page }) => {
  test.setTimeout(60_000);
  await page.setViewportSize({ width: 1440, height: 900 });

  await setupMockApi(page, {
    credentials: [
      {
        id: "cred-visual",
        name: "Gemini Visual",
        provider: "google",
        modalities: ["language", "embedding", "text_to_speech"],
        has_api_key: true,
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-02T00:00:00.000Z",
        model_count: 2,
      },
    ],
    models: [
      {
        id: "mdl-visual-key-chat",
        name: "gemini-2.5-flash",
        provider: "google",
        type: "language",
        credential: "cred-visual",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
      {
        id: "mdl-visual-key-embed",
        name: "text-embedding-004",
        provider: "google",
        type: "embedding",
        credential: "cred-visual",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
    ],
  });

  await gotoWithReadyCheck(page, "/settings/api-keys", async () => {
    await expect(
      page.getByRole("heading", { level: 1, name: "Configure your AI with your own API keys" }),
    ).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText("Gemini Visual")).toBeVisible({ timeout: 30_000 });
  });

  if (shouldAssertVisualBaseline) {
    await expect(page).toHaveScreenshot("settings-api-keys-overview.png", {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.035,
      maxDiffPixels: 32000,
    });
  }
});

test("settings api keys: add config, register models, delete config", async ({ page }) => {
  test.setTimeout(90_000);
  let createCredentialRequests = 0;
  page.on("request", (request) => {
    if (request.method() === "POST" && /\/api\/credentials\/?$/.test(request.url())) {
      createCredentialRequests += 1;
    }
  });

  await setupMockApi(page, {
    modelDefaults: {
      default_chat_model: null,
      default_transformation_model: null,
      default_embedding_model: null,
    },
    discoveredByProvider: {
      google: [
        { name: "gemini-2.5-flash", provider: "google" },
        { name: "gemini-2.5-pro", provider: "google" },
        { name: "text-embedding-004", provider: "google" },
      ],
    },
  });

  await gotoWithReadyCheck(page, "/settings/api-keys", async () => {
    await expect(page).toHaveURL(/\/settings\/api-keys$/, { timeout: 15_000 });
    await expect(
      page.getByRole("heading", { level: 1, name: "Configure your AI with your own API keys" }),
    ).toBeVisible({ timeout: 30_000 });
  });

  await page
    .getByRole("button", { name: /add configuration/i })
    .first()
    .click();
  const cancelledDialog = page.getByRole("dialog");
  await expect(cancelledDialog).toBeVisible();
  await cancelledDialog.locator("#cred-name").fill("Cancelled Config");
  await cancelledDialog.getByRole("button", { name: "Cancel" }).click();
  await expect(cancelledDialog).toHaveCount(0);
  expect(createCredentialRequests).toBe(0);
  await expect(page.getByText("Cancelled Config")).toHaveCount(0);

  await page
    .getByRole("button", { name: /add configuration/i })
    .first()
    .click();

  const formDialog = page.getByRole("dialog");
  await expect(formDialog).toBeVisible();
  const submitCredentialButton = formDialog.getByRole("button", { name: /add configuration/i });
  await expect(submitCredentialButton).toBeDisabled();
  const apiKeyInput = formDialog.locator("#api-key");
  const showApiKeyButton = formDialog.getByRole("button", { name: "Show API key" });
  await showApiKeyButton.click();
  await expect(apiKeyInput).toHaveAttribute("type", "text");
  const hideApiKeyButton = formDialog.getByRole("button", { name: "Hide API key" });
  await expect(hideApiKeyButton).toHaveAttribute("aria-pressed", "true");
  await hideApiKeyButton.click();
  await expect(apiKeyInput).toHaveAttribute("type", "password");
  const createCredentialResponse = page.waitForResponse((response) => {
    return response.url().includes("/api/credentials") && response.request().method() === "POST";
  });
  await formDialog.locator("#cred-name").fill("Gemini Primary");
  await expect(submitCredentialButton).toBeDisabled();
  await formDialog.locator("#api-key").fill("sk-test-key");
  await expect(submitCredentialButton).toBeEnabled();
  await formDialog.locator('button[type="submit"]').click();
  const credentialCreateResult = await createCredentialResponse;
  expect(credentialCreateResult.status()).toBe(201);
  expect(JSON.parse(credentialCreateResult.request().postData() ?? "{}")).toMatchObject({
    name: "Gemini Primary",
  });

  const credentialCard = page
    .getByTestId("credential-card")
    .filter({ hasText: "Gemini Primary" })
    .first();
  await expect(credentialCard).toBeVisible({ timeout: 20_000 });
  const syncModelsButton = credentialCard.getByTestId("credential-sync-models");
  await expect(syncModelsButton).toBeVisible({ timeout: 20_000 });
  const discoverResponse = page.waitForResponse((response) => {
    return (
      response.request().method() === "POST" &&
      /\/api\/credentials\/[^/]+\/discover$/.test(response.url())
    );
  });
  await syncModelsButton.click();
  await expect((await discoverResponse).status()).toBe(200);

  const discoverDialog = page.getByRole("dialog");
  await expect(discoverDialog).toBeVisible({ timeout: 20_000 });
  await expect(discoverDialog.getByText("gemini-2.5-flash")).toBeVisible({ timeout: 20_000 });
  await expect(discoverDialog.getByText("gemini-2.5-pro")).toBeVisible({ timeout: 20_000 });
  const addModelButton = discoverDialog.getByRole("button", { name: "Add (0)" });
  await expect(addModelButton).toBeDisabled();
  const discoverSearchInput = discoverDialog.locator('input[type="text"]').first();
  await discoverSearchInput.fill("pro");
  await expect(discoverDialog.getByText("gemini-2.5-pro")).toBeVisible();
  await expect(discoverDialog.getByText("gemini-2.5-flash")).toHaveCount(0);
  await discoverDialog.getByLabel("gemini-2.5-pro").check();
  await expect(discoverDialog.getByRole("button", { name: "Add (1)" })).toBeEnabled();
  const registerModelsResponse = page.waitForResponse((response) => {
    return (
      response.request().method() === "POST" &&
      /\/api\/credentials\/[^/]+\/register-models$/.test(response.url())
    );
  });
  await discoverDialog.getByRole("button", { name: /Add \(1\)/ }).click();
  const registerResult = await registerModelsResponse;
  expect(registerResult.status()).toBe(200);
  expect(JSON.parse(registerResult.request().postData() ?? "{}")).toMatchObject({
    models: [expect.objectContaining({ name: "gemini-2.5-pro" })],
  });
  await expect(discoverDialog).toHaveCount(0);

  await expect(credentialCard.getByText("gemini-2.5-pro")).toBeVisible();

  await credentialCard.getByTestId("credential-delete").click();
  const deleteDialog = page.getByRole("dialog");
  await deleteDialog.getByRole("button", { name: "Cancel" }).click();
  await expect(deleteDialog).toHaveCount(0);
  await expect(credentialCard).toBeVisible();

  await credentialCard.getByTestId("credential-delete").click();
  const deleteDialogConfirm = page.getByRole("dialog");
  const deleteCredentialResponse = page.waitForResponse((response) => {
    return (
      response.request().method() === "DELETE" &&
      /\/api\/credentials\/[^/?]+/.test(response.url()) &&
      response.url().includes("delete_models=true")
    );
  });
  await deleteDialogConfirm.getByRole("button", { name: "Delete with Models" }).click();
  await expect((await deleteCredentialResponse).status()).toBe(200);

  await expect(page.getByText("Gemini Primary")).toHaveCount(0);

  await page
    .getByRole("button", { name: /add configuration/i })
    .first()
    .click();
  const secondaryDialog = page.getByRole("dialog");
  await secondaryDialog.locator("#cred-name").fill("Gemini Secondary");
  await secondaryDialog.locator("#api-key").fill("sk-secondary-key");
  const createSecondaryCredentialResponse = page.waitForResponse((response) => {
    return response.url().includes("/api/credentials") && response.request().method() === "POST";
  });
  await secondaryDialog.locator('button[type="submit"]').click();
  await expect((await createSecondaryCredentialResponse).status()).toBe(201);

  const secondaryCredentialCard = page
    .getByTestId("credential-card")
    .filter({ hasText: "Gemini Secondary" })
    .first();
  await expect(secondaryCredentialCard).toBeVisible({ timeout: 20_000 });
  await secondaryCredentialCard.getByTestId("credential-delete").click();
  const secondaryDeleteDialog = page.getByRole("dialog");
  const deleteOnlyResponse = page.waitForResponse((response) => {
    return (
      response.request().method() === "DELETE" &&
      /\/api\/credentials\/[^/?]+/.test(response.url()) &&
      !response.url().includes("delete_models=true")
    );
  });
  await secondaryDeleteDialog.getByRole("button", { name: "Delete" }).click();
  await expect((await deleteOnlyResponse).status()).toBe(200);
  await expect(page.getByText("Gemini Secondary")).toHaveCount(0);
});
