# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-24 17:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0002_auto_20170220_1700'),
    ]

    operations = [
        migrations.CreateModel(
            name='Word',
            fields=[
                ('word', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('semanticField', models.CharField(max_length=100)),
            ],
        ),
    ]
