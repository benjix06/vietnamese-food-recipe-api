"""
Serializer for recipe APIs
"""
from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes"""

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'time_minutes', 'price', 'link'
        ]
        read_only_fields = ['id']


class RecipeDetailSerializer(RecipeSerializer):
    """Serialier for recipe detail (having id)"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]


# class TagSerializer(RecipeSerializer):
#     """Serialier for recipe detail (having id)"""

#     class Meta(RecipeSerializer.Meta):
#         fields = RecipeSerializer.Meta.fields + ["description"]
