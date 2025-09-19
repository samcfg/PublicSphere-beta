# File: backend/apps/moderation/models.py
from django.db import models
from django.conf import settings
import uuid

class Moderator(models.Model):
    """
    Model representing a user with moderation privileges.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='moderator_roles',
        null=False
    )
    
    # Scope of moderation privileges
    SCOPE_CHOICES = [
        ('global', 'Global'),
        ('article', 'Article'),
        ('category', 'Category')
    ]
    scope_type = models.CharField(
        max_length=10,
        choices=SCOPE_CHOICES,
        default='global',
        null=False
    )
    
    # ID of the specific entity being moderated (if applicable)
    scope_id = models.UUIDField(null=True, blank=True)
    
    # Appointment information
    appointed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='appointed_moderators',
        null=True
    )
    appointed_at = models.DateTimeField(auto_now_add=True)
    
    # Permissions stored as JSON
    permissions = models.JSONField(default=dict)
    
    # Status
    active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = [['user', 'scope_type', 'scope_id']]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['scope_type', 'scope_id']),
            models.Index(fields=['active']),
        ]
    
    def __str__(self):
        scope = f"{self.scope_type}"
        if self.scope_id:
            scope += f" (ID: {self.scope_id})"
        return f"Moderator: {self.user.username} - {scope}"
    
    @property
    def can_delete_comments(self):
        return self.permissions.get('delete_comments', False)
    
    @property
    def can_lock_threads(self):
        return self.permissions.get('lock_threads', False)
    
    @property
    def can_ban_users(self):
        return self.permissions.get('ban_users', False)
    
    @property
    def can_remove_sources(self):
        return self.permissions.get('remove_sources', False)
    
    @property
    def can_edit_content(self):
        return self.permissions.get('edit_content', False)
    
    def set_default_permissions(self):
        """Set default permissions for a new moderator"""
        self.permissions = {
            'delete_comments': True,
            'lock_threads': True,
            'ban_users': False,
            'remove_sources': False,
            'edit_content': False
        }
        self.save()
    
    @classmethod
    def user_is_moderator(cls, user, scope_type=None, scope_id=None):
        """Check if a user is a moderator for the given scope"""
        if not user or not user.is_authenticated:
            return False
        
        # Staff members are always considered moderators
        if user.is_staff:
            return True
        
        # Base query for active moderators
        query = cls.objects.filter(user=user, active=True)
        
        # Global moderators can moderate everything
        if query.filter(scope_type='global').exists():
            return True
        
        # If scope is specified, check for specific moderation privileges
        if scope_type:
            # Exact match on scope type and ID
            if scope_id and query.filter(scope_type=scope_type, scope_id=scope_id).exists():
                return True
            
            # Match on scope type only (for article-wide or category-wide moderators)
            if query.filter(scope_type=scope_type, scope_id__isnull=True).exists():
                return True
        
        return False


class ModerationAction(models.Model):
    """
    Model for tracking moderation actions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    moderator = models.ForeignKey(
        Moderator,
        on_delete=models.CASCADE,
        related_name='actions',
        null=False
    )
    
    # Type of action
    ACTION_TYPE_CHOICES = [
        ('delete_comment', 'Delete Comment'),
        ('lock_thread', 'Lock Thread'),
        ('ban_user', 'Ban User'),
        ('remove_source', 'Remove Source'),
        ('edit_content', 'Edit Content')
    ]
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        null=False
    )
    
    # Target of the action
    target_type = models.CharField(max_length=50, null=False)
    target_id = models.UUIDField(null=False)
    
    # Reason and notes
    reason = models.TextField(null=False)
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Reversal information
    reversed_by = models.ForeignKey(
        Moderator,
        on_delete=models.SET_NULL,
        related_name='reversed_actions',
        null=True,
        blank=True
    )
    reversed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['moderator']),
            models.Index(fields=['action_type']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        action = self.get_action_type_display()
        target = f"{self.target_type} (ID: {self.target_id})"
        return f"{action} on {target} by {self.moderator.user.username}"
    
    @property
    def is_reversed(self):
        """Check if the action has been reversed"""
        return self.reversed_at is not None