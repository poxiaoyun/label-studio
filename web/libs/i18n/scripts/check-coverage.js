#!/usr/bin/env node
/**
 * [pxs-i18n] Coverage check for the zh-CN catalogue.
 *
 * Fails when a key exists in `en` but not in `zh-CN` (missing translation) or
 * when `zh-CN` has keys the source no longer produces (stale). Also lists
 * entries whose Chinese value still contains a long English run, which usually
 * means it was never translated.
 */
const fs = require("fs");
const path = require("path");

const dir = path.join(__dirname, "../src/locales");
const en = JSON.parse(fs.readFileSync(path.join(dir, "en.json"), "utf8"));
const zh = JSON.parse(fs.readFileSync(path.join(dir, "zh-CN.json"), "utf8"));

const enKeys = Object.keys(en);
const zhKeys = Object.keys(zh);

const missing = enKeys.filter((k) => !(k in zh));
const stale = zhKeys.filter((k) => !(k in en));
const untranslated = enKeys.filter(
  (k) => zh[k] === en[k] && /[A-Za-z]{3,}\s+[A-Za-z]{3,}/.test(en[k]) && !/^[A-Z ]{2,}$/.test(en[k]),
);

console.log(`keys: en=${enKeys.length} zh=${zhKeys.length}`);
if (missing.length) console.log(`missing (${missing.length}):\n  ` + missing.slice(0, 20).join("\n  "));
if (stale.length) console.log(`stale (${stale.length}):\n  ` + stale.slice(0, 20).join("\n  "));
if (untranslated.length)
  console.log(`possibly untranslated (${untranslated.length}):\n  ` + untranslated.slice(0, 20).join("\n  "));

// Every file that calls t() must import it: a missing import only surfaces at
// runtime, as a blank modal ("t is not defined"), so it is checked statically.
const ROOTS = ["apps/labelstudio/src", "libs/app-common/src", "libs/ui/src", "libs/datamanager/src", "libs/editor/src"];
const CALL = /(?<![\w.$])t\(\s*["']/;
const noImport = [];

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (["node_modules", "dist", "__tests__", "stories"].includes(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else if (/\.(tsx?|jsx?)$/.test(entry.name)) out.push(full);
  }
  return out;
}

for (const root of ROOTS) {
  const abs = path.join(__dirname, "../../..", root);
  if (!fs.existsSync(abs)) continue;
  for (const file of walk(abs)) {
    const body = fs.readFileSync(file, "utf8");
    if (!CALL.test(body)) continue;
    if (!body.includes('from "@humansignal/i18n"')) noImport.push(path.relative(abs, file));
  }
}

if (noImport.length)
  console.log(`t() without import (${noImport.length}):\n  ` + noImport.slice(0, 20).join("\n  "));

if (missing.length || stale.length || noImport.length) process.exit(1);
console.log("catalogue OK");
