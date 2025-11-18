"""
User serializers for REST API.
Handles user registration, authentication, and profile data.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from users.models import User, UserProfile, UserAttribution, UserModificationAttribution


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, data):
        """Validate password confirmation matches"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data

    def validate_email(self, value):
        """Ensure email is unique if provided"""
        # Only validate uniqueness if email is provided and non-empty
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        return value

    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm')
        email = validated_data.get('email', '')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=email,
            password=validated_data['password']
        )
        # Create associated UserProfile
        UserProfile.objects.create(user=user)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        """Authenticate user credentials"""
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid username or password")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            data['user'] = user
        else:
            raise serializers.ValidationError("Must include username and password")

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile display"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'username',
            'email',
            'display_name',
            'bio',
            'total_claims',
            'total_sources',
            'total_connections',
            'reputation_score',
            'date_joined',
            'last_updated'
        ]
        read_only_fields = [
            'username',
            'email',
            'total_claims',
            'total_sources',
            'total_connections',
            'reputation_score',
            'date_joined',
            'last_updated'
        ]

    def get_email(self, obj):
        """Return email only if it exists and is not empty"""
        return obj.user.email if obj.user.email else None


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer"""
    email = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = ['id', 'date_joined']

    def get_email(self, obj):
        """Return email only if it exists and is not empty"""
        return obj.email if obj.email else None


class UserAttributionSerializer(serializers.ModelSerializer):
    """
    Serializer for user attribution - respects anonymity settings.
    Only shows user info if is_anonymous=False and user exists.
    """
    username = serializers.SerializerMethodField()

    class Meta:
        model = UserAttribution
        fields = ['entity_uuid', 'entity_type', 'username', 'is_anonymous', 'timestamp']

    def get_username(self, obj):
        """Return username, [anonymous], or [deleted] based on state"""
        if obj.is_anonymous:
            return '[anonymous]'
        elif obj.user is None:
            return '[deleted]'
        else:
            return obj.user.username


class UserModificationAttributionSerializer(serializers.ModelSerializer):
    """
    Serializer for modification attribution - respects anonymity settings.
    Only shows user info if is_anonymous=False and user exists.
    """
    username = serializers.SerializerMethodField()

    class Meta:
        model = UserModificationAttribution
        fields = ['entity_uuid', 'version_number', 'entity_type', 'username', 'is_anonymous', 'timestamp']

    def get_username(self, obj):
        """Return username, [anonymous], or [deleted] based on state"""
        if obj.is_anonymous:
            return '[anonymous]'
        elif obj.user is None:
            return '[deleted]'
        else:
            return obj.user.username


class ContributionSerializer(serializers.Serializer):
    """Serializer for user contribution counts"""
    total_claims = serializers.IntegerField()
    total_sources = serializers.IntegerField()
    total_connections = serializers.IntegerField()
    total_edits = serializers.IntegerField()


class LeaderboardEntrySerializer(serializers.Serializer):
    """Serializer for leaderboard entries"""
    username = serializers.CharField()
    reputation_score = serializers.IntegerField()
    total_claims = serializers.IntegerField()
    total_sources = serializers.IntegerField()
    total_connections = serializers.IntegerField()
    joined_date = serializers.DateTimeField()
