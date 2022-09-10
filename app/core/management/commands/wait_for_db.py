"""
Django command to wait for the databse to be available
"""
import time

from psycopg2 import OperationalError as Psycopg2OpError

from django.core.management.base import BaseCommand

# Error that Django throws when data base is not ready
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for databse"""

    def handle(self, *args, **options):
        """Entrypoint for command"""
        self.stdout.write(" Waiting for database ...")

        db_up = False

        while not db_up:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write("Database is unavailable,\
                                  waiting 1 second...")
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS("Database is available!"))
