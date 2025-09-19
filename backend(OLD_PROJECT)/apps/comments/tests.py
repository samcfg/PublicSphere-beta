# File: backend/apps/comments/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid

from .models import Comment, CommentVote
from apps.forums.models import ForumCategory, Thread
from apps.articles.models import Article

User = get_user_model()

class CommentModelTests(TestCase):
    """Test the Comment model"""
    
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
        self.comment = Comment.objects.create(
            thread=self.thread,
            author=self.user,
            content='This is a test comment.'
        )
    
    def test_comment_creation(self):
        """Test creating a comment"""
        self.assertEqual(self.comment.content, 'This is a test comment.')
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.thread, self.thread)
        self.assertFalse(self.comment.is_edited)
        self.assertIsNone(self.comment.parent)
    
    def test_reply_creation(self):
        """Test creating a reply to a comment"""
        reply = Comment.objects.create(
            thread=self.thread,
            author=self.user,
            content='This is a reply.',
            parent=self.comment
        )
        self.assertEqual(reply.parent, self.comment)
        self.assertTrue(reply.is_reply)
    
    def test_vote_score(self):
        """Test vote score calculation"""
        # Initial score should be 0
        self.assertEqual(self.comment.vote_score, 0)
        
        # Add upvotes and downvotes
        CommentVote.objects.create(
            comment=self.comment,
            user=self.user,
            is_upvote=True
        )
        
        # Create another user for voting
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword'
        )
        CommentVote.objects.create(
            comment=self.comment,
            user=other_user,
            is_upvote=False
        )
        
        # Score should be 0 (1 upvote - 1 downvote)
        self.assertEqual(self.comment.vote_score, 0)


class CommentAPITests(TestCase):
    """Test the Comment API endpoints"""
    
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
        
        # Create thread
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
        self.thread = Thread.objects.create(
            title='API Test Thread',
            category=self.category,
            creator=self.user
        )
    
    def test_create_comment(self):
        """Test creating a comment via API"""
        url = reverse('comment-list')
        comment_data = {
            'thread': str(self.thread.id),
            'content': 'This is a test comment from the API.'
        }
        response = self.client.post(url, comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], comment_data['content'])
        
        # Check that the comment was created in the database
        self.assertTrue(Comment.objects.filter(content=comment_data['content']).exists())
    
    # Modified test_create_reply function
    def test_create_reply(self):
        """Test creating a reply via API"""
        # Create a comment first
        comment = Comment.objects.create(
            thread=self.thread,
            author=self.user,
            content='Initial comment'
        )
        
        # Create a reply
        url = reverse('comment-list')
        reply_data = {
            'thread': str(self.thread.id),
            'content': 'This is a reply.',
            'parent': str(comment.id)
        }
        response = self.client.post(url, reply_data, format='json')
        
        # Debug information
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response content: {response.content}")
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], reply_data['content'])
        self.assertEqual(str(response.data['parent']), str(comment.id))

    # Modified test_upvote_comment function
    def test_upvote_comment(self):
        """Test upvoting a comment"""
        # Create a comment
        comment = Comment.objects.create(
            thread=self.thread,
            author=self.other_user,  # Created by another user
            content='Comment to upvote'
        )
        
        # Upvote the comment
        url = reverse('comment-upvote', args=[comment.id])
        response = self.client.post(url)
        
        # Debug information
        if response.status_code != status.HTTP_200_OK:
            print(f"Response content: {response.content}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the vote was created
        self.assertTrue(
            CommentVote.objects.filter(
                comment=comment,
                user=self.user,
                is_upvote=True
            ).exists()
        )