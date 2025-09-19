# File: backend/apps/articles/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid

from .models import Article

User = get_user_model()

class ArticleModelTests(TestCase):
    """Test the Article model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.article = Article.objects.create(
            title='Test Article',
            url='https://example.com/test-article',
            author_name='Test Author',
            publication='Test Publication',
            registered_by=self.user,
            is_restricted=False
        )
    
    def test_article_creation(self):
        """Test creating an article"""
        self.assertEqual(self.article.title, 'Test Article')
        self.assertEqual(self.article.author_name, 'Test Author')
        self.assertEqual(self.article.registered_by, self.user)
        self.assertFalse(self.article.is_restricted)
    
    def test_article_string_representation(self):
        """Test the string representation of an article"""
        self.assertEqual(str(self.article), 'Test Article')
    # backend/apps/articles/tests.py
# Add a test for the new fields

    def test_article_content_fields(self):
        """Test creating an article with content fields"""
        article = Article.objects.create(
            title='Test Article with Content',
            url='https://publicsphere.fyi/articles/test-article',
            registered_by=self.user,
            content='# Test Markdown\n\nThis is a [test link](https://example.com)',
            content_format='markdown',
            is_self_hosted=True
        )
        self.assertEqual(article.content_format, 'markdown')
        self.assertTrue(article.is_self_hosted)
        self.assertTrue('Test Markdown' in article.content)

class ArticleAPITests(TestCase):
    """Test the Article API endpoints"""
    
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
        self.client.force_authenticate(user=self.user)
        self.article_data = {
            'title': 'API Test Article',
            'url': 'https://example.com/api-test-article',
            'author_name': 'API Author',
            'publication': 'API Publication'
        }
    
    def test_create_article(self):
        """Test creating an article via API"""
        url = reverse('article-list')
        response = self.client.post(url, self.article_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], self.article_data['title'])
        
        # Check that the article was created in the database
        self.assertTrue(Article.objects.filter(title=self.article_data['title']).exists())
    
    def test_toggle_restriction(self):
        """Test toggling article restriction"""
        # Create an article
        article = Article.objects.create(
            title='Restriction Test',
            url='https://example.com/restriction-test',
            registered_by=self.user
        )
        
        # Toggle restriction (requires staff privileges)
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('article-toggle-restriction', args=[article.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that restriction was toggled
        article.refresh_from_db()
        self.assertTrue(article.is_restricted)
        
        # Toggle again
        response = self.client.post(url)
        article.refresh_from_db()
        self.assertFalse(article.is_restricted)