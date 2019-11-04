# Generated by Django 2.1 on 2019-10-21 13:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0030_auto_20191001_1307'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='workpackageparticipant',
            name='work_package',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_package_participants', to='projects.WorkPackage'),
        ),
    ]