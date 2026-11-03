"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] HTTP layer: thin subclasses of the shared storage views.
"""

from drf_spectacular.utils import extend_schema
from io_storages.api import (
    ExportStorageDetailAPI,
    ExportStorageFormLayoutAPI,
    ExportStorageListAPI,
    ExportStorageSyncAPI,
    ExportStorageValidateAPI,
    ImportStorageDetailAPI,
    ImportStorageFormLayoutAPI,
    ImportStorageListAPI,
    ImportStorageSyncAPI,
    ImportStorageValidateAPI,
)

from .models import MohaExportStorage, MohaImportStorage
from .serializers import MohaExportStorageSerializer, MohaImportStorageSerializer

_TAG = 'Storage: Moha'


@extend_schema(tags=[_TAG], summary='List Moha import storages')
class MohaImportStorageListAPI(ImportStorageListAPI):
    queryset = MohaImportStorage.objects.all()
    serializer_class = MohaImportStorageSerializer


@extend_schema(tags=[_TAG], summary='Get, update or delete a Moha import storage')
class MohaImportStorageDetailAPI(ImportStorageDetailAPI):
    queryset = MohaImportStorage.objects.all()
    serializer_class = MohaImportStorageSerializer


@extend_schema(tags=[_TAG], summary='Sync a Moha import storage')
class MohaImportStorageSyncAPI(ImportStorageSyncAPI):
    serializer_class = MohaImportStorageSerializer


@extend_schema(tags=[_TAG], summary='Validate a Moha import storage connection')
class MohaImportStorageValidateAPI(ImportStorageValidateAPI):
    serializer_class = MohaImportStorageSerializer


class MohaImportStorageFormLayoutAPI(ImportStorageFormLayoutAPI):
    pass


@extend_schema(tags=[_TAG], summary='List Moha export storages')
class MohaExportStorageListAPI(ExportStorageListAPI):
    queryset = MohaExportStorage.objects.all()
    serializer_class = MohaExportStorageSerializer


@extend_schema(tags=[_TAG], summary='Get, update or delete a Moha export storage')
class MohaExportStorageDetailAPI(ExportStorageDetailAPI):
    queryset = MohaExportStorage.objects.all()
    serializer_class = MohaExportStorageSerializer


@extend_schema(tags=[_TAG], summary='Sync a Moha export storage')
class MohaExportStorageSyncAPI(ExportStorageSyncAPI):
    serializer_class = MohaExportStorageSerializer


@extend_schema(tags=[_TAG], summary='Validate a Moha export storage connection')
class MohaExportStorageValidateAPI(ExportStorageValidateAPI):
    serializer_class = MohaExportStorageSerializer


class MohaExportStorageFormLayoutAPI(ExportStorageFormLayoutAPI):
    pass
