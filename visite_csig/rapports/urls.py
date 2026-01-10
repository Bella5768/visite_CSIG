from django.urls import path
from . import views

app_name = 'rapports'

urlpatterns = [
    path('journalier/', views.rapport_journalier, name='rapport_journalier'),
    path('statistiques/', views.statistiques, name='statistiques'),
]
