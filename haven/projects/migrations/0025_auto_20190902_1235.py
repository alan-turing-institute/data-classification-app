# Generated by Django 2.1 on 2019-09-02 12:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0024_auto_20190806_0801'),
    ]

    operations = [
        migrations.RenameField(
            model_name='classificationopinion',
            old_name='user',
            new_name='created_by',
        ),
    ]
