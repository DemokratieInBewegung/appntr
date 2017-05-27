from django.contrib import admin
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .helpers import update_application, invite_application, decline_application
from . import loomio
from .models import *


class ApplicationeAdmin(admin.ModelAdmin):
    list_display = ['name', 'priority', 'vielfalt', 'state', 'changed_at']
    ordering = ['changed_at', 'anon_name', 'state']
    actions = ['move_on', 'send_invite', 'decline']
    search_fields = ['actual_name', 'personal_content']


    def decline(self, request, queryset):
        for app in queryset:
            if app.state not in (Application.STATES.REJECTED,
                                 Application.STATES.INVITED,
                                 Application.STATES.INBOX,
                                 Application.STATES.BACKBURNER):
                self.message_user(request, "{} can not be rejected".format(app))
                continue

            decline_application(app);

            self.message_user(request, "{} abgelehnt".format(app))


    decline.short_description = "Decline this application"


    def send_invite(self, request, queryset):
        for app in queryset:
            if app.state != Application.STATES.TO_INVITE:
                self.message_user(request, "{} not invitable".format(app))
                continue

            invite_application(app)
            self.message_user(request, "{} eingeladen".format(app))


    send_invite.short_description = "Invite this application"

    def move_on(self, request, queryset):
        for app in queryset:
            self.message_user(request, update_application(app))

    move_on.short_description = "Move to next Step"



class InviteAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'bundesland','when', 'state',  'added_at', 'reminded_at', 'appointment']

    actions = ['send_reminder', 'reset']

    def when(self, item):
        return item.appointment.datetime if item.appointment else None

    def bundesland(self, item):
        return item.application.bundesland if item.application else None

    def reset(self, request, queryset):
        for invite in queryset:
            invite.appointment.delete()

            EmailMessage(
                    'Einladung zum Gespräch mit Demokratie in Bewegung - Bitte neuen Termin wählen',
                    render_to_string('email_invite.txt', context=dict(invite=invite)),
                    'robot@bewegung.jetzt',
                    [invite.email],
                    reply_to=("bewerbungs-hilfe@demokratie-in-bewegung.org",)
                ).send()

            # invite.reminded_at = datetime.utcnow()
            # invite.save()

            self.message_user(request, "{} Neue Terminanfrage versand".format(invite))

    reset.short_description = "Neuen Termin ausmachen"


    def send_reminder(self, request, queryset):
        for invite in queryset:
            if invite.state != "open":
                self.message_user(request, "{} already accepted".format(invite))
                continue

            if invite.reminded_at:
                self.message_user(request, "{} already reminded".format(invite))
                continue

            EmailMessage(
                    'Einladung zum Gespräch mit Demokratie in Bewegung',
                    render_to_string('email_reminder.txt', context=dict(invite=invite)),
                    'robot@bewegung.jetzt',
                    [invite.email],
                    reply_to=("bewerbungs-hilfe@demokratie-in-bewegung.org",)
                ).send()

            invite.reminded_at = datetime.utcnow()
            invite.save()

            self.message_user(request, "{} Erinnerung versand".format(invite))

    send_reminder.short_description = "Send Reminder"



class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['datetime', 'name', 'email', 'interview_lead', 'interview_snd']

    search_fields = ["invite__name", "invite__email"]



admin.site.register(Interviewer)
admin.site.register(Application, ApplicationeAdmin)
admin.site.register(Invite, InviteAdmin)
admin.site.register(Timeslot)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(CfgOption)