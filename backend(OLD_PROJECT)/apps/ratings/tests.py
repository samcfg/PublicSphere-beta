# File: backend/apps/ratings/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid

from .models import Rating
from apps.articles.models import Article
from apps.sources.models import SourceArea

User = get_user_model()

class RatingModelTests(TestCase):
    """Test the Rating model"""
    
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
        self.source = SourceArea.objects.create(
            title='Test Source',
            creator=self.user,
            content='Test content'
        )
        self.article_rating = Rating.objects.create(
            user=self.user,
            content_type='article',
            object_id=self.article.id,
            value=85.5
        )
        self.source_rating = Rating.objects.create(
            user=self.user,
            content_type='source_area',
            object_id=self.source.id,
            value=75.0
        )
    
    def test_rating_creation(self):
        """Test creating ratings"""
        self.assertEqual(self.article_rating.value, 85.5)
        self.assertEqual(self.article_rating.content_type, 'article')
        self.assertEqual(str(self.article_rating.object_id), str(self.article.id))
        
        self.assertEqual(self.source_rating.value, 75.0)
        self.assertEqual(self.source_rating.content_type, 'source_area')
    
    def test_average_rating(self):
        """Test average rating calculation"""
        # Create another user and rating
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword'
        )
        Rating.objects.create(
            user=other_user,
            content_type='article',
            object_id=self.article.id,
            value=90.0
        )
        
        # Calculate average
        avg = Rating.get_average_rating('article', self.article.id)
        self.assertAlmostEqual(avg, 87.75)  # (85.5 + 90.0) / 2


class RatingAPITests(TestCase):
    """Test the Rating API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create article and source
        self.article = Article.objects.create(
            title='API Test Article',
            url='https://example.com/api-test-article',
            registered_by=self.user
        )
        self.source = SourceArea.objects.create(
            title='API Test Source',
            creator=self.user,
            content='API test content'
        )
    
    def test_create_rating(self):
        """Test creating a rating via API"""
        url = reverse('rating-list')
        rating_data = {
            'content_type': 'article',
            'object_id': str(self.article.id),
            'value': 95.0,
            'explanation': 'Excellent article'
        }
        response = self.client.post(url, rating_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['value']), rating_data['value'])
        
        # Check that the rating was created in the database
        self.assertTrue(
            Rating.objects.filter(
                user=self.user,
                content_type='article',
                object_id=self.article.id
            ).exists()
        )
    
    def test_rating_stats(self):
        """Test getting rating statistics"""
        # Create ratings
        Rating.objects.create(
            user=self.user,
            content_type='source_area',
            object_id=self.source.id,
            value=80.0
        )
        Rating.objects.create(
            user=self.other_user,
            content_type='source_area',
            object_id=self.source.id,
            value=70.0
        )
        
        # Get statistics
        url = reverse('rating-stats')
        response = self.client.get(url, {
            'content_type': 'source_area',
            'object_id': str(self.source.id)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['average'], 75.0)
        self.assertIn('distribution', response.data)
        self.assertIn('user_rating', response.data)