from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.db.models import Q
from django.db import models, IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from uuid import uuid4

import re


class CfgOption(models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    value = models.CharField(max_length=1024, null=True, blank=True)

    def __str__(self):
        return self.key

class Interviewer(models.Model):
    class Meta:
        app_label = 'appntr'

    id = models.CharField(max_length=10, primary_key=True)
    email = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def upcoming(self):
        just_before = datetime.utcnow() - timedelta(hours=1)
        return Appointment.objects.filter(Q(interview_lead=self) | Q(interview_snd=self)
                ).filter(datetime__gte=just_before).order_by("-datetime").all()


class Application(models.Model):
    class Meta:
        app_label = 'appntr'

    class STATES:
        INBOX = "inbox"
        ANON_VOTE = "anon_vote"
        PERSON_VOTE = "person_vote"
        TO_INVITE = "to_invite"
        INVITED = "invited"
        ACCEPTED = "accepted"
        REJECTED = "rejected"
        BACKBURNER = "backburner"


    added_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    state = models.CharField(max_length=25, choices= [
        (STATES.INBOX, "Incoming"),
        (STATES.ANON_VOTE, "In Voting (anon)"),
        (STATES.PERSON_VOTE, "In Voting (person)"),
        (STATES.TO_INVITE, "To invite"),
        (STATES.INVITED, "Invited"),
        (STATES.ACCEPTED, "Accepted"),
        (STATES.REJECTED, "Rejected"),
        (STATES.BACKBURNER, "on Backburner")
    ], default=STATES.INBOX)
    # actual application 
    anon_name = models.CharField(max_length=255)
    anon_content = models.TextField()
    actual_name = models.CharField(max_length=255)
    personal_content = models.TextField()
    contact_details = models.TextField()
    email = models.CharField(max_length=255)

    # external tracking
    loomio_discussion_id = models.CharField(max_length=25, blank=True, null=True)
    loomio_cur_proposal_id = models.CharField(max_length=25, blank=True, null=True)

    def __str__(self):
        return "{}@{}".format(self.name, self.state)

    @property
    def bundesland(self):
        try:
            return self.anon_content.split("für")[1].strip()
        except IndexError:
            return None

    @property
    def vielfalt(self):
        vielfalt = re.search(r"^Vielfalt: (.+)$", self.personal_content, re.MULTILINE)
        if vielfalt:
            return vielfalt.groups()[0]
        return None

    @property
    def priority(self):
        prio = (datetime.utcnow() - self.changed_at.replace(tzinfo=None)).days + 1
        bundesland = self.bundesland;
        if bundesland in ('Bremen', 'Thüringen', 'Saarland'):
            prio += 5
        elif bundesland in ('Mecklenburg-Vorpommern', 'Sachsen-Anhalt', 'Brandenburg'):
            prio += 3
        elif bundesland in ('Sachsen', 'Rheinland-Pfalz', 'Schleswig-Holstein'):
            prio += 2
        elif bundesland in ('Hessen', 'Niedersachen', 'Bayern'):
            prio += 1

        if not re.search(r"^Geschlecht: Männlich$", self.personal_content, re.MULTILINE):
            prio *= 2

        if self.vielfalt:
            prio *= 3

        return prio


    @property
    def name(self):
        if self.state in (Application.STATES.ANON_VOTE, Application.STATES.INBOX):
            return self.anon_name
        return self.actual_name


class Timeslot(models.Model):
    class Meta:
        app_label = 'appntr'
    once = models.BooleanField(default=True)
    datetime = models.DateTimeField()
    interviewer = models.ForeignKey(Interviewer, related_name="slots")

    def __str__(self):
        return "Slot: {}@{}".format(self.interviewer.name, self.datetime)


class Invite(models.Model):
    class Meta:
        app_label = 'appntr'

    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    external_url = models.CharField(max_length=1024)
    added_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    reminded_at = models.DateTimeField(blank=True, null=True, default=None)

    @property
    def state(self):
        try:
            self.appointment.datetime
            return "accepted"
        except:
            return "open"

    def __str__(self):
        try:
            return "☑️ Invite: {} ({}) angenommen für {}".format(self.name, self.email, self.appointment.datetime)
        except:
            return "✉️ Invite: {} ({}) nicht angenommen".format(self.name, self.email)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid4().hex[:8]

        while True:
            try:
                return super(Invite, self).save(*args, **kwargs)
            except IntegrityError:
                self.id = uuid.uuid4().hex[:8]



class Appointment(models.Model):
    class Meta:
        app_label = 'appntr'

    id = models.CharField(max_length=10, primary_key=True)
    link = models.CharField(max_length=255)
    datetime = models.DateTimeField()
    invite = models.OneToOneField(Invite, related_name="appointment")
    interview_lead = models.ForeignKey(Interviewer, related_name="leading")
    interview_snd = models.ForeignKey(Interviewer, related_name="second")  

    def __str__(self):
        return "Termin: {}@{}".format(self.name, self.datetime)

    @property
    def name(self):
        return self.invite.name

    @property
    def email(self):
        return self.invite.email
