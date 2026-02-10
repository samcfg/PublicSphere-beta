from django.contrib import admin
from .models import ClaimVersion, SourceVersion, EdgeVersion, RatingVersion, CommentVersion


@admin.register(ClaimVersion)
class ClaimVersionAdmin(admin.ModelAdmin):
    """Read-only admin for claim version history - append-only audit trail"""
    list_display = ('node_id', 'version_number', 'operation', 'timestamp', 'valid_from', 'valid_to')
    list_filter = ('operation', 'timestamp')
    search_fields = ('node_id', 'content')
    readonly_fields = ('node_id', 'version_number', 'content', 'operation', 'timestamp',
                      'valid_from', 'valid_to', 'changed_by', 'change_notes')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        """Prevent manual creation - versions only via logging.py"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - maintain version audit trail"""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow viewing but prevent editing"""
        return False


@admin.register(SourceVersion)
class SourceVersionAdmin(admin.ModelAdmin):
    """Read-only admin for source version history - append-only audit trail"""
    list_display = ('node_id', 'version_number', 'title', 'source_type', 'operation', 'timestamp')
    list_filter = ('source_type', 'operation', 'timestamp')
    search_fields = ('node_id', 'title', 'url', 'content', 'doi', 'isbn')
    readonly_fields = (
        'node_id', 'version_number', 'title', 'source_type', 'thumbnail_link', 'authors',
        'url', 'accessed_date', 'excerpt', 'content', 'publication_date', 'container_title',
        'publisher', 'publisher_location', 'volume', 'issue', 'pages', 'edition',
        'doi', 'isbn', 'issn', 'pmid', 'pmcid', 'arxiv_id', 'handle', 'persistent_id',
        'persistent_id_type', 'editors', 'jurisdiction', 'legal_category', 'court',
        'decision_date', 'case_name', 'code', 'section', 'metadata',
        'operation', 'timestamp', 'valid_from', 'valid_to', 'changed_by', 'change_notes'
    )
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        """Prevent manual creation - versions only via logging.py"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - maintain version audit trail"""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow viewing but prevent editing"""
        return False


@admin.register(EdgeVersion)
class EdgeVersionAdmin(admin.ModelAdmin):
    """Read-only admin for edge version history - append-only audit trail"""
    list_display = ('edge_id', 'version_number', 'edge_type', 'source_node_id', 'target_node_id', 'operation', 'timestamp')
    list_filter = ('edge_type', 'operation', 'timestamp')
    search_fields = ('edge_id', 'source_node_id', 'target_node_id', 'notes', 'composite_id')
    readonly_fields = ('edge_id', 'version_number', 'edge_type', 'source_node_id', 'target_node_id',
                      'notes', 'logic_type', 'composite_id', 'operation', 'timestamp',
                      'valid_from', 'valid_to', 'changed_by', 'change_notes')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        """Prevent manual creation - versions only via logging.py"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - maintain version audit trail"""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow viewing but prevent editing"""
        return False


@admin.register(RatingVersion)
class RatingVersionAdmin(admin.ModelAdmin):
    """Read-only admin for rating version history - append-only audit trail"""
    list_display = ('rating_id', 'version_number', 'user_id', 'entity_uuid', 'entity_type', 'dimension', 'score', 'operation', 'timestamp')
    list_filter = ('entity_type', 'dimension', 'operation', 'timestamp')
    search_fields = ('rating_id', 'entity_uuid', 'user_id')
    readonly_fields = ('rating_id', 'version_number', 'user_id', 'entity_uuid', 'entity_type',
                      'dimension', 'score', 'operation', 'timestamp', 'valid_from', 'valid_to',
                      'change_notes')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        """Prevent manual creation - versions only via logging.py"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - maintain version audit trail"""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow viewing but prevent editing"""
        return False


@admin.register(CommentVersion)
class CommentVersionAdmin(admin.ModelAdmin):
    """Read-only admin for comment version history - append-only audit trail"""
    list_display = ('comment_id', 'version_number', 'user_id', 'entity_uuid', 'entity_type', 'content_preview', 'is_deleted', 'operation', 'timestamp')
    list_filter = ('entity_type', 'is_deleted', 'operation', 'timestamp')
    search_fields = ('comment_id', 'entity_uuid', 'user_id', 'content')
    readonly_fields = ('comment_id', 'version_number', 'user_id', 'entity_uuid', 'entity_type',
                      'content', 'parent_comment_id', 'is_deleted', 'operation', 'timestamp',
                      'valid_from', 'valid_to', 'change_notes')
    ordering = ('-timestamp',)

    def content_preview(self, obj):
        """Show first 50 chars of content"""
        preview = obj.content[:50]
        if len(obj.content) > 50:
            preview += '...'
        return preview
    content_preview.short_description = 'Content'

    def has_add_permission(self, request):
        """Prevent manual creation - versions only via logging.py"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - maintain version audit trail"""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow viewing but prevent editing"""
        return False
