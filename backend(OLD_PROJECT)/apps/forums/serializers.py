# File: backend/apps/forums/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ForumCategory, Thread, ThreadSettings
from apps.articles.serializers import ArticleSerializer
from apps.comments.serializers import CommentSerializer

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for User model to include in nested serializations"""
    class Meta:
        model = User
        fields = ['id', 'username', 'reputation']
        read_only_fields = ['id', 'username', 'reputation']


class ThreadSettingsSerializer(serializers.ModelSerializer):
    """Serializer for thread settings"""
    class Meta:
        model = ThreadSettings
        fields = [
            'id', 'thread', 'allow_anon', 'allowed_users', 'allowed_roles',
            'language_filter', 'file_types', 'max_file_size'
        ]
        read_only_fields = ['id']


class ThreadSerializer(serializers.ModelSerializer):
    """Serializer for threads"""
    creator = UserMinimalSerializer(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Thread
        fields = [
            'id', 'title', 'category', 'creator', 'created_at', 'updated_at',
            'is_locked', 'is_pinned', 'content_type', 'object_id',
            'is_author_prompt', 'prompt_type', 'comment_count'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        thread = super().create(validated_data)
        
        return thread


class ThreadDetailSerializer(ThreadSerializer):
    """Detailed serializer for threads with settings"""
    settings = ThreadSettingsSerializer(read_only=True)
    recent_comments = serializers.SerializerMethodField()
    
    class Meta(ThreadSerializer.Meta):
        fields = ThreadSerializer.Meta.fields + ['settings', 'recent_comments']
    
    def get_recent_comments(self, obj):
        """Returns the most recent comments for this thread"""
        from apps.comments.models import Comment
        recent_comments = Comment.objects.filter(thread=obj).order_by('-created_at')[:5]
        from apps.comments.serializers import CommentSerializer
        return CommentSerializer(recent_comments, many=True).data


class ForumCategorySerializer(serializers.ModelSerializer):
    """Serializer for forum categories"""
    article_title = serializers.CharField(source='article.title', read_only=True)
    thread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumCategory
        fields = [
            'id', 'name', 'slug', 'description', 'order', 'is_default',
            'article', 'article_title', 'tab_type', 'thread_count'
        ]
        read_only_fields = ['id']
    
    def get_thread_count(self, obj):
        """Returns the number of threads in this category"""
        return obj.threads.count()


class ForumCategoryDetailSerializer(ForumCategorySerializer):
    """Detailed serializer for forum categories with threads"""
    threads = serializers.SerializerMethodField()
    
    class Meta(ForumCategorySerializer.Meta):
        fields = ForumCategorySerializer.Meta.fields + ['threads']
    
    def get_threads(self, obj):
        """Returns the threads in this category, appropriately sorted"""
        threads = obj.threads.all().order_by('-is_pinned', '-updated_at')[:10]
        return ThreadSerializer(threads, many=True).data