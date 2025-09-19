# File: backend/apps/ratings/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Rating(models.Model):
    """
    Model for storing user ratings on various content types
    (source areas, connections, articles).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings',
        null=False
    )
    
    # Content type and object identification
    CONTENT_TYPE_CHOICES = [
        ('source_area', 'Source Area'),
        ('connection', 'Connection'),
        ('article', 'Article'),
    ]
    content_type = models.CharField(
        max_length=20, 
        choices=CONTENT_TYPE_CHOICES,
        null=False
    )
    
    # CHANGE: From UUIDField to CharField to handle both integer and UUID IDs
    object_id = models.CharField(
        max_length=255,
        null=False,
        help_text="ID of the object being rated (can be integer or UUID)"
    )
    
    # Rating value (0-100)
    value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=False,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    
    # Optional explanation for the rating
    explanation = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Rating of {self.value} by {self.user.username} on {self.content_type} {self.object_id}"
    
    @classmethod
    def get_average_rating(cls, content_type, object_id):
        """
        Calculate the average rating for a specific object
        """
        # Convert object_id to string for consistent comparison
        object_id_str = str(object_id)
        ratings = cls.objects.filter(content_type=content_type, object_id=object_id_str)
        if not ratings.exists():
            return None
        
        total = sum(rating.value for rating in ratings)
        return total / ratings.count()
    
    @classmethod
    def get_rating_distribution(cls, content_type, object_id):
        """
        Get the distribution of ratings for a specific object
        Returns a dictionary with ranges as keys and counts as values
        """
        # Convert object_id to string for consistent comparison
        object_id_str = str(object_id)
        ratings = cls.objects.filter(content_type=content_type, object_id=object_id_str)
        
        # Define ranges
        ranges = {
            '0-20': 0,
            '21-40': 0,
            '41-60': 0,
            '61-80': 0,
            '81-100': 0
        }
        
        # Count ratings in each range
        for rating in ratings:
            value = float(rating.value)
            if value <= 20:
                ranges['0-20'] += 1
            elif value <= 40:
                ranges['21-40'] += 1
            elif value <= 60:
                ranges['41-60'] += 1
            elif value <= 80:
                ranges['61-80'] += 1
            else:
                ranges['81-100'] += 1
        
        return ranges