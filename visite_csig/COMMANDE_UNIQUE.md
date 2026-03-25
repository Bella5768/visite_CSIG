# Déploiement PythonAnywhere - Une Commande

## 🚀 Commande unique de déploiement

Copiez-collez cette commande complète dans votre console PythonAnywhere :

```bash
cd ~/visite-csig && git pull origin master && source virtualenv/bin/activate && pip install django==4.2.28 whitenoise pillow qrcode[pil] reportlab && python manage.py migrate && python manage.py collectstatic --noinput && python manage.py check && echo "✅ Déploiement terminé ! Allez dans Web → Reload pour redémarrer l'application"
```

## 📋 Décomposition de la commande

| Commande | Action |
|----------|--------|
| `cd ~/visite-csig` | Navigation vers le projet |
| `git pull origin master` | Mise à jour depuis GitHub |
| `source virtualenv/bin/activate` | Activation environnement virtuel |
| `pip install django==4.2.28 whitenoise pillow qrcode[pil] reportlab` | Installation dépendances |
| `python manage.py migrate` | Application migrations |
| `python manage.py collectstatic --noinput` | Collecte fichiers statiques |
| `python manage.py check` | Vérification configuration |
| `echo "✅ Déploiement terminé !"` | Confirmation succès |

## 🎯 Actions supplémentaires (manuelles)

### 1. Redémarrer l'application
- Allez dans **Web tab** → **Reload**

### 2. Configuration Email (optionnelle)
```bash
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=votre_email@gmail.com
export EMAIL_HOST_PASSWORD=votre_mot_de_passe_app
export DEFAULT_FROM_EMAIL=votre_email@gmail.com
```

### 3. Test email
```bash
python config_email.py test
```

## 🌐 URLs après déploiement

- **Formulaire RDV** : `https://votrenom.pythonanywhere.com/rdv/`
- **Administration** : `https://votrenom.pythonanywhere.com/administration/`
- **Admin Django** : `https://votrenom.pythonanywhere.com/admin/`

## ⚡ Version rapide (si déjà configuré)

Si vous avez déjà déployé et juste besoin de mettre à jour :

```bash
cd ~/visite-csig && git pull && python manage.py migrate && python manage.py collectstatic --noinput
```

Puis **Reload** dans l'interface web.
