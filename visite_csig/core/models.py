from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.utils import OperationalError
from django.utils import timezone


class UtilisateurManager(BaseUserManager):
    def create_user(self, nom_utilisateur, password=None, **extra_fields):
        if not nom_utilisateur:
            raise ValueError('Le nom d\'utilisateur est obligatoire')
        user = self.model(nom_utilisateur=nom_utilisateur, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, nom_utilisateur, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(nom_utilisateur, password, **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [('agent', 'Agent'), ('admin', 'Administrateur'), ('superadmin', 'Super Administrateur')]
    
    nom_utilisateur = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='agent')
    poste = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    objects = UtilisateurManager()
    USERNAME_FIELD = 'nom_utilisateur'
    REQUIRED_FIELDS = ['nom', 'prenoms']
    
    class Meta:
        verbose_name = 'Utilisateur'
    
    def __str__(self):
        return f"{self.prenoms} {self.nom}"
    
    @property
    def is_admin(self):
        return self.role == 'admin'

    def has_module_permission(self, module_code, action):
        if self.role == 'superadmin':
            return True
        if not self.is_active:
            return False
        if action not in ['view', 'add', 'change', 'delete']:
            return False
        perm = getattr(self, 'permissions', None)
        if perm is None:
            return False
        try:
            p = perm.filter(module=module_code).first()
        except OperationalError:
            # Migrations not applied yet: fall back to role-based access to avoid crashing.
            return self.role in ['admin', 'superadmin']
        if not p:
            return False
        return getattr(p, f"can_{action}")


class PermissionUtilisateur(models.Model):
    MODULE_CHOICES = [
        ('visites', 'Visites'),
        ('rendez_vous', 'Rendez-vous'),
        ('visiteurs', 'Visiteurs'),
        ('rapports', 'Rapports'),
        ('agenda', 'Agenda'),
        ('administration', 'Administration'),
        ('utilisateurs', 'Utilisateurs'),
    ]

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='permissions')
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_change = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('utilisateur', 'module')
        verbose_name = 'Permission utilisateur'
        verbose_name_plural = 'Permissions utilisateurs'

    def __str__(self):
        return f"{self.utilisateur} - {self.module}"


class MotifVisite(models.Model):
    libelle = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Motif de visite'
        ordering = ['libelle']
    
    def __str__(self):
        return self.libelle


class Correspondant(models.Model):
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=100)
    fonction = models.CharField(max_length=100, blank=True)
    departement = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Correspondant'
        ordering = ['nom', 'prenoms']
    
    def __str__(self):
        return f"{self.prenoms} {self.nom} - {self.departement}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('rendez_vous', 'Nouveau rendez-vous'),
        ('confirmation', 'Rendez-vous confirmé'),
        ('annulation', 'Rendez-vous annulé'),
        ('modification', 'Rendez-vous modifié'),
        ('visite', 'Nouvelle visite'),
        ('systeme', 'Notification système'),
    ]
    
    titre = models.CharField(max_length=200)
    message = models.TextField()
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES, default='systeme')
    
    # Destinataire
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    
    # État
    lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_lecture = models.DateTimeField(null=True, blank=True)
    
    # Lien optionnel vers l'objet concerné
    contenu_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.titre} - {self.utilisateur}"
    
    def marquer_comme_lue(self):
        if not self.lue:
            self.lue = True
            self.date_lecture = timezone.now()
            self.save(update_fields=['lue', 'date_lecture'])
    
    @classmethod
    def creer_notification(cls, titre, message, utilisateur, type_notification='systeme', objet=None):
        """
        Crée une notification pour un utilisateur
        """
        from django.contrib.contenttypes.models import ContentType
        
        notification = cls.objects.create(
            titre=titre,
            message=message,
            type_notification=type_notification,
            utilisateur=utilisateur
        )
        
        # Associer à un objet si fourni
        if objet:
            content_type = ContentType.objects.get_for_model(objet)
            notification.contenu_type = content_type
            notification.object_id = objet.pk
            notification.save(update_fields=['contenu_type', 'object_id'])
        
        return notification
