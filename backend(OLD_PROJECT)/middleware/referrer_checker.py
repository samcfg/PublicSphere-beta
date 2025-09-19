# File: backend/middleware/referrer_checker.py
from django.conf import settings
from django.http import HttpResponseForbidden
from django.urls import resolve, reverse
from urllib.parse import urlparse

from apps.articles.models import Article
from apps.access.models import UserArticleAccess

class ReferrerCheckerMiddleware:
    """
    Middleware to check HTTP referrer headers for access to restricted article content.
    This middleware validates that users accessing restricted article discussions
    are coming from the original article page or have proper access permissions.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip middleware if referrer checking is disabled
        if not getattr(settings, 'REFERRER_CHECK_ENABLED', True):
            return self.get_response(request)
        
        # Skip middleware for non-article related paths
        if not self._is_article_related_path(request.path):
            return self.get_response(request)
        
        # Extract article ID from the path
        article_id = self._get_article_id_from_path(request.path)
        if not article_id:
            return self.get_response(request)
        
        try:
            article = Article.objects.get(id=article_id)
            
            # Skip validation for non-restricted articles
            if not article.is_restricted:
                return self.get_response(request)
            
            # Staff users bypass referrer checking
            if request.user.is_authenticated and request.user.is_staff:
                return self.get_response(request)
            
            # Authenticated users with explicit access bypass referrer checking
            if request.user.is_authenticated and UserArticleAccess.has_access(request.user, article):
                return self.get_response(request)
            
            # Check referrer for other users
            valid_referrer = self._validate_referrer(request, article)
            if valid_referrer:
                # Grant access if referrer is valid and user is authenticated
                if request.user.is_authenticated:
                    UserArticleAccess.objects.get_or_create(
                        user=request.user,
                        article=article,
                        defaults={
                            'access_method': 'referrer',
                            'referrer_url': request.META.get('HTTP_REFERER', '')
                        }
                    )
                return self.get_response(request)
            
            # Block access for invalid referrers
            return HttpResponseForbidden("Access denied. You need to access this content from the original article.")
            
        except Article.DoesNotExist:
            # Continue with the request if article doesn't exist
            return self.get_response(request)
    
    def _is_article_related_path(self, path):
        """Check if the path is related to article discussions"""
        # Check if path matches forum patterns
        if '/api/forums/' in path:
            return True
        
        # Check if path matches comments patterns
        if '/api/comments/' in path:
            return True
        
        # Check if path matches source connections
        if '/api/connections/' in path:
            return True
        
        return False
    
    def _get_article_id_from_path(self, path):
        """Extract article ID from path"""
        # Try to resolve the URL to a view
        try:
            resolved = resolve(path)
            
            # Check for article ID in URL kwargs
            if 'article_id' in resolved.kwargs:
                return resolved.kwargs['article_id']
            
            # Check query parameters for article ID
            if 'article_id' in resolved.func.view_class.lookup_url_kwarg:
                return resolved.func.view_class.lookup_url_kwarg['article_id']
            
        except Exception:
            pass
        
        return None
    
    def _validate_referrer(self, request, article):
        """
        Validate that the HTTP referrer matches the article URL
        or comes from the PublicSphere platform
        """
        # Get referrer header
        referrer = request.META.get('HTTP_REFERER', '')
        if not referrer:
            return False
        
        # Parse referrer URL
        parsed_referrer = urlparse(referrer)
        
        # Check if referrer is from the same site (PublicSphere)
        if parsed_referrer.netloc == request.get_host():
            return True
        
        # Check if referrer matches the article URL
        article_url = urlparse(article.url)
        if parsed_referrer.netloc == article_url.netloc:
            # Basic check: same domain
            return True
        
        # Optional: Add more sophisticated checks here
        # For example, checking subdomain matching, path similarity, etc.
        
        return False