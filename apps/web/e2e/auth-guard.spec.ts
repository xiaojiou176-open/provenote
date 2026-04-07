import { expect, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

test("auth guard: login rejects invalid password and restores redirect target", async ({
  page,
}) => {
  test.setTimeout(60_000);
  await setupMockApi(page, { authEnabled: true });
  let sawWrongAuthProbe = false;
  let sawCorrectAuthProbe = false;

  const waitForNotebookAuthProbe = (token: string, expectedStatus: number) =>
    page.waitForResponse(
      (response) => {
        const request = response.request();
        const authorization = request.headers()["authorization"];
        return (
          request.method() === "GET" &&
          /\/api\/notebooks/.test(response.url()) &&
          authorization?.toLowerCase() === `bearer ${token}` &&
          response.status() === expectedStatus
        );
      },
      { timeout: 45_000 },
    );

  await page.route("**/api/notebooks**", (route) => {
    const authorization = route.request().headers()["authorization"];
    if (authorization === "Bearer wrong-password") {
      sawWrongAuthProbe = true;
      return route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Unauthorized" }),
      });
    }

    if (authorization === "Bearer correct-password") {
      sawCorrectAuthProbe = true;
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
    }

    return route.fallback();
  });

  const signInButton = page.getByRole("button", { name: "Sign In" });
  await gotoWithReadyCheck(
    page,
    "/login",
    async () => {
      await expect(page).toHaveURL(/\/login$/, { timeout: 15_000 });
      await expect(signInButton).toBeVisible({ timeout: 30_000 });
    },
    { waitUntil: "load" },
  );
  await page.evaluate(() => {
    sessionStorage.setItem("redirectAfterLogin", "/notebooks");
  });
  await expect(signInButton).toBeDisabled();

  await page.getByPlaceholder("Password").fill("wrong-password");
  await expect(signInButton).toBeEnabled();

  const failedAuthProbe = waitForNotebookAuthProbe("wrong-password", 401);
  await signInButton.click();
  await failedAuthProbe;

  await expect(page.getByText("Invalid password. Please try again.")).toBeVisible();
  await expect(page).toHaveURL(/\/login$/);
  expect(sawWrongAuthProbe).toBe(true);

  const redirectAfterLogin = await page.evaluate(() =>
    sessionStorage.getItem("redirectAfterLogin"),
  );
  expect(redirectAfterLogin).toBe("/notebooks");

  await page.getByPlaceholder("Password").fill("correct-password");
  await expect(signInButton).toBeEnabled();
  const successfulAuthProbe = waitForNotebookAuthProbe("correct-password", 200);
  await signInButton.click();
  await successfulAuthProbe;
  expect(sawCorrectAuthProbe).toBe(true);

  await expect(page).toHaveURL(/\/notebooks$/, { timeout: 15_000 });
  await expect(page.getByRole("heading", { level: 1, name: "Notebooks" })).toBeVisible({
    timeout: 15_000,
  });
});
