from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.dateparse import parse_datetime
from django.contrib import messages
from django.contrib.sites.models import Site
from django.conf import settings
from django.forms import ModelForm
from django import forms
from datetime import datetime, timedelta
from django.template.loader import render_to_string
from collections import defaultdict
from django.core.mail import EmailMessage
from django.http import HttpResponse, StreamingHttpResponse

from .helpers import invite_application, decline_application


import re

import random
from uuid import uuid4

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
    leads = [x['user_id'] for x in UserConfig.objects.filter(can_lead=True).values('user_id')]
    return (leads, {k: v for k, v in _get_open_slots(minimum=minimum, tomorrow=tomorrow).items()
            if len(v) >= MINIMUM and any(i for i in v if i in leads)} if leads else {})


def get_recommended_slots(minimum=24, tomorrow=None):
    return {k: v for k, v in _get_open_slots(minimum=minimum, tomorrow=tomorrow).items()
            if len(v) % MINIMUM != 0}


@login_required
def my_appointments(request):
    ctx = _make_context(request, menu='appointments')
    base_query = ctx['appointments_base_query']
    ctx.update(dict(
        upcoming=base_query.filter(datetime__gte=datetime.today()),
        past=base_query.filter(datetime__lt=datetime.today())
        ))
    return render(request, 'interviews/my_appointments.html', context=ctx)



@login_required
def manage_slots(request):
    inter = request.user
    ctx = _make_context(request, interviewer=inter, menu='slots')

    if request.method == "POST":
        inter.first_name = request.POST.get("first_name", inter.first_name)
        inter.last_name = request.POST.get("last_name", inter.last_name)
        inter.email = request.POST.get("email", inter.email)
        inter.save()
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

    return render(request, 'interviews/manage_slots.html', context=ctx)


def invite(request, id):

    invite = get_object_or_404(Invite, pk=id)
    app = invite.application

    try:
        return render(request, "interviews/confirm.html", context=dict(apt=app.appointment))
    except Application.appointment.RelatedObjectDoesNotExist:
        pass


    if request.method == "POST":
        ctx = dict()

        dt = parse_datetime(request.POST.get("slot", ''))

        leads, slots = get_open_slots()
        site = Site.objects.get_current()

        try:
            lead_id = next(i for i in slots[dt] if i in leads)
            # second preference is non-leads, but we take any otherwise
            snd_id = next(i for i in slots[dt] if i not in leads) or next(i for i in slots[dt] if i != lead_id)
            lead = get_user_model().objects.get(pk=lead_id)
            snd = get_user_model().objects.get(pk=snd_id)
            id = uuid4().hex[:6]
            apt = Appointment(interview_lead=lead,
                              interview_snd=snd,
                              datetime=dt,
                              application=app)
            apt.save()

            EmailMessage(
                'Termin für Gespräch mit Demokratie in Bewegung',
                render_to_string('email/confirm_appointment.txt', context=dict(domain=site.domain, apt=apt, app=app)),
                settings.DEFAULT_FROM_EMAIL,
                [app.email],
                headers={
                    'Message-Id': "X-{}".format(invite.id),
                    'Cc': ','.join([lead.email, snd.email])
                }
            ).send()

            
            EmailMessage(
                'Termin mit {} {} (Mitgliedsantragsgespräch)'.format(app.first_name, app.last_name),
                render_to_string('email/interviewers.txt', context=dict(domain=site.domain, apt=apt, app=app)),
                settings.DEFAULT_FROM_EMAIL,
                [lead.email, snd.email],
                headers={
                    'Message-Id': "X-{}".format(invite.id),
                }
            ).send()

            app.state = app.STATES.INTERVIEWING
            app.save()

            return render(request, "interviews/confirm.html", context=dict(apt=apt))

        except KeyError:
            ctx["slots"] = slots
            ctx["message"] = "Zeitraum steht nicht zur Verfügung. Bitte einen anderen auswählen."

    else:
        ctx = dict(name=app.first_name, slots=sorted(get_open_slots()[1].keys()))

    return render(request, "interviews/invite.html", context=ctx)


def index(request):
    # if request.user.is_authenticated:
    return redirect('inbox')
    # return HttpResponse("🎉")


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

    diversity = forms.BooleanField(required=True,
                    label=mark_safe('Wir leben in leider in einer Gesellschaft mit struktureller Diskriminierung und Benachteiligung. Deswegen finde ich es gut, dass sich DiB strukturelle Maßnahmen gibt, dem gegen zu wirken und will diese voll und ganz unterstützen.'))

    ethic_codex = forms.BooleanField(required=True,
                    label=mark_safe('Ich habe den <a href="https://bewegung.jetzt/ethik-kodex/" target="_blank">Ethik-Kodex</a> gelesen und bin bereit ihn zu unterzeichnen.'))

    comm_rules = forms.BooleanField(required=True,
                    label=mark_safe('Ich habe die in der Satzung festgelegten <a href="https://bewegung.jetzt/wp-content/uploads/2017/05/AnhangzurSatzungVerhaltens-Kodex-vom29.April2017.pdf" target="_blank">Verhaltensregel</a> und <a href="https://docs.google.com/document/d/1_6vpN3qkpGe7ef3lgBybkByH7WybKe9-GvVYQRjNxkY/edit?usp=sharing" target="_blank">die internen Kommunikationsregel</a> vernommen und bin bereit mich daran zu halten.'))

    class Meta:
        model = Application
        fields = ['motivation', 'skills', 'ethical_dilemma',
                  'first_name', 'last_name', 'gender', 'country', 'email', 'phone',
                  'internet_profiles', 'affiliations',
                  'ethic_codex', 'diversity', 'comm_rules']

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
                    settings.DEFAULT_FROM_EMAIL,
                    [application.email],
                    reply_to=("mitgliedsantrag@bewegung.jetzt",)
                ).send()

            messages.success(request, "Danke sehr. Dein Antrag ist bei uns eingegangen.")

            form = ApplicationForm()

    else:
        form = ApplicationForm()

    ctx['form'] = form
    return render(request, "apply.html", context=ctx)


def _make_context(request, menu='all', **kwargs):
  base_query = Appointment.objects.filter(Q(interview_lead=request.user) | Q(interview_snd=request.user))
    
  kwargs.update(dict(
      menu=menu,
      appointments_base_query=base_query.order_by('-datetime'),
      appointments_count=base_query.filter(datetime__gte=datetime.today()).count(),
      inbox_count=Application.objects.exclude(id__in=UserVote.objects.filter(user=request.user).values('application_id')).order_by("added_at"
                ).filter(state=Application.STATES.NEW).count()
    ))
  return kwargs


@login_required
def show_application(request, id):
    app = get_object_or_404(Application, pk=id)
    ctx = _make_context(request, menu='all', app=app, my_vote=None)
    try:
      ctx['my_vote'] = app.votes.get(user__id=request.user.id).vote
    except UserVote.DoesNotExist:
      pass
    ctx['show_contact_details'] = request.user.is_staff or app.state in [Application.STATES.TO_INVITE, Application.STATES.INVITED, Application.STATES.INTERVIEWING]
    
    try:
        ctx['can_reset_appointment'] = request.user.is_staff or \
                                       app.appointment.interview_lead == request.user or \
                                      app.appointment.interview_snd == request.user
    except Application.appointment.RelatedObjectDoesNotExist:
        ctx['can_reset_appointment'] = False

    return render(request, "apps/show.html", context=ctx)


@login_required
def all_applications(request):
    ctx = _make_context(request, menu='all', apps=Application.objects.order_by("-added_at"))
    return render(request, "apps/all.html", context=ctx)


@login_required
@require_POST
def vote(request, id):
    app = get_object_or_404(Application, pk=id)

    if app.state != Application.STATES.NEW:
      messages.error(request, "Es kann nicht mehr abgestimmt werden.")
      return redirect(request.META.get('HTTP_REFERER') or '/applications/inbox')

    try:
      vote = UserVote.objects.get(application=app, user=request.user)
      vote.vote = request.POST.get('vote')
      vote.save()
    except UserVote.DoesNotExist:
      UserVote(application=app, user=request.user,vote=request.POST.get('vote')).save()

    if request.POST.get('comment'):
      Comment(application=app, user=request.user, comment=request.POST.get('comment')).save()


    winner = app.winner
    if winner:
        if winner == 'yay':
            invite_application(app)
        elif winner == 'nay':
            decline_application(app)
        # on abstain we wait for more votes for now...

    messages.success(request, "Deine Abstimmung wurde aufgenommen.")
    return redirect(request.META.get('HTTP_REFERER') or '/applications/inbox')


@login_required
@require_POST
def comment(request, id):
    app = get_object_or_404(Application, pk=id)
    Comment(application=app, user=request.user, comment=request.POST.get('comment')).save()

    messages.success(request, "Kommentar erstellt.")
    return redirect(request.META.get('HTTP_REFERER') or '/applications/{}'.format(id))


@login_required
@require_POST
@user_passes_test(lambda u: u.is_staff)
def direct_invite(request, id):
    app = get_object_or_404(Application, pk=id)
    resp = invite_application(app, force=True)

    if app.state == Application.STATES.INVITED:
        messages.success(request, resp)
    else:
        messages.warning(request, resp)
    return redirect(request.META.get('HTTP_REFERER') or '/applications/{}'.format(id))


@login_required
@require_POST
def reset_appointment(request, id):
    app = get_object_or_404(Application, pk=id)
    apt = app.appointment
    site = Site.objects.get_current()
    if not request.user.is_staff and not apt.interview_lead == request.user \
        and not apt.interview_snd == request.user:
      messages.error(request, "Darfste nicht")
      return redirect(request.META.get('HTTP_REFERER') or '/applications/{}'.format(id))


    # if apt.datetime > datetime.now():
    #     EmailMessage(
    #         'ABGESAGT: Termin mit {} {}'.format(app.first_name, app.last_name),
    #         render_to_string('email/interviewers_reset.txt', context=dict(domain=site.domain, apt=apt, app=app)),
    #         settings.DEFAULT_FROM_EMAIL,
    #         [apt.interview_lead.email, apt.interview_snd.email],
    #         headers={
    #             'In-Reply-To': "X-{}".format(app.invite.id),
    #         }
    #     ).send()


    EmailMessage(
        'Termin für Gespräch mit Demokratie in Bewegung zurückgesetzt',
        render_to_string('email/reset.txt', context=dict(domain=site.domain, apt=apt, app=app)),
        settings.DEFAULT_FROM_EMAIL,
        [app.email],
        headers={
            'In-Reply-To': "X-{}".format(app.invite.id)
        }
    ).send()


    app.appointment.delete()
    app.state = Application.STATES.INVITED
    app.save()
    messages.success(request, "Termin zurückgesetzt")
    return redirect(request.META.get('HTTP_REFERER') or '/applications/{}'.format(id))


@login_required
@require_POST
@user_passes_test(lambda u: u.is_staff)
def trash_app(request, id):
    messages.success(request, "Macht noch nix.")
    return redirect(request.META.get('HTTP_REFERER') or '/applications/{}'.format(id))



@login_required
@require_POST
@user_passes_test(lambda u: u.is_staff)
def direct_decline(request, id):
    app = get_object_or_404(Application, pk=id)
    decline_application(app)
    messages.success(request, "Abgelehnt.")
    return redirect(request.META.get('HTTP_REFERER') or '/applications/{}'.format(id))



@login_required
def inbox(request):
    ctx = _make_context(request,
        menu='inbox',
        apps=Application.objects.exclude(id__in=UserVote.objects.filter(user=request.user).values('application_id')).order_by("added_at"
                ).filter(state=Application.STATES.NEW))
    return render(request, "apps/inbox.html", context=ctx)