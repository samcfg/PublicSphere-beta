# File: backend/apps/sources/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid
from django.utils import timezone
from unittest import skip

from .models import SourceArea, SourceAreaVersion
from apps.articles.models import Article

User = get_user_model()

class SourceAreaModelTests(TestCase):
    """Test the SourceArea model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        # Create a valid SourceArea with all required fields including explicit id
        self.source = SourceArea.objects.create(
            id=uuid.uuid4(),  # Explicitly set the ID
            title='Test Source',
            creator=self.user,
            content='This is test content for the source area.'
        )
    
    def test_source_creation(self):
        """Test creating a source area"""
        self.assertEqual(self.source.title, 'Test Source')
        self.assertEqual(self.source.creator, self.user)
        self.assertEqual(self.source.content, 'This is test content for the source area.')
        self.assertEqual(self.source.version, 1)  # Default version should be 1


class SourceAreaAPITests(TestCase):
    """Test the SourceArea API endpoints"""
    
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
        
        # Create a source area with explicit ID
        self.source = SourceArea.objects.create(
            id=uuid.uuid4(),  # Explicitly set the ID
            title='API Test Source',
            creator=self.user,
            content='API test content'
        )
   
    def test_update_source(self):
        """Test updating a source area"""
        url = reverse('sourcearea-detail', args=[self.source.id])
        update_data = {
            'title': 'Updated Source Title',
            'content': 'Updated content'
        }
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the source was updated
        self.source.refresh_from_db()
        self.assertEqual(self.source.title, update_data['title'])
        self.assertEqual(self.source.content, update_data['content'])
    
    def test_other_user_update(self):
        """Test that other users cannot update a source area"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('sourcearea-detail', args=[self.source.id])
        update_data = {
            'title': 'Other User Update',
            'content': 'This should fail'
        }
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        