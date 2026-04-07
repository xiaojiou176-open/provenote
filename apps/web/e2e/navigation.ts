import type { Page } from "@playwright/test";

const RETRIABLE_NAVIGATION_ERRORS = [
  "net::ERR_ABORTED",
  "net::ERR_ADDRESS_INVALID",
  "net::ERR_CONNECTION_REFUSED",
  "frame was detached",
  "can't assign requested address",
  "eaddrnotavail",
];

export async function gotoWithRetry(
  page: Page,
  targetPath: string,
  options?: {
    waitUntil?: "load" | "domcontentloaded";
    timeout?: number;
    maxAttempts?: number;
  },
): Promise<void> {
  const waitUntil = options?.waitUntil ?? "domcontentloaded";
  const timeout = options?.timeout ?? 20_000;
  const maxAttempts = options?.maxAttempts ?? 4;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      await page.goto(targetPath, { waitUntil, timeout });
      return;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const isRetriable = RETRIABLE_NAVIGATION_ERRORS.some((pattern) =>
        message.toLowerCase().includes(pattern.toLowerCase()),
      );
      if (!isRetriable || attempt === maxAttempts) {
        throw error;
      }
      await page.goto("about:blank").catch(() => {});
      await new Promise((resolve) => setTimeout(resolve, attempt * 500));
    }
  }
}

export async function gotoWithReadyCheck(
  page: Page,
  targetPath: string,
  assertReady: () => Promise<void>,
  options?: {
    waitUntil?: "load" | "domcontentloaded";
    timeout?: number;
    maxAttempts?: number;
  },
): Promise<void> {
  const maxAttempts = options?.maxAttempts ?? 4;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      await gotoWithRetry(page, targetPath, options);
      await assertReady();
      return;
    } catch (error) {
      if (attempt === maxAttempts) {
        throw error;
      }
      await page.goto("about:blank", { waitUntil: "domcontentloaded" }).catch(() => {});
    }
  }
}
