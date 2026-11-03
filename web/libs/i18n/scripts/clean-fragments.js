#!/usr/bin/env node
/**
 * [pxs-i18n] Revert `t()` wrapping for strings that must not be translated:
 * fragments split around JSX elements (`of`, `or`, ...) and anything that
 * carries an HTML entity (it reads as markup, not copy).
 *
 * Reads `src/locales/extracted.json`, rewrites matching call sites back to the
 * original literal, and drops the keys from the dictionary.
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "../../..");
const DICT = path.join(__dirname, "../src/locales/extracted.json");

const FRAGMENTS = new Set(["of", "or", "Use", "See", "new)", "and", "to", "by", "in", "on"]);

const dictionary = JSON.parse(fs.readFileSync(DICT, "utf8"));
const drop = Object.entries(dictionary).filter(([, text]) => FRAGMENTS.has(text.trim()) || text.includes("&"));

if (!drop.length) {
  console.log("nothing to revert");
  process.exit(0);
}

const targets = [
  "apps/labelstudio/src",
  "libs/app-common/src",
  "libs/ui/src",
  "libs/datamanager/src",
  "libs/editor/src",
].map((p) => path.resolve(ROOT, p));

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (["node_modules", "__tests__", "stories", "cypress"].includes(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else if (/\.(tsx|jsx)$/.test(entry.name)) out.push(full);
  }
  return out;
}

let reverted = 0;
for (const file of targets.flatMap((t) => walk(t))) {
  let code = fs.readFileSync(file, "utf8");
  let changed = false;
  for (const [key, text] of drop) {
    const call = `{t("${key}")}`;
    if (!code.includes(call)) continue;
    const escaped = text.replace(/"/g, '\\"');
    code = code.split(`={t("${key}")}`).join(`="${escaped}"`);
    code = code.split(`{t("${key}")}`).join(text);
    changed = true;
    reverted += 1;
  }
  if (changed) fs.writeFileSync(file, code);
}

for (const [key] of drop) delete dictionary[key];
fs.writeFileSync(DICT, JSON.stringify(dictionary, Object.keys(dictionary).sort().reduce((a, k) => ((a[k] = true), a), {}), 2) + "\n");
console.log(`reverted ${reverted} call sites, dropped ${drop.length} keys, ${Object.keys(dictionary).length} left`);
