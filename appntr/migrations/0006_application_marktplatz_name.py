# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-09-15 17:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appntr', '0005_userconfig_zoom_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='marktplatz_name',
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name='Falls vorhanden: Nutzer*innen-Name auf dem Marktplatz der Ideen https://marktplatz.dib.de/'),
        ),
    ]
