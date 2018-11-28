
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Check AAD for newly created users'

    def handle(self, *args, **options):
        print("Checking for new users")
