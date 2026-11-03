"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] End-to-end test against a fake Moha HTTP service.

Unlike the other tests this one runs the **real** ``moha-sdk`` client against a
local stub server, so it validates the wire contract we depend on: URL shapes,
resolve redirects/Range handling, upload payloads and error mapping.

Skipped automatically when the SDK is not installed.
"""

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlparse

import pytest
from core.utils.common import load_func
from django.conf import settings

pytest.importorskip('xiaoshiai_hub')

from io_storages.moha.client import MohaClient, MohaConfig  # noqa: E402

REPO_PATH = '/moha/v1/organizations/demo/datasets/repo'
#: The SDK posts commits to the Hub "mutation" prefix (no /v1, no /organizations).
MUTATION_PATH = '/moha/demo/datasets/repo'
FILE_BYTES = b'hello-moha'


class _Handler(BaseHTTPRequestHandler):
    server_version = 'MohaStub/1.0'

    def log_message(self, *args):  # keep pytest output clean
        pass

    # ----------------------------------------------------------------- helpers
    def _json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _record(self, **extra):
        entry = {'method': self.command, 'path': unquote(urlparse(self.path).path)}
        entry.update(extra)
        self.server.requests.append(entry)
        return entry

    # -------------------------------------------------------------------- GET
    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == REPO_PATH:
            self._record()
            return self._json({'name': 'repo', 'type': 'dataset'})
        if path == f'{REPO_PATH}/refs':
            self._record()
            return self._json([{'name': 'main', 'ref': 'refs/heads/main', 'type': 'branch', 'isDefault': True}])
        if path.startswith(f'{REPO_PATH}/contents/'):
            self._record()
            rest = path[len(f'{REPO_PATH}/contents/') :]
            revision, _, sub = rest.partition('/')
            assert revision == 'main'
            return self._json(_contents(sub))
        if path.startswith(f'{REPO_PATH}/resolve/'):
            range_header = self.headers.get('Range')
            entry = self._record(range=range_header, auth=self.headers.get('Authorization'))
            start, end = 0, len(FILE_BYTES) - 1
            status = 200
            if range_header:
                spec = range_header.split('=', 1)[1]
                start_s, _, end_s = spec.partition('-')
                start = int(start_s or 0)
                end = int(end_s) if end_s else end
                status = 206
            chunk = FILE_BYTES[start : end + 1]
            self.send_response(status)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(chunk)))
            if status == 206:
                self.send_header('Content-Range', f'bytes {start}-{end}/{len(FILE_BYTES)}')
            self.end_headers()
            self.wfile.write(chunk)
            self.server.last_resolve = entry
            return
        self._record(status=404)
        return self._json({'message': 'not found'}, status=404)

    # ------------------------------------------------------------------- POST
    def do_POST(self):
        length = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(length) if length else b''
        path = unquote(urlparse(self.path).path)
        if path in (f'{REPO_PATH}/api/upload', f'{MUTATION_PATH}/api/upload'):
            payload = json.loads(raw.decode() or '{}')
            entry = self._record(payload=payload, auth=self.headers.get('Authorization'))
            self.server.uploads.append(entry)
            return self._json({'commit': 'abc', 'files': [f.get('path') for f in payload.get('files', [])]})
        if path.startswith(f'{MUTATION_PATH}/refs/') or path.startswith(f'{REPO_PATH}/refs/'):
            self._record()
            return self._json({})
        self._record(status=404)
        return self._json({'message': 'not found'}, status=404)


def _contents(sub: str):
    if sub in ('', '/'):
        return {'entries': [{'name': 'images', 'path': 'images', 'type': 'dir'}, {'name': 'notes.txt', 'path': 'notes.txt', 'type': 'file', 'size': 3}]}
    if sub == 'images':
        return {
            'entries': [
                {'name': 'a.jpg', 'path': 'images/a.jpg', 'type': 'file', 'size': len(FILE_BYTES), 'contentType': 'image/jpeg'},
            ]
        }
    return {'entries': []}


class StubServer(HTTPServer):
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests = []
        self.uploads = []
        self.last_resolve = None


@pytest.fixture
def moha_server():
    server = StubServer(('127.0.0.1', 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


def _config(server: StubServer, **kwargs) -> MohaConfig:
    defaults = dict(
        endpoint=f'http://127.0.0.1:{server.server_address[1]}',
        token='test-token',
        organization='demo',
        repo_type='datasets',
        repo_name='repo',
        revision='main',
        request_timeout=5,
        connect_timeout=5,
    )
    defaults.update(kwargs)
    return MohaConfig(**defaults)


def test_client_wire_contract(moha_server):
    client = MohaClient(_config(moha_server))

    # repository + refs + contents
    client.get_repository()
    assert client.default_branch() == 'main'
    files = [obj.path for obj in client.list_files(recursive=True)]
    assert sorted(files) == ['images/a.jpg', 'notes.txt']

    # resolve: authorization + range
    stream, content_type, metadata = client.open_stream('images/a.jpg', range_header='bytes=0-1')
    assert b''.join(stream.iter_chunks()) == FILE_BYTES[:2]
    assert metadata['StatusCode'] == 206
    assert metadata['ContentRange'] == f'bytes 0-1/{len(FILE_BYTES)}'
    assert moha_server.last_resolve['auth'] == 'Bearer test-token'

    # upload (single file) — verifies base64 payload and branch
    client.put_file('labels/1.json', b'{"a":1}', 'commit message')
    upload = moha_server.uploads[-1]['payload']
    assert upload['branch'] == 'main'
    assert upload['files'][0]['path'] == 'labels/1.json'
    assert base64.b64decode(upload['files'][0]['content']) == b'{"a":1}'

    # upload (batch) — one request for many files
    client.put_folder({'labels/2.json': b'{}', 'labels/3.json': b'{}'}, 'bulk')
    batch = moha_server.uploads[-1]['payload']
    assert sorted(item['path'] for item in batch['files']) == ['labels/2.json', 'labels/3.json']


@pytest.mark.django_db
def test_storage_end_to_end(moha_server):
    from io_storages.moha.models import MohaExportStorage, MohaImportStorage
    from tasks.models import Annotation, Task

    project = load_func(settings.PROJECT_FACTORY)()
    common = dict(
        project=project,
        title='moha',
        moha_endpoint=f'http://127.0.0.1:{moha_server.server_address[1]}',
        moha_token='test-token',
        organization='demo',
        repo_type='datasets',
        repo_name='repo',
        revision='main',
    )

    source = MohaImportStorage.objects.create(prefix='images', use_blob_urls=True, **common)
    source.validate_connection()
    assert list(source.iter_keys()) == ['images/a.jpg']
    [obj] = source.get_data('images/a.jpg')
    uri = obj.task_data[settings.DATA_UNDEFINED_NAME]
    assert uri == 'moha://demo/datasets/repo/main/images/a.jpg'
    assert source.can_resolve_url(uri)
    stream, _, metadata = source.get_bytes_stream(uri)
    assert b''.join(stream.iter_chunks()) == FILE_BYTES

    target = MohaExportStorage.objects.create(prefix='labels', **common)
    target.validate_connection()
    task = Task.objects.create(project=project, data={'text': 'hi'})
    annotation = Annotation.objects.create(
        task=task, project=project, result=[], completed_by=project.organization.created_by
    )
    target.save_annotation(annotation)
    payload = moha_server.uploads[-1]['payload']
    assert payload['files'][0]['path'] == f'labels/{annotation.id}'
    assert target.links.count() == 1
