
from .models import Application
from django.conf import settings
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .models import *
from . import loomio

def update_application(app, force=False):
	
	proposal = loomio.get_proposal(app.loomio_cur_proposal_id)

	if not proposal['closed_at']:
		return "\n[s] {} noch nicht abgeschlossen".format(app.name)

	if proposal['stances_count'] < settings.MIN_VOTERS and not force:
		prp = loomio.create_proposal(app.loomio_discussion_id,
									"{} interviewen".format(app.name),
									datetime.utcnow() + timedelta(hours=24),
									description="Erneutes Voting über 24h, da weniger als {} abgestimmt haben".format(settings.MIN_VOTERS))
		app.loomio_cur_proposal_id = prp['id']
		app.save()
		return "\n[🔄] {} um 24 verlängert".format(app.name)
		

	result = loomio.calc_result(proposal)

	if result == 'yes':
		if app.state == Application.STATES.ANON_VOTE:
			# flip the card:
			loomio.update_discussion(app.loomio_discussion_id, app.actual_name[:149], app.personal_content)
			prp = loomio.create_proposal(app.loomio_discussion_id,
										"{} interviewen".format(app.actual_name),
										datetime.utcnow() + timedelta(hours=24))
			app.loomio_cur_proposal_id = prp['id']
			app.state = Application.STATES.PERSON_VOTE
			app.save()
			return "\n[➰] {} -> {}".format(app.anon_name, app.actual_name)
		else:
			# We've been in the personal vote. Let's accept them
			loomio.move_discussion(app.loomio_discussion_id, settings.LOOMIO_ACCEPTED_GROUP)
			invite_application(app)
			return "\n[✔] {} eingeladen".format(app.name)

	elif result == 'abstain':
		loomio.move_discussion(app.loomio_discussion_id, settings.LOOMIO_REJECTED_GROUP)
		decline_application(app)
		return "\n[❌] {} abgelehnt".format(app.name)

	else:
		loomio.move_discussion(app.loomio_discussion_id, settings.LOOMIO_REJECTED_GROUP)
		decline_application(app)
		return "\n[❌] {} abgelehnt".format(app.name)

def decline_application(app):
    EmailMessage(
            'Ihre Bewerbung bei Demokratie in Bewegung',
            render_to_string('email_decline.txt', context=dict(app=app)),
            'robot@demokratie-in-bewegung.org',
            [app.email],
            reply_to=("bewerbungs-hilfe@demokratie-in-bewegung.org",)
        ).send()

    app.state = Application.STATES.DECLINED
    app.save()
    return app


def invite_application(app):

    name = app.real_name
    email = app.email

    inv_info = dict(name=name, email=email, application=app)

    if app.loomio_discussion_id:
        dc = loomio.get_discussion(app.loomio_discussion_id)
        inv_info['external_url'] = LOOMIO_URL.format(**dc)

    else:
        inv_info['extra_info'] = app.personal_content


    invite = Invite(**inv_info)
    invite.save()

    EmailMessage(
            'Einladung zum Gespräch mit Demokratie in Bewegung',
            render_to_string('email_invite.txt', context=dict(invite=invite)),
            'robot@demokratie-in-bewegung.org',
            [invite.email],
            reply_to=("bewerbungs-hilfe@demokratie-in-bewegung.org",)
        ).send()

    app.state = Application.STATES.INVITED
    app.save()
    return app