"""
Test for Ingredient for the API
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Create and return an ingredient detail URL based on ID"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='password'):
    """Create and return a new user"""
    return get_user_model().objects.create_user(email, password)


class PublicIngredientApiTests(TestCase):
    """Tests for unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving ingredients"""
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test for authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()

        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name='Pork')
        Ingredient.objects.create(user=self.user, name='Salad')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_limited_ingredients(self):
        """Test limited ingredients to user"""
        user2 = create_user(email='newuser@example.com')
        Ingredient.objects.create(user=user2, name='Salt')

        ingredient = Ingredient.objects.create(
            user=self.user, name='Sugar')  # Different user

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """Test updating an ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Beef')

        pay_load = {
            'name': 'American Beef',
        }

        url = detail_url(ingredient.id)
        res = self.client.patch(url, pay_load)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, pay_load['name'])

    def test_delete_ingredient(self):
        """Test deleting an existing ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Noddle')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipe(self):
        """Test listing ingredients by those assigned to a recipe"""
        in1 = Ingredient.objects.create(user=self.user, name='Water')
        in2 = Ingredient.objects.create(user=self.user, name='Beef')
        recipe = Recipe.objects.create(
            title='Bun Bo Hue',
            time_minutes=260,
            price=Decimal('25.00'),
            user=self.user,
        )
        recipe.ingredients.add(in1)
        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_ingredients_unique(self):
        """Test filtered ingredients return a unique list"""
        ing = Ingredient.objects.create(user=self.user, name='Chicken')
        Ingredient.objects.create(user=self.user, name='Pork')
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

        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
