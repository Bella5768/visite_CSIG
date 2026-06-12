from datetime import date, datetime, time, timedelta
import io
import csv
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

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.models import Correspondant, MotifVisite
from core.permissions import module_permission_required
from visiteurs.models import Visiteur

from .models import CreneauDisponibilite, RendezVous, Visite
from .utils import generate_badge_pdf


# --- Workflow rendez-vous publics ---------------------------------------------
# Règles métier:
#  - Motif "Visite officielle" : disponible du lundi au jeudi, créneau 13h-16h.
#    L'administrateur précise ensuite l'heure exacte au moment de la confirmation.
#  - Motif "Visite personnelle" : disponible uniquement le vendredi, 11h-15h.
# Les créneaux sont générés automatiquement à la volée (semaine en cours).

VISITE_OFFICIELLE = 'officielle'
VISITE_PERSONNELLE = 'personnelle'

# Jours: lundi=0 ... dimanche=6
_REGLES_MOTIF = {
    VISITE_OFFICIELLE: {
        'jours': (0, 1, 2, 3),  # lundi -> jeudi
        'heure_debut': time(13, 0),
        'heure_fin': time(16, 0),
    },
    VISITE_PERSONNELLE: {
        'jours': (4,),  # vendredi
        'heure_debut': time(11, 0),
        'heure_fin': time(15, 0),
    },
}

_JOURS_FR = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
_MOIS_FR = ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']


def _classifier_motif(motif):
    """Retourne VISITE_OFFICIELLE / VISITE_PERSONNELLE ou None selon le libellé."""
    if motif is None:
        return None
    libelle = (motif.libelle or '').lower()
    if 'officiel' in libelle:
        return VISITE_OFFICIELLE
    if 'personnel' in libelle:
        return VISITE_PERSONNELLE
    return None


def _generer_creneaux_virtuels(motif):
    """Génère les créneaux disponibles pour la semaine en cours.

    Règle: on n'expose qu'une seule semaine à la fois. Dès que tous les jours
    autorisés de la semaine sont passés, on bascule automatiquement sur la
    semaine suivante.
    """
    type_motif = _classifier_motif(motif)
    regle = _REGLES_MOTIF.get(type_motif)
    if not regle:
        return []

    today = timezone.now().date()
    jours_autorises = regle['jours']
    h_debut = regle['heure_debut']
    h_fin = regle['heure_fin']

    # Lundi de la semaine en cours.
    lundi = today - timedelta(days=today.weekday())
    # Si tous les jours autorisés de cette semaine sont passés, on passe à
    # la semaine suivante.
    dernier_jour_autorise = lundi + timedelta(days=max(jours_autorises))
    if today > dernier_jour_autorise:
        lundi = lundi + timedelta(days=7)

    fin_semaine = lundi + timedelta(days=6)

    # Les deux types de visites acceptent plusieurs demandes par jour
    # (l'admin choisira l'heure exacte lors de la confirmation).
    creneaux = []
    for offset in range(7):
        jour = lundi + timedelta(days=offset)
        if jour.weekday() not in jours_autorises:
            continue
        if jour < today:
            continue
        iso = jour.isoformat()
        creneaux.append({
            'id': f'v:{type_motif}:{iso}',
            'date': iso,
            'date_formatted': f"{_JOURS_FR[jour.weekday()]} {jour.day} {_MOIS_FR[jour.month]} {jour.year}",
            'heure_debut': h_debut.strftime('%H:%M'),
            'heure_fin': h_fin.strftime('%H:%M'),
            'places_restantes': 1,
            'capacite': 1,
            'label': f"{jour.strftime('%d/%m/%Y')} {h_debut.strftime('%H:%M')} - {h_fin.strftime('%H:%M')}",
        })

    return creneaux


def _resoudre_creneau_virtuel(creneau_id, motif):
    """Crée (et retourne) un CreneauDisponibilite à partir d'un id virtuel.

    Format attendu: ``v:<type>:<YYYY-MM-DD>``.
    Retourne ``None`` si l'id n'est pas un id virtuel valide.
    """
    if not creneau_id or not creneau_id.startswith('v:'):
        return None
    try:
        _, type_motif, iso_date = creneau_id.split(':', 2)
        jour = date.fromisoformat(iso_date)
    except (ValueError, AttributeError):
        return None

    regle = _REGLES_MOTIF.get(type_motif)
    if not regle:
        return None
    if jour.weekday() not in regle['jours']:
        return None
    if jour < timezone.now().date():
        return None
    if _classifier_motif(motif) != type_motif:
        return None

    # Pour la visite personnelle (un seul créneau par vendredi), on réutilise
    # un éventuel créneau libre existant.
    if type_motif == VISITE_PERSONNELLE:
        existant = (
            CreneauDisponibilite.objects
            .filter(motif=motif, date=jour,
                    heure_debut=regle['heure_debut'],
                    heure_fin=regle['heure_fin'])
            .first()
        )
        if existant and existant.est_disponible():
            return existant

    # Visite officielle: chaque demande crée son propre créneau (capacité 1)
    creneau = CreneauDisponibilite.objects.create(
        motif=motif,
        date=jour,
        heure_debut=regle['heure_debut'],
        heure_fin=regle['heure_fin'],
        capacite=1,
        actif=True,
    )
    return creneau


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


@module_permission_required('agenda', 'view')
def agenda_ministre_export_pdf(request):
    start = request.GET.get('start')
    end = request.GET.get('end')

    def _to_date(s):
        if not s:
            return None
        try:
            return date.fromisoformat(s[:10])
        except Exception:
            return None

    start_date = _to_date(start)
    end_date = _to_date(end)

    qs = RendezVous.objects.select_related('visiteur', 'motif', 'correspondant').filter(statut='confirme')
    if start_date:
        qs = qs.filter(date_rendez_vous__gte=start_date)
    if end_date:
        qs = qs.filter(date_rendez_vous__lt=end_date)
    qs = qs.order_by('date_rendez_vous', 'heure_debut')

    filename = 'rendez_vous_confirmes.pdf'
    if start_date and end_date:
        filename = f"rendez_vous_confirmes_{start_date.isoformat()}_{(end_date - timedelta(days=1)).isoformat()}.pdf"
    elif start_date:
        filename = f"rendez_vous_confirmes_{start_date.isoformat()}.pdf"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=22,
        rightMargin=22,
        topMargin=22,
        bottomMargin=18,
        title='Rendez-vous confirmés',
    )

    styles = getSampleStyleSheet()
    title = 'Liste des rendez-vous confirmés'
    if start_date and end_date:
        title = f"Liste des rendez-vous confirmés ({start_date.strftime('%d/%m/%Y')} - {(end_date - timedelta(days=1)).strftime('%d/%m/%Y')})"
    elif start_date:
        title = f"Liste des rendez-vous confirmés (à partir du {start_date.strftime('%d/%m/%Y')})"

    elements = [
        Paragraph(title, styles['Title']),
        Spacer(1, 10),
    ]

    data = [[
        'Date',
        'Début',
        'Fin',
        'Motif',
        'Sujet',
        'Visiteur',
        'Téléphone',
        'Email',
    ]]

    for rdv in qs:
        visiteur = getattr(rdv, 'visiteur', None)
        motif = getattr(rdv, 'motif', None)
        data.append([
            rdv.date_rendez_vous.strftime('%d/%m/%Y') if rdv.date_rendez_vous else '',
            rdv.heure_debut.strftime('%H:%M') if rdv.heure_debut else '',
            rdv.heure_fin.strftime('%H:%M') if rdv.heure_fin else '',
            getattr(motif, 'libelle', '') or '',
            rdv.sujet or '',
            f"{getattr(visiteur, 'prenoms', '')} {getattr(visiteur, 'nom', '')}".strip(),
            getattr(visiteur, 'telephone', '') or '',
            getattr(visiteur, 'email', '') or '',
        ])

    table = Table(
        data,
        colWidths=[60, 40, 40, 90, 140, 120, 80, 140],
        repeatRows=1,
    )

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d3a6e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@module_permission_required('rendez_vous', 'view')
def rendez_vous_list(request):
    date_filter = request.GET.get('date', '')
    statut_filter = request.GET.get('statut', '')
    priorite_filter = request.GET.get('priorite', '')
    search_query = request.GET.get('search', '')
    
    rendez_vous = RendezVous.objects.select_related(
        'visiteur', 'motif', 'correspondant', 'cree_par'
    ).order_by('-date_creation')

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
            def _clean(name):
                # Nettoie les espaces (y compris insécables \xa0) envoyés par
                # certains navigateurs mobiles.
                return (request.POST.get(name) or '').replace('\xa0', ' ').strip()

            motif_id = _clean('motif_id')
            creneau_id = _clean('creneau_id')
            date_rdv = _clean('date_rendez_vous')
            heure_debut = _clean('heure_debut')
            heure_fin = _clean('heure_fin')
            creneau = None

            # Si un créneau prédéfini a été sélectionné, on en déduit la date
            # et les heures (créneau virtuel "v:..." ou créneau existant).
            if creneau_id:
                motif_obj = get_object_or_404(MotifVisite, pk=motif_id)
                if creneau_id.startswith('v:'):
                    creneau = _resoudre_creneau_virtuel(creneau_id, motif_obj)
                else:
                    creneau = CreneauDisponibilite.objects.filter(
                        pk=creneau_id, motif_id=motif_id
                    ).first()
                if creneau:
                    date_rdv = creneau.date
                    heure_debut = creneau.heure_debut
                    heure_fin = creneau.heure_fin

            if not date_rdv or not heure_debut or not heure_fin:
                messages.error(request, 'Veuillez sélectionner un créneau ou renseigner la date et les heures')
                raise ValueError('Date/heures manquantes')

            rdv = RendezVous(
                visiteur_id=_clean('visiteur_id'),
                motif_id=motif_id,
                correspondant_id=_clean('correspondant_id') or None,
                creneau=creneau,
                date_rendez_vous=date_rdv,
                heure_debut=heure_debut,
                heure_fin=heure_fin,
                sujet=_clean('sujet'),
                description=request.POST.get('description', ''),
                notes_confidentielles=request.POST.get('notes_confidentielles', ''),
                priorite=_clean('priorite') or 'normale',
                cree_par=request.user
            )
            rdv.full_clean()
            rdv.save()
            
            messages.success(request, 'Rendez-vous créé avec succès')
            return redirect('visites:rendez_vous_detail', pk=rdv.pk)
            
        except ValueError:
            pass
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
            # L'administrateur peut préciser l'heure exacte au moment de la
            # confirmation (cas typique d'une visite officielle où le créneau
            # initial est large, ex: 13h-16h).
            heure_debut_str = (request.POST.get('heure_debut') or '').strip()
            heure_fin_str = (request.POST.get('heure_fin') or '').strip()

            def _parse(t):
                for fmt in ('%H:%M', '%H:%M:%S'):
                    try:
                        return datetime.strptime(t, fmt).time()
                    except ValueError:
                        continue
                return None

            nouvelle_debut = _parse(heure_debut_str) if heure_debut_str else None
            nouvelle_fin = _parse(heure_fin_str) if heure_fin_str else None

            if nouvelle_debut and nouvelle_fin and nouvelle_fin <= nouvelle_debut:
                messages.error(request, "L'heure de fin doit être postérieure à l'heure de début")
                return redirect('visites:rendez_vous_detail', pk=pk)

            updated_fields = []
            if nouvelle_debut and nouvelle_debut != rendez_vous.heure_debut:
                rendez_vous.heure_debut = nouvelle_debut
                updated_fields.append('heure_debut')
            if nouvelle_fin and nouvelle_fin != rendez_vous.heure_fin:
                rendez_vous.heure_fin = nouvelle_fin
                updated_fields.append('heure_fin')
            if updated_fields:
                rendez_vous.save(update_fields=updated_fields + ['date_modification'])

            # La méthode confirmer enverra automatiquement l'email au demandeur
            rendez_vous.confirmer(request=request)
            messages.success(request, 'Rendez-vous confirmé avec succès. Email de confirmation envoyé au demandeur.')
        except Exception as e:
            messages.error(request, f'Erreur lors de la confirmation: {str(e)}')

    return redirect('visites:rendez_vous_detail', pk=pk)


def _rendez_vous_public_create(request, fixed_motif=None, error_redirect_url_name='rendez_vous_public_create'):
    if request.method == 'POST':
        try:
            nom = (request.POST.get('nom') or '').strip()
            prenoms = (request.POST.get('prenoms') or '').strip()
            email = (request.POST.get('email') or '').strip()
            telephone = (request.POST.get('telephone') or '').strip()

            if not nom or not prenoms:
                messages.error(request, 'Veuillez renseigner votre nom et prénoms')
                return redirect(error_redirect_url_name)

            if not email:
                messages.error(request, 'Veuillez renseigner votre email pour recevoir la confirmation')
                return redirect(error_redirect_url_name)

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

            description = (request.POST.get('description') or '').strip()
            if not description:
                messages.error(request, 'Veuillez préciser le commentaire / la description de votre demande')
                return redirect(error_redirect_url_name)

            # Résolution du créneau: id virtuel (workflow officielle/personnelle)
            # ou id réel d'un CreneauDisponibilite existant.
            motif_obj = get_object_or_404(MotifVisite, pk=motif_id)
            if creneau_id.startswith('v:'):
                creneau = _resoudre_creneau_virtuel(creneau_id, motif_obj)
                if creneau is None:
                    messages.error(request, "Créneau invalide ou indisponible. Veuillez en choisir un autre.")
                    return redirect(error_redirect_url_name)
            else:
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
                description=description,
                priorite='normale',
                cree_par=None,
            )
            rdv.full_clean()
            rdv.save()

            # NB: aucun email n'est envoyé à la création du rendez-vous.
            # L'email de confirmation est déclenché uniquement lorsqu'un
            # administrateur valide la demande en précisant l'heure exacte
            # (voir `rendez_vous_confirmer`).

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

    # Sur la page publique, on n'affiche que les 2 motifs réglementés:
    # "Visite officielle" (lun-jeu 13h-16h) et "Visite personnelle" (ven 11h-15h).
    motifs_publics = [
        m for m in MotifVisite.objects.filter(actif=True)
        if _classifier_motif(m) in _REGLES_MOTIF
    ]

    return render(request, 'rendez_vous/public_create.html', {
        'page_title': 'Prendre rendez-vous',
        'motifs': motifs_publics,
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


def agenda_ministre_public(request, token):
    try:
        signing.loads(token, salt='agenda_ministre_public', max_age=60 * 60 * 24 * 90)
    except Exception:
        return render(request, 'rendez_vous/public_invalid_link.html', {
            'page_title': 'Lien invalide',
        }, status=404)

    return render(request, 'visites/agenda_ministre_public.html', {
        'page_title': "Agenda du Ministre",
        'agenda_token': token,
    })


def agenda_ministre_public_events(request, token):
    try:
        signing.loads(token, salt='agenda_ministre_public', max_age=60 * 60 * 24 * 90)
    except Exception:
        return JsonResponse({'success': False, 'message': 'Lien invalide ou expiré'}, status=403)

    start = request.GET.get('start')
    end = request.GET.get('end')

    def _to_date(s):
        if not s:
            return None
        try:
            return date.fromisoformat(s[:10])
        except Exception:
            return None

    qs = RendezVous.objects.select_related('visiteur', 'motif').exclude(statut='annule')
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
                'description': rdv.description or '',
                'motif': motif_label,
                'visiteur': f"{rdv.visiteur.prenoms} {rdv.visiteur.nom}".strip(),
                'telephone': getattr(rdv.visiteur, 'telephone', '') or '',
                'email': getattr(rdv.visiteur, 'email', '') or '',
                'statut_code': rdv.statut,
                'statut': rdv.get_statut_display() if hasattr(rdv, 'get_statut_display') else rdv.statut,
                'heure_debut': rdv.heure_debut.strftime('%H:%M'),
                'heure_fin': rdv.heure_fin.strftime('%H:%M'),
                'date': rdv.date_rendez_vous.strftime('%d/%m/%Y'),
            },
        })

    return JsonResponse({'success': True, 'events': events})


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
                'description': rdv.description or '',
                'motif': motif_label,
                'visiteur': f"{rdv.visiteur.prenoms} {rdv.visiteur.nom}".strip(),
                'telephone': getattr(rdv.visiteur, 'telephone', '') or '',
                'email': getattr(rdv.visiteur, 'email', '') or '',
                'correspondant': correspondant_label or '',
                'statut_code': rdv.statut,
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

    motif = MotifVisite.objects.filter(pk=motif_id, actif=True).first()
    if not motif:
        return JsonResponse({'success': False, 'message': 'Motif introuvable', 'creneaux': []}, status=404)

    # Visite officielle / personnelle : génération automatique selon les règles métier.
    type_motif = _classifier_motif(motif)
    if type_motif in _REGLES_MOTIF:
        creneaux = _generer_creneaux_virtuels(motif)
        return JsonResponse({'success': True, 'creneaux': creneaux})

    # Autres motifs : créneaux administrés manuellement.
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
            'date_formatted': f"{_JOURS_FR[c.date.weekday()]} {c.date.day} {_MOIS_FR[c.date.month]} {c.date.year}",
            'heure_debut': c.heure_debut.strftime('%H:%M'),
            'heure_fin': c.heure_fin.strftime('%H:%M'),
            'places_restantes': c.get_places_restantes(),
            'capacite': c.capacite,
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

        preuve_url = None
        try:
            if getattr(rendez_vous, 'statut', None) == 'confirme':
                preuve_token = signing.dumps({'rdv_id': rendez_vous.pk}, salt='rendez_vous_public_preuve')
                preuve_url = request.build_absolute_uri(
                    reverse('rendez_vous_public_preuve', kwargs={'token': preuve_token})
                )
        except Exception:
            preuve_url = None

        return render(request, 'rendez_vous/public_detail.html', {
            'page_title': 'Suivi du rendez-vous',
            'rendez_vous': rendez_vous,
            'preuve_url': preuve_url,
        })
    except signing.BadSignature:
        return render(request, 'rendez_vous/public_invalid_link.html', {
            'page_title': 'Lien invalide',
        }, status=404)


def rendez_vous_public_preuve(request, token):
    try:
        data = signing.loads(token, salt='rendez_vous_public_preuve', max_age=60 * 60 * 24 * 180)
        rdv_id = data.get('rdv_id')
    except Exception:
        return render(request, 'rendez_vous/public_invalid_link.html', {
            'page_title': 'Lien invalide',
        }, status=404)

    rendez_vous = get_object_or_404(
        RendezVous.objects.select_related('visiteur', 'motif', 'correspondant'),
        pk=rdv_id,
    )

    if getattr(rendez_vous, 'statut', None) != 'confirme':
        return render(request, 'rendez_vous/public_invalid_link.html', {
            'page_title': 'Lien invalide',
        }, status=404)

    # Générer et télécharger le PDF directement
    from .utils import generer_preuve_pdf
    pdf_buffer = generer_preuve_pdf(rendez_vous)
    nom_pdf = f"preuve_rdv_{rendez_vous.visiteur.nom}_{rendez_vous.date_rendez_vous.strftime('%Y%m%d')}.pdf"

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nom_pdf}"'
    return response


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


# Vues pour la gestion des audiences confirmées
@module_permission_required('visites', 'delete')
def audiences_confirmees_supprimer(request):
    """Vue pour supprimer toutes les audiences confirmées"""
    motif_audience = _get_motif_audience_ministre()
    
    if not motif_audience:
        messages.error(request, "Aucun motif d'audience ministre trouvé")
        return redirect('visites:index')
    
    if request.method == 'POST':
        try:
            # Récupérer les audiences confirmées (visites avec le motif audience et statut 'terminee')
            audiences_confirmees = Visite.objects.filter(
                motif=motif_audience,
                statut='terminee'
            )
            
            count = audiences_confirmees.count()
            if count == 0:
                messages.info(request, "Aucune audience confirmée à supprimer")
            else:
                audiences_confirmees.delete()
                messages.success(request, f'{count} audience(s) confirmée(s) supprimée(s) avec succès')
                
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression: {str(e)}')
    
    return redirect('visites:index')


@module_permission_required('visites', 'view')
def audiences_confirmees_exporter(request):
    """Vue pour exporter les audiences confirmées en CSV"""
    motif_audience = _get_motif_audience_ministre()
    
    if not motif_audience:
        messages.error(request, "Aucun motif d'audience ministre trouvé")
        return redirect('visites:index')
    
    try:
        # Récupérer les audiences confirmées
        audiences_confirmees = Visite.objects.filter(
            motif=motif_audience,
            statut='terminee'
        ).order_by('-date_visite', '-heure_entree')
        
        if audiences_confirmees.count() == 0:
            messages.info(request, "Aucune audience confirmée à exporter")
            return redirect('visites:index')
        
        # Créer la réponse CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="audiences_confirmees_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Écrire l'en-tête CSV
        writer = csv.writer(response)
        writer.writerow([
            'ID Visite', 'Visiteur', 'Téléphone', 'Email', 'Date', 'Heure entrée', 
            'Heure sortie', 'Correspondant', 'Département', 'Observations', 
            'Agent entrée', 'Agent sortie'
        ])
        
        # Écrire les données
        for visite in audiences_confirmees:
            writer.writerow([
                visite.pk,
                f"{visite.visiteur.prenoms} {visite.visiteur.nom}",
                visite.visiteur.telephone or '',
                visite.visiteur.email or '',
                visite.date_visite.strftime('%d/%m/%Y'),
                visite.heure_entree.strftime('%H:%M'),
                visite.heure_sortie.strftime('%H:%M') if visite.heure_sortie else '',
                f"{visite.correspondant.prenoms} {visite.correspondant.nom}" if visite.correspondant else '',
                visite.correspondant.departement if visite.correspondant else '',
                visite.observations.replace('\n', ' ') if visite.observations else '',
                visite.agent_entree,
                visite.agent_sortie or ''
            ])
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'exportation: {str(e)}')
        return redirect('visites:index')


# Vues pour la gestion des rendez-vous
@module_permission_required('rendez_vous', 'delete')
def rendez_vous_supprimer_confirmees(request):
    """Vue pour supprimer tous les rendez-vous confirmés"""
    if request.method == 'POST':
        try:
            # Récupérer les rendez-vous confirmés
            rdv_confirmees = RendezVous.objects.filter(statut='confirme')
            
            count = rdv_confirmees.count()
            if count == 0:
                messages.info(request, "Aucun rendez-vous confirmé à supprimer")
            else:
                rdv_confirmees.delete()
                messages.success(request, f'{count} rendez-vous confirmé(s) supprimé(s) avec succès')
                
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression: {str(e)}')
    
    return redirect('visites:rendez_vous_list')


@module_permission_required('rendez_vous', 'delete')
def rendez_vous_supprimer_tous(request):
    """Vue pour supprimer tous les rendez-vous (sauf annulés)"""
    if request.method == 'POST':
        try:
            # Récupérer tous les rendez-vous sauf les annulés
            rdv_tous = RendezVous.objects.exclude(statut='annule')
            
            count = rdv_tous.count()
            if count == 0:
                messages.info(request, "Aucun rendez-vous à supprimer")
            else:
                rdv_tous.delete()
                messages.success(request, f'{count} rendez-vous supprimé(s) avec succès')
                
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression: {str(e)}')
    
    return redirect('visites:rendez_vous_list')


@module_permission_required('rendez_vous', 'view')
def rendez_vous_exporter(request):
    """Vue pour exporter les rendez-vous en CSV"""
    statut_filter = request.GET.get('statut', 'tous')
    
    try:
        # Filtrer selon le statut
        if statut_filter == 'tous':
            rdv_list = RendezVous.objects.all().order_by('-date_rendez_vous', '-heure_debut')
        elif statut_filter == 'confirme':
            rdv_list = RendezVous.objects.filter(statut='confirme').order_by('-date_rendez_vous', '-heure_debut')
        elif statut_filter == 'termine':
            rdv_list = RendezVous.objects.filter(statut='termine').order_by('-date_rendez_vous', '-heure_debut')
        elif statut_filter == 'planifie':
            rdv_list = RendezVous.objects.filter(statut='planifie').order_by('-date_rendez_vous', '-heure_debut')
        else:
            rdv_list = RendezVous.objects.exclude(statut='annule').order_by('-date_rendez_vous', '-heure_debut')
        
        if rdv_list.count() == 0:
            messages.info(request, "Aucun rendez-vous à exporter")
            return redirect('visites:rendez_vous_list')
        
        # Créer la réponse CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="rendez_vous_{statut_filter}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Écrire l'en-tête CSV
        writer = csv.writer(response)
        writer.writerow([
            'ID RDV', 'Visiteur', 'Téléphone', 'Email', 'Date RDV', 'Heure début', 
            'Heure fin', 'Motif', 'Correspondant', 'Sujet', 'Statut', 'Priorité',
            'Description', 'Date création', 'Créé par'
        ])
        
        # Écrire les données
        for rdv in rdv_list:
            writer.writerow([
                rdv.pk,
                f"{rdv.visiteur.prenoms} {rdv.visiteur.nom}",
                rdv.visiteur.telephone or '',
                rdv.visiteur.email or '',
                rdv.date_rendez_vous.strftime('%d/%m/%Y'),
                rdv.heure_debut.strftime('%H:%M'),
                rdv.heure_fin.strftime('%H:%M') if rdv.heure_fin else '',
                rdv.motif.libelle,
                f"{rdv.correspondant.prenoms} {rdv.correspondant.nom}" if rdv.correspondant else '',
                rdv.sujet,
                rdv.get_statut_display(),
                rdv.get_priorite_display(),
                rdv.description.replace('\n', ' ') if rdv.description else '',
                rdv.date_creation.strftime('%d/%m/%Y %H:%M'),
                f"{rdv.cree_par.prenoms} {rdv.cree_par.nom}" if rdv.cree_par else ''
            ])
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'exportation: {str(e)}')
        return redirect('visites:rendez_vous_list')


@module_permission_required('agenda', 'view')
def agenda_ministre_public_cabinet(request):
    """Vue pour l'agenda du ministre avec URL courte pour le cabinet"""
    import base64
    import hashlib
    from django.core import signing
    from django.utils import timezone
    
    # Créer un token simple et court pour le cabinet
    # Utiliser un code fixe simple: "cabinet-2024"
    simple_token = "cabinet-2024"
    
    # Créer un token signé avec les données du cabinet
    token_data = {
        'audience': 'ministre',
        'cabinet': True,
        'code': simple_token,
        'expires': (timezone.now().date() + timezone.timedelta(days=365)).isoformat()  # Convertir en string
    }
    
    # Utiliser le même salt que agenda_ministre_public
    token = signing.dumps(token_data, salt='agenda_ministre_public', key='cabinet-agenda-key-2024')
    
    # Rediriger vers l'agenda public avec le token
    return redirect('visites:agenda_ministre_public', token=token)


def agenda_ministre_public_direct(request):
    """Vue directe pour l'agenda du ministre avec token fixe ultra court"""
    from django.core import signing
    from django.utils import timezone
    
    # Token fixe et court pour le cabinet
    token_data = {
        'audience': 'ministre',
        'cabinet': True,
        'direct': True,
        'expires': (timezone.now().date() + timezone.timedelta(days=365)).isoformat()  # Convertir en string
    }
    
    # Générer un token avec le même salt que agenda_ministre_public
    token = signing.dumps(token_data, salt='agenda_ministre_public', key='cabinet-direct-2024')
    
    # Afficher directement l'agenda public avec ce token
    request.token = token
    return agenda_ministre_public(request, token)
