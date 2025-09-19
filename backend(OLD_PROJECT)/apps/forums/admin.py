# File: backend/apps/forums/admin.py
from django.contrib import admin
from .models import ForumCategory, Thread, ThreadSettings

class ThreadSettingsInline(admin.StackedInline):
    """Inline admin for thread settings"""
    model = ThreadSettings
    can_delete = False
    verbose_name = "Thread Settings"
    verbose_name_plural = "Thread Settings"


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    """Admin interface for ForumCategory model"""
    list_display = ('name', 'tab_type', 'article', 'order', 'is_default')
    list_filter = ('tab_type', 'is_default')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('article',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        ('Association', {
            'fields': ('article', 'tab_type')
        }),
        ('Display', {
            'fields': ('order', 'is_default')
        }),
    )


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    """Admin interface for Thread model"""
    list_display = ('title', 'category', 'creator', 'created_at', 'updated_at', 
                   'is_locked', 'is_pinned', 'content_type', 'is_author_prompt')
    list_filter = ('is_locked', 'is_pinned', 'content_type', 'is_author_prompt', 'created_at')
    search_fields = ('title',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('category', 'creator')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'category', 'creator')
        }),
        ('Status', {
            'fields': ('is_locked', 'is_pinned')
        }),
        ('Type', {
            'fields': ('content_type', 'object_id', 'is_author_prompt', 'prompt_type')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    inlines = [ThreadSettingsInline]
    
    actions = ['lock_threads', 'unlock_threads', 'pin_threads', 'unpin_threads']
    
    def lock_threads(self, request, queryset):
        """Lock selected threads"""
        queryset.update(is_locked=True)
    lock_threads.short_description = "Lock selected threads"
    
    def unlock_threads(self, request, queryset):
        """Unlock selected threads"""
        queryset.update(is_locked=False)
    unlock_threads.short_description = "Unlock selected threads"
    
    def pin_threads(self, request, queryset):
        """Pin selected threads"""
        queryset.update(is_pinned=True)
    pin_threads.short_description = "Pin selected threads"
    
    def unpin_threads(self, request, queryset):
        """Unpin selected threads"""
        queryset.update(is_pinned=False)
    unpin_threads.short_description = "Unpin selected threads"


@admin.register(ThreadSettings)
class ThreadSettingsAdmin(admin.ModelAdmin):
    """Admin interface for ThreadSettings model"""
    list_display = ('thread', 'allow_anon', 'language_filter', 'max_file_size')
    list_filter = ('allow_anon', 'language_filter')
    raw_id_fields = ('thread',)