# File: backend/apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from .models import UserConsent

User = get_user_model()


class UserConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserConsent
        fields = ['id', 'consent_type', 'consent_version', 'granted_at', 'revoked_at']
        read_only_fields = ['id', 'granted_at']


class UserSerializer(serializers.ModelSerializer):
    consents = UserConsentSerializer(many=True, read_only=True)
    has_pin_2fa = serializers.BooleanField(read_only=True)
    has_email_2fa = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'reputation', 
                  'date_joined', 'last_login_timestamp', 'account_status',
                  'two_factor_enabled', 'two_factor_method', 'has_pin_2fa', 
                  'has_email_2fa', 'consents', 'dark_mode_enabled']
        read_only_fields = ['id', 'date_joined', 'reputation', 'role', 'last_login_timestamp']


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with detailed info (used by admins)
    """
    consents = UserConsentSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'reputation', 
                  'date_joined', 'last_login_timestamp', 'account_status',
                  'two_factor_enabled', 'two_factor_method', 'two_factor_pin',
                  'is_active', 'is_staff', 'is_superuser', 'consents']
        read_only_fields = ['id', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with optional 2FA setup
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    # Required consents
    privacy_policy = serializers.BooleanField(write_only=True, required=True)
    terms_of_service = serializers.BooleanField(write_only=True, required=True)
    
    # Optional 2FA fields
    enable_2fa = serializers.BooleanField(write_only=True, required=False, default=False)
    two_factor_pin = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'password_confirm', 'privacy_policy', 
                  'terms_of_service', 'enable_2fa', 'two_factor_pin', 'email']
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Validate required consents
        if not attrs.get('privacy_policy', False):
            raise serializers.ValidationError({"privacy_policy": "You must accept the Privacy Policy."})
        
        if not attrs.get('terms_of_service', False):
            raise serializers.ValidationError({"terms_of_service": "You must accept the Terms of Service."})
        
        # Validate 2FA setup
        enable_2fa = attrs.get('enable_2fa', False)
        pin = attrs.get('two_factor_pin', '').strip()
        email = attrs.get('email', '').strip()
        
        if enable_2fa:
            if not pin and not email:
                raise serializers.ValidationError({
                    "enable_2fa": "When enabling 2FA, you must provide either a PIN or email address."
                })
        
        # Validate username uniqueness (Django doesn't auto-validate this for custom USERNAME_FIELD)
        username = attrs.get('username')
        if username and User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "A user with this username already exists."})
        
        return attrs
    
    def create(self, validated_data):
        # Remove non-model fields
        validated_data.pop('password_confirm')
        privacy_policy = validated_data.pop('privacy_policy')
        terms_of_service = validated_data.pop('terms_of_service')
        enable_2fa = validated_data.pop('enable_2fa', False)
        pin = validated_data.pop('two_factor_pin', '').strip()
        email = validated_data.pop('email', '').strip()
        
        pin_to_hash = None
        if enable_2fa and (pin or email):
            validated_data['two_factor_enabled'] = True
            
            # Determine 2FA method
            if pin and email:
                validated_data['two_factor_method'] = 'both'
                pin_to_hash = pin  # Store for later hashing
                validated_data['email'] = email
            elif pin:
                validated_data['two_factor_method'] = 'pin'
                pin_to_hash = pin  # Store for later hashing
            elif email:
                validated_data['two_factor_method'] = 'email'
                validated_data['email'] = email
        else:
            # Set email if provided even without 2FA
            if email:
                validated_data['email'] = email

        # Create the user
        user = User.objects.create_user(**validated_data)

        # Hash and set PIN after user creation
        if pin_to_hash:
            user.set_pin(pin_to_hash)
            user.save()
        
        # Create consent records
        if privacy_policy:
            UserConsent.objects.create(
                user=user,
                consent_type='privacy_policy',
                consent_version='1.0'
            )
        
        if terms_of_service:
            UserConsent.objects.create(
                user=user,
                consent_type='terms_of_service',
                consent_version='1.0'
            )
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login with 2FA support
    """
    username = serializers.CharField()
    password = serializers.CharField()
    
    # Optional 2FA fields
    two_factor_pin = serializers.CharField(required=False, allow_blank=True)
    two_factor_email = serializers.EmailField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        pin = attrs.get('two_factor_pin', '').strip()
        email = attrs.get('two_factor_email', '').strip()
        
        if not username or not password:
            raise serializers.ValidationError("Username and password are required.")
        
        # Authenticate user with username/password
        user = authenticate(username=username, password=password)
        
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        
        if user.account_status != 'active':
            raise serializers.ValidationError(f"Your account is {user.account_status}.")
        
        # Check 2FA if enabled
        if user.two_factor_enabled:
            if not user.verify_2fa(pin=pin, email=email):
                # Provide specific error messages based on 2FA method
                if user.two_factor_method == 'pin':
                    raise serializers.ValidationError("Invalid PIN provided.")
                elif user.two_factor_method == 'email':
                    raise serializers.ValidationError("Invalid email provided.")
                elif user.two_factor_method == 'both':
                    raise serializers.ValidationError("Invalid PIN or email provided.")
        
        attrs['user'] = user
        return attrs


class TwoFactorSetupSerializer(serializers.Serializer):
    """
    Serializer for setting up or updating 2FA on existing account
    """
    enable_2fa = serializers.BooleanField(required=True)
    two_factor_method = serializers.ChoiceField(
        choices=['pin', 'email', 'both'], 
        required=False
    )
    two_factor_pin = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        enable_2fa = attrs.get('enable_2fa')
        method = attrs.get('two_factor_method')
        pin = attrs.get('two_factor_pin', '').strip()
        email = attrs.get('email', '').strip()
        
        if enable_2fa:
            if not method:
                raise serializers.ValidationError({"two_factor_method": "2FA method is required when enabling 2FA."})
            
            if method in ['pin', 'both'] and not pin:
                raise serializers.ValidationError({"two_factor_pin": "PIN is required for this 2FA method."})
            
            if method in ['email', 'both'] and not email:
                raise serializers.ValidationError({"email": "Email is required for this 2FA method."})
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Your old password was entered incorrectly.")
        return value


class UserConsentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating user consent
    """
    class Meta:
        model = UserConsent
        fields = ['consent_type', 'consent_version']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class UserConsentRevokeSerializer(serializers.ModelSerializer):
    """
    Serializer for revoking user consent
    """
    class Meta:
        model = UserConsent
        fields = ['revoked_at']