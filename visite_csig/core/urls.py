from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('agenda/', views.cabinet_agenda, name='cabinet_agenda'),
    path('audiences/', views.cabinet_audiences, name='cabinet_audiences'),
    path('demandes/', views.cabinet_demandes, name='cabinet_demandes'),
    path('repertoire/', views.cabinet_repertoire, name='cabinet_repertoire'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profil/', views.profil, name='profil'),
    path('administration/', views.administration, name='administration'),
    path('administration/motifs/', views.admin_motifs, name='admin_motifs'),
    path('administration/correspondants/', views.admin_correspondants, name='admin_correspondants'),
    path('administration/creneaux/', views.admin_creneaux, name='admin_creneaux'),
    path('administration/utilisateurs/', views.admin_utilisateurs, name='admin_utilisateurs'),
    path('administration/utilisateurs/nouveau/', views.admin_utilisateur_create, name='admin_utilisateur_create'),
    path('administration/utilisateurs/<int:pk>/modifier/', views.admin_utilisateur_edit, name='admin_utilisateur_edit'),
    path('administration/utilisateurs/<int:pk>/toggle/', views.admin_utilisateur_toggle, name='admin_utilisateur_toggle'),
    path('administration/utilisateurs/<int:pk>/supprimer/', views.admin_utilisateur_delete, name='admin_utilisateur_delete'),
]
