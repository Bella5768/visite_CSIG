from django.core.management.base import BaseCommand
from core.models import MotifVisite


class Command(BaseCommand):
    help = 'Initialise les motifs de visite par défaut'

    def handle(self, *args, **options):
        motifs = [
            'Réunion professionnelle',
            'Formation',
            'Visite guidée',
            'Recherche documentaire',
            'Entretien d\'embauche',
            'Maintenance/Réparation',
            'Livraison',
            'Visite libre',
            'Conférence/Séminaire',
            'Autre',
        ]
        
        created_count = 0
        for libelle in motifs:
            obj, created = MotifVisite.objects.get_or_create(
                libelle=libelle,
                defaults={'actif': True}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Motif créé: {libelle}'))
            else:
                self.stdout.write(f'Motif existant: {libelle}')
        
        self.stdout.write(self.style.SUCCESS(f'\n{created_count} motifs créés sur {len(motifs)}'))
