from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profil/', views.profil, name='profil'),
    path('administration/motifs/', views.admin_motifs, name='admin_motifs'),
    path('administration/correspondants/', views.admin_correspondants, name='admin_correspondants'),
    path('administration/utilisateurs/', views.admin_utilisateurs, name='admin_utilisateurs'),
    path('administration/utilisateurs/nouveau/', views.admin_utilisateur_create, name='admin_utilisateur_create'),
    path('administration/utilisateurs/<int:pk>/modifier/', views.admin_utilisateur_edit, name='admin_utilisateur_edit'),
    path('administration/utilisateurs/<int:pk>/toggle/', views.admin_utilisateur_toggle, name='admin_utilisateur_toggle'),
    path('administration/utilisateurs/<int:pk>/supprimer/', views.admin_utilisateur_delete, name='admin_utilisateur_delete'),
]
