import { appendFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { expect, type Page, test } from "@playwright/test";

const RUN_LIVE_TESTS = process.env.RUN_LIVE_TESTS === "1";
const LIVE_EXTERNAL_WEB_ENABLED = process.env.LIVE_EXTERNAL_WEB_ENABLED === "1";
const HEARTBEAT_SECONDS = Math.max(
  5,
  Number.parseInt(process.env.LIVE_HEARTBEAT_SECONDS ?? "15", 10) || 15,
);
const LIVE_CLEANUP_POLICY = "live-cleanup: read-only-no-op";
const LIVE_IDEMPOTENCY_POLICY = "live-idempotency: read-only-safe-retry";
const LIVE_TEARDOWN_EVIDENCE_PREFIX = "[live-teardown-evidence]";
const LIVE_TEARDOWN_EVIDENCE_FILE = process.env.LIVE_TEARDOWN_EVIDENCE_FILE?.trim() ?? "";

function isPrivateOrLocalHost(hostname: string): boolean {
  const normalized = hostname.toLowerCase();
  if (normalized === "localhost" || normalized === "0.0.0.0" || normalized === "::1") {
    return true;
  }
  if (normalized.endsWith(".local")) {
    return true;
  }
  if (/^\d+\.\d+\.\d+\.\d+$/.test(normalized)) {
    const parts = normalized.split(".").map(Number);
    const [a, b] = parts;
    if (a === 10) {
      return true;
    }
    if (a === 127) {
      return true;
    }
    if (a === 169 && b === 254) {
      return true;
    }
    if (a === 172 && b >= 16 && b <= 31) {
      return true;
    }
    if (a === 192 && b === 168) {
      return true;
    }
    return false;
  }
  if (normalized.includes(":")) {
    return (
      normalized.startsWith("fc") || normalized.startsWith("fd") || normalized.startsWith("fe80")
    );
  }
  return false;
}

function assertSafeExternalUrl(targetUrl: string): URL {
  const parsed = new URL(targetUrl);
  expect(parsed.protocol).toBe("https:");
  expect(parsed.username).toBe("");
  expect(parsed.password).toBe("");

  const normalizedHost = parsed.hostname.toLowerCase();
  expect(isPrivateOrLocalHost(normalizedHost)).toBe(false);

  return parsed;
}

async function runWithHeartbeat(label: string, operation: () => Promise<void>): Promise<void> {
  const startedAt = Date.now();
  let tick = 0;
  const timer = setInterval(() => {
    tick += 1;
    const elapsed = Math.round((Date.now() - startedAt) / 1000);
    console.log(
      `[live-heartbeat] ${label} still running (tick=${tick}, elapsed=${elapsed}s, interval=${HEARTBEAT_SECONDS}s)`,
    );
  }, HEARTBEAT_SECONDS * 1000);
  try {
    await operation();
  } finally {
    clearInterval(timer);
  }
}

function emitLiveTeardownEvidence(payload: Record<string, unknown>): void {
  const line = JSON.stringify(payload);
  console.log(`${LIVE_TEARDOWN_EVIDENCE_PREFIX} ${line}`);
  if (!LIVE_TEARDOWN_EVIDENCE_FILE) {
    return;
  }
  try {
    mkdirSync(dirname(LIVE_TEARDOWN_EVIDENCE_FILE), { recursive: true });
    appendFileSync(LIVE_TEARDOWN_EVIDENCE_FILE, `${line}\n`, { encoding: "utf-8" });
  } catch (error) {
    console.log(`[live-teardown-evidence-error] failed to persist evidence: ${String(error)}`);
  }
}

async function assertExampleDomainPage(page: Page) {
  await expect(page).toHaveTitle(/Example Domain/i);
  await expect(page.getByRole("heading", { name: /Example Domain/i })).toBeVisible();
}

async function assertGenericExternalPage(page: Page, parsed: URL) {
  await expect(page.locator("body")).toContainText(/\S+/);
  await expect(page).toHaveURL(
    new RegExp(`^${parsed.toString().replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`),
  );
}

test("external web live smoke: visit external website", async ({ page }) => {
  // Read-only live smoke; mutating operations must switch to
  // "live-cleanup: required" and include explicit teardown.
  test.info().annotations.push({ type: "live-cleanup", description: LIVE_CLEANUP_POLICY });
  test.info().annotations.push({ type: "live-idempotency", description: LIVE_IDEMPOTENCY_POLICY });

  const startedAtMs = Date.now();
  let status = "passed";
  let reason = "completed";
  try {
    if (!RUN_LIVE_TESTS) {
      test.info().annotations.push({
        type: "live-disabled",
        description: "Set RUN_LIVE_TESTS=1 to enable live external website tests.",
      });
      status = "skipped";
      reason = "RUN_LIVE_TESTS_disabled";
      return;
    }

    if (!LIVE_EXTERNAL_WEB_ENABLED) {
      test.info().annotations.push({
        type: "external-web-disabled",
        description:
          "Set LIVE_EXTERNAL_WEB_ENABLED=1 to explicitly allow real external website traffic.",
      });
      status = "skipped";
      reason = "LIVE_EXTERNAL_WEB_ENABLED_disabled";
      return;
    }

    const targetUrl = process.env.LIVE_EXTERNAL_SITE_URL ?? "https://example.com/";
    const parsed = assertSafeExternalUrl(targetUrl);
    let navigationStatus = 0;

    await runWithHeartbeat("playwright-page-goto", async () => {
      const response = await page.goto(parsed.toString(), { waitUntil: "domcontentloaded" });
      navigationStatus = response?.status() ?? 0;
    });
    expect(navigationStatus).toBeGreaterThanOrEqual(200);
    expect(navigationStatus).toBeLessThan(500);

    if (parsed.origin === "https://example.com") {
      await assertExampleDomainPage(page);
      return;
    }
    await assertGenericExternalPage(page, parsed);
  } catch (error) {
    status = "failed";
    reason = "assertion_or_runtime_error";
    throw error;
  } finally {
    emitLiveTeardownEvidence({
      event: "live_teardown",
      timestamp_utc: new Date().toISOString(),
      test_name: "external web live smoke: visit external website",
      status,
      reason,
      cleanup_policy: LIVE_CLEANUP_POLICY,
      idempotency_policy: LIVE_IDEMPOTENCY_POLICY,
      details: {
        teardown_action: "no-op-read-only",
        duration_seconds: Math.round((Date.now() - startedAtMs) / 1000),
      },
    });
  }
});
