# Generated by Django 3.1.13 on 2022-05-04 15:05
import uuid

from django.db import migrations


def gen_uuid(apps, schema_editor):
    MyModel = apps.get_model('identity', 'user')
    for row in MyModel.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=['uuid'])


class Migration(migrations.Migration):

    dependencies = [
        ('identity', '0020_user_uuid'),
    ]

    operations = [
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
    ]
