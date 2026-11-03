#!/usr/bin/env node
/**
 * [pxs-i18n] One-shot string extractor.
 *
 * Wraps user-visible English copy in `t("<semantic key>")`, adds the import and
 * prints the `key -> english` map so the locale files can be regenerated.
 *
 * Design notes:
 * - keys are derived from the file path + a slug of the text, e.g.
 *   `pages.settings.storage_settings.storage_card.sync_storage`
 *   (stable, readable, no hand naming for thousands of strings)
 * - only *text positions* are rewritten (JSX text, whitelisted attributes);
 *   every other byte of the file stays identical, so diffs stay reviewable
 * - text that looks like code/data (paths, ids, formats) is skipped
 *
 * Usage: node libs/i18n/scripts/extract.js <dir> [<dir> ...] [--dry]
 */
const fs = require("fs");
const path = require("path");
const parser = require("@babel/parser");

const ROOT = path.resolve(__dirname, "../../..");
const IMPORT_LINE = 'import { t } from "@humansignal/i18n";';

const ATTRS = new Set(["title", "label", "placeholder", "aria-label", "alt", "tooltip", "description", "text"]);

const SKIP_DIRS = new Set(["node_modules", "__tests__", "__mocks__", "stories", "cypress", "dist", "coverage"]);

const SCOPES = [
  ["apps/labelstudio/src", "pages"],
  ["libs/app-common/src", "appcommon"],
  ["libs/ui/src", "ui"],
  ["libs/datamanager/src", "dm"],
  ["libs/editor/src", "lsf"],
];

const slug = (value) =>
  value
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/[^A-Za-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .toLowerCase();

const fileSlug = (file) =>
  slug(
    path
      .basename(file)
      .replace(/\.(tsx?|jsx?|mjs)$/, "")
      .replace(/([a-z0-9])([A-Z])/g, "$1_$2"),
  );

function scopeFor(rel) {
  for (const [prefix, scope] of SCOPES) {
    if (rel.startsWith(prefix + "/")) {
      const rest = rel.slice(prefix.length + 1);
      const dirs = path.dirname(rest).split("/").filter((d) => d && d !== ".");
      const dirSlug = dirs.slice(-2).map(slug).filter(Boolean).join(".");
      return { scope, dirSlug };
    }
  }
  return null;
}

function textKey(text) {
  const words = text
    .replace(/['"“”‘’]/g, "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 5)
    .join("_");
  return slug(words).slice(0, 48) || "text";
}

function isTranslatable(text) {
  const value = text.trim();
  if (value.length < 2 || value.length > 220) return false;
  if (/[<>{}$`]/.test(value)) return false;
  if (/^[\d\s.,:%/·\-–—+()]+$/.test(value)) return false;
  if (/^(https?:|\/|\.\/|#)/.test(value)) return false;
  if (/^[A-Z0-9_]{4,}$/.test(value)) return false; // constants / acronyms
  if (!/[A-Za-z]{2}/.test(value)) return false;
  return true;
}

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (SKIP_DIRS.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else if (/\.(tsx|jsx)$/.test(entry.name) && !/\.(test|spec|stories)\./.test(entry.name)) out.push(full);
  }
  return out;
}

function parse(code) {
  return parser.parse(code, {
    sourceType: "module",
    plugins: ["jsx", "typescript", "classProperties", "decorators-legacy", "objectRestSpread", "optionalChaining", "nullishCoalescingOperator", "topLevelAwait"],
    errorRecovery: true,
    tokens: true,
  });
}

function walkAst(node, visit, parent = null) {
  if (!node || typeof node.type !== "string") return;
  visit(node, parent);
  for (const key of Object.keys(node)) {
    if (key === "loc" || key === "leadingComments" || key === "trailingComments" || key === "tokens") continue;
    const value = node[key];
    if (Array.isArray(value)) {
      for (const item of value) if (item && typeof item.type === "string") walkAst(item, visit, node);
    } else if (value && typeof value.type === "string") {
      walkAst(value, visit, node);
    }
  }
}

function processFile(file) {
  const rel = path.relative(ROOT, file).split(path.sep).join("/");
  const scope = scopeFor(rel);
  if (!scope) return null;

  const code = fs.readFileSync(file, "utf8");
  let ast;
  try {
    ast = parse(code);
  } catch (error) {
    return { file: rel, error: String(error.message).slice(0, 120) };
  }

  const replacements = [];
  const found = new Map(); // key -> english

  const makeKey = (text) => {
    const base = [scope.scope, scope.dirSlug, fileSlug(file), textKey(text)].filter(Boolean).join(".");
    let key = base;
    let index = 2;
    while (found.has(key) && found.get(key) !== text) key = `${base}_${index++}`;
    found.set(key, text);
    return key;
  };

  walkAst(ast, (node, parent) => {
    if (node.type === "JSXText") {
      const raw = code.slice(node.start, node.end);
      const trimmed = raw.trim();
      if (!isTranslatable(trimmed)) return;
      const parentTag = parent?.openingElement?.name?.name;
      if (["code", "pre", "style", "script"].includes(parentTag)) return;

      const leading = raw.indexOf(trimmed);
      const start = node.start + leading;
      const end = start + trimmed.length;
      const key = makeKey(trimmed);
      replacements.push({ start, end, code: `{t("${key}")}` });
      return;
    }

    if (node.type === "JSXAttribute" && node.value && node.value.type === "StringLiteral") {
      const name = node.name?.name;
      if (!ATTRS.has(name)) return;
      const value = node.value.value;
      if (!isTranslatable(value)) return;
      if (/[/_:.]{1}/.test(value) && value.split(" ").length === 1) return; // single token, likely id/format
      const key = makeKey(value);
      replacements.push({ start: node.value.start, end: node.value.end, code: `{t("${key}")}` });
    }
  });

  if (!replacements.length) return { file: rel, count: 0, found };

  let output = code;
  for (const change of replacements.sort((a, b) => b.start - a.start)) {
    output = output.slice(0, change.start) + change.code + output.slice(change.end);
  }

  if (!/from\s+["']@humansignal\/i18n["']/.test(output)) {
    const lines = output.split("\n");
    let insertAt = 0;
    for (let i = 0; i < lines.length; i++) {
      if (/^\s*import\s/.test(lines[i])) insertAt = i + 1;
      else if (lines[i].trim() && !/^\s*(\/\/|\/\*|\*)/.test(lines[i]) && i > 0 && !/^\s*import/.test(lines[i])) break;
    }
    lines.splice(insertAt, 0, IMPORT_LINE);
    output = lines.join("\n");
  }

  fs.writeFileSync(file, output);
  return { file: rel, count: replacements.length, found };
}

const args = process.argv.slice(2).filter((a) => !a.startsWith("--"));
const targets = args.length ? args : ["apps/labelstudio/src", "libs/app-common/src", "libs/ui/src", "libs/datamanager/src", "libs/editor/src"];

const files = targets.flatMap((target) => {
  const resolved = path.resolve(ROOT, target);
  return fs.statSync(resolved).isDirectory() ? walk(resolved) : [resolved];
});
const dictionary = {};
let touched = 0;
let strings = 0;
const errors = [];

for (const file of files) {
  const result = processFile(file);
  if (!result) continue;
  if (result.error) {
    errors.push(`${result.file}: ${result.error}`);
    continue;
  }
  if (result.count) {
    touched += 1;
    strings += result.count;
    Object.assign(dictionary, Object.fromEntries(result.found));
  }
}

const outFile = path.join(__dirname, "../src/locales/extracted.json");
fs.writeFileSync(outFile, JSON.stringify(dictionary, Object.keys(dictionary).sort().reduce((a, k) => ((a[k] = true), a), {}), 2) + "\n");

console.log(`files touched: ${touched}, strings wrapped: ${strings}, unique keys: ${Object.keys(dictionary).length}`);
if (errors.length) console.log(`parse errors (${errors.length}):\n` + errors.slice(0, 10).join("\n"));
