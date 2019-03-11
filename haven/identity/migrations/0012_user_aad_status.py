# Generated by Django 2.1 on 2018-11-28 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('identity', '0011_auto_20181109_1438'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='aad_status',
            field=models.CharField(blank=True, choices=[('failed_to_create', 'Creation failed'), ('pending', 'Pending'), ('created', 'Created'), ('activated', 'Activated')], max_length=16),
        ),
    ]
