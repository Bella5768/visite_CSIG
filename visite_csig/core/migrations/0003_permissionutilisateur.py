from django.db import migrations, models
import django.db.models.deletion


MODULES = [
    'visites',
    'rendez_vous',
    'visiteurs',
    'rapports',
    'agenda',
    'administration',
    'utilisateurs',
]


def create_default_permissions(apps, schema_editor):
    Utilisateur = apps.get_model('core', 'Utilisateur')
    PermissionUtilisateur = apps.get_model('core', 'PermissionUtilisateur')

    for user in Utilisateur.objects.all():
        if user.role == 'superadmin':
            continue

        # Defaults aligned with current role-based behavior
        if user.role == 'admin':
            defaults = {
                'visites': dict(view=True, add=True, change=True, delete=True),
                'rendez_vous': dict(view=True, add=True, change=True, delete=True),
                'visiteurs': dict(view=True, add=True, change=True, delete=True),
                'rapports': dict(view=True, add=True, change=True, delete=True),
                'agenda': dict(view=True, add=False, change=False, delete=False),
                'administration': dict(view=True, add=True, change=True, delete=True),
                'utilisateurs': dict(view=True, add=True, change=True, delete=False),
            }
        else:
            defaults = {
                'visites': dict(view=True, add=True, change=True, delete=False),
                'rendez_vous': dict(view=True, add=True, change=True, delete=False),
                'visiteurs': dict(view=True, add=True, change=True, delete=False),
                'rapports': dict(view=True, add=False, change=False, delete=False),
                'agenda': dict(view=True, add=False, change=False, delete=False),
                'administration': dict(view=False, add=False, change=False, delete=False),
                'utilisateurs': dict(view=False, add=False, change=False, delete=False),
            }

        for module in MODULES:
            p = defaults.get(module, dict(view=False, add=False, change=False, delete=False))
            PermissionUtilisateur.objects.update_or_create(
                utilisateur_id=user.id,
                module=module,
                defaults={
                    'can_view': p['view'],
                    'can_add': p['add'],
                    'can_change': p['change'],
                    'can_delete': p['delete'],
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_utilisateur_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='PermissionUtilisateur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module', models.CharField(choices=[('visites', 'Visites'), ('rendez_vous', 'Rendez-vous'), ('visiteurs', 'Visiteurs'), ('rapports', 'Rapports'), ('agenda', 'Agenda'), ('administration', 'Administration'), ('utilisateurs', 'Utilisateurs')], max_length=50)),
                ('can_view', models.BooleanField(default=False)),
                ('can_add', models.BooleanField(default=False)),
                ('can_change', models.BooleanField(default=False)),
                ('can_delete', models.BooleanField(default=False)),
                ('utilisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permissions', to='core.utilisateur')),
            ],
            options={
                'verbose_name': 'Permission utilisateur',
                'verbose_name_plural': 'Permissions utilisateurs',
                'unique_together': {('utilisateur', 'module')},
            },
        ),
        migrations.RunPython(create_default_permissions, migrations.RunPython.noop),
    ]
