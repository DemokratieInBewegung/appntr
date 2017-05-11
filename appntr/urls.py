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
from django.conf.urls import url
from django.contrib import admin
from .views import index, invite, edit, applications, incoming, set_state, direct_invite, decline

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^interviewer/(?P<id>.*)$', edit),
    url(r'^einladung/(?P<id>.*)', invite),
    url(r'^incoming/EXTERNAL', incoming),
    url(r'^applications/(?P<id>.*)/set_state/(?P<state>.*)', set_state),
    url(r'^applications/decline/(?P<id>.*)', decline),
    url(r'^einladen/', direct_invite),
    url(r'^applications/', applications),
    url(r'^', index)
]
