"""
DRF API views for social interactions.
Wraps services.py business logic with REST endpoints.
"""
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.shortcuts import get_object_or_404

from social.models import Comment, FlaggedContent
from social.serializers import (
    RatingSerializer,
    RatingCreateSerializer,
    RatingAggregateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    CommentUpdateSerializer,
    FlagSerializer,
    FlagCreateSerializer,
    FlagResolveSerializer,
)
from social.services import (
    RatingService,
    CommentService,
    ModerationService,
)


class RateEntityView(APIView):
    """
    Create or update a rating.
    POST /api/social/ratings/
    Body: {entity_uuid, entity_type, dimension, score}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RatingCreateSerializer(data=request.data)
        if serializer.is_valid():
            rating_service = RatingService()
            rating = rating_service.rate_entity(
                user_id=request.user.id,
                entity_uuid=serializer.validated_data['entity_uuid'],
                entity_type=serializer.validated_data['entity_type'],
                score=serializer.validated_data['score'],
                dimension=serializer.validated_data.get('dimension')
            )
            response_serializer = RatingSerializer(rating)
            return Response({
                'data': response_serializer.data,
                'meta': {'source': 'social'},
                'error': None
            }, status=status.HTTP_201_CREATED)
        return Response({
            'data': None,
            'meta': {'source': 'social'},
            'error': {'code': 'validation_error', 'message': serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)


class EntityRatingsView(APIView):
    """
    Get aggregated ratings for an entity.
    GET /api/social/ratings/?entity=<uuid>&dimension=<confidence|relevance>
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        entity_uuid = request.query_params.get('entity')
        dimension = request.query_params.get('dimension')

        if not entity_uuid:
            return Response({
                'data': None,
                'meta': {'source': 'social'},
                'error': {'code': 'missing_parameter', 'message': 'entity parameter is required'}
            }, status=status.HTTP_400_BAD_REQUEST)

        rating_service = RatingService()
        aggregates = rating_service.get_entity_ratings(entity_uuid, dimension)

        serializer = RatingAggregateSerializer(aggregates)
        return Response({
            'data': serializer.data,
            'meta': {'source': 'social'},
            'error': None
        }, status=status.HTTP_200_OK)


class DeleteRatingView(APIView):
    """
    Delete user's own rating.
    DELETE /api/social/ratings/?entity=<uuid>&entity_type=<type>&dimension=<dimension>
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        entity_uuid = request.query_params.get('entity')
        entity_type = request.query_params.get('entity_type')
        dimension = request.query_params.get('dimension')

        if not entity_uuid or not entity_type:
            return Response({
                'data': None,
                'meta': {'source': 'social'},
                'error': {'code': 'missing_parameter', 'message': 'entity and entity_type parameters are required'}
            }, status=status.HTTP_400_BAD_REQUEST)

        rating_service = RatingService()
        success = rating_service.delete_rating(
            user_id=request.user.id,
            entity_uuid=entity_uuid,
            entity_type=entity_type,
            dimension=dimension
        )

        if success:
            return Response({
                'data': {'deleted': True},
                'meta': {'source': 'social'},
                'error': None
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'data': None,
                'meta': {'source': 'social'},
                'error': {'code': 'not_found', 'message': 'Rating not found'}
            }, status=status.HTTP_404_NOT_FOUND)


class CommentEntityView(APIView):
    """
    Create a comment.
    POST /api/social/comments/
    Body: {entity_uuid, entity_type, content, parent_comment (optional)}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            comment_service = CommentService()
            comment = comment_service.create_comment(
                user_id=request.user.id,
                entity_uuid=serializer.validated_data['entity_uuid'],
                entity_type=serializer.validated_data['entity_type'],
                content=serializer.validated_data['content'],
                parent_comment_id=serializer.validated_data.get('parent_comment').id if serializer.validated_data.get('parent_comment') else None
            )
            response_serializer = CommentSerializer(comment)
            return Response({
                'data': response_serializer.data,
                'meta': {'source': 'social'},
                'error': None
            }, status=status.HTTP_201_CREATED)
        return Response({
            'data': None,
            'meta': {'source': 'social'},
            'error': {'code': 'validation_error', 'message': serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)


class EntityCommentsView(APIView):
    """
    Get all comments for an entity.
    GET /api/social/comments/?entity=<uuid>
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        entity_uuid = request.query_params.get('entity')

        if not entity_uuid:
            return Response({
                'data': None,
                'meta': {'source': 'social'},
                'error': {'code': 'missing_parameter', 'message': 'entity parameter is required'}
            }, status=status.HTTP_400_BAD_REQUEST)

        comment_service = CommentService()
        comments = comment_service.get_entity_comments(entity_uuid, include_deleted=False)

        serializer = CommentSerializer(comments, many=True)
        return Response({
            'data': serializer.data,
            'meta': {'source': 'social', 'count': len(comments)},
            'error': None
        }, status=status.HTTP_200_OK)


class CommentDetailView(APIView):
    """
    Update or delete a specific comment.
    PATCH /api/social/comments/<id>/ - Update content (own comment only)
    DELETE /api/social/comments/<id>/ - Soft delete (own comment or moderator)
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, comment_id):
        """Update comment content (own comment only)"""
        serializer = CommentUpdateSerializer(data=request.data)
        if serializer.is_valid():
            comment_service = CommentService()
            comment = comment_service.update_comment(
                comment_id=comment_id,
                user_id=request.user.id,
                new_content=serializer.validated_data['content']
            )
            if comment:
                response_serializer = CommentSerializer(comment)
                return Response({
                    'data': response_serializer.data,
                    'meta': {'source': 'social'},
                    'error': None
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'data': None,
                    'meta': {'source': 'social'},
                    'error': {'code': 'not_found', 'message': 'Comment not found or unauthorized'}
                }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'data': None,
            'meta': {'source': 'social'},
            'error': {'code': 'validation_error', 'message': serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, comment_id):
        """Soft delete comment (own comment or moderator)"""
        comment_service = CommentService()
        is_moderator = request.user.groups.filter(name__in=['Moderator', 'Admin']).exists() or request.user.is_staff

        success = comment_service.soft_delete_comment(
            comment_id=comment_id,
            user_id=request.user.id,
            is_moderator=is_moderator
        )

        if success:
            return Response({
                'data': {'deleted': True},
                'meta': {'source': 'social'},
                'error': None
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'data': None,
                'meta': {'source': 'social'},
                'error': {'code': 'not_found', 'message': 'Comment not found or unauthorized'}
            }, status=status.HTTP_404_NOT_FOUND)


class FlagEntityView(APIView):
    """
    Flag content for moderation review.
    POST /api/social/moderation/flag/
    Body: {entity_uuid, entity_type, reason}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Verify user has moderator permissions
        is_moderator = request.user.groups.filter(name__in=['Moderator', 'Admin']).exists() or request.user.is_staff
        if not is_moderator:
            return Response({
                'data': None,
                'meta': {'source': 'social'},
                'error': {'code': 'permission_denied', 'message': 'Moderator permissions required'}
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = FlagCreateSerializer(data=request.data)
        if serializer.is_valid():
            moderation_service = ModerationService()
            flag = moderation_service.flag_entity(
                flagged_by_id=request.user.id,
                entity_uuid=serializer.validated_data['entity_uuid'],
                entity_type=serializer.validated_data['entity_type'],
                reason=serializer.validated_data['reason']
            )
            response_serializer = FlagSerializer(flag)
            return Response({
                'data': response_serializer.data,
                'meta': {'source': 'social'},
                'error': None
            }, status=status.HTTP_201_CREATED)
        return Response({
            'data': None,
            'meta': {'source': 'social'},
            'error': {'code': 'validation_error', 'message': serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)


class PendingFlagsView(ListAPIView):
    """
    Get all pending moderation flags.
    GET /api/social/moderation/flags/pending/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FlagSerializer

    def get_queryset(self):
        # Verify user has moderator permissions
        is_moderator = self.request.user.groups.filter(name__in=['Moderator', 'Admin']).exists() or self.request.user.is_staff
        if not is_moderator:
            return FlaggedContent.objects.none()

        moderation_service = ModerationService()
        return moderation_service.get_pending_flags()

    def list(self, request, *args, **kwargs):
        """Wrap response in standard format"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'data': serializer.data,
            'meta': {'source': 'social', 'count': len(serializer.data)},
            'error': None
        }, status=status.HTTP_200_OK)


class ResolveFlagView(APIView):
    """
    Resolve a moderation flag (staff admin only).
    POST /api/social/moderation/flags/<id>/resolve/
    Body: {status: 'reviewed'|'action_taken'|'dismissed', resolution_notes (optional)}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, flag_id):
        # Verify user has staff admin permissions
        if not request.user.is_staff:
            return Response({
                'data': None,
                'meta': {'source': 'social'},
                'error': {'code': 'permission_denied', 'message': 'Staff admin permissions required'}
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = FlagResolveSerializer(data=request.data)
        if serializer.is_valid():
            moderation_service = ModerationService()
            flag = moderation_service.resolve_flag(
                flag_id=flag_id,
                reviewed_by_id=request.user.id,
                status=serializer.validated_data['status'],
                resolution_notes=serializer.validated_data.get('resolution_notes', '')
            )
            if flag:
                response_serializer = FlagSerializer(flag)
                return Response({
                    'data': response_serializer.data,
                    'meta': {'source': 'social'},
                    'error': None
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'data': None,
                    'meta': {'source': 'social'},
                    'error': {'code': 'not_found', 'message': 'Flag not found'}
                }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'data': None,
            'meta': {'source': 'social'},
            'error': {'code': 'validation_error', 'message': serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)


class ControlversialEntitiesView(APIView):
    """
    Get entities with high rating variance (controversial).
    GET /api/social/controversial/?limit=50
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 50))
        limit = min(limit, 200)  # Cap at 200

        rating_service = RatingService()
        controversial = rating_service.get_controversial_entities(limit=limit)

        return Response({
            'data': controversial,
            'meta': {'source': 'social', 'count': len(controversial)},
            'error': None
        }, status=status.HTTP_200_OK)
