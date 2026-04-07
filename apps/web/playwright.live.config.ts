import { defineConfig } from '@playwright/test'

const playwrightReportDir =
  process.env.PLAYWRIGHT_REPORT_DIR?.trim() || '../../.runtime-cache/runs/current/evidence/playwright/report'
const playwrightResultsDir =
  process.env.PLAYWRIGHT_RESULTS_DIR?.trim() || '../../.runtime-cache/runs/current/evidence/playwright/results'

export default defineConfig({
  testDir: './e2e-live',
  outputDir: playwrightResultsDir,
  timeout: 120_000,
  expect: {
    timeout: 15_000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI
    ? [['github'], ['html', { open: 'never', outputFolder: playwrightReportDir }]]
    : 'list',
  use: {
    actionTimeout: 20_000,
    navigationTimeout: 60_000,
    ignoreHTTPSErrors: false,
    trace: 'retain-on-failure',
    screenshot: 'on',
    video: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
})
