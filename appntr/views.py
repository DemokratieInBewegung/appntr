from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.dateparse import parse_datetime
from django.contrib import messages
from django.conf import settings
from django.forms import ModelForm
from django import forms
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from collections import defaultdict
from django.core.mail import EmailMessage
from django.http import HttpResponse, StreamingHttpResponse


import re

import random
from uuid import uuid4

URL_BUILDER = "https://talky.io/dib-bw-{}"
from .models import *
from .admin import *


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


def _get_open_slots(minimum=24, tomorrow=None):

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
    return slots


def get_open_slots(minimum=24, tomorrow=None):
    return {k: v for k, v in _get_open_slots(minimum=minimum, tomorrow=tomorrow).items()
            if len(v) >= MINIMUM}


def get_recommended_slots(minimum=24, tomorrow=None):
    return {k: v for k, v in _get_open_slots(minimum=minimum, tomorrow=tomorrow).items()
            if len(v) % MINIMUM != 0}



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
    tomorrow = (datetime.utcnow() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)

    recoms = [x.replace(tzinfo=None) for x in get_recommended_slots().keys()]

    frames = []
    for x in range(14):
        d = tomorrow + timedelta(days=x)
        times = []
        for t in TIMES:
            slot = d.replace(hour=t[0], minute=t[1])
            times.append({
                    "slot": slot,
                    "checked": slot in availables,
                    "recommended": slot in recoms
                })

        frames.append({"day": d, "times": times})

    ctx["frames"] = frames;

    return render(request, 'interviewer.html', context=ctx)


def invite(request, id):

    invite = get_object_or_404(Invite, pk=id)
    app = invite.application

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
                'Termin für Gespräch mit Demokratie in Bewegung',
                render_to_string('email/confirm_appointment.txt', context=dict(apt=apt, app=app)),
                settings.DEFAULT_FROM_EMAIL,
                [app.email],
                headers={
                    'Message-Id': "X-{}".format(invite.id),
                    'Cc': ','.join([lead.email, snd.email])
                }
            ).send()


            
            EmailMessage(
                'Termin mit {} {} (Mitgliedsantragsgespräch)'.format(app.first_name, app.last_name),
                render_to_string('email/interviewers.txt', context=dict(apt=apt)),
                settings.DEFAULT_FROM_EMAIL,
                [lead.email, snd.email]
            ).send()

            return render(request, "confirm.html", context=dict(apt=apt))

        except KeyError:
            ctx["slots"] = slots
            ctx["message"] = "Zeitraum steht nicht zur Verfügung. Bitte einen anderen auswählen."

    else:
        ctx = dict(name=app.name, slots=sorted(get_open_slots().keys()))

    return render(request, "invite.html", context=ctx)


def index(request):
    return HttpResponse("🎉")


def min_length(value):
    if len(value) < 50:
        raise ValidationError('Geht es auch etwas ausführlicher?')


FB_GENDER = ['Mann', 'Frau', "androgyner Mensch","androgyn","bigender","weiblich","Frau zu Mann (FzM)",
             "gender variabel","genderqueer","intersexuell (auch inter*)","männlich","Mann zu Frau (MzF)",
             "weder noch","geschlechtslos","nicht-binär","weitere","Pangender","Pangeschlecht","trans",
             "transweiblich","transmännlich","Transmann","Transmensch","Transfrau","trans*","trans*weiblich",
             "trans*männlich","Trans*Mann","Trans*Mensch","Trans*Frau","transfeminin","Transgender",
             "transgender weiblich","transgender männlich","Transgender Mann","Transgender Mensch",
             "Transgender Frau","transmaskulin","transsexuell","weiblich-transsexuell","männlich-transsexuell",
             "transsexueller Mann","transsexuelle Person","transsexuelle Frau","Inter*","Inter*weiblich",
             "Inter*männlich","Inter*Mann","Inter*Frau","Inter*Mensch","intergender","intergeschlechtlich",
             "zweigeschlechtlich","Zwitter","Hermaphrodit","Two Spirit drittes Geschlecht","Viertes Geschlecht",
             "XY-Frau","Butch","Femme","Drag","Transvestit","Cross-Gender"]

STATES = ["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen",
          "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz",
          "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"]


class ListTextWidget(forms.TextInput):
    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.attrs.update({'list':'list__%s' % self._name})

    def render(self, name, value, attrs=None):
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name
        for item in self._list:
            data_list += '<option value="%s">' % item
        data_list += '</datalist>'

        return (text_html + data_list)


class ApplicationForm(ModelForm):

    motivation = forms.CharField(validators=[min_length],
                                 label="Was ist Deine Motivation Dich bei DiB zu engagieren?",
                                 widget=forms.Textarea)
    skills = forms.CharField(validators=[min_length],
                                 label="Welche Fähigkeiten, Erfahrungen und Ideen willst Du als Mitglied einbringen, die DiB nach vorne bringen werden?",
                                 widget=forms.Textarea)
    ethical_dilemma = forms.CharField(validators=[min_length],
                                 label="Was würdest Du tun, wenn die Beweger/innen und Mitglieder von Demokratie in Bewegung nach dem Initiativprinzip eine Programmentscheidung herbeiführen, die Du persönlich nicht unterstützt?",
                                 widget=forms.Textarea)

    class Meta:
        model = Application
        fields = ['motivation', 'skills', 'ethical_dilemma',
        'first_name', 'last_name', 'gender', 'country', 'email', 'phone', 'internet_profiles']

        widgets = {
            'gender': ListTextWidget(FB_GENDER, 'gender'),
            'country': ListTextWidget(STATES, 'country'),
            'email': forms.EmailInput()
        }


def applyform(request):
    ctx = dict()

    if request.method == "POST":

        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.state = Application.STATES.NEW
            application.save()


            EmailMessage(
                    'Eingangsbestätigung des Mitgliedsantrag bei Demokratie in Bewegung',
                    render_to_string('email/accepted_application.txt', context=dict(application=application)),
                    'keine-antwort@bewegung.jetzt',
                    [application.email],
                    reply_to=("mitgliedsantrag@bewegung.jetzt",)
                ).send()

            messages.success(request, "Danke sehr. Dein Antrag ist bei uns eingegangen.")

            form = ApplicationForm()

    else:
        form = ApplicationForm()

    ctx['form'] = form
    return render(request, "apply.html", context=ctx)


@login_required
def all_applications(request):
    ctx = dict(apps=Application.objects.order_by("-added_at"))
    return render(request, "apps/all.html", context=ctx)

@login_required
@require_POST
def vote(request, id):
    app = get_object_or_404(Application, pk=id)
    UserVote(application=app, user=request.user,
             comment=request.POST.get('comment'), vote=request.POST.get('vote')).save()

    messages.success(request, "Deine Abstimmung wurde aufgenommen.")
    return redirect(request, request.META.get('HTTP_REFERER') or '/applications/inbox')

    pass

@login_required
def inbox(request):
    ctx = dict(apps=Application.objects.exclude(id__in=UserVote.objects.filter(user=request.user)).order_by("added_at"
                ).filter(state=Application.STATES.NEW))
    return render(request, "apps/inbox.html", context=ctx)