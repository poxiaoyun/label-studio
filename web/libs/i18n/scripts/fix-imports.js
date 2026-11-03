#!/usr/bin/env node
/**
 * [pxs-i18n] Repair the `t` import after the bulk wrap.
 *
 * The first pass inserted the import line by scanning lines, which could drop it
 * inside a multi-line `import { ... }` block. This script removes every injected
 * line and re-inserts it after the last top-level import (AST based), so files
 * that use `t(` end up with exactly one correctly placed import.
 */
const fs = require("fs");
const path = require("path");
const parser = require("@babel/parser");

const ROOT = path.resolve(__dirname, "../../..");
const IMPORT_LINE = 'import { t } from "@humanignal/i18n";'.replace("humanignal", "humansignal");

const targets = ["apps/labelstudio/src", "libs/app-common/src", "libs/ui/src", "libs/datamanager/src", "libs/editor/src"].map(
  (p) => path.resolve(ROOT, p),
);

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (["node_modules", "__tests__", "stories", "cypress"].includes(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else if (/\.(tsx|jsx)$/.test(entry.name)) out.push(full);
  }
  return out;
}

let fixed = 0;
for (const file of targets.flatMap((t) => walk(t))) {
  let code = fs.readFileSync(file, "utf8");
  if (!code.includes(IMPORT_LINE) && !code.includes('t("')) continue;

  // 1. drop every previously injected line
  const withoutStray = code
    .split("\n")
    .filter((line) => line.trim() !== IMPORT_LINE)
    .join("\n");

  const usesT = /\bt\((["'`])/.test(withoutStray);
  if (!usesT) {
    if (withoutStray !== code) fs.writeFileSync(file, withoutStray);
    continue;
  }

  if (withoutStray.includes('from "@humansignal/i18n"')) {
    if (withoutStray !== code) fs.writeFileSync(file, withoutStray);
    continue;
  }

  // 2. insert after the last import declaration
  let ast;
  try {
    ast = parser.parse(withoutStray, {
      sourceType: "module",
      plugins: ["jsx", "typescript", "classProperties", "decorators-legacy", "objectRestSpread", "optionalChaining", "topLevelAwait"],
      errorRecovery: true,
    });
  } catch {
    continue;
  }

  const imports = ast.program.body.filter((node) => node.type === "ImportDeclaration");
  const anchor = imports.length ? imports[imports.length - 1] : null;
  let output;
  if (anchor) {
    const end = anchor.end;
    output = `${withoutStray.slice(0, end)}\n${IMPORT_LINE}${withoutStray.slice(end)}`;
  } else {
    output = `${IMPORT_LINE}\n${withoutStray}`;
  }

  fs.writeFileSync(file, output);
  fixed += 1;
}

console.log(`re-inserted import in ${fixed} files`);
