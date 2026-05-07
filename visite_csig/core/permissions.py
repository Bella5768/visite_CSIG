from functools import wraps

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect


def module_permission_required(module_code, action='view', json_forbidden=False):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                accept = (request.headers.get('Accept') or '').lower()
                if json_forbidden or ('application/json' in accept):
                    return JsonResponse({'success': False, 'message': 'Non authentifié'}, status=401)
                return redirect('core:login')

            if getattr(request.user, 'role', None) == 'superadmin':
                return view_func(request, *args, **kwargs)

            if request.user.has_module_permission(module_code, action):
                return view_func(request, *args, **kwargs)

            if json_forbidden:
                return JsonResponse({'success': False, 'message': 'Accès non autorisé'}, status=403)

            messages.error(request, 'Accès non autorisé.')
            return redirect('core:dashboard')

        return wrapper

    return decorator
