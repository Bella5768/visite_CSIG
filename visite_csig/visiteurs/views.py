from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.conf import settings
from .models import Visiteur


@login_required
def index(request):
    search = request.GET.get('search', '')
    visiteurs = Visiteur.objects.annotate(nb_visites=Count('visites'))
    if search:
        visiteurs = visiteurs.filter(Q(nom__icontains=search) | Q(prenoms__icontains=search) | Q(telephone__icontains=search))
    paginator = Paginator(visiteurs, 20)
    return render(request, 'visiteurs/index.html', {'page_title': 'Visiteurs', 'visiteurs': paginator.get_page(request.GET.get('page', 1)), 'search_term': search})


@login_required
def ajouter(request):
    if request.method == 'POST':
        visiteur = Visiteur.objects.create(
            nom=request.POST.get('nom'), prenoms=request.POST.get('prenoms'),
            type_identite=request.POST.get('type_identite', ''),
            numero_identite=request.POST.get('numero_identite') or None,
            telephone=request.POST.get('telephone', ''), email=request.POST.get('email', ''),
            adresse=request.POST.get('adresse', '')
        )
        messages.success(request, 'Visiteur créé')
        if 'save_and_visit' in request.POST:
            return redirect('visites:nouvelle_visite_visiteur', visiteur_id=visiteur.id)
        return redirect('visiteurs:index')
    return render(request, 'visiteurs/ajouter.html', {'page_title': 'Nouveau visiteur', 'types_identite': settings.TYPES_IDENTITE})


@login_required
def modifier(request, pk):
    visiteur = get_object_or_404(Visiteur, pk=pk)
    if request.method == 'POST':
        visiteur.nom, visiteur.prenoms = request.POST.get('nom'), request.POST.get('prenoms')
        visiteur.type_identite = request.POST.get('type_identite', '')
        visiteur.numero_identite = request.POST.get('numero_identite') or None
        visiteur.telephone, visiteur.email = request.POST.get('telephone', ''), request.POST.get('email', '')
        visiteur.adresse = request.POST.get('adresse', '')
        visiteur.save()
        messages.success(request, 'Visiteur modifié')
        return redirect('visiteurs:index')
    return render(request, 'visiteurs/modifier.html', {'page_title': 'Modifier visiteur', 'visiteur': visiteur, 'types_identite': settings.TYPES_IDENTITE})


@login_required
def historique(request, pk):
    visiteur = get_object_or_404(Visiteur, pk=pk)
    return render(request, 'visiteurs/historique.html', {'page_title': f'Historique - {visiteur}', 'visiteur': visiteur, 'visites': visiteur.visites.select_related('motif', 'correspondant')})


@login_required
def rechercher(request):
    q = request.GET.get('q', '')
    visiteurs = Visiteur.objects.filter(Q(nom__icontains=q) | Q(prenoms__icontains=q) | Q(telephone__icontains=q)).annotate(nb_visites=Count('visites'))[:20] if q else []
    return render(request, 'visiteurs/rechercher.html', {'page_title': 'Rechercher', 'visiteurs': visiteurs, 'search_term': q})


@login_required
def api_search(request):
    q = request.GET.get('q', '')
    if len(q) < 2:
        return JsonResponse({'results': []})
    visiteurs = Visiteur.objects.filter(Q(nom__icontains=q) | Q(prenoms__icontains=q) | Q(telephone__icontains=q))[:10]
    return JsonResponse({'results': [{'id': v.id, 'nom': v.nom, 'prenoms': v.prenoms, 'telephone': v.telephone} for v in visiteurs]})
