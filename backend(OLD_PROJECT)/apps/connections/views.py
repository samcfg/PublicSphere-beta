# File: backend/apps/connections/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Connection
from .serializers import ConnectionSerializer, ConnectionDetailSerializer
from utils.permissions import IsCreatorOrReadOnly

class ConnectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Connection objects.
    
    Provides CRUD operations for connections between articles and source areas.
    """
    queryset = Connection.objects.all()
    serializer_class = ConnectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['article_id', 'sourcearea_id', 'creator']
    search_fields = ['source_text', 'argument_text', 'explainer_text']
    ordering_fields = ['created_at', 'updated_at', 'confidence_score']
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        """
        if self.action == 'retrieve':
            return ConnectionDetailSerializer
        return ConnectionSerializer
    
    def perform_create(self, serializer):
        """
        Set the creator when creating a new connection.
        """
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """
        Update the confidence score for a connection.
        """
        connection = self.get_object()
        score = request.data.get('score')
        
        if score is None:
            return Response({"error": "Confidence score is required"}, status=400)
        
        try:
            score = float(score)
            if not (0 <= score <= 100):
                return Response({"error": "Score must be between 0 and 100"}, status=400)
        except ValueError:
            return Response({"error": "Score must be a number"}, status=400)
        
        connection.confidence_score = score
        connection.save()
        
        serializer = self.get_serializer(connection)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_article(self, request):
        """
        List connections filtered by article_id.
        """
        article_id = request.query_params.get('article_id')
        if not article_id:
            return Response({"error": "article_id parameter is required"}, status=400)
        
        connections = self.queryset.filter(article_id=article_id)
        page = self.paginate_queryset(connections)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(connections, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_source(self, request):
        """
        List connections filtered by sourcearea_id.
        """
        sourcearea_id = request.query_params.get('sourcearea_id')
        if not sourcearea_id:
            return Response({"error": "sourcearea_id parameter is required"}, status=400)
        
        connections = self.queryset.filter(sourcearea_id=sourcearea_id)
        page = self.paginate_queryset(connections)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(connections, many=True)
        return Response(serializer.data)