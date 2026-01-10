from django.contrib import admin
from .models import Visite


@admin.register(Visite)
class VisiteAdmin(admin.ModelAdmin):
    list_display = ('visiteur', 'motif', 'correspondant', 'date_visite', 'heure_entree', 'heure_sortie', 'statut')
    list_filter = ('statut', 'date_visite', 'motif', 'type_visite')
    search_fields = ('visiteur__nom', 'visiteur__prenoms', 'correspondant__nom')
    date_hierarchy = 'date_visite'
    raw_id_fields = ('visiteur',)
    list_per_page = 50
