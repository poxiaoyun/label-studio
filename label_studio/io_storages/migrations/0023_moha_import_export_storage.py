# [moha] Initial tables for the Moha storage driver.
#
# Hand-written to keep the upstream migration chain untouched (0001-0022 are not
# modified). If upstream later ships its own 0023, rename this file to the next
# free number and update ``dependencies`` (see io_storages/moha/README.md).
# Generated from the model definitions in io_storages/moha/models.py.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('io_storages', '0022_normalize_localfiles_paths'),
        ('projects', '__first__'),
        ('tasks', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='MohaImportStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'title',
                    models.CharField(
                        blank=True,
                        help_text='Cloud storage title',
                        max_length=256,
                        null=True,
                        verbose_name='title',
                    ),
                ),
                (
                    'description',
                    models.TextField(
                        blank=True, help_text='Cloud storage description', null=True, verbose_name='description'
                    ),
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True, help_text='Creation time', verbose_name='created at'),
                ),
                (
                    'last_sync',
                    models.DateTimeField(
                        blank=True, help_text='Last sync finished time', null=True, verbose_name='last sync'
                    ),
                ),
                (
                    'last_sync_count',
                    models.PositiveIntegerField(
                        blank=True, help_text='Count of tasks synced last time', null=True, verbose_name='last sync count'
                    ),
                ),
                (
                    'last_sync_job',
                    models.CharField(
                        blank=True,
                        help_text='Last sync job ID',
                        max_length=256,
                        null=True,
                        verbose_name='last_sync_job',
                    ),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('initialized', 'Initialized'),
                            ('queued', 'Queued'),
                            ('in_progress', 'In progress'),
                            ('failed', 'Failed'),
                            ('completed', 'Completed'),
                            ('completed_with_errors', 'Completed with errors'),
                        ],
                        default='initialized',
                        max_length=64,
                    ),
                ),
                (
                    'traceback',
                    models.TextField(
                        blank=True, help_text='Traceback report for the last failed sync', null=True
                    ),
                ),
                (
                    'meta',
                    models.JSONField(
                        default=dict,
                        help_text='Meta and debug information about storage processes',
                        null=True,
                        verbose_name='meta',
                    ),
                ),
                (
                    'synchronizable',
                    models.BooleanField(
                        default=True, help_text='If storage can be synced', verbose_name='synchronizable'
                    ),
                ),
                (
                    'moha_endpoint',
                    models.TextField(
                        blank=True,
                        help_text='Moha endpoint URL, e.g. https://rune.example.com (without /moha)',
                        null=True,
                        verbose_name='moha_endpoint',
                    ),
                ),
                (
                    'moha_token',
                    models.TextField(
                        blank=True,
                        help_text='Moha access token (sent as a Bearer token)',
                        null=True,
                        verbose_name='moha_token',
                    ),
                ),
                (
                    'organization',
                    models.TextField(
                        blank=True, help_text='Moha organization name', null=True, verbose_name='organization'
                    ),
                ),
                (
                    'repo_type',
                    models.TextField(
                        choices=[('datasets', 'Datasets'), ('models', 'Models')],
                        default='datasets',
                        help_text='Moha repository type',
                        verbose_name='repo_type',
                    ),
                ),
                (
                    'repo_name',
                    models.TextField(
                        blank=True, help_text='Moha repository name', null=True, verbose_name='repo_name'
                    ),
                ),
                (
                    'revision',
                    models.TextField(
                        blank=True,
                        help_text='Branch, tag or commit; empty means the repository default branch',
                        null=True,
                        verbose_name='revision',
                    ),
                ),
                (
                    'prefix',
                    models.TextField(
                        blank=True,
                        help_text='Directory inside the repository (empty for the repository root)',
                        null=True,
                        verbose_name='prefix',
                    ),
                ),
                (
                    'presign',
                    models.BooleanField(default=False, help_text='Generate presigned URLs', verbose_name='presign'),
                ),
                (
                    'recursive_scan',
                    models.BooleanField(
                        default=False,
                        help_text='Perform recursive scan over the repository content',
                        verbose_name='recursive scan',
                    ),
                ),
                (
                    'regex_filter',
                    models.TextField(
                        blank=True,
                        help_text='Cloud storage regex for filtering objects',
                        null=True,
                        verbose_name='regex_filter',
                    ),
                ),
                (
                    'use_blob_urls',
                    models.BooleanField(
                        default=False,
                        help_text='Interpret objects as BLOBs and generate URLs',
                        verbose_name='use_blob_urls',
                    ),
                ),
                (
                    'project',
                    models.ForeignKey(
                        help_text='A unique integer value identifying this project.',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='%(app_label)s_%(class)ss',
                        to='projects.project',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MohaExportStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'title',
                    models.CharField(
                        blank=True,
                        help_text='Cloud storage title',
                        max_length=256,
                        null=True,
                        verbose_name='title',
                    ),
                ),
                (
                    'description',
                    models.TextField(
                        blank=True, help_text='Cloud storage description', null=True, verbose_name='description'
                    ),
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True, help_text='Creation time', verbose_name='created at'),
                ),
                (
                    'last_sync',
                    models.DateTimeField(
                        blank=True, help_text='Last sync finished time', null=True, verbose_name='last sync'
                    ),
                ),
                (
                    'last_sync_count',
                    models.PositiveIntegerField(
                        blank=True, help_text='Count of tasks synced last time', null=True, verbose_name='last sync count'
                    ),
                ),
                (
                    'last_sync_job',
                    models.CharField(
                        blank=True,
                        help_text='Last sync job ID',
                        max_length=256,
                        null=True,
                        verbose_name='last_sync_job',
                    ),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('initialized', 'Initialized'),
                            ('queued', 'Queued'),
                            ('in_progress', 'In progress'),
                            ('failed', 'Failed'),
                            ('completed', 'Completed'),
                            ('completed_with_errors', 'Completed with errors'),
                        ],
                        default='initialized',
                        max_length=64,
                    ),
                ),
                (
                    'traceback',
                    models.TextField(
                        blank=True, help_text='Traceback report for the last failed sync', null=True
                    ),
                ),
                (
                    'meta',
                    models.JSONField(
                        default=dict,
                        help_text='Meta and debug information about storage processes',
                        null=True,
                        verbose_name='meta',
                    ),
                ),
                (
                    'synchronizable',
                    models.BooleanField(
                        default=True, help_text='If storage can be synced', verbose_name='synchronizable'
                    ),
                ),
                (
                    'moha_endpoint',
                    models.TextField(
                        blank=True,
                        help_text='Moha endpoint URL, e.g. https://rune.example.com (without /moha)',
                        null=True,
                        verbose_name='moha_endpoint',
                    ),
                ),
                (
                    'moha_token',
                    models.TextField(
                        blank=True,
                        help_text='Moha access token (sent as a Bearer token)',
                        null=True,
                        verbose_name='moha_token',
                    ),
                ),
                (
                    'organization',
                    models.TextField(
                        blank=True, help_text='Moha organization name', null=True, verbose_name='organization'
                    ),
                ),
                (
                    'repo_type',
                    models.TextField(
                        choices=[('datasets', 'Datasets'), ('models', 'Models')],
                        default='datasets',
                        help_text='Moha repository type',
                        verbose_name='repo_type',
                    ),
                ),
                (
                    'repo_name',
                    models.TextField(
                        blank=True, help_text='Moha repository name', null=True, verbose_name='repo_name'
                    ),
                ),
                (
                    'revision',
                    models.TextField(
                        blank=True,
                        help_text='Branch, tag or commit; empty means the repository default branch',
                        null=True,
                        verbose_name='revision',
                    ),
                ),
                (
                    'prefix',
                    models.TextField(
                        blank=True,
                        help_text='Directory inside the repository (empty for the repository root)',
                        null=True,
                        verbose_name='prefix',
                    ),
                ),
                (
                    'can_delete_objects',
                    models.BooleanField(
                        blank=True,
                        help_text='Deletion from storage enabled',
                        null=True,
                        verbose_name='can_delete_objects',
                    ),
                ),
                (
                    'project',
                    models.ForeignKey(
                        help_text='A unique integer value identifying this project.',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='%(app_label)s_%(class)ss',
                        to='projects.project',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MohaExportStorageLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'object_exists',
                    models.BooleanField(
                        default=True,
                        help_text='Whether object under external link still exists',
                        verbose_name='object exists',
                    ),
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True, help_text='Creation time', verbose_name='created at'),
                ),
                (
                    'updated_at',
                    models.DateTimeField(auto_now=True, help_text='Update time', verbose_name='updated at'),
                ),
                (
                    'annotation',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='%(app_label)s_%(class)s',
                        to='tasks.annotation',
                    ),
                ),
                (
                    'storage',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='links',
                        to='io_storages.mohaexportstorage',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MohaImportStorageLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.TextField(help_text='External link key', verbose_name='key')),
                (
                    'object_exists',
                    models.BooleanField(
                        default=True,
                        help_text='Whether object under external link still exists',
                        verbose_name='object exists',
                    ),
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True, help_text='Creation time', verbose_name='created at'),
                ),
                ('row_group', models.IntegerField(blank=True, help_text='Parquet row group', null=True)),
                (
                    'row_index',
                    models.IntegerField(blank=True, help_text='Parquet row index, or JSON[L] object index', null=True),
                ),
                (
                    'storage',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='links',
                        to='io_storages.mohaimportstorage',
                    ),
                ),
                (
                    'task',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='%(app_label)s_%(class)s',
                        to='tasks.task',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
