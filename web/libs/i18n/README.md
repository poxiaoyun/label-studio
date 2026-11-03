# web/libs/i18n — pxs 中文国际化

`@humansignal/i18n` 是外壳、Data Manager、标注器（LSF）三个 bundle 共用的运行时。

## 用法

```ts
import { t } from "@humansignal/i18n";

<h3>{t("pages.settings.storage_settings.storage_card.sync_storage")}</h3>
<Button title={t("...")} />
```

- 变量插值：`t("key", { count })` 对应文案里的 `{{count}}`。
- 缺 key 时回退英文，再回退 key 本身（不会出现空白）。
- 模块顶层也能用（provider 配置、菜单表等）：`t` 是普通函数，不依赖 hook。

## 为什么是普通函数而不是 `useTranslation`

三个 bundle 彼此独立、不共享 React 树，且大量文案写在模块作用域（provider 配置、
菜单表）。切换语言时统一「持久化 + reload」，所以不需要订阅式重渲染。

## 语言解析顺序

1. `localStorage["pxs-language"]`
2. `window.APP_SETTINGS.locale`（Django 按 `Accept-Language` / `django_language` cookie 解析后下发）
3. `navigator.languages`
4. `en`

切换时写 `localStorage` + `django_language` cookie（`zh-hans`）后 `location.reload()`，
三个 bundle 因此同时生效。

## 文案与 key

- key = `区域.目录.文件.文案slug`，由 `scripts/extract.js` 自动生成，例如
  `pages.settings.storage_settings.storage_card.sync_storage`。
- 资源是扁平的 `key -> text` JSON（`src/locales/en.json`、`zh-CN.json`），便于 diff 与机器校验。

## 重新抽取（上游升级后）

```bash
cd web
node libs/i18n/scripts/extract.js      # 包 t(), 输出 locales/extracted.json
node libs/i18n/scripts/clean-fragments.js   # 还原 of/or 等被拆散的片段
node libs/i18n/scripts/clean-lowercase.js   # 还原小写句尾片段
node libs/i18n/scripts/fix-imports.js       # 校正 import 位置（多行 import 安全）
```

新增文案不会自动进 `zh-CN.json`：缺 key 时显示英文，`npm run i18n:check` 可列出缺口。

## 已知限制

- 双态切换按钮只支持中/英；加第三种语言需要改成下拉（`LanguageSwitcher` 内 `NEXT_LOCALE` 表）。
- 英文句子里被 JSX 元素拆开的片段（`of` / `from the` / 小写句尾）保持英文，避免中文语序错乱。
- 文案由 AI 初翻 + 术语表（`label-studio-i18n-术语表.md`）校对，专业术语以该表为准。
