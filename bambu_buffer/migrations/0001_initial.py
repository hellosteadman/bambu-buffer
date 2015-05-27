# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BufferedItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'db_table': 'buffer_buffereditem',
            },
        ),
        migrations.CreateModel(
            name='BufferProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('avatar', models.URLField(max_length=255)),
                ('created_at', models.DateTimeField()),
                ('default', models.BooleanField(default=True)),
                ('formatted_username', models.CharField(max_length=100)),
                ('remote_id', models.CharField(unique=True, max_length=36)),
                ('schedules', models.TextField()),
                ('selected', models.BooleanField()),
            ],
            options={
                'db_table': 'buffer_profile',
            },
        ),
        migrations.CreateModel(
            name='BufferService',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('remote_id', models.CharField(max_length=36)),
                ('username', models.CharField(max_length=30)),
            ],
            options={
                'db_table': 'buffer_service',
            },
        ),
        migrations.CreateModel(
            name='BufferToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.CharField(max_length=36)),
                ('user', models.OneToOneField(related_name='buffer_token', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'buffer_token',
            },
        ),
        migrations.AddField(
            model_name='bufferservice',
            name='token',
            field=models.ForeignKey(related_name='services', to='bambu_buffer.BufferToken'),
        ),
        migrations.AddField(
            model_name='bufferprofile',
            name='service',
            field=models.ForeignKey(related_name='profiles', to='bambu_buffer.BufferService'),
        ),
        migrations.AlterUniqueTogether(
            name='buffereditem',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
