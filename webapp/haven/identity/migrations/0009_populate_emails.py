# Generated by Django 2.1 on 2018-11-09 12:32

from django.db import migrations


def populate_email_addresses(apps, schema_editor):
    # Ensure all users have an email address before we make the field unique.
    # Use the username if it looks like an email address, or append a dummy
    # domain if it doesn't.
    # This is done early on in development so there shouldn't be problems
    # with doing this :)
    User = apps.get_model('identity', 'User')
    for user in User.objects.all():
        if not user.email:
            if '@' in user.username:
                user.email = user.username
            else:
                user.email = user.username + '@example.com'
            user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('identity', '0008_remove_participant_table'),
    ]

    operations = [
        migrations.RunPython(populate_email_addresses, migrations.RunPython.noop)
    ]
