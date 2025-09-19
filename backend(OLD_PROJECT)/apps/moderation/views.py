# File: backend/apps/moderation/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Moderator, ModerationAction
from .serializers import (
    ModeratorSerializer, 
    ModerationActionSerializer,
    ReverseActionSerializer,
    ModeratorPermissionsSerializer
)
from .permissions import (
    IsAdminOrSelfForModeratorPermission,
    HasModeratorPermission
)

class ModeratorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing moderators.
    """
    queryset = Moderator.objects.all()
    serializer_class = ModeratorSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelfForModeratorPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['user', 'scope_type', 'scope_id', 'active']
    search_fields = ['user__username']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        user = self.request.user
        
        # Admins can see all moderators
        if user.is_staff:
            return Moderator.objects.all()
        
        # Users can see only their own moderator records
        return Moderator.objects.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a moderator"""
        moderator = self.get_object()
        moderator.active = True
        moderator.save()
        serializer = self.get_serializer(moderator)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a moderator"""
        moderator = self.get_object()
        moderator.active = False
        moderator.save()
        serializer = self.get_serializer(moderator)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'put'])
    def permissions(self, request, pk=None):
        """Get or update moderator permissions"""
        moderator = self.get_object()
        
        if request.method == 'GET':
            serializer = ModeratorPermissionsSerializer(instance=moderator.permissions)
            return Response(serializer.data)
        
        # Update permissions
        serializer = ModeratorPermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update the permissions field with the validated data
        permissions = moderator.permissions.copy()
        permissions.update(serializer.validated_data)
        moderator.permissions = permissions
        moderator.save()
        
        return Response(ModeratorPermissionsSerializer(instance=moderator.permissions).data)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's moderator roles"""
        user = request.user
        moderator_roles = Moderator.objects.filter(user=user, active=True)
        serializer = self.get_serializer(moderator_roles, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """Check if the current user is a moderator for a specific scope"""
        user = request.user
        scope_type = request.query_params.get('scope_type')
        scope_id = request.query_params.get('scope_id')
        
        if not scope_type:
            return Response(
                {"detail": "scope_type parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_moderator = Moderator.user_is_moderator(user, scope_type, scope_id)
        
        if is_moderator:
            # Get the applicable moderator record for this scope
            moderator = None
            
            # Try to find an exact match first
            if scope_id:
                moderator = Moderator.objects.filter(
                    user=user,
                    active=True,
                    scope_type=scope_type,
                    scope_id=scope_id
                ).first()
            
            # If no exact match, try to find a broader match
            if not moderator:
                moderator = Moderator.objects.filter(
                    user=user,
                    active=True,
                    scope_type=scope_type,
                    scope_id__isnull=True
                ).first()
            
            # If still no match, try to find a global moderator
            if not moderator:
                moderator = Moderator.objects.filter(
                    user=user,
                    active=True,
                    scope_type='global'
                ).first()
            
            if moderator:
                serializer = self.get_serializer(moderator)
                return Response({
                    "is_moderator": True,
                    "moderator": serializer.data
                })
        
        return Response({"is_moderator": is_moderator})


class ModerationActionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for moderation actions.
    """
    queryset = ModerationAction.objects.all()
    serializer_class = ModerationActionSerializer
    permission_classes = [permissions.IsAuthenticated, HasModeratorPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['moderator', 'action_type', 'target_type', 'target_id']
    search_fields = ['reason', 'notes']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        user = self.request.user
        
        # Admins can see all actions
        if user.is_staff:
            return ModerationAction.objects.all()
        
        # Moderators can see their own actions
        moderator_ids = Moderator.objects.filter(user=user).values_list('id', flat=True)
        return ModerationAction.objects.filter(moderator__id__in=moderator_ids)
    
    @action(detail=True, methods=['post'])
    def reverse(self, request, pk=None):
        """Reverse a moderation action"""
        action = self.get_object()
        
        # Check if the action is already reversed
        if action.is_reversed:
            return Response(
                {"detail": "Action is already reversed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate the request
        serializer = ReverseActionSerializer(
            data=request.data,
            context={'action': action}
        )
        serializer.is_valid(raise_exception=True)
        
        # Find an appropriate moderator record for the current user
        user = request.user
        moderator = Moderator.objects.filter(
            user=user,
            active=True
        ).first()
        
        if not moderator:
            return Response(
                {"detail": "User is not an active moderator"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update the action
        action.reversed_by = moderator
        action.reversed_at = timezone.now()
        action.notes = (action.notes or "") + f"\n\nReversed: {serializer.validated_data['reason']}"
        action.save()
        
        # Return the updated action
        serializer = self.get_serializer(action)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def for_target(self, request):
        """Get moderation actions for a specific target"""
        target_type = request.query_params.get('target_type')
        target_id = request.query_params.get('target_id')
        
        if not target_type or not target_id:
            return Response(
                {"detail": "Both target_type and target_id parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        actions = self.get_queryset().filter(
            target_type=target_type,
            target_id=target_id
        )
        
        serializer = self.get_serializer(actions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def logs(self, request):
        """Get moderation logs with filtering options"""
        # Get query parameters
        moderator_id = request.query_params.get('moderator_id')
        scope_type = request.query_params.get('scope_type')
        scope_id = request.query_params.get('scope_id')
        action_type = request.query_params.get('action_type')
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        reversed = request.query_params.get('reversed')
        
        # Start with the base queryset
        queryset = self.get_queryset()
        
        # Apply filters based on query parameters
        if moderator_id:
            queryset = queryset.filter(moderator__id=moderator_id)
        
        if scope_type:
            # Filter by moderator scope
            moderators = Moderator.objects.filter(scope_type=scope_type)
            if scope_id:
                moderators = moderators.filter(scope_id=scope_id)
            
            moderator_ids = moderators.values_list('id', flat=True)
            queryset = queryset.filter(moderator__id__in=moderator_ids)
        
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        if from_date:
            queryset = queryset.filter(timestamp__gte=from_date)
        
        if to_date:
            queryset = queryset.filter(timestamp__lte=to_date)
        
        if reversed is not None:
            is_reversed = reversed.lower() == 'true'
            if is_reversed:
                queryset = queryset.filter(reversed_at__isnull=False)
            else:
                queryset = queryset.filter(reversed_at__isnull=True)
        
        # Paginate and return
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)