from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from core.permissions import module_permission_required

from .models import Correspondant, MotifVisite, PermissionUtilisateur, Utilisateur
from visites.models import CreneauDisponibilite, RendezVous


def _clean_error_message(e):
    """Extract a clean, user-friendly message from a Django exception."""
    if isinstance(e, ValidationError):
        if hasattr(e, 'message_dict'):
            parts = []
            for field, msgs in e.message_dict.items():
                joined = ', '.join(msgs)
                if field == '__all__':
                    parts.append(joined)
                else:
                    parts.append(f"{field}: {joined}")
            return ' | '.join(parts)
        if hasattr(e, 'messages'):
            return ' | '.join(e.messages)
    return str(e)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('nom_utilisateur'), password=request.POST.get('mot_de_passe'))
        if user:
            login(request, user)
            messages.success(request, 'Connexion réussie!')
            return redirect('core:dashboard')
        messages.error(request, 'Identifiants incorrects')
    return render(request, 'core/login.html', {'page_title': 'Connexion'})


def logout_view(request):
    logout(request)
    return redirect('core:login')


@login_required
def dashboard(request):
    today = timezone.now().date()
    month = today.month
    year = today.year

    rdv_today = RendezVous.objects.select_related('visiteur', 'motif').filter(date_rendez_vous=today).exclude(statut='annule')
    agenda_du_jour = rdv_today.order_by('heure_debut')

    audiences_mois = RendezVous.objects.filter(
        date_rendez_vous__year=year,
        date_rendez_vous__month=month,
        statut__in=['confirme', 'en_cours', 'termine'],
    ).count()

    demandes_attente = RendezVous.objects.filter(statut='planifie').count()

    prochaines_audiences = RendezVous.objects.select_related('visiteur', 'motif').filter(
        date_rendez_vous__gte=today,
        statut__in=['confirme', 'planifie'],
    ).order_by('date_rendez_vous', 'heure_debut')[:8]

    dernieres_demandes = RendezVous.objects.select_related('visiteur', 'motif').filter(
        statut='planifie'
    ).order_by('-date_creation')[:8]

    return render(request, 'cabinet/dashboard.html', {
        'page_title': 'Tableau de bord',
        'rdv_du_jour': rdv_today.count(),
        'audiences_mois': audiences_mois,
        'demandes_attente': demandes_attente,
        'agenda_du_jour': agenda_du_jour,
        'prochaines_audiences': prochaines_audiences,
        'dernieres_demandes': dernieres_demandes,
        'today': today,
    })


@module_permission_required('agenda', 'view')
def cabinet_agenda(request):
    return redirect('visites:agenda_ministre')


@module_permission_required('rendez_vous', 'view')
def cabinet_audiences(request):
    statut_filter = request.GET.get('statut', '')
    priorite_filter = request.GET.get('priorite', '')
    search_query = request.GET.get('search', '')

    qs = RendezVous.objects.select_related('visiteur', 'motif', 'correspondant').exclude(statut='planifie')

    if statut_filter:
        qs = qs.filter(statut=statut_filter)
    if priorite_filter:
        qs = qs.filter(priorite=priorite_filter)
    if search_query:
        qs = qs.filter(
            Q(sujet__icontains=search_query) |
            Q(visiteur__nom__icontains=search_query) |
            Q(visiteur__prenoms__icontains=search_query) |
            Q(visiteur__telephone__icontains=search_query) |
            Q(visiteur__email__icontains=search_query) |
            Q(motif__libelle__icontains=search_query)
        )

    paginator = Paginator(qs.order_by('-date_rendez_vous', '-heure_debut'), 20)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'cabinet/audiences.html', {
        'page_title': 'Audiences',
        'audiences': page,
        'statuts': RendezVous.STATUT_CHOICES,
        'priorites': RendezVous.PRIORITE_CHOICES,
        'statut_filter': statut_filter,
        'priorite_filter': priorite_filter,
        'search_query': search_query,
    })


@module_permission_required('rendez_vous', 'view')
def cabinet_demandes(request):
    priorite_filter = request.GET.get('priorite', '')
    search_query = request.GET.get('search', '')

    qs = RendezVous.objects.select_related('visiteur', 'motif', 'correspondant').filter(statut='planifie')
    if priorite_filter:
        qs = qs.filter(priorite=priorite_filter)
    if search_query:
        qs = qs.filter(
            Q(sujet__icontains=search_query) |
            Q(visiteur__nom__icontains=search_query) |
            Q(visiteur__prenoms__icontains=search_query) |
            Q(visiteur__telephone__icontains=search_query) |
            Q(visiteur__email__icontains=search_query) |
            Q(motif__libelle__icontains=search_query)
        )

    paginator = Paginator(qs.order_by('-date_creation'), 20)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'cabinet/demandes.html', {
        'page_title': 'Demandes',
        'demandes': page,
        'priorites': RendezVous.PRIORITE_CHOICES,
        'priorite_filter': priorite_filter,
        'search_query': search_query,
    })


@module_permission_required('administration', 'view')
def cabinet_repertoire(request):
    search_query = (request.GET.get('search') or '').strip()
    qs = Correspondant.objects.all()
    if search_query:
        qs = qs.filter(
            Q(nom__icontains=search_query) |
            Q(prenoms__icontains=search_query) |
            Q(fonction__icontains=search_query) |
            Q(departement__icontains=search_query) |
            Q(telephone__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    paginator = Paginator(qs.order_by('nom', 'prenoms'), 25)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'cabinet/repertoire.html', {
        'page_title': 'Répertoire',
        'contacts': page,
        'search_query': search_query,
    })


@login_required
def profil(request):
    if request.method == 'POST':
        request.user.nom = request.POST.get('nom', request.user.nom)
        request.user.prenoms = request.POST.get('prenoms', request.user.prenoms)
        request.user.save()
        messages.success(request, 'Profil mis à jour')
    return render(request, 'core/profil.html', {'page_title': 'Mon profil'})


@login_required
def admin_motifs(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            MotifVisite.objects.create(libelle=request.POST.get('libelle'), description=request.POST.get('description', ''))
            messages.success(request, 'Motif créé')
        elif action == 'update':
            motif = get_object_or_404(MotifVisite, pk=request.POST.get('motif_id'))
            motif.libelle = request.POST.get('libelle')
            motif.description = request.POST.get('description', '')
            motif.actif = request.POST.get('actif') == 'on'
            motif.save()
            messages.success(request, 'Motif modifié')
        return redirect('core:admin_motifs')
    return render(request, 'core/admin_motifs.html', {'page_title': 'Gestion des motifs', 'motifs': MotifVisite.objects.all()})


@login_required
def admin_correspondants(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Correspondant.objects.create(
                nom=request.POST.get('nom'), prenoms=request.POST.get('prenoms'),
                fonction=request.POST.get('fonction', ''), departement=request.POST.get('departement', ''),
                telephone=request.POST.get('telephone', ''), email=request.POST.get('email', '')
            )
            messages.success(request, 'Correspondant créé')
        elif action == 'update':
            c = get_object_or_404(Correspondant, pk=request.POST.get('correspondant_id'))
            c.nom, c.prenoms = request.POST.get('nom'), request.POST.get('prenoms')
            c.fonction, c.departement = request.POST.get('fonction', ''), request.POST.get('departement', '')
            c.telephone, c.email = request.POST.get('telephone', ''), request.POST.get('email', '')
            c.save()
            messages.success(request, 'Correspondant modifié')
        return redirect('core:admin_correspondants')
    return render(request, 'core/admin_correspondants.html', {'page_title': 'Correspondants', 'correspondants': Correspondant.objects.all()})


def admin_required(view_func):
    """Décorateur pour vérifier si l'utilisateur est admin ou superadmin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if request.user.role not in ['admin', 'superadmin']:
            messages.error(request, 'Accès non autorisé. Privilèges administrateur requis.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def _save_user_permissions_from_post(utilisateur, post_data):
    for module_code, _label in PermissionUtilisateur.MODULE_CHOICES:
        PermissionUtilisateur.objects.update_or_create(
            utilisateur=utilisateur,
            module=module_code,
            defaults={
                'can_view': post_data.get(f'perm_{module_code}_view') == 'on',
                'can_add': post_data.get(f'perm_{module_code}_add') == 'on',
                'can_change': post_data.get(f'perm_{module_code}_change') == 'on',
                'can_delete': post_data.get(f'perm_{module_code}_delete') == 'on',
            },
        )


@module_permission_required('administration', 'view')
def administration(request):
    invite_token = signing.dumps({'audience': 'ministre'}, salt='rendez_vous_public_ministre_invite')
    invite_url = request.build_absolute_uri(
        reverse('rendez_vous_public_ministre_invite', kwargs={'token': invite_token})
    )
    agenda_token = signing.dumps({'audience': 'ministre'}, salt='agenda_ministre_public')
    agenda_url = request.build_absolute_uri(
        reverse('agenda_ministre_public', kwargs={'token': agenda_token})
    )
    public_rdv_url = request.build_absolute_uri(
        reverse('rendez_vous_public_create')
    )
    return render(request, 'core/administration.html', {
        'page_title': 'Administration',
        'invite_url': invite_url,
        'agenda_url': agenda_url,
        'public_rdv_url': public_rdv_url,
    })


@module_permission_required('administration', 'view')
def admin_creneaux(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            creneau = CreneauDisponibilite(
                motif_id=request.POST.get('motif_id'),
                date=request.POST.get('date'),
                heure_debut=request.POST.get('heure_debut'),
                heure_fin=request.POST.get('heure_fin'),
                capacite=1,
                actif=True,
            )
            try:
                creneau.full_clean()
                creneau.save()
                messages.success(request, 'Créneau créé')
            except ValidationError as e:
                msg = str(e)
                if hasattr(e, 'message_dict') and e.message_dict:
                    msg = ' | '.join(['; '.join(v) for v in e.message_dict.values()])
                messages.error(request, msg)
        elif action == 'update':
            creneau = get_object_or_404(CreneauDisponibilite, pk=request.POST.get('creneau_id'))
            creneau.motif_id = request.POST.get('motif_id')
            creneau.date = request.POST.get('date')
            creneau.heure_debut = request.POST.get('heure_debut')
            creneau.heure_fin = request.POST.get('heure_fin')
            creneau.actif = request.POST.get('actif') == 'on'
            creneau.capacite = 1
            try:
                creneau.full_clean()
                creneau.save()
                messages.success(request, 'Créneau modifié')
            except ValidationError as e:
                msg = str(e)
                if hasattr(e, 'message_dict') and e.message_dict:
                    msg = ' | '.join(['; '.join(v) for v in e.message_dict.values()])
                messages.error(request, msg)
        elif action == 'delete':
            creneau = get_object_or_404(CreneauDisponibilite, pk=request.POST.get('creneau_id'))
            creneau.delete()
            messages.success(request, 'Créneau supprimé')
        return redirect('core:admin_creneaux')

    creneaux = CreneauDisponibilite.objects.select_related('motif').all().order_by('-date', '-heure_debut')
    return render(request, 'core/admin_creneaux.html', {
        'page_title': 'Gestion des créneaux',
        'creneaux': creneaux,
        'motifs': MotifVisite.objects.filter(actif=True),
    })


def superadmin_required(view_func):
    """Décorateur pour vérifier si l'utilisateur est superadmin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if request.user.role != 'superadmin':
            messages.error(request, 'Accès non autorisé. Privilèges Super Administrateur requis.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@module_permission_required('utilisateurs', 'view')
def admin_utilisateurs(request):
    """Liste des utilisateurs"""
    utilisateurs = Utilisateur.objects.all().order_by('-date_creation')
    stats = {
        'total': utilisateurs.count(),
        'admins': utilisateurs.filter(role__in=['admin', 'superadmin']).count(),
        'agents': utilisateurs.filter(role='agent').count(),
        'actifs': utilisateurs.filter(is_active=True).count(),
    }
    return render(request, 'core/admin_utilisateurs.html', {
        'page_title': 'Gestion des utilisateurs',
        'utilisateurs': utilisateurs,
        'stats': stats,
    })


@module_permission_required('utilisateurs', 'add')
def admin_utilisateur_create(request):
    """Créer un utilisateur"""
    if request.method == 'POST':
        nom_utilisateur = request.POST.get('nom_utilisateur')
        password = request.POST.get('password')
        nom = request.POST.get('nom')
        prenoms = request.POST.get('prenoms')
        role = request.POST.get('role', 'agent')
        poste = request.POST.get('poste', '')
        
        # Vérifier si le nom d'utilisateur existe déjà
        if Utilisateur.objects.filter(nom_utilisateur=nom_utilisateur).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà')
            return redirect('core:admin_utilisateur_create')
        
        # Seul superadmin peut créer un superadmin
        if role == 'superadmin' and request.user.role != 'superadmin':
            messages.error(request, 'Seul un Super Administrateur peut créer un autre Super Administrateur')
            return redirect('core:admin_utilisateur_create')
        
        user = Utilisateur.objects.create_user(
            nom_utilisateur=nom_utilisateur,
            password=password,
            nom=nom,
            prenoms=prenoms,
            role=role,
            poste=poste,
            is_staff=(role in ['admin', 'superadmin']),
        )

        if request.user.role == 'superadmin':
            _save_user_permissions_from_post(user, request.POST)

        messages.success(request, f'Utilisateur {user.prenoms} {user.nom} créé avec succès')
        return redirect('core:admin_utilisateurs')
    
    roles = Utilisateur.ROLE_CHOICES
    # Si l'utilisateur n'est pas superadmin, ne pas afficher l'option superadmin
    if request.user.role != 'superadmin':
        roles = [r for r in roles if r[0] != 'superadmin']
    
    return render(request, 'core/admin_utilisateur_form.html', {
        'page_title': 'Nouvel utilisateur',
        'roles': roles,
        'action': 'create',
        'perm_modules': PermissionUtilisateur.MODULE_CHOICES,
    })


@module_permission_required('utilisateurs', 'change')
def admin_utilisateur_edit(request, pk):
    """Modifier un utilisateur"""
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    
    # Ne pas permettre la modification d'un superadmin par un non-superadmin
    if utilisateur.role == 'superadmin' and request.user.role != 'superadmin':
        messages.error(request, 'Vous ne pouvez pas modifier un Super Administrateur')
        return redirect('core:admin_utilisateurs')
    
    if request.method == 'POST':
        utilisateur.nom = request.POST.get('nom')
        utilisateur.prenoms = request.POST.get('prenoms')
        utilisateur.poste = request.POST.get('poste', '')
        
        new_role = request.POST.get('role', utilisateur.role)
        # Seul superadmin peut définir le rôle superadmin
        if new_role == 'superadmin' and request.user.role != 'superadmin':
            new_role = utilisateur.role
        utilisateur.role = new_role
        utilisateur.is_staff = (new_role in ['admin', 'superadmin'])
        
        # Changer le mot de passe si fourni
        new_password = request.POST.get('password')
        if new_password:
            utilisateur.set_password(new_password)
        
        utilisateur.save()

        if request.user.role == 'superadmin':
            _save_user_permissions_from_post(utilisateur, request.POST)

        messages.success(request, f'Utilisateur {utilisateur.prenoms} {utilisateur.nom} modifié')
        return redirect('core:admin_utilisateurs')
    
    roles = Utilisateur.ROLE_CHOICES
    if request.user.role != 'superadmin':
        roles = [r for r in roles if r[0] != 'superadmin']
    
    return render(request, 'core/admin_utilisateur_form.html', {
        'page_title': f'Modifier {utilisateur.prenoms} {utilisateur.nom}',
        'utilisateur': utilisateur,
        'roles': roles,
        'action': 'edit',
        'perm_modules': PermissionUtilisateur.MODULE_CHOICES,
        'existing_perms': {p.module: p for p in utilisateur.permissions.all()},
    })


@module_permission_required('utilisateurs', 'change')
def admin_utilisateur_toggle(request, pk):
    """Activer/Désactiver un utilisateur"""
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    
    # Ne pas permettre la désactivation d'un superadmin par un non-superadmin
    if utilisateur.role == 'superadmin' and request.user.role != 'superadmin':
        messages.error(request, 'Vous ne pouvez pas désactiver un Super Administrateur')
        return redirect('core:admin_utilisateurs')
    
    # Ne pas permettre l'auto-désactivation
    if utilisateur == request.user:
        messages.error(request, 'Vous ne pouvez pas vous désactiver vous-même')
        return redirect('core:admin_utilisateurs')
    
    utilisateur.is_active = not utilisateur.is_active
    utilisateur.save()
    status = 'activé' if utilisateur.is_active else 'désactivé'
    messages.success(request, f'Utilisateur {utilisateur.prenoms} {utilisateur.nom} {status}')
    return redirect('core:admin_utilisateurs')


@module_permission_required('utilisateurs', 'delete')
def admin_utilisateur_delete(request, pk):
    """Supprimer un utilisateur (SuperAdmin uniquement)"""
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    
    if utilisateur == request.user:
        messages.error(request, 'Vous ne pouvez pas vous supprimer vous-même')
        return redirect('core:admin_utilisateurs')
    
    nom = f'{utilisateur.prenoms} {utilisateur.nom}'
    utilisateur.delete()
    messages.success(request, f'Utilisateur {nom} supprimé')
    return redirect('core:admin_utilisateurs')


# Vues pour les notifications
@login_required
def notifications_list(request):
    """Liste des notifications de l'utilisateur"""
    notifications = request.user.notifications.all()
    
    # Pagination
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/notifications_list.html', {
        'page_title': 'Notifications',
        'notifications': page_obj,
        'non_lues_count': request.user.notifications.filter(lue=False).count()
    })


@csrf_exempt
@login_required
def notifications_api(request):
    """API pour les notifications en temps réel"""
    if request.method == 'GET':
        # Récupérer les notifications non lues
        notifications = request.user.notifications.filter(lue=False).order_by('-date_creation')[:5]
        
        data = []
        for notif in notifications:
            data.append({
                'id': notif.id,
                'titre': notif.titre,
                'message': notif.message,
                'type': notif.type_notification,
                'date': notif.date_creation.strftime('%d/%m/%Y %H:%M'),
                'url': notif.get_url() if hasattr(notif, 'get_url') else '#'
            })
        
        from django.http import JsonResponse
        return JsonResponse({
            'notifications': data,
            'non_lues_count': request.user.notifications.filter(lue=False).count()
        })
    
    elif request.method == 'POST':
        # Marquer une notification comme lue
        notif_id = request.POST.get('notification_id')
        if notif_id:
            try:
                notification = request.user.notifications.get(id=notif_id)
                notification.marquer_comme_lue()
                from django.http import JsonResponse
                return JsonResponse({'success': True})
            except:
                from django.http import JsonResponse
                return JsonResponse({'success': False})
        
        # Marquer toutes les notifications comme lues
        if request.POST.get('marquer_toutes') == 'true':
            request.user.notifications.filter(lue=False).update(lue=True, date_lecture=timezone.now())
            from django.http import JsonResponse
            return JsonResponse({'success': True})
        
        from django.http import JsonResponse
        return JsonResponse({'success': False})


@login_required
def marquer_notification_lue(request, notification_id):
    """Marquer une notification spécifique comme lue"""
    notification = get_object_or_404(request.user.notifications, id=notification_id)
    notification.marquer_comme_lue()
    
    # Rediriger vers l'objet concerné si possible
    if hasattr(notification, 'get_url'):
        return redirect(notification.get_url())
    
    return redirect('core:notifications_list')


