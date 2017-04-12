from django.core.management.base import BaseCommand, CommandError
from datetime import datetime, timedelta
from django.conf import settings
from appntr import loomio
from appntr.models import Application
from appntr.helpers import update_application

class Command(BaseCommand):
    help = "Automatically move items to the next step"

    def handle(self, *args, **options):
        print("Refreshing")

        for discussion in loomio.get_vote_ended():
            try:
                app = Application.objects.get(loomio_discussion_id=discussion['id'])
            except:
                print("\nSkipping: {id}, {title} -- unknown".format(**discussion))
                continue

            print(update_application(app))

        print("Done")