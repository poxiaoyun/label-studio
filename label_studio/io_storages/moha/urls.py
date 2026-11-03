"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] URLs for the Moha storage driver.

The full ``api/storages/`` prefix is declared here so upstream
``io_storages/urls.py`` does not need a patch; ``core/urls.py`` only adds a single
include line. Names live in their own ``moha`` namespace to avoid clashing with
the upstream ``api`` namespace.
"""

from django.urls import include, path
from io_storages.api import ImportStorageListFilesAPI

from .api import (
    MohaExportStorageDetailAPI,
    MohaExportStorageFormLayoutAPI,
    MohaExportStorageListAPI,
    MohaExportStorageSyncAPI,
    MohaExportStorageValidateAPI,
    MohaImportStorageDetailAPI,
    MohaImportStorageFormLayoutAPI,
    MohaImportStorageListAPI,
    MohaImportStorageSyncAPI,
    MohaImportStorageValidateAPI,
)
from .serializers import MohaImportStorageSerializer

_moha_patterns = [
    path('moha/', MohaImportStorageListAPI.as_view(), name='storage-moha-list'),
    path('moha/<int:pk>', MohaImportStorageDetailAPI.as_view(), name='storage-moha-detail'),
    path('moha/<int:pk>/sync', MohaImportStorageSyncAPI.as_view(), name='storage-moha-sync'),
    path('moha/validate', MohaImportStorageValidateAPI.as_view(), name='storage-moha-validate'),
    path('moha/form', MohaImportStorageFormLayoutAPI.as_view(), name='storage-moha-form'),
    path(
        'moha/files',
        ImportStorageListFilesAPI().as_view(serializer_class=MohaImportStorageSerializer),
        name='storage-moha-list-files',
    ),
    path('export/moha', MohaExportStorageListAPI.as_view(), name='export-storage-moha-list'),
    path('export/moha/<int:pk>', MohaExportStorageDetailAPI.as_view(), name='export-storage-moha-detail'),
    path('export/moha/<int:pk>/sync', MohaExportStorageSyncAPI.as_view(), name='export-storage-moha-sync'),
    path('export/moha/validate', MohaExportStorageValidateAPI.as_view(), name='export-storage-moha-validate'),
    path('export/moha/form', MohaExportStorageFormLayoutAPI.as_view(), name='export-storage-moha-form'),
]

urlpatterns = [
    path('api/storages/', include((_moha_patterns, 'api'), namespace='moha')),
]
