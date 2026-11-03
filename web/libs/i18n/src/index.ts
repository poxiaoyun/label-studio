/**
 * [pxs-i18n] Shared, dependency-free i18n runtime for the three front-end
 * bundles (shell, Data Manager, LSF editor).
 *
 * Why not i18next (decision C1): adding a runtime dependency to three separate
 * webpack builds in this fork costs a full dependency re-resolution and a
 * lockfile churn that outweighs the ~60 lines below. The public surface mirrors
 * i18next (`t`, `initI18n`, `changeLanguage`, `getLanguage`, `{{var}}`
 * interpolation, `en` fallback), so it can be swapped later by re-implementing
 * this file only.
 *
 * Why a plain `t()` instead of hooks:
 * - the three bundles do not share a React tree, and a lot of copy lives in
 *   module scope (provider configs, menu tables) where hooks are unavailable;
 * - switching persists the choice and reloads, so no re-render subscription.
 *
 * Keys are flat (`key -> text`) which keeps the locale files diffable.
 */
import en from "./locales/en.json";
import zhCN from "./locales/zh-CN.json";

export type Locale = "en" | "zh-CN";

export const SUPPORTED_LOCALES: Locale[] = ["en", "zh-CN"];

/** localStorage key; mirrors the theme's `preferred-color-scheme` pattern. */
export const STORAGE_KEY = "pxs-language";

/** Django reads this cookie for template / `gettext` rendering. */
export const COOKIE_NAME = "django_language";

const DJANGO_LOCALE: Record<Locale, string> = {
  en: "en",
  "zh-CN": "zh-hans",
};

const HTML_LANG: Record<Locale, string> = {
  en: "en",
  "zh-CN": "zh-CN",
};

export const LOCALE_LABEL: Record<Locale, string> = {
  en: "English",
  "zh-CN": "中文",
};

const RESOURCES: Record<Locale, Record<string, string>> = {
  en: en as Record<string, string>,
  "zh-CN": zhCN as Record<string, string>,
};

export function normalizeLocale(value?: string | null): Locale {
  if (!value) return "en";
  return value.toLowerCase().startsWith("zh") ? "zh-CN" : "en";
}

/** localStorage -> server-provided locale -> browser languages -> en. */
export function detectLocale(): Locale {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) return normalizeLocale(stored);
  } catch {
    // private mode / storage disabled
  }

  const fromServer = (window as any).APP_SETTINGS?.locale;
  if (fromServer) return normalizeLocale(fromServer);

  const languages = navigator.languages ?? (navigator.language ? [navigator.language] : []);
  for (const language of languages) {
    if (language?.toLowerCase().startsWith("zh")) return "zh-CN";
  }
  return "en";
}

let current: Locale = "en";
let initialized = false;

function applyDocumentLang(locale: Locale) {
  if (typeof document === "undefined") return;
  document.documentElement.lang = HTML_LANG[locale];
  document.documentElement.dataset.locale = locale;
}

export function initI18n(forcedLocale?: Locale): Locale {
  if (initialized) return current;
  current = forcedLocale ?? detectLocale();
  initialized = true;
  applyDocumentLang(current);
  return current;
}

export function getLanguage(): Locale {
  return current;
}

function interpolate(template: string, vars?: Record<string, unknown>): string {
  if (!vars) return template;
  return template.replace(/\{\{\s*(\w+)\s*\}\}/g, (match, name) => {
    const value = vars[name];
    return value === undefined || value === null ? match : String(value);
  });
}

/**
 * Translate `key`; falls back to English, then to the key itself.
 * Interpolation uses `{{name}}`.
 */
export function t(key: string, vars?: Record<string, unknown>): string {
  if (!initialized) initI18n();
  if (!key) return key;
  const template = RESOURCES[current]?.[key] ?? RESOURCES.en[key];
  if (template === undefined) return key;
  return interpolate(template, vars);
}

/** Language switch without reload (tests, storybook). */
export function setLanguage(locale: Locale): void {
  current = normalizeLocale(locale);
  initialized = true;
  applyDocumentLang(current);
}

function writeCookie(locale: Locale) {
  try {
    const value = encodeURIComponent(DJANGO_LOCALE[locale]);
    // one year, root path, lax: enough for Django to pick it up on the next request
    document.cookie = `${COOKIE_NAME}=${value}; path=/; max-age=31536000; samesite=lax`;
  } catch {
    // ignore
  }
}

/**
 * Persist the choice (localStorage for the bundles, cookie for Django) and
 * reload, so Data Manager and the editor - separate builds - start in the new
 * language too.
 */
export function changeLanguage(locale: Locale): void {
  const next = normalizeLocale(locale);
  try {
    window.localStorage.setItem(STORAGE_KEY, next);
  } catch {
    // ignore
  }
  writeCookie(next);
  setLanguage(next);
  window.location.reload();
}

/** Initialise on import so module-scope copy resolves correctly. */
if (typeof window !== "undefined") {
  initI18n();
}
