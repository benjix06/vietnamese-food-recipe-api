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

TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    # Public Test - Unauthenticated request
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
        user_exists = get_user_model().objects.filter(
            email=pay_load['email']).exists()

        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test create token for user"""
        user_details = {
            'name': 'test name',
            'email': 'test@example.com',
            'password': 'test-user-password',
        }
        create_user(**user_details)

        pay_load = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URL, pay_load)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials are invalid"""
        create_user(email='test@example.com', password='test123')

        pay_load = {
            'email': 'test@example.com',
            'password': 'badpass',
        }
        res = self.client.post(TOKEN_URL, pay_load)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error"""
        pay_load = {
            'email': 'test@example.com',
            'password': '',
        }
        res = self.client.post(TOKEN_URL, pay_load)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(
            email="test@example.com",
            password="testpassword",
            name="test user"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        """Test POST ist not allowed for the me URL endpoint"""
        # Me URL should only be used when we create object in the system
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating user profile for the authenticated user"""
        pay_load = {
            'name': "update name",
            "password": "update-password",
        }
        res = self.client.patch(ME_URL, pay_load)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, pay_load['name'])
        self.assertTrue(self.user.check_password, pay_load['password'])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
