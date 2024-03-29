# Generated by Django 2.1 on 2019-09-02 14:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0027_auto_20190902_1401'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkPackageParticipant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('participant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='projects.Participant')),
                ('work_package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='projects.WorkPackage')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='workpackage',
            name='participants',
            field=models.ManyToManyField(blank=True, related_name='work_packages', through='projects.WorkPackageParticipant', to='projects.Participant'),
        ),
    ]
