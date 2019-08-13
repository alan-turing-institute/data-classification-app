# Generated by Django 2.1 on 2019-07-09 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0009_dataset_default_representative'),
        ('projects', '0019_remove_project_datasets'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='datasets2',
        ),
        migrations.AddField(
            model_name='project',
            name='datasets',
            field=models.ManyToManyField(blank=True, related_name='projects', through='projects.ProjectDataset', to='data.Dataset'),
        ),
    ]
