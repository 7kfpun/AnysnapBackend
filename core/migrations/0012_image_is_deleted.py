# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-04 13:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_notification_is_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
