
from .models import Application
from django.conf import settings
from . import loomio

def update_application(app, force=False):
	
	proposal = loomio.get_proposal(app.loomio_cur_proposal_id)

	if not proposal['closed_at']:
		return "\n[s] {} noch nicht abgeschlossen".format(app.name)

	if proposal['voters_count'] < settings.MIN_VOTERS and not force:
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
			loomio.update_discussion(app.loomio_discussion_id, app.actual_name, app.personal_content)
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
			app.state = Application.STATES.TO_INVITE
			app.save()
			return "\n[✔] {name} accepted".format(app.name)
			# FIXME: send email to invite them for a discussion.

	elif result == 'abstain':
		loomio.move_discussion(app.loomio_discussion_id, settings.LOOMIO_BACKBURNER_GROUP)
		app.state = Application.STATES.BACKBURNER
		app.save()
		return "\n[⭕] {} warm gehalten".format(app.name)

	else:
		loomio.move_discussion(app.loomio_discussion_id, settings.LOOMIO_REJECTED_GROUP)
		app.state = Application.STATES.REJECTED
		app.save()
		return "\n[❌] {} fliegt raus".format(app.name)