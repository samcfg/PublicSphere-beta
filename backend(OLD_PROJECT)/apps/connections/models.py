# File: backend/apps/connections/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Connection(models.Model):
    """
    Represents a connection between an article and a source area.
    
    This model stores the relationship between an article and a source area,
    including the text being referenced and explanations of the connection.
    """
    article_id = models.UUIDField(
        help_text="Reference to the article being connected"
    )
    sourcearea_id = models.UUIDField(
        help_text="Reference to the source area being connected"
    )
    source_text = models.TextField(
        blank=True,
        help_text="Quote or paraphrase from the source material"
    )
    argument_text = models.TextField(
        blank=True,
        help_text="Direct quote from article sentence referencing this source"
    )
    explainer_text = models.TextField(
        blank=True,
        help_text="Optional clarification between source and argument"
    )
    source_page_ref = models.CharField(
        max_length=50,
        blank=True,
        help_text="Page or section reference for the source (e.g., 'p. 128', 'pp. 7, 78-79')"
    )
    argument_page_ref = models.CharField(
        max_length=50,
        blank=True,
        help_text="Page or section reference for the argument (e.g., 'p. 128', 'pp. 7, 78-79')"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this connection was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this connection was last updated"
    )
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Confidence score for this connection (0-100)"
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_connections",
        help_text="User who created this connection"
    )

    class Meta:
        indexes = [
            models.Index(fields=['article_id']),
            models.Index(fields=['sourcearea_id']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Connection {self.id}: Article {self.article_id} to Source {self.sourcearea_id}"