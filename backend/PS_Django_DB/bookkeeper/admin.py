from django.contrib import admin
from .models import NodeVersion, EdgeVersion


@admin.register(NodeVersion)
class NodeVersionAdmin(admin.ModelAdmin):
    list_display = ('node_id', 'node_label', 'operation', 'timestamp', 'valid_from', 'valid_to')
    list_filter = ('node_label', 'operation', 'timestamp')
    search_fields = ('node_id', 'content')
    readonly_fields = ('timestamp', 'valid_from')
    ordering = ('-timestamp',)


@admin.register(EdgeVersion)
class EdgeVersionAdmin(admin.ModelAdmin):
    list_display = ('edge_id', 'edge_type', 'source_node_id', 'target_node_id', 'operation', 'timestamp')
    list_filter = ('edge_type', 'operation', 'timestamp')
    search_fields = ('edge_id', 'source_node_id', 'target_node_id', 'notes')
    readonly_fields = ('timestamp', 'valid_from')
    ordering = ('-timestamp',)
