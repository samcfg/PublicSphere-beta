# File: backend/apps/connections/serializers.py
from rest_framework import serializers
from .models import Connection

from django.contrib.auth import get_user_model

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for User model to include in nested serializations"""
    class Meta:
        model = User
        fields = ['id', 'username', 'reputation']
        read_only_fields = ['id', 'username', 'reputation']


class ConnectionSerializer(serializers.ModelSerializer):
    """
    Serializer for Connection model.
    
    Includes a read-only representation of the creator.
    """
    creator = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = Connection
        fields = [
            'id', 'article_id', 'sourcearea_id', 'source_text', 'argument_text',
            'explainer_text', 'source_page_ref', 'argument_page_ref', 'confidence_score', 
            'creator', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'creator']
    def validate_article_id(self, value):
        from apps.articles.models import Article
        if not Article.objects.filter(id=value).exists():
            raise serializers.ValidationError("Article does not exist")
        return value

    def validate_sourcearea_id(self, value):
        from apps.sources.models import SourceArea  
        if not SourceArea.objects.filter(id=value).exists():
            raise serializers.ValidationError("Source area does not exist")
        return value
    def create(self, validated_data):
        """
        Create a new connection with the current user as creator.
        """
        # Get the user from the context
        user = self.context['request'].user
        validated_data['creator'] = user
        return super().create(validated_data)

class ConnectionDetailSerializer(ConnectionSerializer):
    """
    Detailed serializer for Connection model.
    
    Includes additional details that might be needed for full display.
    """
    # This will be expanded later to include article and source area details
    # when those apps are fully implemented
    pass