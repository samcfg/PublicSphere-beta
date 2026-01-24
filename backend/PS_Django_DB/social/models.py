import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User


class Rating(models.Model):
    """
    User ratings on graph entities (claims, sources, connections).
    Scores aggregate into global_strength values for reputation calculation.

    Design: No graph DB changes—all Django. Ratings stored relationally,
    aggregated on-demand or cached in Redis.
    """
    DIMENSION_CHOICES = [
        ('confidence', 'Confidence'),
        ('relevance', 'Relevance'),
    ]

    ENTITY_TYPE_CHOICES = [
        ('claim', 'Claim'),
        ('source', 'Source'),
        ('connection', 'Connection'),
        ('comment', 'Comment'),
        ('suggested_edit', 'Suggested Edit'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    entity_uuid = models.CharField(
        max_length=36,
        db_index=True,
        help_text="UUID of the claim, source, or connection being rated"
    )
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES
    )
    dimension = models.CharField(
        max_length=20,
        choices=DIMENSION_CHOICES,
        blank=True,
        null=True,
        help_text="Optional: What aspect is being rated (confidence or relevance)"
    )
    score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Rating score from 0-100"
    )
    is_anonymous = models.BooleanField(
        default=False,
        help_text="If True, display as [anonymous] in public queries"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ratings'
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'
        indexes = [
            models.Index(fields=['entity_uuid']),  # Entity lookup
            models.Index(fields=['user']),  # User ratings
            models.Index(fields=['entity_uuid', 'dimension']),  # Aggregation queries
        ]
        # One rating per user per entity (or per dimension if specified)
        unique_together = [['user', 'entity_uuid', 'entity_type', 'dimension']]

    def __str__(self):
        user_display = self.get_display_name()
        return f"{user_display} rated {self.entity_type} {self.entity_uuid[:8]} ({self.dimension}): {self.score}"

    def get_display_name(self):
        """
        Returns the display name for UI rendering.
        - [anonymous] if is_anonymous is True
        - username otherwise
        """
        if self.is_anonymous:
            return "[anonymous]"
        return self.user.username if self.user else "[deleted]"


class Comment(models.Model):
    """
    Threaded comments on graph entities.
    Supports nested replies via parent_comment_id (self-referencing FK).
    Soft-delete via is_deleted flag (preserves structure, hides content).

    Design: Comments provide human interpretive layer without cluttering
    formal graph structure. Version history tracked in bookkeeper.CommentVersion.
    """
    ENTITY_TYPE_CHOICES = [
        ('claim', 'Claim'),
        ('source', 'Source'),
        ('connection', 'Connection'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,  # Allow [deleted] display on user deletion
        related_name='comments'
    )
    entity_uuid = models.CharField(
        max_length=36,
        db_index=True,
        help_text="UUID of the claim, source, or connection being commented on"
    )
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES
    )
    content = models.TextField(
        help_text="Comment text content"
    )
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="If set, this is a reply to another comment"
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag—hides content in UI, preserves structure"
    )
    is_anonymous = models.BooleanField(
        default=False,
        help_text="If True, display as [anonymous] in public queries"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comments'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        indexes = [
            models.Index(fields=['entity_uuid']),  # Entity comment lookup
            models.Index(fields=['user']),  # User comments
            models.Index(fields=['parent_comment']),  # Thread traversal
            models.Index(fields=['timestamp']),  # Chronological ordering
        ]

    def __str__(self):
        user_display = self.get_display_name()
        status = " (deleted)" if self.is_deleted else ""
        return f"Comment by {user_display} on {self.entity_type} {self.entity_uuid[:8]}{status}"

    def get_display_name(self):
        """
        Returns the display name for UI rendering.
        - [deleted] if user is None (account deleted)
        - [anonymous] if is_anonymous is True
        - username otherwise
        """
        if self.user is None:
            return "[deleted]"
        if self.is_anonymous:
            return "[anonymous]"
        return self.user.username

    def get_display_content(self):
        """
        Returns content for UI rendering.
        - "[deleted]" if is_deleted is True
        - actual content otherwise
        """
        if self.is_deleted:
            return "[deleted]"
        return self.content


class ViewCount(models.Model):
    """
    Simple view counter for entities. GDPR-compliant (no personal data).
    Stores only aggregate counts, not individual views.
    """
    ENTITY_TYPE_CHOICES = [
        ('claim', 'Claim'),
        ('source', 'Source'),
        ('connection', 'Connection'),
    ]

    entity_uuid = models.CharField(
        max_length=36,
        unique=True,
        db_index=True,
        help_text="UUID of the entity"
    )
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES
    )
    count = models.IntegerField(
        default=0,
        help_text="Total view count"
    )

    class Meta:
        db_table = 'view_counts'
        verbose_name = 'View Count'
        verbose_name_plural = 'View Counts'
        indexes = [
            models.Index(fields=['entity_uuid']),
        ]
        # One counter per entity
        unique_together = [['entity_uuid', 'entity_type']]

    def __str__(self):
        return f"{self.entity_type} {self.entity_uuid[:8]}: {self.count} views"


class SuggestedEdit(models.Model):
    """
    User-proposed modifications to locked nodes (past edit window or not owned).
    Community rates suggestions; accepted suggestions apply changes to target node.

    Workflow:
    1. User creates suggestion → status='pending'
    2. Community rates the suggestion (Rating model with entity_type='suggested_edit')
    3. Moderator reviews OR threshold auto-triggers → status='accepted'/'rejected'
    4. Accepted suggestions apply changes via ops.edit_node()
    """
    ENTITY_TYPE_CHOICES = [
        ('claim', 'Claim'),
        ('source', 'Source'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    suggestion_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="UUID for this suggestion"
    )
    entity_uuid = models.CharField(
        max_length=36,
        db_index=True,
        help_text="UUID of the target claim or source to modify"
    )
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES
    )
    suggested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='suggested_edits'
    )
    proposed_changes = models.JSONField(
        help_text="Dict of property: new_value pairs. E.g. {'content': 'new text'}"
    )
    rationale = models.TextField(
        help_text="Why this change improves the node"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_suggestions'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'suggested_edits'
        verbose_name = 'Suggested Edit'
        verbose_name_plural = 'Suggested Edits'
        indexes = [
            models.Index(fields=['entity_uuid']),
            models.Index(fields=['status']),
            models.Index(fields=['suggested_by']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        user_display = self.suggested_by.username if self.suggested_by else '[deleted]'
        return f"Suggestion for {self.entity_type} {self.entity_uuid[:8]} by {user_display} ({self.status})"


class FlaggedContent(models.Model):
    """
    Moderation flags for review.
    Created by moderators/admins to mark entities for staff investigation.

    Design: Moderators flag suspicious content → staff admins review queue
    → take action (hide, verify, ignore).
    """
    ENTITY_TYPE_CHOICES = [
        ('claim', 'Claim'),
        ('source', 'Source'),
        ('connection', 'Connection'),
        ('comment', 'Comment'),
        ('rating', 'Rating'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('action_taken', 'Action Taken'),
        ('dismissed', 'Dismissed'),
    ]

    entity_uuid = models.CharField(
        max_length=36,
        db_index=True,
        help_text="UUID of the flagged entity"
    )
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES
    )
    flagged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='flags_created'
    )
    reason = models.TextField(
        help_text="Explanation for why this content was flagged"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flags_reviewed',
        help_text="Staff admin who reviewed this flag"
    )
    resolution_notes = models.TextField(
        blank=True,
        default='',
        help_text="Notes from staff admin review"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'flagged_content'
        verbose_name = 'Flagged Content'
        verbose_name_plural = 'Flagged Content'
        indexes = [
            models.Index(fields=['entity_uuid']),
            models.Index(fields=['status']),  # Pending queue lookup
            models.Index(fields=['flagged_by']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.entity_type} {self.entity_uuid[:8]} flagged by {self.flagged_by.username if self.flagged_by else '[deleted]'}"
