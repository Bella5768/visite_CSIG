from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-visite-csig-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', '.pythonanywhere.com']

CSRF_TRUSTED_ORIGINS = [
    'https://menaetfp.pythonanywhere.com',
    'http://menaetfp.pythonanywhere.com',
    'https://boubacar32.pythonanywhere.com',
    'http://boubacar32.pythonanywhere.com',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://127.0.0.1:52594',
    'http://localhost:52594',
]

# En mode DEBUG, on peut ajouter d'autres origines via la variable
# d'environnement CSRF_EXTRA_ORIGINS (ex: proxy Windsurf à port dynamique).
if DEBUG:
    _extra = os.environ.get('CSRF_EXTRA_ORIGINS', '')
    if _extra:
        CSRF_TRUSTED_ORIGINS += [o.strip() for o in _extra.split(',') if o.strip()]

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

# Configuration SendGrid - fonctionne avec tous les domaines
# Pour utiliser SendGrid, créez un compte gratuit sur https://sendgrid.com/
# et obtenez votre API Key dans Settings > API Keys
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')

# Identifiants SendGrid (remplacez par votre clé API réelle)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'apikey')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'SG.MCSLHKQMR15R94L7GWBPCJD4')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Cabinet MENA-ETFP <noreply@menaetfp.gn>')

# Timeout SMTP
EMAIL_TIMEOUT = 30

# Configuration EmailJS (envoi via API REST - https://www.emailjs.com/)
# Créez un compte gratuit, configurez un service email et un template,
# puis renseignez les identifiants ci-dessous.
# Dashboard EmailJS:
#  - Service ID : Email Services > votre service
#  - Template ID : Email Templates > votre template
#  - Public Key / Private Key : Account > General
EMAILJS_SERVICE_ID = os.environ.get('EMAILJS_SERVICE_ID', 'service_dzf7alq')
EMAILJS_TEMPLATE_ID = os.environ.get('EMAILJS_TEMPLATE_ID', 'template_vb1ojbm')
EMAILJS_PUBLIC_KEY = os.environ.get('EMAILJS_PUBLIC_KEY', 'DmHMKv0FI7BVr0fGw')
EMAILJS_PRIVATE_KEY = os.environ.get('EMAILJS_PRIVATE_KEY', 'u-CR5VtSndzFJkHugYj0L')
# Active EmailJS si les identifiants sont renseignés
USE_EMAILJS = bool(EMAILJS_SERVICE_ID and EMAILJS_TEMPLATE_ID and EMAILJS_PUBLIC_KEY)

# Configuration pour le développement (commenter pour tester)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configurations pré-définies selon le fournisseur
# Pour SendGrid - recommandé:
# EMAIL_HOST=smtp.sendgrid.net, EMAIL_PORT=587, EMAIL_USE_TLS=True, EMAIL_HOST_USER=apikey, EMAIL_HOST_PASSWORD=SG.YOUR_API_KEY
# Pour Brevo (Sendinblue):
# EMAIL_HOST=smtp-relay.brevo.com, EMAIL_PORT=587, EMAIL_USE_TLS=True
# Pour Gmail:
# EMAIL_HOST=smtp.gmail.com, EMAIL_PORT=587, EMAIL_USE_TLS=True
# Pour Outlook/Hotmail:
# EMAIL_HOST=smtp-mail.outlook.com, EMAIL_PORT=587, EMAIL_USE_TLS=True

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

APP_NAME = 'MENA-ETFP'
APP_VERSION = '2.0'

# URL publique du site (pour les images dans les emails)
SITE_PUBLIC_URL = os.environ.get('SITE_PUBLIC_URL', 'https://boubacar32.pythonanywhere.com')

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
