# File: backend/apps/comments/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Comment, CommentVote
from apps.forums.models import Thread

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for User model to include in nested serializations"""
    class Meta:
        model = User
        fields = ['id', 'username', 'reputation']
        read_only_fields = ['id', 'username', 'reputation']


class CommentVoteSerializer(serializers.ModelSerializer):
    """Serializer for comment votes"""
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = CommentVote
        fields = ['id', 'comment', 'user', 'is_upvote', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ReplySerializer(serializers.ModelSerializer):
    """Serializer for comment replies (simplified)"""
    author = UserMinimalSerializer(read_only=True)
    vote_score = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'content', 'created_at', 'updated_at',
            'vote_score', 'is_edited', 'is_deleted'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'vote_score']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments"""
    author = UserMinimalSerializer(read_only=True)
    vote_score = serializers.IntegerField(read_only=True)
    user_vote = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'thread', 'author', 'content', 'created_at', 'updated_at',
            'parent', 'vote_score', 'user_vote', 'reply_count',
            'is_edited', 'is_deleted'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'vote_score', 'user_vote', 'reply_count']
    
    def get_user_vote(self, obj):
        """Get the current user's vote on this comment, if any"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                vote = CommentVote.objects.get(comment=obj, user=request.user)
                return vote.is_upvote
            except CommentVote.DoesNotExist:
                return None
        return None
    
    def get_reply_count(self, obj):
        """Get the number of replies to this comment"""
        return obj.replies.count()
    
    def validate(self, data):
        """Validate comment data"""
        # Check that thread is not locked
        thread = data.get('thread')
        if thread and thread.is_locked:
            raise serializers.ValidationError({"thread": "Cannot comment on a locked thread"})
        
        # Check parent is in the same thread
        parent = data.get('parent')
        if parent and parent.thread != thread:
            raise serializers.ValidationError({"parent": "Parent comment must be in the same thread"})
        
        return data
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        
        # Set is_edited to False for new comments
        validated_data['is_edited'] = False
        
        # Create the comment
        comment = Comment.objects.create(**validated_data)
        
        # Update thread's updated_at time
        thread = validated_data['thread']
        thread.save(update_fields=['updated_at'])
        
        return comment
    
    def update(self, instance, validated_data):
        # If content is being updated, mark as edited
        if 'content' in validated_data and validated_data['content'] != instance.content:
            validated_data['is_edited'] = True
        
        # Update the comment
        return super().update(instance, validated_data)


class CommentDetailSerializer(CommentSerializer):
    """Detailed serializer for comments with replies"""
    replies = serializers.SerializerMethodField()
    
    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ['replies']
    
    def get_replies(self, obj):
        """Get direct replies to this comment"""
        replies = obj.replies.filter(is_deleted=False).order_by('created_at')
        return ReplySerializer(replies, many=True, context=self.context).data