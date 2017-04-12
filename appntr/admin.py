from django.contrib import admin
from .helpers import update_application
from . import loomio
from .models import *

LOOMIO_URL = "https://www.loomio.org/d/{key}/asdf"


class ApplicationeAdmin(admin.ModelAdmin):
    list_display = ['name', 'priority', 'vielfalt', 'state', 'changed_at']
    ordering = ['changed_at', 'anon_name', 'state']
    actions = ['move_on', 'send_invite']

    def send_invite(self, request, queryset):
        for app in queryset:
            if app.state != Application.STATES.TO_INVITE:
                self.message_user(request, "{} not invitable".format(app))
                continue

            dc = loomio.get_discussion(app.loomio_discussion_id)

            name = app.actual_name.split("(")[0].strip()
            email = app.email

            Invite(name=name, email=email,
                   external_url=LOOMIO_URL.format(**dc)).save()

            app.state = Application.STATES.INVITED
            app.save()

            self.message_user(request, "{} eingeladen".format(app))


    send_invite.short_description = "Invite this application"

    def move_on(self, request, queryset):
        for app in queryset:
            self.message_user(request, update_application(app))

    move_on.short_description = "Move to next Step"


class InviteAdmin(admin.ModelAdmin):
    list_display = ['state', 'name', 'email', 'appointment']


admin.site.register(Interviewer)
admin.site.register(Application, ApplicationeAdmin)
admin.site.register(Invite, InviteAdmin)
admin.site.register(Timeslot)
admin.site.register(Appointment)
admin.site.register(CfgOption)