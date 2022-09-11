"""
Test for the user API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

# Getting the full URL path from the views
CREATE_USER_URL = reverse('user:create')

def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)

# Public Test - Unauthenticated request
class PublicUserApiTests(TestCase):
    """Test the public feature of the user API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user if it's successful"""
        pay_load = {
            'email': 'test@example.com',
            "password": 'test123',
            'name': 'test name',
        }

        res = self.client.post(CREATE_USER_URL, pay_load)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=pay_load['email'])
        self.assertTrue(user.check_password(pay_load['password']))

        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error when creating user with existing emails"""
        pay_load = {
            'email': 'test@example.com',
            "password": 'test123',
            'name': 'test name',
        }

        create_user(**pay_load)
        res = self.client.post(CREATE_USER_URL, pay_load)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error if password is less than 5 characters"""
        pay_load = {
            'email': 'test@example.com',
            "password": '123',
            'name': 'test name',
        }

        res = self.client.post(CREATE_USER_URL, pay_load)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=pay_load['email']).exists()

        self.assertFalse(user_exists)
