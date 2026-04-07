import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";
import {
  BROWSER_IDENTITY_RUNTIME_DIRNAME,
  buildBrowserIdentityPageHtml,
  writeBrowserIdentityPage,
} from "./browser-instance-identity.mjs";

const tempRoots = new Set();

function makeTempRoot() {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "provenote-browser-identity-"));
  tempRoots.add(tempRoot);
  return tempRoot;
}

afterEach(() => {
  for (const tempRoot of tempRoots) {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
  tempRoots.clear();
});

describe("browser-instance-identity", () => {
  it("renders the core repo identity fields into the html payload", () => {
    const html = buildBrowserIdentityPageHtml({
      repoLabel: "provenote",
      repoRoot: "/tmp/provenote",
      cdpUrl: "http://127.0.0.1:9342",
      cdpPort: 9342,
      userDataDir: "/tmp/browser-root",
      profileName: "provenote",
      profileDirectory: "Profile 1",
      accent: "#2563eb",
      monogram: "PR",
      startUrl: "http://127.0.0.1:3100/",
    });

    expect(html).toContain("provenote");
    expect(html).toContain("http://127.0.0.1:9342");
    expect(html).toContain("/tmp/provenote");
    expect(html).toContain("/tmp/browser-root");
    expect(html).toContain("Profile 1");
    expect(html).toContain("Keep it as the left-most anchor");
    expect(html).toContain("Primary site");
    expect(html).toContain("browser lane");
  });

  it("writes the identity page under .runtime-cache/browser-identity", () => {
    const repoRoot = makeTempRoot();
    const result = writeBrowserIdentityPage({
      repoRoot,
      env: {},
      cdpPort: 9342,
      cdpUrl: "http://127.0.0.1:9342",
      browserProfile: {
        userDataDir: "/tmp/browser-root",
        profileName: "provenote",
        profileDirectory: "Profile 1",
      },
      startUrl: "http://127.0.0.1:3100/",
    });

    expect(result.identityPath).toBe(
      path.join(repoRoot, ".runtime-cache", BROWSER_IDENTITY_RUNTIME_DIRNAME, "index.html"),
    );
    expect(fs.existsSync(result.identityPath)).toBe(true);
    expect(fileURLToPath(result.identityUrl)).toBe(result.identityPath);

    const html = fs.readFileSync(result.identityPath, "utf8");
    expect(html).toContain(path.basename(repoRoot));
    expect(html).toContain("/tmp/browser-root");
    expect(html).toContain("http://127.0.0.1:9342");
  });

  it("honors explicit label and accent overrides", () => {
    const repoRoot = makeTempRoot();
    const result = writeBrowserIdentityPage({
      repoRoot,
      env: {
        PROVENOTE_BROWSER_IDENTITY_LABEL: "Provenote Lane",
        PROVENOTE_BROWSER_IDENTITY_ACCENT: "#0f766e",
      },
      cdpPort: 9342,
      cdpUrl: "http://127.0.0.1:9342",
      browserProfile: {
        userDataDir: "/tmp/browser-root",
        profileName: "provenote",
        profileDirectory: "Profile 1",
      },
      startUrl: "http://127.0.0.1:3100/",
    });

    expect(result.repoLabel).toBe("Provenote Lane");
    expect(result.accent).toBe("#0f766e");
    expect(result.monogram).toBe("PL");
  });
});
