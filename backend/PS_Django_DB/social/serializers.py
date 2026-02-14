"""
DRF serializers for social interactions.
Handles input validation for ratings, comments, moderation flags, and suggestions.
"""
from rest_framework import serializers
from social.models import Rating, Comment, FlaggedContent, SuggestedEdit


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
        allowed = ['claim', 'source', 'connection', 'comment', 'suggested_edit']
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
        """Return username respecting anonymity and ownership"""
        request = self.context.get('request')

        # Handle deleted users
        if obj.user is None:
            return '[deleted]'

        # If anonymous
        if obj.is_anonymous:
            # Show real username only to owner
            if request and request.user.is_authenticated and obj.user.id == request.user.id:
                return obj.user.username
            return 'Anonymous'

        # Not anonymous - show username
        return obj.user.username

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


class SuggestedEditSerializer(serializers.ModelSerializer):
    """Serializer for displaying suggested edits"""
    suggested_by_username = serializers.SerializerMethodField()
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True, allow_null=True)
    rating_stats = serializers.SerializerMethodField()

    class Meta:
        model = SuggestedEdit
        fields = [
            'suggestion_id', 'entity_uuid', 'entity_type', 'suggested_by_username',
            'proposed_changes', 'rationale', 'is_anonymous', 'refactor_type', 'status', 'resolved_by_username',
            'resolution_notes', 'created_at', 'resolved_at', 'rating_stats'
        ]
        read_only_fields = [
            'suggestion_id', 'suggested_by_username', 'status', 'resolved_by_username',
            'resolution_notes', 'created_at', 'resolved_at', 'rating_stats', 'is_anonymous'
        ]

    def get_suggested_by_username(self, obj):
        """Return username respecting anonymity"""
        return obj.get_display_name()

    def get_rating_stats(self, obj):
        """Get aggregated rating stats for this suggestion"""
        from django.db.models import Avg, Count
        stats = Rating.objects.filter(
            entity_uuid=str(obj.suggestion_id),
            entity_type='suggested_edit'
        ).aggregate(
            count=Count('id'),
            avg=Avg('score')
        )
        return {
            'count': stats['count'] or 0,
            'avg': round(stats['avg'], 1) if stats['avg'] is not None else None
        }


class SuggestedEditCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating suggested edits with strict validation"""

    class Meta:
        model = SuggestedEdit
        fields = ['entity_uuid', 'entity_type', 'proposed_changes', 'rationale', 'is_anonymous', 'refactor_type']

    def validate_entity_type(self, value):
        """Validate entity_type is allowed"""
        allowed = ['claim', 'source', 'connection']
        if value not in allowed:
            raise serializers.ValidationError(f"entity_type must be one of: {', '.join(allowed)}")
        return value

    def validate_rationale(self, value):
        """Validate rationale is provided and sufficient"""
        if not value or not value.strip():
            raise serializers.ValidationError("Rationale cannot be empty")
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Rationale must be at least 20 characters")
        if len(value) > 2000:
            raise serializers.ValidationError("Rationale cannot exceed 2000 characters")
        return value.strip()

    def validate_proposed_changes(self, value):
        """Validate proposed_changes is a dict with valid structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("proposed_changes must be a dictionary")
        if not value:
            raise serializers.ValidationError("proposed_changes cannot be empty")

        # Block internal/read-only fields
        forbidden_fields = {
            'id', 'node_id', 'url_normalized', 'doi_normalized', 'title_normalized',
            'content_normalized', 'version_number', 'operation', 'timestamp',
            'valid_from', 'valid_to', 'changed_by', 'change_notes'
        }

        forbidden_found = [k for k in value.keys() if k in forbidden_fields]
        if forbidden_found:
            raise serializers.ValidationError(
                f"Cannot modify read-only fields: {', '.join(forbidden_found)}"
            )

        return value

    def validate(self, attrs):
        """Cross-field validation: validate proposed_changes against entity schema"""
        entity_type = attrs.get('entity_type')
        proposed_changes = attrs.get('proposed_changes', {})
        refactor_type = attrs.get('refactor_type')

        # Handle refactorings separately
        if refactor_type == 'connection_restructure':
            # Validate it's targeting a connection
            if entity_type != 'connection':
                raise serializers.ValidationError({
                    'refactor_type': 'connection_restructure can only target connections'
                })

            # Validate refactoring structure
            from social.validators import RefactoringValidator
            validator = RefactoringValidator(proposed_changes)
            try:
                validator.validate()
            except Exception as e:
                raise serializers.ValidationError({
                    'proposed_changes': str(e)
                })

            # Skip normal validation for refactorings
            return attrs

        # Normal validation for simple edits
        if entity_type == 'claim':
            # Use ClaimSerializer for validation (partial=True for updates)
            from graph.serializers import ClaimSerializer
            serializer = ClaimSerializer(data=proposed_changes, partial=True)

            if not serializer.is_valid():
                raise serializers.ValidationError({
                    'proposed_changes': serializer.errors
                })

            # Must only have 'content' field for claims
            allowed_fields = {'content'}
            invalid_keys = set(proposed_changes.keys()) - allowed_fields
            if invalid_keys:
                raise serializers.ValidationError({
                    'proposed_changes': f"Invalid fields for claim: {', '.join(invalid_keys)}. "
                                       f"Only 'content' is allowed."
                })

        elif entity_type == 'source':
            # Use SourceSerializer for validation (partial=True for updates)
            from graph.serializers import SourceSerializer
            serializer = SourceSerializer(data=proposed_changes, partial=True)

            if not serializer.is_valid():
                raise serializers.ValidationError({
                    'proposed_changes': serializer.errors
                })

            # Validate authors structure if present
            if 'authors' in proposed_changes:
                authors = proposed_changes['authors']
                if authors is not None:
                    if not isinstance(authors, list):
                        raise serializers.ValidationError({
                            'proposed_changes': {'authors': 'Must be a list of author objects'}
                        })
                    for idx, author in enumerate(authors):
                        if not isinstance(author, dict):
                            raise serializers.ValidationError({
                                'proposed_changes': {'authors': f'Author at index {idx} must be an object'}
                            })
                        if 'name' not in author:
                            raise serializers.ValidationError({
                                'proposed_changes': {'authors': f'Author at index {idx} missing required "name" field'}
                            })

            # Validate editors structure if present
            if 'editors' in proposed_changes:
                editors = proposed_changes['editors']
                if editors is not None:
                    if not isinstance(editors, list):
                        raise serializers.ValidationError({
                            'proposed_changes': {'editors': 'Must be a list of editor objects'}
                        })
                    for idx, editor in enumerate(editors):
                        if not isinstance(editor, dict):
                            raise serializers.ValidationError({
                                'proposed_changes': {'editors': f'Editor at index {idx} must be an object'}
                            })
                        if 'name' not in editor:
                            raise serializers.ValidationError({
                                'proposed_changes': {'editors': f'Editor at index {idx} missing required "name" field'}
                            })

            # Validate source_type enum if present
            if 'source_type' in proposed_changes:
                valid_types = [
                    'journal_article', 'preprint', 'book', 'website', 'newspaper',
                    'magazine', 'thesis', 'conference_paper', 'technical_report',
                    'government_document', 'dataset', 'media', 'legal', 'testimony'
                ]
                if proposed_changes['source_type'] not in valid_types:
                    raise serializers.ValidationError({
                        'proposed_changes': {'source_type': f'Must be one of: {", ".join(valid_types)}'}
                    })

            # Validate legal_category enum if present
            if 'legal_category' in proposed_changes:
                valid_categories = ['case', 'statute', 'regulation', 'treaty']
                if proposed_changes['legal_category'] not in valid_categories:
                    raise serializers.ValidationError({
                        'proposed_changes': {'legal_category': f'Must be one of: {", ".join(valid_categories)}'}
                    })

        elif entity_type == 'connection':
            # Connections: Only 'notes' field can be edited
            allowed_fields = {'notes'}
            invalid_keys = set(proposed_changes.keys()) - allowed_fields
            if invalid_keys:
                raise serializers.ValidationError({
                    'proposed_changes': f"Invalid fields for connection: {', '.join(invalid_keys)}. "
                                       f"Only 'notes' is allowed."
                })

            # Validate 'notes' field if present
            if 'notes' in proposed_changes:
                notes = proposed_changes['notes']
                if notes is not None:
                    if not isinstance(notes, str):
                        raise serializers.ValidationError({
                            'proposed_changes': {'notes': 'Must be a string'}
                        })
                    if len(notes) > 5000:
                        raise serializers.ValidationError({
                            'proposed_changes': {'notes': 'Cannot exceed 5000 characters'}
                        })

        return attrs


