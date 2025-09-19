# File: backend/apps/access/tests.py
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid
from datetime import timedelta

from .models import UserArticleAccess
from apps.articles.models import Article

User = get_user_model()

class UserArticleAccessModelTests(TestCase):
    """Test the UserArticleAccess model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        self.article = Article.objects.create(
            title='Test Article',
            url='https://example.com/test-article',
            registered_by=self.admin_user,
            is_restricted=True
        )
        self.access = UserArticleAccess.objects.create(
            user=self.user,
            article=self.article,
            access_method='referrer',
            referrer_url='https://example.com/test-article'
        )
    
    def test_string_representation(self):
        """Test the string representation"""
        self.assertEqual(
            str(self.access),
            f"Access for {self.user.username} to {self.article.title}"
        )
    
    def test_is_expired_property(self):
        """Test is_expired property"""
        # Access without expiration should not be expired
        self.assertFalse(self.access.is_expired)
        
        # Set expiration in the past
        self.access.access_expires_at = timezone.now() - timedelta(days=1)
        self.access.save()
        self.assertTrue(self.access.is_expired)
        
        # Set expiration in the future
        self.access.access_expires_at = timezone.now() + timedelta(days=1)
        self.access.save()
        self.assertFalse(self.access.is_expired)
    
    def test_has_access_class_method(self):
        """Test has_access class method"""
        # User with access record should have access
        self.assertTrue(UserArticleAccess.has_access(self.user, self.article))
        
        # Admin should always have access
        self.assertTrue(UserArticleAccess.has_access(self.admin_user, self.article))
        
        # Create another user without access
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword'
        )
        self.assertFalse(UserArticleAccess.has_access(other_user, self.article))
        
        # Expired access should not grant access
        self.access.access_expires_at = timezone.now() - timedelta(days=1)
        self.access.save()
        self.assertFalse(UserArticleAccess.has_access(self.user, self.article))
        
        # Create unrestricted article - all authenticated users should have access
        unrestricted_article = Article.objects.create(
            title='Unrestricted Article',
            url='https://example.com/unrestricted',
            registered_by=self.admin_user,
            is_restricted=False
        )
        self.assertTrue(UserArticleAccess.has_access(self.user, unrestricted_article))
        self.assertTrue(UserArticleAccess.has_access(other_user, unrestricted_article))


class UserArticleAccessAPITests(TestCase):
    """Test the User Article Access API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword'
        )
        
        # Create articles
        self.article = Article.objects.create(
            title='Test Article',
            url='https://example.com/test-article',
            registered_by=self.admin_user,
            is_restricted=True
        )
        self.unrestricted_article = Article.objects.create(
            title='Unrestricted Article',
            url='https://example.com/unrestricted',
            registered_by=self.admin_user,
            is_restricted=False
        )
        
        # Create access record
        self.access = UserArticleAccess.objects.create(
            user=self.user,
            article=self.article,
            access_method='referrer',
            referrer_url='https://example.com/test-article'
        )
    
    def test_list_access_as_admin(self):
        """Test that an admin can list all access records"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('userarticleaccess-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_access_as_user(self):
        """Test that users can only see their own access records"""
        self.client.force_authenticate(user=self.user)
        url = reverse('userarticleaccess-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Other user should see no records
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_validate_referrer(self):
        """Test referrer validation"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('userarticleaccess-validate-referrer')
        
        # Valid referrer should grant access
        data = {
            'article_id': str(self.article.id),
            'referrer_url': 'https://example.com/test-article?param=value'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertTrue(response.data['access_granted'])
        
        # Check that access was granted
        self.assertTrue(
            UserArticleAccess.objects.filter(
                user=self.other_user,
                article=self.article
            ).exists()
        )
        
        # Invalid referrer
        data = {
            'article_id': str(self.article.id),
            'referrer_url': 'https://invalid.com/test-article'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['valid'])
        self.assertFalse(response.data['access_granted'])
    
    def test_check_access(self):
        """Test checking user access"""
        self.client.force_authenticate(user=self.user)
        url = reverse('userarticleaccess-check-access')
        
        # User should have access to the restricted article
        data = {
            'article_id': str(self.article.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_access'])
        self.assertTrue(response.data['is_restricted'])
        
        # User should have access to the unrestricted article
        data = {
            'article_id': str(self.unrestricted_article.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_access'])
        self.assertFalse(response.data['is_restricted'])
        
        # Other user should not have access to the restricted article
        self.client.force_authenticate(user=self.other_user)
        data = {
            'article_id': str(self.article.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_access'])
        self.assertTrue(response.data['is_restricted'])
    
    def test_grant_access(self):
        """Test granting access"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('userarticleaccess-grant-access')
        
        # Grant access to the other user
        data = {
            'user': str(self.other_user.id),
            'article': str(self.article.id),
            'access_method': 'direct',
            'expires_in_days': 30
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that access was granted
        access = UserArticleAccess.objects.get(
            user=self.other_user,
            article=self.article
        )
        self.assertEqual(access.access_method, 'direct')
        self.assertIsNotNone(access.access_expires_at)
        
        # Regular user cannot grant access
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_revoke_access(self):
        """Test revoking access"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('userarticleaccess-revoke', args=[self.access.id])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that access was revoked
        self.access.refresh_from_db()
        self.assertTrue(self.access.is_expired)
        
        # Regular user cannot revoke access
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ArticleAccessAPITests(TestCase):
    """Test the Article Access API endpoints"""
    
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
        self.users = []
        for i in range(5):
            self.users.append(
                User.objects.create_user(
                    username=f'user{i}',
                    email=f'user{i}@example.com',
                    password='password'
                )
            )
        
        # Create article
        self.article = Article.objects.create(
            title='Test Article',
            url='https://example.com/test-article',
            registered_by=self.admin_user,
            is_restricted=True
        )
        

        # Create access records for some users
        for i in range(3):
            UserArticleAccess.objects.create(
                user=self.users[i],
                article=self.article,
                access_method='direct'
            )
    
    def test_get_article_access_records(self):
        """Test retrieving all access records for an article"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('article-access-detail', args=[self.article.id])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Regular users should not be able to access this endpoint
        self.client.force_authenticate(user=self.users[0])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_grant_batch_access(self):
        """Test granting access to multiple users"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('article-access-grant-batch-access', args=[self.article.id])
        
        # Grant access to users 3 and 4 (who don't have access yet)
        data = {
            'user_ids': [str(self.users[3].id), str(self.users[4].id)],
            'access_method': 'invitation',
            'expires_in_days': 14
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['granted_count'], 2)
        
        # Check that access was granted
        self.assertTrue(
            UserArticleAccess.objects.filter(
                user=self.users[3],
                article=self.article,
                access_method='invitation'
            ).exists()
        )
        self.assertTrue(
            UserArticleAccess.objects.filter(
                user=self.users[4],
                article=self.article,
                access_method='invitation'
            ).exists()
        )
        
        # Regular users should not be able to grant batch access
        self.client.force_authenticate(user=self.users[0])
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_revoke_all_access(self):
        """Test revoking access for all users"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('article-access-revoke-all-access', args=[self.article.id])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['revoked_count'], 3)
        
        # Check that all access records were revoked
        for i in range(3):
            access = UserArticleAccess.objects.get(
                user=self.users[i],
                article=self.article
            )
            self.assertTrue(access.is_expired)
        
        # Regular users should not be able to revoke all access
        self.client.force_authenticate(user=self.users[0])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReferrerMiddlewareTests(TestCase):
    """
    Test the referrer validation middleware.
    
    Note: This assumes you have a middleware in place for validating
    referrers in HTTP requests. If you're using a different approach
    for referrer validation, you might need to adjust these tests.
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        
        # Create articles
        self.article = Article.objects.create(
            title='Test Article',
            url='https://example.com/test-article',
            registered_by=self.admin_user,
            is_restricted=True
        )
        self.unrestricted_article = Article.objects.create(
            title='Unrestricted Article',
            url='https://example.com/unrestricted',
            registered_by=self.admin_user,
            is_restricted=False
        )
    
    def test_my_access_endpoint(self):
        """Test the my_access endpoint"""
        self.client.force_authenticate(user=self.user)
        url = reverse('userarticleaccess-my-access')
        
        # Initially, user should have no access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        
        # Grant access to the restricted article
        UserArticleAccess.objects.create(
            user=self.user,
            article=self.article,
            access_method='direct'
        )
        
        # Now user should have one access record
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Add an expired access record
        expired_article = Article.objects.create(
            title='Expired Article',
            url='https://example.com/expired',
            registered_by=self.admin_user,
            is_restricted=True
        )
        UserArticleAccess.objects.create(
            user=self.user,
            article=expired_article,
            access_method='direct',
            access_expires_at=timezone.now() - timedelta(days=1)
        )
        
        # User should still only see one non-expired access record
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_access_with_various_expiration_scenarios(self):
        """Test access with different expiration scenarios"""
        # Create access records with different expiration settings
        
        # 1. Permanent access (no expiration)
        permanent_access = UserArticleAccess.objects.create(
            user=self.user,
            article=self.article,
            access_method='direct'
        )
        
        # 2. Future expiration
        future_article = Article.objects.create(
            title='Future Expiration Article',
            url='https://example.com/future',
            registered_by=self.admin_user,
            is_restricted=True
        )
        future_access = UserArticleAccess.objects.create(
            user=self.user,
            article=future_article,
            access_method='direct',
            access_expires_at=timezone.now() + timedelta(days=30)
        )
        
        # 3. Expired access
        expired_article = Article.objects.create(
            title='Expired Article',
            url='https://example.com/expired',
            registered_by=self.admin_user,
            is_restricted=True
        )
        expired_access = UserArticleAccess.objects.create(
            user=self.user,
            article=expired_article,
            access_method='direct',
            access_expires_at=timezone.now() - timedelta(days=1)
        )
        
        # Check access for each case
        self.assertTrue(UserArticleAccess.has_access(self.user, self.article))
        self.assertTrue(UserArticleAccess.has_access(self.user, future_article))
        self.assertFalse(UserArticleAccess.has_access(self.user, expired_article))
        
        # Unrestricted article should be accessible without access record
        self.assertTrue(UserArticleAccess.has_access(self.user, self.unrestricted_article))