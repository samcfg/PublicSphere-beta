# File: backend/apps/ratings/serializers.py
# Complete fix for the rating serializer

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Rating
from apps.sources.models import SourceArea
from apps.connections.models import Connection
from apps.articles.models import Article

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for User model to include in nested serializations"""
    class Meta:
        model = User
        fields = ['id', 'username', 'reputation']
        read_only_fields = ['id', 'username', 'reputation']


class RatingSerializer(serializers.ModelSerializer):
    """Serializer for ratings"""
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = Rating
        fields = [
            'id', 'user', 'content_type', 'object_id', 
            'value', 'explanation', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate that:
        1. The content_type is valid
        2. The object_id corresponds to an existing object of the given content_type
        3. The value is within the allowed range (0-100)
        """
        content_type = data.get('content_type')
        object_id = data.get('object_id')
        value = data.get('value')
        
        # Validate content_type
        valid_content_types = [choice[0] for choice in Rating.CONTENT_TYPE_CHOICES]
        if content_type not in valid_content_types:
            raise serializers.ValidationError(
                {"content_type": f"Invalid content type. Must be one of: {', '.join(valid_content_types)}"}
            )
        
        # Validate object exists
        if not self._object_exists(content_type, object_id):
            raise serializers.ValidationError(
                {"object_id": f"No {content_type} found with ID {object_id}"}
            )
        
        # Validate value range
        if value is not None:
            if value < 0 or value > 100:
                raise serializers.ValidationError(
                    {"value": "Value must be between 0 and 100"}
                )
        
        return data
    
    def _object_exists(self, content_type, object_id):
        """Check if an object of the given content_type and object_id exists"""
        if content_type == 'source_area':
            # Sources use UUIDs
            return SourceArea.objects.filter(id=object_id).exists()
        elif content_type == 'connection':
            # Connections use integers - convert object_id to int
            try:
                connection_id = int(object_id)
                return Connection.objects.filter(id=connection_id).exists()
            except (ValueError, TypeError):
                return False
        elif content_type == 'article':
            # Articles use UUIDs
            return Article.objects.filter(id=object_id).exists()
        return False
    
    def create(self, validated_data):
        """Create or update rating"""
        # Get user from validated_data (passed by view's perform_create)
        user = validated_data.pop('user', None)
        if not user:
            # Fallback to context if not in validated_data
            user = self.context['request'].user
        
        content_type = validated_data['content_type']
        object_id = str(validated_data['object_id'])  # Ensure it's stored as string
        
        # Try to get existing rating
        try:
            rating = Rating.objects.get(
                user=user,
                content_type=content_type,
                object_id=object_id
            )
            # Update existing rating
            for attr, value in validated_data.items():
                if attr == 'object_id':
                    setattr(rating, attr, str(value))  # Ensure string
                else:
                    setattr(rating, attr, value)
            rating.save()
            return rating
        except Rating.DoesNotExist:
            # Create new rating
            validated_data['object_id'] = str(validated_data['object_id'])  # Ensure string
            return Rating.objects.create(user=user, **validated_data)


class RatingStatsSerializer(serializers.Serializer):
    """Serializer for rating statistics"""
    average = serializers.FloatField(allow_null=True)
    count = serializers.IntegerField()
    distribution = serializers.DictField(
        child=serializers.IntegerField()
    )
    user_rating = RatingSerializer(allow_null=True)