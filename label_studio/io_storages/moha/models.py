"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] Moha cloud storage driver for Label Studio.

Layout mirrors the upstream drivers (``s3``, ``gcs``, ``azure_blob``): a shared
mixin holding the credential/repository fields, an import base used by the
project-scoped source storage, an export storage, and the two link models.

All SDK and HTTP details live in :mod:`io_storages.moha.client`; this module only
orchestrates Label Studio's storage lifecycle.
"""

import json
import logging
import re
from typing import Iterator, List, Optional

from core.redis import start_job_async_or_sync
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from io_storages.base_models import (
    ExportStorage,
    ExportStorageLink,
    ImportStorage,
    ImportStorageLink,
    ProjectStorageMixin,
)
from io_storages.utils import StorageObject, load_tasks_json
from rest_framework.exceptions import ValidationError
from tasks.models import Annotation

from .client import MohaClient, MohaConfig, MohaObject
from .errors import describe
from .uri import REPO_TYPES, build_uri, in_scope, parse_uri

logger = logging.getLogger(__name__)

#: Repositories usually contain README/metadata next to the data. In "Tasks" mode
#: only these extensions can produce tasks; anything else is skipped instead of
#: aborting the whole sync (upstream raises ``UnsupportedFileFormatError``).
_TASK_FILE_SUFFIXES = ('.json', '.jsonl', '.parquet')


class MohaStorageMixin(models.Model):
    """Fields and connection helpers shared by source and target storages."""

    moha_endpoint = models.TextField(
        _('moha_endpoint'),
        null=True,
        blank=True,
        help_text='Moha endpoint URL, e.g. https://rune.example.com (without /moha)',
    )
    moha_token = models.TextField(
        _('moha_token'),
        null=True,
        blank=True,
        help_text='Moha access token (sent as a Bearer token)',
    )
    organization = models.TextField(_('organization'), null=True, blank=True, help_text='Moha organization name')
    repo_type = models.TextField(
        _('repo_type'),
        choices=[(value, value.capitalize()) for value in REPO_TYPES],
        default=REPO_TYPES[0],
        help_text='Moha repository type',
    )
    repo_name = models.TextField(_('repo_name'), null=True, blank=True, help_text='Moha repository name')
    revision = models.TextField(
        _('revision'),
        null=True,
        blank=True,
        help_text='Branch, tag or commit; empty means the repository default branch',
    )
    prefix = models.TextField(
        _('prefix'),
        null=True,
        blank=True,
        help_text='Directory inside the repository (empty for the repository root)',
    )

    class Meta:
        abstract = True

    # ------------------------------------------------------------- connection

    @property
    def moha_client(self) -> MohaClient:
        if not hasattr(self, '_moha_client'):
            self._moha_client = MohaClient(
                MohaConfig(
                    endpoint=(self.moha_endpoint or '').rstrip('/'),
                    token=self.moha_token or '',
                    organization=self.organization or '',
                    repo_type=self.repo_type or REPO_TYPES[0],
                    repo_name=self.repo_name or '',
                    revision=self.revision or '',
                    request_timeout=getattr(settings, 'MOHA_REQUEST_TIMEOUT', 30.0),
                    connect_timeout=getattr(settings, 'MOHA_STREAM_CONNECT_TIMEOUT', 10.0),
                )
            )
        return self._moha_client

    def resolved_revision(self) -> str:
        """Configured revision, or the repository default branch (cached per instance)."""
        if self.revision:
            return self.revision
        if not hasattr(self, '_resolved_revision'):
            self._resolved_revision = self.moha_client.resolve_revision()
        return self._resolved_revision

    def build_uri(self, path: str) -> str:
        return build_uri(
            organization=self.organization or '',
            repo_type=self.repo_type or REPO_TYPES[0],
            repo_name=self.repo_name or '',
            revision=self.resolved_revision(),
            path=path,
        )

    def _describe(self, exc: BaseException) -> str:
        return describe(exc)


class MohaImportStorageBase(MohaStorageMixin, ImportStorage):
    url_scheme = 'moha'

    #: Required by ``io_storages.proxy_api``: a storage without this attribute is
    #: rejected with 404. Moha has no browser-facing presigned URL, so it is always
    #: False and every read is proxied through Label Studio.
    presign = models.BooleanField(_('presign'), default=False, help_text='Generate presigned URLs')
    recursive_scan = models.BooleanField(
        _('recursive scan'),
        default=False,
        help_text=_('Perform recursive scan over the repository content'),
    )
    regex_filter = models.TextField(
        _('regex_filter'),
        null=True,
        blank=True,
        help_text='Cloud storage regex for filtering objects',
    )
    use_blob_urls = models.BooleanField(
        _('use_blob_urls'),
        default=False,
        help_text='Interpret objects as BLOBs and generate URLs',
    )

    class Meta:
        abstract = True

    # --------------------------------------------------------------- listing

    def iter_objects(self) -> Iterator[MohaObject]:
        regex = re.compile(str(self.regex_filter)) if self.regex_filter else None
        skipped = 0
        for obj in self.moha_client.list_files(
            prefix=self.prefix or '',
            recursive=bool(self.recursive_scan),
            regex=regex,
            revision=self.resolved_revision(),
        ):
            if not self.use_blob_urls and not obj.path.lower().endswith(_TASK_FILE_SUFFIXES):
                skipped += 1
                continue
            yield obj
        if skipped:
            logger.info(
                '[moha] skipped %s non-task file(s); enable "Files" import method to import them as blobs',
                skipped,
            )

    def iter_keys(self) -> Iterator[str]:
        for obj in self.iter_objects():
            yield obj.path

    def get_unified_metadata(self, obj: MohaObject) -> dict:
        return {'key': obj.path, 'last_modified': obj.modified, 'size': obj.size}

    def get_data(self, key) -> List[StorageObject]:
        if self.use_blob_urls:
            return [
                StorageObject(
                    key=key,
                    task_data={settings.DATA_UNDEFINED_NAME: self.build_uri(key)},
                )
            ]
        blob = self.moha_client.read_bytes(key, revision=self.resolved_revision())
        return list(load_tasks_json(blob, key))

    # ---------------------------------------------------------------- proxy

    def can_resolve_url(self, url) -> bool:
        if not isinstance(url, str) or self.url_scheme not in url:
            return False
        try:
            parsed = parse_uri(url)
        except ValueError:
            return False
        return in_scope(
            parsed,
            organization=self.organization or '',
            repo_type=self.repo_type or REPO_TYPES[0],
            repo_name=self.repo_name or '',
            revision=self.revision or None,
            prefix=self.prefix or '',
        )

    def generate_http_url(self, url):
        # No browser-facing presigned URL exists; resolution always goes through
        # the Label Studio proxy (``presign`` stays False).
        return None

    def get_bytes_stream(self, uri, range_header=None):
        parsed = parse_uri(uri)
        if not self.can_resolve_url(uri):
            logger.warning('[moha] refusing to stream out-of-scope URI for storage %s', self.pk)
            return None, None, {}
        return self.moha_client.open_stream(
            parsed.path,
            revision=parsed.revision,
            range_header=range_header,
        )

    # ------------------------------------------------------------ validation

    def validate_connection(self, client: Optional[MohaClient] = None):
        adapter = client or self.moha_client
        try:
            adapter.get_repository()
            revision = self.resolved_revision()
            if not adapter.ref_exists(revision):
                # ``revision`` may be a tag or a commit; refs only list branches/tags.
                try:
                    adapter.get_content('', revision=revision)
                except Exception as exc:
                    raise ValidationError(
                        f'Revision "{revision}" was not found in {self.organization}/{self.repo_name}.'
                    ) from exc
            # Walk one level (or the configured depth) and require at least one file.
            first = next(
                iter(
                    adapter.list_files(
                        prefix=self.prefix or '',
                        recursive=bool(self.recursive_scan),
                        regex=re.compile(str(self.regex_filter)) if self.regex_filter else None,
                        revision=revision,
                        limit=1,
                    )
                ),
                None,
            )
            if first is None:
                raise ValidationError(
                    'No files found under the configured prefix. '
                    'Check the path, the file name filter and the token permissions.'
                )
        except ValidationError:
            raise
        except Exception as exc:
            logger.info('[moha] connection validation failed: %s', type(exc).__name__)
            raise ValidationError(self._describe(exc)) from exc

    def scan_and_create_links(self):
        return self._scan_and_create_links(MohaImportStorageLink)


class MohaImportStorage(ProjectStorageMixin, MohaImportStorageBase):
    class Meta:
        abstract = False


class MohaExportStorage(MohaStorageMixin, ExportStorage):
    #: Number of annotations serialized per commit when running a bulk sync.
    bulk_commit_size = 500

    class Meta:
        abstract = False

    # ------------------------------------------------------------- validation

    def validate_connection(self, client: Optional[MohaClient] = None):
        adapter = client or self.moha_client
        try:
            adapter.get_repository()
            if not self.revision:
                return  # default branch always exists
            if not adapter.ref_exists(self.revision):
                # Target storages may point at a branch that does not exist yet.
                # Creating it from the default branch keeps "add target storage"
                # working on a fresh repository; the repository itself is never
                # created implicitly.
                adapter.ensure_branch(self.revision)
        except ValidationError:
            raise
        except Exception as exc:
            logger.info('[moha] target validation failed: %s', type(exc).__name__)
            raise ValidationError(self._describe(exc)) from exc

    # ---------------------------------------------------------------- export

    def _object_path(self, key: str) -> str:
        prefix = (self.prefix or '').strip('/')
        return f'{prefix}/{key}' if prefix else key

    def save_annotation(self, annotation):
        payload = self._get_serialized_data(annotation)
        key = MohaExportStorageLink.get_key(annotation)
        self.moha_client.put_file(
            path=self._object_path(key),
            data=json.dumps(payload).encode('utf-8'),
            message=f'label-studio: annotation {annotation.id}',
            revision=self.resolved_revision(),
        )
        MohaExportStorageLink.create(annotation, self)

    def save_annotations(self, annotations):
        """Bulk export in bounded batches so each batch is a single commit."""
        self.info_set_in_progress()
        self.cached_user = self.project.organization.created_by

        exported = 0
        batch_files = {}
        batch_annotations = []
        total = annotations.count() if hasattr(annotations, 'count') else None

        for annotation in annotations.iterator(chunk_size=200):
            annotation.cached_user = self.cached_user
            key = MohaExportStorageLink.get_key(annotation)
            batch_files[self._object_path(key)] = json.dumps(
                self._get_serialized_data(annotation)
            ).encode('utf-8')
            batch_annotations.append(annotation)

            if len(batch_files) >= self.bulk_commit_size:
                self._flush_batch(batch_files, batch_annotations, exported)
                exported += len(batch_annotations)
                batch_files, batch_annotations = {}, []
                self.info_update_progress(last_sync_count=exported, total_annotations=total)

        if batch_files:
            self._flush_batch(batch_files, batch_annotations, exported)
            exported += len(batch_annotations)

        self.info_set_completed(last_sync_count=exported, total_annotations=total)

    def _flush_batch(self, files: dict, annotations: list, offset: int) -> None:
        self.moha_client.put_folder(
            files=files,
            message=f'label-studio: sync {offset + len(files)} annotations',
            revision=self.resolved_revision(),
        )
        # Link rows are created only after a successful commit, so a failed upload
        # never marks annotations as exported.
        for annotation in annotations:
            MohaExportStorageLink.create(annotation, self)

    def delete_annotation(self, annotation):
        key = MohaExportStorageLink.get_key(annotation)
        self.moha_client.delete_file(
            path=self._object_path(key),
            message=f'label-studio: remove annotation {annotation.id}',
            revision=self.resolved_revision(),
        )
        MohaExportStorageLink.objects.filter(storage=self, annotation=annotation).delete()


def async_export_annotation_to_moha_storages(annotation):
    if isinstance(annotation, int):
        try:
            annotation = Annotation.objects.get(pk=annotation)
        except Annotation.DoesNotExist:
            logger.info('[moha] annotation %s no longer exists, skipping export', annotation)
            return

    project = annotation.project
    if hasattr(project, 'io_storages_mohaexportstorages'):
        for storage in project.io_storages_mohaexportstorages.all():
            logger.debug('[moha] export annotation %s to storage %s', annotation.id, storage.id)
            storage.save_annotation(annotation)


@receiver(post_save, sender=Annotation)
def export_annotation_to_moha_storages(sender, instance, **kwargs):
    storages = getattr(instance.project, 'io_storages_mohaexportstorages', None)
    if storages and storages.exists():
        start_job_async_or_sync(async_export_annotation_to_moha_storages, instance.pk)


@receiver(pre_delete, sender=Annotation)
def delete_annotation_from_moha_storages(sender, instance, **kwargs):
    links = MohaExportStorageLink.objects.filter(annotation=instance)
    for link in links:
        storage = link.storage
        if storage.can_delete_objects:
            logger.debug('[moha] delete annotation %s from storage %s', instance.id, storage.id)
            storage.delete_annotation(instance)


class MohaImportStorageLink(ImportStorageLink):
    storage = models.ForeignKey(MohaImportStorage, on_delete=models.CASCADE, related_name='links')


class MohaExportStorageLink(ExportStorageLink):
    storage = models.ForeignKey(MohaExportStorage, on_delete=models.CASCADE, related_name='links')
