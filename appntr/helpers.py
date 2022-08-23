
from .models import Application
from django.conf import settings
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.sites.models import Site
from .models import *
from uuid import uuid4


BALANCE_GENDERS = ['Mann', 'mann', 'männlich', "Männlich"]
ACCEPTED_RATIO = 0.0
MAX_WAIT = timedelta(days=0) # we postpone max 0 days


def decline_application(app):
    EmailMessage(
            'Ihr Mitgliedsantrag bei DiB - DEMOKRATIE IN BEWEGUNG',
            render_to_string('email/decline.txt', context=dict(app=app)),
            settings.DEFAULT_FROM_EMAIL,
            [app.email],
            reply_to=(settings.REPLY_TO_EMAIL,)
        ).send()

    app.state = Application.STATES.REJECTED
    app.save()


def _calc_ratio():
	base_query = Application.objects.filter(state__in=[Application.STATES.INVITED, Application.STATES.INTERVIEWING])
	gender_query = base_query.filter(gender__in=BALANCE_GENDERS)
	return gender_query.count() / (base_query.count() or 1)


def invite_application(app, force=False):

    if app.state not in [Application.STATES.TO_INVITE, Application.STATES.NEW]:
    	raise NotImplemented

    if not force and app.gender in BALANCE_GENDERS and app.changed_at + MAX_WAIT > now():
    	cur_ratio = _calc_ratio()
    	if cur_ratio > ACCEPTED_RATIO:
    		if app.state == Application.STATES.NEW:
    			app.state = Application.STATES.TO_INVITE
    			app.save()
    		return "Skipping invite to fix the gender balance ratio."
    	# lets check against

    site = Site.objects.get_current()
    invite = Invite(application=app, id=uuid4().hex[:10])
    invite.save()

    EmailMessage(
            'Einladung zum Gespräch mit DiB - DEMOKRATIE IN BEWEGUNG',
            render_to_string('email/invite.txt', context=dict(domain=site.domain, app=app, invite=invite)),
            settings.DEFAULT_FROM_EMAIL,
            [app.email],
            reply_to=(settings.REPLY_TO_EMAIL,)
        ).send()

    app.state = Application.STATES.INVITED
    app.save()
    return "Eingeladen."