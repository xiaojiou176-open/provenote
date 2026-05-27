import childProcess from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  buildBrowserIdentityMetadata,
  writeBrowserIdentityPage,
} from "./shared/browser-instance-identity.mjs";

const DEFAULT_BROWSER_MODE = "real_chrome_profile";
const DEFAULT_PROFILE_NAME = "notebooklab";
const TARGET_PROFILE_KEY = "Profile 1";
const DEFAULT_START_URL = "about:blank";
const DEFAULT_CDP_PORT = 9342;
const DEFAULT_CHROME_EXECUTABLE =
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const DETACHED_CHROME_LAUNCH_ENV = "NOTEBOOKLAB_ALLOW_DETACHED_CHROME_LAUNCH";
const SINGLETON_PREFIX = "Singleton";
const SCRIPT_FILE = fileURLToPath(import.meta.url);
const SCRIPT_DIR = path.dirname(SCRIPT_FILE);
const APP_ROOT = path.resolve(SCRIPT_DIR, "..");
const REPO_ROOT = path.resolve(APP_ROOT, "../..");

function stableHomeDir(env = process.env) {
  return env.HOME?.trim() || os.homedir();
}

export function resolveRepoRoot() {
  return REPO_ROOT;
}

export function resolveChromeSourceUserDataDir(env = process.env) {
  const configured = env.NOTEBOOKLAB_SOURCE_CHROME_USER_DATA_DIR?.trim();
  if (configured) {
    return configured;
  }
  return path.join(
    stableHomeDir(env),
    "Library",
    "Application Support",
    "Google",
    "Chrome",
  );
}

export function resolveChromeUserDataDir(env = process.env) {
  const configured = env.NOTEBOOKLAB_CHROME_USER_DATA_DIR?.trim();
  if (configured) {
    return configured;
  }
  return path.join(stableHomeDir(env), ".cache", "notebooklab", "browser", "chrome-user-data");
}

export function resolveChromeProfileName(env = process.env) {
  return env.NOTEBOOKLAB_CHROME_PROFILE_NAME?.trim() || DEFAULT_PROFILE_NAME;
}

export function resolveBrowserMode(env = process.env) {
  return env.NOTEBOOKLAB_BROWSER_MODE?.trim() || DEFAULT_BROWSER_MODE;
}

export function resolveChromeCdpPort(env = process.env) {
  const configured = Number.parseInt(env.NOTEBOOKLAB_CHROME_CDP_PORT?.trim() || "", 10);
  if (Number.isInteger(configured) && configured > 0) {
    return configured;
  }
  return DEFAULT_CDP_PORT;
}

export function resolveChromeCdpUrl(env = process.env) {
  return `http://127.0.0.1:${resolveChromeCdpPort(env)}`;
}

export function resolveChromeExecutable(env = process.env) {
  return env.NOTEBOOKLAB_CHROME_EXECUTABLE?.trim() || DEFAULT_CHROME_EXECUTABLE;
}

export function resolveManualPlaywrightProfileDir(env = process.env) {
  const configured = env.NOTEBOOKLAB_MANAGED_PLAYWRIGHT_PROFILE_DIR?.trim();
  if (configured) {
    return configured;
  }
  return path.join(resolveRepoRoot(), ".runtime-cache", "browser", "manual-playwright-profile");
}

export function resolveBrowserInstanceStateFile(env = process.env) {
  const configured = env.NOTEBOOKLAB_BROWSER_INSTANCE_STATE_FILE?.trim();
  if (configured) {
    return configured;
  }
  return path.join(resolveRepoRoot(), ".runtime-cache", "browser", "chrome-instance.json");
}

function readJsonFile(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function ensureParentDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function writeJsonFile(filePath, payload) {
  ensureParentDir(filePath);
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function rmIfExists(targetPath) {
  if (fs.existsSync(targetPath)) {
    fs.rmSync(targetPath, { recursive: true, force: true });
  }
}

function removeSingletonArtifacts(rootDir) {
  if (!fs.existsSync(rootDir)) {
    return;
  }
  for (const entryName of fs.readdirSync(rootDir)) {
    if (!entryName.startsWith(SINGLETON_PREFIX)) {
      continue;
    }
    rmIfExists(path.join(rootDir, entryName));
  }
}

function hostDefaultMacChromeUserDataDir() {
  return path.join(
    os.homedir(),
    "Library",
    "Application Support",
    "Google",
    "Chrome",
  );
}

function assertNoChromeProcessesRunning(sourceUserDataDir, env = process.env) {
  if (!fs.existsSync(sourceUserDataDir)) {
    return;
  }

  const lsofResult = childProcess.spawnSync("lsof", ["+D", sourceUserDataDir], {
    encoding: "utf8",
  });

  if (lsofResult.error) {
    if (lsofResult.error.code !== "ENOENT") {
      throw lsofResult.error;
    }
    const fallbackMatches = listChromeProcessDetails().filter(({ commandLine }) =>
      commandLine.includes(`--user-data-dir=${sourceUserDataDir}`),
    );
    if (fallbackMatches.length > 0) {
      throw new Error(
        [
          `Chrome/Chromium processes are still using the source root ${sourceUserDataDir}; close that root before migration.`,
          ...fallbackMatches.map(({ pid, commandLine }) => `${pid} ${commandLine}`),
        ].join("\n"),
      );
    }
    return;
  }

  const conflictingLines = lsofResult.stdout
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(1)
    .filter((line) => {
      const commandToken = line.split(/\s+/)[0]?.toLowerCase() || "";
      return (
        commandToken.includes("chrome") ||
        commandToken.includes("chromium")
      );
    });

  if (conflictingLines.length > 0) {
    throw new Error(
      [
        `Chrome/Chromium processes are still using the source root ${sourceUserDataDir}; close that root before migration.`,
        ...conflictingLines,
      ].join("\n"),
    );
  }
}

export function resolveChromeProfileKey(localState, profileName, explicitKey) {
  const configuredKey = explicitKey?.trim();
  if (configuredKey) {
    return configuredKey;
  }

  const infoCache = localState?.profile?.info_cache;
  if (!infoCache || typeof infoCache !== "object") {
    throw new Error("Chrome Local State does not expose profile.info_cache");
  }

  for (const [profileKey, metadata] of Object.entries(infoCache)) {
    if (
      metadata &&
      typeof metadata === "object" &&
      "name" in metadata &&
      String(metadata.name).trim().toLowerCase() === profileName.trim().toLowerCase()
    ) {
      return profileKey;
    }
  }

  throw new Error(`Chrome profile named "${profileName}" was not found in Local State`);
}

export function rewriteMigratedLocalState(localState, sourceProfileKey, targetProfileKey, profileName) {
  const nextState = structuredClone(localState);
  const existingProfileSection =
    nextState.profile && typeof nextState.profile === "object" ? nextState.profile : {};
  const infoCache =
    existingProfileSection.info_cache && typeof existingProfileSection.info_cache === "object"
      ? existingProfileSection.info_cache
      : {};
  const sourceMetadata =
    infoCache[sourceProfileKey] && typeof infoCache[sourceProfileKey] === "object"
      ? infoCache[sourceProfileKey]
      : {};

  nextState.profile = {
    ...existingProfileSection,
    info_cache: {
      [targetProfileKey]: {
        ...sourceMetadata,
        name: profileName,
      },
    },
    last_used: targetProfileKey,
    last_active_profiles: [targetProfileKey],
  };

  return nextState;
}

export function buildMigrationPlan(env = process.env) {
  const sourceUserDataDir = resolveChromeSourceUserDataDir(env);
  const sourceLocalStatePath = path.join(sourceUserDataDir, "Local State");
  const profileName = resolveChromeProfileName(env);
  const sourceLocalState = readJsonFile(sourceLocalStatePath);
  const sourceProfileKey = resolveChromeProfileKey(
    sourceLocalState,
    profileName,
    env.NOTEBOOKLAB_SOURCE_CHROME_PROFILE_KEY,
  );
  const sourceProfileDir = path.join(sourceUserDataDir, sourceProfileKey);
  const targetUserDataDir = resolveChromeUserDataDir(env);
  const targetLocalStatePath = path.join(targetUserDataDir, "Local State");
  const targetProfileKey = TARGET_PROFILE_KEY;
  const targetProfileDir = path.join(targetUserDataDir, targetProfileKey);

  return {
    command: "migrate",
    sourceUserDataDir,
    sourceLocalStatePath,
    sourceProfileKey,
    sourceProfileDir,
    targetUserDataDir,
    targetLocalStatePath,
    targetProfileKey,
    targetProfileDir,
    profileName,
    copiedPaths: ["Local State", sourceProfileKey],
    removedSingletons: [
      "SingletonLock",
      "SingletonCookie",
      "SingletonSocket",
      "Singleton*",
    ],
  };
}

function buildIdentityPageConfig({
  repoRoot,
  env = process.env,
  cdpPort,
  cdpUrl,
  userDataDir,
  profileName,
  profileKey,
}) {
  return buildBrowserIdentityMetadata({
    repoRoot,
    env,
    cdpPort,
    cdpUrl,
    browserProfile: {
      userDataDir,
      profileName,
      profileDirectory: profileKey,
    },
  });
}

function buildCanonicalTargetUrls({ identityPageUrl, targetUrl }) {
  return [...new Set([identityPageUrl, targetUrl].filter((url) => url && url !== DEFAULT_START_URL))];
}

export function buildRealChromeLaunchConfig(env = process.env) {
  const browserMode = resolveBrowserMode(env);
  if (browserMode !== "real_chrome_profile") {
    throw new Error(
      `real Chrome launcher only supports NOTEBOOKLAB_BROWSER_MODE=real_chrome_profile (received ${browserMode})`,
    );
  }

  const userDataDir = resolveChromeUserDataDir(env);
  const targetUrl = env.NOTEBOOKLAB_BROWSER_URL?.trim() || DEFAULT_START_URL;
  const cdpPort = resolveChromeCdpPort(env);
  const cdpUrl = resolveChromeCdpUrl(env);
  const profileName = resolveChromeProfileName(env);
  const profileKey = env.NOTEBOOKLAB_CHROME_PROFILE_KEY?.trim() || TARGET_PROFILE_KEY;
  const identityPage = buildIdentityPageConfig({
    repoRoot: resolveRepoRoot(),
    env,
    cdpPort,
    cdpUrl,
    userDataDir,
    profileName,
    profileKey,
    startUrl: targetUrl,
  });

  return {
    command: "start-or-attach",
    browserMode,
    userDataDir,
    profileName,
    profileKey,
    targetUrl,
    cdpPort,
    cdpUrl,
    channel: "chrome",
    executable: resolveChromeExecutable(env),
    identityPage,
    identityPagePath: identityPage.identityPath,
    identityPageUrl: identityPage.identityUrl,
    identityLabel: identityPage.repoLabel,
    identityAccent: identityPage.accent,
    launchTargets: buildCanonicalTargetUrls({
      identityPageUrl: identityPage.identityUrl,
      targetUrl,
    }),
    args: [
      `--user-data-dir=${userDataDir}`,
      `--profile-directory=${profileKey}`,
      `--remote-debugging-port=${cdpPort}`,
      "--remote-debugging-address=127.0.0.1",
      "--no-first-run",
      "--no-default-browser-check",
    ],
  };
}

export function buildManagedPlaywrightLaunchConfig(env = process.env) {
  const browserMode = resolveBrowserMode(env);
  if (browserMode !== "managed_playwright") {
    throw new Error(
      `managed Playwright launcher only supports NOTEBOOKLAB_BROWSER_MODE=managed_playwright (received ${browserMode})`,
    );
  }

  return {
    command: "start-or-attach",
    browserMode,
    userDataDir: resolveManualPlaywrightProfileDir(env),
    profileKey: "",
    targetUrl: env.NOTEBOOKLAB_BROWSER_URL?.trim() || DEFAULT_START_URL,
    headless: false,
    channel: "chromium",
    args: [],
  };
}

export function buildManualBrowserLaunchConfig(env = process.env) {
  return resolveBrowserMode(env) === "managed_playwright"
    ? buildManagedPlaywrightLaunchConfig(env)
    : buildRealChromeLaunchConfig(env);
}

function readInstanceStateFile(env = process.env) {
  const statePath = resolveBrowserInstanceStateFile(env);
  if (!fs.existsSync(statePath)) {
    return null;
  }
  return readJsonFile(statePath);
}

function writeInstanceStateFile(payload, env = process.env) {
  const statePath = resolveBrowserInstanceStateFile(env);
  writeJsonFile(statePath, payload);
  return statePath;
}

function isPidAlive(pid) {
  if (!Number.isInteger(pid) || pid <= 0) {
    return false;
  }
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

function readProcessCommandLine(pid) {
  try {
    return childProcess
      .execFileSync("ps", ["-p", String(pid), "-o", "command="], {
        encoding: "utf8",
      })
      .trim();
  } catch {
    return "";
  }
}

function listChromeProcessDetails() {
  const result = childProcess.execFileSync("ps", ["-A", "-o", "pid=", "-o", "command="], {
    encoding: "utf8",
  });
  return result
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const separator = line.search(/\s/);
      const pid = Number.parseInt(line.slice(0, separator), 10);
      const commandLine = line.slice(separator).trim();
      return { pid, commandLine };
    })
    .filter(({ pid, commandLine }) => Number.isInteger(pid) && commandLine.length > 0);
}

function discoverMatchingChromeProcess(config) {
  return listChromeProcessDetails().find(
    ({ commandLine }) =>
      commandLine.includes(`--user-data-dir=${config.userDataDir}`) &&
      commandLine.includes(`--profile-directory=${config.profileKey}`) &&
      commandLine.includes(`--remote-debugging-port=${config.cdpPort}`),
  );
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request to ${url} returned ${response.status}`);
  }
  return response.json();
}

async function waitForCdpUrl(cdpUrl, timeoutMs = 15000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const payload = await fetchJson(`${cdpUrl}/json/version`);
      return payload;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
  throw new Error(`Timed out waiting for Chrome CDP endpoint at ${cdpUrl}`);
}

export async function connectBrowserOverCdp(cdpUrl) {
  const { chromium } = await import("@playwright/test");
  return chromium.connectOverCDP(cdpUrl);
}

export async function ensureBrowserTargetsOverCdp(cdpUrl, targetUrls, options = {}) {
  const desiredTargets = [...new Set(targetUrls.filter((value) => value && value !== DEFAULT_START_URL))];
  if (desiredTargets.length === 0) {
    return [];
  }

  const connect = options.connect || connectBrowserOverCdp;
  const browser = await connect(cdpUrl);
  try {
    const context = browser.contexts()[0];
    if (!context) {
      throw new Error(`No browser context available via ${cdpUrl}`);
    }

    const existingTargets = new Set(context.pages().map((page) => page.url()));
    for (const targetUrl of desiredTargets) {
      if (existingTargets.has(targetUrl)) {
        continue;
      }
      const page = await context.newPage();
      await page.goto(targetUrl, {
        waitUntil: "domcontentloaded",
        timeout: 45000,
      });
      existingTargets.add(page.url());
    }

    return [...existingTargets];
  } finally {
    await browser.close();
  }
}

export async function openTargetUrlOverCdp(cdpUrl, targetUrl, options = {}) {
  return ensureBrowserTargetsOverCdp(cdpUrl, [targetUrl], options);
}

export async function connectToRealChromeOverCDP(env = process.env) {
  const inspection = await inspectManualBrowserState(env);
  if (!inspection.attachable) {
    throw new Error(
      `Chrome instance is not attachable for ${inspection.expectedUserDataDir} (${inspection.reason})`,
    );
  }
  const { chromium } = await import("@playwright/test");
  return chromium.connectOverCDP(inspection.expectedCdpUrl);
}

export async function inspectManualBrowserState(env = process.env) {
  const config = buildRealChromeLaunchConfig(env);
  const statePath = resolveBrowserInstanceStateFile(env);
  const state = readInstanceStateFile(env);
  const result = {
    command: "status",
    statePath,
    stateExists: fs.existsSync(statePath),
    attachable: false,
    reason: "missing-state",
    expectedUserDataDir: config.userDataDir,
    expectedProfileKey: config.profileKey,
    expectedCdpUrl: config.cdpUrl,
    expectedIdentityPagePath: config.identityPage.identityPath,
    expectedIdentityPageUrl: config.identityPage.identityUrl,
    expectedIdentityLabel: config.identityPage.repoLabel,
    expectedIdentityAccent: config.identityPage.accent,
    stateExists: Boolean(state),
    state,
  };

  const buildDiscoveredResult = async () => {
    const discovered = discoverMatchingChromeProcess(config);
    if (!discovered) {
      return result;
    }
    try {
      const versionInfo = await waitForCdpUrl(config.cdpUrl, 2000);
      const discoveredState = {
        pid: discovered.pid,
        cdpUrl: config.cdpUrl,
        cdpPort: config.cdpPort,
        userDataDir: config.userDataDir,
        profileKey: config.profileKey,
        startedAt: new Date().toISOString(),
      };
      return {
        ...result,
        attachable: true,
        reason: "command-and-cdp-ready",
        commandLine: discovered.commandLine,
        state: discoveredState,
        versionInfo,
      };
    } catch (error) {
      return {
        ...result,
        reason: "cdp-unreachable",
        commandLine: discovered.commandLine,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  };

  if (!state || typeof state !== "object") {
    return buildDiscoveredResult();
  }

  if (!isPidAlive(Number(state.pid))) {
    return buildDiscoveredResult();
  }

  if (
    state.userDataDir !== config.userDataDir ||
    state.profileKey !== config.profileKey ||
    state.cdpUrl !== config.cdpUrl
  ) {
    return buildDiscoveredResult();
  }

  const commandLine = readProcessCommandLine(Number(state.pid));
  if (
    !commandLine.includes(`--user-data-dir=${config.userDataDir}`) ||
    !commandLine.includes(`--profile-directory=${config.profileKey}`) ||
    !commandLine.includes(`--remote-debugging-port=${config.cdpPort}`)
  ) {
    return buildDiscoveredResult();
  }

  try {
    const versionInfo = await waitForCdpUrl(config.cdpUrl, 2000);
    return {
      ...result,
      attachable: true,
      reason: "ready",
      commandLine,
      versionInfo,
    };
  } catch (error) {
    return {
      ...result,
      reason: "cdp-unreachable",
      commandLine,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

export function migrateChromeProfile(env = process.env) {
  const plan = buildMigrationPlan(env);
  assertNoChromeProcessesRunning(plan.sourceUserDataDir, env);

  if (!fs.existsSync(plan.sourceLocalStatePath)) {
    throw new Error(`Chrome Local State not found at ${plan.sourceLocalStatePath}`);
  }
  if (!fs.existsSync(plan.sourceProfileDir)) {
    throw new Error(`Chrome profile directory not found at ${plan.sourceProfileDir}`);
  }
  if (fs.existsSync(plan.targetUserDataDir)) {
    const existingEntries = fs.readdirSync(plan.targetUserDataDir);
    if (existingEntries.length > 0) {
      throw new Error(
        `Target Chrome root already exists and is not empty: ${plan.targetUserDataDir}`,
      );
    }
  }

  const tempTargetDir = `${plan.targetUserDataDir}.tmp-${process.pid}`;
  rmIfExists(tempTargetDir);
  fs.mkdirSync(tempTargetDir, { recursive: true });

  const tempLocalStatePath = path.join(tempTargetDir, "Local State");
  const tempProfileDir = path.join(tempTargetDir, plan.targetProfileKey);
  fs.copyFileSync(plan.sourceLocalStatePath, tempLocalStatePath);
  fs.cpSync(plan.sourceProfileDir, tempProfileDir, {
    recursive: true,
    filter: (entry) => !path.basename(entry).startsWith(SINGLETON_PREFIX),
  });

  const sourceLocalState = readJsonFile(plan.sourceLocalStatePath);
  const rewrittenLocalState = rewriteMigratedLocalState(
    sourceLocalState,
    plan.sourceProfileKey,
    plan.targetProfileKey,
    plan.profileName,
  );
  writeJsonFile(tempLocalStatePath, rewrittenLocalState);
  removeSingletonArtifacts(tempTargetDir);
  removeSingletonArtifacts(tempProfileDir);

  rmIfExists(plan.targetUserDataDir);
  fs.renameSync(tempTargetDir, plan.targetUserDataDir);

  return {
    ...plan,
    migrated: true,
  };
}

async function attachToRealChrome(env = process.env) {
  const config = buildRealChromeLaunchConfig(env);
  const identityPage = writeBrowserIdentityPage({
    repoRoot: resolveRepoRoot(),
    env,
    cdpPort: config.cdpPort,
    cdpUrl: config.cdpUrl,
    browserProfile: {
      userDataDir: config.userDataDir,
      profileName: config.profileName,
      profileDirectory: config.profileKey,
    },
    startUrl: config.targetUrl,
  });
  const inspection = await inspectManualBrowserState(env);
  let action = "attached";
  let statePath = resolveBrowserInstanceStateFile(env);
  let state = inspection.state;

  if (!inspection.attachable) {
    if (!fs.existsSync(path.join(config.userDataDir, "Local State"))) {
      throw new Error(
        `Isolated Chrome root is missing at ${config.userDataDir}. Run browser:manual:migrate-profile first.`,
      );
    }

    const chromeArgs = [
      ...config.args,
      ...config.launchTargets,
    ];
    if (env[DETACHED_CHROME_LAUNCH_ENV]?.trim() !== "1") {
      const manualLaunchCommand = [config.executable, ...chromeArgs]
        .map((part) => JSON.stringify(part))
        .join(" ");
      throw new Error(
        [
          `Detached repo-owned Chrome launch now requires ${DETACHED_CHROME_LAUNCH_ENV}=1.`,
          `Launch Chrome manually with ${manualLaunchCommand} or rerun with that explicit operator override.`,
        ].join(" "),
      );
    }

    const chrome = childProcess.spawn(config.executable, chromeArgs, {
      detached: true,
      stdio: "ignore",
    });
    chrome.unref();

    await waitForCdpUrl(config.cdpUrl);
    statePath = writeInstanceStateFile({
      pid: chrome.pid,
      cdpUrl: config.cdpUrl,
      cdpPort: config.cdpPort,
      userDataDir: config.userDataDir,
      profileKey: config.profileKey,
      startedAt: new Date().toISOString(),
    }, env);
    state = readInstanceStateFile(env);
    action = "started";
  } else if (inspection.state) {
    statePath = writeInstanceStateFile(inspection.state, env);
    state = inspection.state;
  }

  await waitForCdpUrl(config.cdpUrl);
  const ensuredTargets = await ensureBrowserTargetsOverCdp(config.cdpUrl, [
    identityPage.identityUrl,
    config.targetUrl,
  ]);

  return {
    action,
    config,
    identityPage,
    ensuredTargets,
    state,
    statePath,
  };
}

async function launchManagedPlaywright(env = process.env) {
  const { chromium } = await import("@playwright/test");
  const config = buildManagedPlaywrightLaunchConfig(env);
  const context = await chromium.launchPersistentContext(config.userDataDir, {
    headless: config.headless,
    viewport: null,
  });
  const page = context.pages()[0] ?? (await context.newPage());
  await page.goto(config.targetUrl);
  return { config, context, page };
}

function parseCommandLine(argv) {
  const args = [...argv];
  const command = args[0] && !args[0].startsWith("-") ? args.shift() : "start-or-attach";
  return {
    command,
    dryRun: args.includes("--dry-run"),
  };
}

async function main() {
  const { command, dryRun } = parseCommandLine(process.argv.slice(2));

  if (command === "migrate") {
    if (dryRun) {
      process.stdout.write(`${JSON.stringify(buildMigrationPlan(process.env), null, 2)}\n`);
      return;
    }
    process.stdout.write(`${JSON.stringify(migrateChromeProfile(process.env), null, 2)}\n`);
    return;
  }

  if (command === "status") {
    process.stdout.write(`${JSON.stringify(await inspectManualBrowserState(process.env), null, 2)}\n`);
    return;
  }

  if (command !== "start-or-attach") {
    throw new Error(`Unsupported command: ${command}`);
  }

  if (dryRun) {
    process.stdout.write(
      `${JSON.stringify(buildManualBrowserLaunchConfig(process.env), null, 2)}\n`,
    );
    return;
  }

  if (process.env.CI === "1" && resolveBrowserMode(process.env) === "real_chrome_profile") {
    throw new Error("real Chrome profile mode is local-only and cannot run under CI");
  }

  if (resolveBrowserMode(process.env) === "managed_playwright") {
    const { config, context } = await launchManagedPlaywright(process.env);
    process.stdout.write(
      [
        "[browser-manual] launched",
        `browserMode=${config.browserMode}`,
        `userDataDir=${config.userDataDir}`,
        `targetUrl=${config.targetUrl}`,
      ].join("\n") + "\n",
    );

    const shutdown = async () => {
      await context.close();
      process.exit(0);
    };
    process.on("SIGINT", () => void shutdown());
    process.on("SIGTERM", () => void shutdown());
    return;
  }

  const { action, config, ensuredTargets, identityPage, state, statePath } = await attachToRealChrome(process.env);
  process.stdout.write(
    `${JSON.stringify(
      {
        command: "start-or-attach",
        action,
        browserMode: config.browserMode,
        userDataDir: config.userDataDir,
        profileKey: config.profileKey,
        cdpUrl: config.cdpUrl,
        cdpPort: config.cdpPort,
        statePath,
        pid: state?.pid ?? null,
        targetUrl: config.targetUrl,
        identityPagePath: identityPage.identityPath,
        identityPageUrl: identityPage.identityUrl,
        identityLabel: identityPage.repoLabel,
        identityAccent: identityPage.accent,
        ensuredTargets,
      },
      null,
      2,
    )}\n`,
  );
}

if (import.meta.url === pathToFileURL(process.argv[1] || "").href) {
  void main();
}
