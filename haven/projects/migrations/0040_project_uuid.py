# Generated by Django 3.1.13 on 2022-05-04 16:32

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0039_workpackage_uuid_unique_non_editable'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4),
        ),
    ]
