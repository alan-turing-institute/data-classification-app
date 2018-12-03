from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Check AAD for newly created users'

    def handle(self, *args, **options):
        print("Checking for new users")
