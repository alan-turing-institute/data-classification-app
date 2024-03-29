# Generated by Django 3.1.13 on 2022-04-26 12:42

from django.db import migrations, models
import django.db.models.deletion

def insert_default_questionset(apps, schema_editor):
    ClassificationQuestionSet = apps.get_model('data', 'ClassificationQuestionSet')
    default_question_set = ClassificationQuestionSet(name="turing")
    default_question_set.save()

class Migration(migrations.Migration):

    dependencies = [
        ('data', '0023_remove_host_and_storage_path'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassificationQuestionSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True)),
                ('description', models.TextField()),
            ],
        ),
        migrations.RunPython(insert_default_questionset),
        migrations.AlterField(
            model_name='classificationquestion',
            name='name',
            field=models.CharField(max_length=256),
        ),
        migrations.AlterField(
            model_name='historicalclassificationquestion',
            name='name',
            field=models.CharField(max_length=256),
        ),
        migrations.AddField(
            model_name='classificationquestion',
            name='question_set',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='data.classificationquestionset'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalclassificationquestion',
            name='question_set',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='data.classificationquestionset'),
        ),
        migrations.AlterUniqueTogether(
            name='classificationquestion',
            unique_together={('name', 'question_set')},
        ),
    ]
