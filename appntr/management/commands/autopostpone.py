from django.core.management.base import BaseCommand, CommandError
from datetime import datetime, timedelta
from django.conf import settings
from appntr import loomio

class Command(BaseCommand):
    help = "Automatically postpone proposals if closing soon and haven't enough votes yet"

    def handle(self, *args, **options):

        next_time = datetime.utcnow() + timedelta(hours=settings.LOOMIO_POSTPONE_BY_HOURS)
        max_end_time = datetime.utcnow() + timedelta(hours=2)
        print("Refreshing")
        for discussion, proposal in loomio.get_votes_need_postponing(max_end_time):
            loomio.postpone_proposal(proposal['id'], next_time)
            print("{id} ({title}) postponed".format(**discussion))

        print("Done")

