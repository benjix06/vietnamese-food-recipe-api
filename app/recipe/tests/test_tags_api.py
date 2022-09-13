"""
Test for tags API
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    """Create and return a tag detail URL"""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='example@example.com', password='secret123'):
    """Create and return a new user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tag"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Tehst authenticated API requests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tag(self):
        """Test retrieve a list of tags"""
        Tag.objects.create(user=self.user, name="Soup")
        Tag.objects.create(user=self.user, name="Fried")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated users"""
        user2 = create_user(email="new@example.com")  # Unauthenticated user
        Tag.objects.create(user=user2, name="Fruit")
        tag = Tag.objects.create(user=self.user, name="Comfort Food")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test udpate tag"""
        tag = Tag.objects.create(user=self.user, name="Dinner")
        pay_load = {
            'name': 'Dessert'
        }
        url = detail_url(tag.id)
        res = self.client.patch(url, pay_load)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()

        self.assertEqual(tag.name,  pay_load['name'])

    def test_delete_tag(self):
        """Test deleting a tag"""
        tag = Tag.objects.create(user=self.user, name="Bun")

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipe(self):
        """Test listing ingredients by those assigned to a recipe"""
        tag1 = Tag.objects.create(user=self.user, name='Dinner')
        tag2 = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = Recipe.objects.create(
            title='Bun Bo Hue',
            time_minutes=260,
            price=Decimal('25.00'),
            user=self.user,
        )
        recipe.tags.add(tag1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_tags_unique(self):
        """Test filtered ingredients return a unique list"""
        tag = Tag.objects.create(user=self.user, name='Lunch')
        Tag.objects.create(user=self.user, name='Dessert')
        recipe1 = Recipe.objects.create(
            title='Bun Ga',
            time_minutes=300,
            price=Decimal('35.00'),
            user=self.user,
        )

        recipe2 = Recipe.objects.create(
            title='Bun Bo',
            time_minutes=250,
            price=Decimal('34.00'),
            user=self.user,
        )

        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
