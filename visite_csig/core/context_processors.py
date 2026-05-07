from django.conf import settings

def app_settings(request):
    user_perms = {}
    demandes_count = 0
    audiences_count = 0
    try:
        if getattr(request, 'user', None) and request.user.is_authenticated:
            if getattr(request.user, 'role', None) == 'superadmin':
                user_perms = {
                    'visites': {'view': True, 'add': True, 'change': True, 'delete': True},
                    'rendez_vous': {'view': True, 'add': True, 'change': True, 'delete': True},
                    'visiteurs': {'view': True, 'add': True, 'change': True, 'delete': True},
                    'rapports': {'view': True, 'add': True, 'change': True, 'delete': True},
                    'agenda': {'view': True, 'add': True, 'change': True, 'delete': True},
                    'administration': {'view': True, 'add': True, 'change': True, 'delete': True},
                    'utilisateurs': {'view': True, 'add': True, 'change': True, 'delete': True},
                }
            else:
                for p in request.user.permissions.all():
                    user_perms[p.module] = {
                        'view': p.can_view,
                        'add': p.can_add,
                        'change': p.can_change,
                        'delete': p.can_delete,
                    }
            from visites.models import RendezVous
            demandes_count = RendezVous.objects.filter(statut='planifie').count()
            audiences_count = RendezVous.objects.exclude(statut='planifie').exclude(statut='annule').count()
    except Exception:
        user_perms = {}

    return {
        'APP_NAME': settings.APP_NAME,
        'APP_VERSION': settings.APP_VERSION,
        'user_perms': user_perms,
        'demandes_count': demandes_count,
        'audiences_count': audiences_count,
    }
