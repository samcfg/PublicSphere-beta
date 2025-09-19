# Create a new file: backend/config/test_settings.py
from config.settings import *

# Override the REST_FRAMEWORK settings completely (don't extend the original)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Make sure these are proper string values, not imported functions
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'FORMAT_SUFFIX_KWARG': 'format',
}

# For testing, disable security settings
DEBUG = True
print("Using test settings! DEBUG is set to:", DEBUG)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False