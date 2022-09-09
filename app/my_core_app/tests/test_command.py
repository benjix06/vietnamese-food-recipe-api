"""
Test custom Django management commands.
"""
from unittest.mock import patch

from psycopg2 import OperationalError as Psycopg2Error

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase

@patch('my_core_app.management.commands.wait_for_db.Command.check')
class CommandTest(SimpleTestCase):
    """Test commands"""
    
    def test_wait_for_db_ready(self, patched_check):
        """Test waiting database if it's ready"""
        patched_check.return_value = True
        
        call_command('wait_for_db')
        
        patched_check.assert_called_once_with(database=['default'])
        