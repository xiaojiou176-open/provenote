import { defineConfig, type ScreenshotMode, type TraceMode, type VideoMode } from "@playwright/test";

if (process.env.FORCE_COLOR) {
  delete process.env.NO_COLOR;
}

const DEFAULT_PLAYWRIGHT_PORT = 3100;
const configuredBaseURL = process.env.PLAYWRIGHT_BASE_URL?.trim();
const configuredPortFromBaseURL = (() => {
  if (!configuredBaseURL) {
    return null;
  }
  try {
    const parsed = new URL(configuredBaseURL);
    return parsed.port ? Number(parsed.port) : null;
  } catch {
    return null;
  }
})();
const playwrightPort = Number(
  process.env.PLAYWRIGHT_PORT ?? String(configuredPortFromBaseURL ?? DEFAULT_PLAYWRIGHT_PORT),
);
const baseURL = configuredBaseURL ?? `http://127.0.0.1:${playwrightPort}`;
const apiPort = Number(process.env.PLAYWRIGHT_API_PORT ?? "5055");
const apiBaseURL = process.env.PLAYWRIGHT_API_BASE_URL ?? `http://127.0.0.1:${apiPort}`;
const nextDistDir =
  process.env.NEXT_DIST_DIR?.trim() || ".runtime-cache/build/next-playwright";
const useRealBackend = process.env.PLAYWRIGHT_REAL_BACKEND === "1";
const isListMode = process.argv.includes("--list");
const realBackendSmokeSpec = "**/real-backend-smoke.spec.ts";
const reuseExistingServer = process.env.PLAYWRIGHT_REUSE_EXISTING_SERVER === "1" && !process.env.CI;
const surrealExternalUrl = process.env.SURREAL_EXTERNAL_URL?.trim();
const configuredWorkers = process.env.PLAYWRIGHT_WORKERS?.trim();
const playwrightWorkers = useRealBackend ? 1 : configuredWorkers ? Number(configuredWorkers) : 1;
const traceModes = ["off", "on", "retain-on-failure", "on-first-retry"] as const;
const screenshotModes = ["off", "on", "only-on-failure"] as const;
const videoModes = ["off", "on", "retain-on-failure", "on-first-retry"] as const;

function parseMode<T extends string>(
  value: string | undefined,
  allowed: readonly T[],
  fallback: T,
): T {
  const normalized = value?.trim();
  return normalized && allowed.includes(normalized as T) ? (normalized as T) : fallback;
}

const traceMode: TraceMode = parseMode(
  process.env.PLAYWRIGHT_TRACE_MODE,
  traceModes,
  "retain-on-failure",
);
const screenshotMode: ScreenshotMode = parseMode(
  process.env.PLAYWRIGHT_SCREENSHOT_MODE,
  screenshotModes,
  "only-on-failure",
);
const videoMode: VideoMode = parseMode(
  process.env.PLAYWRIGHT_VIDEO_MODE,
  videoModes,
  "on-first-retry",
);
const playwrightReportDir =
  process.env.PLAYWRIGHT_REPORT_DIR?.trim() ||
  "../../.runtime-cache/runs/current/evidence/playwright/report";
const playwrightResultsDir =
  process.env.PLAYWRIGHT_RESULTS_DIR?.trim() ||
  "../../.runtime-cache/runs/current/evidence/playwright/results";

const corsAllowOrigins = [
  `http://127.0.0.1:${playwrightPort}`,
  `http://localhost:${playwrightPort}`,
  "http://127.0.0.1:3000",
  "http://localhost:3000",
  "http://127.0.0.1:5173",
  "http://localhost:5173",
].join(",");

export function getFrontendServerCommands(options: {
  nextDistDir: string;
  playwrightPort: number;
  apiBaseURL: string;
  useRealBackend: boolean;
  isCI: boolean;
}) {
  const { nextDistDir, playwrightPort, apiBaseURL, useRealBackend, isCI } = options;
  const startPrefix = [
    `NEXT_DIST_DIR=${nextDistDir}`,
    "NEXT_TELEMETRY_DISABLED=1",
    "__NEXT_DEV_INDICATOR=false",
  ];
  const realBackendEnv = [
    `API_URL=${apiBaseURL}`,
    `NEXT_PUBLIC_API_URL=${apiBaseURL}`,
    `INTERNAL_API_URL=${apiBaseURL}`,
    `INTERNAL_API_PORT=${new URL(apiBaseURL).port || "5055"}`,
  ];

  if (isCI) {
    const buildCommand = `npm run build`;
    const startCommand = `HOSTNAME=127.0.0.1 PORT=${playwrightPort} node ${nextDistDir}/standalone/server.js`;
    return {
      frontendCommand: `${startPrefix.join(" ")} ${buildCommand} && ${startPrefix.join(" ")} ${startCommand}`,
      frontendCommandWithRealBackend: `${[...startPrefix, ...realBackendEnv].join(" ")} ${buildCommand} && ${[
        ...startPrefix,
        ...realBackendEnv,
      ].join(" ")} ${startCommand}`,
    };
  }

  return {
    frontendCommand: `${startPrefix.join(" ")} npm run dev -- --webpack --hostname 127.0.0.1 --port ${playwrightPort}`,
    frontendCommandWithRealBackend: `${[...startPrefix, ...realBackendEnv].join(" ")} npm run dev -- --webpack --hostname 127.0.0.1 --port ${playwrightPort}`,
  };
}

const backendCommandWithEmbeddedSurreal = `cd ../.. && bash -lc 'set -euo pipefail
# shellcheck source=/dev/null
source tooling/scripts/runtime/cache_env.sh
MACHINE_CACHE_ROOT="$(resolve_open_notebook_machine_cache_root)"
ensure_open_notebook_machine_cache_layout "\${MACHINE_CACHE_ROOT}"
SURREAL_LOCAL_BIN="\${SURREAL_BIN:-$(resolve_open_notebook_machine_surreal_binary_path "\${MACHINE_CACHE_ROOT}")}"
SURREAL_BIND="\${SURREAL_BIND:-127.0.0.1:38080}"
SURREAL_USER="\${SURREAL_USER:-root}"
SURREAL_PASSWORD="\${SURREAL_PASSWORD:-root}"
SURREAL_DATA_PATH="\${SURREAL_DATA_PATH:-.runtime-cache/state/local/data/surrealdb/playwright-e2e.db}"
SURREAL_HOST="\${SURREAL_BIND%:*}"
SURREAL_PORT="\${SURREAL_BIND##*:}"
SURREAL_CONTAINER="open-notebook-playwright-surreal-\${SURREAL_PORT}"
SKIP_MIGRATIONS=false
cleanup() {
  if [ -n "\${surreal_pid:-}" ] && kill -0 "\${surreal_pid}" 2>/dev/null; then
    kill "\${surreal_pid}" >/dev/null 2>&1 || true
  fi
  if [ -n "\${surreal_container_started:-}" ]; then
    docker rm -f "\${SURREAL_CONTAINER}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT
if [ -x "\${SURREAL_LOCAL_BIN}" ]; then
  mkdir -p "$(dirname "\${SURREAL_DATA_PATH}")"
  "\${SURREAL_LOCAL_BIN}" start --log warn --user "\${SURREAL_USER}" --pass "\${SURREAL_PASSWORD}" --bind "\${SURREAL_BIND}" "rocksdb:\${SURREAL_DATA_PATH}" >/tmp/open-notebook-playwright-surreal.log 2>&1 &
  surreal_pid=$!
elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  docker rm -f "\${SURREAL_CONTAINER}" >/dev/null 2>&1 || true
  docker run -d --name "\${SURREAL_CONTAINER}" -p "\${SURREAL_PORT}:8000" surrealdb/surrealdb:v2.3.10 start --log warn --user "\${SURREAL_USER}" --pass "\${SURREAL_PASSWORD}" memory >/tmp/open-notebook-playwright-surreal.log 2>&1
  surreal_container_started=1
elif command -v surreal >/dev/null 2>&1; then
  mkdir -p "$(dirname "\${SURREAL_DATA_PATH}")"
  surreal start --log warn --user "\${SURREAL_USER}" --pass "\${SURREAL_PASSWORD}" --bind "\${SURREAL_BIND}" "rocksdb:\${SURREAL_DATA_PATH}" >/tmp/open-notebook-playwright-surreal.log 2>&1 &
  surreal_pid=$!
  SKIP_MIGRATIONS=true
else
  echo "ERROR: missing machine-cache surreal binary, docker daemon, and surreal CLI fallback" >&2
  exit 1
fi
for _ in $(seq 1 30); do
  if (echo > "/dev/tcp/\${SURREAL_HOST}/\${SURREAL_PORT}") >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
if ! (echo > "/dev/tcp/\${SURREAL_HOST}/\${SURREAL_PORT}") >/dev/null 2>&1; then
  echo "ERROR: SurrealDB did not become ready at \${SURREAL_BIND}" >&2
  exit 1
fi
OPEN_NOTEBOOK_SKIP_GEMINI_STARTUP_PROBE=1 OPEN_NOTEBOOK_SKIP_MIGRATIONS="\${SKIP_MIGRATIONS}" OPEN_NOTEBOOK_PASSWORD="\${OPEN_NOTEBOOK_PASSWORD:-open-notebook-test-password}" OPEN_NOTEBOOK_CORS_ALLOW_ORIGINS="${corsAllowOrigins}" API_HOST=127.0.0.1 API_PORT=${apiPort} API_RELOAD=false SURREAL_URL="ws://\${SURREAL_BIND}/rpc" bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/bin/run_api.py'`;
const backendCommandWithExternalSurreal = `cd ../.. && bash -lc 'set -euo pipefail; OPEN_NOTEBOOK_SKIP_GEMINI_STARTUP_PROBE=1 OPEN_NOTEBOOK_CORS_ALLOW_ORIGINS="${corsAllowOrigins}" API_HOST=127.0.0.1 API_PORT=${apiPort} API_RELOAD=false SURREAL_URL=${surrealExternalUrl} bash tooling/scripts/runtime/run_uv_managed.sh run python tooling/bin/run_api.py'`;
const { frontendCommand, frontendCommandWithRealBackend } = getFrontendServerCommands({
  nextDistDir,
  playwrightPort,
  apiBaseURL,
  useRealBackend,
  isCI: !!process.env.CI,
});

export default defineConfig({
  testDir: "./e2e",
  outputDir: playwrightResultsDir,
  timeout: useRealBackend ? 120_000 : undefined,
  testIgnore: useRealBackend ? [] : [realBackendSmokeSpec],
  snapshotPathTemplate: "{testDir}/{testFilePath}-snapshots/{arg}-{projectName}{ext}",
  fullyParallel: !useRealBackend,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: playwrightWorkers,
  reporter: process.env.CI
    ? [["github"], ["html", { open: "never", outputFolder: playwrightReportDir }]]
    : "list",
  use: {
    baseURL,
    trace: traceMode,
    screenshot: screenshotMode,
    video: videoMode,
  },
  webServer: isListMode
    ? undefined
    : useRealBackend
      ? [
          {
            command: surrealExternalUrl
              ? backendCommandWithExternalSurreal
              : backendCommandWithEmbeddedSurreal,
            url: `${apiBaseURL}/health`,
            reuseExistingServer,
            timeout: 120 * 1000,
          },
          {
            command: frontendCommandWithRealBackend,
            url: baseURL,
            reuseExistingServer,
            timeout: 120 * 1000,
          },
        ]
      : {
          command: frontendCommand,
          url: baseURL,
          reuseExistingServer,
          timeout: 120 * 1000,
        },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
    {
      name: "firefox",
      use: { browserName: "firefox" },
    },
    {
      name: "webkit",
      use: { browserName: "webkit" },
    },
  ],
});
