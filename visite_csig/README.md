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

1. Uploader le projet
2. Créer virtualenv et installer requirements
3. Configurer Web app avec WSGI
4. Collecter les fichiers statiques: `python manage.py collectstatic`

## Identifiants par défaut

- **Utilisateur**: admin
- **Mot de passe**: admin123
