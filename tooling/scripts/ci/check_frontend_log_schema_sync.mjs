#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const schemaPath = path.join(repoRoot, "contracts/observability/log-event.schema.json");
const logPath = path.join(repoRoot, "apps/web/src/lib/log.ts");
const contextPath = path.join(repoRoot, "apps/web/src/lib/observability/run-context.ts");

const schema = JSON.parse(fs.readFileSync(schemaPath, "utf8"));
const logSource = fs.readFileSync(logPath, "utf8");
const contextSource = fs.readFileSync(contextPath, "utf8");

const requiredProperties = [
  "source_kind",
  "route",
  "browser_session_id",
  "workflow_name",
  "job_name",
];

const failures = [];
for (const property of requiredProperties) {
  if (!(property in (schema.properties ?? {}))) {
    failures.push(`log event schema missing frontend/CI property: ${property}`);
  }
  if (!logSource.includes(property) && !contextSource.includes(property)) {
    failures.push(`frontend logging runtime missing property binding: ${property}`);
  }
}

for (const property of ["timestamp", "level", "event", "component", "service", "domain", "run_id"]) {
  if (!logSource.includes(property)) {
    failures.push(`frontend logger missing core field: ${property}`);
  }
}

if (failures.length > 0) {
  for (const failure of failures) {
    console.log(`FAIL: ${failure}`);
  }
  process.exit(1);
}

console.log("PASS: frontend logging schema and runtime bindings are synchronized.");
