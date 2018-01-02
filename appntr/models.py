from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.db.models import Q
from django.conf import settings
from django.db import models, IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

import re

URL_BUILDER = "https://talky.io/dib-ma-{}"
MIN_VOTES = 8

class Timeslot(models.Model):
    class Meta:
        app_label = 'appntr'
    once = models.BooleanField(default=True)
    datetime = models.DateTimeField()
    interviewer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="slots")



class Application(models.Model):
    class Meta:
        app_label = 'appntr'
        index_together = [
            ["state"]
        ]

    class STATES:
        NEW = "new"
        TO_INVITE = "to_invite"
        INVITED = "invited"
        INTERVIEWING = "interview"
        ACCEPTED = "accepted"
        REJECTED = "rejected"


    added_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    state = models.CharField(db_index=True, max_length=25, choices= [
        (STATES.NEW, "new"),
        (STATES.TO_INVITE, "To invite"),
        (STATES.INVITED, "Invited"),
        (STATES.INTERVIEWING, "Being interviewed"),
        (STATES.ACCEPTED, "Accepted"),
        (STATES.REJECTED, "Rejected")
    ], default=STATES.NEW)
    # actual application 

    # personal data
    first_name = models.CharField(max_length=255, verbose_name="Vorname")
    last_name = models.CharField(max_length=255, verbose_name="Nachname")
    gender = models.CharField(max_length=30, verbose_name="Geschlecht")
    email = models.CharField(max_length=255, verbose_name="E-Mail Adresse", help_text="Unter welcher E-Mail Adresse können wir Dich persönlich erreichen?")
    phone = models.CharField(max_length=255, verbose_name="Telefonnummer", help_text="Unter welcher Telefonnummer können wir Dich persönlich erreichen?")
    country = models.CharField(max_length=25, verbose_name="Bundesland", help_text="In welchem Bundesland hast du deinen Erstwohnsitz?")
    marktplatz_name = models.CharField(max_length=120, null=True, blank=True, verbose_name="Marktplatz Nutzername", help_text="Falls gegeben: Nutzername auf dem Marktplatz der Ideen")
    internet_profiles = models.TextField(null=True, blank=True, verbose_name="Falls gegeben: Persönliche Webseite(n), Profile auf Sozialen Netzwerken (Xing, Facebook, Twitter und so weiter)")
    affiliations = models.TextField(null=True, blank=True, verbose_name="Falls gegeben: (ehemalige) Parteimitgliedschaft oder Interessenvertretungen")

    # application
    motivation = models.TextField()
    skills = models.TextField()
    ethical_dilemma = models.TextField()
    dib_participation = models.BooleanField(default=False, verbose_name="Ich habe bereits an Aktionen von DiB teilgenommen")
    dib_participation_details = models.TextField(null=True, blank=True, verbose_name="Wenn ja, welche Aktionen hat Du bereits mitgemacht:", help_text="Bitte zähle kurz auf: (z.B. Initiative eingereicht, Unterschriften gesammelt, Stände betreut, DiB-Tische besucht etc.)")
    contacted_members = models.TextField(null=True, blank=True, verbose_name="Falls gegeben: Ich bin bereits mit folgenden DiB-Aktiven im Kontakt:")

    @property
    def is_open_state(self):
        return self.state not in [self.STATES.ACCEPTED, self.STATES.REJECTED]

    @property
    def winner(self):
        votes = dict(y=0, n=0, a=0)
        for v in self.votes.all():
            votes[v.vote] += 1

        tally = sum(votes.values())
        if tally < MIN_VOTES:
            # None yet
            return None

        if votes['y'] > votes['n']:
            if votes['y'] <= votes['a']:
                return 'abstain'
            
            return "yay"
        return "nay" 


class Feedback(models.Model):
    class Meta:
        app_label = 'appntr'

    class TYPES:
        YES = "yes"
        NO = "no"
        MAYBE = "maybe"
        MISSED = "missed"
        RECALL_YES = "recall_yes"
        RECALL_NO = "recall_no"
        RECALL_MAYBE = "recall_maybe"

    added_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="feedbacks")
    application = models.ForeignKey(Application, related_name="feedbacks")

    interviewer_names = models.TextField(null=False, blank=False, verbose_name="Namen der beiden DiB-Gesprächspartner*innen")

    feedback_type = models.CharField(db_index=True, max_length=25, choices= [
        (TYPES.YES, "Ja, aufnehmen"),
        (TYPES.NO, "Nein, nicht aufnehmen"),
        (TYPES.MAYBE, "Wir können uns nicht einigen. Bitte erneut einladen."),
        (TYPES.MISSED, "Person ist nicht zum Termin erschienen"),
        (TYPES.RECALL_YES, "Gespräch einzeln geführt, meine Empfehlung: ja, aufnehmen --> bitte zweiten Gesprächspartner organisieren"),
        (TYPES.RECALL_NO, "Gespräch einzeln geführt, meine Empfehlung: nein, nicht aufnehmen --> bitte zweiten Gesprächspartner organisieren"),
        (TYPES.RECALL_MAYBE, "Gespräch einzeln geführt, meine Empfehlung:bin mir unsicher --> bitte zwei neue Gesprächspartner organisieren")
    ])

    statement_yes = models.TextField(null=True, blank=True, verbose_name="BEI ZUSAGE: Kompetenzen für Mitarbeit", help_text="Bitte diesen Teil nur bei Zusage ausfüllen")
    statement_maybe = models.TextField(null=True, blank=True, verbose_name="BEI UNSICHERHEIT/ UNEINIGKEIT: Kurze Begründung", help_text="Bitte gebt den nächsten Gesprächspartnern mit auf den Weg, wo ihr unsicher seid")
    statement_no = models.TextField(null=True, blank=True, verbose_name="BEI ABSAGE: kurze, sachliche Begründung", help_text="Bitte diesen Teil nur bei Absage ausfüllen, bitte sachlich schreiben (bspw. passt nicht zu den Werten etc.)")

class UserVote(models.Model):
    class Meta:
        app_label = 'appntr'
    added_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="votes")
    application = models.ForeignKey(Application, related_name="votes")
    vote = models.CharField(max_length=1, choices=[('y', 'yay'), ('n', 'nay'), ('a', 'abstain')])

    class Meta:
        unique_together = (("user", "application"),)


class Comment(models.Model):
    class Meta:
        app_label = 'appntr'
    added_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="comments")
    application = models.ForeignKey(Application, related_name="comments")
    comment = models.TextField(blank=True, null=True)


class Invite(models.Model):
    class Meta:
        app_label = 'appntr'

    id = models.CharField(max_length=10, primary_key=True)
    application = models.OneToOneField(Application, null=True, default=None, related_name="invite")
    added_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    reminded_at = models.DateTimeField(blank=True, null=True, default=None)


class Appointment(models.Model):
    class Meta:
        app_label = 'appntr'

    datetime = models.DateTimeField()
    application = models.OneToOneField(Application, related_name="appointment")
    interview_lead = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="leading")
    interview_snd = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="second")  


    @property
    def link(self):
        if self.interview_lead.config.zoom_id:
            return "https://zoom.us/j/{}".format(self.interview_lead.config.zoom_id)

        return URL_BUILDER.format(self.application.invite.id)


class UserConfig(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="config", on_delete=models.CASCADE)
    can_lead = models.BooleanField(default=False)
    zoom_id = models.CharField(blank=True, null=True, max_length=100)