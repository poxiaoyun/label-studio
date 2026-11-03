"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] Upstream-integration self check.

Runs without Django and without the SDK so it can be used right after a rebase:

    python label_studio/io_storages/moha/selfcheck.py

It verifies that every upstream anchor the driver relies on still exists and that
the "no invasive edits" budget (see README.md) is respected. When the checkout has
git metadata the diff against ``BASE_REF`` is measured as well; without git that
single check is skipped so the driver still self-checks inside build containers.
``pytest`` runs the same checks in ``test_moha_integration_anchors.py``.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

MARKER = '[moha]'

# Files we are allowed to touch (all edits must carry MARKER).
ALLOWED_UPSTREAM_EDITS = (
    'label_studio/core/settings/label_studio.py',
    'label_studio/core/urls.py',
    'label_studio/io_storages/models.py',
)

#: Frontend counterpart of ``ALLOWED_UPSTREAM_EDITS``.
ALLOWED_FRONTEND_EDITS = (
    'web/apps/labelstudio/src/pages/Settings/StorageSettings/providers/index.ts',
    'web/apps/labelstudio/src/pages/Settings/StorageSettings/StorageSummary.jsx',
    'web/libs/app-common/src/blocks/StorageProviderForm/Steps/preview-step.tsx',
    'web/libs/app-common/src/blocks/StorageProviderForm/types/common.ts',
    'web/libs/ui/src/assets/icons/index.ts',
    'web/apps/labelstudio/src/assets/images/logo.svg',
)

#: Per-file diff budget against the imported upstream ref: ``(added, deleted)``.
#:
#: Deletions are only budgeted where the fork deliberately replaces upstream
#: content: the provider grid (product decision to drop unused providers) and the
#: brand glyph inside ``logo.svg``. Everything else is additive.
DIFF_BUDGET = {
    'label_studio/core/settings/label_studio.py': (8, 0),
    'label_studio/core/urls.py': (1, 0),
    'label_studio/io_storages/models.py': (3, 0),
    'pyproject.toml': (1, 0),
    'web/apps/labelstudio/src/assets/images/logo.svg': (4, 2),
    'web/apps/labelstudio/src/pages/Settings/StorageSettings/StorageSummary.jsx': (12, 0),
    'web/apps/labelstudio/src/pages/Settings/StorageSettings/providers/index.ts': (5, 13),
    'web/libs/app-common/src/blocks/StorageProviderForm/Steps/preview-step.tsx': (6, 1),
    'web/libs/app-common/src/blocks/StorageProviderForm/types/common.ts': (3, 0),
    'web/libs/ui/src/assets/icons/index.ts': (1, 0),
}

#: Upstream ref the budget is measured against (the release we forked from).
BASE_REF = '1.23.2'

# Files that must stay untouched. A marker in any of them means the driver has
# started to patch upstream internals, which makes rebases expensive.
FORBIDDEN_UPSTREAM_EDITS = (
    'label_studio/io_storages/base_models.py',
    'label_studio/io_storages/api.py',
    'label_studio/io_storages/proxy_api.py',
    'label_studio/io_storages/serializers.py',
    'label_studio/io_storages/functions.py',
    'label_studio/io_storages/all_api.py',
    'label_studio/io_storages/urls.py',
    'label_studio/core/settings/base.py',
    'web/libs/app-common/src/blocks/StorageProviderForm/components/provider-form.tsx',
    'web/libs/app-common/src/blocks/StorageProviderForm/index.tsx',
    'web/libs/app-common/src/blocks/StorageProviderForm/hooks/useStorageApi.ts',
)

# (path, needle, description)
ANCHORS = (
    (
        'label_studio/core/settings/base.py',
        "GET_STORAGE_LIST = 'io_storages.functions.get_storage_list'",
        'default GET_STORAGE_LIST setting',
    ),
    (
        'label_studio/core/settings/base.py',
        'IO_STORAGES_IMPORT_LINK_NAMES = [',
        'import link name list',
    ),
    (
        'label_studio/core/settings/label_studio.py',
        "GET_STORAGE_LIST = 'io_storages.moha.registry.get_storage_list'",
        'moha settings override',
    ),
    (
        'label_studio/core/urls.py',
        "include('io_storages.moha.urls')",
        'moha URL include',
    ),
    (
        'label_studio/io_storages/models.py',
        'from .moha import models',
        'model registration import',
    ),
    (
        'label_studio/io_storages/base_models.py',
        'def iter_keys(self)',
        'ImportStorage.iter_keys',
    ),
    (
        'label_studio/io_storages/base_models.py',
        'def get_data(self, key)',
        'ImportStorage.get_data',
    ),
    (
        'label_studio/io_storages/base_models.py',
        'def get_bytes_stream(self, uri)',
        'ImportStorage.get_bytes_stream',
    ),
    (
        'label_studio/io_storages/base_models.py',
        'def save_annotation(self, annotation)',
        'ExportStorage.save_annotation',
    ),
    (
        'label_studio/io_storages/proxy_api.py',
        'storage.get_bytes_stream(uri, range_header=range_header)',
        'proxy stream call signature',
    ),
    (
        'label_studio/io_storages/api.py',
        'class ImportStorageListAPI(generics.ListCreateAPIView)',
        'shared import list API',
    ),
    (
        'label_studio/io_storages/api.py',
        'class ExportStorageSyncAPI(generics.GenericAPIView)',
        'shared export sync API',
    ),
    (
        'web/libs/app-common/src/blocks/StorageProviderForm/providers.ts',
        'export function getProviderConfig',
        'frontend provider registry accessor',
    ),
    (
        'web/libs/app-common/src/blocks/StorageProviderForm/types/common.ts',
        'export interface ProviderConfig',
        'ProviderConfig type',
    ),
    (
        'web/apps/labelstudio/src/pages/Settings/StorageSettings/providers/index.ts',
        'export const providers = {',
        'frontend provider map',
    ),
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read(root: Path, relative: str) -> str:
    path = root / relative
    if not path.exists():
        raise FileNotFoundError(relative)
    return path.read_text(encoding='utf-8')


def check_anchors(root: Path) -> List[str]:
    failures = []
    for relative, needle, description in ANCHORS:
        try:
            body = _read(root, relative)
        except FileNotFoundError:
            failures.append(f'anchor missing: {description} ({relative} does not exist)')
            continue
        if needle not in body:
            failures.append(f'anchor missing: {description} ({relative}: {needle!r})')
    return failures


def check_edit_budget(root: Path) -> List[str]:
    failures = []
    for relative in FORBIDDEN_UPSTREAM_EDITS:
        try:
            body = _read(root, relative)
        except FileNotFoundError:
            failures.append(f'guarded file missing: {relative}')
            continue
        if MARKER in body:
            failures.append(f'{relative} must not be patched ({MARKER} found)')
    for relative in (*ALLOWED_UPSTREAM_EDITS, *ALLOWED_FRONTEND_EDITS):
        try:
            body = _read(root, relative)
        except FileNotFoundError:
            failures.append(f'allowed edit file missing: {relative}')
            continue
        if MARKER not in body:
            failures.append(f'{relative} lost its {MARKER} marker')
    return failures


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.DEVNULL)


def check_diff_budget(root: Path) -> List[str]:
    """Measure the fork against BASE_REF.

    Skipped when the checkout has no git metadata (e.g. the driver copied into a
    build container) or when the base ref is not fetched.
    """
    if not (root / '.git').exists():
        return []
    try:
        _git(root, 'rev-parse', '--verify', '--quiet', BASE_REF)
        tracked = set(_git(root, 'ls-tree', '-r', '--name-only', BASE_REF).splitlines())
        changed = _git(root, 'diff', '--name-status', BASE_REF, '--').splitlines()
    except (subprocess.CalledProcessError, OSError):
        return []

    failures = []
    for line in changed:
        parts = line.split('\t')
        path = parts[-1]
        if path in tracked and path not in DIFF_BUDGET:
            failures.append(f'{path} is an upstream file outside the diff budget')

    budgeted = sorted(DIFF_BUDGET)
    numstat = _git(root, 'diff', '--numstat', BASE_REF, '--', *budgeted)
    for line in numstat.splitlines():
        added, deleted, path = line.split('\t')
        if added == '-' or deleted == '-':
            continue
        max_added, max_deleted = DIFF_BUDGET[path]
        if int(added) > max_added or int(deleted) > max_deleted:
            failures.append(
                f'{path} exceeds its diff budget: +{added}/-{deleted} (allowed +{max_added}/-{max_deleted})'
            )
    return failures


def _python_sources(root: Path) -> Iterable[Path]:
    yield from (root / 'label_studio').rglob('*.py')


#: This file names the SDK/flag strings on purpose; skip it in the text scans.
_SCAN_EXEMPT = {'selfcheck.py'}


def check_sdk_boundary(root: Path) -> List[str]:
    failures = []
    for path in _python_sources(root):
        if '__pycache__' in path.parts or path.name in _SCAN_EXEMPT:
            continue
        if 'tests' in path.parts:
            # Tests may talk to the SDK directly (the e2e test does on purpose).
            continue
        body = path.read_text(encoding='utf-8', errors='ignore')
        if 'xiaoshiai_hub' in body and path.name != 'client.py':
            failures.append(
                f'{path.relative_to(root)} imports xiaoshiai_hub; only io_storages/moha/client.py may do that'
            )
    return failures


def check_no_feature_flags(root: Path) -> List[str]:
    failures = []
    driver = root / 'label_studio/io_storages/moha'
    for path in driver.rglob('*.py'):
        if '__pycache__' in path.parts or path.name in _SCAN_EXEMPT:
            continue
        body = path.read_text(encoding='utf-8', errors='ignore')
        if re.search(r"flag_set\(\s*'fflag", body) or 'feature_flags' in body:
            failures.append(f'{path.relative_to(root)} must not depend on internal feature flags')
    return failures


def check_frontend_registration(root: Path) -> List[str]:
    failures = []
    providers_map = _read(root, 'web/apps/labelstudio/src/pages/Settings/StorageSettings/providers/index.ts')
    if 'moha' not in providers_map:
        failures.append('frontend provider map does not register "moha"')
    icons = _read(root, 'web/libs/ui/src/assets/icons/index.ts')
    if 'IconCloudProviderMoha' not in icons:
        failures.append('icon index does not export IconCloudProviderMoha')
    for relative in (
        'web/apps/labelstudio/src/pages/Settings/StorageSettings/providers/moha.tsx',
        'web/libs/ui/src/assets/icons/cloud-provider-moha.svg',
        'label_studio/io_storages/moha/README.md',
    ):
        if not (root / relative).exists():
            failures.append(f'missing file: {relative}')
    return failures


CHECKS = (
    check_anchors,
    check_edit_budget,
    check_diff_budget,
    check_sdk_boundary,
    check_no_feature_flags,
    check_frontend_registration,
)


def run_checks(root: Path = None) -> List[str]:
    root = root or repo_root()
    failures: List[str] = []
    for check in CHECKS:
        failures.extend(check(root))
    return failures


def main() -> int:
    root = repo_root()
    failures = run_checks(root)
    if not (root / '.git').exists():
        print('[moha] note: no git metadata here, diff budget check skipped')
    if failures:
        print(f'[moha] integration self check FAILED ({len(failures)} issue(s)):')
        for item in failures:
            print(f'  - {item}')
        return 1
    print('[moha] integration self check OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
