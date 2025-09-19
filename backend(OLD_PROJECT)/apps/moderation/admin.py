# File: backend/apps/moderation/admin.py
from django.contrib import admin
from .models import Moderator, ModerationAction

@admin.register(Moderator)
class ModeratorAdmin(admin.ModelAdmin):
    """Admin interface for Moderator model"""
    list_display = ('id', 'user', 'scope_type', 'scope_id', 'appointed_by', 'appointed_at', 'active')
    list_filter = ('scope_type', 'active', 'appointed_at')
    search_fields = ('user__username', 'appointed_by__username')
    readonly_fields = ('id', 'appointed_at')
    raw_id_fields = ('user', 'appointed_by')
    
    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'scope_type', 'scope_id', 'active')
        }),
        ('Appointment Details', {
            'fields': ('appointed_by', 'appointed_at')
        }),
        ('Permissions', {
            'fields': ('permissions',)
        }),
    )
    
    def get_queryset(self, request):
        """Get the queryset for the admin view"""
        qs = super().get_queryset(request)
        return qs
    
    def save_model(self, request, obj, form, change):
        """Override save_model to set appointed_by if not set"""
        if not change and not obj.appointed_by:
            obj.appointed_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    """Admin interface for ModerationAction model"""
    list_display = ('id', 'get_moderator_username', 'action_type', 'target_type', 'timestamp', 'is_reversed')
    list_filter = ('action_type', 'timestamp', 'reversed_at')
    search_fields = ('moderator__user__username', 'reason', 'notes')
    readonly_fields = ('id', 'timestamp', 'reversed_at')
    raw_id_fields = ('moderator', 'reversed_by')
    
    fieldsets = (
        (None, {
            'fields': ('id', 'moderator', 'action_type')
        }),
        ('Target', {
            'fields': ('target_type', 'target_id')
        }),
        ('Details', {
            'fields': ('reason', 'notes', 'timestamp')
        }),
        ('Reversal', {
            'fields': ('reversed_by', 'reversed_at')
        }),
    )
    
    def get_moderator_username(self, obj):
        """Get the username of the moderator"""
        return obj.moderator.user.username
    get_moderator_username.short_description = 'Moderator'
    get_moderator_username.admin_order_field = 'moderator__user__username'
    
    def is_reversed(self, obj):
        """Check if the action has been reversed"""
        return obj.reversed_at is not None
    is_reversed.boolean = True
    is_reversed.short_description = 'Reversed'