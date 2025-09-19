# File: backend/middleware/sliding_token.py
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

logger = logging.getLogger(__name__)

class SlidingTokenMiddleware:
    """
    Middleware to implement sliding window token refresh.
    Issues new tokens when existing ones are within the refresh window.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.refresh_window = getattr(
            settings, 
            'SLIDING_TOKEN_REFRESH_WINDOW', 
            settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] / 2
        )
    
    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Check if we should issue a new token
        if hasattr(request, 'user') and request.user.is_authenticated:
            new_token = self._check_and_refresh_token(request)
            if new_token:
                response['X-New-Token'] = str(new_token)
                logger.info(f"Issued new sliding token for user {request.user.username}")
        
        return response
    
    def _check_and_refresh_token(self, request):
        """
        Check if token should be refreshed based on sliding window.
        Returns new token if refresh needed, None otherwise.
        """
        # Get token from request
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        token_string = auth_header.split(' ')[1]
        
        try:
            # Validate and decode current token
            token = AccessToken(token_string)
            
            # Check if token is within refresh window
            now = timezone.now()
            expires_at = timezone.datetime.fromtimestamp(token['exp'], tz=timezone.utc)
            time_until_expiry = expires_at - now
            
            # If token expires within refresh window, issue new one
            if time_until_expiry <= self.refresh_window:
                # Create new token for the same user
                new_token = AccessToken.for_user(request.user)
                return new_token
                
        except (InvalidToken, TokenError, KeyError) as e:
            logger.warning(f"Invalid token in sliding refresh: {e}")
            return None
        
        return None