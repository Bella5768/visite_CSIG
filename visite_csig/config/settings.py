from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-visite-csig-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', '.pythonanywhere.com']

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000', 
    'http://localhost:8000', 
    'http://127.0.0.1:55006',
    'https://boubacar32.pythonanywhere.com',
    'http://boubacar32.pythonanywhere.com',
    'http://127.0.0.1:58635',
    'http://localhost:58635',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    'core',
    'visites',
    'visiteurs',
    'rapports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.app_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

# Configuration email multi-fournisseurs
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Configuration principale (Gmail par défaut)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'True'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'True'

# Identifiants
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'noreply@csig-guinee.org')

# Configuration pour le développement (commenter pour tester)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configurations pré-définies selon le fournisseur
# Pour Gmail:
# EMAIL_HOST=smtp.gmail.com, EMAIL_PORT=587, EMAIL_USE_TLS=True
# Pour Outlook/Hotmail:
# EMAIL_HOST=smtp-mail.outlook.com, EMAIL_PORT=587, EMAIL_USE_TLS=True
# Pour Yahoo:
# EMAIL_HOST=smtp.mail.yahoo.com, EMAIL_PORT=587, EMAIL_USE_TLS=True
# Pour Orange:
# EMAIL_HOST=smtp.orange.fr, EMAIL_PORT=587, EMAIL_USE_TLS=True

AUTH_USER_MODEL = 'core.Utilisateur'
LOGIN_URL = 'core:login'
LOGIN_REDIRECT_URL = 'core:dashboard'

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Conakry'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

APP_NAME = 'Visite CSIG'
APP_VERSION = '2.0'

TYPES_IDENTITE = [
    ('cni', 'Carte Nationale d\'Identité'),
    ('passeport', 'Passeport'),
    ('permis', 'Permis de conduire'),
    ('autre', 'Autre'),
]

STATUTS_VISITE = [
    ('en_cours', 'En cours'),
    ('terminee', 'Terminée'),
    ('annulee', 'Annulée'),
]

TYPES_VISITE = [
    ('professionnelle', 'Professionnelle'),
    ('personnelle', 'Personnelle'),
]
