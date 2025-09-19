# File: config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints for each app
    path('api/users/', include('apps.users.urls')),
    path('api/articles/', include('apps.articles.urls')),
    path('api/sources/', include('apps.sources.urls')),
    path('api/connections/', include('apps.connections.urls')),
    path('api/forums/', include('apps.forums.urls')),
    path('api/comments/', include('apps.comments.urls')),
    path('api/ratings/', include('apps.ratings.urls')),
    path('api/moderation/', include('apps.moderation.urls')),
    path('api/access/', include('apps.access.urls')),
    path('api/core/', include('apps.core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)