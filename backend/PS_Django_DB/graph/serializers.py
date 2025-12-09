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
    url = serializers.URLField(max_length=2000, required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    author = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)
    publication_date = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    source_type = serializers.ChoiceField(
        choices=['web', 'book', 'paper', 'observation'],
        required=False,
        allow_blank=True,
        allow_null=True
    )
    content = serializers.CharField(max_length=50000, required=False, allow_blank=True, allow_null=True)


class SourceCreateSerializer(serializers.Serializer):
    """Serializer for creating Source nodes"""
    url = serializers.URLField(max_length=2000, required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(max_length=500, required=True, allow_blank=False)  # REQUIRED
    author = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)
    publication_date = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    source_type = serializers.ChoiceField(
        choices=['web', 'book', 'paper', 'observation'],
        required=False,
        allow_blank=True,
        allow_null=True
    )
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
