import { Button } from "@humansignal/ui";
import { type Locale, changeLanguage, getLanguage, t } from "@humansignal/i18n";

const NEXT_LOCALE: Record<Locale, Locale> = {
  en: "zh-CN",
  "zh-CN": "en",
};

/**
 * [pxs-i18n] Two-state language switch for the header.
 *
 * Switching persists the choice (localStorage for the bundles, `django_language`
 * for Django) and reloads, so the shell, Data Manager and the editor all come
 * back in the same language.
 */
export const LanguageSwitcher = () => {
  const current = getLanguage();
  const next = NEXT_LOCALE[current];
  const tooltip = next === "zh-CN" ? t("common.language.to_chinese") : t("common.language.to_english");

  return (
    <Button
      variant="neutral"
      look="outlined"
      size="small"
      tooltip={tooltip}
      aria-label={tooltip}
      data-testid="language-switcher"
      onClick={() => changeLanguage(next)}
    >
      {next === "zh-CN" ? "中" : "EN"}
    </Button>
  );
};

export default LanguageSwitcher;
