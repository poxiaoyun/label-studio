"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] Upstream contract guard.

These assertions turn a silently broken rebase into a failing test: if upstream
renames a hook, moves a route include or starts requiring a new abstract method,
the driver's assumptions are reported immediately.
"""

from io_storages.base_models import ExportStorage, ImportStorage
from io_storages.moha.models import MohaExportStorage, MohaImportStorageBase
from io_storages.moha.selfcheck import run_checks

EXPECTED_IMPORT_METHODS = {'iter_objects', 'iter_keys', 'get_unified_metadata', 'get_data', 'scan_and_create_links'}
EXPECTED_EXPORT_METHODS = {'save_annotation', 'save_annotations', 'delete_annotation'}


def test_selfcheck_passes():
    assert run_checks() == []


def test_import_storage_contract_is_implemented():
    assert issubclass(MohaImportStorageBase, ImportStorage)
    assert not getattr(MohaImportStorageBase, '__abstractmethods__', frozenset())
    for method in EXPECTED_IMPORT_METHODS:
        assert callable(getattr(MohaImportStorageBase, method, None)), method


def test_export_storage_contract_is_implemented():
    assert issubclass(MohaExportStorage, ExportStorage)
    assert not getattr(MohaExportStorage, '__abstractmethods__', frozenset())
    for method in EXPECTED_EXPORT_METHODS:
        assert callable(getattr(MohaExportStorage, method, None)), method


def test_proxy_requires_presign_attribute():
    # io_storages.proxy_api rejects storages without this attribute (404).
    field_names = {field.name for field in MohaImportStorageBase._meta.get_fields()}
    assert 'presign' in field_names
