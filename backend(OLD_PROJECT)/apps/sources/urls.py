# File: backend/apps/sources/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SourceAreaViewSet

router = DefaultRouter()
router.register(r'', SourceAreaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]