#!/usr/bin/env node
/**
 * [pxs-i18n] Report-only scanner: lists user-visible English that is NOT wrapped
 * in `t()`, so leftovers can be fixed by hand (extract.js only wraps JSX text
 * and a few attributes; object literals and template strings need review).
 *
 * Usage: node libs/i18n/scripts/scan.js <path> [<path> ...]
 */
const fs = require("fs");
const path = require("path");
const parser = require("@babel/parser");

const ROOT = path.resolve(__dirname, "../../..");
const ATTRS = new Set(["title", "label", "placeholder", "aria-label", "alt", "tooltip", "text", "buttonLabel"]);
const SKIP_DIRS = new Set(["node_modules", "__tests__", "__mocks__", "stories", "cypress", "dist", "coverage"]);

function isTranslatable(value) {
  const text = value.trim();
  if (text.length < 2 || text.length > 220) return false;
  if (/[<>{}$`]/.test(text)) return false;
  if (/^[\d\s.,:%/·\-–—+()]+$/.test(text)) return false;
  if (/^(https?:|\/|\.\/|#)/.test(text)) return false;
  if (/^[A-Z0-9_]{4,}$/.test(text)) return false;
  if (!/[A-Za-z]{2}/.test(text)) return false;
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
    plugins: ["jsx", "typescript", "classProperties", "decorators-legacy", "topLevelAwait"],
    errorRecovery: true,
  });
}

const files = process.argv.slice(2).flatMap((target) => {
  const resolved = path.resolve(ROOT, target);
  return fs.statSync(resolved).isDirectory() ? walk(resolved) : [resolved];
});

let total = 0;
for (const file of files) {
  const rel = path.relative(ROOT, file);
  const code = fs.readFileSync(file, "utf8");
  let ast;
  try {
    ast = parse(code);
  } catch (error) {
    console.log(`${rel}: parse error ${error.message}`);
    continue;
  }

  const hits = [];
  (function walkAst(node, parent) {
    if (!node || typeof node.type !== "string") return;
    if (node.type === "JSXText") {
      const raw = code.slice(node.start, node.end).trim();
      if (isTranslatable(raw)) hits.push(`JSX text: ${raw.slice(0, 90)}`);
    }
    if (node.type === "JSXAttribute" && node.value?.type === "StringLiteral") {
      const name = node.name?.name;
      const value = node.value.value;
      if (ATTRS.has(name) && isTranslatable(value)) hits.push(`attr ${name}: ${value.slice(0, 90)}`);
    }
    if (node.type === "StringLiteral" && parent?.type === "ObjectProperty" && parent.value === node) {
      const key = parent.key?.name ?? parent.key?.value;
      if (["title", "label", "description", "help", "helpText", "placeholder", "tooltip", "text"].includes(key)) {
        if (isTranslatable(node.value)) hits.push(`prop ${key}: ${node.value.slice(0, 90)}`);
      }
    }
    for (const key of Object.keys(node)) {
      if (key === "loc" || key === "leadingComments" || key === "trailingComments") continue;
      const value = node[key];
      if (Array.isArray(value)) {
        for (const item of value) if (item && typeof item.type === "string") walkAst(item, node);
      } else if (value && typeof value.type === "string") {
        walkAst(value, node);
      }
    }
  })(ast, null);

  // template/multiline strings passed straight to render are common leftovers
  const templateHits = [...code.matchAll(/^\s*(?:label|title|description|help):\s*`([^`]{4,90})`/gm)].map(
    (m) => `tmpl: ${m[1].slice(0, 90)}`,
  );

  const all = [...hits, ...templateHits];
  if (all.length) {
    total += all.length;
    console.log(`\n### ${rel} (${all.length})`);
    for (const hit of all) console.log(`  ${hit}`);
  }
}
console.log(`\ntotal unwrapped candidates: ${total}`);
