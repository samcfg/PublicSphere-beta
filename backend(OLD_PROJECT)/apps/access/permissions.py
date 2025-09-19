#backend/apps/access/permissions.py
from backend.utils import permissions


def update_access_permissions(request):
    """
    Create a file at backend/apps/access/permissions.py or update the existing one
    to include a custom permission class for unrestricted articles
    """
    class PublicOrHasArticleAccess(permissions.BasePermission):
        """
        Custom permission to allow access to unrestricted articles without authentication.
        """
        def has_permission(self, request, view):
            # Always allow GET, HEAD or OPTIONS requests for public endpoints
            if request.method in permissions.SAFE_METHODS:
                return True
                
            # For actions that modify data, require authentication
            return request.user and request.user.is_authenticated
            
        def has_object_permission(self, request, view, obj):
            # If the article is not restricted, allow access
            if hasattr(obj, 'article'):
                article = obj.article
                if not article.is_restricted:
                    return True
                
            # Check if user has access to restricted article
            from apps.access.models import UserArticleAccess
            
            # For unrestricted article or user with access, allow
            if hasattr(obj, 'is_restricted') and not obj.is_restricted:
                return True
                
            # Otherwise, fall back to the standard permission check
            if request.method in permissions.SAFE_METHODS:
                return True
                
            return request.user.is_authenticated