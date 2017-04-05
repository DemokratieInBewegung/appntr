from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime
from django.conf import settings
from django.forms import ModelForm
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from collections import defaultdict
from django.core.mail import EmailMessage
from django.http import HttpResponse, StreamingHttpResponse
from . import loomio
import re

import random
from uuid import uuid4

URL_BUILDER = "https://talky.io/dib-bw-{}"
from .models import *

MIN_VOTERS = 5

MINIMUM = 2
TIMES = [(6, 0), (6, 30),
		 (7, 0), (7, 30),
		 (8, 0), (8, 30),
		 (9, 0), (9, 30),
		 (10, 0), (10, 30),
		 (11, 0), (11, 30),
		 (12, 0), (12, 30),
		 (13, 0), (13, 30),
		 (14, 0), (14, 30),
		 (15, 0), (15, 30),
		 (16, 0), (16, 30),
		 (17, 0), (17, 30),
		 (18, 0), (18, 30),
		 (19, 0), (19, 30),
		 (20, 0), (20, 30),
		 (21, 0), (21, 30),
		 (22, 0), (22, 30)]


def get_open_slots(minimum=24, tomorrow=None):
	if tomorrow is None:
		tomorrow = datetime.utcnow() + timedelta(hours=minimum)

	slots = defaultdict(list)
	for slot in Timeslot.objects.filter(once=True, datetime__gte=tomorrow):
		slots[slot.datetime].append(slot.interviewer.id)

	# filter out existing
	for appt in Appointment.objects.filter(datetime__gte=tomorrow):
		if slots[appt.datetime]:
			try:
				slots[appt.datetime].remove(appt.interview_lead.id)
			except ValueError:
				pass
			try:
				slots[appt.datetime].remove(appt.interview_snd.id)
			except ValueError:
				pass

	return {k: v for k, v in slots.items() if len(v) >= MINIMUM}


def edit(request, id):

	inter = get_object_or_404(Interviewer, pk=id)
	ctx = dict(interviewer=inter)

	if request.method == "POST":
		inter.name = request.POST.get("name", inter.name)
		inter.email = request.POST.get("email", inter.email)
		# clear slots
		Timeslot.objects.filter(interviewer=inter).delete()
		for slot in request.POST.getlist("slot"):
			parsed = parse_datetime(slot)
			Timeslot(interviewer=inter, datetime=slot, once=True).save()

	availables = [s.datetime.replace(tzinfo=None) for s in inter.slots.all()]
	tomorrow = (datetime.utcnow() + timedelta(days=1)).replace(minute=0, hour=0, second=0, microsecond=0)


	frames = []
	for x in range(14):
		d = tomorrow + timedelta(days=x)
		times = []
		for t in TIMES:
			slot = d.replace(hour=t[0], minute=t[1])
			times.append({
					"slot": slot,
					"checked": slot in availables
				})

		frames.append({"day": d, "times": times})

	ctx["frames"] = frames;

	return render(request, 'interviewer.html', context=ctx)


def invite(request, id):

	invite = get_object_or_404(Invite, pk=id)

	try:
		return render(request, "confirm.html", context=dict(apt=invite.appointment))
	except Invite.appointment.RelatedObjectDoesNotExist:
		pass


	if request.method == "POST":
		ctx = dict()

		dt = parse_datetime(request.POST.get("slot", ''))

		slots = get_open_slots()

		try:
			users = random.sample(slots[dt], 2)
			lead = Interviewer.objects.get(pk=users[0])
			snd = Interviewer.objects.get(pk=users[1])
			id = uuid4().hex[:6]
			apt = Appointment(id=id,
							  interview_lead=lead,
							  interview_snd=snd,
							  datetime=dt,
							  invite=invite,
							  link=URL_BUILDER.format(id))
			apt.save()

			EmailMessage(
				'Termin für Bewerbungsgespräch mit Demokratie in Bewegung',
			    render_to_string('email.txt', context=dict(apt=apt)),
			    'robot@demokratie-in-bewegung.org',
			    [apt.invite.email],
			    headers={
			    	'Message-Id': "X-{}".format(invite.id),
			    	'Cc': ','.join([lead.email, snd.email])
			    }
			).send()


			
			EmailMessage(
				'Termin mit {} (Bewerbungsgespräch)'.format(apt.name),
			    render_to_string('email_interviewers.txt', context=dict(apt=apt)),
			    'robot@demokratie-in-bewegung.org',
			    [lead.email, snd.email]
			).send()

			return render(request, "confirm.html", context=dict(apt=apt))

		except KeyError:
			ctx["slots"] = slots
			ctx["message"] = "Zeitraum steht nicht zur Verfügung. Bitte einen anderen auswählen."

	else:
		ctx = dict(name=invite.name, slots=sorted(get_open_slots().keys()))

	return render(request, "invite.html", context=ctx)


def index(request):
	return HttpResponse("🎉")



class AnonForm(ModelForm):
	class Meta:
	    model = Application
	    fields = ['anon_name', 'anon_content']


class IncomingForm(ModelForm):
	class Meta:
	    model = Application
	    fields = ['anon_name', 'anon_content', 'actual_name', 'personal_content', 'contact_details', 'email']


@csrf_exempt
def incoming(request):
	form = IncomingForm(request.POST)
	if form.save():
		return HttpResponse("ok")
	else:
		raise ValueError()


@login_required
@user_passes_test(lambda u: u.is_superuser)
def refresh_votes(request):
	vote_ended = loomio.get_vote_ended()
	missing = []
	def iterate():
		maximum = int(request.GET.get("max", 1000))
		yield "Refreshing..."
		for discussion in vote_ended:
			try:
				app = Application.objects.get(loomio_discussion_id=discussion['id'])
			except:
				missing.append(discussion)
				yield "\n[s] {id}, {title} -- unknown".format(**discussion)
				continue

			if not app.loomio_cur_proposal_id:
				missing.append(discussion)
				yield "\n[s] {id} {title} -- not managed by us".format(**discussion)
				continue

			proposal = loomio.get_proposal(app.loomio_cur_proposal_id)

			if proposal['voters_count'] < MIN_VOTERS:
				name = app.anon_name if app.state == Application.STATES.ANON_VOTE else app.actual_name
				prp = loomio.create_proposal(app.loomio_discussion_id,
											"{} interviewen".format(name),
											datetime.utcnow() + timedelta(hours=24),
											description="Erneutes Voting über 24h, da weniger als {} abgestimmt haben".format(MIN_VOTERS))
				app.loomio_cur_proposal_id = prp['id']
				app.save()
				yield "\n[🔄]{id}, {title} um 24 verlängert".format(**discussion)
				continue

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
					yield "\n[➰]{id}, {title} -> {actual_name}".format(actual_name=app.actual_name, **discussion)
				else:
					# We've been in the personal vote. Let's accept them
					loomio.move_discussion(app.loomio_discussion_id, settings.LOOMIO_ACCEPTED_GROUP)
					app.state = Application.STATES.ACCEPTED
					app.save()
					yield "\n[✔] {id}, {actual_name} accepted".format(actual_name=app.actual_name, **discussion)
					# FIXME: send email to invite them for a discussion.

			elif result == 'abstain':
				loomio.move_discussion(app.loomio_discussion_id, settings.LOOMIO_BACKBURNER_GROUP)
				app.state = Application.STATES.BACKBURNER
				app.save()
				yield "\n[⭕] {id}, {title} warm gehalten".format(**discussion)

			else:
				loomio.move_discussion(app.loomio_discussion_id, settings.LOOMIO_REJECTED_GROUP)
				app.state = Application.STATES.REJECTED
				app.save()
				yield "\n[❌] {id}, {title} fliegt raus".format(**discussion)

			maximum -= 1
			if maximum <= 0:
				break


		if missing:
			yield "\n------------------------------ Missing ---------------------------"
			for x in missing:
				yield "\n{id},{key},{title}".format(**missing)


	return StreamingHttpResponse(iterate(), status=200, content_type="text/plain;utf-8")


@login_required
@user_passes_test(lambda u: u.is_superuser)
def set_state(request, state, id):
	app = get_object_or_404(Application, pk=id)
	app.state = state
	app.save()
	return redirect("/applications/")


@login_required
@user_passes_test(lambda u: u.is_superuser)
def applications(request):
	ctx = {}
	if request.method == "POST":
		app = get_object_or_404(Application, pk=request.POST.get("id"))

		if AnonForm(request.POST, instance=app).save(commit=False):
			items = app.actual_name.split('"')
			if len(items) == 3:
				items[1] = app.anon_name
				app.actual_name = '"'.join(items)
			else:
				app.actual_name += ' ehemals "{}"'.format(app.anon_name)


			dsc = loomio.create_discussion(app.anon_name, app.anon_content)
			app.loomio_discussion_id = dsc['id']
			prp = loomio.create_proposal(app.loomio_discussion_id,
										"{} interviewen".format(app.anon_name),
										datetime.utcnow() + timedelta(hours=48))
			app.loomio_cur_proposal_id = prp['id']
			app.state = Application.STATES.ANON_VOTE
			app.save()
			ctx["message"] = "Bewerbung '{}' in anonyme Abstimmung verschoben".format(app.anon_name)

	apps = [{"id": a.id, "name": a.anon_name, "form": AnonForm(instance=a)}
		 for a in Application.objects.filter(state=Application.STATES.INBOX)]
	ctx["applications"] = apps
	return render(request, "applications.html", context=ctx)