from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.db.models import Q
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.core.mail import EmailMessage


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


    def __str__(self):
        try:
            return "☑️ Invite: {} ({}) angenommen für {}".format(self.name, self.email, self.appointment.datetime)
        except:
            return "✉️ Invite: {} ({}) nicht angenommen".format(self.name, self.email)



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


@receiver(post_save, sender=Invite, dispatch_uid="send_invite")
def send_invite(sender, instance, **kwargs):
    
    EmailMessage(
            'Einladung zum Gespräch mit Demokratie in Bewegung',
            render_to_string('email_invite.txt', context=dict(invite=instance)),
            'robot@demokratie-in-bewegung.org',
            [instance.email],
            reply_to=("bewerbungs-hilfe@demokratie-in-bewegung.org",)
        ).send()


from django.contrib import admin
admin.site.register(Interviewer)
admin.site.register(Invite)
admin.site.register(Timeslot)
admin.site.register(Appointment)