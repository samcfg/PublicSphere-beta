# File: backend/apps/articles/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend

from .models import Article
from .serializers import ArticleSerializer, ArticleDetailSerializer
from utils.permissions import IsAdminOrReadOnly, IsRegistrarOrReadOnly

class ArticleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing articles.
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['publication', 'is_restricted', 'is_featured']
    search_fields = ['title', 'author_name', 'publication', 'description']
    ordering_fields = ['created_at', 'pub_date', 'view_count', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return ArticleDetailSerializer
        return ArticleSerializer
    
    @action(detail=False, methods=['get'], url_path='by-slug/(?P<slug>[^/.]+)')
    def by_slug(self, request, slug=None):
        """Retrieve article by slug."""
        try:
            article = Article.objects.get(slug=slug)
            # Increment view count
            #article.view_count = F('view_count') + 1  
            #article.save(update_fields=['view_count'])
            serializer = self.get_serializer(article)
            return Response(serializer.data)
        except Article.DoesNotExist:
            return Response(
                {"detail": "Article not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    def perform_create(self, serializer):
        """Save the article with the current user as registrar."""
        serializer.save(registered_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        """Increment the view count for an article."""
        article = self.get_object()
        article.view_count = F('view_count') + 1
        article.save(update_fields=['view_count'])
        return Response({'status': 'view count incremented'})
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Return only featured articles."""
        featured = Article.objects.filter(is_featured=True)
        serializer = self.get_serializer(featured, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_publication(self, request):
        """Group articles by publication."""
        from django.db.models import Count
        publications = Article.objects.values('publication').annotate(
            count=Count('id')
        ).order_by('-count')
        return Response(publications)
    
    @action(detail=True, methods=['post'])
    def toggle_restriction(self, request, pk=None):
        """Toggle the restriction status of an article."""
        article = self.get_object()
        article.is_restricted = not article.is_restricted
        article.save(update_fields=['is_restricted'])
        return Response({
            'status': 'restriction updated',
            'is_restricted': article.is_restricted
        })
    
    @action(detail=True, methods=['put'], url_path='bibliography-order')
    def set_bibliography_order(self, request, slug=None):
        """
        Set the source bibliography order for an article.
        
        Body: { "source_ids": ["uuid1", "uuid2", "uuid3"] }
        """
        article = self.get_object()
        
        source_ids = request.data.get('source_ids')
        if source_ids is None:
            return Response(
                {"error": "source_ids field is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Basic validation
        if not isinstance(source_ids, list):
            return Response(
                {"error": "source_ids must be a list"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for duplicates
        if len(source_ids) != len(set(source_ids)):
            return Response(
                {"error": "source_ids cannot contain duplicates"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the article
        article.source_bibliography_order = source_ids if source_ids else None
        article.save(update_fields=['source_bibliography_order'])
        
        return Response({
            "message": "Bibliography order updated successfully",
            "source_ids": source_ids
        })