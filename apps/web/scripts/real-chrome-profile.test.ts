import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  buildManagedPlaywrightLaunchConfig,
  buildManualBrowserLaunchConfig,
  buildMigrationPlan,
  buildRealChromeLaunchConfig,
  openTargetUrlOverCdp,
  resolveBrowserInstanceStateFile,
  resolveBrowserMode,
  resolveChromeCdpPort,
  resolveChromeCdpUrl,
  resolveChromeProfileKey,
  resolveChromeProfileName,
  resolveChromeSourceUserDataDir,
  resolveChromeUserDataDir,
  resolveManualPlaywrightProfileDir,
  rewriteMigratedLocalState,
} from "./real-chrome-profile.mjs";

describe("real chrome profile helpers", () => {
  function createSourceRoot(profileKey = "Profile 25") {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "notebooklab-chrome-source-"));
    const sourceRoot = path.join(root, "Library", "Application Support", "Google", "Chrome");
    fs.mkdirSync(path.join(sourceRoot, profileKey), { recursive: true });
    fs.writeFileSync(
      path.join(sourceRoot, "Local State"),
      JSON.stringify({
        profile: {
          info_cache: {
            [profileKey]: {
              name: "notebooklab",
            },
          },
          last_used: profileKey,
        },
      }),
      "utf8",
    );
    return { root, sourceRoot };
  }

  it("defaults the profile name to notebooklab", () => {
    expect(resolveChromeProfileName({} as NodeJS.ProcessEnv)).toBe("notebooklab");
  });

  it("defaults browser mode to real_chrome_profile", () => {
    expect(resolveBrowserMode({} as NodeJS.ProcessEnv)).toBe("real_chrome_profile");
  });

  it("defaults the target chrome user data dir into the repo machine cache root", () => {
    expect(resolveChromeUserDataDir({ HOME: "/Users/example" } as NodeJS.ProcessEnv)).toBe(
      "/Users/example/.cache/notebooklab/browser/chrome-user-data",
    );
  });

  it("defaults the source chrome user data dir to the system Chrome root", () => {
    expect(
      resolveChromeSourceUserDataDir({ HOME: "/Users/example" } as NodeJS.ProcessEnv),
    ).toBe("/Users/example/Library/Application Support/Google/Chrome");
  });

  it("defaults browser state file into repo runtime cache", () => {
    expect(resolveBrowserInstanceStateFile({} as NodeJS.ProcessEnv)).toContain(
      ".runtime-cache/browser/chrome-instance.json",
    );
  });

  it("defaults managed profile dir into repo runtime cache", () => {
    expect(
      resolveManualPlaywrightProfileDir({
        PWD: "/Users/example/notebooklab/apps/web",
      } as NodeJS.ProcessEnv),
    ).toContain(".runtime-cache/browser/manual-playwright-profile");
  });

  it("defaults the CDP port and URL", () => {
    expect(resolveChromeCdpPort({} as NodeJS.ProcessEnv)).toBe(9342);
    expect(resolveChromeCdpUrl({} as NodeJS.ProcessEnv)).toBe("http://127.0.0.1:9342");
  });

  it("resolves profile key from Local State by profile name", () => {
    const key = resolveChromeProfileKey(
      {
        profile: {
          info_cache: {
            "Profile 24": { name: "other" },
            "Profile 25": { name: "notebooklab" },
          },
        },
      },
      "notebooklab",
      undefined,
    );

    expect(key).toBe("Profile 25");
  });

  it("prefers explicit profile key over Local State lookup", () => {
    expect(
      resolveChromeProfileKey(
        {
          profile: {
            info_cache: {
              "Profile 25": { name: "notebooklab" },
            },
          },
        },
        "notebooklab",
        "Profile 99",
      ),
    ).toBe("Profile 99");
  });

  it("rewrites migrated Local State to only keep Profile 1", () => {
    const rewritten = rewriteMigratedLocalState(
      {
        profile: {
          info_cache: {
            "Profile 25": { name: "notebooklab", avatar_icon: "foo" },
            "Profile 31": { name: "other" },
          },
          last_used: "Profile 25",
          last_active_profiles: ["Profile 25", "Profile 31"],
        },
      },
      "Profile 25",
      "Profile 1",
      "notebooklab",
    );

    expect(rewritten.profile.info_cache).toEqual({
      "Profile 1": {
        name: "notebooklab",
        avatar_icon: "foo",
      },
    });
    expect(rewritten.profile.last_used).toBe("Profile 1");
    expect(rewritten.profile.last_active_profiles).toEqual(["Profile 1"]);
  });

  it("builds a migration plan from source Profile 25 into target Profile 1", () => {
    const { root } = createSourceRoot();
    const plan = buildMigrationPlan({
      HOME: root,
      NOTEBOOKLAB_CHROME_PROFILE_NAME: "notebooklab",
    } as NodeJS.ProcessEnv);

    expect(plan.sourceUserDataDir).toBe(
      `${root}/Library/Application Support/Google/Chrome`,
    );
    expect(plan.sourceProfileKey).toBe("Profile 25");
    expect(plan.targetUserDataDir).toBe(
      `${root}/.cache/notebooklab/browser/chrome-user-data`,
    );
    expect(plan.targetProfileKey).toBe("Profile 1");
  });

  it("builds a real chrome start-or-attach config", () => {
    const config = buildRealChromeLaunchConfig({
      NOTEBOOKLAB_CHROME_USER_DATA_DIR: "/tmp/notebooklab-chrome",
      NOTEBOOKLAB_BROWSER_URL: "https://example.com",
    } as NodeJS.ProcessEnv);

    expect(config.command).toBe("start-or-attach");
    expect(config.browserMode).toBe("real_chrome_profile");
    expect(config.userDataDir).toBe("/tmp/notebooklab-chrome");
    expect(config.profileKey).toBe("Profile 1");
    expect(config.targetUrl).toBe("https://example.com");
    expect(config.channel).toBe("chrome");
    expect(config.cdpPort).toBe(9342);
    expect(config.cdpUrl).toBe("http://127.0.0.1:9342");
    expect(config.identityPage.repoLabel).toBe("notebooklab");
    expect(config.identityPage.identityPath).toContain(".runtime-cache/browser-identity/index.html");
    expect(config.identityPage.identityUrl.startsWith("file://")).toBe(true);
    expect(config.launchTargets[0]).toBe(config.identityPage.identityUrl);
    expect(config.launchTargets[1]).toBe("https://example.com");
    expect(config.args).toContain("--profile-directory=Profile 1");
    expect(config.args).toContain("--remote-debugging-port=9342");
  });

  it("builds a managed Playwright fallback config when requested", () => {
    const config = buildManagedPlaywrightLaunchConfig({
      NOTEBOOKLAB_BROWSER_MODE: "managed_playwright",
      NOTEBOOKLAB_MANAGED_PLAYWRIGHT_PROFILE_DIR: "/tmp/manual-profile",
      NOTEBOOKLAB_BROWSER_URL: "https://example.com",
    } as NodeJS.ProcessEnv);

    expect(config.command).toBe("start-or-attach");
    expect(config.browserMode).toBe("managed_playwright");
    expect(config.userDataDir).toBe("/tmp/manual-profile");
    expect(config.channel).toBe("chromium");
    expect(config.args).toEqual([]);
  });

  it("passes explicit identity label and accent into the real chrome config", () => {
    const config = buildRealChromeLaunchConfig({
      NOTEBOOKLAB_CHROME_USER_DATA_DIR: "/tmp/notebooklab-chrome",
      NOTEBOOKLAB_BROWSER_IDENTITY_LABEL: "Notebooklab Lane",
      NOTEBOOKLAB_BROWSER_IDENTITY_ACCENT: "#2563eb",
    } as NodeJS.ProcessEnv);

    expect(config.identityPage.repoLabel).toBe("Notebooklab Lane");
    expect(config.identityPage.accent).toBe("#2563eb");
    expect(config.identityPage.monogram).toBe("PL");
  });

  it("routes the generic launch builder through managed mode when requested", () => {
    const config = buildManualBrowserLaunchConfig({
      NOTEBOOKLAB_BROWSER_MODE: "managed_playwright",
      NOTEBOOKLAB_MANAGED_PLAYWRIGHT_PROFILE_DIR: "/tmp/manual-profile",
    } as NodeJS.ProcessEnv);

    expect(config.browserMode).toBe("managed_playwright");
    expect(config.userDataDir).toBe("/tmp/manual-profile");
  });

  it("opens a new page through the attached CDP browser", async () => {
    const calls: Array<{ type: string; payload?: unknown }> = [];
    let currentUrl = "about:blank";
    const fakePage = {
      goto: async (url: string, options: Record<string, unknown>) => {
        currentUrl = url;
        calls.push({ type: "goto", payload: { url, options } });
      },
      url: () => currentUrl,
    };
    const fakeContext = {
      pages: () => [],
      newPage: async () => {
        calls.push({ type: "newPage" });
        return fakePage;
      },
    };
    const fakeBrowser = {
      contexts: () => [fakeContext],
      close: async () => {
        calls.push({ type: "close" });
      },
    };

    await openTargetUrlOverCdp("http://127.0.0.1:9342", "https://example.com", {
      connect: async (cdpUrl: string) => {
        calls.push({ type: "connect", payload: cdpUrl });
        return fakeBrowser;
      },
    });

    expect(calls).toEqual([
      { type: "connect", payload: "http://127.0.0.1:9342" },
      { type: "newPage" },
      {
        type: "goto",
        payload: {
          url: "https://example.com",
          options: {
            waitUntil: "domcontentloaded",
            timeout: 45000,
          },
        },
      },
      { type: "close" },
    ]);
  });

  it("skips opening a new page when the target URL is about:blank", async () => {
    const calls: Array<{ type: string; payload?: unknown }> = [];

    await openTargetUrlOverCdp("http://127.0.0.1:9342", "about:blank", {
      connect: async (cdpUrl: string) => {
        calls.push({ type: "connect", payload: cdpUrl });
        return {
          contexts: () => [],
          close: async () => {
            calls.push({ type: "close" });
          },
        };
      },
    });

    expect(calls).toEqual([]);
  });
});
