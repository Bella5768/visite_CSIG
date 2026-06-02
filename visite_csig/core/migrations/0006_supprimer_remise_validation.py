from django.db import migrations


def desactiver_remise_validation(apps, schema_editor):
    """Désactive le motif 'Remise de validation officielle' s'il existe."""
    MotifVisite = apps.get_model('core', 'MotifVisite')
    MotifVisite.objects.filter(libelle__icontains='remise de validation').update(actif=False)


def restaurer_remise_validation(apps, schema_editor):
    """Réactive le motif (rollback)."""
    MotifVisite = apps.get_model('core', 'MotifVisite')
    MotifVisite.objects.filter(libelle__icontains='remise de validation').update(actif=True)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_motifs_visite_publics'),
    ]

    operations = [
        migrations.RunPython(desactiver_remise_validation, restaurer_remise_validation),
    ]
