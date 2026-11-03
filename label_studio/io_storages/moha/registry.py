"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] Storage registry entry.

``settings.GET_STORAGE_LIST`` points here (see ``core/settings/label_studio.py``)
instead of patching ``io_storages.functions``. The upstream list is kept as the
source of truth and the Moha entry is appended, so new upstream drivers show up
automatically after merging onto a newer release.
"""

from .api import MohaExportStorageListAPI, MohaImportStorageListAPI

MOHA_STORAGE_ENTRY = {
    'name': 'moha',
    'title': 'Moha',
    'import_list_api': MohaImportStorageListAPI,
    'export_list_api': MohaExportStorageListAPI,
}


def get_storage_list():
    """Return the upstream storage list plus the Moha driver."""
    from io_storages.functions import get_storage_list as _upstream_get_storage_list

    return [*_upstream_get_storage_list(), MOHA_STORAGE_ENTRY]
