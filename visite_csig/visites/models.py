from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q
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


class RendezVous(models.Model):
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('confirme', 'Confirmé'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]
    
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]
    
    visiteur = models.ForeignKey(Visiteur, on_delete=models.CASCADE, related_name='rendez_vous')
    motif = models.ForeignKey(MotifVisite, on_delete=models.PROTECT)
    correspondant = models.ForeignKey(Correspondant, on_delete=models.SET_NULL, null=True, blank=True)

    creneau = models.ForeignKey(
        'CreneauDisponibilite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rendez_vous',
    )
    
    date_rendez_vous = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='planifie')
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='normale')
    
    sujet = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    notes_confidentielles = models.TextField(blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='rendez_vous_crees'
    )
    
    class Meta:
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        ordering = ['date_rendez_vous', 'heure_debut']
        constraints = [
            models.UniqueConstraint(
                fields=['creneau'],
                condition=~Q(statut='annule'),
                name='unique_rdv_actif_par_creneau',
            )
        ]
    
    def __str__(self):
        return f"RDV {self.sujet} - {self.visiteur} le {self.date_rendez_vous} à {self.heure_debut}"
    
    def clean(self):
        if self.heure_fin and self.heure_debut:
            if self.heure_fin <= self.heure_debut:
                raise ValidationError("L'heure de fin doit être postérieure à l'heure de début")
        
        if self.date_rendez_vous and self.date_rendez_vous < timezone.now().date():
            raise ValidationError("La date du rendez-vous ne peut pas être dans le passé")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_duree(self):
        if not self.heure_fin:
            return None
        from datetime import datetime
        debut = datetime.combine(self.date_rendez_vous, self.heure_debut)
        fin = datetime.combine(self.date_rendez_vous, self.heure_fin)
        diff = fin - debut
        total_minutes = int(diff.total_seconds() / 60)
        heures, minutes = divmod(total_minutes, 60)
        return f"{heures}h {minutes}min" if heures else f"{minutes}min"
    
    def est_a_venir(self):
        now = timezone.now()
        rdv_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date_rendez_vous, self.heure_debut)
        )
        return rdv_datetime > now
    
    def est_en_retard(self):
        if self.statut in ['termine', 'annule']:
            return False
        now = timezone.now()
        rdv_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date_rendez_vous, self.heure_debut)
        )
        return rdv_datetime < now
    
    def confirmer(self):
        if self.statut == 'planifie':
            self.statut = 'confirme'
            super().save(update_fields=['statut', 'date_modification'])
    
    def annuler(self, raison=""):
        self.statut = 'annule'
        if raison:
            self.description = f"{self.description}\n[ANNULE] {raison}" if self.description else f"[ANNULE] {raison}"
        super().save(update_fields=['statut', 'description', 'date_modification'])
    
    def commencer(self):
        if self.statut in ['planifie', 'confirme']:
            self.statut = 'en_cours'
            super().save(update_fields=['statut', 'date_modification'])
    
    def terminer(self):
        if self.statut == 'en_cours':
            self.statut = 'termine'
            super().save(update_fields=['statut', 'date_modification'])


class CreneauDisponibilite(models.Model):
    motif = models.ForeignKey(MotifVisite, on_delete=models.PROTECT, related_name='creneaux_disponibilite')
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    capacite = models.PositiveIntegerField(default=1)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Créneau de disponibilité'
        verbose_name_plural = 'Créneaux de disponibilité'
        ordering = ['date', 'heure_debut']

    def __str__(self):
        return f"{self.motif} - {self.date} {self.heure_debut}-{self.heure_fin}"

    def clean(self):
        if self.heure_fin and self.heure_debut and self.heure_fin <= self.heure_debut:
            raise ValidationError("L'heure de fin doit être postérieure à l'heure de début")
        if self.date and self.date < timezone.now().date():
            raise ValidationError("La date du créneau ne peut pas être dans le passé")
        if self.capacite != 1:
            raise ValidationError("La capacité d'un créneau est fixée à 1 (un rendez-vous par créneau)")

    def get_nb_reservations(self):
        return self.rendez_vous.exclude(statut='annule').count()

    def get_places_restantes(self):
        return 0 if self.get_nb_reservations() >= 1 else 1

    def est_disponible(self):
        return self.actif and self.get_nb_reservations() == 0
