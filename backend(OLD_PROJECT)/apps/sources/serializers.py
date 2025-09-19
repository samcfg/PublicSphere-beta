# File: backend/apps/sources/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SourceArea, SourceAreaVersion

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for User model to include in nested serializations"""
    class Meta:
        model = User
        fields = ['id', 'username', 'reputation']
        read_only_fields = ['id', 'username', 'reputation']

class SourceAreaVersionSerializer(serializers.ModelSerializer):
    """Serializer for source area versions"""
    created_by = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = SourceAreaVersion
        fields = [
            'id', 'source_area', 'version_number', 'title', 'content',
            'author', 'institution', 'url', 'file_attachment',
            'date_published', 'date_accessed', 'doi', 'source_type',
            'created_at', 'created_by'
        ]
        read_only_fields = ['id', 'source_area', 'version_number', 'created_at', 'created_by']

class SourceAreaSerializer(serializers.ModelSerializer):
    """Serializer for source areas"""
    creator = UserMinimalSerializer(read_only=True)
    versions = serializers.SerializerMethodField()
    
    class Meta:
        model = SourceArea
        fields = [
            'id', 'title', 'content', 'creator', 'created_at', 'updated_at',
            'author', 'institution', 'url', 'file_attachment',
            'date_published', 'date_accessed', 'doi', 'source_type',
            'confidence_score', 'version', 'versions'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at', 'version']
    
    def get_versions(self, obj):
        """Returns the latest 5 versions of this source area"""
        versions = obj.versions.all()[:5]
        return SourceAreaVersionSerializer(versions, many=True).data
    
    def create(self, validated_data):
        """Create a new source area with the current user as creator"""
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        """Perform validation across fields"""
        # Check dates if both are provided
        if data.get('date_published') and data.get('date_accessed'):
            if data['date_accessed'] < data['date_published']:
                raise serializers.ValidationError(
                    {"date_accessed": "Access date cannot be before publication date"}
                )
        return data

class SourceAreaDetailSerializer(SourceAreaSerializer):
    """Detailed serializer with all versions"""
    
    def get_versions(self, obj):
        """Returns all versions of this source area"""
        versions = obj.versions.all()
        return SourceAreaVersionSerializer(versions, many=True).data