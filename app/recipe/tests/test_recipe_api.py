"""
Tesets for a recipe AIPs
"""
from decimal import Decimal
from genericpath import exists
from hashlib import new

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create and return a recipe details URL based on the recipe ID"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a recipe"""
    defaults = {
        "title": 'Sample Recipe',
        'time_minutes': 22,
        'price': Decimal('5.50'),
        'description': 'Sample Recipe Description',
        'link': 'https://example.com/recipe.pdf'
    }

    defaults.update(params)

    recipes = Recipe.objects.create(user=user, **defaults)
    return recipes


def create_user(**params):
    """Create a new user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='password123',
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated users"""
        other_user = create_user(
            email='use1r@example.com',
            password='password123',
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)  # authenticated user

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe through API"""
        pay_load = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': Decimal('8.19'),
        }
        res = self.client.post(RECIPES_URL, pay_load)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for key, value in pay_load.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update a recipe (small part of the recipe)"""
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe',
            link=original_link,
        )

        # Only update the title of the recipe
        pay_load = {
            'title': 'new etitle',
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, pay_load)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, pay_load['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update a recipe"""
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe',
            link='http://example.com/recipe.pdf',
            description='Sample Recipe description'
        )

        pay_load = {
            'title': 'Sample Recipe new',
            'link': 'http://example.com/recipe-new.pdf',
            'description': 'Sample Recipe description new',
            'time_minutes': 39,
            'price': Decimal('5.19'),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, pay_load)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for key, value in pay_load.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_create_recipe_with_new_tags(self):
        """Createing a recipe with new tags"""
        pay_load = {
            'title': 'Bun Bo Hue',
            'time_minutes': 240,
            'price': Decimal('50.19'),
            'tags': [
                {'name': 'Bun'},
                {'name': 'Dinner'}
            ]
        }
        res = self.client.post(RECIPES_URL, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]

        self.assertEqual(recipe.tags.count(), 2)
        for tag in pay_load['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags"""
        tag_pho = Tag.objects.create(user=self.user, name="Pho")
        pay_load = {
            'title': 'Pho Ga',
            'time_minutes': 300,
            'price': Decimal('55'),
            'tags': [
                {'name': 'Pho'},
                {'name': 'Breakfast'}
            ]
        }

        res = self.client.post(RECIPES_URL, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]

        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_pho, recipe.tags.all())
        for tag in pay_load['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating a tag when updating a recipe"""
        recipe = create_recipe(user=self.user)
        pay_load = {
            'tags': [
                {'name': 'Lunch'}
            ]
        }
        url = detail_url(recipe.id)
        # Pathc - partial update request
        res = self.client.patch(url, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""

        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        pay_load = {
            'tag': [{'name': 'Lunch'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # self.assertIn(tag_lunch, recipe.tags.all())
        self.assertIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tag(self):
        """Test clearing a recipe tag"""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        pay_load = {'tag': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
