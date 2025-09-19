# File: backend/utils/permissions.py
from rest_framework import permissions
from apps.moderation.models import Moderator

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Read: Anyone
    Create/Edit/Delete: Admin only
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff

class IsCreatorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow creators of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the creator of the object
        return obj.creator == request.user


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of a comment or post to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author
        return obj.author == request.user


class IsRaterOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow users who created a rating to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the user who created the rating
        return obj.user == request.user


class IsRegistrarOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow users who registered an article to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the registrar or staff
        return obj.registered_by == request.user or request.user.is_staff


class IsModeratorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow moderators to edit an object.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to moderators or staff
        if request.user.is_staff:
            return True

        return Moderator.user_is_moderator(request.user)

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Staff can do anything
        if request.user.is_staff:
            return True

        # Check if user is a moderator for the relevant scope
        # This handles different object types (article, category, etc.)
        scope_type = None
        scope_id = None

        # Determine scope type and ID based on object type
        if hasattr(obj, 'article'):
            scope_type = 'article'
            scope_id = obj.article.id
        elif hasattr(obj, 'category') and hasattr(obj.category, 'article'):
            scope_type = 'article'
            scope_id = obj.category.article.id
        elif hasattr(obj, 'thread') and hasattr(obj.thread, 'category'):
            scope_type = 'article'
            scope_id = obj.thread.category.article.id

        return Moderator.user_is_moderator(request.user, scope_type, scope_id)


class HasArticleAccess(permissions.BasePermission):
    """
    Custom permission to check if user has access to a restricted article.
    """
    def has_permission(self, request, view):
        # Check if article ID is in the request
        article_id = request.query_params.get('article_id')
        if not article_id:
            return True  # No article specified, so defer to view logic

        # Import here to avoid circular imports
        from apps.articles.models import Article
        from apps.access.models import UserArticleAccess

        try:
            article = Article.objects.get(id=article_id)
            # If article is not restricted, allow access
            if not article.is_restricted:
                return True
            
            # Check if user has access
            return UserArticleAccess.has_access(request.user, article)
        except Article.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        # Handle different object types
        article = None
        
        if hasattr(obj, 'article'):
            article = obj.article
        elif hasattr(obj, 'category') and hasattr(obj.category, 'article'):
            article = obj.category.article
        elif hasattr(obj, 'thread') and hasattr(obj.thread, 'category'):
            article = obj.thread.category.article
        
        if not article:
            return True  # No article associated, so allow
            
        # If article is not restricted, allow access
        if not article.is_restricted:
            return True
            
        # Import here to avoid circular imports
        from apps.access.models import UserArticleAccess
        
        # Check if user has access
        return UserArticleAccess.has_access(request.user, article)