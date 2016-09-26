# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-26 07:33
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20160921_1110'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='original_url',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='feature',
            field=models.CharField(blank=True, choices=[('CA', 'Category'), ('DE', 'Describe'), ('AD', 'Adult'), ('TE', 'Text'), ('FA', 'Face'), ('LO', 'Logo'), ('MA', 'Map'), ('PH', 'Phone'), ('UR', 'Url')], default='CA', max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='service',
            field=models.CharField(blank=True, choices=[('GO', 'Google Vision'), ('MI', 'Microsoft Cognitive'), ('CR', 'Craftar')], default='UR', max_length=2, null=True),
        ),
        migrations.AddField(
            model_name='tag',
            name='payload',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tag',
            name='service',
            field=models.CharField(blank=True, choices=[('GO', 'Google Vision'), ('MI', 'Microsoft Cognitive')], default='GO', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='category',
            field=models.CharField(blank=True, choices=[('AI', 'AI'), ('HU', 'Human')], default='AI', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='results', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='tag',
            name='category',
            field=models.CharField(blank=True, choices=[('AI', 'AI'), ('HU', 'Human')], default='AI', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tags', to=settings.AUTH_USER_MODEL),
        ),
    ]
