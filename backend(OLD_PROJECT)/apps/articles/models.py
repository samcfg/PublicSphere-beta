# File: backend/apps/articles/models.py
from django.db import models
from django.conf import settings
import uuid

class Article(models.Model):
    """
    Model representing an article with associated discussions in the SourceExchange platform.
    Articles can be external content (hosted elsewhere) that link to discussions on PublicSphere.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    url = models.URLField(max_length=2048, null=False, blank=False)
    author_name = models.CharField(max_length=255, null=True, blank=True)
    publication = models.CharField(max_length=255, null=True, blank=True)
    pub_date = models.DateField(null=True, blank=True)
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='registered_articles',
        null=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_restricted = models.BooleanField(default=False, help_text="Whether access to this article is restricted")
    
    # Additional fields that might be useful
    description = models.TextField(null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    featured_image = models.URLField(max_length=2048, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    # backend/apps/articles/models.py
# Add these fields to the Article model

    content = models.TextField(blank=True, null=True,
                            #help_text="Full content of the article for locally hosted articles"
                            )
    content_format = models.CharField(
        max_length=20, 
        choices=[('markdown', 'Markdown'), ('html', 'HTML'), ('plain', 'Plain Text')],
        default='markdown'
        #help_text="Format of the article content"
    )
    is_self_hosted = models.BooleanField(
        default=False
        #"Whether the article is hosted on PublicSphere or external"
    )
    source_bibliography_order = models.JSONField(
        null=True,
        blank=True,
        #Ordered array of source IDs for bibliography numbering
    )
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['url']),
            models.Index(fields=['pub_date']),
            models.Index(fields=['registered_by']),
            models.Index(fields=['is_restricted']),
        ]
    
    def __str__(self):
        return self.title