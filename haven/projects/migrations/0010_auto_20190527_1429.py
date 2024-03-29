# Generated by Django 2.1 on 2019-05-27 14:29

from django.db import migrations, models
import django.db.models.deletion
import haven.projects.models

from haven.projects import policies


def insert_initial_policies(apps, schema_editor):
    Policy = apps.get_model('projects', 'Policy')
    PolicyGroup = apps.get_model('projects', 'PolicyGroup')
    PolicyAssignment = apps.get_model('projects', 'PolicyAssignment')
    policies.insert_initial_policies(PolicyGroup, Policy, PolicyAssignment)


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0009_auto_20181231_1244'),
    ]

    operations = [
        migrations.CreateModel(
            name='Policy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='PolicyAssignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tier', models.PositiveSmallIntegerField(choices=[(0, 'Tier 0'), (1, 'Tier 1'), (2, 'Tier 2'), (3, 'Tier 3'), (4, 'Tier 4')])),
                ('policy', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='projects.Policy')),
            ],
        ),
        migrations.CreateModel(
            name='PolicyGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('description', models.TextField()),
            ],
        ),
        migrations.AlterField(
            model_name='participant',
            name='role',
            field=models.CharField(choices=[('referee', 'Referee'), ('research_coordinator', 'Research Coordinator'), ('investigator', 'Investigator'), ('researcher', 'Researcher'), ('data_provider_representative', 'Data Provider Representative')], help_text="The participant's role on this project", max_length=50, validators=[haven.projects.models.validate_role]),
        ),
        migrations.AddField(
            model_name='policy',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='projects.PolicyGroup'),
        ),
        migrations.RunPython(insert_initial_policies, migrations.RunPython.noop),
    ]
