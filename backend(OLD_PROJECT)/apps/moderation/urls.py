# File: backend/apps/moderation/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModeratorViewSet, ModerationActionViewSet

router = DefaultRouter()
router.register(r'moderators', ModeratorViewSet)
router.register(r'actions', ModerationActionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]