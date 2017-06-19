from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Application, UserVote, Invite, Timeslot, Appointment, UserConfig

admin.site.register(Application)
admin.site.register(UserVote)
admin.site.register(Invite)
admin.site.register(Timeslot)
admin.site.register(Appointment)



class UserConfigInline(admin.StackedInline):
    model = UserConfig
    can_delete = False
    verbose_name_plural = 'config'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserConfigInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)