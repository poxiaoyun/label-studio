"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] URI helpers for the Moha storage driver.

URI shape::

    moha://{organization}/{repo_type}/{repo_name}/{revision}/{file_path}

``revision`` is percent-encoded (``safe=''``) so branch names containing ``/``
(``feature/x``) stay unambiguous; everything else is kept verbatim so the path
matches the key Label Studio stores in ``MohaImportStorageLink``.

This module is intentionally dependency free (no Django, no network, no SDK):
it is the cheapest place to unit test the driver's addressing rules.
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote, unquote, urlparse

SCHEME = 'moha'

#: Repository types exposed by the Moha Hub API (``/organizations/{org}/{type}/...``).
#: ``spaces``/``images`` are served by dedicated endpoints and are out of scope.
REPO_TYPES = ('datasets', 'models')

_TRAVERSAL = re.compile(r'(^|/)\.\.?(/|$)')
_CONTROL = re.compile(r'[\x00-\x1f\x7f]')


class MohaURIError(ValueError):
    """Raised when a ``moha://`` URI cannot be parsed or is out of scope."""


@dataclass(frozen=True)
class MohaURI:
    organization: str
    repo_type: str
    repo_name: str
    revision: str
    path: str


def _clean_path(path: str, *, field: str) -> str:
    """Validate a repository-relative path and strip leading/trailing slashes."""
    if path is None:
        return ''
    if not isinstance(path, str):
        raise MohaURIError(f'{field} must be a string')
    if _CONTROL.search(path):
        raise MohaURIError(f'{field} contains control characters')
    if '\\' in path:
        raise MohaURIError(f'{field} must use forward slashes')
    path = path.strip('/')
    if not path:
        return ''
    if _TRAVERSAL.search(path):
        raise MohaURIError(f'{field} must not contain "." or ".." segments')
    if any(not segment for segment in path.split('/')):
        raise MohaURIError(f'{field} contains an empty segment')
    return path


def _clean_identifier(value: str, *, field: str) -> str:
    if not value or not isinstance(value, str):
        raise MohaURIError(f'{field} is required')
    if '/' in value or _CONTROL.search(value) or value in ('.', '..'):
        raise MohaURIError(f'{field} contains invalid characters')
    return value


def build_uri(
    organization: str,
    repo_type: str,
    repo_name: str,
    revision: str,
    path: str,
) -> str:
    """Build the canonical URI for one repository file."""
    organization = _clean_identifier(organization, field='organization')
    repo_name = _clean_identifier(repo_name, field='repo_name')
    if repo_type not in REPO_TYPES:
        raise MohaURIError(f'repo_type must be one of {", ".join(REPO_TYPES)}')
    if not revision:
        raise MohaURIError('revision is required to build a stable URI')
    path = _clean_path(path, field='path')
    if not path:
        raise MohaURIError('path is required')

    revision_token = quote(revision, safe='')
    return f'{SCHEME}://{organization}/{repo_type}/{repo_name}/{revision_token}/{path}'


def parse_uri(uri: str) -> MohaURI:
    """Parse a ``moha://`` URI. Raises :class:`MohaURIError` when malformed."""
    if not isinstance(uri, str) or not uri:
        raise MohaURIError('URI must be a non-empty string')

    parsed = urlparse(uri, allow_fragments=False)
    if parsed.scheme != SCHEME:
        raise MohaURIError(f'URI scheme must be "{SCHEME}"')

    organization = parsed.netloc
    segments: List[str] = [s for s in parsed.path.split('/') if s != '']
    # Allow "moha://org/datasets/repo/main/a/b/c" (path may contain slashes) but
    # reject "moha://org//datasets/..." style holes.
    if parsed.path.startswith('//') or '//' in parsed.path:
        raise MohaURIError('URI path contains an empty segment')
    if len(segments) < 4:
        raise MohaURIError('URI must be moha://{org}/{repo_type}/{repo}/{revision}/{path}')

    organization = _clean_identifier(organization, field='organization')
    repo_type, repo_name, revision_token = segments[0], segments[1], segments[2]
    path = _clean_path('/'.join(segments[3:]), field='path')
    if repo_type not in REPO_TYPES:
        raise MohaURIError(f'unsupported repo_type "{repo_type}"')

    revision = unquote(revision_token)
    if not revision:
        raise MohaURIError('URI revision is empty')

    return MohaURI(
        organization=organization,
        repo_type=repo_type,
        repo_name=_clean_identifier(repo_name, field='repo_name'),
        revision=revision,
        path=path,
    )


def in_scope(
    parsed: MohaURI,
    *,
    organization: str,
    repo_type: str,
    repo_name: str,
    revision: Optional[str],
    prefix: Optional[str],
) -> bool:
    """Return True when ``parsed`` belongs to the storage identified by the arguments.

    ``revision=None`` means the storage follows the repository default branch and
    accepts any pinned revision; an explicit revision must match exactly.
    """
    if parsed.organization != organization:
        return False
    if parsed.repo_type != repo_type:
        return False
    if parsed.repo_name != repo_name:
        return False
    if revision and parsed.revision != revision:
        return False

    scope = _clean_path(prefix or '', field='prefix')
    if not scope:
        return True
    return parsed.path == scope or parsed.path.startswith(scope + '/')
