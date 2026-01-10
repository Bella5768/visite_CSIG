from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
import json

from visites.models import Visite
from visiteurs.models import Visiteur
from .utils import export_rapport_pdf


@login_required
def rapport_journalier(request):
    date = request.GET.get('date', str(timezone.now().date()))
    visites = Visite.objects.filter(date_visite=date).select_related('visiteur', 'motif', 'correspondant')
    stats = {'total': visites.count(), 'en_cours': visites.filter(statut='en_cours').count(), 'terminees': visites.filter(statut='terminee').count(), 'annulees': visites.filter(statut='annulee').count()}
    par_motif = visites.values('motif__libelle').annotate(count=Count('id')).order_by('-count')
    if request.GET.get('export') == 'pdf':
        pdf_buffer = export_rapport_pdf(visites, date, stats)
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_{date}.pdf"'
        return response
    return render(request, 'rapports/rapport_journalier.html', {'page_title': 'Rapport journalier', 'date': date, 'visites': visites, 'stats': stats, 'par_motif': par_motif})


@login_required
def statistiques(request):
    today = timezone.now().date()
    stats_globales = {
        'total_visiteurs': Visiteur.objects.count(),
        'total_visites': Visite.objects.count(),
        'visites_mois': Visite.objects.filter(date_visite__month=today.month, date_visite__year=today.year).count(),
        'visites_jour': Visite.objects.filter(date_visite=today).count(),
    }
    top_visiteurs = Visiteur.objects.annotate(nb_visites=Count('visites')).order_by('-nb_visites')[:10]
    repartition_motifs = Visite.objects.values('motif__libelle').annotate(count=Count('id')).order_by('-count')[:10]
    evolution = [{'jour': str(today - timedelta(days=i)), 'count': Visite.objects.filter(date_visite=today - timedelta(days=i)).count()} for i in range(30, -1, -1)]
    return render(request, 'rapports/statistiques.html', {'page_title': 'Statistiques', 'stats_globales': stats_globales, 'top_visiteurs': top_visiteurs, 'repartition_motifs': repartition_motifs, 'evolution': json.dumps(evolution)})
