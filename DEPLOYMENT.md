# Déploiement de visite_CSIG sur PythonAnywhere

## 📋 Prérequis

1. **Compte PythonAnywhere** avec un nom d'utilisateur `menaetfp`
2. **Dépôt GitHub** : https://github.com/Bella5768/visite_CSIG.git
3. **Clé SSH** configurée entre GitHub et PythonAnywhere

## 🚀 Déploiement Manuel

### 1. Connexion à PythonAnywhere
```bash
ssh menaetfp@ssh.pythonanywhere.com
```

### 2. Cloner le projet (première fois)
```bash
git clone https://github.com/Bella5768/visite_CSIG.git
cd visite_CSIG
```

### 3. Créer l'environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configurer la base de données
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Configurer les variables d'environnement
Dans le dashboard PythonAnywhere → Web → Variables d'environnement :
```
SECRET_KEY=votre-clé-secrète
DEBUG=False
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
SITE_PUBLIC_URL=https://menaetfp.pythonanywhere.com
```

### 6. Configurer l'application web
Dans le dashboard PythonAnywhere → Web :
- **Source code** : `/home/menaetfp/visite_CSIG`
- **Working directory** : `/home/menaetfp/visite_CSIG`
- **Virtualenv** : `/home/menaetfp/visite_CSIG/venv`
- **WSGI configuration file** : `/home/menaetfp/visite_CSIG/config/wsgi.py`

### 7. Script WSGI
```python
import os
import sys

path = '/home/menaetfp/visite_CSIG'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## 🔄 Déploiement Automatique (GitHub Actions)

### 1. Générer une clé SSH
```bash
ssh-keygen -t rsa -b 4096 -C "pythonanywhere-deploy"
```

### 2. Ajouter la clé publique à PythonAnywhere
- Copier le contenu de `~/.ssh/id_rsa.pub`
- Ajouter dans PythonAnywhere → Account → SSH Keys

### 3. Ajouter la clé privée aux secrets GitHub
- Aller dans GitHub → Settings → Secrets and variables → Actions
- Ajouter `PYTHONANYWHERE_SSH_KEY` avec le contenu de `~/.ssh/id_rsa`

### 4. Activer les Actions
Le fichier `.github/workflows/deploy.yml` est déjà configuré. Chaque push sur `master` déclenchera le déploiement.

## 📝 Mises à jour

### Mise à jour manuelle
```bash
cd ~/visite_CSIG
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

### Recharger l'application
```bash
/usr/local/bin/pa_reload_webapp menaetfp
```

## 🐛 Débogage

### Vérifier les logs
```bash
tail -f /var/log/nginx/error.log
tail -f /var/log/apache2/error.log
```

### Tester l'application localement
```bash
cd ~/visite_CSIG
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

## 📊 Configuration spécifique

### Domaine configuré
- URL principale : https://menaetfp.pythonanywhere.com
- Domaines autorisés : `.pythonanywhere.com`

### Base de données
- SQLite3 configuré dans `settings.py`
- Fichier : `db.sqlite3`

### Fichiers statiques
- Gérés par WhiteNoise
- Collectés dans `staticfiles/`

## 🎯 Prochaines étapes

1. ✅ Configurer les variables d'environnement
2. ✅ Tester le déploiement manuel
3. ✅ Configurer GitHub Actions
4. 🔄 Déployer en production
5. 📈 Monitorer les performances
