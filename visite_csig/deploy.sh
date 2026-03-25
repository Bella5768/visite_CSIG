#!/bin/bash

# Script de déploiement automatique pour PythonAnywhere
# Usage: bash deploy.sh

echo "🚀 Déploiement du système CSIG sur PythonAnywhere..."

# Navigation vers le projet
echo "📁 Navigation vers le projet..."
cd ~/visite-csig || { echo "❌ Erreur: Répertoire introuvable"; exit 1; }

# Mise à jour depuis GitHub
echo "📥 Mise à jour depuis GitHub..."
git pull origin master || { echo "❌ Erreur: Git pull failed"; exit 1; }

# Activation environnement virtuel
echo "🐍 Activation de l'environnement virtuel..."
source virtualenv/bin/activate || { echo "❌ Erreur: Environnement virtuel introuvable"; exit 1; }

# Installation dépendances
echo "📦 Installation des dépendances..."
pip install django==4.2.28 whitenoise pillow qrcode[pil] reportlab || { echo "❌ Erreur: Installation dépendances"; exit 1; }

# Application des migrations
echo "🗄️ Application des migrations..."
python manage.py migrate || { echo "❌ Erreur: Migration failed"; exit 1; }

# Collecte des fichiers statiques
echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput || { echo "❌ Erreur: Collectstatic failed"; exit 1; }

# Configuration email (optionnel - décommenter si nécessaire)
# echo "📧 Configuration email..."
# export EMAIL_HOST=smtp.gmail.com
# export EMAIL_PORT=587
# export EMAIL_USE_TLS=True
# export EMAIL_HOST_USER=votre_email@gmail.com
# export EMAIL_HOST_PASSWORD=votre_mot_de_passe_app
# export DEFAULT_FROM_EMAIL=votre_email@gmail.com

# Test de configuration
echo "✅ Test de configuration Django..."
python manage.py check || { echo "❌ Erreur: Django check failed"; exit 1; }

echo "🎉 Déploiement terminé avec succès !"
echo ""
echo "📋 Actions manuelles requises :"
echo "1. Allez dans l'interface web PythonAnywhere"
echo "2. Cliquez sur 'Web' → 'Reload' pour redémarrer l'application"
echo "3. Configurez les variables d'environnement email si nécessaire"
echo ""
echo "🌐 URLs disponibles :"
echo "- Formulaire RDV : https://votrenom.pythonanywhere.com/rdv/"
echo "- Administration : https://votrenom.pythonanywhere.com/administration/"
echo "- Admin Django : https://votrenom.pythonanywhere.com/admin/"
