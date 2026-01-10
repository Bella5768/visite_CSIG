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
]
