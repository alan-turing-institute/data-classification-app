# Generated by Django 3.1.13 on 2022-06-07 09:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0022_alter_field_history_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataset',
            name='host',
        ),
        migrations.RemoveField(
            model_name='dataset',
            name='storage_path',
        ),
    ]
