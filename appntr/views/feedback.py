from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from appntr.models import Application, Feedback
from appntr.views.general import make_context

from datetime import datetime

@login_required
@require_POST
def feedback(request, id):
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


@login_required
def feedbacks(request):
    feedback_list = Feedback.objects.order_by("-added_at").filter(feedback_type=Feedback.TYPES.YES)
    ctx = make_context(
        request,
        menu='feedbacks',
        feedbacks=feedback_list.filter(status=Feedback.STATUS.OPEN),
        feedback_history=feedback_list.filter(status=Feedback.STATUS.DONE)
    )
    return render(request, "apps/feedbacks.html", context=ctx)


@login_required
def feedback_done(request, id):
    feedback = get_object_or_404(Feedback, pk=id)
    feedback.status = Feedback.STATUS.DONE
    feedback.done_at = datetime.now()
    feedback.done_user = request.user
    feedback.save()
    return redirect(request.META.get('HTTP_REFERER') or '/application/feedbacks')


def feedback_reopen(request, id):
    feedback = get_object_or_404(Feedback, pk=id)
    feedback.status = Feedback.STATUS.OPEN
    feedback.done_at = None
    feedback.done_user = None
    feedback.save()
    return redirect(request.META.get('HTTP_REFERER') or '/application/feedbacks')