from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, MotifVisite, Correspondant


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('nom_utilisateur', 'nom', 'prenoms', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('nom_utilisateur', 'nom', 'prenoms')
    ordering = ('nom_utilisateur',)
    fieldsets = (
        (None, {'fields': ('nom_utilisateur', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenoms', 'poste')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('nom_utilisateur', 'nom', 'prenoms', 'password1', 'password2', 'role')}),
    )


@admin.register(MotifVisite)
class MotifVisiteAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'actif', 'date_creation')
    list_filter = ('actif',)
    search_fields = ('libelle',)
    list_editable = ('actif',)


@admin.register(Correspondant)
class CorrespondantAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenoms', 'fonction', 'departement', 'telephone', 'actif')
    list_filter = ('departement', 'actif')
    search_fields = ('nom', 'prenoms', 'departement')
    list_editable = ('actif',)
