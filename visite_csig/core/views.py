from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Utilisateur, MotifVisite, Correspondant
from visites.models import Visite
from visiteurs.models import Visiteur


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
    return render(request, 'core/dashboard.html', {
        'page_title': 'Tableau de bord',
        'visites_jour': Visite.objects.filter(date_visite=today).count(),
        'visites_en_cours': Visite.objects.filter(date_visite=today, statut='en_cours').count(),
        'total_visiteurs': Visiteur.objects.count(),
        'visites_mois': Visite.objects.filter(date_visite__month=today.month).count(),
        'dernieres_visites': Visite.objects.filter(date_visite=today).select_related('visiteur', 'motif')[:10],
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
