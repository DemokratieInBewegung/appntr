from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.db.models import Q
from django.conf import settings
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


STATES = [
]

class Application(models.Model):
    class Meta:
        app_label = 'appntr'

    class STATES:
        NEW = "new"
        TO_INVITE = "to_invite"
        INVITED = "invited"
        INTERVIEWING = "interview"
        ACCEPTED = "accepted"
        REJECTED = "rejected"


    added_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    state = models.CharField(max_length=25, choices= [
        (STATES.NEW, "new"),
        (STATES.TO_INVITE, "To invite"),
        (STATES.INVITED, "Invited"),
        (STATES.INTERVIEWING, "Being interviewed"),
        (STATES.ACCEPTED, "Accepted"),
        (STATES.REJECTED, "Rejected")
    ], default=STATES.NEW)
    # actual application 

    # personal data
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=30)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    country = models.CharField(max_length=25)
    internet_profiles = models.TextField(null=True, blank=True)

    # application
    motivation = models.TextField()
    skills = models.TextField()
    ethical_dilemma = models.TextField()

    def __str__(self):
        return "{}@{}".format(self.name, self.state)


class UserVote(models.Model):
    added_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="votes")
    application = models.ForeignKey(Application, related_name="votes")
    vote = models.CharField(max_length=1, choices=[('y', 'yay'), ('n', 'nay'), ('a', 'abstain')])

    class Meta:
        unique_together = (("user", "application"),)


class Timeslot(models.Model):
    class Meta:
        app_label = 'appntr'
    once = models.BooleanField(default=True)
    datetime = models.DateTimeField()
    interviewer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="slots")


class Invite(models.Model):
    class Meta:
        app_label = 'appntr'

    id = models.CharField(max_length=10, primary_key=True)
    application = models.ForeignKey(Application, null=True, default=None)
    added_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    reminded_at = models.DateTimeField(blank=True, null=True, default=None)
    extra_info = models.TextField(null=True, default=None)

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
    interview_lead = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="leading")
    interview_snd = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="second")  

    def __str__(self):
        return "Termin: {}@{}".format(self.name, self.datetime)

    @property
    def name(self):
        return self.invite.name

    @property
    def email(self):
        return self.invite.email
