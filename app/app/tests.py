from django.test import SimpleTestCase

from app import cal

class CalTest(SimpleTestCase):
    
    def test_add(self):
        res = cal.add(5,4)
        
        self.assertEqual(res,9)