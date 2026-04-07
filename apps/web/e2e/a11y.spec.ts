import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";
import { setupMockApi } from "./mock-api";
import { gotoWithReadyCheck } from "./navigation";

const colorContrastDisableRequested = process.env.PLAYWRIGHT_DISABLE_COLOR_CONTRAST_CHECK === "1";
const colorContrastDisableReason = (
  process.env.PLAYWRIGHT_DISABLE_COLOR_CONTRAST_REASON ?? ""
).trim();
const isCiEnvironment = process.env.CI === "true";

if (colorContrastDisableRequested && colorContrastDisableReason.length === 0) {
  throw new Error(
    "PLAYWRIGHT_DISABLE_COLOR_CONTRAST_CHECK=1 requires PLAYWRIGHT_DISABLE_COLOR_CONTRAST_REASON to avoid accidental a11y blind spots.",
  );
}

if (isCiEnvironment && colorContrastDisableRequested) {
  throw new Error(
    "CI must not disable axe color-contrast checks. Remove PLAYWRIGHT_DISABLE_COLOR_CONTRAST_CHECK override in CI.",
  );
}

const disableColorContrastCheck =
  !isCiEnvironment && colorContrastDisableRequested && colorContrastDisableReason.length > 0;
const pageReadiness: Record<string, (page: Page) => Promise<void>> = {
  "/notebooks": async (page) => {
    await expect(page.getByRole("main").getByTestId("notebooks-refresh")).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByRole("heading", { level: 1, name: "Notebooks" })).toBeVisible({
      timeout: 30_000,
    });
  },
  "/search": async (page) => {
    await expect(page.locator("#ask-question")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole("heading", { level: 1, name: "Ask and Search" })).toBeVisible({
      timeout: 30_000,
    });
  },
  "/sources": async (page) => {
    await expect(page.getByRole("heading", { level: 1, name: "Sources" })).toBeVisible({
      timeout: 30_000,
    });
  },
  "/settings": async (page) => {
    await expect(page.getByRole("heading", { level: 1, name: "Settings" })).toBeVisible({
      timeout: 30_000,
    });
  },
  "/podcasts": async (page) => {
    await expect(page.getByRole("main").getByTestId("a11y-route-podcasts-ready")).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByRole("heading", { level: 1, name: /podcast/i })).toBeVisible({
      timeout: 30_000,
    });
  },
  "/advanced": async (page) => {
    await expect(page.getByRole("main").getByTestId("a11y-route-advanced-ready")).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByRole("heading", { level: 1, name: /advanced/i })).toBeVisible({
      timeout: 30_000,
    });
  },
  "/transformations": async (page) => {
    await expect(page.getByRole("heading", { level: 1, name: /transformations/i })).toBeVisible({
      timeout: 30_000,
    });
  },
  "/settings/api-keys": async (page) => {
    await expect(
      page.getByRole("main").getByTestId("a11y-route-settings-api-keys-ready"),
    ).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole("heading", { level: 1, name: /configure your ai/i })).toBeVisible({
      timeout: 30_000,
    });
  },
};

const routePaths = Object.keys(pageReadiness) as Array<keyof typeof pageReadiness>;

async function applyTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate((selectedTheme) => {
    window.localStorage.setItem(
      "theme-storage",
      JSON.stringify({
        state: { theme: selectedTheme },
        version: 0,
      }),
    );

    const root = window.document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(selectedTheme);
    root.setAttribute("data-theme", selectedTheme);
  }, theme);
}

async function assertNoModerateA11yViolations(
  pagePath: string,
  theme: "light" | "dark",
  page: Page,
) {
  const readiness = pageReadiness[pagePath];
  if (!readiness) {
    throw new Error(`Missing page readiness configuration for route: ${pagePath}`);
  }
  await gotoWithReadyCheck(
    page,
    pagePath,
    async () => {
      await expect(page).toHaveURL(new RegExp(`${pagePath}$`), { timeout: 15_000 });
      await readiness(page);
    },
    { timeout: 45_000, maxAttempts: 3 },
  );
  await applyTheme(page, theme);
  await page.waitForFunction((selectedTheme) => {
    return window.document.documentElement.classList.contains(selectedTheme);
  }, theme);

  const axeBuilder = new AxeBuilder({ page });
  if (disableColorContrastCheck) {
    console.warn(
      `[a11y] color-contrast rule disabled via explicit override. reason="${colorContrastDisableReason}"`,
    );
    axeBuilder.disableRules(["color-contrast"]);
  }

  const results = await axeBuilder.analyze();
  const blockers = results.violations.filter(
    (violation) =>
      violation.impact === "moderate" ||
      violation.impact === "serious" ||
      violation.impact === "critical",
  );

  expect(
    blockers,
    [
      `Found ${blockers.length} moderate/serious/critical accessibility violation(s) on ${pagePath} (${theme} theme):`,
      ...blockers.map((violation) => `- ${violation.id}: ${violation.help}`),
    ].join("\n"),
  ).toEqual([]);
}

async function setupA11yMocks(page: Page) {
  await setupMockApi(page, {
    notebooks: [
      {
        id: "nb-a11y",
        name: "Accessibility Notebook",
        description: "Notebook used for accessibility regression checks",
        archived: false,
        source_count: 1,
        note_count: 1,
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
      },
    ],
    sources: [
      {
        id: "src-a11y",
        title: "Accessibility Source",
        created: "2025-01-01T00:00:00.000Z",
        updated: "2025-01-01T00:00:00.000Z",
        insights_count: 1,
        embedded: true,
      },
    ],
  });
}

for (const pagePath of routePaths) {
  for (const theme of ["light", "dark"] as const) {
    test(`a11y: ${pagePath} has no moderate+ violations (${theme})`, async ({ page }) => {
      test.setTimeout(120_000);
      await setupA11yMocks(page);
      await assertNoModerateA11yViolations(pagePath, theme, page);
    });
  }
}
