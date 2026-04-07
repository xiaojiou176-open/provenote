import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import libCoverage from "istanbul-lib-coverage";
import libReport from "istanbul-lib-report";
import reports from "istanbul-reports";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(__dirname, "..");
const srcDir = path.join(frontendDir, "src");
const runtimeDir = path.resolve(
  frontendDir,
  "..",
  "..",
  ".runtime-cache",
  "test",
  "coverage-batches",
  "apps-web",
);
const FINAL_COVERAGE_DIR_REL = "../../.runtime-cache/test/coverage/apps/web";
const finalCoverageDir = path.resolve(frontendDir, FINAL_COVERAGE_DIR_REL);
const batchSize = Number(process.env.FRONTEND_COVERAGE_BATCH_SIZE ?? "12");
const maxBatches = Number(process.env.FRONTEND_COVERAGE_MAX_BATCHES ?? "0");
const maxSplitDepth = Number(process.env.FRONTEND_COVERAGE_MAX_SPLIT_DEPTH ?? "6");
const batchNodeOptions =
  process.env.FRONTEND_COVERAGE_NODE_OPTIONS ?? "--max-old-space-size=2048";

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await walk(fullPath)));
      continue;
    }
    if (/\.test\.(ts|tsx)$/.test(entry.name)) {
      files.push(fullPath);
    }
  }
  return files;
}

function chunk(items, size) {
  const result = [];
  for (let index = 0; index < items.length; index += size) {
    result.push(items.slice(index, index + size));
  }
  return result;
}

function runCommand(command, args, extraEnv = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: frontendDir,
      env: { ...process.env, ...extraEnv },
      stdio: ["ignore", "pipe", "pipe"],
      shell: false,
    });
    let combinedOutput = "";

    child.stdout.on("data", (chunk) => {
      const text = chunk.toString();
      combinedOutput += text;
      process.stdout.write(text);
    });

    child.stderr.on("data", (chunk) => {
      const text = chunk.toString();
      combinedOutput += text;
      process.stderr.write(text);
    });

    child.on("exit", (code, signal) => {
      if (code === 0) {
        resolve();
        return;
      }

      const failure = new Error(
        `${command} ${args.join(" ")} exited with ${code ?? "null"}${signal ? ` (signal: ${signal})` : ""}\n${combinedOutput}`,
      );
      failure.exitCode = code;
      failure.signal = signal;
      reject(failure);
    });

    child.on("error", reject);
  });
}

function buildVitestArgs(testFiles) {
  return [
    "vitest",
    "run",
    "--coverage",
    "--coverage.provider=istanbul",
    "--coverage.thresholds.lines=0",
    "--coverage.thresholds.functions=0",
    "--coverage.thresholds.statements=0",
    "--coverage.thresholds.branches=0",
    "--maxWorkers=1",
    ...testFiles.map((testFile) => path.relative(frontendDir, testFile)),
  ];
}

function isOutOfMemoryLike(error) {
  const message = String(error?.message ?? "");
  return (
    error?.exitCode === 137 ||
    error?.signal === "SIGKILL" ||
    message.includes("exited with 137") ||
    message.includes("signal: SIGKILL")
  );
}

function isCoverageTempWriteLike(error) {
  const message = String(error?.message ?? "");
  return (
    message.includes("ENOENT") &&
    message.includes(".tmp") &&
    message.includes("coverage-") &&
    (message.includes("no such file or directory") || message.includes("lstat"))
  );
}

async function loadCoveragePayloads(batchDir) {
  const coveragePath = path.join(batchDir, "coverage-final.json");
  try {
    return [JSON.parse(await fs.readFile(coveragePath, "utf8"))];
  } catch (error) {
    if (error?.code !== "ENOENT") {
      throw error;
    }
  }

  const tmpDir = path.join(batchDir, ".tmp");
  const coverageFiles = (await fs.readdir(tmpDir))
    .filter((entry) => /^coverage-\d+\.json$/.test(entry))
    .sort((left, right) => left.localeCompare(right, undefined, { numeric: true }));

  if (coverageFiles.length === 0) {
    throw new Error(`Missing coverage artifacts under ${batchDir}`);
  }

  return Promise.all(
    coverageFiles.map(async (filename) =>
      JSON.parse(await fs.readFile(path.join(tmpDir, filename), "utf8")),
    ),
  );
}

async function runCoverageBatch(batchTests, batchDir, splitDepth = 0) {
  await fs.rm(batchDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  await fs.mkdir(batchDir, { recursive: true });
  await fs.mkdir(path.join(batchDir, ".tmp"), { recursive: true });

  try {
    await runCommand(
      process.platform === "win32" ? "npx.cmd" : "npx",
      buildVitestArgs(batchTests),
      {
        FRONTEND_COVERAGE_BATCH_MODE: "1",
        FRONTEND_COVERAGE_REPORTS_DIR: path.relative(frontendDir, batchDir),
        NODE_OPTIONS: [process.env.NODE_OPTIONS, batchNodeOptions].filter(Boolean).join(" ").trim(),
      },
    );
    return await loadCoveragePayloads(batchDir);
  } catch (error) {
    const failureMode = isOutOfMemoryLike(error)
      ? "oom-like"
      : isCoverageTempWriteLike(error)
        ? "coverage-temp-write"
        : "nonzero-exit";
    const canSplit = batchTests.length > 1 && splitDepth < maxSplitDepth;

    if (!canSplit) {
      throw error;
    }

    const middle = Math.ceil(batchTests.length / 2);
    const left = batchTests.slice(0, middle);
    const right = batchTests.slice(middle);

    console.warn(
      `[coverage-batch] ${failureMode} in batch size ${batchTests.length}; splitting into ${left.length}+${right.length} (depth=${splitDepth + 1})`,
    );

    const leftCoverage = await runCoverageBatch(left, `${batchDir}-a`, splitDepth + 1);
    const rightCoverage = await runCoverageBatch(right, `${batchDir}-b`, splitDepth + 1);
    return [...leftCoverage, ...rightCoverage];
  }
}

async function main() {
  await fs.rm(runtimeDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  await fs.rm(finalCoverageDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  await fs.mkdir(runtimeDir, { recursive: true });

  const allTests = (await walk(srcDir)).sort();
  const batches = chunk(allTests, batchSize);
  const selectedBatches = maxBatches > 0 ? batches.slice(0, maxBatches) : batches;
  const coverageMap = libCoverage.createCoverageMap({});

  for (let index = 0; index < selectedBatches.length; index += 1) {
    const batchDir = path.join(runtimeDir, `batch-${index + 1}`);
    const batchTests = selectedBatches[index];
    const coveragePayloads = await runCoverageBatch(batchTests, batchDir);
    for (const payload of coveragePayloads) {
      coverageMap.merge(payload);
    }
  }

  await fs.mkdir(finalCoverageDir, { recursive: true });
  await fs.writeFile(
    path.join(finalCoverageDir, "coverage-final.json"),
    JSON.stringify(coverageMap.toJSON()),
  );

  const context = libReport.createContext({
    dir: finalCoverageDir,
    coverageMap,
  });

  reports.create("text").execute(context);
  reports.create("html").execute(context);
  reports.create("lcov").execute(context);
  reports.create("json-summary").execute(context);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
