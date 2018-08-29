# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-01-02 16:56
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('appntr', '0008_auto_20171130_1621'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('interviewer_names', models.TextField(verbose_name='Namen der beiden DiB-Gesprächspartner*innen')),
                ('feedback_type', models.CharField(choices=[('yes', 'Ja, aufnehmen'), ('no', 'Nein, nicht aufnehmen'), ('maybe', 'Wir können uns nicht einigen. Bitte erneut einladen.'), ('missed', 'Person ist nicht zum Termin erschienen'), ('recall_yes', 'Gespräch einzeln geführt, meine Empfehlung: ja, aufnehmen --> bitte zweiten Gesprächspartner organisieren'), ('recall_no', 'Gespräch einzeln geführt, meine Empfehlung: nein, nicht aufnehmen --> bitte zweiten Gesprächspartner organisieren'), ('recall_maybe', 'Gespräch einzeln geführt, meine Empfehlung:bin mir unsicher --> bitte zwei neue Gesprächspartner organisieren')], db_index=True, max_length=25)),
                ('statement_yes', models.TextField(blank=True, help_text='Bitte diesen Teil nur bei Zusage ausfüllen', null=True, verbose_name='BEI ZUSAGE: Kompetenzen für Mitarbeit')),
                ('statement_maybe', models.TextField(blank=True, help_text='Bitte gebt den nächsten Gesprächspartnern mit auf den Weg, wo ihr unsicher seid', null=True, verbose_name='BEI UNSICHERHEIT/ UNEINIGKEIT: Kurze Begründung')),
                ('statement_no', models.TextField(blank=True, help_text='Bitte diesen Teil nur bei Absage ausfüllen, bitte sachlich schreiben (bspw. passt nicht zu den Werten etc.)', null=True, verbose_name='BEI ABSAGE: kurze, sachliche Begründung')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to='appntr.Application')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
