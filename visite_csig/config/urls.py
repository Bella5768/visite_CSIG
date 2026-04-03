"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from visites import views as visites_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('rdv/', visites_views.rendez_vous_public_create, name='rendez_vous_public_create'),
    path('rdv/ministre/', visites_views.rendez_vous_public_ministre, name='rendez_vous_public_ministre'),
    path('rdv/ministre/<str:token>/', visites_views.rendez_vous_public_ministre_invite, name='rendez_vous_public_ministre_invite'),
    path('agenda/ministre/<str:token>/', visites_views.agenda_ministre_public, name='agenda_ministre_public'),
    path('agenda/ministre/<str:token>/events/', visites_views.agenda_ministre_public_events, name='agenda_ministre_public_events'),
    path('rdv/api/creneaux/', visites_views.rendez_vous_public_creneaux, name='rendez_vous_public_creneaux'),
    path('rdv/suivi/<str:token>/', visites_views.rendez_vous_public_suivi, name='rendez_vous_public_suivi'),
    path('visites/', include('visites.urls')),
    path('visiteurs/', include('visiteurs.urls')),
    path('rapports/', include('rapports.urls')),
]
