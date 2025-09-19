# File: backend/apps/articles/admin.py
from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin interface for Article model"""
    list_display = ('title', 'publication', 'author_name', 'pub_date', 'registered_by', 
                   'created_at', 'is_restricted', 'is_featured', 'view_count')
    list_filter = ('is_restricted', 'is_featured', 'pub_date', 'created_at')
    search_fields = ('title', 'author_name', 'publication', 'description')
    readonly_fields = ('created_at', 'view_count')
    raw_id_fields = ('registered_by',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'url', 'slug')
        }),
        ('Publication Details', {
            'fields': ('author_name', 'publication', 'pub_date', 'description', 'featured_image')
        }),
        ('Status', {
            'fields': ('is_restricted', 'is_featured', 'view_count')
        }),
        ('System', {
            'fields': ('registered_by', 'created_at')
        }),
    )
    
    actions = ['toggle_restriction', 'toggle_featured']
    
    def toggle_restriction(self, request, queryset):
        """Toggle restriction status for selected articles"""
        for article in queryset:
            article.is_restricted = not article.is_restricted
            article.save()
    toggle_restriction.short_description = "Toggle restriction status"
    
    def toggle_featured(self, request, queryset):
        """Toggle featured status for selected articles"""
        for article in queryset:
            article.is_featured = not article.is_featured
            article.save()
    toggle_featured.short_description = "Toggle featured status"