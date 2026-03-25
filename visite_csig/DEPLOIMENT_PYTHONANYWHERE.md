# Guide de Déploiement - PythonAnywhere

## 🚀 Commandes à exécuter sur PythonAnywhere

### 1. Connexion à la console
```bash
# Connectez-vous à PythonAnywhere et ouvrez la console Bash
```

### 2. Navigation vers le projet
```bash
cd ~/visite-csig  # ou le nom de votre projet
```

### 3. Mise à jour depuis GitHub
```bash
# Récupérer les dernières modifications
git pull origin master

# Vérifier le statut
git status
```

### 4. Installation des dépendances
```bash
# Activer l'environnement virtuel (si nécessaire)
source virtualenv/bin/activate

# Installer les nouvelles dépendances
pip install -r requirements.txt

# Ou si pas de requirements.txt :
pip install django==4.2.28 whitenoise pillow qrcode[pil] reportlab
```

### 5. Appliquer les migrations
```bash
python manage.py migrate
```

### 6. Collecter les fichiers statiques
```bash
python manage.py collectstatic --noinput
```

### 7. Configuration des variables d'environnement (Email)
```bash
# Option 1 : Créer un fichier .env
cat > .env << EOF
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre_email@gmail.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe_application
DEFAULT_FROM_EMAIL=votre_email@gmail.com
EOF

# Option 2 : Exporter directement
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=votre_email@gmail.com
export EMAIL_HOST_PASSWORD=votre_mot_de_passe_application
export DEFAULT_FROM_EMAIL=votre_email@gmail.com
```

### 8. Test de configuration email
```bash
# Tester la configuration email
python config_email.py test
```

### 9. Redémarrage de l'application web
```bash
# Via l'interface web PythonAnywhere :
# 1. Allez dans "Web" tab
# 2. Cliquez sur "Reload" pour votre application
```

### 10. Vérification
```bash
# Vérifier que tout fonctionne
python manage.py check
```

## 📧 Configuration Email - Gmail

### Étapes préalables (sur votre compte Gmail) :
1. Activez l'authentification à 2 facteurs
2. Allez dans : https://myaccount.google.com/apppasswords
3. Créez un "mot de passe d'application"
4. Utilisez ce mot de passe (16 caractères)

### Variables à configurer :
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=votre_email@gmail.com
EMAIL_HOST_PASSWORD=le_mot_de_passe_application_16_caracteres
DEFAULT_FROM_EMAIL=votre_email@gmail.com
```

## 🔧 Dépannage

### Problèmes courants :

#### Erreur de migration
```bash
# Si erreur de migration, vérifier l'état
python manage.py showmigrations

# Forcer la migration si nécessaire
python manage.py migrate --fake
```

#### Erreur de fichiers statiques
```bash
# Vider et recréer les fichiers statiques
rm -rf staticfiles/*
python manage.py collectstatic --noinput --clear
```

#### Erreur email
```bash
# Tester avec console backend (temporairement)
# Dans settings.py :
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Puis tester
python config_email.py test
```

#### Permissions
```bash
# Vérifier les permissions des fichiers
chmod -R 755 .
chown -R $USER:$USER .
```

## 🌐 URLs après déploiement

Votre application sera accessible via :
- **URL principale** : `https://votrenom.pythonanywhere.com/`
- **Formulaire RDV** : `https://votrenom.pythonanywhere.com/rdv/`
- **Administration** : `https://votrenom.pythonanywhere.com/administration/`
- **Admin Django** : `https://votrenom.pythonanywhere.com/admin/`

## 📋 Checklist de déploiement

- [ ] Git pull réussi
- [ ] Dépendances installées
- [ ] Migrations appliquées
- [ ] Fichiers statiques collectés
- [ ] Variables d'environnement configurées
- [ ] Email testé et fonctionnel
- [ ] Application web redémarrée
- [ ] URLs accessibles et fonctionnelles

## 🔄 Maintenance régulière

### Mises à jour hebdomadaires :
```bash
git pull origin master
python manage.py migrate
python manage.py collectstatic --noinput
# Redémarrer l'application web
```

### Sauvegarde base de données :
```bash
# Exporter la base de données
python manage.py dumpdata > backup_$(date +%Y%m%d).json
```

### Logs et monitoring :
```bash
# Vérifier les logs d'erreurs
tail -f ~/logs/user.log
```

---

**Note** : Remplacez `votrenom` par votre véritable nom d'utilisateur PythonAnywhere et `votre_email@gmail.com` par votre email configuré.
