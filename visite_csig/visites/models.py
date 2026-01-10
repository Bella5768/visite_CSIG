from django.db import models
from django.conf import settings
from django.utils import timezone
from visiteurs.models import Visiteur
from core.models import Correspondant, MotifVisite


class Visite(models.Model):
    STATUT_CHOICES = settings.STATUTS_VISITE
    TYPE_VISITE_CHOICES = settings.TYPES_VISITE
    
    visiteur = models.ForeignKey(Visiteur, on_delete=models.CASCADE, related_name='visites')
    motif = models.ForeignKey(MotifVisite, on_delete=models.PROTECT)
    correspondant = models.ForeignKey(Correspondant, on_delete=models.SET_NULL, null=True, blank=True)
    type_visite = models.CharField(max_length=50, choices=TYPE_VISITE_CHOICES, default='professionnelle')
    date_visite = models.DateField(default=timezone.now)
    heure_entree = models.TimeField()
    heure_sortie = models.TimeField(null=True, blank=True)
    observations = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours')
    agent_entree = models.CharField(max_length=100, blank=True)
    agent_sortie = models.CharField(max_length=100, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Visite'
        ordering = ['-date_visite', '-heure_entree']
    
    def __str__(self):
        return f"Visite de {self.visiteur} le {self.date_visite}"
    
    def get_duree(self):
        if not self.heure_sortie:
            return 'En cours'
        from datetime import datetime
        entree = datetime.combine(self.date_visite, self.heure_entree)
        sortie = datetime.combine(self.date_visite, self.heure_sortie)
        diff = sortie - entree
        total_minutes = int(diff.total_seconds() / 60)
        heures, minutes = divmod(total_minutes, 60)
        return f"{heures}h {minutes}min" if heures else f"{minutes}min"
    
    def enregistrer_sortie(self, agent_sortie):
        self.heure_sortie = timezone.now().time()
        self.agent_sortie = agent_sortie
        self.statut = 'terminee'
        self.save()
    
    def annuler(self, raison):
        self.statut = 'annulee'
        self.observations = f"{self.observations}\n[ANNULEE] {raison}" if self.observations else f"[ANNULEE] {raison}"
        self.save()
