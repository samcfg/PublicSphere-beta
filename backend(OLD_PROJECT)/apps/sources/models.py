# File: backend/apps/sources/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class SourceArea(models.Model):
    """
    Model representing a source (like an academic paper, news article, etc.)
    that can be referenced in discussions and connected to articles.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    content = models.TextField(blank=True, null=True, 
                              help_text="The main text content or excerpt from the source")
    
    # Metadata fields
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_sources')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Source details
    author = models.CharField(max_length=255, blank=True, null=True)
    institution = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(max_length=2048, blank=True, null=True)
    file_attachment = models.CharField(max_length=255, blank=True, null=True,
                                      help_text="Path to attached file if any")
    date_published = models.DateField(blank=True, null=True)
    date_accessed = models.DateField(blank=True, null=True)
    doi = models.CharField(max_length=100, blank=True, null=True,
                          help_text="Digital Object Identifier if available")
    
    # Source categorization
    SOURCE_TYPES = [
        ('paper', 'Academic Paper'),
        ('news', 'News Article'),
        ('firsthand', 'First-hand Account'),
        ('book', 'Book'),
        ('video', 'Video'),
        ('other', 'Other'),
    ]
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, 
                                  default='other', blank=True, null=True)
    
    # Confidence rating
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, 
                                         null=True, blank=True,
                                         validators=[
                                             MinValueValidator(0),
                                             MaxValueValidator(100)
                                         ])
    
    # Search optimization
    title_vector = SearchVectorField(null=True, blank=True)
    author_vector = SearchVectorField(null=True, blank=True)
    
    # Versioning
    version = models.IntegerField(default=1, null=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['author']),
            models.Index(fields=['date_published']),
            models.Index(fields=['source_type']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_current_version(self):
        """Returns the current version of this source area"""
        return self.version
    
    def create_new_version(self, updated_by):
        """
        Creates a new version of this source area and increments the version number
        """
        # Save the current state as a version
        SourceAreaVersion.objects.create(
            source_area=self,
            title=self.title,
            content=self.content,
            author=self.author,
            institution=self.institution,
            url=self.url,
            file_attachment=self.file_attachment,
            date_published=self.date_published,
            date_accessed=self.date_accessed,
            doi=self.doi,
            source_type=self.source_type,
            version_number=self.version,
            created_by=updated_by
        )
        
        # Increment version number
        self.version += 1
        self.save(update_fields=['version'])
        
        return self.version


class SourceAreaVersion(models.Model):
    """
    Model for storing previous versions of a source area
    """
    id = models.UUIDField(primary_key=True, editable=False, auto_created=True)
    source_area = models.ForeignKey(SourceArea, on_delete=models.CASCADE, related_name='versions')
    
    # Version metadata
    version_number = models.IntegerField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Fields that mirror SourceArea
    title = models.CharField(max_length=255, null=False, blank=False)
    content = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    institution = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(max_length=2048, blank=True, null=True)
    file_attachment = models.CharField(max_length=255, blank=True, null=True)
    date_published = models.DateField(blank=True, null=True)
    date_accessed = models.DateField(blank=True, null=True)
    doi = models.CharField(max_length=100, blank=True, null=True)
    source_type = models.CharField(max_length=20, choices=SourceArea.SOURCE_TYPES, 
                                 default='other', blank=True, null=True)
    
    class Meta:
        unique_together = [['source_area', 'version_number']]
        ordering = ['-version_number']
    
    def __str__(self):
        return f"{self.source_area.title} - v{self.version_number}"