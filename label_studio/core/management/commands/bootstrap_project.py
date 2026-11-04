"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[pxs] Idempotent install-time bootstrap.

The Kubernetes chart runs this once in an init container, so a fresh install
already has an account, a workspace, a project with a labeling config and the
Moha source storage. Every step is create-only: existing rows are left alone so
that edits made in the UI survive ``helm upgrade``. ``--force-update`` and
``--reset-password`` are the only ways to overwrite.

Secrets arrive through environment variables (``BOOTSTRAP_USER_PASSWORD``,
``BOOTSTRAP_MOHA_TOKEN``) because command-line arguments are readable in the pod
spec, while every other parameter can come from either source.
"""

import os

from core.utils.io import find_dir, read_yaml
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from io_storages.moha.models import MohaImportStorage
from io_storages.moha.serializers import normalize_endpoint
from io_storages.moha.uri import REPO_TYPES
from organizations.models import Organization
from projects.models import Project

User = get_user_model()


def env(name):
    return os.environ.get(name, '').strip()


class Command(BaseCommand):
    help = 'Create the bootstrap account, workspace, project, labeling config and Moha storage (idempotent).'

    def add_arguments(self, parser):
        parser.add_argument('--email', default=env('BOOTSTRAP_USER_EMAIL'), help='Account email, also the login name.')
        parser.add_argument('--password', default=env('BOOTSTRAP_USER_PASSWORD'), help='Account password.')
        parser.add_argument('--first-name', default=env('BOOTSTRAP_USER_FIRST_NAME'), help='Account first name.')
        parser.add_argument('--last-name', default=env('BOOTSTRAP_USER_LAST_NAME'), help='Account last name.')
        parser.add_argument(
            '--api-token',
            default=env('BOOTSTRAP_API_TOKEN'),
            help='Fixed API token for the account, used by the install-time sync job.',
        )
        parser.add_argument('--org-title', default=env('BOOTSTRAP_ORG_TITLE'), help='Workspace title.')
        parser.add_argument('--project-title', default=env('BOOTSTRAP_PROJECT_TITLE'), help='Project title.')
        parser.add_argument(
            '--template',
            default=env('BOOTSTRAP_TEMPLATE'),
            help='Built-in labeling template, e.g. natural-language-processing/question-answering.',
        )
        parser.add_argument('--moha-endpoint', default=env('BOOTSTRAP_MOHA_ENDPOINT'), help='Moha base URL.')
        parser.add_argument('--moha-token', default=env('BOOTSTRAP_MOHA_TOKEN'), help='Moha access token.')
        parser.add_argument('--moha-organization', default=env('BOOTSTRAP_MOHA_ORGANIZATION'), help='Moha organization.')
        parser.add_argument('--moha-repo-type', default=env('BOOTSTRAP_MOHA_REPO_TYPE'), help='Moha repository type.')
        parser.add_argument('--moha-dataset', default=env('BOOTSTRAP_MOHA_DATASET'), help='Moha repository name.')
        parser.add_argument('--moha-revision', default=env('BOOTSTRAP_MOHA_REVISION'), help='Branch, tag or commit.')
        parser.add_argument('--moha-prefix', default=env('BOOTSTRAP_MOHA_PREFIX'), help='Directory inside the repository.')
        parser.add_argument(
            '--force-update', action='store_true', help='Overwrite the labeling config of an existing project.'
        )
        parser.add_argument(
            '--reset-password', action='store_true', help='Reset the password of an existing account.'
        )
        parser.add_argument('--dry-run', action='store_true', help='Roll everything back after reporting.')

    def handle(self, *args, **options):
        email = options['email']
        if not email:
            raise CommandError('--email or BOOTSTRAP_USER_EMAIL is required')

        label_config = self._label_config(options['template'])

        try:
            with transaction.atomic():
                user = self._ensure_user(options)
                self._ensure_api_token(options, user)
                organization = self._ensure_organization(options, user)
                project = self._ensure_project(options, organization, user, label_config)
                self._ensure_storage(options, project)
                if options['dry_run']:
                    transaction.set_rollback(True)
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(f'bootstrap failed: {exc}') from exc

        self._report(options, email)

    # ------------------------------------------------------------------ steps

    def _ensure_user(self, options):
        email = options['email']
        password = options['password']
        user = User.objects.filter(email__iexact=email).first()

        if user is not None:
            if options['reset_password']:
                if not password:
                    raise CommandError('--reset-password requires --password')
                user.set_password(password)
                user.save(update_fields=['password'])
                self._log('user %s: password reset', email)
            else:
                self._log('user %s: exists, skipped', email)
            return user

        if not password:
            raise CommandError('--password or BOOTSTRAP_USER_PASSWORD is required for a new account')

        username = email.split('@')[0]
        if User.objects.filter(username=username).exists():
            username = email

        user = User.objects.create_user(
            email=email,
            password=password,
            username=username,
            first_name=options['first_name'],
            last_name=options['last_name'],
        )
        self._log('user %s: created', email)
        return user

    def _ensure_api_token(self, options, user):
        """Pin the account token so the install-time sync job can authenticate."""
        key = options['api_token']
        if not key:
            return

        from rest_framework.authtoken.models import Token

        token = Token.objects.filter(user=user).first()
        if token is not None and token.key == key:
            self._log('api token: exists, skipped')
            return

        try:
            if token is not None:
                # ``key`` is the primary key, so rotation means replacing the row.
                token.delete()
            Token.objects.create(user=user, key=key)
        except IntegrityError as exc:
            raise CommandError('--api-token is already used by another account') from exc

        self._log('api token: %s for %s', 'rotated' if token else 'created', user.email)

    def _ensure_organization(self, options, user):
        title = options['org_title'] or 'Label Studio'
        organization = Organization.objects.filter(title=title).first()

        if organization is None:
            organization = Organization.create_organization(created_by=user, title=title)
            self._log('workspace %s: created', title)
        else:
            self._log('workspace %s: exists, skipped', title)

        if not organization.has_user(user):
            organization.add_user(user)
            self._log('workspace %s: member %s added', title, user.email)

        if user.active_organization_id != organization.pk:
            user.active_organization = organization
            user.save(update_fields=['active_organization'])

        return organization

    def _ensure_project(self, options, organization, user, label_config):
        title = options['project_title']
        if not title:
            raise CommandError('--project-title or BOOTSTRAP_PROJECT_TITLE is required')

        project = Project.objects.filter(organization=organization, title=title).first()
        if project is None:
            project = Project.objects.create(
                title=title,
                organization=organization,
                created_by=user,
                label_config=label_config,
            )
            self._log('project %s: created (id=%s)', title, project.pk)
            return project

        if options['force_update'] and project.label_config != label_config:
            project.label_config = label_config
            project.save(update_fields=['label_config'])
            self._log('project %s: labeling config updated', title)
        else:
            self._log('project %s: exists, skipped', title)

        return project

    def _ensure_storage(self, options, project):
        endpoint = normalize_endpoint(options['moha_endpoint'] or '')
        dataset = options['moha_dataset'] or ''
        if not endpoint or not dataset:
            self._log('storage: skipped (no Moha endpoint or dataset configured)')
            return None

        repo_type = options['moha_repo_type'] or REPO_TYPES[0]
        if repo_type not in REPO_TYPES:
            raise CommandError(f'--moha-repo-type must be one of {", ".join(REPO_TYPES)}')

        token = options['moha_token']
        lookup = {
            'project': project,
            'moha_endpoint': endpoint,
            'organization': options['moha_organization'] or '',
            'repo_type': repo_type,
            'repo_name': dataset,
        }
        storage = MohaImportStorage.objects.filter(**lookup).first()
        if storage is not None:
            self._log('storage %s/%s: exists, skipped', lookup['organization'], dataset)
            return storage

        if not token:
            raise CommandError('--moha-token or BOOTSTRAP_MOHA_TOKEN is required to create the storage')

        storage = MohaImportStorage(
            title='Moha',
            project=project,
            moha_token=token,
            revision=options['moha_revision'] or '',
            prefix=options['moha_prefix'] or '',
            recursive_scan=False,
            use_blob_urls=False,
            presign=False,
            **lookup,
        )
        storage.validate_connection()
        storage.save()
        self._log('storage %s/%s: created (id=%s)', lookup['organization'], dataset, storage.pk)
        return storage

    # ---------------------------------------------------------------- helpers

    def _label_config(self, name):
        if not name:
            raise CommandError('--template or BOOTSTRAP_TEMPLATE is required')

        root = find_dir('annotation_templates')
        candidate = os.path.realpath(os.path.join(root, name))
        if not candidate.startswith(os.path.realpath(root) + os.sep):
            raise CommandError(f'template {name} is outside the template library')

        for path in (candidate, f'{candidate}.yml', os.path.join(candidate, 'config.yml')):
            if os.path.isfile(path) and path.endswith('.yml'):
                config = read_yaml(path).get('config')
                if not config:
                    raise CommandError(f'template {path} has no config section')
                self._log('template %s: loaded', os.path.relpath(path, root))
                return config

        raise CommandError(
            f'template {name} not found; use a path such as natural-language-processing/question-answering'
        )

    def _log(self, message, *args):
        self.stdout.write(f'[bootstrap] {message % args if args else message}')

    def _report(self, options, email):
        if options['dry_run']:
            self.stdout.write('[bootstrap] dry run: all changes rolled back')
            return
        self.stdout.write(
            '[bootstrap] done: sign in as %s, project "%s"; run a storage sync in the UI if no tasks appear'
            % (email, options['project_title'])
        )
