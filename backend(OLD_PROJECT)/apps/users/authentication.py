# File: backend/apps/users/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class SlidingJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that works with sliding token middleware.
    Extends the default JWT authentication to handle sliding window refresh.
    """
    
    def authenticate(self, request):
        """
        Authenticate using JWT with sliding window support.
        """
        try:
            # Use parent class authentication logic
            result = super().authenticate(request)
            
            if result is not None:
                user, validated_token = result
                
                # Store token info on request for middleware access
                request.jwt_token = validated_token
                
                logger.debug(f"Authenticated user {user.username} with sliding JWT")
                
            return result
            
        except (InvalidToken, TokenError) as e:
            logger.warning(f"JWT authentication failed: {e}")
            return None
    
    def get_user(self, validated_token):
        """
        Get user from validated token.
        Override to add any custom user retrieval logic if needed.
        """
        try:
            user_id = validated_token.get('user_id')
            user = User.objects.get(id=user_id)
            
            # Check if user account is still active
            if not user.is_active:
                logger.warning(f"Inactive user {user.username} attempted authentication")
                return None
                
            return user
            
        except User.DoesNotExist:
            logger.warning(f"User with ID {user_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving user from token: {e}")
            return None