from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Provides username, email, password, is_staff, is_superuser out of the box.
    """
    # AbstractUser provides: username, email, password, first_name, last_name,
    # is_staff, is_superuser, is_active, date_joined, last_login

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    """
    Extended user profile with reputation and contribution metrics.
    One-to-one relationship with User.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True
    )
    bio = models.TextField(blank=True, default='')
    display_name = models.CharField(max_length=100, blank=True, default='')

    # Contribution counts (updated via signals/services)
    total_claims = models.IntegerField(default=0)
    total_sources = models.IntegerField(default=0)
    total_connections = models.IntegerField(default=0)

    # Reputation score (contribution-based, formula visible to users)
    # Formula: total_claims + total_sources + total_connections
    # (ratings integration deferred to Phase 2)
    reputation_score = models.IntegerField(default=0)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile: {self.user.username}"

    def calculate_reputation(self):
        """
        Calculate reputation score based on contribution counts.
        Phase 1: Simple sum of contributions.
        Phase 2: Will incorporate average ratings received.
        """
        self.reputation_score = (
            self.total_claims +
            self.total_sources +
            self.total_connections
        )
        return self.reputation_score


class UserAttribution(models.Model):
    """
    Links entity UUIDs to users with privacy controls.
    Queried by UI to display authorship (respects is_anonymous flag).

    Design: User creates content -> Graph DB (no user data) -> logging.py
    -> creates UserAttribution entry linking entity UUID to user.
    """
    ENTITY_TYPE_CHOICES = [
        ('claim', 'Claim'),
        ('source', 'Source'),
        ('connection', 'Connection'),
    ]

    entity_uuid = models.CharField(
        max_length=36,
        db_index=True,
        help_text="UUID of the claim, source, or connection"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,  # Allows soft delete (nullify on account deletion)
        related_name='attributions'
    )
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES
    )
    is_anonymous = models.BooleanField(
        default=False,
        help_text="If True, display as [anonymous]; if user is None, display as [deleted]"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_attributions'
        verbose_name = 'User Attribution'
        verbose_name_plural = 'User Attributions'
        indexes = [
            models.Index(fields=['entity_uuid']),  # Primary lookup by entity
            models.Index(fields=['user']),  # User contribution queries
        ]
        # Ensure one attribution per entity (original creator only)
        unique_together = [['entity_uuid', 'entity_type']]

    def __str__(self):
        user_display = self.get_display_name()
        return f"{self.entity_type} {self.entity_uuid[:8]} by {user_display}"

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


class UserModificationAttribution(models.Model):
    """
    Tracks modifications (UPDATE operations) to entities.
    Links entity UUID + version number to the user who made that edit.

    Design: User modifies content -> logging.py creates version record with incremented
    version_number -> creates UserModificationAttribution entry.
    """
    ENTITY_TYPE_CHOICES = [
        ('claim', 'Claim'),
        ('source', 'Source'),
        ('connection', 'Connection'),
    ]

    entity_uuid = models.CharField(
        max_length=36,
        db_index=True,
        help_text="UUID of the claim, source, or connection"
    )
    version_number = models.IntegerField(
        help_text="Sequential version number (v1, v2, v3...)"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,  # Allows soft delete (nullify on account deletion)
        related_name='modification_attributions'
    )
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES
    )
    is_anonymous = models.BooleanField(
        default=False,
        help_text="If True, display as [anonymous]; if user is None, display as [deleted]"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_modification_attributions'
        verbose_name = 'User Modification Attribution'
        verbose_name_plural = 'User Modification Attributions'
        indexes = [
            models.Index(fields=['entity_uuid', 'version_number']),  # Primary lookup
            models.Index(fields=['user']),  # User modification queries
        ]
        # Ensure one attribution per version
        unique_together = [['entity_uuid', 'entity_type', 'version_number']]

    def __str__(self):
        user_display = self.get_display_name()
        return f"{self.entity_type} {self.entity_uuid[:8]} v{self.version_number} by {user_display}"

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
