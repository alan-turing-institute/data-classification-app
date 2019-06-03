from django.db import migrations, models


def update_system_manager(apps, schema_editor):
    User = apps.get_model('identity', 'User')
    for next_user in User.objects.all():
        role = next_user.role
        if role == "system_controller":
            role = "system_manager"
        next_user.role = role
        next_user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('identity', '0016_custom_user_manager'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(blank=True, choices=[('system_manager', 'System Manager'), ('research_coordinator', 'Research Coordinator'), ('', '')], help_text="The user's role in the system", max_length=50),
        ),
        migrations.RunPython(
            code=update_system_manager,
        ),
    ]
