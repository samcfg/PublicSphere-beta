# File: backend/apps/moderation/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid
from django.utils import timezone

from .models import Moderator, ModerationAction

User = get_user_model()

class ModeratorModelTests(TestCase):
    """Test the Moderator model"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpassword'
        )
        self.mod_user = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='modpassword'
        )
        
        # Create a global moderator
        self.global_mod = Moderator.objects.create(
            user=self.mod_user,
            scope_type='global',
            appointed_by=self.admin_user,
            permissions={
                'delete_comments': True,
                'lock_threads': True,
                'ban_users': False,
                'remove_sources': False,
                'edit_content': False
            }
        )
    
    def test_moderator_string_representation(self):
        """Test the string representation of a Moderator"""
        self.assertEqual(
            str(self.global_mod),
            f"Moderator: {self.mod_user.username} - global"
        )
    
    def test_permission_properties(self):
        """Test permission properties"""
        self.assertTrue(self.global_mod.can_delete_comments)
        self.assertTrue(self.global_mod.can_lock_threads)
        self.assertFalse(self.global_mod.can_ban_users)
        self.assertFalse(self.global_mod.can_remove_sources)
        self.assertFalse(self.global_mod.can_edit_content)
    
    def test_set_default_permissions(self):
        """Test setting default permissions"""
        # Create moderator without permissions
        mod = Moderator.objects.create(
            user=self.regular_user,
            scope_type='article',
            scope_id=uuid.uuid4(),
            appointed_by=self.admin_user,
            permissions={}
        )
        
        # Set default permissions
        mod.set_default_permissions()
        
        # Check permissions
        self.assertTrue(mod.can_delete_comments)
        self.assertTrue(mod.can_lock_threads)
        self.assertFalse(mod.can_ban_users)
        self.assertFalse(mod.can_remove_sources)
        self.assertFalse(mod.can_edit_content)
    
    def test_user_is_moderator(self):
        """Test user_is_moderator class method"""
        # Admin is always a moderator
        self.assertTrue(Moderator.user_is_moderator(self.admin_user))
        
        # Global moderator can moderate anything
        self.assertTrue(Moderator.user_is_moderator(self.mod_user))
        self.assertTrue(Moderator.user_is_moderator(self.mod_user, 'article', uuid.uuid4()))
        
        # Regular user is not a moderator
        self.assertFalse(Moderator.user_is_moderator(self.regular_user))
        
        # Test with article-specific moderator
        article_id = uuid.uuid4()
        article_mod = Moderator.objects.create(
            user=self.regular_user,
            scope_type='article',
            scope_id=article_id,
            appointed_by=self.admin_user
        )
        
        self.assertTrue(Moderator.user_is_moderator(self.regular_user, 'article', article_id))
        self.assertFalse(Moderator.user_is_moderator(self.regular_user, 'article', uuid.uuid4()))
        self.assertFalse(Moderator.user_is_moderator(self.regular_user, 'category'))


class ModerationActionModelTests(TestCase):
    """Test the ModerationAction model"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        self.mod_user = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='modpassword'
        )
        
        # Create a moderator
        self.moderator = Moderator.objects.create(
            user=self.mod_user,
            scope_type='global',
            appointed_by=self.admin_user,
            permissions={
                'delete_comments': True,
                'lock_threads': True,
                'ban_users': False,
                'remove_sources': False,
                'edit_content': False
            }
        )
        
        # Create a moderation action
        self.action = ModerationAction.objects.create(
            moderator=self.moderator,
            action_type='delete_comment',
            target_type='comment',
            target_id=uuid.uuid4(),
            reason='Spam content'
        )
    
    def test_action_string_representation(self):
        """Test the string representation of a ModerationAction"""
        self.assertEqual(
            str(self.action),
            f"Delete Comment on comment (ID: {self.action.target_id}) by {self.mod_user.username}"
        )
    
    def test_is_reversed_property(self):
        """Test is_reversed property"""
        self.assertFalse(self.action.is_reversed)
        
        # Reverse the action
        admin_moderator = Moderator.objects.create(
            user=self.admin_user,
            scope_type='global',
            appointed_by=self.admin_user
        )
        
        self.action.reversed_by = admin_moderator
        self.action.reversed_at = timezone.now()
        self.action.save()
        
        self.assertTrue(self.action.is_reversed)


class ModeratorViewSetTests(TestCase):
    """Test the ModeratorViewSet"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpassword'
        )
        self.mod_user = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='modpassword'
        )
        
        # Create a global moderator
        self.global_mod = Moderator.objects.create(
            user=self.mod_user,
            scope_type='global',
            appointed_by=self.admin_user,
            permissions={
                'delete_comments': True,
                'lock_threads': True,
                'ban_users': False,
                'remove_sources': False,
                'edit_content': False
            }
        )
    
    def test_list_moderators_as_admin(self):
        """Test that an admin can list all moderators"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('moderator-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_moderators_as_regular_user(self):
        """Test that a regular user can see only their own moderator records"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('moderator-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        
        # Create a moderator record for the regular user
        article_mod = Moderator.objects.create(
            user=self.regular_user,
            scope_type='article',
            scope_id=uuid.uuid4(),
            appointed_by=self.admin_user
        )
        
        # Try again
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_moderator_as_admin(self):
        """Test that an admin can create a moderator"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('moderator-list')
        data = {
            'user_id': str(self.regular_user.id),
            'scope_type': 'article',
            'scope_id': str(uuid.uuid4()),
            'permissions': {
                'delete_comments': True,
                'lock_threads': True
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the moderator was created
        self.assertTrue(Moderator.objects.filter(user=self.regular_user).exists())
    
    def test_create_moderator_as_regular_user(self):
        """Test that a regular user cannot create a moderator"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('moderator-list')
        data = {
            'user_id': str(self.regular_user.id),
            'scope_type': 'article',
            'scope_id': str(uuid.uuid4()),
            'permissions': {
                'delete_comments': True,
                'lock_threads': True
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_deactivate_moderator(self):
        """Test deactivating a moderator"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('moderator-deactivate', args=[self.global_mod.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the moderator was deactivated
        self.global_mod.refresh_from_db()
        self.assertFalse(self.global_mod.active)
    
    def test_check_moderator_status(self):
        """Test checking if a user is a moderator for a scope"""
        self.client.force_authenticate(user=self.mod_user)
        url = reverse('moderator-check')
        response = self.client.get(url, {'scope_type': 'article'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_moderator'])
        
        # Test with a regular user
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url, {'scope_type': 'article'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_moderator'])


class ModerationActionViewSetTests(TestCase):
    """Test the ModerationActionViewSet"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        self.mod_user = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='modpassword'
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpassword'
        )
        
        # Create a moderator
        self.moderator = Moderator.objects.create(
            user=self.mod_user,
            scope_type='global',
            appointed_by=self.admin_user,
            permissions={
                'delete_comments': True,
                'lock_threads': True,
                'ban_users': False,
                'remove_sources': False,
                'edit_content': False
            }
        )
        
        # Create a moderation action
        self.action = ModerationAction.objects.create(
            moderator=self.moderator,
            action_type='delete_comment',
            target_type='comment',
            target_id=uuid.uuid4(),
            reason='Spam content'
        )
    
    def test_list_actions_as_admin(self):
        """Test that an admin can list all actions"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('moderationaction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_actions_as_moderator(self):
        """Test that a moderator can list actions"""
        self.client.force_authenticate(user=self.mod_user)
        url = reverse('moderationaction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_actions_as_regular_user(self):
        """Test that a regular user cannot list actions"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('moderationaction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_action_as_moderator(self):
        """Test that a moderator can create an action"""
        self.client.force_authenticate(user=self.mod_user)
        url = reverse('moderationaction-list')
        data = {
            'action_type': 'lock_thread',
            'target_type': 'thread',
            'target_id': str(uuid.uuid4()),
            'reason': 'Off-topic discussion'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the action was created
        self.assertEqual(ModerationAction.objects.count(), 2)
    
    def test_create_action_with_insufficient_permissions(self):
        """Test that a moderator cannot create an action they don't have permission for"""
        self.client.force_authenticate(user=self.mod_user)
        url = reverse('moderationaction-list')
        data = {
            'action_type': 'ban_user',  # Moderator doesn't have this permission
            'target_type': 'user',
            'target_id': str(uuid.uuid4()),
            'reason': 'Repeated violations'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_reverse_action(self):
        """Test reversing a moderation action"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create an admin moderator
        admin_moderator = Moderator.objects.create(
            user=self.admin_user,
            scope_type='global',
            appointed_by=self.admin_user
        )
        
        url = reverse('moderationaction-reverse', args=[self.action.id])
        data = {
            'reason': 'Action taken in error'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the action was reversed
        self.action.refresh_from_db()
        self.assertTrue(self.action.is_reversed)
    
    def test_get_actions_for_target(self):
        """Test getting actions for a specific target"""
        self.client.force_authenticate(user=self.mod_user)
        target_id = self.action.target_id
        url = reverse('moderationaction-for-target')
        response = self.client.get(url, {
            'target_type': 'comment',
            'target_id': str(target_id)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['target_id'], str(target_id))


class ModerationPermissionsTests(TestCase):
    """Test permissions for moderation views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        self.mod_user = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='modpassword'
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpassword'
        )
        
        # Create a moderator
        self.moderator = Moderator.objects.create(
            user=self.mod_user,
            scope_type='global',
            appointed_by=self.admin_user,
            permissions={
                'delete_comments': True,
                'lock_threads': True,
                'ban_users': False,
                'remove_sources': False,
                'edit_content': False
            }
        )
    
    def test_moderator_permissions_endpoint(self):
        """Test the permissions endpoint"""
        # Admin can access
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('moderator-permissions', args=[self.moderator.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Moderator can access their own permissions
        self.client.force_authenticate(user=self.mod_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Regular user cannot access
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_moderator_permissions(self):
        """Test updating moderator permissions"""
        # Admin can update permissions
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('moderator-permissions', args=[self.moderator.id])
        data = {
            'ban_users': True,
            'remove_sources': True
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that permissions were updated
        self.moderator.refresh_from_db()
        self.assertTrue(self.moderator.can_ban_users)
        self.assertTrue(self.moderator.can_remove_sources)
        
        # Moderator cannot update their own permissions
        self.client.force_authenticate(user=self.mod_user)
        data = {
            'edit_content': True
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)