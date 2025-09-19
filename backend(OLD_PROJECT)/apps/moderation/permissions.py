# File: backend/apps/moderation/permissions.py
from rest_framework import permissions
from .models import Moderator

class IsAdminOrSelfForModeratorPermission(permissions.BasePermission):
    """
    Custom permission to only allow admins or users to view/edit their own moderator records.
    """
    def has_permission(self, request, view):
        # Authenticated users can view moderator records
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Only admins can create/update/delete moderator records
        return request.user.is_authenticated and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_staff:
            return True
        
        # Users can view their own moderator records
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user
        
        # Only admins can modify moderator records
        return False


class HasModeratorPermission(permissions.BasePermission):
    """
    Custom permission to only allow users with moderator privileges.
    """
    def has_permission(self, request, view):
        # Admins can do anything
        if request.user.is_staff:
            return True
        
        # Only moderators can access moderation actions
        return Moderator.objects.filter(
            user=request.user,
            active=True
        ).exists()
    
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_staff:
            return True
        
        # Moderators can see all actions but can only modify their own
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only the moderator who performed the action or an admin can modify it
        return obj.moderator.user == request.user