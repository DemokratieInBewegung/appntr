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

from . import loomio
from .helpers import update_application
import re

import random
from uuid import uuid4

URL_BUILDER = "https://talky.io/dib-bw-{}"
from .models import *
from . import admin


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
                'robot@bewegung.jetzt',
                [apt.invite.email],
                headers={
                    'Message-Id': "X-{}".format(invite.id),
                    'Cc': ','.join([lead.email, snd.email])
                }
            ).send()


            
            EmailMessage(
                'Termin mit {} (Bewerbungsgespräch)'.format(apt.name),
                render_to_string('email_interviewers.txt', context=dict(apt=apt)),
                'robot@bewegung.jetzt',
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
@user_passes_test(lambda u: u.is_staff)
def set_state(request, state, id):
    app = get_object_or_404(Application, pk=id)
    app.state = state
    app.save()
    return redirect("/applications/")


@login_required
@user_passes_test(lambda u: u.is_staff)
def direct_invite(request):
    ctx = {"form": DirectInvite()}

    if request.method == "POST":

        form = DirectInvite(request.POST)
        if form.is_valid():
            invite = form.save()

            try:
                app = Application.objects.get(email=invite.email)
            except Application.DoesNotExist:
                pass
            else:
                invite.app = app
                invite.extra_info += "\n\n\n" + app.personal_content
                app.state = Application.STATES.INVITED

                invite.save()
                app.save()

            EmailMessage(
                    'Einladung zum Gespräch mit Demokratie in Bewegung',
                    render_to_string('email_invite.txt', context=dict(invite=invite)),
                    'robot@bewegung.jetzt',
                    [invite.email],
                    reply_to=("bewerbungs-hilfe@demokratie-in-bewegung.org",)
                ).send()


            ctx["message"] = "Invite an {} ({}) geschickt".format(invite.name, invite.email)
        else:
            ctx["form"] = form

    return render(request, 'direct_invite.html', ctx)


@login_required
@user_passes_test(lambda u: u.is_staff)
def decline(request, id):
    app = get_object_or_404(Application, pk=id)

    EmailMessage(
            'Ihre Bewerbung bei Demokratie in Bewegung',
            render_to_string('email_decline.txt', context=dict(app=app)),
            'robot@bewegung.jetzt',
            [app.email],
            reply_to=("bewerbungs-hilfe@demokratie-in-bewegung.org",)
        ).send()

    app.state = Application.STATES.DECLINED
    app.save()
    return redirect("/applications/")


@login_required
@user_passes_test(lambda u: u.is_staff)
def applications(request):
    ctx = {}
    if request.method == "POST":
        app = get_object_or_404(Application, pk=request.POST.get("id"))

        if app.state == Application.STATES.INBOX:
            app.state = Application.STATES.ANON_VOTE
            app.save()

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
                app.save()
                ctx["message"] = "Bewerbung '{}' in anonyme Abstimmung verschoben".format(app.anon_name)
        else:
            ctx["message"] = "Bewerbung '{}' schon verschoben".format(app.anon_name)


    apps = [{"id": a.id, "name": a.anon_name, "form": AnonForm(instance=a)}
         for a in sorted(Application.objects.filter(state=Application.STATES.INBOX),
                         key=lambda a: a.priority, reverse=True)]
    ctx["applications"] = apps
    return render(request, "applications.html", context=ctx)