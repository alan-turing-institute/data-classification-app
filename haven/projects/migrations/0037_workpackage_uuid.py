# Generated by Django 3.1.13 on 2022-05-04 16:18

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0036_project_programmes'),
    ]

    operations = [
        migrations.AddField(
            model_name='workpackage',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4),
        ),
    ]
