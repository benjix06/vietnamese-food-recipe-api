"""
Serializer for the user API View

Serializer:
A way to convert objects to and from Python objects
Takes adjacent input that might be posted from the API and validate the input
to make sure that it is secure and valid
Then it convert to Python object that we can use or a model in database

"""
from django.contrib.auth import get_user_model

from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""

    class Meta:
        model = get_user_model()
        fields = ["email", "password", "name"]
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 5
            },
        }

    # Only get called when the data is valid
    def create(self, validated_data):
        """Create and return a user with encrypted password"""
        return get_user_model().objects.create_user(**validated_data)