# pxs 定制说明

本文件记录 **本仓库相对上游 `HumanSignal/label-studio` 1.23.2 的全部改动**，供后续迭代与升级时对照。
改动落在一个长期分支 `1.23.2-pxs` 上，上游每发新版本就用 **merge-forward**（不是 rebase）把本分支合进新版本分支。

- 基线：上游 tag `1.23.2`
- 分支：`1.23.2-pxs`（一版一分支，下个版本是 `<新tag>-pxs`）
- 规模：`277` 个文件、`+9407 / −1498` 行；其中新增 `40`、修改 `237`、删除 `0`
- 前端改动集中在 `207` 个 `.jsx/.tsx`（国际化改写），后端 `34` 个文件（其中 `19` 个属 Moha 驱动）

> 维护规则：**每轮迭代先看「七、变更台账」，改完在表尾追加一行**，并同步更新对应章节的数字与文件清单。
> 章节顺序与代码结构一致，找东西按目录跳。

---

## 一、Moha 云存储驱动

在项目的 Cloud Storage 里新增一种 provider「Moha」，从魔哈（Moha）仓库直接读取/写入数据集，
同时支持 Source 与 Target Storage，走完整的 Label Studio 存储生命周期（测试连接 → 同步 → 导出）。

### 新增文件（`label_studio/io_storages/moha/`）

| 文件 | 职责 |
| --- | --- |
| `models.py` | `MohaImportStorage` / `MohaExportStorage` + URL 生成 + 保存时校验 |
| `client.py` | **唯一**的 SDK 边界，封装 `xiaoshiai_hub`（`HubClient`） |
| `uri.py` | `moha://组织/类型/仓库/版本/路径` 的解析与拼装 |
| `serializers.py` | DRF 序列化；含 endpoint 归一化与 SSRF 白名单校验 |
| `api.py` | 连接测试、同步触发、列表接口 |
| `registry.py` | provider 注册信息 |
| `urls.py` | 路由挂载点 |
| `form_layout.yml` | 前端表单字段分组与顺序 |
| `errors.py` | 把 SDK 异常翻译成可读错误 |
| `selfcheck.py` | 上游侵入预算自检（见第五节） |
| `README.md` | 驱动本身的使用与限制说明 |

配套：`label_studio/io_storages/migrations/0023_moha_import_export_storage.py`、
`label_studio/io_storages/tests/test_moha_{client,fake_server,integration_anchors,registration,storage,uri}.py`。

### 关键设计（改代码前先读）

- **SDK 只出现在 `client.py`**：升级 `moha-hub` 只改这一个文件，其它模块不感知 SDK 变化。
- **注册走 settings 覆写**：`core/settings/label_studio.py` 里对 `GET_STORAGE_LIST` 追加 Moha，
  不改上游 `io_storages/functions.py`，减少合并冲突。
- **URI 形态**：`moha://<org>/<type>/<repo>/<revision>/<path>`；仓库类型仅 `models` / `datasets` / `spaces`，
  驱动默认按数据集使用。
- **读取**：`/resolve` 302 到对象存储，**Range 请求原样透传**，不做本地缓存。
- **写入**：`upload_file` / `upload_folder`，一次请求等于一次 commit。
- **`type = 'moha'` 必须在 serializer 里显式覆写**，否则前端拼出的编辑/删除/同步路由会落到 `io_storages`。
- **endpoint 归一化**：`normalize_endpoint()` 会剥掉 `/console`、`/moha`、`/moha/v1`，
  因为控制台给的地址是带路径的。
- **Tasks 模式只认 json / jsonl / parquet**，遇到 `README.md` 之类跳过并记日志，避免整次同步失败。
- **SSRF**：`_endpoint_allowlisted()` 支持 CIDR 与域名后缀；集群内地址靠
  `MOHA_ENDPOINT_ALLOWLIST=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16` 放行。

### 依赖

`pyproject.toml` 增加 `moha-hub[upload]>=2.0.0,<3.0.0`（`upload` extra 用于目标存储）。
仓库里 PyPI 只有 2.0.1，**`poetry.lock` 没有跟着更新**，正式构建前需要跑一次 `poetry lock`。

---

## 二、前端国际化（zh-CN）

上游没有可用方案（i18next 在本仓库装不上），因此自建了一个 168 行的运行时（`web/libs/i18n/src/index.ts`），
API 与 i18next 同名，后续若真要换回 i18next 可以无痛替换。

### 新增（`web/libs/i18n/`）

| 路径 | 说明 |
| --- | --- |
| `src/index.ts` | 运行时：`t()` / `tTemplate()` / `initI18n()` / `changeLanguage()` / `getLanguage()`，支持 `{{var}}` 插值；常量 `SUPPORTED_LOCALES`、`LOCALE_LABEL` |
| `src/locales/en.json` | 英文词条 **1241** 条 |
| `src/locales/zh-CN.json` | 中文词条 **1241** 条（覆盖率 100%） |
| `src/locales/templates.json` | 标注模板标题的对照表（模板来自后端 YAML，不能直接改源码） |
| `scripts/extract.js` | 从 JSX 抽取待翻译文案 |
| `scripts/clean-fragments.js` | 合并被 JSX 拆散的句子片段 |
| `scripts/clean-lowercase.js` | 归一化大小写建键 |
| `scripts/fix-imports.js` | 用 AST 补 `import { t }`（**不要退回文本替换**，会插进多行 import 块里） |
| `scripts/scan.js` | 统计使用情况 |
| `scripts/check-coverage.js` | 门禁：缺失词条、冗余词条、用了 `t()` 却没 import |
| `README.md` | 词条约定与流水线说明 |

### 改造范围

- **207 个 `.jsx/.tsx`** 改为调用 `t()`，键名由文件路径派生（如 `dm.data_manager.toolbar.label_button.*`）。
- **后端**：`settings/base.py` 打开 `USE_I18N`、声明 `LANGUAGES = [('en',…), ('zh-hans',…)]` 与 `LOCALE_PATHS`；
  新增 `label_studio/locale/zh_Hans/LC_MESSAGES/django.po|.mo`（`.mo` 用 `msgfmt` 编译后提交）。
- **模板**：`templates/base.html` 输出 `<html lang>` 与 `locale`，供前端运行时读取。
- **语言切换**：右上角按钮；选择写入 `localStorage['pxs-language']` + `django_language` cookie，然后 `location.reload()`，
  这样三个独立 bundle（`react-app` / 数据管理器 / 编辑器）才同时生效。
- **必填标记**：上游用 CSS `content: "Required"` 渲染，中文靠 4 处 `Label.scss` 里
  `html[lang="zh-CN"]` 覆盖成「必填」。

### 改词条的标准动作

```bash
cd web
node libs/i18n/scripts/extract.js          # 抽取新文案
# 编辑 libs/i18n/src/locales/{en,zh-CN}.json
node libs/i18n/scripts/check-coverage.js   # 必须为 0 缺口
NODE_ENV=production yarn build             # 只构建 shell
node_modules/.bin/nx run-many -t build -p editor datamanager --configuration=production
```

**三个 bundle 各自内联词条**，只改 `locales/*.json` 而不重建对应 bundle，界面上看不到变化。

### 已知遗留

- 拼接式文案已整理成整句（「标注全部任务」「有 N 个隐藏区域」「添加筛选条件」等），
  英文用两条 key 处理单复数；仍有个别 `t(...) + 变量` 形态（如 `Task 5`），中文语序读得通，暂未动。
- 用户数据（项目名、标签名、仓库名、模板内容）不翻译，属预期行为。
- `USE_I18N=True` 会带来日期格式变化，导出 CSV 的时间格式未做回归测试。

---

## 三、品牌

- `web/apps/labelstudio/src/assets/images/logo.svg`：左侧图形换成 Moha 三色 M，**右侧文字仍是 Label Studio**。
- `label_studio/core/static/images/favicon.{ico,png}` 与 `web/{apps/labelstudio/src,libs/editor/public}/favicon.ico`：
  全部换成 Moha 标记（纯 Python 生成，无 Pillow 依赖）。
- `templates/base.html` / `templates/simple.html`：favicon 链接带 `?v=2` 绕浏览器缓存
  （favicon 缓存极顽固，换图后不带参数用户看不到变化）。
- `users/templates/users/new-ui/user_base.html`：登录/注册页左侧 30×30 图形换 Moha 标记，字标保留。
- 页面标题、侧栏底部的版本号与外链已移除（见第四节）。

---

## 四、产品裁剪

去掉与本次交付无关或属于商业版的入口，减少误导。

| 位置 | 改动 |
| --- | --- |
| 存储 provider 网格 | 只保留 `moha`（置顶）、`s3`、`redis`、`localfiles`；删除 GCS、Azure、databricks 等 |
| 创建项目的模板列表 | `TemplatesList.jsx` 过滤 `recipe.type === "enterprise"`，不再展示企业版模板 |
| 首页 | 删除右栏「资源」卡片（文档/API/发布说明/博客/Slack）与「社区版」徽标，改单列布局 |
| 侧栏 | 移除版本提示、API/Docs/GitHub/Slack 外链 |
| 设置页 | 删除工作区块（workspace）相关设置 |
| 注册页 | 删除 `how_find_us`、补充说明输入、newsletter 勾选（后端字段本就是 `required=False`） |
| 推广卡片 | `HeidiTips` 用 `SHOW_ENTERPRISE_TIPS = false` 关掉，组件保留 |
| 数据管理器 | 「Label All Tasks」等拼接文案改为整句词条 |

**保留但未生效**：设置页的「不确定性采样」带 enterprise 徽标，位于 feature flag `FF_LSDV_E_297` 之后且 `disabled`，未处理。

---

## 五、上游侵入清单（自动门禁）

上游文件只允许在 `label_studio/io_storages/moha/selfcheck.py` 的 `DIFF_BUDGET` 里登记，超预算即失败：

| 上游文件 | +/− 预算 | 用途 |
| --- | --- | --- |
| `label_studio/core/settings/label_studio.py` | 8 / 0 | 向 `GET_STORAGE_LIST` 追加 Moha |
| `label_studio/core/urls.py` | 1 / 0 | include Moha 路由 |
| `label_studio/io_storages/models.py` | 3 / 0 | 导入 Moha 模型 |
| `pyproject.toml` | 1 / 0 | `moha-hub` 依赖 |
| `web/apps/labelstudio/src/assets/images/logo.svg` | 4 / 2 | 品牌图形 |
| `…/StorageSettings/StorageSummary.jsx` | 12 / 0 | 存储摘要展示 Moha |
| `…/StorageSettings/providers/index.ts` | 5 / 13 | provider 注册表（含删除） |
| `web/libs/app-common/src/blocks/StorageProviderForm/Steps/preview-step.tsx` | 6 / 1 | 预览步骤识别 Moha |
| `web/libs/app-common/src/blocks/StorageProviderForm/types/common.ts` | 3 / 0 | 类型枚举 |
| `web/libs/ui/src/assets/icons/index.ts` | 1 / 0 | 图标导出 |

自检命令：

```bash
python label_studio/io_storages/moha/selfcheck.py            # 以当前分支基线跑
MOHA_BASE_REF=1.24.0 python label_studio/io_storages/moha/selfcheck.py   # 升级后以新 tag 为基线
```

**新增上游改动前先问自己**：能不能放进 `io_storages/moha/` 或 `web/libs/i18n/`？不能才动上游，并同步更新 `DIFF_BUDGET`。

---

## 六、安装期初始化（后端命令）

Helm Chart 安装时用它一次性建好账号、工作区、项目、标注配置与数据源。**只创建不覆盖**，
界面上改过的内容不会被 `helm upgrade` 回滚。

### `label_studio/core/management/commands/bootstrap_project.py`

| 参数 | 环境变量 | 说明 |
| --- | --- | --- |
| `--email` / `--password` | `BOOTSTRAP_USER_EMAIL` / `BOOTSTRAP_USER_PASSWORD` | 账号；密码只在新建或 `--reset-password` 时写入 |
| `--org-title` | `BOOTSTRAP_ORG_TITLE` | 工作区名称，默认 `Moha` |
| `--project-title` | `BOOTSTRAP_PROJECT_TITLE` | 项目名称；Chart 默认取实例名 |
| `--template` | `BOOTSTRAP_TEMPLATE` | 内置模板相对路径；留空走自动推断 |
| `--label-config` | `BOOTSTRAP_LABEL_CONFIG` | 单行 XML，优先于模板；写入前过 `Project.validate_label_config` |
| `--moha-endpoint` / `--token` / `--dataset` | 同名 `BOOTSTRAP_*` | 数据源；`--dataset` 支持 `组织/数据集` 形式 |
| `--moha-organization` / `--moha-repo-type` / `--moha-revision` / `--moha-prefix` | 同上 | 组织可省略（从 `dataset` 拆），仓库类型固定 `datasets` |
| `--api-token` | `BOOTSTRAP_API_TOKEN` | 固定 DRF Token 给同步 Job 用 |
| `--force-update` / `--reset-password` / `--dry-run` | — | 覆盖已有配置 / 重置密码 / 只打印不落库 |

凭据一律走环境变量，不走命令行参数——参数在 Pod spec 里是明文可见的。

### `label_studio/core/management/commands/_labeling_config.py`

读数据源第一条记录，按字段形态推断标注配置，覆盖：多轮对话、PDF、图片分类/框选、音频转写、
句对/NLI、问答对、文本分类，以及认不出时的通用界面（展示前 4 个文本字段 + 评审选项）。
字段名走同义词表（`instruction` / `prompt` / `question` / `query`…）。

**不支持的形态**：ShareGPT 的 `conversations: [{from, value}]` —— Label Studio 的 Chat 控件只认
`role`/`content`，模板层无法转换，只能报错提示。

### 踩过的坑（改这块前必看）

1. `Organization.created_by` 是 OneToOne：工作区标题变了会导致重装时 UNIQUE 冲突，代码里回退到该账号已拥有的工作区。
2. 组织默认 `JWTSettings.legacy_api_tokens_enabled=False`，DRF Token 认证直接 401，bootstrap 显式打开。
3. `Token.key` 是主键，不能 `get_or_create(defaults={'key': ...})`，只能删了重建。
4. 以脚本方式跑 `manage.py` 需要 `PYTHONPATH=/label-studio`，且要显式给 `LABEL_STUDIO_BASE_DATA_DIR`，
   否则落到只读 HOME 报 `PermissionError: /.local`。

---

## 七、变更台账

| 日期 | 提交 | 内容 |
| --- | --- | --- |
| 2026-11-03 | `c3b7d67` 等 | Moha 驱动落地：models/client/uri/serializers/api/registry、迁移、6 个测试、上游预算自检；导航 logo 换 Moha 图形 |
| 2026-11-03 | `4b809bc` | i18n 运行时 + 语言切换 + Django 页面中文 |
| 2026-11-03 | `8c42613` `51aa41d` `7745f94` | shell/设置/存储、数据管理器、标注编辑器分别中文化 |
| 2026-11-03 | `69aff55` | i18n 库 README 与覆盖率检查 |
| 2026-11-04 | `c365a81` `3c305b0` `5b6ee37` | 补齐设置/存储/模板/快捷键/账户页；删企业版入口；登录注册页换品牌 |
| 2026-11-04 | `7708f3d` | 拼接文案改整句；首页删资源卡；favicon 换 Moha |
| 2026-11-04 | `5bb3168` `c672528` | 新增 `bootstrap_project` 与镜像 workflow；修幂等与 token 认证 |
| 2026-11-04 | `ab18f15` `600ff6a` | ACR 拒绝 attestation 空层（`provenance: false`）；修存储参数重复 + 支持 `--label-config` |
| 2026-11-04 | `26673d6` `f1cbb8e` | 标注配置自动推断；数据源支持 `组织/数据集` |

---

## 八、升级到新上游版本

```bash
# 1. 取上游
git remote add upstream https://github.com/HumanSignal/label-studio.git   # 首次
git fetch upstream --tags

# 2. 建新分支并合并（不 rebase 已发布分支，不 force push）
git switch -c 1.24.0-pxs 1.24.0
git merge 1.23.2-pxs

# 3. 浅克隆必须先补历史，否则合并失败
git fetch --unshallow

# 4. 把预算基线切到新 tag 再自检
MOHA_BASE_REF=1.24.0 python label_studio/io_storages/moha/selfcheck.py
```

合并后逐项确认：

1. `DIFF_BUDGET` 里的 10 个上游文件是否还能对上（尤其 `providers/index.ts`、`preview-step.tsx`）
2. i18n 是否被上游改写冲掉：`node web/libs/i18n/scripts/check-coverage.js`
3. `label_studio/locale/zh_Hans/LC_MESSAGES/django.po` 是否需要补新条目并重新 `msgfmt`
4. 前端三个 bundle 重新构建
5. 端到端：登录 → 项目在 → 标注界面按模板渲染 → 存储指向目标仓库 → 同步出任务 → 语言切换生效

---

## 九、镜像与发布

镜像不走 GitHub Actions：本仓库是公开仓库，而组织 runner 组不允许公开仓库，自托管 runner 会一直排队；
公开 fork 又无法转 private（转换即被标记 disabled）。因此改为**在构建机上构建后推 ACR**。

- 构建机：`10.0.11.1`（`/opt/docker`，已登录 ACR）
- 镜像：`registry.cn-hangzhou.aliyuncs.com/xiaoshiai/label-studio-pxs`
- 标签：`1.23.2-pxs.<日期>`（如 `1.23.2-pxs.20261104`），另有 `1.23.2-pxs.sha-<短码>` 便于溯源
- workflow `.github/workflows/pxs-image.yml` 保留但已 `disabled`，将来若自托管 runner 可用可重新启用

镜像内容 = `label_studio/` + `deploy/` + 已构建的 `web/dist/` + `pyproject.toml`，
基于带 Python 依赖的基础镜像，启动命令 `migrate && runserver`（仅适合单实例验证；
要上多副本需改用 uwsgi/gunicorn 并接外部数据库）。

配套 Helm Chart 在 `poxiaoyun/plugins` 的 `charts/default/moha-label-studio`，其 `image.tag` 需与本处对齐。
