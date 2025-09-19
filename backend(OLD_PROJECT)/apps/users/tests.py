from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse



User = get_user_model()
APIClient(secure=False)
class UserModelTests(TestCase):
    """Test the custom User model"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword123'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_user_creation(self):
        """Test creating a user"""
        self.assertEqual(self.user.username, self.user_data['username'])
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertTrue(self.user.check_password(self.user_data['password']))
        self.assertEqual(self.user.reputation, 0)  # Default reputation
        self.assertEqual(self.user.role, 'user')  # Default role
    
    def test_user_string_representation(self):
        """Test the string representation of a user"""
        self.assertEqual(str(self.user), self.user_data['username'])


class UserAPITests(TestCase):
    """Test the User API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        # Use reverse to get the correct URLs
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        
        self.user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
            'privacy_policy': True,
            'terms_of_service': True
        }
    
    def test_user_registration(self):
        """Test user registration"""
        response = self.client.post(self.register_url, self.user_data, format='json', secure=True)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], self.user_data['username'])
        
        # Check that the user was created in the database
        self.assertTrue(User.objects.filter(username=self.user_data['username']).exists())
    
    def test_user_login(self):
        """Test user login"""
        # Create a user
        User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='loginpassword123'
        )
        
        # Login with correct credentials
        login_data = {
            'email': 'login@example.com',
            'password': 'loginpassword123'
        }
        response = self.client.post(self.login_url, login_data, format='json', secure=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'loginuser')
        
        # Login with incorrect credentials
        login_data['password'] = 'wrongpassword'
        response = self.client.post(self.login_url, login_data, format='json', secure=True)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)