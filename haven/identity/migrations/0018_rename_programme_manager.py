# Generated by Django 2.1 on 2019-06-03 16:22

from django.db import migrations, models


def update_programme_manager(apps, schema_editor):
    User = apps.get_model('identity', 'User')
    for next_user in User.objects.all():
        role = next_user.role
        if role == "research_coordinator":
            role = "programme_manager"
        next_user.role = role
        next_user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('identity', '0017_rename_system_manager'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(blank=True, choices=[('system_manager', 'System Manager'), ('programme_manager', 'Programme Manager'), ('', '')], help_text="The user's role in the system", max_length=50),
        ),
        migrations.RunPython(
            code=update_programme_manager,
        ),
    ]
