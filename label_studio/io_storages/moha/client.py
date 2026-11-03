"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] The only module that talks to ``xiaoshiai_hub`` (moha-sdk).

Everything above this layer (models, serializers, API views) consumes standard
Python types only, which keeps SDK upgrades local to this file.

Public surface:
    MohaConfig      plain settings object (no Django import)
    MohaObject      listing entry
    MohaClient      thin, explicit wrapper around HubClient + the resolve endpoint
"""

import logging
import os
import re
import tempfile
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple
from urllib.parse import quote

logger = logging.getLogger(__name__)

#: Server side default page size for ``/contents`` is small; warn when a directory
#: hits it so operators can spot a possibly truncated listing (see README, R1).
CONTENTS_PAGE_SIZE_HINT = 100

_BINARY_SUFFIXES = ('.gitkeep', '.gitattributes')


@dataclass(frozen=True)
class MohaConfig:
    endpoint: str
    token: str
    organization: str
    repo_type: str
    repo_name: str
    revision: str = ''
    request_timeout: float = 30.0
    connect_timeout: float = 10.0

    @property
    def repo_id(self) -> str:
        return f'{self.organization}/{self.repo_name}'


@dataclass(frozen=True)
class MohaObject:
    path: str
    size: int = 0
    modified: Optional[str] = None
    content_type: Optional[str] = None


class ResponseStream:
    """Adapt ``requests.Response`` to the API ``proxy_api.time_limited_chunker`` expects.

    ``proxy_api`` calls ``stream.iter_chunks(chunk_size=...)`` and ``stream.close()``
    (the shape boto3's ``StreamingBody`` exposes). ``skip``/``limit`` implement the
    Range fallback for the Moha ``/resolve`` endpoint, which ignores Range headers
    for git-backed files.
    """

    def __init__(self, response, skip: int = 0, limit: Optional[int] = None):
        self._response = response
        self._skip = max(0, int(skip or 0))
        self._limit = limit
        self._consumed = 0
        self._closed = False

    def __iter__(self) -> Iterator[bytes]:
        return self.iter_chunks()

    def iter_chunks(self, chunk_size: int = 64 * 1024) -> Iterator[bytes]:
        remaining_skip = self._skip
        remaining_limit = self._limit

        for chunk in self._response.iter_content(chunk_size=chunk_size):
            if self._closed:
                return
            if not chunk:
                continue

            if remaining_skip:
                if len(chunk) <= remaining_skip:
                    remaining_skip -= len(chunk)
                    continue
                chunk = chunk[remaining_skip:]
                remaining_skip = 0

            if remaining_limit is not None:
                if remaining_limit <= 0:
                    return
                if len(chunk) > remaining_limit:
                    chunk = chunk[:remaining_limit]
                remaining_limit -= len(chunk)

            self._consumed += len(chunk)
            yield chunk

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._response.close()
        except Exception:  # pragma: no cover - defensive
            logger.debug('[moha] failed to close response', exc_info=True)


class MohaClient:
    """Thin adapter over ``xiaoshiai_hub.HubClient`` and the ``/resolve`` endpoint."""

    def __init__(self, config: MohaConfig, hub=None):
        self.config = config
        self._hub = hub
        self.last_truncated_dirs: List[str] = []

    # ------------------------------------------------------------------ setup

    @property
    def hub(self):
        if self._hub is None:
            # Imported lazily: keeps this module importable in tests and lets the
            # rest of Label Studio boot even if the SDK is missing.
            from xiaoshiai_hub import HubClient

            self._hub = HubClient(
                base_url=self.config.endpoint,
                token=self.config.token or None,
            )
        return self._hub

    def _base(self) -> str:
        return self.config.endpoint.rstrip('/')

    def _repo_path(self) -> str:
        c = self.config
        return f'{self._base()}/moha/v1/organizations/{c.organization}/{c.repo_type}/{c.repo_name}'

    # ------------------------------------------------------------- repository

    def get_repository(self):
        c = self.config
        return self.hub.get_repository_info(c.organization, c.repo_type, c.repo_name)

    def refs(self):
        c = self.config
        return self.hub.get_repository_refs(c.organization, c.repo_type, c.repo_name)

    def default_branch(self) -> str:
        for ref in self.refs():
            if getattr(ref, 'is_default', False) and getattr(ref, 'type', 'branch') == 'branch':
                return ref.name
        return 'main'

    def resolve_revision(self) -> str:
        """Return the configured revision or the repository default branch."""
        return self.config.revision or self.default_branch()

    def ref_exists(self, revision: str) -> bool:
        return any(getattr(ref, 'name', None) == revision for ref in self.refs())

    def ensure_branch(self, branch: str, from_branch: Optional[str] = None) -> None:
        """Create ``branch`` when missing. No-op when it already exists."""
        if self.ref_exists(branch):
            return
        c = self.config
        base = from_branch or self.default_branch()
        logger.info('[moha] creating branch %s in %s from %s', branch, c.repo_id, base)
        self.hub.create_branch(c.organization, c.repo_type, c.repo_name, branch, base)

    # -------------------------------------------------------------- listing

    def get_content(self, path: str = '', revision: Optional[str] = None):
        c = self.config
        return self.hub.get_repository_content(
            c.organization,
            c.repo_type,
            c.repo_name,
            revision or self.resolve_revision(),
            path or '',
        )

    def list_files(
        self,
        prefix: str = '',
        recursive: bool = False,
        regex: Optional[re.Pattern] = None,
        revision: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Iterator[MohaObject]:
        """Yield files under ``prefix`` honouring ``recursive`` and ``regex``."""
        stack = [(prefix or '').strip('/')]
        emitted = 0
        self.last_truncated_dirs = []

        while stack:
            path = stack.pop()
            content = self.get_content(path, revision=revision)
            entries = getattr(content, 'entries', None) or []

            if len(entries) >= CONTENTS_PAGE_SIZE_HINT:
                # The SDK does not expose page/limit yet; a full page may be truncated.
                self.last_truncated_dirs.append(path or '/')
                logger.warning(
                    '[moha] directory %r returned %d entries (page size hint %d); '
                    'the listing may be truncated until moha-sdk exposes paging',
                    path or '/',
                    len(entries),
                    CONTENTS_PAGE_SIZE_HINT,
                )

            for entry in entries:
                entry_path = getattr(entry, 'path', '') or ''
                entry_type = getattr(entry, 'type', 'file')

                if entry_type == 'dir':
                    if recursive:
                        stack.append(entry_path)
                    continue
                if entry_type != 'file':
                    # symlinks/submodules are not valid Label Studio tasks
                    continue
                if not entry_path or entry_path.rsplit('/', 1)[-1] in _BINARY_SUFFIXES:
                    continue
                if regex and not regex.match(entry_path):
                    continue

                yield MohaObject(
                    path=entry_path,
                    size=int(getattr(entry, 'size', 0) or 0),
                    modified=_iso(getattr(entry, 'last_commit', None)),
                    content_type=getattr(entry, 'content_type', None),
                )
                emitted += 1
                if limit is not None and emitted >= limit:
                    return

    # ------------------------------------------------------------- reading

    def read_bytes(self, path: str, revision: Optional[str] = None) -> bytes:
        """Download one file fully. Used for JSON/JSONL task files only."""
        c = self.config
        fd, tmp = tempfile.mkstemp(prefix='moha-read-')
        os.close(fd)
        try:
            self.hub.download_file(
                organization=c.organization,
                repo_type=c.repo_type,
                repo_name=c.repo_name,
                branch=revision or self.resolve_revision(),
                file_path=path,
                local_path=tmp,
                show_progress=False,
            )
            with open(tmp, 'rb') as handle:
                return handle.read()
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                logger.debug('[moha] failed to remove temp file %s', tmp, exc_info=True)

    def open_stream(
        self,
        path: str,
        revision: Optional[str] = None,
        range_header: Optional[str] = None,
    ) -> Tuple[Optional[ResponseStream], Optional[str], Dict[str, object]]:
        """Open a streaming read against ``/resolve``.

        Moha answers either with the file body or with a 302 to the object store.
        ``requests`` follows the redirect and keeps the ``Range`` header, so the
        object store returns ``206`` for seekable playback. When the server ignores
        Range (git-backed files) we trim locally to keep semantics correct.
        """
        c = self.config
        rev = quote(revision or self.resolve_revision(), safe='')
        url = f'{self._repo_path()}/resolve/{rev}/{quote(path.lstrip("/"), safe="/")}'
        headers = {'Range': range_header} if range_header else {}

        response = self.hub.session.get(
            url,
            headers=headers,
            stream=True,
            allow_redirects=True,
            timeout=(self.config.connect_timeout, self.config.request_timeout),
        )
        if response.status_code >= 400:
            logger.warning(
                '[moha] resolve failed for %s/%s status=%s',
                c.repo_id,
                path,
                response.status_code,
            )
            response.close()
            return None, None, {}

        skip, limit = 0, None
        content_range = response.headers.get('Content-Range')
        if range_header and response.status_code == 200:
            skip, limit = _parse_range(range_header)

        content_length = response.headers.get('Content-Length')
        try:
            content_length_int = int(content_length) if content_length is not None else None
        except (TypeError, ValueError):
            content_length_int = None
        if content_length_int is not None and skip:
            content_length_int = max(0, content_length_int - skip)

        metadata: Dict[str, object] = {
            'StatusCode': response.status_code,
            'ContentLength': content_length_int,
            'ContentRange': content_range,
            'LastModified': response.headers.get('Last-Modified'),
            'ETag': response.headers.get('ETag'),
        }
        return (
            ResponseStream(response, skip=skip, limit=limit),
            response.headers.get('Content-Type'),
            metadata,
        )

    # ------------------------------------------------------------- writing

    def put_file(
        self,
        path: str,
        data: bytes,
        message: str,
        revision: Optional[str] = None,
    ) -> None:
        fd, tmp = tempfile.mkstemp(prefix='moha-put-', suffix='.json')
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(data)
            self.hub_upload_file(tmp, path, message, revision)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                logger.debug('[moha] failed to remove temp file %s', tmp, exc_info=True)

    def hub_upload_file(self, local_path: str, path: str, message: str, revision: Optional[str]) -> None:
        c = self.config
        from xiaoshiai_hub import upload_file

        upload_file(
            path_file=local_path,
            path_in_repo=path,
            repo_id=c.repo_id,
            repo_type=c.repo_type,
            revision=revision or self.resolve_revision(),
            commit_message=message,
            base_url=self._base(),
            token=c.token or None,
        )

    def put_folder(
        self,
        files: Dict[str, bytes],
        message: str,
        revision: Optional[str] = None,
    ) -> None:
        """Upload a batch in a single commit (``upload_folder`` = one API call)."""
        if not files:
            return
        c = self.config
        from xiaoshiai_hub import upload_folder

        with tempfile.TemporaryDirectory(prefix='moha-batch-') as staging:
            for relative, payload in files.items():
                target = os.path.join(staging, *relative.split('/'))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, 'wb') as handle:
                    handle.write(payload)

            upload_folder(
                folder_path=staging,
                repo_id=c.repo_id,
                repo_type=c.repo_type,
                revision=revision or self.resolve_revision(),
                commit_message=message,
                base_url=self._base(),
                token=c.token or None,
            )

    def delete_file(self, path: str, message: str, revision: Optional[str] = None) -> None:
        c = self.config
        self.hub.delete_file(
            c.organization,
            c.repo_type,
            c.repo_name,
            revision or self.resolve_revision(),
            path,
            message,
        )


def _iso(commit) -> Optional[str]:
    if commit is None:
        return None
    value = getattr(commit, 'date', None) or getattr(commit, 'created', None) or getattr(commit, 'time', None)
    if value is None:
        return None
    return value.isoformat() if hasattr(value, 'isoformat') else str(value)


def _parse_range(range_header: str) -> Tuple[int, Optional[int]]:
    """Translate ``bytes=start-end`` into ``(skip, length)`` for local trimming."""
    try:
        spec = range_header.split('=', 1)[1]
        start_raw, _, end_raw = spec.partition('-')
        start = int(start_raw) if start_raw else 0
    except (IndexError, ValueError):
        return 0, None

    if not end_raw:
        return start, None
    try:
        end = int(end_raw)
    except ValueError:
        return start, None
    if end < start:
        return start, None
    return start, end - start + 1


__all__ = [
    'CONTENTS_PAGE_SIZE_HINT',
    'MohaClient',
    'MohaConfig',
    'MohaObject',
    'ResponseStream',
]
