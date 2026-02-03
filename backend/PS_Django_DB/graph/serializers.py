from rest_framework import serializers


class ClaimSerializer(serializers.Serializer):
    """Serializer for Claim nodes"""
    id = serializers.UUIDField(read_only=True)
    content = serializers.CharField(max_length=10000, required=False, allow_blank=True, allow_null=True)


class ClaimCreateSerializer(serializers.Serializer):
    """Serializer for creating Claim nodes"""
    content = serializers.CharField(max_length=10000, required=False, allow_blank=True, allow_null=True)


class SourceSerializer(serializers.Serializer):
    """Serializer for Source nodes"""
    id = serializers.UUIDField(read_only=True)

    # Core citation fields
    title = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    source_type = serializers.ChoiceField(
        choices=['journal_article', 'book', 'book_chapter', 'website',
                'newspaper', 'magazine', 'conference_paper', 'thesis',
                'report', 'personal_communication', 'observation', 'preprint'],
        required=False,
        allow_blank=True,
        allow_null=True
    )
    authors = serializers.JSONField(required=False, allow_null=True)
    author = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)  # Legacy

    # Publication metadata
    publication_date = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    container_title = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    publisher = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    publisher_location = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    # Volume/Issue/Pages
    volume = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    issue = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    pages = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)

    # Identifiers
    url = serializers.URLField(max_length=2048, required=False, allow_blank=True, allow_null=True)
    doi = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    isbn = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    issn = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)

    # Web-specific
    accessed_date = serializers.DateField(required=False, allow_null=True)

    # Flexible metadata
    metadata = serializers.JSONField(required=False, allow_null=True)

    # Content
    content = serializers.CharField(max_length=50000, required=False, allow_blank=True, allow_null=True)


class SourceCreateSerializer(serializers.Serializer):
    """Serializer for creating Source nodes"""
    # Core citation fields
    title = serializers.CharField(max_length=500, required=True, allow_blank=False)  # REQUIRED
    source_type = serializers.ChoiceField(
        choices=['journal_article', 'book', 'book_chapter', 'website',
                'newspaper', 'magazine', 'conference_paper', 'thesis',
                'report', 'personal_communication', 'observation', 'preprint'],
        required=False,
        allow_blank=True,
        allow_null=True
    )
    authors = serializers.JSONField(required=False, allow_null=True)
    # Expected format: [{"name": "Last, First", "role": "author", "affiliation": "..."}]
    author = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)  # Legacy

    # Publication metadata
    publication_date = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    container_title = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    publisher = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    publisher_location = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    # Volume/Issue/Pages
    volume = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    issue = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    pages = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)

    # Identifiers
    url = serializers.URLField(max_length=2048, required=False, allow_blank=True, allow_null=True)
    doi = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    isbn = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    issn = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)

    # Web-specific
    accessed_date = serializers.DateField(required=False, allow_null=True)

    # Flexible metadata
    metadata = serializers.JSONField(required=False, allow_null=True)

    # Content
    content = serializers.CharField(max_length=50000, required=False, allow_blank=True, allow_null=True)


class ConnectionSerializer(serializers.Serializer):
    """Serializer for Connection edges"""
    id = serializers.UUIDField(read_only=True)
    from_node_id = serializers.UUIDField()
    to_node_id = serializers.UUIDField()
    notes = serializers.CharField(max_length=5000, required=False, allow_blank=True, allow_null=True)
    logic_type = serializers.ChoiceField(
        choices=['AND', 'OR', 'NOT', 'NAND'],
        required=False,
        allow_blank=True,
        allow_null=True
    )
    composite_id = serializers.UUIDField(required=False, allow_null=True)


class ConnectionCreateSerializer(serializers.Serializer):
    """Serializer for creating Connection edges"""
    from_node_id = serializers.UUIDField()
    to_node_id = serializers.UUIDField()
    notes = serializers.CharField(max_length=5000, required=False, allow_blank=True, allow_null=True)
    logic_type = serializers.ChoiceField(
        choices=['AND', 'OR', 'NOT', 'NAND'],
        required=False,
        allow_blank=True,
        allow_null=True
    )
    composite_id = serializers.UUIDField(required=False, allow_null=True)


class CompoundConnectionCreateSerializer(serializers.Serializer):
    """Serializer for creating compound connections (multiple edges with shared metadata)"""
    source_node_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=2,
        help_text="List of source node UUIDs (all edges will point to same target)"
    )
    target_node_id = serializers.UUIDField()
    logic_type = serializers.ChoiceField(
        choices=['AND', 'OR', 'NOT', 'NAND'],
        help_text="Logical operator shared by all edges in the compound group"
    )
    notes = serializers.CharField(max_length=5000, required=False, allow_blank=True, allow_null=True)
    composite_id = serializers.UUIDField(required=False, allow_null=True)


class NodeUpdateSerializer(serializers.Serializer):
    """Serializer for updating node properties (generic, accepts any fields)"""
    # Dynamic fields handled in view validation
    pass


class EdgeUpdateSerializer(serializers.Serializer):
    """Serializer for updating edge properties (generic, accepts any fields)"""
    # Dynamic fields handled in view validation
    pass
