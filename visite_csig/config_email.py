"""
Script de configuration et test des emails pour différents fournisseurs
"""
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def tester_configuration_email():
    """Teste la configuration email actuelle"""
    print("🔧 Test de la configuration email...")
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Port: {settings.EMAIL_PORT}")
    print(f"TLS: {settings.EMAIL_USE_TLS}")
    print(f"SSL: {settings.EMAIL_USE_SSL}")
    print(f"User: {settings.EMAIL_HOST_USER}")
    print(f"From: {settings.DEFAULT_FROM_EMAIL}")
    print()
    
    try:
        sujet = "🧪 Test de configuration email - CSIG"
        message = """
Ceci est un email de test pour vérifier que la configuration SMTP fonctionne correctement.

Si vous recevez cet email, cela signifie que :
✅ La connexion au serveur SMTP est établie
✅ Les identifiants sont corrects
✅ L'envoi d'emails fonctionne

Vous pouvez maintenant utiliser le système de rendez-vous avec notifications automatiques.

Cité des Sciences et de l'Innovation de Guinée
        """
        
        send_mail(
            sujet,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],  # Envoie à soi-même pour tester
            fail_silently=False,
        )
        
        print("[OK] Email de test envoye avec succes!")
        print(f"Verifiez votre boite de reception: {settings.EMAIL_HOST_USER}")
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors de l'envoi: {e}")
        print("\nSolutions possibles:")
        print("1. Verifiez vos identifiants email")
        print("2. Pour Gmail: utilisez un 'mot de passe d'application'")
        print("3. Verifiez que le pare-feu ne bloque pas le port SMTP")
        print("4. Assurez-vous que l'authentification 2FA est configuree correctement")

def configurer_gmail():
    """Guide de configuration pour Gmail"""
    print("\nConfiguration pour Gmail:")
    print("1. Allez dans: https://myaccount.google.com/")
    print("2. → Securite → Authentification a 2 facteurs (activez-la)")
    print("3. → Securite → Mots de passe des applications")
    print("4. Creez un nouveau mot de passe d'application")
    print("5. Utilisez ce mot de passe dans EMAIL_HOST_PASSWORD")
    print("\nVariables d'environnement a definir:")
    print("EMAIL_HOST=smtp.gmail.com")
    print("EMAIL_PORT=587")
    print("EMAIL_USE_TLS=True")
    print("EMAIL_HOST_USER=votre_email@gmail.com")
    print("EMAIL_HOST_PASSWORD=le_mot_de_passe_application")

def configurer_outlook():
    """Guide de configuration pour Outlook"""
    print("\nConfiguration pour Outlook/Hotmail:")
    print("1. Utilisez votre email et mot de passe habituels")
    print("2. Activez l'authentification 2 facteurs si necessaire")
    print("\nVariables d'environnement a definir:")
    print("EMAIL_HOST=smtp-mail.outlook.com")
    print("EMAIL_PORT=587")
    print("EMAIL_USE_TLS=True")
    print("EMAIL_HOST_USER=votre_email@outlook.com")
    print("EMAIL_HOST_PASSWORD=votre_mot_de_passe")

if __name__ == "__main__":
    print("Configuration Email - CSIG")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "gmail":
            configurer_gmail()
        elif sys.argv[1] == "outlook":
            configurer_outlook()
        elif sys.argv[1] == "test":
            tester_configuration_email()
        else:
            print("Usage: python config_email.py [gmail|outlook|test]")
    else:
        print("Choisissez une option:")
        print("python config_email.py gmail    - Guide Gmail")
        print("python config_email.py outlook  - Guide Outlook") 
        print("python config_email.py test    - Tester la configuration")
