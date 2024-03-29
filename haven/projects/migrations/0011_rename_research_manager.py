# Generated by Django 2.1 on 2019-06-03 15:24

from django.db import migrations, models
import haven.projects.models


def update_project_manager(apps, schema_editor):
    Participant = apps.get_model('projects', 'Participant')
    for next_participant in Participant.objects.all():
        role = next_participant.role
        if role == "research_coordinator":
            role = "project_manager"
        next_participant.role = role
        next_participant.save()


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0010_auto_20190527_1429'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='role',
            field=models.CharField(choices=[('referee', 'Referee'), ('project_manager', 'Research Coordinator'), ('investigator', 'Investigator'), ('researcher', 'Researcher'), ('data_provider_representative', 'Data Provider Representative')], help_text="The participant's role on this project", max_length=50, validators=[haven.projects.models.validate_role]),
        ),
        migrations.RunPython(
            code=update_project_manager,
        ),
    ]
