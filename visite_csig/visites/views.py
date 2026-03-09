from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.core import signing
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import qrcode, io, json
from .utils import generate_badge_pdf

from .models import Visite, RendezVous, CreneauDisponibilite
from visiteurs.models import Visiteur
from core.models import MotifVisite, Correspondant
from django.db.models import Q


@login_required
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


@login_required
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


@login_required
def sortie(request):
    if request.method == 'POST':
        visite = get_object_or_404(Visite, pk=request.POST.get('visite_id'))
        visite.enregistrer_sortie(f"{request.user.prenoms} {request.user.nom}")
        messages.success(request, 'Sortie enregistrée')
        return redirect('visites:sortie')
    return render(request, 'visites/sortie.html', {'page_title': 'Enregistrer sortie', 'visites_en_cours': Visite.objects.filter(date_visite=timezone.now().date(), statut='en_cours').select_related('visiteur', 'motif')})


@login_required
def detail(request, pk):
    return render(request, 'visites/detail.html', {'page_title': f'Visite #{pk}', 'visite': get_object_or_404(Visite.objects.select_related('visiteur', 'motif', 'correspondant'), pk=pk)})


@login_required
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


@login_required
def annuler(request, pk):
    visite = get_object_or_404(Visite, pk=pk)
    if request.method == 'POST':
        visite.annuler(request.POST.get('raison', 'Non spécifiée'))
        messages.success(request, 'Visite annulée')
        return redirect('visites:index')
    return render(request, 'visites/annuler.html', {'page_title': 'Annuler visite', 'visite': visite})


@login_required
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


@login_required
def scanner_qrcode(request):
    mode = request.GET.get('mode', 'entree')
    return render(request, 'visites/scanner_qrcode.html', {'page_title': 'Scanner QR Code', 'mode': mode})


@login_required
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


@login_required
def traiter_sortie_qrcode(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        visite = Visite.objects.filter(visiteur_id=data.get('visiteur_id'), statut='en_cours', date_visite=timezone.now().date()).first()
        if visite:
            visite.enregistrer_sortie(f"{request.user.prenoms} {request.user.nom}")
            return JsonResponse({'success': True, 'message': 'Sortie enregistrée'})
        return JsonResponse({'success': False, 'message': 'Aucune visite en cours'})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


@login_required
def api_motifs(request):
    return JsonResponse({'motifs': [{'id': m.id, 'libelle': m.libelle} for m in MotifVisite.objects.filter(actif=True)]})


@login_required
def api_correspondants(request):
    return JsonResponse({'correspondants': [{'id': c.id, 'nom': f"{c.prenoms} {c.nom}", 'departement': c.departement} for c in Correspondant.objects.filter(actif=True)]})


@login_required
def imprimer_badge(request, pk):
    visite = get_object_or_404(Visite.objects.select_related('visiteur', 'motif'), pk=pk)
    pdf_buffer = generate_badge_pdf(visite.visiteur, visite)
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="badge_{visite.visiteur.nom}.pdf"'
    return response


@login_required
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


@login_required
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


@login_required
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


@login_required
def rendez_vous_update(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    
    if request.method == 'POST':
        try:
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
            
            rendez_vous.full_clean()
            rendez_vous.save()
            
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


@login_required
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


@login_required
def rendez_vous_confirmer(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    
    if request.method == 'POST':
        try:
            rendez_vous.confirmer()
            messages.success(request, 'Rendez-vous confirmé avec succès')
        except Exception as e:
            messages.error(request, f'Erreur lors de la confirmation: {str(e)}')
    
    return redirect('visites:rendez_vous_detail', pk=pk)


def rendez_vous_public_create(request):
    if request.method == 'POST':
        try:
            nom = (request.POST.get('nom') or '').strip()
            prenoms = (request.POST.get('prenoms') or '').strip()
            telephone = (request.POST.get('telephone') or '').strip()
            email = (request.POST.get('email') or '').strip()

            if not nom or not prenoms:
                messages.error(request, 'Veuillez renseigner votre nom et prénoms')
                return redirect('rendez_vous_public_create')

            if not telephone and not email:
                messages.error(request, 'Veuillez renseigner un téléphone ou un email')
                return redirect('rendez_vous_public_create')

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

            motif_id = request.POST.get('motif_id')
            creneau_id = request.POST.get('creneau_id')

            if not motif_id:
                messages.error(request, 'Veuillez sélectionner un motif')
                return redirect('rendez_vous_public_create')

            if not creneau_id:
                messages.error(request, 'Veuillez sélectionner un créneau disponible')
                return redirect('rendez_vous_public_create')

            creneau = get_object_or_404(CreneauDisponibilite, pk=creneau_id, motif_id=motif_id)
            if not creneau.est_disponible():
                messages.error(request, 'Ce créneau n\'est plus disponible. Veuillez en choisir un autre.')
                return redirect('rendez_vous_public_create')

            rdv = RendezVous(
                visiteur=visiteur,
                motif_id=motif_id,
                correspondant_id=request.POST.get('correspondant_id') or None,
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
            from .utils import envoyer_email_confirmation_rendez_vous, notifier_correspondant_rendez_vous
            
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
            try:
                notif_sent = notifier_correspondant_rendez_vous(rdv, request)
                if notif_sent:
                    print(f"[OK] Notification envoyee au correspondant {rdv.correspondant.email if rdv.correspondant else 'N/A'}")
                else:
                    print(f"[ERREUR] Erreur lors de l'envoi de la notification au correspondant")
            except Exception as e:
                print(f"[ERREUR] Exception lors de l'envoi de la notification au correspondant: {e}")

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
        'correspondants': Correspondant.objects.filter(actif=True),
        'today': timezone.now().date(),
        'types_identite': settings.TYPES_IDENTITE,
    })


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


@login_required
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


@login_required
def rendez_vous_commencer(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    
    if request.method == 'POST':
        try:
            rendez_vous.commencer()
            messages.success(request, 'Rendez-vous démarré avec succès')
        except Exception as e:
            messages.error(request, f'Erreur lors du démarrage: {str(e)}')
    
    return redirect('visites:rendez_vous_detail', pk=pk)


@login_required
def rendez_vous_terminer(request, pk):
    rendez_vous = get_object_or_404(RendezVous, pk=pk)
    
    if request.method == 'POST':
        try:
            rendez_vous.terminer()
            messages.success(request, 'Rendez-vous terminé avec succès')
        except Exception as e:
            messages.error(request, f'Erreur lors de la terminaison: {str(e)}')
    
    return redirect('visites:rendez_vous_detail', pk=pk)
