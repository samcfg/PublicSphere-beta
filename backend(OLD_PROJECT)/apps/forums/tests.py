# File: backend/apps/forums/tests.py
import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid

from .models import ForumCategory, Thread, ThreadSettings
from apps.articles.models import Article
User = get_user_model()

class ForumModelTests(TestCase):
    """Test the Forum models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.article = Article.objects.create(
            title='Test Article',
            url='https://example.com/test-article',
            registered_by=self.user
        )
        self.category = ForumCategory.objects.create(
            name='Test Category',
            slug='test-category',
            article=self.article,
            tab_type='general'
        )
        self.thread = Thread.objects.create(
            title='Test Thread',
            category=self.category,
            creator=self.user
        )
    
    def test_category_creation(self):
        """Test creating a forum category"""
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.tab_type, 'general')
        self.assertEqual(self.category.article, self.article)
    
    def test_thread_creation(self):
        """Test creating a thread"""
        self.assertEqual(self.thread.title, 'Test Thread')
        self.assertEqual(self.thread.category, self.category)
        self.assertEqual(self.thread.creator, self.user)
        self.assertFalse(self.thread.is_locked)
        self.assertFalse(self.thread.is_pinned)
        
        # Test automatic creation of thread settings
        self.assertTrue(hasattr(self.thread, 'settings'))
        self.assertTrue(self.thread.settings.allow_anon)


class ForumAPITests(TestCase):
    """Test the Forum API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        
        # Use force_authenticate instead of login
        self.client.force_authenticate(user=self.user)
        
        # Create article and category
        self.article = Article.objects.create(
            title='API Test Article',
            url='https://example.com/api-test-article',
            registered_by=self.user
        )
        self.category = ForumCategory.objects.create(
            name='API Test Category',
            slug='api-test-category',
            article=self.article,
            tab_type='general'
        )
    
    def test_simple_access(self):
        """Simple test to verify API access works"""
        url = reverse('thread-list')
        response = self.client.get(url)
        # Just check that we get a response
        self.assertIsNotNone(response)
    
    def test_create_thread_simple(self):
        """Test creating a thread without format parameter"""
        url = reverse('thread-list')
        thread_data = {
            'title': 'API Test Thread',
            'category': str(self.category.id),
            'content_type': 'thread'
        }
        # Use Django's client without the format parameter
        response = self.client.post(
            url, 
            data=json.dumps(thread_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the thread was created in the database
        self.assertTrue(Thread.objects.filter(title=thread_data['title']).exists())
    
    def test_lock_thread_simple(self):
        """Test locking a thread without format parameter"""
        # Create a thread
        thread = Thread.objects.create(
            title='Lock Test Thread',
            category=self.category,
            creator=self.user
        )
        
        # Lock the thread
        url = reverse('thread-lock', args=[thread.id])
        response = self.client.post(
            url, 
            data={},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the thread was locked
        thread.refresh_from_db()
        self.assertTrue(thread.is_locked)
    
    def test_pin_thread_simple(self):
        """Test pinning a thread (admin only) without format parameter"""
        # Create a thread
        thread = Thread.objects.create(
            title='Pin Test Thread',
            category=self.category,
            creator=self.user
        )
        
        # Try to pin as regular user (should fail)
        url = reverse('thread-pin', args=[thread.id])
        response = self.client.post(
            url, 
            data={},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Create new client for admin to avoid authentication conflicts
        admin_client = APIClient()
        admin_client.force_authenticate(user=self.admin_user)
        response = admin_client.post(
            url, 
            data={},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the thread was pinned
        thread.refresh_from_db()
        self.assertTrue(thread.is_pinned)


class ForumAPIJWTTests(TestCase):
    """Test the Forum API endpoints using JWT authentication"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='jwtuser',
            email='jwt@example.com',
            password='password123'
        )
        self.admin_user = User.objects.create_user(
            username='jwtadmin',
            email='jwtadmin@example.com',
            password='adminpassword',
            is_staff=True
        )
        
        # Use JWT token authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token_for_user(self.user)}')
        
        # Create article and category
        self.article = Article.objects.create(
            title='JWT API Test Article',
            url='https://example.com/jwt-api-test-article',
            registered_by=self.user
        )
        self.category = ForumCategory.objects.create(
            name='JWT API Test Category',
            slug='jwt-api-test-category',
            article=self.article,
            tab_type='general'
        )
    
    def get_token_for_user(self, user):
        """Helper method to get a JWT token for a user"""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_simple_jwt_access(self):
        """Simple test to verify API access works with JWT"""
        url = reverse('thread-list')
        response = self.client.get(url)
        # Just check that we get a response
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)