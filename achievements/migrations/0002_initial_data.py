# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-28 02:54
from __future__ import unicode_literals

from django.db import migrations


def data_migration(apps, schema_editor):
    # Move to fixtures
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('achievements', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(data_migration),
    ]
