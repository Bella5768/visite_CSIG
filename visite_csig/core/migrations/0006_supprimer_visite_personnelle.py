from django.db import migrations


def supprimer_visite_personnelle(apps, schema_editor):
    """Supprime le motif 'Visite personnelle' s'il existe."""
    MotifVisite = apps.get_model('core', 'MotifVisite')
    MotifVisite.objects.filter(libelle='Visite personnelle').delete()


def restaurer_visite_personnelle(apps, schema_editor):
    """Ne restaure rien (rollback vide)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_motifs_visite_publics'),
    ]

    operations = [
        migrations.RunPython(supprimer_visite_personnelle, restaurer_visite_personnelle),
    ]
