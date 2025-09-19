# File: backend/apps/access/serializers.py
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from .models import UserArticleAccess
from apps.articles.models import Article
from apps.articles.serializers import ArticleSerializer

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for User model to include in nested serializations"""
    class Meta:
        model = User
        fields = ['id', 'username', 'reputation']
        read_only_fields = ['id', 'username', 'reputation']


class UserArticleAccessSerializer(serializers.ModelSerializer):
    """Serializer for user article access"""
    user = UserMinimalSerializer(read_only=True)
    article_title = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserArticleAccess
        fields = [
            'id', 'user', 'article', 'article_title', 'access_granted_at', 'access_expires_at',
            'access_method', 'referrer_url', 'access_metadata', 'is_expired'
        ]
        read_only_fields = ['id', 'access_granted_at', 'is_expired']
    
    def get_article_title(self, obj):
        """Get the title of the article"""
        return obj.article.title if obj.article else None


class UserArticleAccessCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user article access"""
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    article = serializers.PrimaryKeyRelatedField(queryset=Article.objects.all())
    expires_in_days = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = UserArticleAccess
        fields = [
            'user', 'article', 'access_method', 'access_expires_at',
            'referrer_url', 'access_metadata', 'expires_in_days'
        ]
    
    def validate(self, data):
        """Calculate expiration date if expires_in_days is provided"""
        expires_in_days = data.pop('expires_in_days', None)
        if expires_in_days:
            data['access_expires_at'] = timezone.now() + timedelta(days=expires_in_days)
        return data


class ReferrerValidationSerializer(serializers.Serializer):
    """Serializer for referrer validation"""
    article_id = serializers.UUIDField(required=True)
    referrer_url = serializers.URLField(required=True)
    
    def validate_article_id(self, value):
        """Validate that the article exists"""
        try:
            article = Article.objects.get(id=value)
            self.context['article'] = article
            return value
        except Article.DoesNotExist:
            raise serializers.ValidationError("Article not found")
    
    def validate(self, data):
        """Add article to validated data"""
        data['article'] = self.context.get('article')
        return data


class AccessCheckSerializer(serializers.Serializer):
    """Serializer for checking access to an article"""
    article_id = serializers.UUIDField(required=True)
    
    def validate_article_id(self, value):
        """Validate that the article exists"""
        try:
            article = Article.objects.get(id=value)
            self.context['article'] = article
            return value
        except Article.DoesNotExist:
            raise serializers.ValidationError("Article not found")
    
    def validate(self, data):
        """Add article to validated data"""
        data['article'] = self.context.get('article')
        return data