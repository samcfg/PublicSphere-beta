#backend/apps/core/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SiteBanner(models.Model):
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'), 
        ('critical', 'Critical'),
        ('legal', 'Legal/Compliance')
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='info')
    is_active = models.BooleanField(default=True)
    is_dismissible = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.severity.upper()}: {self.title}"