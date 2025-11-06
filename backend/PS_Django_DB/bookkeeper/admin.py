from django.contrib import admin
from .models import ClaimVersion, SourceVersion, EdgeVersion


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
    list_display = ('node_id', 'version_number', 'title', 'author', 'source_type', 'operation', 'timestamp')
    list_filter = ('source_type', 'operation', 'timestamp')
    search_fields = ('node_id', 'title', 'author', 'url', 'content')
    readonly_fields = ('node_id', 'version_number', 'url', 'title', 'author', 'publication_date',
                      'source_type', 'content', 'operation', 'timestamp', 'valid_from',
                      'valid_to', 'changed_by', 'change_notes')
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
