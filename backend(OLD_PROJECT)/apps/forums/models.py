# File: backend/apps/forums/models.py
from django.db import models
from django.conf import settings
import uuid

from apps.articles.models import Article
from apps.sources.models import SourceArea
from django.db.models.signals import post_save
from django.dispatch import receiver

class ForumCategory(models.Model):
    """
    Model representing forum categories, which can be associated with an article
    and organized by tab types.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    slug = models.SlugField(max_length=100, unique=True, null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    is_default = models.BooleanField(default=False)
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='categories',
        null=True,
        blank=True
    )
    
    TAB_TYPE_CHOICES = [
        ('sources', 'Sources'),
        ('general', 'General'),
        ('reader_topics', 'Reader Topics'),
        ('author_asks', 'Author Asks'),
        ('experience', 'Give Your Experience'),
        ('other', 'Other')
    ]
    tab_type = models.CharField(
        max_length=20,
        choices=TAB_TYPE_CHOICES,
        default='sources'
    )
    
    class Meta:
        verbose_name = 'forum category'
        verbose_name_plural = 'forum categories'
        ordering = ['order', 'name']
        unique_together = [['article', 'tab_type']]
    
    def __str__(self):
        if self.article:
            return f"{self.name} ({self.article.title})"
        return self.name


class Thread(models.Model):
    """
    Model representing discussion threads within forum categories.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    category = models.ForeignKey(
        ForumCategory,
        on_delete=models.CASCADE,
        related_name='threads',
        null=False
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_threads',
        null=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_locked = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    CONTENT_TYPE_CHOICES = [
        ('thread', 'Regular Thread'),
        ('source_discussion', 'Source Discussion'),
        ('source_exchange', 'Source Exchange'),
        ('connection_thread', 'Connection Thread'),
        ('author_ask', 'Author Ask'),
        ('testimony', 'Testimony')
    ]
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='thread'
    )
    
    # Reference to the relevant object (can be a SourceArea or other object)
    object_id = models.UUIDField(null=True, blank=True)
    
    # Author prompt settings
    is_author_prompt = models.BooleanField(default=False)
    PROMPT_TYPE_CHOICES = [
        ('general', 'General Discussion'),
        ('source_request', 'Source Request'),
        ('experience', 'Experience')
    ]
    prompt_type = models.CharField(
        max_length=20,
        choices=PROMPT_TYPE_CHOICES,
        default='general'
    )
    
    class Meta:
        ordering = ['-is_pinned', '-updated_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['creator']),
            models.Index(fields=['content_type']),
            models.Index(fields=['object_id']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def comment_count(self):
        return self.comments.count()
    
    @property
    def latest_comment_date(self):
        latest_comment = self.comments.order_by('-created_at').first()
        return latest_comment.created_at if latest_comment else self.created_at


class ThreadSettings(models.Model):
    """
    Model for storing thread-specific settings and permissions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.OneToOneField(
        Thread,
        on_delete=models.CASCADE,
        related_name='settings',
        null=False
    )
    allow_anon = models.BooleanField(default=True)
    allowed_users = models.JSONField(null=True, blank=True)
    allowed_roles = models.JSONField(null=True, blank=True)
    
    LANGUAGE_FILTER_CHOICES = [
        ('none', 'No Filter'),
        ('standard', 'Standard Filter'),
        ('strict', 'Strict Filter')
    ]
    language_filter = models.CharField(
        max_length=10,
        choices=LANGUAGE_FILTER_CHOICES,
        default='standard'
    )
    
    file_types = models.JSONField(null=True, blank=True)
    max_file_size = models.IntegerField(default=5242880)  # 5MB in bytes
    
    class Meta:
        verbose_name = 'thread settings'
        verbose_name_plural = 'thread settings'
    
    def __str__(self):
        return f"Settings for {self.thread.title}"


# Signal to automatically create ThreadSettings when a Thread is created
@receiver(post_save, sender=Thread)
def create_thread_settings(sender, instance, created, **kwargs):
    """Create ThreadSettings when a new Thread is created"""
    if created:
        ThreadSettings.objects.get_or_create(thread=instance)