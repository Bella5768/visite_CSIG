from django.urls import path
from . import views

app_name = 'visiteurs'

urlpatterns = [
    path('', views.index, name='index'),
    path('ajouter/', views.ajouter, name='ajouter'),
    path('modifier/<int:pk>/', views.modifier, name='modifier'),
    path('historique/<int:pk>/', views.historique, name='historique'),
    path('rechercher/', views.rechercher, name='rechercher'),
    path('api/search/', views.api_search, name='api_search'),
    path('importer/', views.importer_excel, name='importer_excel'),
    path('exporter/', views.exporter_excel, name='exporter_excel'),
    path('modele-excel/', views.telecharger_modele_excel, name='telecharger_modele_excel'),
]
