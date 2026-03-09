from django.urls import path
from . import views

app_name = 'visites'

urlpatterns = [
    path('', views.index, name='index'),
    path('nouvelle/', views.nouvelle_visite, name='nouvelle_visite'),
    path('nouvelle/<int:visiteur_id>/', views.nouvelle_visite, name='nouvelle_visite_visiteur'),
    path('sortie/', views.sortie, name='sortie'),
    path('detail/<int:pk>/', views.detail, name='detail'),
    path('modifier/<int:pk>/', views.modifier, name='modifier'),
    path('annuler/<int:pk>/', views.annuler, name='annuler'),
    path('badge/<int:pk>/', views.imprimer_badge, name='imprimer_badge'),
    path('qrcode/<int:visiteur_id>/', views.generer_qrcode, name='generer_qrcode'),
    path('scanner/', views.scanner_qrcode, name='scanner_qrcode'),
    path('api/entree/', views.traiter_entree_qrcode, name='traiter_entree_qrcode'),
    path('api/sortie/', views.traiter_sortie_qrcode, name='traiter_sortie_qrcode'),
    path('api/motifs/', views.api_motifs, name='api_motifs'),
    path('api/correspondants/', views.api_correspondants, name='api_correspondants'),
    
    # Rendez-vous URLs
    path('rendez-vous/', views.rendez_vous_list, name='rendez_vous_list'),
    path('rendez-vous/nouveau/', views.rendez_vous_create, name='rendez_vous_create'),
    path('rendez-vous/nouveau/<int:visiteur_id>/', views.rendez_vous_create, name='rendez_vous_create_visiteur'),
    path('rendez-vous/<int:pk>/', views.rendez_vous_detail, name='rendez_vous_detail'),
    path('rendez-vous/<int:pk>/modifier/', views.rendez_vous_update, name='rendez_vous_update'),
    path('rendez-vous/<int:pk>/supprimer/', views.rendez_vous_delete, name='rendez_vous_delete'),
    path('rendez-vous/<int:pk>/confirmer/', views.rendez_vous_confirmer, name='rendez_vous_confirmer'),
    path('rendez-vous/<int:pk>/annuler/', views.rendez_vous_annuler, name='rendez_vous_annuler'),
    path('rendez-vous/<int:pk>/commencer/', views.rendez_vous_commencer, name='rendez_vous_commencer'),
    path('rendez-vous/<int:pk>/terminer/', views.rendez_vous_terminer, name='rendez_vous_terminer'),
]
