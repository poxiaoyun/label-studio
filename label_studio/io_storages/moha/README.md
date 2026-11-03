# Moha storage driver

[Moha](https://github.com/poxiaoyun/moha) (魔哈) repository storage for Label Studio:
import datasets/models as labeling tasks, and write annotations back as repository commits.

Baseline: `HumanSignal/label-studio` **1.23.2** (`df96d79`).

---

## 1. Layout

| File | Responsibility |
| --- | --- |
| `models.py` | Django models, links, annotation signals, `validate_connection()` |
| `client.py` | **The only module importing `xiaoshiai_hub`**. Streaming, listing, uploads, branch creation |
| `uri.py` | `moha://` addressing, prefix scoping, traversal guards (pure functions) |
| `errors.py` | SDK/HTTP exception → user-facing message (pure functions) |
| `serializers.py` | Field validation, SSRF/allowlist, token redaction |
| `api.py` | Thin views subclassing `io_storages/api.py` |
| `registry.py` | `settings.GET_STORAGE_LIST` entry |
| `urls.py` | `/api/storages/moha/...` and `/api/storages/export/moha/...` |
| `form_layout.yml` | Legacy form (when the new storage UI flag is off) |
| `selfcheck.py` | Anchor / boundary checks, runnable without Django |

Frontend:

| File | Responsibility |
| --- | --- |
| `web/apps/.../StorageSettings/providers/moha.tsx` | `ProviderConfig` (fields, layout, `prefixLabel`) |
| `web/libs/ui/src/assets/icons/cloud-provider-moha.svg` | Provider icon |

## 2. Upstream touch points

Only **9 files** are modified, **+56 / −4 lines**, every line tagged `[moha]`.
The only removed lines are the 4 hardcoded prefix-label lines in `preview-step.tsx`
that `prefixLabel` replaces.

| File | Change |
| --- | --- |
| `core/settings/label_studio.py` | `GET_STORAGE_LIST` override, link name append, `MOHA_*` settings |
| `core/urls.py` | one `include('io_storages.moha.urls')` |
| `io_storages/models.py` | one import so Django registers the models early |
| `pyproject.toml` | `moha-hub` dependency |
| `web/.../providers/index.ts` | register `moha` |
| `web/libs/ui/src/assets/icons/index.ts` | export `IconCloudProviderMoha` |
| `web/.../types/common.ts` | optional `prefixLabel` on `ProviderConfig` |
| `web/.../Steps/preview-step.tsx` | use `prefixLabel` instead of a hardcoded label |
| `web/.../StorageSummary.jsx` | `SummaryMoha` row |

Deliberately **not** touched: `io_storages/base_models.py`, `api.py`,
`proxy_api.py`, `functions.py`, `serializers.py`, `all_api.py`, `urls.py`,
`core/settings/base.py`, and the `StorageProviderForm` engine
(`index.tsx`, `hooks/`, `components/provider-form.tsx`).

`python label_studio/io_storages/moha/selfcheck.py` enforces all of the above.

## 3. Configuration

| Field | Import | Export | Notes |
| --- | --- | --- | --- |
| `moha_endpoint` | ✓ | ✓ | e.g. `https://rune.example.com`, no `/moha` suffix |
| `moha_token` | ✓ | ✓ | Bearer token, never returned by the API |
| `organization` | ✓ | ✓ | |
| `repo_type` | ✓ | ✓ | `datasets` (default) or `models` |
| `repo_name` | ✓ | ✓ | |
| `revision` | ✓ | ✓ | branch/tag/commit; empty = default branch |
| `prefix` | ✓ | ✓ | directory inside the repository |
| `regex_filter` | ✓ | — | `re.match` on the full path |
| `use_blob_urls` | ✓ | — | Files vs Tasks import |
| `recursive_scan` | ✓ | — | walk sub-directories |
| `presign` | ✓ | — | always `False`; required by the proxy API |
| `can_delete_objects` | — | ✓ | enables `delete_annotation()` |

Server settings:

| Setting | Default | Purpose |
| --- | --- | --- |
| `MOHA_ENDPOINT_ALLOWLIST` | empty | comma-separated host suffixes allowed to bypass SSRF private-IP blocking (internal deployments) |
| `MOHA_REQUEST_TIMEOUT` | `30` | metadata/listing timeout (s) |
| `MOHA_STREAM_CONNECT_TIMEOUT` | `10` | proxy stream connect timeout (s) |

## 4. How reads work

```
task.data = moha://org/datasets/repo/main/images/1.jpg
   → /tasks/{id}/resolve/?fileuri=…       (Label Studio proxy)
   → can_resolve_url()                    (scheme + repo + revision + prefix scope)
   → client.open_stream()                 (GET …/resolve/{rev}/{path}, Range forwarded)
   → 302 to object storage                (206 for Range) or 200 with local trimming
```

`presign` stays `False`, so nothing is ever exposed to the browser directly.

## 5. How writes work

* Realtime: `Annotation` post_save → `save_annotation()` → one commit per annotation.
* Bulk: **Sync Storage** → `save_annotations()` → batches of `bulk_commit_size`
  (500) files → one commit per batch via `upload_folder`.
* Deletion: only when `can_delete_objects=True` (annotation `pre_delete`).

## 6. Upgrading Label Studio

> **Dependency lock**: `moha-hub[upload]` is declared in `pyproject.toml`, but the
> upstream `poetry.lock` is intentionally left untouched (regenerating it would
> churn hundreds of unrelated entries and make rebases noisy). Run
> `poetry lock` once in the build environment before `poetry install` /
> `docker build`; plain `pip install -e .` already resolves the SDK.

```bash
git remote add upstream https://github.com/HumanSignal/label-studio.git  # once
git fetch upstream --tags
git switch feat/moha-storage-provider
git rebase upstream/<new-version>

python label_studio/io_storages/moha/selfcheck.py   # anchors + boundaries
pytest label_studio/io_storages/tests/test_moha_*.py -q

# migration number collision: rename 0023_* to the next free number and update
# its dependencies; never edit 0001-0022.
```

Conflicts can only appear in the 9 files above, and every one of them is a single
appended line: keep both sides.

Run from the repository root with Label Studio's test environment
(`DJANGO_SETTINGS_MODULE=core.settings.label_studio`).

## 7. Known limitations

| # | Limitation | Impact | Where to fix |
| --- | --- | --- | --- |
| R1 | `moha-sdk` `get_repository_content` has no `page/limit` | a directory with more entries than the server page size may be truncated; a warning is logged and `meta.truncated_dirs` is populated | `client.list_files()` once the SDK exposes paging |
| R2 | Moha `/resolve` ignores `Range` for git-backed files | those files are trimmed locally (correct but not efficient); object-storage backed files use the 302 + 206 path | `client.open_stream()` |
| R3 | Realtime export creates one commit per annotation | verbose repository history; use bulk Sync for large backfills | `models.save_annotation()` |
| R4 | `images` / `spaces` repositories are out of scope | Moha serves them from dedicated endpoints | `uri.REPO_TYPES` + client |
| R5 | Token is stored like other storage credentials (DB plaintext) | same posture as S3 | future KMS field |

## 8. Tests

| File | Scope |
| --- | --- |
| `tests/test_moha_uri.py` | URI build/parse, traversal, prefix scoping |
| `tests/test_moha_client.py` | listing, Range handling, error mapping (fake hub, no network) |
| `tests/test_moha_storage.py` | Django models/serializer/export batching |
| `tests/test_moha_registration.py` | storage list, link names, URL reversing |
| `tests/test_moha_fake_server.py` | end-to-end with the **real SDK** against a local stub server (wire contract, Range, upload payloads) |
| `tests/test_moha_integration_anchors.py` | upstream anchors + edit budget (`selfcheck.run_checks`) |
