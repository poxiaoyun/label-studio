"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] Error translation for the Moha storage driver.

The SDK raises its own exception hierarchy; Label Studio surfaces
``rest_framework.exceptions.ValidationError`` to the storage form. Keeping the
translation in one dependency-free function means:

* ``moha/client.py`` does not import Django;
* ``moha/serializers.py`` is the only place that wraps errors for the API;
* messages stay stable and testable without a Django environment.
"""

from typing import Optional


def _exception_name(exc: BaseException) -> str:
    return type(exc).__name__


def status_code(exc: BaseException) -> Optional[int]:
    """Best-effort HTTP status extraction (works for SDK ``HTTPError`` and requests)."""
    code = getattr(exc, 'status_code', None)
    if isinstance(code, int):
        return code
    response = getattr(exc, 'response', None)
    code = getattr(response, 'status_code', None)
    return code if isinstance(code, int) else None


def describe(exc: BaseException) -> str:
    """Return a user-facing, secret-free message for a storage error."""
    name = _exception_name(exc)
    code = status_code(exc)

    if name == 'AuthenticationError' or code == 401:
        return 'Moha rejected the token: check that it is valid and not expired.'
    if code == 403:
        return 'The token has no permission for this repository (read/write access is required).'
    if name == 'RepositoryNotFoundError' or code == 404:
        return 'Repository, revision or file not found, or the token cannot see it.'
    if name in ('Timeout', 'ConnectTimeout', 'ReadTimeout'):
        return 'Timed out connecting to the Moha endpoint. Check the URL and network reachability.'
    if name in ('ConnectionError', 'SSLError'):
        return 'Cannot reach the Moha endpoint. Check the URL, TLS certificate and network.'
    if name in ('JSONDecodeError', 'ValueError') and 'expecting value' in str(exc).lower():
        return (
            'The endpoint returned a non-JSON response (usually the console or a login page). '
            'Use the Moha service root URL, e.g. http://host:8000 — without /console or /moha.'
        )
    if code and code >= 500:
        return f'Moha returned HTTP {code}. Try again later or contact the platform administrator.'
    if code:
        return f'Moha returned HTTP {code}.'

    detail = str(exc).strip().splitlines()[0] if str(exc).strip() else name
    # Never leak tokens that may be embedded in URLs by the HTTP layer.
    if 'token=' in detail.lower() or 'authorization' in detail.lower():
        detail = 'request failed (details redacted)'
    return f'Moha request failed: {detail[:300]}'
