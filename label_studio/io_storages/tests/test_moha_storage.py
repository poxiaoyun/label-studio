"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] Model / serializer behaviour with a stubbed adapter (no network).
"""

from unittest.mock import MagicMock

import pytest
from core.utils.common import load_func
from django.conf import settings
from io_storages.moha.models import MohaExportStorage, MohaImportStorage, MohaImportStorageLink
from io_storages.moha.serializers import MohaImportStorageSerializer
from django.test import override_settings
from io_storages.moha.serializers import _endpoint_allowlisted
from rest_framework.exceptions import ValidationError
from tasks.models import Annotation, Task


@pytest.fixture(autouse=True)
def disable_realtime_export(monkeypatch):
    """Annotation post_save would otherwise try to reach a real Moha endpoint."""
    monkeypatch.setattr(
        'io_storages.moha.models.async_export_annotation_to_moha_storages',
        lambda *args, **kwargs: None,
    )


def _import_storage(**kwargs) -> MohaImportStorage:
    defaults = dict(
        moha_endpoint='https://moha.example.com',
        moha_token='tok',
        organization='demo',
        repo_type='datasets',
        repo_name='repo',
        revision='main',
        prefix='images',
    )
    defaults.update(kwargs)
    return MohaImportStorage(**defaults)


def _stub_client(**methods) -> MagicMock:
    stub = MagicMock()
    for name, value in methods.items():
        getattr(stub, name).return_value = value
    return stub


class TestImportStorageUnit:
    def test_build_uri_pins_revision(self):
        storage = _import_storage()
        assert storage.build_uri('images/a.jpg') == 'moha://demo/datasets/repo/main/images/a.jpg'

    def test_can_resolve_url_matches_scope(self):
        storage = _import_storage()
        assert storage.can_resolve_url('moha://demo/datasets/repo/main/images/a.jpg')
        assert not storage.can_resolve_url('moha://demo/datasets/repo/main/audio/a.wav')
        assert not storage.can_resolve_url('moha://other/datasets/repo/main/images/a.jpg')
        assert not storage.can_resolve_url('moha://demo/datasets/repo/dev/images/a.jpg')
        assert not storage.can_resolve_url('moha://demo/datasets/repo/main/../secret')
        assert not storage.can_resolve_url('https://example.com/a.jpg')

    def test_generate_http_url_is_never_used(self):
        assert _import_storage().generate_http_url('moha://demo/datasets/repo/main/a.jpg') is None

    def test_get_data_blob_mode_uses_uri(self):
        storage = _import_storage(use_blob_urls=True)
        storage._moha_client = _stub_client()
        [obj] = storage.get_data('images/a.jpg')
        assert obj.task_data == {settings.DATA_UNDEFINED_NAME: 'moha://demo/datasets/repo/main/images/a.jpg'}

    def test_iter_objects_delegates(self):
        storage = _import_storage(regex_filter=r'.*\.jpg$')
        storage._moha_client = _stub_client()
        storage.moha_client.list_files.return_value = iter([])
        list(storage.iter_objects())
        _, kwargs = storage.moha_client.list_files.call_args
        assert kwargs['prefix'] == 'images'
        assert kwargs['recursive'] is False
        assert kwargs['regex'].pattern == r'.*\.jpg$'

    def test_get_bytes_stream_rejects_out_of_scope(self):
        storage = _import_storage()
        stream, content_type, metadata = storage.get_bytes_stream('moha://demo/datasets/repo/main/audio/a.wav')
        assert (stream, content_type, metadata) == (None, None, {})

    def test_get_bytes_stream_uses_uri_revision(self):
        # An unpinned storage accepts any revision and forwards the URI's revision.
        storage = _import_storage(revision='')
        storage._moha_client = _stub_client()
        storage.get_bytes_stream('moha://demo/datasets/repo/release-1/images/a.jpg', range_header='bytes=0-1')
        _, kwargs = storage.moha_client.open_stream.call_args
        assert kwargs['revision'] == 'release-1'
        assert kwargs['range_header'] == 'bytes=0-1'

    def test_get_bytes_stream_rejects_other_revision_when_pinned(self):
        storage = _import_storage(revision='main')
        storage._moha_client = _stub_client()
        result = storage.get_bytes_stream('moha://demo/datasets/repo/release-1/images/a.jpg')
        assert result == (None, None, {})
        storage.moha_client.open_stream.assert_not_called()

    def test_validate_connection_requires_files(self):
        storage = _import_storage()
        client = _stub_client()
        client.list_files.return_value = iter([])
        with pytest.raises(ValidationError):
            storage.validate_connection(client=client)

    def test_validate_connection_accepts_commit_revision(self):
        storage = _import_storage(revision='deadbeef')
        client = _stub_client()
        client.ref_exists.return_value = False
        client.get_content.return_value = object()
        client.list_files.return_value = iter([object()])
        storage.validate_connection(client=client)
        client.get_content.assert_called_once()


class TestExportStorageUnit:
    def test_object_path_joins_prefix(self):
        storage = MohaExportStorage(prefix='labels/out')
        assert storage._object_path('12.json') == 'labels/out/12.json'

    def test_object_path_without_prefix(self):
        storage = MohaExportStorage(prefix='')
        assert storage._object_path('12.json') == '12.json'

    def test_validate_connection_creates_missing_branch(self):
        storage = MohaExportStorage(revision='labels')
        client = _stub_client()
        client.ref_exists.return_value = False
        storage.validate_connection(client=client)
        client.ensure_branch.assert_called_once_with('labels')

    def test_validate_connection_skips_branch_work_without_revision(self):
        storage = MohaExportStorage(revision='')
        client = _stub_client()
        storage.validate_connection(client=client)
        client.ensure_branch.assert_not_called()


@pytest.mark.django_db
class TestExportStorageWithDatabase:
    @pytest.fixture
    def project(self):
        return load_func(settings.PROJECT_FACTORY)()

    @pytest.fixture
    def storage(self, project):
        return MohaExportStorage.objects.create(
            project=project,
            title='Moha export',
            moha_endpoint='https://moha.example.com',
            moha_token='tok',
            organization='demo',
            repo_type='datasets',
            repo_name='repo',
            prefix='labels',
            revision='main',
        )

    @pytest.fixture
    def annotations(self, project):
        task = Task.objects.create(project=project, data={'text': 'hello'})
        created = []
        for _ in range(3):
            created.append(
                Annotation.objects.create(
                    task=task,
                    project=project,
                    result=[],
                    completed_by=project.organization.created_by,
                )
            )
        return created

    def test_save_annotation_commits_once(self, storage):
        storage._moha_client = _stub_client()
        task = Task.objects.create(project=storage.project, data={'text': 'x'})
        annotation = Annotation.objects.create(
            task=task,
            project=storage.project,
            result=[],
            completed_by=storage.project.organization.created_by,
        )

        storage.save_annotation(annotation)

        storage.moha_client.put_file.assert_called_once()
        _, kwargs = storage.moha_client.put_file.call_args
        assert kwargs['path'] == f'labels/{annotation.id}'
        assert kwargs['revision'] == 'main'
        assert storage.links.count() == 1

    def test_bulk_save_batches_into_single_commit(self, storage, annotations):
        storage._moha_client = _stub_client()
        storage.status = 'queued'
        storage.save(update_fields=['status'])

        storage.save_annotations(Annotation.objects.filter(project=storage.project))

        storage.moha_client.put_folder.assert_called_once()
        files = storage.moha_client.put_folder.call_args.kwargs['files']
        assert len(files) == 3
        assert all(path.startswith('labels/') for path in files)
        assert storage.links.count() == 3
        storage.refresh_from_db()
        assert storage.status == 'completed'
        assert storage.last_sync_count == 3


@pytest.mark.django_db
class TestSerializer:
    def test_token_is_not_returned(self):
        project = load_func(settings.PROJECT_FACTORY)()
        storage = MohaImportStorage.objects.create(
            project=project,
            title='source',
            moha_endpoint='https://moha.example.com',
            moha_token='super-secret',
            organization='demo',
            repo_name='repo',
        )
        payload = MohaImportStorageSerializer(storage).data
        assert 'moha_token' not in payload

    def test_create_requires_token(self):
        project = load_func(settings.PROJECT_FACTORY)()
        serializer = MohaImportStorageSerializer(
            data={
                'project': project.id,
                'title': 'source',
                'moha_endpoint': 'https://moha.example.com',
                'organization': 'demo',
                'repo_name': 'repo',
            }
        )
        assert not serializer.is_valid()
        assert 'moha_token' in serializer.errors

    def test_models_live_in_the_shared_app(self):
        assert MohaImportStorage._meta.app_label == 'io_storages'
        assert MohaImportStorageLink._meta.app_label == 'io_storages'


class TestEndpointAllowlist:
    """MOHA_ENDPOINT_ALLOWLIST must accept host suffixes and IP networks."""

    @override_settings(MOHA_ENDPOINT_ALLOWLIST='example.com')
    def test_host_suffix(self):
        assert _endpoint_allowlisted('https://moha.example.com')
        assert not _endpoint_allowlisted('https://example.org')

    @override_settings(MOHA_ENDPOINT_ALLOWLIST='192.168.0.0/16')
    def test_cidr_with_ip_literal(self):
        assert _endpoint_allowlisted('http://192.168.10.5:8080')
        assert not _endpoint_allowlisted('http://10.1.2.3:8080')

    @override_settings(MOHA_ENDPOINT_ALLOWLIST='10.0.0.0/8, example.com')
    def test_multiple_entries(self):
        assert _endpoint_allowlisted('http://10.2.3.4')
        assert _endpoint_allowlisted('http://x.example.com')
        assert not _endpoint_allowlisted('http://172.16.0.1')

    @override_settings(MOHA_ENDPOINT_ALLOWLIST='')
    def test_empty_allowlist_blocks_private(self):
        assert not _endpoint_allowlisted('http://192.168.1.1')
