# File: backend/apps/access/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from urllib.parse import urlparse

from .models import UserArticleAccess
from .serializers import (
    UserArticleAccessSerializer,
    UserArticleAccessCreateSerializer,
    ReferrerValidationSerializer,
    AccessCheckSerializer
)
from apps.articles.models import Article
from utils.permissions import IsAdminOrReadOnly

User = get_user_model()

class UserArticleAccessViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user article access.
    """
    queryset = UserArticleAccess.objects.all()
    serializer_class = UserArticleAccessSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'article', 'access_method']
    ordering_fields = ['access_granted_at', 'access_expires_at']
    ordering = ['-access_granted_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        user = self.request.user
        
        # Admins can see all access records
        if user.is_staff:
            return UserArticleAccess.objects.all()
        
        # Regular users can only see their own access records
        return UserArticleAccess.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserArticleAccessCreateSerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def validate_referrer(self, request):
        """
        Validate a referrer URL and grant access if valid.
        This endpoint should be called by the frontend when a user clicks
        a link from a publisher's website to PublicSphere.
        """
        serializer = ReferrerValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        article = serializer.validated_data['article']
        referrer_url = serializer.validated_data['referrer_url']
        
        # Skip validation for non-restricted articles
        if not article.is_restricted:
            return Response({
                "valid": True,
                "message": "Article is not restricted",
                "access_granted": False
            })
        
        # Validate the referrer against the article URL
        # This is a simplified check - in a real implementation, you would
        # validate domain matching, publisher verification, etc.
        article_domain = urlparse(article.url).netloc
        referrer_domain = urlparse(referrer_url).netloc
        valid_referrer = article_domain == referrer_domain
        
        if valid_referrer and request.user.is_authenticated:
            # Grant access by creating or updating the access record
            access, created = UserArticleAccess.objects.update_or_create(
                user=request.user,
                article=article,
                defaults={
                    'access_method': 'referrer',
                    'referrer_url': referrer_url,
                    'access_granted_at': timezone.now(),
                    'access_expires_at': None  # Permanent access
                }
            )
            
            return Response({
                "valid": True,
                "message": "Referrer validated successfully",
                "access_granted": True,
                "access": UserArticleAccessSerializer(access).data
            })
        
        return Response({
            "valid": valid_referrer,
            "message": "Referrer validation failed" if not valid_referrer else "Authentication required for access",
            "access_granted": False
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def check_access(self, request):
        """Check if the current user has access to an article"""
        serializer = AccessCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        article = serializer.validated_data['article']
        has_access = UserArticleAccess.has_access(request.user, article)
        
        return Response({
            "has_access": has_access,
            "is_restricted": article.is_restricted
        })
    
    @action(detail=False, methods=['get'])
    def my_access(self, request):
        """Get all articles the current user has access to"""
        user = request.user
        
        # Get all access records for the user
        access_records = UserArticleAccess.objects.filter(
            user=user
        ).exclude(
            # Exclude expired access
            access_expires_at__isnull=False,
            access_expires_at__lt=timezone.now()
        )
        
        serializer = self.get_serializer(access_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke access by setting an immediate expiration"""
        access = self.get_object()
        
        # Only staff can revoke access
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to revoke access"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Set expired timestamp to now
        access.access_expires_at = timezone.now()
        access.save()
        
        serializer = self.get_serializer(access)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def grant_access(self, request):
        """Grant direct access to an article for a user"""
        # Only staff can grant direct access
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to grant access"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserArticleAccessCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Default to direct access method if not specified
        if 'access_method' not in serializer.validated_data:
            serializer.validated_data['access_method'] = 'direct'
        
        # Create or update the access record
        user = serializer.validated_data.pop('user')
        article = serializer.validated_data.pop('article')
        
        access, created = UserArticleAccess.objects.update_or_create(
            user=user,
            article=article,
            defaults=serializer.validated_data
        )
        
        response_serializer = UserArticleAccessSerializer(access)
        return Response(response_serializer.data)


class ArticleAccessViewSet(viewsets.ViewSet):
    """
    API endpoint for article access management from the article perspective.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    
    def retrieve(self, request, pk=None):
        """Get all access records for a specific article"""
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to view this information"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        article = get_object_or_404(Article, pk=pk)
        access_records = UserArticleAccess.objects.filter(article=article)
        
        serializer = UserArticleAccessSerializer(access_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def grant_batch_access(self, request, pk=None):
        """Grant access to multiple users for this article"""
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to grant access"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        article = get_object_or_404(Article, pk=pk)
        user_ids = request.data.get('user_ids', [])
        access_method = request.data.get('access_method', 'direct')
        expires_in_days = request.data.get('expires_in_days')
        
        if not user_ids:
            return Response(
                {"detail": "No user IDs provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate expiration date if provided
        access_expires_at = None
        if expires_in_days:
            access_expires_at = timezone.now() + timezone.timedelta(days=expires_in_days)
        
        # Grant access to each user
        granted = []
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                access, created = UserArticleAccess.objects.update_or_create(
                    user=user,
                    article=article,
                    defaults={
                        'access_method': access_method,
                        'access_expires_at': access_expires_at
                    }
                )
                granted.append(UserArticleAccessSerializer(access).data)
            except User.DoesNotExist:
                continue
        
        return Response({
            "granted_count": len(granted),
            "total_requested": len(user_ids),
            "granted_access": granted
        })
    
    @action(detail=True, methods=['post'])
    def revoke_all_access(self, request, pk=None):
        """Revoke all access for this article"""
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to revoke access"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        article = get_object_or_404(Article, pk=pk)
        
        # Set all access records to expired
        now = timezone.now()
        updated = UserArticleAccess.objects.filter(article=article).update(
            access_expires_at=now
        )
        
        return Response({
            "revoked_count": updated,
            "message": f"Revoked access for {updated} users"
        })