# File: backend/apps/sources/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .models import SourceArea, SourceAreaVersion
from .serializers import (
    SourceAreaSerializer, 
    SourceAreaDetailSerializer,
    SourceAreaVersionSerializer
)
from utils.permissions import IsCreatorOrReadOnly

class SourceAreaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows source areas to be viewed or edited.
    """
    queryset = SourceArea.objects.all()
    serializer_class = SourceAreaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author', 'content', 'institution']
    ordering_fields = ['created_at', 'updated_at', 'title', 'confidence_score']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SourceAreaDetailSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['get'])
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def versions(self, request, pk=None):
        """
        Return all versions of a source area
        """
        source_area = self.get_object()
        versions = source_area.versions.all()
        serializer = SourceAreaVersionSerializer(versions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """
        Create a new version of the source area
        """
        source_area = self.get_object()
        
        # Check if user has permission to create new versions
        if request.user != source_area.creator and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to create new versions of this source."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create new version
        new_version = source_area.create_new_version(request.user)
        
        # Return updated source area
        serializer = self.get_serializer(source_area)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced search for source areas
        """
        query = request.query_params.get('q', '')
        source_type = request.query_params.get('type')
        
        if not query:
            return Response({"results": []})
        
        queryset = self.get_queryset()
        
        # Filter by source type if provided
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        
        # Full text search across multiple fields
        results = queryset.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__icontains=query) |
            Q(institution__icontains=query)
        )
        
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)