"""
Database models
"""
import uuid
import os

from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)


def recipe_image_file_path(instance, file_name):
    """Generate file path for a new recipe image file"""
    ext = os.path.splitext(file_name)[1]
    file_name = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'recipe', file_name)


# Create your models here.
class UserManager(BaseUserManager):
    """Manager for users"""

    def create_user(self, email, password=None, **extra_field):
        """Create, save and return a new user"""
        if not email:
            raise ValueError("Please provide an email address")
        user = self.model(email=self.normalize_email(email), **extra_field)
        user.set_password(password)

        # Support to add multiple database
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser"""
        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""
    email = models.EmailField(max_length=30, unique=True)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"


class Recipe(models.Model):
    """Recipe object in the system"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    tags = models.ManyToManyField("Tag")
    ingredients = models.ManyToManyField("Ingredient")
    image = models.ImageField(null=True, upload_to=recipe_image_file_path)

    def __str__(self):
        return self.title


class Tag(models.Model):
    """Tag for filtering recipes"""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingredient for the recipe"""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name
