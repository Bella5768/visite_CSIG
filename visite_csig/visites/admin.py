from django.contrib import admin
from .models import Visite, RendezVous, CreneauDisponibilite


@admin.register(Visite)
class VisiteAdmin(admin.ModelAdmin):
    list_display = ('visiteur', 'motif', 'correspondant', 'date_visite', 'heure_entree', 'heure_sortie', 'statut')
    list_filter = ('statut', 'date_visite', 'motif', 'type_visite')
    search_fields = ('visiteur__nom', 'visiteur__prenoms', 'correspondant__nom')
    date_hierarchy = 'date_visite'
    raw_id_fields = ('visiteur',)
    list_per_page = 50


@admin.register(CreneauDisponibilite)
class CreneauDisponibiliteAdmin(admin.ModelAdmin):
    list_display = ('motif', 'date', 'heure_debut', 'heure_fin', 'actif')
    list_filter = ('actif', 'motif', 'date')
    search_fields = ('motif__libelle',)
    list_editable = ('actif',)
    date_hierarchy = 'date'
    list_per_page = 50


@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('sujet', 'visiteur', 'motif', 'date_rendez_vous', 'heure_debut', 'statut', 'priorite')
    list_filter = ('statut', 'priorite', 'motif', 'date_rendez_vous')
    search_fields = ('sujet', 'visiteur__nom', 'visiteur__prenoms', 'motif__libelle')
    date_hierarchy = 'date_rendez_vous'
    raw_id_fields = ('visiteur',)
    list_per_page = 50
