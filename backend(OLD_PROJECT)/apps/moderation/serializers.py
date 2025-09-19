# File: backend/apps/moderation/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Moderator, ModerationAction

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for User model to include in nested serializations"""
    class Meta:
        model = User
        fields = ['id', 'username', 'reputation']
        read_only_fields = ['id', 'username', 'reputation']
        
class ModeratorSerializer(serializers.ModelSerializer):
    """Serializer for moderators"""
    user = UserMinimalSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    appointed_by = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = Moderator
        fields = [
            'id', 'user', 'user_id', 'scope_type', 'scope_id',
            'appointed_by', 'appointed_at', 'permissions', 'active'
        ]
        read_only_fields = ['id', 'appointed_by', 'appointed_at']
    
    def validate(self, data):
        """Validate the moderator data"""
        # Ensure the user exists
        user_id = data.get('user_id')
        if user_id:
            try:
                User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError({"user_id": "User does not exist"})
        
        # Ensure scope_id is provided when scope_type is not global
        scope_type = data.get('scope_type')
        scope_id = data.get('scope_id')
        if scope_type != 'global' and not scope_id:
            raise serializers.ValidationError(
                {"scope_id": f"scope_id is required for scope_type '{scope_type}'"}
            )
        
        # Validate permissions
        permissions = data.get('permissions')
        if permissions:
            valid_permissions = [
                'delete_comments', 'lock_threads', 'ban_users', 
                'remove_sources', 'edit_content'
            ]
            for perm in permissions:
                if perm not in valid_permissions:
                    raise serializers.ValidationError(
                        {"permissions": f"Invalid permission: {perm}"}
                    )
        
        return data
    
    def create(self, validated_data):
        """Create a new moderator"""
        # Set the appointing user
        validated_data['appointed_by'] = self.context['request'].user
        
        # Get the user from the user_id
        user_id = validated_data.pop('user_id')
        validated_data['user'] = User.objects.get(id=user_id)
        
        # Create the moderator
        moderator = Moderator.objects.create(**validated_data)
        
        # Set default permissions if none provided
        if not moderator.permissions:
            moderator.set_default_permissions()
        
        return moderator


class ModerationActionSerializer(serializers.ModelSerializer):
    """Serializer for moderation actions"""
    moderator = serializers.StringRelatedField(read_only=True)
    moderator_id = serializers.UUIDField(write_only=True, required=False)
    reversed_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = ModerationAction
        fields = [
            'id', 'moderator', 'moderator_id', 'action_type', 
            'target_type', 'target_id', 'reason', 'notes',
            'timestamp', 'reversed_by', 'reversed_at', 'is_reversed'
        ]
        read_only_fields = ['id', 'timestamp', 'reversed_by', 'reversed_at', 'is_reversed']
    
    def validate(self, data):
        """Validate the moderation action data"""
        # Ensure the action type is valid for the moderator's permissions
        action_type = data.get('action_type')
        moderator = None
        
        if self.context['request'].method == 'POST':
            # For new actions, get the moderator record for the current user
            user = self.context['request'].user
            moderator_id = data.get('moderator_id')
            
            if moderator_id:
                try:
                    moderator = Moderator.objects.get(id=moderator_id)
                except Moderator.DoesNotExist:
                    raise serializers.ValidationError({"moderator_id": "Moderator does not exist"})
            else:
                # Try to find an appropriate moderator record
                moderators = Moderator.objects.filter(user=user, active=True)
                if not moderators.exists():
                    raise serializers.ValidationError(
                        {"moderator_id": "User is not a moderator or moderator_id is required"}
                    )
                
                # Use global moderator if available, otherwise use the first one
                global_moderator = moderators.filter(scope_type='global').first()
                moderator = global_moderator if global_moderator else moderators.first()
            
            # Store the moderator for use in create
            self.context['moderator'] = moderator
            
            # Check permissions
            if action_type == 'delete_comment' and not moderator.can_delete_comments:
                raise serializers.ValidationError(
                    {"action_type": "Moderator does not have permission to delete comments"}
                )
            elif action_type == 'lock_thread' and not moderator.can_lock_threads:
                raise serializers.ValidationError(
                    {"action_type": "Moderator does not have permission to lock threads"}
                )
            elif action_type == 'ban_user' and not moderator.can_ban_users:
                raise serializers.ValidationError(
                    {"action_type": "Moderator does not have permission to ban users"}
                )
            elif action_type == 'remove_source' and not moderator.can_remove_sources:
                raise serializers.ValidationError(
                    {"action_type": "Moderator does not have permission to remove sources"}
                )
            elif action_type == 'edit_content' and not moderator.can_edit_content:
                raise serializers.ValidationError(
                    {"action_type": "Moderator does not have permission to edit content"}
                )
        
        return data
    
    def create(self, validated_data):
        """Create a new moderation action"""
        # Remove moderator_id if present
        validated_data.pop('moderator_id', None)
        
        # Use the moderator from context
        validated_data['moderator'] = self.context['moderator']
        
        return ModerationAction.objects.create(**validated_data)


class ReverseActionSerializer(serializers.Serializer):
    """Serializer for reversing a moderation action"""
    reason = serializers.CharField(required=True)
    
    def validate(self, data):
        # Check that the action is not already reversed
        action = self.context['action']
        if action.is_reversed:
            raise serializers.ValidationError({"detail": "Action is already reversed"})
        
        return data


class ModeratorPermissionsSerializer(serializers.Serializer):
    """Serializer for updating moderator permissions"""
    delete_comments = serializers.BooleanField(required=False)
    lock_threads = serializers.BooleanField(required=False)
    ban_users = serializers.BooleanField(required=False)
    remove_sources = serializers.BooleanField(required=False)
    edit_content = serializers.BooleanField(required=False)