# Generated by Django 2.1 on 2018-11-09 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('identity', '0009_populate_emails'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='email address'),
        ),
    ]
