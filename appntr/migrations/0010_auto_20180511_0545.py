# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-05-11 05:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appntr', '0009_auto_20180510_1744'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='email',
            field=models.CharField(help_text='Unter welcher E-Mail-Adresse können wir Dich persönlich erreichen?', max_length=255, verbose_name='E-Mail-Adresse'),
        ),
    ]