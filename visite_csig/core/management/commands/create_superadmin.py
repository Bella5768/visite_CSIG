from django.core.management.base import BaseCommand
from core.models import Utilisateur


class Command(BaseCommand):
    help = 'Créer un Super Administrateur'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nom d\'utilisateur')
        parser.add_argument('--password', type=str, help='Mot de passe')
        parser.add_argument('--nom', type=str, help='Nom de famille')
        parser.add_argument('--prenoms', type=str, help='Prénom(s)')

    def handle(self, *args, **options):
        username = options.get('username') or input('Nom d\'utilisateur: ')
        password = options.get('password') or input('Mot de passe: ')
        nom = options.get('nom') or input('Nom: ')
        prenoms = options.get('prenoms') or input('Prénom(s): ')
        
        if Utilisateur.objects.filter(nom_utilisateur=username).exists():
            self.stdout.write(self.style.ERROR(f'L\'utilisateur "{username}" existe déjà'))
            
            # Proposer de le convertir en superadmin
            convert = input('Voulez-vous le convertir en Super Admin? (o/n): ')
            if convert.lower() == 'o':
                user = Utilisateur.objects.get(nom_utilisateur=username)
                user.role = 'superadmin'
                user.is_staff = True
                user.is_superuser = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'"{username}" est maintenant Super Admin'))
            return
        
        user = Utilisateur.objects.create_user(
            nom_utilisateur=username,
            password=password,
            nom=nom,
            prenoms=prenoms,
            role='superadmin',
            is_staff=True,
            is_superuser=True,
        )
        
        self.stdout.write(self.style.SUCCESS(f'Super Admin "{prenoms} {nom}" créé avec succès!'))
        self.stdout.write(f'  - Nom d\'utilisateur: {username}')
        self.stdout.write(f'  - Rôle: Super Administrateur')
