from django.core.management.base import BaseCommand, CommandError
from datetime import datetime, timedelta
from django.conf import settings
from appntr.models import Application
from appntr.helpers import invite_application

class Command(BaseCommand):
    help = "Automatically move items to the next step"

    def handle(self, *args, **options):
        print("Refreshing")

        for app in Application.objects.filter(state=Application.STATES.TO_INVITE):
            print(invite_application(app))

        print("Done")