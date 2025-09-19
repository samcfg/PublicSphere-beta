# File: backend/apps/sources/admin.py
from django.contrib import admin
from .models import SourceArea, SourceAreaVersion

class SourceAreaVersionInline(admin.TabularInline):
    """Inline admin for source area versions"""
    model = SourceAreaVersion
    extra = 0
    readonly_fields = ('created_at', 'created_by', 'version_number')
    fields = ('version_number', 'title', 'created_at', 'created_by')
    can_delete = False
    max_num = 10
    verbose_name = "Version History"
    verbose_name_plural = "Version History"


@admin.register(SourceArea)
class SourceAreaAdmin(admin.ModelAdmin):
    """Admin interface for SourceArea model"""
    list_display = ('title', 'source_type', 'author', 'creator', 'created_at', 'version')
    list_filter = ('source_type', 'created_at')
    search_fields = ('title', 'author', 'content', 'institution')
    readonly_fields = ('created_at', 'updated_at', 'version', 'creator')
    raw_id_fields = ('creator',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content')
        }),
        ('Metadata', {
            'fields': ('author', 'institution', 'url', 'file_attachment', 'date_published', 
                      'date_accessed', 'doi', 'source_type')
        }),
        ('System', {
            'fields': ('creator', 'created_at', 'updated_at', 'version', 'confidence_score')
        }),
    )
    
    inlines = [SourceAreaVersionInline]


@admin.register(SourceAreaVersion)
class SourceAreaVersionAdmin(admin.ModelAdmin):
    """Admin interface for SourceAreaVersion model"""
    list_display = ('source_area', 'version_number', 'created_at', 'created_by')
    list_filter = ('created_at',)
    search_fields = ('source_area__title', 'title')
    readonly_fields = ('created_at', 'version_number')
    raw_id_fields = ('source_area', 'created_by')