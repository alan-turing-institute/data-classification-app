# Generated by Django 2.1 on 2020-02-04 11:22

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('projects', '0035_workpackage_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='programmes',
            field=taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]