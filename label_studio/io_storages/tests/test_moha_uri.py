"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] URI addressing tests (no Django, no network).
"""

import unittest

from io_storages.moha.uri import (
    MohaURIError,
    build_uri,
    in_scope,
    parse_uri,
)


class TestMohaURI(unittest.TestCase):
    def test_roundtrip_simple(self):
        uri = build_uri('demo', 'datasets', 'street-view', 'main', 'images/1.jpg')
        self.assertEqual(uri, 'moha://demo/datasets/street-view/main/images/1.jpg')
        parsed = parse_uri(uri)
        self.assertEqual(parsed.organization, 'demo')
        self.assertEqual(parsed.repo_type, 'datasets')
        self.assertEqual(parsed.repo_name, 'street-view')
        self.assertEqual(parsed.revision, 'main')
        self.assertEqual(parsed.path, 'images/1.jpg')

    def test_roundtrip_branch_with_slash(self):
        uri = build_uri('demo', 'datasets', 'repo', 'feature/labeling', 'a.json')
        self.assertIn('feature%2Flabeling', uri)
        self.assertEqual(parse_uri(uri).revision, 'feature/labeling')

    def test_roundtrip_unicode_path(self):
        uri = build_uri('demo', 'datasets', 'repo', 'main', '目录/图片 1.jpg')
        self.assertEqual(parse_uri(uri).path, '目录/图片 1.jpg')

    def test_build_rejects_traversal(self):
        with self.assertRaises(MohaURIError):
            build_uri('demo', 'datasets', 'repo', 'main', '../etc/passwd')
        with self.assertRaises(MohaURIError):
            build_uri('demo', 'datasets', 'repo', 'main', 'a/../../b')

    def test_build_rejects_bad_repo_type(self):
        with self.assertRaises(MohaURIError):
            build_uri('demo', 'images', 'repo', 'main', 'a.jpg')

    def test_build_requires_revision(self):
        with self.assertRaises(MohaURIError):
            build_uri('demo', 'datasets', 'repo', '', 'a.jpg')

    def test_parse_rejects_wrong_scheme(self):
        with self.assertRaises(MohaURIError):
            parse_uri('s3://demo/datasets/repo/main/a.jpg')

    def test_parse_rejects_short_uri(self):
        with self.assertRaises(MohaURIError):
            parse_uri('moha://demo/datasets/repo')

    def test_parse_rejects_traversal(self):
        with self.assertRaises(MohaURIError):
            parse_uri('moha://demo/datasets/repo/main/../secret.txt')

    def test_in_scope_prefix(self):
        parsed = parse_uri('moha://demo/datasets/repo/main/images/a.jpg')
        self.assertTrue(
            in_scope(
                parsed,
                organization='demo',
                repo_type='datasets',
                repo_name='repo',
                revision=None,
                prefix='images',
            )
        )
        self.assertFalse(
            in_scope(
                parsed,
                organization='demo',
                repo_type='datasets',
                repo_name='repo',
                revision=None,
                prefix='audio',
            )
        )

    def test_in_scope_prefix_is_not_a_string_prefix(self):
        parsed = parse_uri('moha://demo/datasets/repo/main/images2/a.jpg')
        self.assertFalse(
            in_scope(
                parsed,
                organization='demo',
                repo_type='datasets',
                repo_name='repo',
                revision=None,
                prefix='images',
            )
        )

    def test_in_scope_revision(self):
        parsed = parse_uri('moha://demo/datasets/repo/main/a.jpg')
        self.assertTrue(
            in_scope(
                parsed,
                organization='demo',
                repo_type='datasets',
                repo_name='repo',
                revision='main',
                prefix='',
            )
        )
        self.assertFalse(
            in_scope(
                parsed,
                organization='demo',
                repo_type='datasets',
                repo_name='repo',
                revision='dev',
                prefix='',
            )
        )

    def test_in_scope_other_repository(self):
        parsed = parse_uri('moha://demo/datasets/repo/main/a.jpg')
        self.assertFalse(
            in_scope(
                parsed,
                organization='other',
                repo_type='datasets',
                repo_name='repo',
                revision=None,
                prefix='',
            )
        )


if __name__ == '__main__':
    unittest.main()
