from rest_framework import serializers
from .models import ClaimVersion, SourceVersion, EdgeVersion, RatingVersion, CommentVersion


class ClaimVersionSerializer(serializers.ModelSerializer):
    """Serializer for ClaimVersion temporal data"""

    class Meta:
        model = ClaimVersion
        fields = [
            'id',
            'node_id',
            'version_number',
            'content',
            'operation',
            'timestamp',
            'valid_from',
            'valid_to',
            'changed_by',
            'change_notes',
        ]
        read_only_fields = ['id', 'timestamp', 'valid_from']


class SourceVersionSerializer(serializers.ModelSerializer):
    """Serializer for SourceVersion temporal data"""

    class Meta:
        model = SourceVersion
        fields = [
            'id',
            'node_id',
            'version_number',
            'url',
            'title',
            'author',
            'publication_date',
            'source_type',
            'content',
            'operation',
            'timestamp',
            'valid_from',
            'valid_to',
            'changed_by',
            'change_notes',
        ]
        read_only_fields = ['id', 'timestamp', 'valid_from']


class EdgeVersionSerializer(serializers.ModelSerializer):
    """Serializer for EdgeVersion temporal data"""

    class Meta:
        model = EdgeVersion
        fields = [
            'id',
            'edge_id',
            'edge_type',
            'version_number',
            'source_node_id',
            'target_node_id',
            'notes',
            'logic_type',
            'composite_id',
            'operation',
            'timestamp',
            'valid_from',
            'valid_to',
            'changed_by',
            'change_notes',
        ]
        read_only_fields = ['id', 'timestamp', 'valid_from']


class RatingVersionSerializer(serializers.ModelSerializer):
    """Serializer for RatingVersion temporal data"""

    class Meta:
        model = RatingVersion
        fields = [
            'id',
            'rating_id',
            'version_number',
            'user_id',
            'entity_uuid',
            'entity_type',
            'dimension',
            'score',
            'operation',
            'timestamp',
            'valid_from',
            'valid_to',
            'change_notes',
        ]
        read_only_fields = ['id', 'timestamp', 'valid_from']


class CommentVersionSerializer(serializers.ModelSerializer):
    """Serializer for CommentVersion temporal data"""

    class Meta:
        model = CommentVersion
        fields = [
            'id',
            'comment_id',
            'version_number',
            'user_id',
            'entity_uuid',
            'entity_type',
            'content',
            'parent_comment_id',
            'is_deleted',
            'operation',
            'timestamp',
            'valid_from',
            'valid_to',
            'change_notes',
        ]
        read_only_fields = ['id', 'timestamp', 'valid_from']
