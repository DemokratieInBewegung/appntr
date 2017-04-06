from django.contrib import admin
from .helpers import update_application
from .models import *


class ApplicationeAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'changed_at']
    ordering = ['changed_at', 'anon_name', 'state']
    actions = ['move_on']

    def move_on(self, request, queryset):
        self.message_user(request,"".join([update_application(app)
            for app in queryset]))

    move_on.short_description = "Move to next Step"


admin.site.register(Interviewer)
admin.site.register(Application, ApplicationeAdmin)
admin.site.register(Invite)
admin.site.register(Timeslot)
admin.site.register(Appointment)
admin.site.register(CfgOption)