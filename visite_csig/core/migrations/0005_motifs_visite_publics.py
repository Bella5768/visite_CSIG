from django.db import migrations


MOTIFS_PUBLICS = [
    {
        'libelle': 'Visite officielle',
        'description': "Visite officielle du lundi au jeudi, créneau 13h-16h. L'administrateur précisera l'heure exacte lors de la confirmation.",
    },
]


def creer_motifs_publics(apps, schema_editor):
    MotifVisite = apps.get_model('core', 'MotifVisite')
    for data in MOTIFS_PUBLICS:
        MotifVisite.objects.update_or_create(
            libelle=data['libelle'],
            defaults={'description': data['description'], 'actif': True},
        )


def supprimer_motifs_publics(apps, schema_editor):
    MotifVisite = apps.get_model('core', 'MotifVisite')
    MotifVisite.objects.filter(
        libelle__in=[d['libelle'] for d in MOTIFS_PUBLICS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_notification'),
    ]

    operations = [
        migrations.RunPython(creer_motifs_publics, supprimer_motifs_publics),
    ]
