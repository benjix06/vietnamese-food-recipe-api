"""
Views for the recipe APIs
"""

from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from recipe import serializers

# Create your views here.


class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs"""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve recipes for authenticated users"""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for the request"""
        if self.action == 'list':
            return serializers.RecipeSerializer

        return self.serializer_class

    # Override the behavior when django framework saves a model in the Viewset
    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)


class ViewSet(mixins.DestroyModelMixin,
              mixins.UpdateModelMixin,
              mixins.ListModelMixin,
              viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated users"""
        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagViewSet(ViewSet):
    """Manage tags in the databse"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(ViewSet):
    """Manage ingredients in the databse"""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
