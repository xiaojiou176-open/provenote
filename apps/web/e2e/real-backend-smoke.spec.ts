import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { expect, type Page, type TestInfo, test } from "@playwright/test";

const RESPONSE_TIMEOUT_MS = 30_000;
const UI_READY_TIMEOUT_MS = 20_000;
const allowOfflineDbStatus = process.env.PLAYWRIGHT_ALLOW_DB_OFFLINE_DB_STATUS === "1";
const realBackendModeEnabled = process.env.PLAYWRIGHT_REAL_BACKEND === "1";
const REAL_BACKEND_TEST_PASSWORD =
  process.env.OPEN_NOTEBOOK_PASSWORD ?? "open-notebook-test-password";
const ACTION_EVIDENCE_SPEC_ID = "real-backend-smoke.spec.ts";
const runtimeActionEvidencePath = process.env.PLAYWRIGHT_ACTION_EVIDENCE_FILE?.trim();

type RuntimeEvidenceLayer = "ui-ready" | "network-contract" | "payload-shape";

type RuntimeActionEvidenceEntry = {
  action_id: string;
  spec_id: string;
  route: string;
  layers: RuntimeEvidenceLayer[];
  observed_at: string;
  details: Record<string, unknown>;
};

const runtimeActionEvidenceEntries: RuntimeActionEvidenceEntry[] = [];

function requireRealBackendMode() {
  if (!realBackendModeEnabled) {
    throw new Error("PLAYWRIGHT_REAL_BACKEND=1 is required for real-backend smoke checks.");
  }
}

function recordRuntimeActionEvidence(
  actionId: string,
  route: string,
  layers: RuntimeEvidenceLayer[],
  details: Record<string, unknown>,
) {
  runtimeActionEvidenceEntries.push({
    action_id: actionId,
    spec_id: ACTION_EVIDENCE_SPEC_ID,
    route,
    layers,
    observed_at: new Date().toISOString(),
    details,
  });
}

function attachFailureLogs(page: Page, testInfo: TestInfo) {
  const logs: string[] = [];
  const push = (line: string) => logs.push(`[${new Date().toISOString()}] ${line}`);

  page.on("console", (msg) => push(`console.${msg.type()}: ${msg.text()}`));
  page.on("pageerror", (error) => push(`pageerror: ${error.message}`));
  page.on("requestfailed", (request) =>
    push(
      `requestfailed ${request.method()} ${request.url()} :: ${request.failure()?.errorText ?? "unknown"}`,
    ),
  );
  page.on("response", (response) => {
    if (response.status() >= 400) {
      push(`response.${response.status()} ${response.request().method()} ${response.url()}`);
    }
  });

  return async () => {
    const pageDiagnostics = {
      currentUrl: page.url(),
      title: await page.title().catch(() => "<title unavailable>"),
      readyState: await page
        .evaluate(() => document.readyState)
        .catch(() => "<readyState unavailable>"),
    };

    await testInfo.attach("runtime-debug.log", {
      body: (logs.length > 0 ? logs : ["no runtime errors captured"]).join("\n"),
      contentType: "text/plain",
    });
    await testInfo.attach("runtime-debug-context.json", {
      body: JSON.stringify(pageDiagnostics, null, 2),
      contentType: "application/json",
    });
  };
}

async function waitForPageStability(page: Page, criticalElement: ReturnType<Page["locator"]>) {
  // Real-backend mode may keep long-lived network activity (polling/HMR/websocket),
  // so "networkidle" can hang even when the UI is ready.
  await page.waitForLoadState("domcontentloaded");
  await expect(criticalElement).toBeVisible({ timeout: UI_READY_TIMEOUT_MS });
}

async function bootstrapAuthenticatedSession(page: Page, targetPath: string) {
  await page.addInitScript((token: string) => {
    sessionStorage.setItem(
      "auth-storage",
      JSON.stringify({
        state: { token, isAuthenticated: true },
        version: 0,
      }),
    );
  }, REAL_BACKEND_TEST_PASSWORD);
  await page.goto(targetPath);

  if (!page.url().includes("/login")) {
    return;
  }

  const passwordInput = page.locator('input[type="password"]').first();
  await expect(passwordInput).toBeVisible({ timeout: UI_READY_TIMEOUT_MS });
  const signInButton = page.locator('button[type="submit"]').first();
  await passwordInput.fill(REAL_BACKEND_TEST_PASSWORD);
  await expect(signInButton).toBeEnabled({ timeout: UI_READY_TIMEOUT_MS });
  await signInButton.click();
  await expect(passwordInput).toBeHidden({ timeout: UI_READY_TIMEOUT_MS });

  if (!page.url().includes(targetPath)) {
    await page.goto(targetPath);
  }
}

test.afterAll(async () => {
  if (!runtimeActionEvidencePath) {
    return;
  }
  await mkdir(dirname(runtimeActionEvidencePath), { recursive: true });
  await writeFile(
    runtimeActionEvidencePath,
    `${JSON.stringify(
      {
        generated_at: new Date().toISOString(),
        source: ACTION_EVIDENCE_SPEC_ID,
        entries: runtimeActionEvidenceEntries,
      },
      null,
      2,
    )}\n`,
    "utf-8",
  );
});

test("smoke: notebooks page requests real backend config endpoint", async ({ page }) => {
  requireRealBackendMode();

  await bootstrapAuthenticatedSession(page, "/notebooks");
  const configResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/config") && response.request().method() === "GET",
    { timeout: RESPONSE_TIMEOUT_MS },
  );
  await page.reload();
  await waitForPageStability(page, page.getByTestId("notebooks-refresh"));

  const configResponse = await configResponsePromise;
  expect(configResponse.ok()).toBe(true);
  expect(configResponse.status()).toBe(200);

  const payload = (await page.evaluate(async () => {
    const response = await fetch("/api/config");
    return response.json();
  })) as { dbStatus?: string; version?: string };
  expect(typeof payload.version).toBe("string");
  expect(payload.version?.trim().length ?? 0).toBeGreaterThan(0);
  expect(typeof payload.dbStatus).toBe("string");
  const acceptedDbStatus = allowOfflineDbStatus ? ["online", "offline"] : ["online"];
  expect(acceptedDbStatus).toContain(payload.dbStatus ?? "");

  await expect(page).toHaveURL(/\/notebooks/);
});

test("cuj: notebooks list loads from real backend and refresh keeps interactive state", async ({
  page,
}, testInfo) => {
  requireRealBackendMode();
  const flushLogs = attachFailureLogs(page, testInfo);

  const notebookResponses: Array<{ url: string; status: number; bodyType: string }> = [];
  page.on("response", async (response) => {
    if (response.request().method() === "GET" && response.url().includes("/api/notebooks")) {
      let bodyType = "unknown";
      try {
        const payload = await response.json();
        bodyType = Array.isArray(payload) ? "array" : typeof payload;
      } catch {
        bodyType = "non-json";
      }
      notebookResponses.push({
        url: response.url(),
        status: response.status(),
        bodyType,
      });
    }
  });

  try {
    await bootstrapAuthenticatedSession(page, "/notebooks");

    const initialNotebooksResponsePromise = page.waitForResponse(
      (response) =>
        response.request().method() === "GET" && response.url().includes("/api/notebooks"),
      { timeout: RESPONSE_TIMEOUT_MS },
    );
    await page.reload();
    await waitForPageStability(page, page.getByTestId("notebooks-refresh"));

    const initialNotebooksResponse = await initialNotebooksResponsePromise;
    expect(initialNotebooksResponse.status()).toBe(200);
    const initialNotebooksRequestUrl = initialNotebooksResponse.request().url();
    expect(initialNotebooksRequestUrl).toContain("/api/notebooks");
    const initialNotebooksPayload = (await initialNotebooksResponse.json()) as Array<{
      id?: unknown;
      name?: unknown;
    }>;
    expect(Array.isArray(initialNotebooksPayload)).toBe(true);
    if (initialNotebooksPayload.length > 0) {
      expect(initialNotebooksPayload[0]).toEqual(
        expect.objectContaining({
          id: expect.any(String),
          name: expect.any(String),
        }),
      );
    }

    await expect(page.getByRole("heading", { level: 1, name: "Notebooks" })).toBeVisible();
    const refreshButton = page.getByTestId("notebooks-refresh");
    await expect(refreshButton).toBeVisible();
    await expect(refreshButton).toBeEnabled();

    const firstNotebookEvidence = notebookResponses.at(-1);
    expect(firstNotebookEvidence?.status).toBe(200);
    expect(firstNotebookEvidence?.bodyType).toBe("array");

    const searchInput = page.locator("#notebook-search");
    await expect(searchInput).toBeVisible();
    await searchInput.fill("smoke-real-backend");
    await expect(searchInput).toHaveValue("smoke-real-backend");

    const refreshResponsePromise = page.waitForResponse(
      (response) =>
        response.request().method() === "GET" && response.url().includes("/api/notebooks"),
      { timeout: RESPONSE_TIMEOUT_MS },
    );
    await refreshButton.click();
    const refreshResponse = await refreshResponsePromise;
    expect(refreshResponse.status()).toBe(200);
    expect(refreshResponse.request().url()).toContain("archived=false");
    await waitForPageStability(page, refreshButton);

    const latestNotebookEvidence = notebookResponses.at(-1);
    expect(latestNotebookEvidence?.status).toBe(200);
    expect(latestNotebookEvidence?.bodyType).toBe("array");
    expect(notebookResponses.length).toBeGreaterThanOrEqual(2);
    expect(notebookResponses.every((entry) => entry.status < 500)).toBe(true);
    recordRuntimeActionEvidence(
      "role.real-notebooks-refresh",
      "/notebooks",
      ["ui-ready", "network-contract", "payload-shape"],
      {
        initialStatus: initialNotebooksResponse.status(),
        refreshStatus: refreshResponse.status(),
        sampleBodyType: latestNotebookEvidence?.bodyType ?? "unknown",
        observedRequestCount: notebookResponses.length,
      },
    );

    await testInfo.attach("notebooks-network-evidence.json", {
      body: JSON.stringify(notebookResponses, null, 2),
      contentType: "application/json",
    });
  } finally {
    await flushLogs();
  }
});

test("cuj: search submits real request and renders completed ui state", async ({
  page,
}, testInfo) => {
  requireRealBackendMode();
  const flushLogs = attachFailureLogs(page, testInfo);

  try {
    await bootstrapAuthenticatedSession(page, "/search?mode=search");
    const searchTab = page.getByRole("tab", { name: /^search$/i });
    if (await searchTab.isVisible().catch(() => false)) {
      await searchTab.click();
    }
    await waitForPageStability(page, page.locator("#search-query"));

    const searchPanel = page.getByRole("tabpanel").filter({ has: page.locator("#search-query") });
    const searchInput = searchPanel.locator("#search-query");
    const searchButton = searchPanel.getByRole("button", { name: /search/i }).first();

    await expect(searchInput).toBeVisible();

    const query = "real backend smoke query";
    const requestPromise = page.waitForRequest(
      (request) => {
        return request.method() === "POST" && request.url().includes("/api/search");
      },
      { timeout: RESPONSE_TIMEOUT_MS },
    );
    const responsePromise = page.waitForResponse(
      (response) => {
        return response.request().method() === "POST" && response.url().includes("/api/search");
      },
      { timeout: RESPONSE_TIMEOUT_MS },
    );

    await searchInput.fill(query);
    await expect(searchButton).toBeEnabled();
    await searchButton.click();

    const request = await requestPromise;
    const response = await responsePromise;
    const requestPayload = JSON.parse(request.postData() ?? "{}") as Record<string, unknown>;
    const responsePayload = (await response.json()) as {
      total_count?: number;
      results?: unknown[];
      search_type?: string;
    };

    await waitForPageStability(page, searchButton);

    expect(requestPayload).toMatchObject({
      query,
      type: "text",
      search_sources: true,
      search_notes: true,
    });
    expect(response.status()).toBe(200);
    expect(responsePayload.search_type).toBe("text");
    expect(Array.isArray(responsePayload.results)).toBe(true);
    expect(typeof responsePayload.total_count).toBe("number");
    expect(Number.isFinite(responsePayload.total_count)).toBe(true);
    expect(responsePayload.total_count ?? -1).toBeGreaterThanOrEqual(0);
    expect((responsePayload.results?.length ?? 0) <= (responsePayload.total_count ?? 0)).toBe(true);

    await expect(searchInput).toHaveValue(query);
    await expect(searchButton).toBeEnabled();
    recordRuntimeActionEvidence(
      "role.real-search-submit",
      "/search",
      ["ui-ready", "network-contract", "payload-shape"],
      {
        requestStatus: response.status(),
        requestUrl: request.url(),
        responseUrl: response.url(),
        totalCount: responsePayload.total_count ?? 0,
        resultCount: responsePayload.results?.length ?? 0,
      },
    );

    await testInfo.attach("search-network-evidence.json", {
      body: JSON.stringify(
        {
          request: {
            url: request.url(),
            method: request.method(),
            payload: requestPayload,
          },
          response: {
            url: response.url(),
            status: response.status(),
            payloadShape: {
              search_type: responsePayload.search_type,
              total_count: responsePayload.total_count,
              result_count: responsePayload.results?.length ?? 0,
            },
          },
        },
        null,
        2,
      ),
      contentType: "application/json",
    });
  } finally {
    await flushLogs();
  }
});

test("cuj: settings refresh requests real backend settings endpoint", async ({
  page,
}, testInfo) => {
  requireRealBackendMode();
  const flushLogs = attachFailureLogs(page, testInfo);
  const settingsStatuses: number[] = [];

  page.on("response", (response) => {
    if (response.request().method() === "GET" && response.url().includes("/api/settings")) {
      settingsStatuses.push(response.status());
    }
  });

  try {
    await bootstrapAuthenticatedSession(page, "/settings");

    const initialSettingsResponsePromise = page.waitForResponse(
      (response) =>
        response.request().method() === "GET" && response.url().includes("/api/settings"),
      { timeout: RESPONSE_TIMEOUT_MS },
    );
    await page.reload();
    await waitForPageStability(page, page.getByTestId("settings-refresh"));

    const initialSettingsResponse = await initialSettingsResponsePromise;
    expect(initialSettingsResponse.status()).toBe(200);
    await expect(page.getByRole("heading", { level: 1, name: "Settings" })).toBeVisible();

    const refreshButton = page.getByTestId("settings-refresh");
    await expect(refreshButton).toBeEnabled();
    const refreshSettingsResponsePromise = page.waitForResponse(
      (response) =>
        response.request().method() === "GET" && response.url().includes("/api/settings"),
      { timeout: RESPONSE_TIMEOUT_MS },
    );
    await refreshButton.click();
    const refreshSettingsResponse = await refreshSettingsResponsePromise;
    expect(refreshSettingsResponse.status()).toBe(200);

    expect(settingsStatuses.length).toBeGreaterThanOrEqual(2);
    expect(settingsStatuses.every((status) => status < 500)).toBe(true);
    recordRuntimeActionEvidence(
      "role.real-settings-refresh",
      "/settings",
      ["ui-ready", "network-contract"],
      {
        initialStatus: initialSettingsResponse.status(),
        refreshStatus: refreshSettingsResponse.status(),
        observedStatuses: settingsStatuses,
      },
    );

    await testInfo.attach("settings-network-evidence.json", {
      body: JSON.stringify({ statuses: settingsStatuses }, null, 2),
      contentType: "application/json",
    });
  } finally {
    await flushLogs();
  }
});

test("cuj: api keys route loads real backend provider state after auth bootstrap", async ({
  page,
}, testInfo) => {
  requireRealBackendMode();
  const flushLogs = attachFailureLogs(page, testInfo);
  const credentialStatuses: number[] = [];
  const modelDefaultStatuses: number[] = [];

  page.on("response", (response) => {
    if (
      response.request().method() === "GET" &&
      response.url().includes("/api/credentials/status")
    ) {
      credentialStatuses.push(response.status());
    }
    if (response.request().method() === "GET" && response.url().includes("/api/models/defaults")) {
      modelDefaultStatuses.push(response.status());
    }
  });

  try {
    await bootstrapAuthenticatedSession(page, "/settings/api-keys");
    await page.reload();
    await page.waitForLoadState("domcontentloaded");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible({
      timeout: UI_READY_TIMEOUT_MS,
    });

    await expect
      .poll(() => credentialStatuses.length, { timeout: RESPONSE_TIMEOUT_MS })
      .toBeGreaterThan(0);
    await expect
      .poll(() => modelDefaultStatuses.length, { timeout: RESPONSE_TIMEOUT_MS })
      .toBeGreaterThan(0);
    expect(credentialStatuses.every((status) => status < 500)).toBe(true);
    expect(modelDefaultStatuses.every((status) => status < 500)).toBe(true);
    recordRuntimeActionEvidence(
      "role.real-api-keys-open",
      "/settings/api-keys",
      ["ui-ready", "network-contract"],
      {
        credentialStatuses,
        modelDefaultStatuses,
        currentUrl: page.url(),
      },
    );

    await testInfo.attach("api-keys-network-evidence.json", {
      body: JSON.stringify(
        {
          credentialStatuses,
          modelDefaultStatuses,
          currentUrl: page.url(),
        },
        null,
        2,
      ),
      contentType: "application/json",
    });
  } finally {
    await flushLogs();
  }
});

test("cuj: transformations and podcasts routes stay interactive against the real backend", async ({
  page,
}, testInfo) => {
  requireRealBackendMode();
  const flushLogs = attachFailureLogs(page, testInfo);
  const transformationStatuses: number[] = [];
  const podcastStatuses: number[] = [];

  page.on("response", (response) => {
    if (response.request().method() === "GET" && response.url().includes("/api/transformations")) {
      transformationStatuses.push(response.status());
    }
    if (
      response.request().method() === "GET" &&
      response.url().includes("/api/podcasts/episodes")
    ) {
      podcastStatuses.push(response.status());
    }
  });

  try {
    await bootstrapAuthenticatedSession(page, "/transformations");
    await page.reload();
    await page.waitForLoadState("domcontentloaded");
    await expect(page.getByRole("heading", { level: 1, name: "Transformations" })).toBeVisible({
      timeout: UI_READY_TIMEOUT_MS,
    });
    await expect(page.getByRole("button", { name: /refresh/i })).toBeVisible({
      timeout: UI_READY_TIMEOUT_MS,
    });

    await page.goto("/podcasts");
    await page.waitForLoadState("domcontentloaded");
    await expect(page.getByRole("heading", { level: 1, name: "Podcasts" })).toBeVisible({
      timeout: UI_READY_TIMEOUT_MS,
    });
    await expect(page.getByRole("tab", { name: /episodes/i })).toBeVisible({
      timeout: UI_READY_TIMEOUT_MS,
    });
    await expect(page.getByRole("tab", { name: /templates/i })).toBeVisible({
      timeout: UI_READY_TIMEOUT_MS,
    });

    await expect
      .poll(() => transformationStatuses.length, { timeout: RESPONSE_TIMEOUT_MS })
      .toBeGreaterThan(0);
    await expect
      .poll(() => podcastStatuses.length, { timeout: RESPONSE_TIMEOUT_MS })
      .toBeGreaterThan(0);
    expect(transformationStatuses.every((status) => status < 500)).toBe(true);
    expect(podcastStatuses.every((status) => status < 500)).toBe(true);
    recordRuntimeActionEvidence(
      "role.real-transformations-open",
      "/transformations",
      ["ui-ready", "network-contract"],
      {
        transformationStatuses,
      },
    );
    recordRuntimeActionEvidence(
      "role.real-podcasts-open",
      "/podcasts",
      ["ui-ready", "network-contract"],
      {
        podcastStatuses,
        currentUrl: page.url(),
      },
    );

    await testInfo.attach("transformations-podcasts-network-evidence.json", {
      body: JSON.stringify(
        {
          transformationStatuses,
          podcastStatuses,
          currentUrl: page.url(),
        },
        null,
        2,
      ),
      contentType: "application/json",
    });
  } finally {
    await flushLogs();
  }
});
