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

    # Required fields
    title = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    source_type = serializers.ChoiceField(
        choices=['journal_article', 'preprint', 'book', 'website', 'newspaper',
                'magazine', 'thesis', 'conference_paper', 'technical_report',
                'government_document', 'dataset', 'media', 'legal', 'testimony'],
        required=False,
        allow_blank=True,
        allow_null=True
    )

    # Universal optional fields
    thumbnail_link = serializers.URLField(max_length=2048, required=False, allow_blank=True, allow_null=True)
    authors = serializers.JSONField(required=False, allow_null=True)
    url = serializers.URLField(max_length=2048, required=False, allow_blank=True, allow_null=True)
    accessed_date = serializers.DateField(required=False, allow_null=True)
    excerpt = serializers.CharField(max_length=50000, required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(max_length=50000, required=False, allow_blank=True, allow_null=True)

    # Publication metadata
    publication_date = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    container_title = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    publisher = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    publisher_location = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    # Volume/Issue/Pages
    volume = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    issue = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    pages = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)

    # Book-specific
    edition = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)

    # Identifiers
    doi = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    isbn = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    issn = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    pmid = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    pmcid = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    arxiv_id = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    handle = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    persistent_id = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    persistent_id_type = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)

    # Editors
    editors = serializers.JSONField(required=False, allow_null=True)

    # Legal-specific
    jurisdiction = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    legal_category = serializers.ChoiceField(
        choices=['case', 'statute', 'regulation', 'treaty'],
        required=False,
        allow_blank=True,
        allow_null=True
    )
    court = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    decision_date = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    case_name = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    code = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    section = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    # Flexible metadata overflow
    metadata = serializers.JSONField(required=False, allow_null=True)


class SourceCreateSerializer(serializers.Serializer):
    """Serializer for creating Source nodes"""
    # Required fields
    title = serializers.CharField(max_length=500, required=True, allow_blank=False)
    source_type = serializers.ChoiceField(
        choices=['journal_article', 'preprint', 'book', 'website', 'newspaper',
                'magazine', 'thesis', 'conference_paper', 'technical_report',
                'government_document', 'dataset', 'media', 'legal', 'testimony'],
        required=True
    )

    # Universal optional fields
    thumbnail_link = serializers.URLField(max_length=2048, required=False, allow_blank=True, allow_null=True)
    authors = serializers.JSONField(required=False, allow_null=True)
    # Expected format: [{"name": "...", "role": "author"}]
    url = serializers.URLField(max_length=2048, required=False, allow_blank=True, allow_null=True)
    accessed_date = serializers.DateField(required=False, allow_null=True)
    excerpt = serializers.CharField(max_length=50000, required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(max_length=50000, required=False, allow_blank=True, allow_null=True)

    # Publication metadata
    publication_date = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    container_title = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    publisher = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    publisher_location = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    # Volume/Issue/Pages
    volume = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    issue = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    pages = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)

    # Book-specific
    edition = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)

    # Identifiers
    doi = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    isbn = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    issn = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    pmid = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    pmcid = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    arxiv_id = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    handle = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    persistent_id = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    persistent_id_type = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)

    # Editors
    editors = serializers.JSONField(required=False, allow_null=True)
    # Expected format: [{"name": "...", "role": "editor"}]

    # Legal-specific
    jurisdiction = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    legal_category = serializers.ChoiceField(
        choices=['case', 'statute', 'regulation', 'treaty'],
        required=False,
        allow_blank=True,
        allow_null=True
    )
    court = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    decision_date = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    case_name = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    code = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    section = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    # Flexible metadata overflow
    metadata = serializers.JSONField(required=False, allow_null=True)

    def validate(self, data):
        """Type-specific required field validation"""
        source_type = data.get('source_type')

        # Legal sources require jurisdiction and legal_category
        if source_type == 'legal':
            if not data.get('jurisdiction'):
                raise serializers.ValidationError({"jurisdiction": "jurisdiction is required for legal sources"})
            if not data.get('legal_category'):
                raise serializers.ValidationError({"legal_category": "legal_category is required for legal sources"})

        # Website sources require url
        if source_type == 'website':
            if not data.get('url'):
                raise serializers.ValidationError({"url": "url is required for website sources"})

        return data


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
    quote = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)


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
    quote = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Optional excerpt from source node (max 500 chars for fair use)"
    )


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
    quote = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Optional excerpt from source nodes (max 500 chars for fair use)"
    )


class NodeUpdateSerializer(serializers.Serializer):
    """Serializer for updating node properties (generic, accepts any fields)"""
    # Dynamic fields handled in view validation
    pass


class EdgeUpdateSerializer(serializers.Serializer):
    """Serializer for updating edge properties (generic, accepts any fields)"""
    # Dynamic fields handled in view validation
    pass
