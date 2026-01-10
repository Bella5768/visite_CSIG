from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


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
    ROLE_CHOICES = [('agent', 'Agent'), ('admin', 'Administrateur')]
    
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
