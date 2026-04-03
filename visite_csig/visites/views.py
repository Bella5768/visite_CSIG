from datetime import date, timedelta
import io
import json

import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from core.models import Correspondant, MotifVisite
from core.permissions import module_permission_required
from visiteurs.models import Visiteur

from .models import CreneauDisponibilite, RendezVous, Visite
from .utils import generate_badge_pdf


def _get_motif_audience_ministre(require_active=True):
    qs = MotifVisite.objects.all()
    if require_active:
        qs = qs.filter(actif=True)

    motif = (
        qs.filter(libelle__icontains='audience')
        .filter(libelle__icontains='ministre')
        .first()
    )
    if motif:
        return motif

    return qs.filter(libelle__icontains='ministre').first()


@module_permission_required('visites', 'view')
def index(request):
    date_filter = request.GET.get('date', str(timezone.now().date()))
    statut_filter = request.GET.get('statut', '')
    visites = Visite.objects.select_related('visiteur', 'motif', 'correspondant')
    if date_filter:
        visites = visites.filter(date_visite=date_filter)
    if statut_filter:
        visites = visites.filter(statut=statut_filter)
    today = timezone.now().date()
    stats = {'total_jour': Visite.objects.filter(date_visite=today).count(), 'en_cours': Visite.objects.filter(date_visite=today, statut='en_cours').count(), 'terminees': Visite.objects.filter(date_visite=today, statut='terminee').count()}
    paginator = Paginator(visites, 20)
    return render(request, 'visites/index.html', {'page_title': 'Visites', 'visites': paginator.get_page(request.GET.get('page', 1)), 'stats': stats, 'date_filter': date_filter, 'statut_filter': statut_filter, 'statuts': settings.STATUTS_VISITE})


@module_permission_required('visites', 'add')
def nouvelle_visite(request, visiteur_id=None):
    visiteur = get_object_or_404(Visiteur, pk=visiteur_id) if visiteur_id else None
    if request.method == 'POST':
        visiteur_id = request.POST.get('visiteur_id')
        if not visiteur_id:
            messages.error(request, 'Veuillez sélectionner un visiteur')
            return redirect('visites:nouvelle_visite')
        Visite.objects.create(
            visiteur_id=visiteur_id, motif_id=request.POST.get('motif_id'),
            correspondant_id=request.POST.get('correspondant_id') or None,
            type_visite=request.POST.get('type_visite', 'professionnelle'),
            heure_entree=timezone.now().time(), observations=request.POST.get('observations', ''),
            agent_entree=f"{request.user.prenoms} {request.user.nom}"
        )
        messages.success(request, 'Visite enregistrée')
        return redirect('visites:index')
    return render(request, 'visites/nouvelle_visite.html', {'page_title': 'Nouvelle visite', 'visiteur': visiteur, 'motifs': MotifVisite.objects.filter(actif=True), 'correspondants': Correspondant.objects.filter(actif=True), 'types_visite': settings.TYPES_VISITE})


@module_permission_required('visites', 'view')
def detail(request, pk):
    return render(request, 'visites/detail.html', {'page_title': f'Visite #{pk}', 'visite': get_object_or_404(Visite.objects.select_related('visiteur', 'motif', 'correspondant'), pk=pk)})


@module_permission_required('visites', 'change')
def modifier(request, pk):
    visite = get_object_or_404(Visite, pk=pk)
    if request.method == 'POST':
        visite.motif_id = request.POST.get('motif_id')
        visite.correspondant_id = request.POST.get('correspondant_id') or None
        visite.observations = request.POST.get('observations', '')
        visite.save()
        messages.success(request, 'Visite modifiée')
        return redirect('visites:detail', pk=pk)
    return render(request, 'visites/modifier.html', {'page_title': 'Modifier visite', 'visite': visite, 'motifs': MotifVisite.objects.filter(actif=True), 'correspondants': Correspondant.objects.filter(actif=True)})


@module_permission_required('visites', 'delete')
def annuler(request, pk):
    visite = get_object_or_404(Visite, pk=pk)
    if request.method == 'POST':
        visite.annuler(request.POST.get('raison', 'Non spécifiée'))
        messages.success(request, 'Visite annulée')
        return redirect('visites:index')
    return render(request, 'visites/annuler.html', {'page_title': 'Annuler visite', 'visite': visite})


@module_permission_required('visites', 'view')
def generer_qrcode(request, visiteur_id):
    visiteur = get_object_or_404(Visiteur, pk=visiteur_id)
    data = json.dumps({'type': 'visiteur_csig', 'id': visiteur.id, 'nom': visiteur.nom, 'prenoms': visiteur.prenoms})
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return HttpResponse(buffer, content_type='image/png')


@module_permission_required('visites', 'view')
def scanner_qrcode(request):
    return render(request, 'visites/scanner_qrcode.html', {'page_title': 'Scanner QR Code'})


@module_permission_required('visites', 'add', json_forbidden=True)
def traiter_entree_qrcode(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        visiteur = get_object_or_404(Visiteur, pk=data.get('visiteur_id'))
        Visite.objects.create(
            visiteur=visiteur, motif_id=data.get('motif_id'),
            correspondant_id=data.get('correspondant_id') or None,
            heure_entree=timezone.now().time(),
            agent_entree=f"{request.user.prenoms} {request.user.nom}"
        )
        return JsonResponse({'success': True, 'message': f'Entrée enregistrée pour {visiteur}'})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


@module_permission_required('visites', 'view', json_forbidden=True)
def api_motifs(request):
    return JsonResponse({'motifs': [{'id': m.id, 'libelle': m.libelle} for m in MotifVisite.objects.filter(actif=True)]})


@module_permission_required('visites', 'view', json_forbidden=True)
def api_correspondants(request):
    return JsonResponse({'correspondants': [{'id': c.id, 'nom': f"{c.prenoms} {c.nom}", 'departement': c.departement} for c in Correspondant.objects.filter(actif=True)]})


@module_permission_required('visites', 'view')
def imprimer_badge(request, pk):
    visite = get_object_or_404(Visite.objects.select_related('visiteur', 'motif'), pk=pk)
    pdf_buffer = generate_badge_pdf(visite.visiteur, visite)
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="badge_{visite.visiteur.nom}.pdf"'
    return response


@module_permission_required('rendez_vous', 'view')
def rendez_vous_list(request):
    date_filter = request.GET.get('date', '')
    statut_filter = request.GET.get('statut', '')
    priorite_filter = request.GET.get('priorite', '')
    search_query = request.GET.get('search', '')
    
    rendez_vous = RendezVous.objects.select_related(
        'visiteur', 'motif', 'correspondant', 'cree_par'
    )
    
    if date_filter:
        rendez_vous = rendez_vous.filter(date_rendez_vous=date_filter)
    
    if statut_filter:
        rendez_vous = rendez_vous.filter(statut=statut_filter)
    
    if priorite_filter:
        rendez_vous = rendez_vous.filter(priorite=priorite_filter)
    
    if search_query:
        rendez_vous = rendez_vous.filter(
            Q(sujet__icontains=search_query) |
            Q(visiteur__nom__icontains=search_query) |
            Q(visiteur__prenoms__icontains=search_query) |
            Q(motif__libelle__icontains=search_query)
        )
    
    paginator = Paginator(rendez_vous, 20)
    page = paginator.get_page(request.GET.get('page', 1))
    
    stats = {
        'total': RendezVous.objects.count(),
        'aujourdhui': RendezVous.objects.filter(date_rendez_vous=timezone.now().date()).count(),
        'a_venir': RendezVous.objects.filter(
            date_rendez_vous__gte=timezone.now().date(),
            statut__in=['planifie', 'confirme']
        ).count(),
        'en_retard': RendezVous.objects.filter(
            date_rendez_vous__lt=timezone.now().date(),
            statut__in=['planifie', 'confirme', 'en_cours']
        ).count(),
    }
    
    context = {
        'page_title': 'Rendez-vous',
        'rendez_vous': page,
        'stats': stats,
        'date_filter': date_filter,
        'statut_filter': statut_filter,
        'priorite_filter': priorite_filter,
        'search_query': search_query,
        'statuts': RendezVous.STATUT_CHOICES,
        'priorites': RendezVous.PRIORITE_CHOICES,
    }
    
    return render(request, 'rendez_vous/list.html', context)


@module_permission_required('rendez_vous', 'add')
def rendez_vous_create(request, visiteur_id=None):
    visiteur = get_object_or_404(Visiteur, pk=visiteur_id) if visiteur_id else None
    
    if request.method == 'POST':
        try:
            rdv = RendezVous(
                visiteur_id=request.POST.get('visiteur_id'),
                motif_id=request.POST.get('motif_id'),
                correspondant_id=request.POST.get('correspondant_id') or None,
                date_rendez_vous=request.POST.get('date_rendez_vous'),
                heure_debut=request.POST.get('heure_debut'),
                heure_fin=request.POST.get('heure_fin'),
                sujet=request.POST.get('sujet'),
                description=request.POST.get('description', ''),
                notes_confidentielles=request.POST.get('notes_confidentielles', ''),
                priorite=request.POST.get('priorite', 'normale'),
                cree_par=request.user
            )
            rdv.full_clean()
            rdv.save()
            
            messages.success(request, 'Rendez-vous créé avec succès')
            return redirect('visites:rendez_vous_detail', pk=rdv.pk)
            
        except ValidationError as e:
            messages.error(request, 'Erreur de validation: ' + str(e))
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {str(e)}')
    
    context = {
        'page_title': 'Nouveau rendez-vous',
        'visiteur': visiteur,
        'visiteur_preselect_id': visiteur.pk if visiteur else None,
        'visiteurs': Visiteur.objects.all(),
        'motifs': MotifVisite.objects.filter(actif=True),
        'correspondants': Correspondant.objects.filter(actif=True),
        'priorites': RendezVous.PRIORITE_CHOICES,
        'today': timezone.now().date(),
    }
    
    return render(request, 'rendez_vous/create.html', context)


@module_permission_required('rendez_vous', 'view')
def rendez_vous_detail(request, pk):
    rendez_vous = get_object_or_404(
        RendezVous.objects.select_related(
            'visiteur', 'motif', 'correspondant', 'cree_par'
        ),
        pk=pk
    )
    
    context = {
        'page_title': f'Détails du rendez-vous - {rendez_vous.sujet}',
        'rendez_vous': rendez_vous,
    }
    
    return render(request, 'rendez_vous/detail.html', context)


@module_permission_required('rendez_vous', 'change')
def rendez_vous_update(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    
    if request.method == 'POST':
        try:
            old_motif = rendez_vous.motif
            old_correspondant = rendez_vous.correspondant
            original = {
                'visiteur_id': rendez_vous.visiteur_id,
                'motif_id': rendez_vous.motif_id,
                'correspondant_id': rendez_vous.correspondant_id,
                'date_rendez_vous': rendez_vous.date_rendez_vous,
                'heure_debut': rendez_vous.heure_debut,
                'heure_fin': rendez_vous.heure_fin,
                'sujet': rendez_vous.sujet,
                'description': rendez_vous.description,
                'priorite': rendez_vous.priorite,
            }

            rendez_vous.visiteur_id = request.POST.get('visiteur_id')
            rendez_vous.motif_id = request.POST.get('motif_id')
            rendez_vous.correspondant_id = request.POST.get('correspondant_id') or None
            rendez_vous.date_rendez_vous = request.POST.get('date_rendez_vous')
            rendez_vous.heure_debut = request.POST.get('heure_debut')
            rendez_vous.heure_fin = request.POST.get('heure_fin')
            rendez_vous.sujet = request.POST.get('sujet')
            rendez_vous.description = request.POST.get('description', '')
            rendez_vous.notes_confidentielles = request.POST.get('notes_confidentielles', '')
            rendez_vous.priorite = request.POST.get('priorite', 'normale')

            if rendez_vous.creneau_id:
                c = rendez_vous.creneau
                if (
                    str(rendez_vous.motif_id) != str(c.motif_id)
                    or rendez_vous.date_rendez_vous != c.date
                    or rendez_vous.heure_debut != c.heure_debut
                    or rendez_vous.heure_fin != c.heure_fin
                ):
                    rendez_vous.creneau = None
            
            rendez_vous.full_clean()
            rendez_vous.save()

            try:
                from .utils import notifier_visiteur_modification_rendez_vous

                changes = []
                if original['sujet'] != rendez_vous.sujet:
                    changes.append({'label': 'Sujet', 'old': original['sujet'], 'new': rendez_vous.sujet})
                if original['date_rendez_vous'] != rendez_vous.date_rendez_vous:
                    changes.append({'label': 'Date', 'old': original['date_rendez_vous'], 'new': rendez_vous.date_rendez_vous})
                if original['heure_debut'] != rendez_vous.heure_debut:
                    changes.append({'label': 'Heure début', 'old': original['heure_debut'], 'new': rendez_vous.heure_debut})
                if original['heure_fin'] != rendez_vous.heure_fin:
                    changes.append({'label': 'Heure fin', 'old': original['heure_fin'], 'new': rendez_vous.heure_fin})
                if str(original['motif_id']) != str(rendez_vous.motif_id):
                    changes.append({'label': 'Motif', 'old': old_motif, 'new': rendez_vous.motif})
                if str(original['correspondant_id'] or '') != str(rendez_vous.correspondant_id or ''):
                    changes.append({'label': 'Correspondant', 'old': old_correspondant or '-', 'new': rendez_vous.correspondant or '-'})
                if original['priorite'] != rendez_vous.priorite:
                    changes.append({'label': 'Priorité', 'old': original['priorite'], 'new': rendez_vous.priorite})

                if changes:
                    notifier_visiteur_modification_rendez_vous(rendez_vous, request, changes=changes)
            except Exception:
                pass
            
            messages.success(request, 'Rendez-vous mis à jour avec succès')
            return redirect('visites:rendez_vous_detail', pk=rendez_vous.pk)
            
        except ValidationError as e:
            messages.error(request, 'Erreur de validation: ' + str(e))
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour: {str(e)}')
    
    context = {
        'page_title': f'Modifier le rendez-vous - {rendez_vous.sujet}',
        'rendez_vous': rendez_vous,
        'visiteurs': Visiteur.objects.all(),
        'motifs': MotifVisite.objects.filter(actif=True),
        'correspondants': Correspondant.objects.filter(actif=True),
        'priorites': RendezVous.PRIORITE_CHOICES,
        'today': timezone.now().date(),
    }
    
    return render(request, 'rendez_vous/update.html', context)


@module_permission_required('rendez_vous', 'delete')
def rendez_vous_delete(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    
    if request.method == 'POST':
        sujet = rendez_vous.sujet
        rendez_vous.delete()
        messages.success(request, f'Le rendez-vous "{sujet}" a été supprimé avec succès')
        return redirect('visites:rendez_vous_list')
    
    context = {
        'page_title': 'Supprimer le rendez-vous',
        'rendez_vous': rendez_vous,
    }
    
    return render(request, 'rendez_vous/delete.html', context)


@module_permission_required('rendez_vous', 'change')
def rendez_vous_confirmer(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    
    if request.method == 'POST':
        try:
            rendez_vous.confirmer()
            messages.success(request, 'Rendez-vous confirmé avec succès')

            try:
                from .utils import envoyer_email_confirmation_rendez_vous

                email_sent = envoyer_email_confirmation_rendez_vous(rendez_vous, request)
                if not email_sent:
                    messages.warning(request, "Le rendez-vous est confirmé, mais l'email de confirmation n'a pas pu être envoyé (adresse email manquante ou configuration email).")
            except Exception as e:
                messages.warning(request, f"Le rendez-vous est confirmé, mais une erreur est survenue lors de l'envoi de l'email de confirmation: {str(e)}")
        except Exception as e:
            messages.error(request, f'Erreur lors de la confirmation: {str(e)}')
    
    return redirect('visites:rendez_vous_detail', pk=pk)


def _rendez_vous_public_create(request, fixed_motif=None, error_redirect_url_name='rendez_vous_public_create'):
    if request.method == 'POST':
        try:
            nom = (request.POST.get('nom') or '').strip()
            prenoms = (request.POST.get('prenoms') or '').strip()
            telephone = (request.POST.get('telephone') or '').strip()
            email = (request.POST.get('email') or '').strip()

            if not nom or not prenoms:
                messages.error(request, 'Veuillez renseigner votre nom et prénoms')
                return redirect(error_redirect_url_name)

            if not telephone and not email:
                messages.error(request, 'Veuillez renseigner un téléphone ou un email')
                return redirect(error_redirect_url_name)

            visiteur = None
            if telephone:
                visiteur = Visiteur.objects.filter(telephone=telephone).first()
            if not visiteur and email:
                visiteur = Visiteur.objects.filter(email=email).first()

            if not visiteur:
                visiteur = Visiteur.objects.create(
                    nom=nom,
                    prenoms=prenoms,
                    telephone=telephone,
                    email=email,
                    adresse=(request.POST.get('adresse') or '').strip(),
                    type_identite=(request.POST.get('type_identite') or '').strip(),
                    numero_identite=(request.POST.get('numero_identite') or '').strip() or None,
                )

            motif_id = str(fixed_motif.pk) if fixed_motif else request.POST.get('motif_id')
            creneau_id = request.POST.get('creneau_id')

            if not motif_id:
                messages.error(request, 'Veuillez sélectionner un motif')
                return redirect(error_redirect_url_name)

            if not creneau_id:
                messages.error(request, 'Veuillez sélectionner un créneau disponible')
                return redirect(error_redirect_url_name)

            creneau = get_object_or_404(CreneauDisponibilite, pk=creneau_id, motif_id=motif_id)
            if not creneau.est_disponible():
                messages.error(request, 'Ce créneau n\'est plus disponible. Veuillez en choisir un autre.')
                return redirect(error_redirect_url_name)

            rdv = RendezVous(
                visiteur=visiteur,
                motif_id=motif_id,
                creneau=creneau,
                date_rendez_vous=creneau.date,
                heure_debut=creneau.heure_debut,
                heure_fin=creneau.heure_fin,
                sujet=(request.POST.get('sujet') or '').strip(),
                description=(request.POST.get('description') or '').strip(),
                priorite='normale',
                cree_par=None,
            )
            rdv.full_clean()
            rdv.save()

            # Envoyer les emails de notification
            from .utils import envoyer_email_confirmation_rendez_vous
            
            # Email de confirmation au demandeur
            try:
                email_sent = envoyer_email_confirmation_rendez_vous(rdv, request)
                if email_sent:
                    print(f"[OK] Email de confirmation envoye a {rdv.visiteur.email}")
                else:
                    print(f"[ERREUR] Erreur lors de l'envoi de l'email de confirmation a {rdv.visiteur.email}")
            except Exception as e:
                print(f"[ERREUR] Exception lors de l'envoi de l'email de confirmation: {e}")
            
            # Notification au correspondant
            # (désactivée pour la page publique: le demandeur ne choisit pas de correspondant)

            suivi_token = signing.dumps({'rdv_id': rdv.pk}, salt='rendez_vous_public_suivi')
            suivi_url = request.build_absolute_uri(
                reverse('rendez_vous_public_suivi', kwargs={'token': suivi_token})
            )

            return render(request, 'rendez_vous/public_success.html', {
                'page_title': 'Rendez-vous enregistré',
                'rendez_vous': rdv,
                'suivi_token': suivi_token,
                'suivi_url': suivi_url,
            })

        except ValidationError as e:
            messages.error(request, 'Erreur de validation: ' + str(e))
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {str(e)}')

    return render(request, 'rendez_vous/public_create.html', {
        'page_title': 'Prendre rendez-vous',
        'motifs': MotifVisite.objects.filter(actif=True),
        'today': timezone.now().date(),
        'types_identite': settings.TYPES_IDENTITE,
        'fixed_motif': fixed_motif,
    })


def rendez_vous_public_create(request):
    return _rendez_vous_public_create(request)


def rendez_vous_public_ministre(request):
    motif = _get_motif_audience_ministre(require_active=True)

    if not motif:
        messages.error(
            request,
            "Motif 'Audience Ministre' introuvable. Veuillez le créer dans Administration > Motifs et l'activer."
        )
        return redirect('rendez_vous_public_create')

    return _rendez_vous_public_create(
        request,
        fixed_motif=motif,
        error_redirect_url_name='rendez_vous_public_ministre',
    )


def rendez_vous_public_ministre_invite(request, token):
    try:
        signing.loads(token, salt='rendez_vous_public_ministre_invite', max_age=60 * 60 * 24 * 90)
    except Exception:
        messages.error(request, "Lien invalide ou expiré. Veuillez demander un nouveau lien.")
        return redirect('rendez_vous_public_create')

    return rendez_vous_public_ministre(request)


@module_permission_required('agenda', 'view')
def agenda_ministre(request):
    return render(request, 'visites/agenda_ministre.html', {
        'page_title': "Agenda du Ministre",
    })


@module_permission_required('agenda', 'view', json_forbidden=True)
def agenda_ministre_events(request):
    start = request.GET.get('start')
    end = request.GET.get('end')

    def _to_date(s):
        if not s:
            return None
        try:
            # FullCalendar can send ISO datetimes (e.g. 2026-03-25T00:00:00Z)
            # while our field is a DateField.
            return date.fromisoformat(s[:10])
        except Exception:
            return None

    qs = RendezVous.objects.select_related('visiteur', 'motif').filter(statut='confirme')
    start_date = _to_date(start)
    end_date = _to_date(end)
    if start_date:
        qs = qs.filter(date_rendez_vous__gte=start_date)
    if end_date:
        qs = qs.filter(date_rendez_vous__lt=end_date)

    colors = {
        'planifie': '#2563eb',
        'confirme': '#16a34a',
        'en_cours': '#f59e0b',
        'termine': '#64748b',
        'annule': '#dc2626',
    }

    events = []
    for rdv in qs:
        start_dt = f"{rdv.date_rendez_vous.isoformat()}T{rdv.heure_debut.strftime('%H:%M:%S')}"
        end_dt = f"{rdv.date_rendez_vous.isoformat()}T{rdv.heure_fin.strftime('%H:%M:%S')}"
        motif_label = rdv.motif.libelle if getattr(rdv, 'motif', None) else ''
        color = colors.get(rdv.statut, '#2563eb')
        correspondant_label = None
        try:
            if getattr(rdv, 'correspondant', None):
                correspondant_label = f"{rdv.correspondant.prenoms} {rdv.correspondant.nom}".strip()
        except Exception:
            correspondant_label = None
        events.append({
            'id': rdv.pk,
            'title': f"[{motif_label}] {rdv.sujet} - {rdv.visiteur.prenoms} {rdv.visiteur.nom}" if motif_label else f"{rdv.sujet} - {rdv.visiteur.prenoms} {rdv.visiteur.nom}",
            'start': start_dt,
            'end': end_dt,
            'backgroundColor': color,
            'borderColor': color,
            'textColor': '#ffffff',
            'extendedProps': {
                'sujet': rdv.sujet,
                'motif': motif_label,
                'visiteur': f"{rdv.visiteur.prenoms} {rdv.visiteur.nom}".strip(),
                'telephone': getattr(rdv.visiteur, 'telephone', '') or '',
                'email': getattr(rdv.visiteur, 'email', '') or '',
                'correspondant': correspondant_label or '',
                'statut': rdv.get_statut_display() if hasattr(rdv, 'get_statut_display') else rdv.statut,
                'heure_debut': rdv.heure_debut.strftime('%H:%M'),
                'heure_fin': rdv.heure_fin.strftime('%H:%M'),
                'date': rdv.date_rendez_vous.strftime('%d/%m/%Y'),
            },
        })

    return JsonResponse({'success': True, 'events': events})


def rendez_vous_public_creneaux(request):
    motif_id = request.GET.get('motif_id')
    if not motif_id:
        return JsonResponse({'success': False, 'message': 'motif_id requis', 'creneaux': []}, status=400)

    today = timezone.now().date()
    qs = (
        CreneauDisponibilite.objects
        .filter(motif_id=motif_id, actif=True, date__gte=today)
        .order_by('date', 'heure_debut')
    )

    creneaux = []
    for c in qs:
        if not c.est_disponible():
            continue
        creneaux.append({
            'id': c.id,
            'date': c.date.strftime('%Y-%m-%d'),
            'heure_debut': c.heure_debut.strftime('%H:%M'),
            'heure_fin': c.heure_fin.strftime('%H:%M'),
            'places_restantes': c.get_places_restantes(),
            'label': f"{c.date.strftime('%d/%m/%Y')} {c.heure_debut.strftime('%H:%M')} - {c.heure_fin.strftime('%H:%M')}",
        })

    return JsonResponse({'success': True, 'creneaux': creneaux})


def rendez_vous_public_suivi(request, token):
    try:
        data = signing.loads(token, salt='rendez_vous_public_suivi')
        rdv_id = data.get('rdv_id')
        rendez_vous = get_object_or_404(
            RendezVous.objects.select_related('visiteur', 'motif', 'correspondant'),
            pk=rdv_id,
        )
        return render(request, 'rendez_vous/public_detail.html', {
            'page_title': 'Suivi du rendez-vous',
            'rendez_vous': rendez_vous,
        })
    except signing.BadSignature:
        return render(request, 'rendez_vous/public_invalid_link.html', {
            'page_title': 'Lien invalide',
        }, status=404)


@module_permission_required('rendez_vous', 'change')
def rendez_vous_annuler(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    
    if request.method == 'POST':
        raison = request.POST.get('raison', '')
        try:
            rendez_vous.annuler(raison)
            messages.success(request, 'Rendez-vous annulé avec succès')
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'annulation: {str(e)}')
    
    return redirect('visites:rendez_vous_detail', pk=pk)


@module_permission_required('rendez_vous', 'change')
def rendez_vous_commencer(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    
    if request.method == 'POST':
        try:
            rendez_vous.commencer()
            messages.success(request, 'Rendez-vous démarré avec succès')
        except Exception as e:
            messages.error(request, f'Erreur lors du démarrage: {str(e)}')
    
    return redirect('visites:rendez_vous_detail', pk=pk)


@module_permission_required('rendez_vous', 'change')
def rendez_vous_terminer(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    
    if request.method == 'POST':
        try:
            rendez_vous.terminer()
            messages.success(request, 'Rendez-vous terminé avec succès')
        except Exception as e:
            messages.error(request, f'Erreur lors de la terminaison: {str(e)}')
    
    return redirect('visites:rendez_vous_detail', pk=pk)
