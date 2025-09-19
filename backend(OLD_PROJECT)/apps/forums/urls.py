# File: backend/apps/forums/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ForumCategoryViewSet, ThreadViewSet

router = DefaultRouter()
router.register(r'categories', ForumCategoryViewSet)
router.register(r'threads', ThreadViewSet)

urlpatterns = [
    path('', include(router.urls)),
]