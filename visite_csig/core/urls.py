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
]
