# File: backend/apps/users/views.py
from rest_framework import status, generics, viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, login, logout
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .services import AccountDeletionService, UserDataService

from .models import UserConsent
from .serializers import (
    UserSerializer, 
    UserDetailSerializer,
    RegisterSerializer, 
    LoginSerializer, 
    ChangePasswordSerializer,
    TwoFactorSetupSerializer,
    UserConsentSerializer,
    UserConsentCreateSerializer,
    UserConsentRevokeSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    API view for user registration with optional 2FA setup
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Return the created user data with tokens
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "access": str(access_token),
            "refresh": str(refresh),
            "message": "User registered successfully",
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    API view for user login with 2FA support
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Update last login timestamp
        user.last_login_timestamp = timezone.now()
        user.save(update_fields=['last_login_timestamp'])
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return Response({
            "user": UserSerializer(user).data,
            "access": str(access_token),
            "refresh": str(refresh),
            "message": "User logged in successfully",
        })


class LoginCheckView(APIView):
    """
    API view to check what 2FA methods a user has enabled
    This allows the frontend to show appropriate 2FA fields
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {"detail": "Username and password are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use a constant-time approach to prevent timing attacks
        from django.contrib.auth import authenticate
        import time
        start_time = time.time()
        
        user = authenticate(username=username, password=password)
        
        # Ensure minimum response time to prevent timing attacks
        elapsed = time.time() - start_time
        if elapsed < 0.1:  # Minimum 100ms response time
            time.sleep(0.1 - elapsed)
        
        if not user:
            return Response(
                {"detail": "Invalid username or password"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active or user.account_status != 'active':
            return Response(
                {"detail": "Account is not active"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Return 2FA requirements without logging the user in
        response_data = {
            "username": user.username,
            "two_factor_enabled": user.two_factor_enabled,
        }
        
        if user.two_factor_enabled:
            response_data.update({
                "two_factor_method": user.two_factor_method,
                "requires_pin": user.has_pin_2fa(),
                "requires_email": user.has_email_2fa(),
            })
        else:
            # If no 2FA, we can complete login immediately
            user.last_login_timestamp = timezone.now()
            user.save(update_fields=['last_login_timestamp'])
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            response_data.update({
                "user": UserSerializer(user).data,
                "access": str(access_token),
                "refresh": str(refresh),
                "login_complete": True,
                "message": "Login successful - no 2FA required"
            })
        
        return Response(response_data)


class LogoutView(APIView):
    """
    API view for user logout
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass  # Token might already be blacklisted or invalid
        
        return Response({"message": "User logged out successfully"})


class UserDetailsView(generics.RetrieveUpdateAPIView):
    """
    API view for retrieving and updating user details
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
class AccountDataView(APIView):
    """
    API view for retrieving user's account data summary
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get account data summary for the authenticated user"""
        from .services import UserDataService
        data_service = UserDataService(request.user)
        data = data_service.get_account_data_summary()
        return Response(data)

class DeleteAccountView(APIView):
    """Two-step account deletion process"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        step = request.data.get('step', '1')
        
        if step == '1':
            # First step: show deletion impact
            deletion_service = AccountDeletionService(request.user)
            impact = deletion_service.get_deletion_impact()
            return Response({
                'step': 1,
                'impact': impact,
                'message': 'Review what will be affected by account deletion'
            })
        
        elif step == '2':
            # Second step: confirm and execute deletion
            confirmation = request.data.get('confirmation', '')
            if confirmation != 'DELETE_MY_ACCOUNT':
                return Response(
                    {'error': 'Invalid confirmation text'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            deletion_service = AccountDeletionService(request.user)
            deletion_service.delete_account_with_tombstoning()
            
            # Logout user
            logout(request)
            
            return Response({
                'step': 2,
                'message': 'Account successfully deleted',
                'deleted': True
            })
        
        else:
            return Response(
                {'error': 'Invalid step'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class TwoFactorSetupView(generics.UpdateAPIView):
    """
    API view for setting up or updating 2FA settings
    """
    serializer_class = TwoFactorSetupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        enable_2fa = serializer.validated_data['enable_2fa']
        
        if enable_2fa:
            method = serializer.validated_data['two_factor_method']
            pin = serializer.validated_data.get('two_factor_pin', '').strip()
            email = serializer.validated_data.get('email', '').strip()
            
            user.two_factor_enabled = True
            user.two_factor_method = method
            
            if method in ['pin', 'both']:
                user.set_pin(pin)
            else:
                user.two_factor_pin = None
                
            if method in ['email', 'both']:
                user.email = email
            # Note: We don't clear email if not using email 2FA, 
            # user might want to keep it for other purposes
            
        else:
            # Disable 2FA
            user.two_factor_enabled = False
            user.two_factor_method = 'pin'  # Reset to default
            user.two_factor_pin = None
        
        user.save()
        
        return Response({
            "message": "2FA settings updated successfully",
            "user": UserSerializer(user).data
        })


class ChangePasswordView(generics.UpdateAPIView):
    """
    API view for changing password
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({"message": "Password updated successfully"})


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management (admin only)
    """
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.account_status = 'active'
        user.save()
        return Response({"message": "User activated successfully"})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.account_status = 'suspended'
        user.save()
        return Response({"message": "User deactivated successfully"})
    
    @action(detail=True, methods=['post'])
    def set_role(self, request, pk=None):
        user = self.get_object()
        role = request.data.get('role')
        
        if role not in [choice[0] for choice in User.ROLE_CHOICES]:
            return Response(
                {"error": f"Invalid role. Choose from: {[choice[0] for choice in User.ROLE_CHOICES]}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.role = role
        user.save()
        return Response({"message": f"User role updated to {role}"})


class UserConsentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user consents
    """
    serializer_class = UserConsentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserConsent.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserConsentCreateSerializer
        elif self.action == 'revoke':
            return UserConsentRevokeSerializer
        return self.serializer_class
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        consent = self.get_object()
        consent.revoked_at = timezone.now()
        consent.save()
        return Response({"message": "Consent revoked successfully"})
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        active_consents = UserConsent.objects.filter(
            user=request.user,
            revoked_at__isnull=True
        )
        serializer = self.get_serializer(active_consents, many=True)
        return Response(serializer.data)
    
class UserPreferencesView(APIView):
    """
    API view for updating user preferences
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request):
        """Update user preferences"""
        user = request.user
        
        # Update dark mode preference if provided
        if 'dark_mode_enabled' in request.data:
            user.dark_mode_enabled = request.data['dark_mode_enabled']
            user.save(update_fields=['dark_mode_enabled'])
        
        return Response({
            'dark_mode_enabled': user.dark_mode_enabled,
            'message': 'Preferences updated successfully'
        })
    
    def get(self, request):
        """Get current user preferences"""
        return Response({
            'dark_mode_enabled': request.user.dark_mode_enabled
        })