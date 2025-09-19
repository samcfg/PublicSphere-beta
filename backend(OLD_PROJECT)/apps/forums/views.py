# File: backend/apps/forums/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import ForumCategory, Thread, ThreadSettings
from .serializers import (
    ForumCategorySerializer,
    ForumCategoryDetailSerializer,
    ThreadSerializer,
    ThreadDetailSerializer,
    ThreadSettingsSerializer
)
from utils.permissions import IsCreatorOrReadOnly, IsModeratorOrReadOnly
from apps.articles.models import Article
from apps.sources.models import SourceArea

class ForumCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for forum categories.
    """
    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsModeratorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['article', 'tab_type', 'is_default']
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ForumCategoryDetailSerializer
        return self.serializer_class
    
    @action(detail=False, methods=['get'])
    def for_article(self, request):
        """
        Return categories for a specific article.
        """
        article_id = request.query_params.get('article_id')
        if not article_id:
            return Response(
                {"detail": "article_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        article = get_object_or_404(Article, id=article_id)
        categories = self.get_queryset().filter(article=article).order_by('order')
        
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_tab_type(self, request):
        """
        Return categories grouped by tab type.
        """
        article_id = request.query_params.get('article_id')
        
        if not article_id:
            return Response(
                {"detail": "article_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        article = get_object_or_404(Article, id=article_id)
        
        # Get all tab types with categories for this article
        result = {}
        for tab_type, _ in ForumCategory.TAB_TYPE_CHOICES:
            categories = self.get_queryset().filter(
                article=article,
                tab_type=tab_type
            ).order_by('order')
            
            if categories.exists():
                result[tab_type] = self.get_serializer(categories, many=True).data
        
        return Response(result)


class ThreadViewSet(viewsets.ModelViewSet):
    """
    API endpoint for threads.
    """
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_locked', 'is_pinned', 'content_type', 'is_author_prompt', 'object_id']
    search_fields = ['title']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return ThreadDetailSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['get', 'put', 'patch'])
    def thread_settings(self, request, pk=None):
        """
        Get or update thread settings.
        """
        thread = self.get_object()
        
        # Check if user has permission to modify settings
        if request.method != 'GET' and request.user != thread.creator and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to modify these settings."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            settings, _ = ThreadSettings.objects.get_or_create(thread=thread)
            serializer = ThreadSettingsSerializer(settings)
            return Response(serializer.data)
        
        settings, _ = ThreadSettings.objects.get_or_create(thread=thread)
        
        if request.method == 'PUT':
            serializer = ThreadSettingsSerializer(settings, data=request.data)
        else:  # PATCH
            serializer = ThreadSettingsSerializer(settings, data=request.data, partial=True)
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """
        Lock or unlock a thread.
        """
        thread = self.get_object()
        
        # Check if user has permission to lock/unlock
        if request.user != thread.creator and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to lock/unlock this thread."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        thread.is_locked = not thread.is_locked
        thread.save(update_fields=['is_locked'])
        
        return Response({
            "status": "thread locked" if thread.is_locked else "thread unlocked",
            "is_locked": thread.is_locked
        })
    
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """
        Pin or unpin a thread.
        """
        thread = self.get_object()
        
        # Only staff/moderators can pin threads
        if not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to pin/unpin threads."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        thread.is_pinned = not thread.is_pinned
        thread.save(update_fields=['is_pinned'])
        
        return Response({
            "status": "thread pinned" if thread.is_pinned else "thread unpinned",
            "is_pinned": thread.is_pinned
        })
    
    @action(detail=False, methods=['get'])
    def for_source(self, request):
        """
        Return threads related to a specific source.
        """
        source_id = request.query_params.get('source_id')
        if not source_id:
            return Response(
                {"detail": "source_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        source = get_object_or_404(SourceArea, id=source_id)
        threads = self.get_queryset().filter(
            content_type='source_discussion',
            object_id=source.id
        )
        
        serializer = self.get_serializer(threads, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def author_prompts(self, request):
        """
        Return threads that are author prompts.
        """
        article_id = request.query_params.get('article_id')
        if not article_id:
            return Response(
                {"detail": "article_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        article = get_object_or_404(Article, id=article_id)
        categories = ForumCategory.objects.filter(article=article)
        
        threads = self.get_queryset().filter(
            category__in=categories,
            is_author_prompt=True
        )
        
        prompt_type = request.query_params.get('prompt_type')
        if prompt_type:
            threads = threads.filter(prompt_type=prompt_type)
        
        serializer = self.get_serializer(threads, many=True)
        return Response(serializer.data)