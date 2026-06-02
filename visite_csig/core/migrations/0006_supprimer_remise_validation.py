from django.db import migrations


def supprimer_remise_validation(apps, schema_editor):
    """Supprime le motif 'Remise de validation officielle' s'il existe."""
    MotifVisite = apps.get_model('core', 'MotifVisite')
    MotifVisite.objects.filter(libelle__icontains='remise de validation').delete()


def restaurer_remise_validation(apps, schema_editor):
    """Ne restaure rien (rollback vide)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_motifs_visite_publics'),
    ]

    operations = [
        migrations.RunPython(supprimer_remise_validation, restaurer_remise_validation),
    ]
