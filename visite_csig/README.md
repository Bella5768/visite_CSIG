# Visite CSIG

Système de gestion des visites - Django

## Installation locale

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Déploiement PythonAnywhere

### 1. Uploader le projet
- Uploadez le dossier `visite_csig` dans `/home/boubacar32/`

### 2. Créer l'environnement virtuel
```bash
cd /home/boubacar32/visite_csig
mkvirtualenv --python=/usr/bin/python3.10 visite_env
pip install -r requirements.txt
```

### 3. Configurer la base de données
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

### 4. Configurer le fichier WSGI
Dans Web > WSGI configuration file, remplacez par:
```python
import os
import sys

path = '/home/boubacar32/visite_csig'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 5. Configurer les fichiers statiques
- URL: `/static/`
- Directory: `/home/boubacar32/visite_csig/staticfiles/`

### 6. Recharger l'application
Cliquez sur "Reload" dans l'onglet Web

## Identifiants par défaut

- **Utilisateur**: admin
- **Mot de passe**: admin123
