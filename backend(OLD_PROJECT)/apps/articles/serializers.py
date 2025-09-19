# File: backend/apps/articles/serializers.py
from rest_framework import serializers
from django.utils.text import slugify
from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for basic Article representation.
    """
    registered_by_username = serializers.CharField(source='registered_by.username', read_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'url', 'author_name', 'publication',
            'pub_date', 'created_at', 'is_restricted', 'content',
            'content_format', 'is_self_hosted', 'registered_by_username', 
            'description', 'featured_image', 'is_featured', 'view_count', 'slug',
            'source_bibliography_order'
        ]
        read_only_fields = ['id', 'created_at', 'registered_by_username', 'view_count', 'slug']

class ArticleDetailSerializer(ArticleSerializer):
    """
    Serializer for detailed Article representation.
    """
    class Meta(ArticleSerializer.Meta):
        fields = ArticleSerializer.Meta.fields
        read_only_fields = ArticleSerializer.Meta.read_only_fields
    
    def validate_source_bibliography_order(self, value):
        """Basic validation for source bibliography order"""
        if value is None:
            return value
            
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list of source IDs")
        
        # Check for duplicates
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Cannot contain duplicate source IDs")
        
        return value
    
    def create(self, validated_data):
        """Create a new article with auto-generated slug."""
        if not validated_data.get('slug'):
            # Generate a slug from the title
            slug = slugify(validated_data['title'])
            
            # Ensure slug is unique
            base_slug = slug
            counter = 1
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            validated_data['slug'] = slug
        
        return super().create(validated_data)
    
    def validate_url(self, value):
        """Ensure URL uniqueness."""
        instance = getattr(self, 'instance', None)
        
        # If updating an existing instance, exclude this instance from the check
        if instance:
            exists = Article.objects.exclude(pk=instance.pk).filter(url=value).exists()
        else:
            exists = Article.objects.filter(url=value).exists()
        
        if exists:
            raise serializers.ValidationError("An article with this URL already exists.")
        
        return value