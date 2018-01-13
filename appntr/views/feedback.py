from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from appntr.models import Application, Feedback

@login_required
@require_POST
def comment(request, id):
    app = get_object_or_404(Application, pk=id)
    Feedback(
        application=app,
        user=request.user,
        interviewer_names = request.POST.get('interviewer_names'),
        feedback_type = request.POST.get('feedback_type'),
        statement_yes = request.POST.get('statement_yes'),
        statement_maybe = request.POST.get('statement_maybe'),
        statement_no = request.POST.get('statement_no')
    ).save()

    messages.success(request, "Feedback hinterlegt.")
    return redirect(request.META.get('HTTP_REFERER') or '/applications/{}'.format(id))
