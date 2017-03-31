from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.db.models import Q
from django.db import models



class Interviewer(models.Model):
    class Meta:
        app_label = 'appntr'
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

class Appointment(models.Model):
    class Meta:
        app_label = 'appntr'
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    link = models.CharField(max_length=255)
    datetime = models.DateTimeField()
    interview_lead = models.ForeignKey(Interviewer, related_name="leading")
    interview_snd = models.ForeignKey(Interviewer, related_name="second")  


    def __str__(self):
        return "Termin: {}@{}".format(self.name, self.datetime)



from django.contrib import admin
admin.site.register(Interviewer)
admin.site.register(Timeslot)
admin.site.register(Appointment)