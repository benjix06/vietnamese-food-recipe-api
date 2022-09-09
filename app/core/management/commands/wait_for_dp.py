"""
Django command to wait for the databse to be available
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for databse"""
    
    def handle(self, *args, **options):
        pass
    