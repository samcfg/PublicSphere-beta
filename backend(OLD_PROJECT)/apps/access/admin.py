# File: backend/apps/access/admin.py
from django.contrib import admin
from .models import UserArticleAccess

@admin.register(UserArticleAccess)
class UserArticleAccessAdmin(admin.ModelAdmin):
    """Admin interface for UserArticleAccess model"""
    list_display = ('id', 'user', 'article', 'access_method', 'access_granted_at', 'access_expires_at', 'is_expired')
    list_filter = ('access_method', 'access_granted_at', 'access_expires_at')
    search_fields = ('user__username', 'article__title', 'referrer_url')
    raw_id_fields = ('user', 'article')
    readonly_fields = ('id', 'access_granted_at')
    
    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'article')
        }),
        ('Access Details', {
            'fields': ('access_method', 'access_granted_at', 'access_expires_at', 'referrer_url')
        }),
        ('Additional Data', {
            'fields': ('access_metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def is_expired(self, obj):
        """Display if access is expired"""
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'