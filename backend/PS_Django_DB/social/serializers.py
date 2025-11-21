"""
DRF serializers for social interactions.
Handles input validation for ratings, comments, and moderation flags.
"""
from rest_framework import serializers
from social.models import Rating, Comment, FlaggedContent


class RatingSerializer(serializers.ModelSerializer):
    """Serializer for displaying ratings"""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'username', 'entity_uuid', 'entity_type', 'dimension', 'score', 'timestamp']
        read_only_fields = ['id', 'username', 'timestamp']


class RatingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating ratings"""

    class Meta:
        model = Rating
        fields = ['entity_uuid', 'entity_type', 'dimension', 'score']

    def validate_score(self, value):
        """Validate score is between 0-100"""
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Score must be between 0 and 100")
        return value

    def validate_entity_type(self, value):
        """Validate entity_type is allowed"""
        allowed = ['claim', 'source', 'connection', 'comment']
        if value not in allowed:
            raise serializers.ValidationError(f"entity_type must be one of: {', '.join(allowed)}")
        return value

    def validate_dimension(self, value):
        """Validate dimension if provided"""
        if value and value not in ['confidence', 'relevance']:
            raise serializers.ValidationError("dimension must be 'confidence' or 'relevance'")
        return value


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for displaying comments"""
    username = serializers.SerializerMethodField()
    display_content = serializers.CharField(source='get_display_content', read_only=True)
    reply_count = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'username', 'entity_uuid', 'entity_type', 'content',
            'display_content', 'parent_comment', 'is_deleted', 'is_anonymous',
            'timestamp', 'reply_count', 'is_own'
        ]
        read_only_fields = ['id', 'username', 'timestamp', 'is_deleted', 'is_anonymous', 'display_content', 'reply_count', 'is_own']

    def get_username(self, obj):
        """Return sanitized username respecting is_anonymous flag"""
        return obj.get_display_name()

    def get_reply_count(self, obj):
        """Count non-deleted replies"""
        return obj.replies.filter(is_deleted=False).count()

    def get_is_own(self, obj):
        """Check if this comment belongs to the requesting user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj.user:
            return obj.user.id == request.user.id
        return False


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments"""

    class Meta:
        model = Comment
        fields = ['entity_uuid', 'entity_type', 'content', 'parent_comment']

    def validate_content(self, value):
        """Validate comment content length"""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty")
        if len(value) > 10000:
            raise serializers.ValidationError("Comment content cannot exceed 10000 characters")
        return value.strip()

    def validate_entity_type(self, value):
        """Validate entity_type is allowed"""
        allowed = ['claim', 'source', 'connection']
        if value not in allowed:
            raise serializers.ValidationError(f"entity_type must be one of: {', '.join(allowed)}")
        return value

    def validate_parent_comment(self, value):
        """Validate parent comment exists and isn't deleted"""
        if value and value.is_deleted:
            raise serializers.ValidationError("Cannot reply to a deleted comment")
        return value


class CommentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating comment content"""

    class Meta:
        model = Comment
        fields = ['content']

    def validate_content(self, value):
        """Validate comment content length"""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty")
        if len(value) > 10000:
            raise serializers.ValidationError("Comment content cannot exceed 10000 characters")
        return value.strip()


class FlagSerializer(serializers.ModelSerializer):
    """Serializer for moderation flags"""
    flagged_by_username = serializers.CharField(source='flagged_by.username', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True, allow_null=True)

    class Meta:
        model = FlaggedContent
        fields = [
            'id', 'entity_uuid', 'entity_type', 'flagged_by_username',
            'reason', 'status', 'reviewed_by_username', 'resolution_notes',
            'timestamp', 'reviewed_at'
        ]
        read_only_fields = [
            'id', 'flagged_by_username', 'status', 'reviewed_by_username',
            'resolution_notes', 'timestamp', 'reviewed_at'
        ]


class FlagCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating moderation flags"""

    class Meta:
        model = FlaggedContent
        fields = ['entity_uuid', 'entity_type', 'reason']

    def validate_reason(self, value):
        """Validate reason is provided"""
        if not value or not value.strip():
            raise serializers.ValidationError("Reason cannot be empty")
        if len(value) > 2000:
            raise serializers.ValidationError("Reason cannot exceed 2000 characters")
        return value.strip()

    def validate_entity_type(self, value):
        """Validate entity_type is allowed"""
        allowed = ['claim', 'source', 'connection', 'comment', 'rating']
        if value not in allowed:
            raise serializers.ValidationError(f"entity_type must be one of: {', '.join(allowed)}")
        return value


class FlagResolveSerializer(serializers.Serializer):
    """Serializer for resolving flags (staff admin only)"""
    status = serializers.ChoiceField(choices=['reviewed', 'action_taken', 'dismissed'])
    resolution_notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate_status(self, value):
        """Validate status is not 'pending'"""
        if value == 'pending':
            raise serializers.ValidationError("Cannot resolve flag with 'pending' status")
        return value


class RatingAggregateSerializer(serializers.Serializer):
    """Serializer for aggregated rating data"""
    avg_score = serializers.FloatField(allow_null=True)
    count = serializers.IntegerField()
    stddev = serializers.FloatField(allow_null=True)
    distribution = serializers.DictField()
    user_score = serializers.FloatField(allow_null=True)
