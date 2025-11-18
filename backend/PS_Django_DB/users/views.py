"""
User authentication and profile views.
Provides REST API endpoints for user management.
"""
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404

from common.api_standards import standard_response, StandardResponseMixin
from users.models import User, UserProfile, UserAttribution, UserModificationAttribution
from users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserSerializer,
    UserAttributionSerializer,
    UserModificationAttributionSerializer,
    ContributionSerializer,
    LeaderboardEntrySerializer
)
from users.services import UserContributionService
from users.tokens import refresh_token, get_token_expiration_time


class UserRegistrationView(APIView):
    """
    Register a new user account.
    POST /api/users/register/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Create fresh auth token (auto-expires in 15 days)
            token = refresh_token(user)
            return standard_response(
                data={
                    'user': UserSerializer(user).data,
                    'token': token.key,
                    'expires_at': get_token_expiration_time(token).isoformat()
                },
                status_code=status.HTTP_201_CREATED,
                source='users'
            )
        return standard_response(error=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST, source='users')


class UserLoginView(APIView):
    """
    Login user and return authentication token.
    POST /api/users/login/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # Always refresh token on login (delete old, create new)
            # This ensures 15-day expiration starts from login time
            token = refresh_token(user)
            login(request, user)
            return standard_response(
                data={
                    'user': UserSerializer(user).data,
                    'token': token.key,
                    'expires_at': get_token_expiration_time(token).isoformat()
                },
                source='users'
            )
        return standard_response(error=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST, source='users')


class UserLogoutView(APIView):
    """
    Logout user and delete authentication token.
    POST /api/users/logout/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Delete token
        request.user.auth_token.delete()
        logout(request)
        return standard_response(data={'detail': 'Successfully logged out'}, source='users')


class UserProfileView(StandardResponseMixin, generics.RetrieveUpdateAPIView):
    """
    Retrieve or update user profile.
    GET/PUT /api/users/profile/
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get profile for authenticated user"""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class UserProfileDetailView(StandardResponseMixin, generics.RetrieveAPIView):
    """
    Retrieve public profile for any user by username.
    GET /api/users/profile/<username>/
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'user__username'
    lookup_url_kwarg = 'username'
    queryset = UserProfile.objects.select_related('user')


class UserContributionsView(APIView):
    """
    Get contribution counts for authenticated user.
    GET /api/users/contributions/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        service = UserContributionService()
        contributions = service.get_user_contributions(request.user.id)
        serializer = ContributionSerializer(contributions)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EntityAttributionView(APIView):
    """
    Get attribution info for a specific entity.
    GET /api/users/attribution/<entity_uuid>/?type=<claim|source|connection>
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, entity_uuid):
        entity_type = request.query_params.get('type')
        if not entity_type or entity_type not in ['claim', 'source', 'connection']:
            return Response(
                {'error': 'Invalid or missing entity type. Use ?type=claim|source|connection'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get original creator
        try:
            attribution = UserAttribution.objects.get(
                entity_uuid=entity_uuid,
                entity_type=entity_type
            )
            creator_data = UserAttributionSerializer(attribution).data
        except UserAttribution.DoesNotExist:
            creator_data = None

        # Get all editors
        modifications = UserModificationAttribution.objects.filter(
            entity_uuid=entity_uuid,
            entity_type=entity_type
        ).order_by('version_number')
        editors_data = UserModificationAttributionSerializer(modifications, many=True).data

        return Response({
            'creator': creator_data,
            'editors': editors_data
        }, status=status.HTTP_200_OK)


class ToggleAnonymityView(APIView):
    """
    Toggle anonymity for user's own contributions.
    POST /api/users/toggle-anonymity/
    Body: {"entity_uuid": "...", "entity_type": "claim|source|connection", "version_number": null|int}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        entity_uuid = request.data.get('entity_uuid')
        entity_type = request.data.get('entity_type')
        version_number = request.data.get('version_number')

        if not entity_uuid or not entity_type:
            return Response(
                {'error': 'entity_uuid and entity_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if entity_type not in ['claim', 'source', 'connection']:
            return Response(
                {'error': 'Invalid entity_type. Use claim, source, or connection'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = UserContributionService()
        success = service.toggle_anonymity(
            entity_uuid=entity_uuid,
            entity_type=entity_type,
            user_id=request.user.id,
            version_number=version_number
        )

        if success:
            return Response({'detail': 'Anonymity toggled successfully'}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Attribution not found or unauthorized'},
                status=status.HTTP_404_NOT_FOUND
            )


class LeaderboardView(APIView):
    """
    Get top contributors leaderboard.
    GET /api/users/leaderboard/?limit=100
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 100))
        limit = min(limit, 1000)  # Cap at 1000

        service = UserContributionService()
        leaderboard = service.get_leaderboard(limit=limit)
        serializer = LeaderboardEntrySerializer(leaderboard, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BatchAttributionView(APIView):
    """
    Get attributions for multiple entities in one request.
    POST /api/users/attributions/batch/
    Body: {
        "entities": [
            {"uuid": "...", "type": "claim"},
            {"uuid": "...", "type": "source"},
            {"uuid": "...", "type": "connection"}
        ]
    }
    Returns: {entity_uuid: {creator: {...}, editors: [...]}, ...}
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        entities = request.data.get('entities', [])

        if not isinstance(entities, list):
            return Response(
                {'error': 'entities must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = {}
        for entity in entities:
            entity_uuid = entity.get('uuid')
            entity_type = entity.get('type')

            if not entity_uuid or entity_type not in ['claim', 'source', 'connection']:
                continue

            # Get creator
            try:
                attribution = UserAttribution.objects.get(
                    entity_uuid=entity_uuid,
                    entity_type=entity_type
                )
                creator_data = UserAttributionSerializer(attribution).data
            except UserAttribution.DoesNotExist:
                creator_data = None

            # Get editors
            modifications = UserModificationAttribution.objects.filter(
                entity_uuid=entity_uuid,
                entity_type=entity_type
            ).order_by('version_number')
            editors_data = UserModificationAttributionSerializer(modifications, many=True).data

            result[entity_uuid] = {
                'creator': creator_data,
                'editors': editors_data
            }

        return Response(result, status=status.HTTP_200_OK)
