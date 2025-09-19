# File: backend/apps/ratings/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count
from django_filters.rest_framework import DjangoFilterBackend

from .models import Rating
from .serializers import RatingSerializer, RatingStatsSerializer
from utils.permissions import IsRaterOrReadOnly

class RatingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing ratings.
    """
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsRaterOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['content_type', 'object_id', 'user']
    ordering_fields = ['created_at', 'updated_at', 'value']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Set the user when creating a rating"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get rating statistics for a specific object.
        Required query parameters: content_type, object_id
        """
        content_type = request.query_params.get('content_type')
        object_id = request.query_params.get('object_id')
        
        if not content_type or not object_id:
            return Response(
                {"detail": "Both content_type and object_id parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert object_id to string for consistent filtering
        object_id_str = str(object_id)
        
        # Get ratings for the object
        ratings = Rating.objects.filter(content_type=content_type, object_id=object_id_str)
        
        # Calculate statistics with proper null handling
        avg_result = ratings.aggregate(Avg('value'))['value__avg']
        
        stats = {
            # Explicitly handle null vs 0 - if no ratings, return null, otherwise convert Decimal to float
            'average': float(avg_result) if avg_result is not None else None,
            'count': ratings.count(),
            'distribution': Rating.get_rating_distribution(content_type, object_id),
            'user_rating': None
        }
        
        # Get user's rating if authenticated
        if request.user.is_authenticated:
            try:
                user_rating = Rating.objects.get(
                    content_type=content_type,
                    object_id=object_id_str,
                    user=request.user
                )
                stats['user_rating'] = RatingSerializer(user_rating).data
            except Rating.DoesNotExist:
                pass
        
        serializer = RatingStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_ratings(self, request):
        """
        Get ratings by the current user.
        Optional query parameter: content_type
        """
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Filter by user
        ratings = Rating.objects.filter(user=request.user)
        
        # Filter by content_type if provided
        content_type = request.query_params.get('content_type')
        if content_type:
            ratings = ratings.filter(content_type=content_type)
        
        # Paginate and return
        page = self.paginate_queryset(ratings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def rate(self, request):
        """
        Create or update a rating for a specific object.
        Required fields: content_type, object_id, value
        Optional field: explanation
        """
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Convert object_id to string for consistent storage
        data = request.data.copy()
        if 'object_id' in data:
            data['object_id'] = str(data['object_id'])
        
        # Create serializer with data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Use perform_create to save with user
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """
        Get top-rated objects for a specific content type.
        Required query parameter: content_type
        Optional query parameter: limit (default: 10)
        """
        content_type = request.query_params.get('content_type')
        limit = int(request.query_params.get('limit', 10))
        
        if not content_type:
            return Response(
                {"detail": "content_type parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get objects with at least 3 ratings
        rated_objects = Rating.objects.filter(content_type=content_type) \
            .values('object_id') \
            .annotate(
                average_rating=Avg('value'),
                rating_count=Count('id')
            ) \
            .filter(rating_count__gte=3) \
            .order_by('-average_rating')[:limit]
        
        return Response(rated_objects)