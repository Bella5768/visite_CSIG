from django.db import models
from django.conf import settings


class Visiteur(models.Model):
    TYPE_IDENTITE_CHOICES = settings.TYPES_IDENTITE
    
    type_identite = models.CharField(max_length=50, choices=TYPE_IDENTITE_CHOICES, blank=True)
    numero_identite = models.CharField(max_length=100, blank=True, unique=True, null=True)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=150)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Visiteur'
        ordering = ['nom', 'prenoms']
    
    def __str__(self):
        return f"{self.prenoms} {self.nom}"
    
    def get_nb_visites(self):
        return self.visites.count()
    
    def get_derniere_visite(self):
        return self.visites.order_by('-date_visite', '-heure_entree').first()
