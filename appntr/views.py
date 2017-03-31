from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from collections import defaultdict
from django.core.mail import send_mail

import random
from uuid import uuid4

from .models import *

MINIMUM = 2
URL_BUILDER = "https://talky.io/dib-bw-{}"


def get_open_slots(futureWeeks=2, minimum=24, tomorrow=None):
	if tomorrow is None:
		tomorrow = datetime.utcnow() + timedelta(hours=minimum)

	slots = defaultdict(list)
	for slot in Timeslot.objects.filter(once=True, datetime__gte=datetime.utcnow()):
		print(slot)
		slots[slot.datetime].append(slot.interviewer.id)

	print(slots)
	# filter out existing
	for appt in Appointment.objects.filter(datetime__gte=datetime.utcnow()):
		print(appt, slots[appt.datetime])
		if slots[appt.datetime]:
			try:
				slots[appt.datetime].remove(appt.interview_lead.id)
			except ValueError:
				pass
			try:
				slots[appt.datetime].remove(appt.interview_snd.id)
			except ValueError:
				pass
		print(slots[appt.datetime])

	return {k: v for k, v in slots.items() if len(v) >= MINIMUM}



def index(request):
	if request.method == "POST":
		ctx = dict(name=request.POST.get("name"),
				   email=request.POST.get("email"))

		dt = parse_datetime(request.POST.get("slot", ''))

		slots = get_open_slots()

		try:
			users = random.sample(slots[dt], 2)
			lead = Interviewer.objects.get(pk=users[0])
			snd = Interviewer.objects.get(pk=users[1])
			apt = Appointment(interview_lead=lead,
							  interview_snd=snd,
							  datetime=dt,
							  link=URL_BUILDER.format(uuid4().hex[:6]),
							  **ctx)
			apt.save()

			send_mail('Termin für Bewerbungsgespräch von {} mit Demokratie in Bewegung'.format(apt.name),
				    render_to_string('email.txt', context=dict(apt=apt)),
				    'robot@demokratie-in-bewegung.org',
				    [apt.email, lead.email, snd.email],
				    fail_silently=False,
				)

			return render(request, "confirm.html", context=dict(apt=apt))

		except KeyError:
			ctx["slots"] = slots
			ctx["message"] = "Zeitraum steht nicht zur Verfügung. Bitte einen anderen auswählen."

	else:
		ctx = dict(name=request.GET.get("name"),
				   slots=get_open_slots().keys(),
				   email=request.GET.get("email"))

	return render(request, "index.html", context=ctx)
