"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] Serializers: field-level guarding, credential redaction and connection checks.
"""

import ipaddress
import logging
import socket
from urllib.parse import urlparse

from core.utils.io import validate_url_for_ssrf
from django.conf import settings
from io_storages.serializers import ExportStorageSerializer, ImportStorageSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .errors import describe
from .models import MohaExportStorage, MohaImportStorage
from .uri import REPO_TYPES

logger = logging.getLogger(__name__)

#: UI/API suffixes users tend to paste. The SDK appends ``/moha/v1/...`` itself, so
#: keeping these would produce ``/console/moha/v1/...`` and an HTML error page.
_ENDPOINT_SUFFIXES = ('/console', '/moha/v1', '/moha')


def normalize_endpoint(value: str) -> str:
    """Strip trailing slashes and accidental console/API suffixes from an endpoint."""
    value = (value or '').strip().rstrip('/')
    changed = True
    while changed:
        changed = False
        lowered = value.lower()
        for suffix in _ENDPOINT_SUFFIXES:
            if lowered.endswith(suffix):
                value = value[: -len(suffix)].rstrip('/')
                changed = True
                break
    return value


def _resolve_ips(host: str) -> set:
    """Resolve ``host`` to IP addresses; tolerates IP literals and DNS failures."""
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        infos = []
    addresses = set()
    for info in infos:
        try:
            addresses.add(ipaddress.ip_address(info[4][0]))
        except ValueError:
            continue
    if not addresses:
        try:
            addresses.add(ipaddress.ip_address(host))
        except ValueError:
            pass
    return addresses


def _endpoint_allowlisted(endpoint: str) -> bool:
    """Allow internal Moha endpoints without disabling SSRF protection globally.

    Entries in ``MOHA_ENDPOINT_ALLOWLIST`` are either:

    * host suffixes — ``example.com`` matches ``moha.example.com``;
    * IP networks — ``192.168.0.0/16`` / ``10.1.2.3`` match after resolving the host.
    """
    allowlist = getattr(settings, 'MOHA_ENDPOINT_ALLOWLIST', '') or ''
    entries = [item.strip().lower() for item in str(allowlist).split(',') if item.strip()]
    if not entries:
        return False

    host = (urlparse(endpoint).hostname or '').lower()
    if not host:
        return False

    resolved = None
    for entry in entries:
        if '/' in entry:
            try:
                network = ipaddress.ip_network(entry, strict=False)
            except ValueError:
                logger.warning('[moha] ignoring invalid MOHA_ENDPOINT_ALLOWLIST entry %r', entry)
                continue
            if resolved is None:
                resolved = _resolve_ips(host)
            if any(address in network for address in resolved):
                return True
        elif host == entry or host.endswith('.' + entry):
            return True
    return False


class MohaStorageSerializerMixin:
    """Shared behaviour for source and target storage serializers."""

    secure_fields = ['moha_token']

    #: Declared explicitly so the API rejects empty values even though the model
    #: columns are nullable (the form always sends them).
    organization = serializers.CharField(required=False, allow_blank=True)
    repo_name = serializers.CharField(required=False, allow_blank=True)
    moha_token = serializers.CharField(required=False, allow_blank=True)
    repo_type = serializers.ChoiceField(choices=REPO_TYPES, required=False)

    def to_representation(self, instance):
        result = super().to_representation(instance)
        for attr in self.secure_fields:
            result.pop(attr, None)
        return result

    def validate_moha_endpoint(self, value):
        if not value:
            return value
        value = normalize_endpoint(value)
        if settings.SSRF_PROTECTION_ENABLED and not _endpoint_allowlisted(value):
            validate_url_for_ssrf(value)
        return value

    def validate(self, data):
        data = super().validate(data)

        # PATCH without connection fields: nothing to re-validate here.
        if self.partial and 'moha_endpoint' not in data:
            return data

        instance = self.instance
        if instance is None and self.initial_data.get('id'):
            instance = self.Meta.model.objects.filter(pk=self.initial_data['id']).first()

        if instance is None and not data.get('moha_token'):
            raise ValidationError({'moha_token': 'A Moha token is required.'})

        storage = instance or self.Meta.model()
        for attr, value in data.items():
            setattr(storage, attr, value)

        try:
            storage.validate_connection()
        except ValidationError:
            raise
        except Exception as exc:  # defensive: validate_connection already translates
            logger.info('[moha] serializer validation failed: %s', type(exc).__name__)
            raise ValidationError(describe(exc)) from exc

        return data


class MohaImportStorageSerializer(MohaStorageSerializerMixin, ImportStorageSerializer):
    # ``type`` drives the frontend API paths (/api/storages/{type}/...). The shared
    # serializer derives it from its own file location ("io_storages"), so every
    # driver must override it.
    type = serializers.ReadOnlyField(default='moha')

    class Meta:
        model = MohaImportStorage
        fields = '__all__'


class MohaExportStorageSerializer(MohaStorageSerializerMixin, ExportStorageSerializer):
    type = serializers.ReadOnlyField(default='moha')

    class Meta:
        model = MohaExportStorage
        fields = '__all__'
