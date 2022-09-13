"""
Tesets for a recipe AIPs
"""
from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create and return a recipe details URL based on the recipe ID"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return a image upload URL based on the recipe ID"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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
        self.client.force_authenticate(self.user)

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
        # Patch - partial update request
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
            'tags': [{'name': 'Lunch'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tag(self):
        """Test clearing a recipe tag"""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        pay_load = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_ingredient(self):
        """Test creating an ingredient"""
        user = create_user(
            email='hello@example.com', password='password123'
        )
        ingredient = Ingredient.objects.create(
            user=user,
            name='Noddle'
        )

        self.assertEqual(str(ingredient), ingredient.name)

    def test_create_recipe_with_new_ingredient(self):
        """Test creating a new recipe with new ingredient using API"""

        pay_load = {
            'title': 'Lau Chua Cay',
            'time_minutes': 120,
            'price': Decimal('30.00'),
            'ingredients': [{'name': 'Bun'}, {'name': 'Hai san'}],
        }

        res = self.client.post(RECIPES_URL, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in pay_load['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a recipe with an existing ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Rice')

        pay_load = {
            'title': 'Chao',
            'time_minutes': 25,
            'price': Decimal('10.02'),
            'ingredients': [{'name': 'Rice'}, {'name': 'Water'}],
        }

        res = self.client.post(RECIPES_URL, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())

        for ingredient in pay_load['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a recipe"""
        recipe = create_recipe(user=self.user)

        pay_load = {
            'ingredients': [{'name': 'Lemon'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(
            user=self.user, name='Lemon')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Pork')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Chili')

        # Update the ingredient in recipe
        pay_load = {
            'ingredients': [{'name': 'Chili'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredient(self):
        """test clearing a recipe's ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Chicken')

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        pay_load = {
            'ingredients': []
        }

        url = detail_url(recipe.id)

        # Update the ingredient in recipe
        res = self.client.patch(url, pay_load, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


class ImageUploadTests(TestCase):
    """Test for the image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "example@example.com",
            "password",
        )

        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test upload image"""
        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            pay_load = {
                'image': image_file,
            }
            res = self.client.post(url, pay_load, format='multipart')

        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_bad_image(self):
        """Test uploading bad image requests."""
        url = image_upload_url(self.recipe.id)
        pay_load = {
            'image': 'notanimage'
        }

        res = self.client.post(url, pay_load, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
