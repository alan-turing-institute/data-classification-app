# Generated by Django 3.1.13 on 2022-04-27 08:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0024_add_classification_questionset'),
    ]

    operations = [
        migrations.AddField(
            model_name='classificationguidance',
            name='question_set',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='guidance', to='data.classificationquestionset'),
            preserve_default=False,
        ),
    ]
