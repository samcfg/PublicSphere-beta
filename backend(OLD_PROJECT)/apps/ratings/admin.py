# File: backend/apps/ratings/admin.py
from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Admin interface for Rating model"""
    list_display = ('id', 'user', 'content_type', 'get_object_name', 'value', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('user__username', 'explanation')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'content_type', 'object_id')
        }),
        ('Rating', {
            'fields': ('value', 'explanation')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_object_name(self, obj):
        """Try to get the name of the rated object"""
        if obj.content_type == 'article':
            from apps.articles.models import Article
            try:
                article = Article.objects.get(id=obj.object_id)
                return article.title
            except Article.DoesNotExist:
                pass
        elif obj.content_type == 'source_area':
            from apps.sources.models import SourceArea
            try:
                source = SourceArea.objects.get(id=obj.object_id)
                return source.title
            except SourceArea.DoesNotExist:
                pass
        return str(obj.object_id)
    get_object_name.short_description = "Object"