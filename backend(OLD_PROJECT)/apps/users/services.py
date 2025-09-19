# File: backend/apps/users/services.py
from django.db.models import Count

class UserDataService:
    def __init__(self, user):
        self.user = user
    
    def get_account_data_summary(self):
        """Get minimal user data summary for account page display"""
        return {
            'profile': {
                'username': self.user.username,
                'email': self.user.email or '',
                'date_joined': self.user.date_joined.isoformat() if self.user.date_joined else None,
                'account_status': self.user.account_status,
                'two_factor_enabled': self.user.two_factor_enabled,
            },
            'content_counts': {
                'sources_created': self.user.created_sources.count(),
                'comments_posted': self.user.comments.count(),
                'connections_made': self.user.created_connections.count(),
                'ratings_given': self.user.ratings.count(),
                'threads_created': self.user.created_threads.count(),
            },
            'consents': list(self.user.consents.filter(revoked_at__isnull=True).values(
                'consent_type', 'consent_version', 'granted_at'
            ))
        }

class AccountDeletionService:
    def __init__(self, user):
        self.user = user
    
    def delete_account_with_tombstoning(self):
        """Delete account using tombstoning approach"""
        from django.db import transaction
        
        with transaction.atomic():
            # Tombstone user profile
            self.user.username = "[deleted]"
            self.user.email = None
            self.user.account_status = 'deleted'
            self.user.is_active = False
            self.user.two_factor_enabled = False
            self.user.two_factor_pin = None
            
            # Tombstone comments
            self.user.comments.update(content="[deleted]")
            
            # Tombstone connection explanations
            self.user.created_connections.update(
                article_text="[deleted]",
                explainer_text="[deleted]"
            )
            
            # For sources: tombstone content but keep metadata for citations
            self.user.created_sources.update(content="[deleted]")
            
            # Remove all ratings (these don't need preservation)
            self.user.ratings.all().delete()
            
            # Remove consents
            self.user.consents.all().delete()
            
            # Remove access records
            self.user.article_access.all().delete()
            
            self.user.save()
            
        return True
    
    def get_deletion_impact(self):
        """Get summary of what will be affected by deletion"""
        return {
            'sources_count': self.user.created_sources.count(),
            'comments_count': self.user.comments.count(),
            'connections_count': self.user.created_connections.count(),
            'threads_count': self.user.created_threads.count(),
            'will_become_deleted_placeholders': True
        }