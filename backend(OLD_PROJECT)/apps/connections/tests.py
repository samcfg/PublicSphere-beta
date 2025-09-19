# File: backend/apps/connections/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid
from decimal import Decimal

from .models import Connection
from apps.articles.models import Article
from apps.sources.models import SourceArea

User = get_user_model()

class ConnectionModelTests(TestCase):
    """Test the Connection model"""
    
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
            content='Test source content'
        )
        self.connection = Connection.objects.create(
            article_id=self.article.id,
            sourcearea_id=self.source.id,
            article_text='Referenced text from article',
            explainer_text='This source supports the claim',
            confidence_score=85.50,
            creator=self.user
        )
    
    def test_connection_creation(self):
        """Test creating a connection"""
        self.assertEqual(self.connection.article_id, self.article.id)
        self.assertEqual(self.connection.sourcearea_id, self.source.id)
        self.assertEqual(self.connection.article_text, 'Referenced text from article')
        self.assertEqual(self.connection.explainer_text, 'This source supports the claim')
        self.assertEqual(self.connection.confidence_score, Decimal('85.50'))
        self.assertEqual(self.connection.creator, self.user)
    
    def test_connection_string_representation(self):
        """Test the string representation of a connection"""
        expected = f"Connection {self.connection.id}: Article {self.article.id} to Source {self.source.id}"
        self.assertEqual(str(self.connection), expected)
    
    def test_confidence_score_validation(self):
        """Test confidence score validation"""
        # Valid scores
        connection = Connection(
            article_id=self.article.id,
            sourcearea_id=self.source.id,
            confidence_score=0,
            creator=self.user
        )
        connection.full_clean()  # Should not raise
        
        connection.confidence_score = 100
        connection.full_clean()  # Should not raise
        
        connection.confidence_score = 50.25
        connection.full_clean()  # Should not raise
    
    def test_optional_fields(self):
        """Test connection with minimal required fields"""
        minimal_connection = Connection.objects.create(
            article_id=self.article.id,
            sourcearea_id=self.source.id,
            creator=self.user
        )
        self.assertEqual(minimal_connection.article_text, '')
        self.assertEqual(minimal_connection.explainer_text, '')
        self.assertIsNone(minimal_connection.confidence_score)
    
    def test_connection_ordering(self):
        """Test default ordering by created_at descending"""
        # Create another connection
        connection2 = Connection.objects.create(
            article_id=self.article.id,
            sourcearea_id=self.source.id,
            creator=self.user
        )
        
        connections = list(Connection.objects.all())
        self.assertEqual(connections[0], connection2)  # Most recent first
        self.assertEqual(connections[1], self.connection)


class ConnectionAPITests(TestCase):
    """Test the Connection API endpoints"""
    
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
        
        # Create test article and source
        self.article = Article.objects.create(
            title='API Test Article',
            url='https://example.com/api-test-article',
            registered_by=self.user
        )
        self.source = SourceArea.objects.create(
            title='API Test Source',
            creator=self.user,
            content='API test source content'
        )
        
        self.connection = Connection.objects.create(
            article_id=self.article.id,
            sourcearea_id=self.source.id,
            article_text='Test article text',
            explainer_text='Test explanation',
            confidence_score=75.0,
            creator=self.user
        )
    
    def test_create_connection(self):
        """Test creating a connection via API"""
        url = reverse('connection-list')
        connection_data = {
            'article_id': str(self.article.id),
            'sourcearea_id': str(self.source.id),
            'article_text': 'New connection article text',
            'explainer_text': 'New connection explanation',
            'confidence_score': 90.0
        }
        response = self.client.post(url, connection_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['article_text'], connection_data['article_text'])
        self.assertEqual(response.data['creator']['id'], str(self.user.id))
        
        # Check that the connection was created in the database
        self.assertTrue(
            Connection.objects.filter(
                article_text=connection_data['article_text']
            ).exists()
        )
    
    def test_list_connections(self):
        """Test listing connections"""
        url = reverse('connection-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.connection.id)
    
    def test_retrieve_connection(self):
        """Test retrieving a specific connection"""
        url = reverse('connection-detail', args=[self.connection.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.connection.id)
        self.assertEqual(response.data['article_text'], self.connection.article_text)
    
    def test_update_connection(self):
        """Test updating a connection"""
        url = reverse('connection-detail', args=[self.connection.id])
        update_data = {
            'article_text': 'Updated article text',
            'confidence_score': 95.0
        }
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the connection was updated
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.article_text, update_data['article_text'])
        self.assertEqual(float(self.connection.confidence_score), update_data['confidence_score'])
    
    def test_delete_connection(self):
        """Test deleting a connection"""
        url = reverse('connection-detail', args=[self.connection.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check that the connection was deleted
        self.assertFalse(Connection.objects.filter(id=self.connection.id).exists())
    
    def test_rate_connection(self):
        """Test rating a connection via the rate endpoint"""
        url = reverse('connection-rate', args=[self.connection.id])
        rate_data = {'score': 88.5}
        response = self.client.post(url, rate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the confidence score was updated
        self.connection.refresh_from_db()
        self.assertEqual(float(self.connection.confidence_score), rate_data['score'])
    
    def test_rate_connection_invalid_score(self):
        """Test rating with invalid confidence score"""
        url = reverse('connection-rate', args=[self.connection.id])
        
        # Test score above 100
        response = self.client.post(url, {'score': 150}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test negative score
        response = self.client.post(url, {'score': -10}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test non-numeric score
        response = self.client.post(url, {'score': 'invalid'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_connections_by_article(self):
        """Test filtering connections by article"""
        # Create another article and connection
        article2 = Article.objects.create(
            title='Second Article',
            url='https://example.com/second-article',
            registered_by=self.user
        )
        Connection.objects.create(
            article_id=article2.id,
            sourcearea_id=self.source.id,
            creator=self.user
        )
        
        url = reverse('connection-by-article')
        response = self.client.get(url, {'article_id': str(self.article.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['article_id'], str(self.article.id))
        
        # Test without article_id parameter
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_connections_by_source(self):
        """Test filtering connections by source"""
        # Create another source and connection
        source2 = SourceArea.objects.create(
            title='Second Source',
            creator=self.user,
            content='Second source content'
        )
        Connection.objects.create(
            article_id=self.article.id,
            sourcearea_id=source2.id,
            creator=self.user
        )
        
        url = reverse('connection-by-source')
        response = self.client.get(url, {'sourcearea_id': str(self.source.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['sourcearea_id'], str(self.source.id))
        
        # Test without sourcearea_id parameter
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_permissions_creator_only(self):
        """Test that only connection creators can modify their connections"""
        # Other user cannot update
        self.client.force_authenticate(user=self.other_user)
        url = reverse('connection-detail', args=[self.connection.id])
        update_data = {'article_text': 'Unauthorized update'}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Other user cannot delete
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Other user cannot rate (assuming rate action requires creator permission)
        rate_url = reverse('connection-rate', args=[self.connection.id])
        response = self.client.post(rate_url, {'score': 50}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_access(self):
        """Test access without authentication"""
        self.client.force_authenticate(user=None)
        
        # List should work (read-only)
        url = reverse('connection-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Create should fail
        connection_data = {
            'article_id': str(self.article.id),
            'sourcearea_id': str(self.source.id)
        }
        response = self.client.post(url, connection_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_search_functionality(self):
        """Test searching connections by text content"""
        # Create connections with different text
        Connection.objects.create(
            article_id=self.article.id,
            sourcearea_id=self.source.id,
            article_text='Financial data shows growth',
            explainer_text='Economic statistics',
            creator=self.user
        )
        Connection.objects.create(
            article_id=self.article.id,
            sourcearea_id=self.source.id,
            article_text='Climate change impacts',
            explainer_text='Environmental research',
            creator=self.user
        )
        
        url = reverse('connection-list')
        
        # Search in article_text
        response = self.client.get(url, {'search': 'Financial'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Search in explainer_text
        response = self.client.get(url, {'search': 'Environmental'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_ordering_functionality(self):
        """Test ordering connections"""
        url = reverse('connection-list')
        
        # Test ordering by confidence_score
        response = self.client.get(url, {'ordering': 'confidence_score'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test ordering by created_at (descending - default)
        response = self.client.get(url, {'ordering': '-created_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ConnectionSerializerTests(TestCase):
    """Test the Connection serializers"""
    
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
            content='Test source content'
        )
    
    def test_connection_serializer_creation(self):
        """Test creating a connection through serializer"""
        from .serializers import ConnectionSerializer
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = self.user
        
        data = {
            'article_id': str(self.article.id),
            'sourcearea_id': str(self.source.id),
            'article_text': 'Serializer test text',
            'explainer_text': 'Serializer test explanation',
            'confidence_score': 80.0
        }
        
        serializer = ConnectionSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        connection = serializer.save()
        self.assertEqual(connection.creator, self.user)
        self.assertEqual(connection.article_text, data['article_text'])
    
    def test_connection_serializer_read_only_fields(self):
        """Test that read-only fields are properly handled"""
        from .serializers import ConnectionSerializer
        
        connection = Connection.objects.create(
            article_id=self.article.id,
            sourcearea_id=self.source.id,
            creator=self.user
        )
        
        serializer = ConnectionSerializer(connection)
        data = serializer.data
        
        # Check that read-only fields are included
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIn('creator', data)
        
        # Check creator nested serialization
        self.assertEqual(data['creator']['username'], self.user.username)
        self.assertEqual(data['creator']['id'], str(self.user.id))