#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const rulesPath = path.join(repoRoot, "config/architecture/frontend-layer-boundaries.json");
const payload = JSON.parse(fs.readFileSync(rulesPath, "utf8"));

const pathLayers = payload.path_layers ?? [];
const layerImportRules = payload.layer_import_rules ?? {};
const allowedExtensions = new Set([".ts", ".tsx", ".js", ".jsx", ".mjs"]);
const importPattern =
  /^\s*import(?:["'\s]*[\w*{}\n\r\t, ]+from\s*)?["']([^"']+)["'];?\s*$/gm;

function walk(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walk(fullPath));
      continue;
    }
    if (allowedExtensions.has(path.extname(entry.name))) {
      files.push(fullPath);
    }
  }
  return files;
}

function normalize(relPath) {
  return relPath.split(path.sep).join("/");
}

function resolveLayer(relPath) {
  for (const item of pathLayers) {
    if (relPath.startsWith(item.prefix)) {
      return item.layer;
    }
  }
  return null;
}

function resolveImportToLayer(sourceRelPath, importPath) {
  if (!importPath.startsWith("@/")) {
    return null;
  }
  const aliasRelPath = normalize(
    path.join("apps/web/src", importPath.slice(2))
  );
  for (const item of pathLayers) {
    if (aliasRelPath.startsWith(item.prefix)) {
      return item.layer;
    }
  }
  if (sourceRelPath.startsWith("apps/web/src/lib/api/") && aliasRelPath.startsWith("apps/web/src/lib/api/generated/")) {
    return "lib_api";
  }
  return null;
}

const scanRoot = path.join(repoRoot, "apps/web/src");
const violations = [];

for (const filePath of walk(scanRoot)) {
  const relPath = normalize(path.relative(repoRoot, filePath));
  const sourceLayer = resolveLayer(relPath);
  if (!sourceLayer) {
    continue;
  }
  const allowed = new Set(layerImportRules[sourceLayer] ?? []);
  const content = fs.readFileSync(filePath, "utf8");
  for (const match of content.matchAll(importPattern)) {
    const importPath = match[1];
    const targetLayer = resolveImportToLayer(relPath, importPath);
    if (!targetLayer) {
      continue;
    }
    if (!allowed.has(targetLayer)) {
      const lineNo = content.slice(0, match.index).split("\n").length;
      violations.push(
        `${relPath}:${lineNo}: layer '${sourceLayer}' must not import '${importPath}' (target layer '${targetLayer}')`
      );
    }
  }
}

if (violations.length > 0) {
  for (const violation of violations) {
    console.log(`FAIL: ${violation}`);
  }
  process.exit(1);
}

console.log("PASS: frontend layer boundary rules hold for first-party imports.");
