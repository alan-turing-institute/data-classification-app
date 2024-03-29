# Generated by Django 2.1 on 2018-10-23 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('identity', '0004_help_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='role',
            field=models.CharField(choices=[('referee', 'Referee'), ('investigator', 'Investigator'), ('researcher', 'Researcher')], help_text="The participant's role on this project", max_length=50),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(blank=True, choices=[('system_controller', 'System Controller'), ('research_coordinator', 'Research Coordinator'), ('data_provider_representative', 'Data Provider Representative')], help_text="The user's role in the system", max_length=50),
        ),
    ]
