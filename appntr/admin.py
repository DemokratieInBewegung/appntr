from django.contrib import admin
from .models import Application, UserVote, Invite, Timeslot, Appointment

admin.site.register(Application)
admin.site.register(UserVote)
admin.site.register(Invite)
admin.site.register(Timeslot)
admin.site.register(Appointment)
