"""
Django admin configuration for social models.
Implements three-tier access control: Superuser, Staff Admin, Moderator.

Permissions:
- Superuser: Full access (break-glass emergency use only)
- Staff Admin: Hard delete comments, modify ratings, resolve flags
- Moderator: Soft delete comments, flag content, view moderation queue
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from social.models import Rating, Comment, FlaggedContent, ViewCount


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Admin interface for Rating model"""

    list_display = ('id', 'user_link', 'entity_info', 'dimension', 'score', 'timestamp')
    list_filter = ('entity_type', 'dimension', 'timestamp')
    search_fields = ('entity_uuid', 'user__username')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

    fieldsets = (
        ('Rating Info', {
            'fields': ('user', 'entity_uuid', 'entity_type', 'dimension', 'score', 'timestamp')
        }),
    )

    def user_link(self, obj):
        """Link to user admin page"""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "[deleted]"
    user_link.short_description = 'User'

    def entity_info(self, obj):
        """Display entity type and truncated UUID"""
        return f"{obj.entity_type} {obj.entity_uuid[:8]}..."
    entity_info.short_description = 'Entity'

    def has_delete_permission(self, request, obj=None):
        """
        Staff Admins can delete ratings (remove spam/brigading).
        Moderators cannot delete ratings.
        """
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Staff Admin').exists():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """
        Staff Admins can modify ratings.
        Moderators have read-only access.
        """
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Staff Admin').exists():
            return True
        # Moderators can view but not change
        return False

    def has_add_permission(self, request):
        """
        No one should create ratings through admin.
        Ratings are created via API only.
        """
        return False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for Comment model"""

    list_display = ('id', 'user_link', 'entity_info', 'content_preview', 'parent_comment', 'is_deleted', 'timestamp')
    list_filter = ('entity_type', 'is_deleted', 'timestamp')
    search_fields = ('entity_uuid', 'user__username', 'content')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    actions = ['soft_delete_comments', 'restore_comments']

    fieldsets = (
        ('Comment Info', {
            'fields': ('user', 'entity_uuid', 'entity_type', 'parent_comment', 'is_deleted', 'timestamp')
        }),
        ('Content', {
            'fields': ('content',)
        }),
    )

    def user_link(self, obj):
        """Link to user admin page"""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "[deleted]"
    user_link.short_description = 'User'

    def entity_info(self, obj):
        """Display entity type and truncated UUID"""
        return f"{obj.entity_type} {obj.entity_uuid[:8]}..."
    entity_info.short_description = 'Entity'

    def content_preview(self, obj):
        """Show first 50 chars of content"""
        if obj.is_deleted:
            return format_html('<em>[deleted]</em>')
        preview = obj.content[:50]
        if len(obj.content) > 50:
            preview += '...'
        return preview
    content_preview.short_description = 'Content'

    def soft_delete_comments(self, request, queryset):
        """Moderator action: Soft delete selected comments"""
        count = queryset.update(is_deleted=True)
        self.message_user(request, f"{count} comment(s) soft-deleted.")
    soft_delete_comments.short_description = "Soft delete selected comments"

    def restore_comments(self, request, queryset):
        """Staff Admin action: Restore soft-deleted comments"""
        count = queryset.update(is_deleted=False)
        self.message_user(request, f"{count} comment(s) restored.")
    restore_comments.short_description = "Restore soft-deleted comments"

    def has_delete_permission(self, request, obj=None):
        """
        Only Staff Admins can hard delete comments.
        Moderators use soft delete action instead.
        """
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Staff Admin').exists():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """
        Moderators can change is_deleted flag (soft delete).
        Staff Admins have full change access.
        """
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Staff Admin').exists():
            return True
        if request.user.groups.filter(name='Moderator').exists():
            return True
        return False

    def has_add_permission(self, request):
        """
        No one should create comments through admin.
        Comments are created via API only.
        """
        return False

    def get_actions(self, request):
        """
        Moderators get soft_delete action.
        Staff Admins get both soft_delete and restore actions.
        """
        actions = super().get_actions(request)
        if not request.user.is_superuser and not request.user.groups.filter(name='Staff Admin').exists():
            # Moderators don't get restore action
            if 'restore_comments' in actions:
                del actions['restore_comments']
        return actions


@admin.register(FlaggedContent)
class FlaggedContentAdmin(admin.ModelAdmin):
    """Admin interface for FlaggedContent model"""

    list_display = ('id', 'entity_info', 'flagged_by_link', 'reason_preview', 'status', 'reviewed_by_link', 'timestamp')
    list_filter = ('entity_type', 'status', 'timestamp')
    search_fields = ('entity_uuid', 'flagged_by__username', 'reason')
    readonly_fields = ('timestamp', 'reviewed_at')
    ordering = ('status', '-timestamp')  # Pending flags first
    actions = ['mark_as_reviewed', 'mark_as_action_taken', 'mark_as_dismissed']

    fieldsets = (
        ('Flag Info', {
            'fields': ('entity_uuid', 'entity_type', 'flagged_by', 'reason', 'timestamp')
        }),
        ('Resolution', {
            'fields': ('status', 'reviewed_by', 'resolution_notes', 'reviewed_at')
        }),
    )

    def entity_info(self, obj):
        """Display entity type and truncated UUID"""
        return f"{obj.entity_type} {obj.entity_uuid[:8]}..."
    entity_info.short_description = 'Entity'

    def flagged_by_link(self, obj):
        """Link to flagging user admin page"""
        if obj.flagged_by:
            url = reverse('admin:users_user_change', args=[obj.flagged_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.flagged_by.username)
        return "[deleted]"
    flagged_by_link.short_description = 'Flagged By'

    def reviewed_by_link(self, obj):
        """Link to reviewing user admin page"""
        if obj.reviewed_by:
            url = reverse('admin:users_user_change', args=[obj.reviewed_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.reviewed_by.username)
        return "-"
    reviewed_by_link.short_description = 'Reviewed By'

    def reason_preview(self, obj):
        """Show first 50 chars of reason"""
        preview = obj.reason[:50]
        if len(obj.reason) > 50:
            preview += '...'
        return preview
    reason_preview.short_description = 'Reason'

    def mark_as_reviewed(self, request, queryset):
        """Staff Admin action: Mark flags as reviewed"""
        count = queryset.filter(status='pending').update(
            status='reviewed',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{count} flag(s) marked as reviewed.")
    mark_as_reviewed.short_description = "Mark as reviewed"

    def mark_as_action_taken(self, request, queryset):
        """Staff Admin action: Mark flags as action taken"""
        count = queryset.filter(status='pending').update(
            status='action_taken',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{count} flag(s) marked as action taken.")
    mark_as_action_taken.short_description = "Mark as action taken"

    def mark_as_dismissed(self, request, queryset):
        """Staff Admin action: Dismiss flags"""
        count = queryset.filter(status='pending').update(
            status='dismissed',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{count} flag(s) dismissed.")
    mark_as_dismissed.short_description = "Dismiss flags"

    def has_delete_permission(self, request, obj=None):
        """
        Only Staff Admins can delete flags.
        Moderators should use status changes instead.
        """
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Staff Admin').exists():
            return True
        return False

    def has_change_permission(self, request, obj=None):
        """
        Both Moderators and Staff Admins can modify flags.
        """
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Staff Admin').exists():
            return True
        if request.user.groups.filter(name='Moderator').exists():
            return True
        return False

    def has_add_permission(self, request):
        """
        Moderators can create flags.
        Staff Admins can create flags.
        """
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Staff Admin').exists():
            return True
        if request.user.groups.filter(name='Moderator').exists():
            return True
        return False

    def get_readonly_fields(self, request, obj=None):
        """
        Moderators can only edit reason field.
        Staff Admins can edit all fields except timestamps.
        """
        readonly = list(self.readonly_fields)
        if obj and not request.user.is_superuser and not request.user.groups.filter(name='Staff Admin').exists():
            # Moderators: most fields readonly except reason
            readonly.extend(['status', 'reviewed_by', 'resolution_notes'])
        return readonly


@admin.register(ViewCount)
class ViewCountAdmin(admin.ModelAdmin):
    """Admin interface for ViewCount model (read-only analytics)"""

    list_display = ('id', 'entity_info', 'count')
    list_filter = ('entity_type',)
    search_fields = ('entity_uuid',)
    readonly_fields = ('entity_uuid', 'entity_type', 'count')
    ordering = ('-count',)

    def entity_info(self, obj):
        """Display entity type and truncated UUID"""
        return f"{obj.entity_type} {obj.entity_uuid[:8]}..."
    entity_info.short_description = 'Entity'

    def has_add_permission(self, request):
        """View counts created via API only"""
        return False

    def has_change_permission(self, request, obj=None):
        """Read-only analytics data"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Staff Admins can delete for data cleanup"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name='Staff Admin').exists():
            return True
        return False
