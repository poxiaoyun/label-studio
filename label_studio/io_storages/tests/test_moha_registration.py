"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] Registration surface: the driver must be visible to the API, the model
discovery helpers and the data manager without patching upstream modules.
"""

from core.utils.common import load_func
from django.conf import settings
from django.urls import reverse
from io_storages.functions import get_storage_list as upstream_get_storage_list
from io_storages.models import get_storage_classes
from io_storages.moha.models import MohaExportStorage, MohaImportStorage


def test_settings_registry_contains_moha_and_keeps_upstream_entries():
    entries = load_func(settings.GET_STORAGE_LIST)()
    names = [entry['name'] for entry in entries]
    assert 'moha' in names
    for upstream in ('s3', 'gcs', 'azure', 'redis'):
        assert upstream in names
    moha = next(entry for entry in entries if entry['name'] == 'moha')
    assert moha['title'] == 'Moha'
    assert moha['import_list_api'] and moha['export_list_api']


def test_upstream_functions_are_left_untouched():
    # The Moha entry must come from settings, not from a patched upstream list.
    assert 'moha' not in [entry['name'] for entry in upstream_get_storage_list()]


def test_storage_classes_are_discovered():
    assert MohaImportStorage in get_storage_classes('import')
    assert MohaExportStorage in get_storage_classes('export')


def test_import_link_name_registered():
    assert 'io_storages_mohaimportstoragelink' in settings.IO_STORAGES_IMPORT_LINK_NAMES


def test_urls_reverse():
    assert reverse('moha:storage-moha-list') == '/api/storages/moha/'
    assert reverse('moha:storage-moha-validate') == '/api/storages/moha/validate'
    assert reverse('moha:storage-moha-list-files') == '/api/storages/moha/files'
    assert reverse('moha:export-storage-moha-list') == '/api/storages/export/moha'
    assert reverse('moha:export-storage-moha-sync', kwargs={'pk': 1}) == '/api/storages/export/moha/1/sync'


def test_storage_types_endpoint_payload():
    # Mirrors what AllImportStorageTypesAPI returns.
    entries = load_func(settings.GET_STORAGE_LIST)()
    payload = [{'name': entry['name'], 'title': entry['title']} for entry in entries]
    assert {'name': 'moha', 'title': 'Moha'} in payload
