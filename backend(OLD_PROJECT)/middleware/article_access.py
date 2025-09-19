# File: backend/middleware/article_access.py
from django.http import JsonResponse
from django.conf import settings
from django.urls import resolve
from apps.articles.models import Article
from apps.forums.models import Thread, ForumCategory
from apps.access.models import UserArticleAccess


class ArticleAccessMiddleware:
    """
    Middleware to check access to restricted articles across all API endpoints.
    Handles direct article access and indirect access via threads/categories.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # API paths that should be checked for article access
        self.protected_paths = [
            '/api/articles/',
            '/api/connections/',
            '/api/forums/',
            '/api/comments/',
            '/api/sources/',  # When sources are connected to restricted articles
        ]
    
    def __call__(self, request):
        # Skip if not an API request or not a protected path
        if not self._should_check_access(request):
            return self.get_response(request)
        
        # Skip for staff users (they have global access)
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff:
            return self.get_response(request)
        
        # Try to get article from request
        try:
            article = self._get_article_from_request(request)
            if article and article.is_restricted:
                # Check if user has access
                if not UserArticleAccess.has_access(request.user, article):
                    return JsonResponse(
                        {
                            "detail": "Access denied. You need access to this article's content.",
                            "article_id": str(article.id),
                            "article_title": article.title,
                            "is_restricted": True
                        },
                        status=403
                    )
        except (Article.DoesNotExist, Thread.DoesNotExist, ForumCategory.DoesNotExist):
            # If referenced objects don't exist, let the view handle it
            pass
        except Exception as e:
            # Log unexpected errors but don't block the request
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"ArticleAccessMiddleware error: {e}")
        
        return self.get_response(request)
    
    def _should_check_access(self, request):
        """Determine if this request should be checked for article access"""
        # Only check API requests
        if not request.path.startswith('/api/'):
            return False
        
        # Only check specific API paths
        return any(request.path.startswith(path) for path in self.protected_paths)
    
    def _get_article_from_request(self, request):
        """Extract article from request via various methods"""
        # Method 1: Direct article_id parameter
        article_id = request.GET.get('article_id')
        if not article_id and hasattr(request, 'resolver_match') and request.resolver_match:
            article_id = request.resolver_match.kwargs.get('article_id')
        
        if article_id:
            return Article.objects.get(id=article_id)
        
        # Method 2: Article slug in URL path (for ArticleViewSet)
        if hasattr(request, 'resolver_match') and request.resolver_match:
            slug = request.resolver_match.kwargs.get('slug')
            if slug and '/api/articles/' in request.path:
                return Article.objects.get(slug=slug)
        
        # Method 3: Indirect via thread_id
        thread_id = request.GET.get('thread_id')
        if not thread_id and hasattr(request, 'resolver_match') and request.resolver_match:
            thread_id = request.resolver_match.kwargs.get('thread_id')
        
        if thread_id:
            thread = Thread.objects.select_related('category__article').get(id=thread_id)
            return thread.category.article if thread.category else None
        
        # Method 4: Indirect via category
        category_id = request.GET.get('category_id')
        if not category_id and hasattr(request, 'resolver_match') and request.resolver_match:
            category_id = request.resolver_match.kwargs.get('category')
            if not category_id:
                category_id = request.resolver_match.kwargs.get('pk')
                # Only treat pk as category_id if we're in forums/categories/ endpoint
                if not ('/api/forums/categories/' in request.path):
                    category_id = None
        
        if category_id:
            category = ForumCategory.objects.select_related('article').get(id=category_id)
            return category.article
        
        # Method 5: Connection-specific checks
        if '/api/connections/' in request.path:
            # For connections, we need to check both article_id and sourcearea_id contexts
            # The by_article endpoint uses article_id parameter (handled above)
            # Individual connection access needs the connection's article
            if hasattr(request, 'resolver_match') and request.resolver_match:
                connection_id = request.resolver_match.kwargs.get('pk')
                if connection_id:
                    from apps.connections.models import Connection
                    try:
                        connection = Connection.objects.get(id=connection_id)
                        return Article.objects.get(id=connection.article_id)
                    except (Connection.DoesNotExist, Article.DoesNotExist):
                        pass
        
        # Method 6: Source-article connections
        if '/api/sources/' in request.path:
            # Sources themselves aren't restricted, but their connections to articles might be
            # This is more complex and might be handled at the view level instead
            pass
        
        return None