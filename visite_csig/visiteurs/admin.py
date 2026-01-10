from django.contrib import admin
from .models import Visiteur


@admin.register(Visiteur)
class VisiteurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenoms', 'telephone', 'type_identite', 'numero_identite', 'date_creation')
    list_filter = ('type_identite', 'date_creation')
    search_fields = ('nom', 'prenoms', 'telephone', 'numero_identite')
    date_hierarchy = 'date_creation'
