"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] Adapter tests. A fake hub keeps these tests offline and SDK-free.
"""

import json
import unittest
from dataclasses import dataclass
from typing import Dict, List, Optional

from io_storages.moha.client import (
    CONTENTS_PAGE_SIZE_HINT,
    MohaClient,
    MohaConfig,
    ResponseStream,
)
from io_storages.moha.errors import describe, status_code


@dataclass
class FakeEntry:
    path: str
    type: str = 'file'
    size: int = 10
    content_type: Optional[str] = 'image/jpeg'
    last_commit: Optional[object] = None


class FakeContent:
    def __init__(self, entries: List[FakeEntry]):
        self.entries = entries


class FakeRef:
    def __init__(self, name: str, is_default: bool = False, type_: str = 'branch'):
        self.name = name
        self.is_default = is_default
        self.type = type_


class FakeResponse:
    def __init__(self, status_code=200, headers=None, chunks=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._chunks = chunks or []
        self.closed = False

    def iter_content(self, chunk_size=1024):
        for chunk in self._chunks:
            yield chunk

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class FakeHub:
    def __init__(self, tree: Dict[str, List[FakeEntry]], refs=None, response=None):
        self.tree = tree
        self.refs = refs or [FakeRef('main', is_default=True)]
        self.session = FakeSession(response or FakeResponse())
        self.downloads = []
        self.delete_calls = []
        self.branches = []

    def get_repository_info(self, organization, repo_type, repo_name):
        return object()

    def get_repository_refs(self, organization, repo_type, repo_name):
        return list(self.refs)

    def get_repository_content(self, organization, repo_type, repo_name, branch, path):
        return FakeContent(self.tree.get(path, []))

    def download_file(self, organization, repo_type, repo_name, branch, file_path, local_path, show_progress):
        self.downloads.append((branch, file_path))
        with open(local_path, 'wb') as handle:
            handle.write(b'{"data": {"text": "ok"}}')

    def create_branch(self, organization, repo_type, repo_name, branch_name, from_branch):
        self.branches.append((branch_name, from_branch))
        self.refs.append(FakeRef(branch_name))

    def delete_file(self, organization, repo_type, repo_name, branch, file_path, message):
        self.delete_calls.append((branch, file_path, message))


def _config(**kwargs) -> MohaConfig:
    defaults = dict(
        endpoint='https://moha.example.com',
        token='tok',
        organization='demo',
        repo_type='datasets',
        repo_name='repo',
        revision='main',
    )
    defaults.update(kwargs)
    return MohaConfig(**defaults)


class TestListing(unittest.TestCase):
    def setUp(self):
        self.tree = {
            '': [FakeEntry('images', type='dir'), FakeEntry('readme.md'), FakeEntry('.gitkeep')],
            'images': [
                FakeEntry('images/a.jpg'),
                FakeEntry('images/b.png', size=20),
                FakeEntry('images/nested', type='dir'),
            ],
            'images/nested': [FakeEntry('images/nested/c.jpg')],
        }
        self.hub = FakeHub(self.tree)
        self.client = MohaClient(_config(), hub=self.hub)

    def test_non_recursive_lists_top_level_files_only(self):
        files = [obj.path for obj in self.client.list_files()]
        self.assertEqual(files, ['readme.md'])

    def test_recursive_lists_all_files(self):
        files = [obj.path for obj in self.client.list_files(recursive=True)]
        self.assertEqual(sorted(files), ['images/a.jpg', 'images/b.png', 'images/nested/c.jpg', 'readme.md'])

    def test_prefix_scopes_listing(self):
        files = [obj.path for obj in self.client.list_files(prefix='images', recursive=True)]
        self.assertEqual(sorted(files), ['images/a.jpg', 'images/b.png', 'images/nested/c.jpg'])

    def test_regex_filter(self):
        import re

        files = [
            obj.path for obj in self.client.list_files(recursive=True, regex=re.compile(r'.*\.png$'))
        ]
        self.assertEqual(files, ['images/b.png'])

    def test_limit_stops_early(self):
        files = list(self.client.list_files(recursive=True, limit=2))
        self.assertEqual(len(files), 2)

    def test_page_size_warning(self):
        self.tree['big'] = [FakeEntry(f'big/{i}.jpg') for i in range(CONTENTS_PAGE_SIZE_HINT)]
        list(self.client.list_files(prefix='big'))
        self.assertIn('big', self.client.last_truncated_dirs)


class TestStreaming(unittest.TestCase):
    def _client(self, response):
        return MohaClient(_config(), hub=FakeHub({}, response=response))

    def test_range_passthrough_and_metadata(self):
        response = FakeResponse(
            status_code=206,
            headers={
                'Content-Range': 'bytes 3-5/10',
                'Content-Length': '3',
                'Content-Type': 'video/mp4',
                'Last-Modified': 'Wed, 01 Jan 2025 00:00:00 GMT',
            },
            chunks=[b'345'],
        )
        client = self._client(response)
        stream, content_type, metadata = client.open_stream('a.mp4', range_header='bytes=3-5')

        self.assertIsInstance(stream, ResponseStream)
        self.assertEqual(content_type, 'video/mp4')
        self.assertEqual(metadata['StatusCode'], 206)
        self.assertEqual(metadata['ContentRange'], 'bytes 3-5/10')
        self.assertEqual(b''.join(stream.iter_chunks(chunk_size=2)), b'345')

        _, kwargs = client.hub.session.calls[0]
        self.assertEqual(kwargs['headers'], {'Range': 'bytes=3-5'})
        self.assertTrue(kwargs['stream'])
        self.assertTrue(kwargs['allow_redirects'])

    def test_server_ignoring_range_is_trimmed_locally(self):
        response = FakeResponse(
            status_code=200,
            headers={'Content-Length': '10', 'Content-Type': 'application/octet-stream'},
            chunks=[b'01234', b'56789'],
        )
        client = self._client(response)
        stream, _, metadata = client.open_stream('a.bin', range_header='bytes=3-5')
        self.assertEqual(b''.join(stream.iter_chunks(chunk_size=2)), b'345')
        self.assertEqual(metadata['ContentLength'], 7)  # 10 - skip(3)

    def test_http_error_returns_empty(self):
        response = FakeResponse(status_code=404, chunks=[])
        client = self._client(response)
        stream, content_type, metadata = client.open_stream('missing.jpg')
        self.assertIsNone(stream)
        self.assertIsNone(content_type)
        self.assertEqual(metadata, {})
        self.assertTrue(response.closed)

    def test_stream_close_is_idempotent(self):
        response = FakeResponse(chunks=[b'x'])
        stream = ResponseStream(response)
        stream.close()
        stream.close()
        self.assertTrue(response.closed)


class TestRefsAndBranches(unittest.TestCase):
    def test_default_branch(self):
        hub = FakeHub({}, refs=[FakeRef('dev'), FakeRef('main', is_default=True)])
        client = MohaClient(_config(revision=''), hub=hub)
        self.assertEqual(client.resolve_revision(), 'main')

    def test_ensure_branch_creates_once(self):
        hub = FakeHub({}, refs=[FakeRef('main', is_default=True)])
        client = MohaClient(_config(), hub=hub)
        client.ensure_branch('feature/x')
        client.ensure_branch('feature/x')
        self.assertEqual(hub.branches, [('feature/x', 'main')])

    def test_ensure_branch_noop_when_present(self):
        hub = FakeHub({}, refs=[FakeRef('main', is_default=True), FakeRef('release')])
        client = MohaClient(_config(), hub=hub)
        client.ensure_branch('release')
        self.assertEqual(hub.branches, [])


class TestErrorMapping(unittest.TestCase):
    def test_status_code_from_attribute(self):
        class Boom(Exception):
            status_code = 403

        self.assertEqual(status_code(Boom()), 403)
        self.assertIn('permission', describe(Boom()).lower())

    def test_auth_error_by_name(self):
        class AuthenticationError(Exception):
            pass

        self.assertIn('token', describe(AuthenticationError()).lower())

    def test_not_found(self):
        class RepositoryNotFoundError(Exception):
            pass

        self.assertIn('not found', describe(RepositoryNotFoundError()).lower())

    def test_server_error(self):
        class HTTPError(Exception):
            status_code = 502

        self.assertIn('502', describe(HTTPError()))

    def test_redacts_authorization(self):
        class Weird(Exception):
            pass

        self.assertNotIn('Bearer', describe(Weird('Authorization: Bearer abc')))

    def test_non_json_response_is_explained(self):
        with self.assertRaises(json.JSONDecodeError) as ctx:
            json.loads('<html>console</html>')
        message = describe(ctx.exception)
        self.assertIn('non-JSON', message)
        self.assertIn('/console', message)


if __name__ == '__main__':
    unittest.main()
