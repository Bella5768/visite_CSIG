from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import qrcode, io, json
from .utils import generate_badge_pdf

from .models import Visite
from visiteurs.models import Visiteur
from core.models import MotifVisite, Correspondant


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
