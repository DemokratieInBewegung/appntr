"""appntr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from .views import (index, applyform, inbox, direct_invite, comment, invite,
                    direct_decline, trash_app, reset_appointment, my_appointments,
                    show_application, manage_slots, all_applications, vote, feedback, feedbacks, feedback_done, feedback_reopen)
# , invite, edit, applications, incoming, set_state, direct_invite, decline

urlpatterns = [
    url(r'^account/manage_slots$', manage_slots, name="manage_slots"),
    url(r"^account/", include("account.urls")),
    url(r'^admin/', admin.site.urls),
    url(r'^apply/', applyform),
    url(r'^einladung/(?P<id>.*)', invite, name="invite"),
    # url(r'^incoming/EXTERNAL', incoming),
    # url(r'^applications/(?P<id>.*)/set_state/(?P<state>.*)', set_state),
    # url(r'^applications/decline/(?P<id>.*)', decline),
    # url(r'^einladen/', direct_invite),
    url(r'^applications/(?P<id>\d+)$', show_application, name="show_application"),
    url(r'^applications/(?P<id>\d+)/invite$', direct_invite, name="direct_invite"),
    url(r'^applications/(?P<id>\d+)/reset$', reset_appointment, name="reset_appointment"),
    url(r'^applications/(?P<id>\d+)/decline$', direct_decline, name="direct_decline"),
    url(r'^applications/(?P<id>\d+)/trash$', trash_app, name="trash_app"),
    url(r'^applications/(?P<id>\d+)/comment$', comment, name="comment"),
    url(r'^applications/(?P<id>\d+)/feedback$', feedback, name="feedback"),
    url(r'^applications/feedbacks$', feedbacks, name="feedbacks"),
    url(r'^applications/feedback_done/(?P<id>\d+)$', feedback_done, name="feedback_done"),
    url(r'^applications/feedback_reopen/(?P<id>\d+)$', feedback_reopen, name="feedback_reopen"),
    url(r'^applications/inbox', inbox, name="inbox"),
    url(r'^applications/all', all_applications, name="all_applications"),
    url(r'^appointments$', my_appointments, name="my_appointments"),
    url(r'^vote/(?P<id>.*)$', vote, name="vote"),
    url(r'^', index)
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)