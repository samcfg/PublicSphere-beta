# File: backend/middleware/rate_limiter.py
import time
import sys
from django.conf import settings
from django.http import HttpResponse  # Changed from HttpResponseTooManyRequests
from django.core.cache import cache
import hashlib

class RateLimitMiddleware:
    """
    Middleware for implementing rate limiting based on IP address and user ID.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Get rate limit configurations from settings
        self.rate_limits = getattr(settings, 'RATE_LIMIT', {
                'DEFAULT': '1000/day',        # Increased from 100/day
                'REGISTER': '100/day',        # Increased from 10/day  
                'LOGIN': '200/hour',          # Increased from 20/hour
                'CREATE_SOURCE': '500/day',   # Increased from 50/day
                'CREATE_COMMENT': '2000/day', # Increased from 200/day
                'CREATE_ARTICLE': '200/day',  # Increased from 20/day
        })
    
    def __call__(self, request):
        # Skip rate limiting for:
        # 1. Staff users
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff:
            return self.get_response(request)
        
        # 2. Test environment
        if 'test' in sys.argv:
            return self.get_response(request)
            
        # 3. Development environment
        if settings.DEBUG:
            return self.get_response(request)
        
        # Determine which rate limit to apply
        limit_key = self._get_limit_key(request)
        
        # Apply rate limiting
        if limit_key:
            # Get rate limit details
            limit, period = self._parse_rate_limit(self.rate_limits.get(limit_key, self.rate_limits['DEFAULT']))
            
            # Generate client identifier
            client_id = self._get_client_identifier(request)
            
            # Check if rate limit is exceeded
            cache_key = f"ratelimit:{limit_key}:{client_id}"
            
            # Get current count from cache
            count = cache.get(cache_key, 0)
            
            if count >= limit:
                # Create a custom 429 response instead of using HttpResponseTooManyRequests
                response = HttpResponse("Rate limit exceeded. Please try again later.", status=429)
                return response
            
            # Increment the count
            if count == 0:
                # First request in the period
                cache.set(cache_key, 1, timeout=self._get_period_seconds(period))
            else:
                # Increment existing count
                cache.incr(cache_key)
        
        return self.get_response(request)
        
    # Rest of your methods remain unchanged
    def _get_limit_key(self, request):
        """Determine which rate limit category applies to this request"""
        # Registration endpoint
        if request.path == '/api/users/register/' and request.method == 'POST':
            return 'REGISTER'
        
        # Login endpoint
        if request.path == '/api/users/login/' and request.method == 'POST':
            return 'LOGIN'
        
        # Source creation
        if request.path == '/api/sources/' and request.method == 'POST':
            return 'CREATE_SOURCE'
        
        # Comment creation
        if request.path == '/api/comments/' and request.method == 'POST':
            return 'CREATE_COMMENT'
        
        # Article creation
        if request.path == '/api/articles/' and request.method == 'POST':
            return 'CREATE_ARTICLE'
        
        # Default rate limit for other endpoints
        if request.method != 'GET':
            return 'DEFAULT'
        
        return None
    
    def _parse_rate_limit(self, rate_limit_str):
        """Parse the rate limit string into limit and period"""
        parts = rate_limit_str.split('/')
        limit = int(parts[0])
        period = parts[1]
        return limit, period
    
    def _get_period_seconds(self, period):
        """Convert period string to seconds"""
        if period == 'second':
            return 1
        elif period == 'minute':
            return 60
        elif period == 'hour':
            return 3600
        elif period == 'day':
            return 86400
        elif period == 'week':
            return 604800
        elif period == 'month':
            return 2592000
        else:
            return 86400  # Default: 1 day
    
    def _get_client_identifier(self, request):
        """
        Generate a unique identifier for the client based on IP and user ID if available.
        Uses a hash to protect privacy.
        """
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        # Add user ID if authenticated
        user_id = str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else ''
        
        # Create a unique identifier
        identifier = f"{ip}:{user_id}"
        
        # Hash the identifier to protect privacy
        return hashlib.md5(identifier.encode()).hexdigest()