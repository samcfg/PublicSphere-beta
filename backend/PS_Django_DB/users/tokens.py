"""
Custom token model with expiration support.
Extends DRF's token authentication to auto-expire after 15 days.
"""
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


# Token expiration duration (15 days)
TOKEN_EXPIRATION_DAYS = getattr(settings, 'TOKEN_EXPIRATION_DAYS', 15)


class ExpiringTokenAuthentication(TokenAuthentication):
    """
    Custom token authentication that checks expiration.

    Tokens older than TOKEN_EXPIRATION_DAYS are considered invalid.
    Returns 401 with clear error message for expired tokens.
    """

    def authenticate_credentials(self, key):
        """
        Override to add expiration check.

        Raises:
            AuthenticationFailed: If token is expired
        """
        # Call parent to get user from token
        try:
            user, token = super().authenticate_credentials(key)
        except AuthenticationFailed:
            raise

        # Check if token has expired
        expiration_time = token.created + timedelta(days=TOKEN_EXPIRATION_DAYS)

        if timezone.now() > expiration_time:
            # Delete expired token
            token.delete()
            raise AuthenticationFailed('Token has expired. Please log in again.')

        return user, token


def is_token_expired(token):
    """
    Check if a token has expired.

    Args:
        token: Token instance

    Returns:
        bool: True if expired, False otherwise
    """
    expiration_time = token.created + timedelta(days=TOKEN_EXPIRATION_DAYS)
    return timezone.now() > expiration_time


def get_token_expiration_time(token):
    """
    Get the expiration timestamp for a token.

    Args:
        token: Token instance

    Returns:
        datetime: When the token expires
    """
    return token.created + timedelta(days=TOKEN_EXPIRATION_DAYS)


def refresh_token(user):
    """
    Refresh a user's token by deleting old and creating new.

    Args:
        user: User instance

    Returns:
        Token: New token instance
    """
    # Delete old token if exists
    Token.objects.filter(user=user).delete()

    # Create new token
    token = Token.objects.create(user=user)

    return token
