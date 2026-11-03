"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[moha] Serializers: field-level guarding, credential redaction and connection checks.
"""

import logging
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


def _endpoint_allowlisted(endpoint: str) -> bool:
    """Allow internal (private) Moha endpoints without disabling SSRF protection globally."""
    allowlist = getattr(settings, 'MOHA_ENDPOINT_ALLOWLIST', '') or ''
    hosts = [item.strip().lower() for item in str(allowlist).split(',') if item.strip()]
    if not hosts:
        return False
    host = (urlparse(endpoint).hostname or '').lower()
    return any(host == allowed or host.endswith('.' + allowed) for allowed in hosts)


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
        value = value.strip().rstrip('/')
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
    class Meta:
        model = MohaImportStorage
        fields = '__all__'


class MohaExportStorageSerializer(MohaStorageSerializerMixin, ExportStorageSerializer):
    class Meta:
        model = MohaExportStorage
        fields = '__all__'
