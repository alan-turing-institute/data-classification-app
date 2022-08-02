# Generated by Django 3.1.13 on 2022-05-04 16:22

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0038_workpackage_populate_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workpackage',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]