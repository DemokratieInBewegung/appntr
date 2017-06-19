
from .models import Application
from django.conf import settings
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.sites.models import Site
from .models import *
from uuid import uuid4


def decline_application(app):
    EmailMessage(
            'Ihre Mitgliedsantrag bei Demokratie in Bewegung',
            render_to_string('email/decline.txt', context=dict(app=app)),
            settings.DEFAULT_FROM_EMAIL,
            [app.email],
            reply_to=(settings.REPLY_TO_EMAIL,)
        ).send()

    app.state = Application.STATES.REJECTED
    app.save()


def invite_application(app):

    if app.state not in [Application.STATES.TO_INVITE, Application.STATES.NEW]:
    	raise NotImplemented

    site = Site.objects.get_current()
    invite = Invite(application=app, id=uuid4().hex[:10])
    invite.save()

    EmailMessage(
            'Einladung zum Gespräch mit Demokratie in Bewegung',
            render_to_string('email/invite.txt', context=dict(domain=site.domain, app=app, invite=invite)),
            settings.DEFAULT_FROM_EMAIL,
            [app.email],
            reply_to=(settings.REPLY_TO_EMAIL,)
        ).send()

    app.state = Application.STATES.INVITED
    app.save()
    return app