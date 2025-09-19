# File: backend/apps/access/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserArticleAccessViewSet, ArticleAccessViewSet

router = DefaultRouter()
router.register(r'user-access', UserArticleAccessViewSet)
router.register(r'article-access', ArticleAccessViewSet, basename='article-access')

urlpatterns = [
    path('', include(router.urls)),
]