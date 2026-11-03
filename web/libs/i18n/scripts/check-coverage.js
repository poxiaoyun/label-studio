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

if (missing.length || stale.length) process.exit(1);
console.log("catalogue OK");
