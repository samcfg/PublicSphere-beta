verify frontend grouping logic doesn't break when edge appears in multiple composite_id sets.

We removed a session auth setting: (ramafications?)
"""
● Update(config/settings.py)
  ⎿  Updated config/settings.py with 1 addition and 1 removal                                      
       153    REST_FRAMEWORK = {
       154        'DEFAULT_AUTHENTICATION_CLASSES': [
       155            'users.tokens.ExpiringTokenAuthentication',  # Custom token auth with 15-day 
             expiration
       156 -          'rest_framework.authentication.SessionAuthentication',
       156 +          # SessionAuthentication removed - causes CSRF issues with token-based 
           + frontend
       157        ],
       158        'DEFAULT_PERMISSION_CLASSES': [
       159            'rest_framework.permissions.IsAuthenticatedOrReadOnly',

● Perfect! Now the server should auto-reload with this change. The issue was:

  Root Cause: SessionAuthentication in DRF enforces CSRF protection on all POST/PUT/PATCH/DELETE
  requests. Since your frontend uses Token authentication (not sessions), this was blocking legitimate
   requests.

  Solution: Removed SessionAuthentication from DEFAULT_AUTHENTICATION_CLASSES. You only need
  ExpiringTokenAuthentication for your token-based API.
"""