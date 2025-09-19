# File: backend/apps/access/models.py
from django.db import models
from django.conf import settings
import uuid

from apps.articles.models import Article

class UserArticleAccess(models.Model):
    """
    Model for tracking user access permissions to articles.
    This is used to grant and verify access to restricted articles.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='article_access',
        null=False
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='user_access',
        null=False
    )
    
    # Access info
    access_granted_at = models.DateTimeField(auto_now_add=True)
    
    ACCESS_METHOD_CHOICES = [
        ('referrer', 'Referrer Validation'),
        ('direct', 'Direct Access Grant'),
        ('invitation', 'Invitation'),
        ('subscription', 'Subscription')
    ]
    access_method = models.CharField(
        max_length=20,
        choices=ACCESS_METHOD_CHOICES,
        default='referrer',
        null=False
    )
    
    # Optional expiration
    access_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Referrer URL if access was granted via referrer
    referrer_url = models.URLField(max_length=2048, null=True, blank=True)
    
    # Additional data about the access (JSON)
    access_metadata = models.JSONField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'article']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['article']),
            models.Index(fields=['access_granted_at']),
            models.Index(fields=['access_expires_at']),
            models.Index(fields=['access_method']),
        ]
    
    def __str__(self):
        return f"Access for {self.user.username} to {self.article.title}"
    
    @property
    def is_expired(self):
        """Check if access has expired"""
        if self.access_expires_at is None:
            return False
        from django.utils import timezone
        return timezone.now() > self.access_expires_at
    
    @classmethod
    def has_access(cls, user, article):
        """Check if a user has access to an article"""
        if not user.is_authenticated or (user.is_authenticated and user.account_status == 'suspended'): # Treat unauthenticated AND suspended users the same way
            return False
        
        # Staff always have access
        if user.is_staff:
            return True
        
        # Non-restricted articles are accessible to all
        if not article.is_restricted:
            return True
            
        # Check for valid access record
        try:
            access = cls.objects.get(user=user, article=article)
            if not access.is_expired:
                return True
        except cls.DoesNotExist:
            pass
            
        return False