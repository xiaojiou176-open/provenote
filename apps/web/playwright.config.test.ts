import { describe, expect, it } from "vitest";
import { getFrontendServerCommands } from "./playwright.config";

describe("getFrontendServerCommands", () => {
  it("uses production-style frontend server in CI mock mode", () => {
    const commands = getFrontendServerCommands({
      nextDistDir: ".runtime-cache/build/next-playwright",
      playwrightPort: 3113,
      apiBaseURL: "http://127.0.0.1:5113",
      useRealBackend: false,
      isCI: true,
    });

    expect(commands.frontendCommand).toContain("npm run build");
    expect(commands.frontendCommand).toContain(
      "PORT=3113 node .runtime-cache/build/next-playwright/standalone/server.js",
    );
    expect(commands.frontendCommand).not.toContain("npm run start");
    expect(commands.frontendCommand).not.toContain("npm run dev");
  });

  it("keeps dev server for local mock mode", () => {
    const commands = getFrontendServerCommands({
      nextDistDir: ".runtime-cache/build/next-playwright",
      playwrightPort: 3100,
      apiBaseURL: "http://127.0.0.1:5055",
      useRealBackend: false,
      isCI: false,
    });

    expect(commands.frontendCommand).toContain("npm run dev -- --webpack");
    expect(commands.frontendCommand).not.toContain("npm run build");
  });

  it("uses production-style frontend server for CI real-backend mode", () => {
    const commands = getFrontendServerCommands({
      nextDistDir: ".runtime-cache/build/next-playwright",
      playwrightPort: 3116,
      apiBaseURL: "http://127.0.0.1:5116",
      useRealBackend: true,
      isCI: true,
    });

    expect(commands.frontendCommandWithRealBackend).toContain("API_URL=http://127.0.0.1:5116");
    expect(commands.frontendCommandWithRealBackend).toContain("npm run build");
    expect(commands.frontendCommandWithRealBackend).toContain(
      "PORT=3116 node .runtime-cache/build/next-playwright/standalone/server.js",
    );
    expect(commands.frontendCommandWithRealBackend).not.toContain("npm run start");
    expect(commands.frontendCommandWithRealBackend).not.toContain("npm run dev");
  });
});
