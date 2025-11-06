from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, UserAttribution, UserModificationAttribution


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for User model.
    Extends Django's default UserAdmin with custom display.
    """
    list_display = ['username', 'email', 'is_staff', 'is_superuser', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model.
    """
    list_display = [
        'user',
        'display_name',
        'total_claims',
        'total_sources',
        'total_connections',
        'reputation_score',
        'last_updated'
    ]
    search_fields = ['user__username', 'display_name']
    readonly_fields = ['last_updated']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Profile Information', {
            'fields': ('display_name', 'bio')
        }),
        ('Contribution Metrics', {
            'fields': ('total_claims', 'total_sources', 'total_connections', 'reputation_score')
        }),
        ('Timestamps', {
            'fields': ('last_updated',)
        }),
    )


@admin.register(UserAttribution)
class UserAttributionAdmin(admin.ModelAdmin):
    """
    Admin interface for UserAttribution model.
    Read-only access - attributions only created via logging.py
    """
    list_display = ['entity_uuid', 'entity_type', 'display_user', 'is_anonymous', 'timestamp']
    list_filter = ['entity_type', 'is_anonymous']
    search_fields = ['entity_uuid', 'user__username']
    readonly_fields = ['entity_uuid', 'display_user_detail', 'entity_type', 'timestamp']

    def display_user(self, obj):
        """Display user as [anonymous] if is_anonymous=True, [deleted] if user is None"""
        if obj.is_anonymous:
            return '[anonymous]'
        elif obj.user is None:
            return '[deleted]'
        else:
            return obj.user.username
    display_user.short_description = 'User'

    def display_user_detail(self, obj):
        """Display user in detail view - respects anonymity"""
        if obj.is_anonymous:
            return '[anonymous]'
        elif obj.user is None:
            return '[deleted]'
        else:
            return f"{obj.user.username} (ID: {obj.user.id})"
    display_user_detail.short_description = 'User'

    def has_add_permission(self, request):
        """Prevent manual creation - attributions only via logging.py"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - maintain attribution audit trail"""
        return False

    # Allow editing is_anonymous flag for retroactive anonymity toggle
    fieldsets = (
        ('Attribution', {
            'fields': ('entity_uuid', 'entity_type', 'display_user_detail', 'timestamp')
        }),
        ('Privacy', {
            'fields': ('is_anonymous',),
            'description': 'Retroactive anonymity toggle - only editable field'
        }),
    )


@admin.register(UserModificationAttribution)
class UserModificationAttributionAdmin(admin.ModelAdmin):
    """
    Admin interface for UserModificationAttribution model.
    Read-only access - modification attributions only created via logging.py
    """
    list_display = ['entity_uuid', 'version_number', 'entity_type', 'display_user', 'is_anonymous', 'timestamp']
    list_filter = ['entity_type', 'is_anonymous']
    search_fields = ['entity_uuid', 'user__username']
    readonly_fields = ['entity_uuid', 'version_number', 'display_user_detail', 'entity_type', 'timestamp']

    def display_user(self, obj):
        """Display user as [anonymous] if is_anonymous=True, [deleted] if user is None"""
        if obj.is_anonymous:
            return '[anonymous]'
        elif obj.user is None:
            return '[deleted]'
        else:
            return obj.user.username
    display_user.short_description = 'User'

    def display_user_detail(self, obj):
        """Display user in detail view - respects anonymity"""
        if obj.is_anonymous:
            return '[anonymous]'
        elif obj.user is None:
            return '[deleted]'
        else:
            return f"{obj.user.username} (ID: {obj.user.id})"
    display_user_detail.short_description = 'User'

    def has_add_permission(self, request):
        """Prevent manual creation - modification attributions only via logging.py"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - maintain modification audit trail"""
        return False

    # Allow editing is_anonymous flag for retroactive anonymity toggle
    fieldsets = (
        ('Attribution', {
            'fields': ('entity_uuid', 'version_number', 'entity_type', 'display_user_detail', 'timestamp')
        }),
        ('Privacy', {
            'fields': ('is_anonymous',),
            'description': 'Retroactive anonymity toggle - only editable field'
        }),
    )
